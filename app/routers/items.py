from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.database import get_db
from app.models import Item, ProductCache
from app.schemas import ItemCreate, ItemResponse, ItemUpdate, DashboardStats

router = APIRouter(prefix="/api/items", tags=["Items"])


def enrich_item(item: Item) -> ItemResponse:
    today = date.today()
    days_left = (item.expiration_date - today).days
    return ItemResponse(
        id=item.id,
        ean=item.ean,
        name=item.name,
        brand=item.brand,
        expiration_date=item.expiration_date,
        quantity=item.quantity,
        category=item.category,
        location=item.location,
        notes=item.notes,
        image_url=item.image_url,
        status=item.status,
        created_at=item.created_at,
        updated_at=item.updated_at,
        days_left=days_left,
    )


@router.get("/stats", response_model=DashboardStats)
def get_stats(db: Session = Depends(get_db)):
    active_items = db.query(Item).filter(Item.status == "active").all()
    today = date.today()

    expired_count = 0
    expiring_soon_count = 0
    ok_count = 0

    for item in active_items:
        days = (item.expiration_date - today).days
        if days < 0:
            expired_count += 1
        elif days <= 3:
            expiring_soon_count += 1
        else:
            ok_count += 1

    return DashboardStats(
        total_active=len(active_items),
        expired_count=expired_count,
        expiring_soon_count=expiring_soon_count,
        ok_count=ok_count,
    )


@router.get("", response_model=List[ItemResponse])
def list_items(
    status: Optional[str] = Query("active", description="Filter by status (active, consumed, discarded, all)"),
    search: Optional[str] = Query(None, description="Search term for name, brand, or ean"),
    category: Optional[str] = Query(None, description="Filter by category"),
    location: Optional[str] = Query(None, description="Filter by location"),
    db: Session = Depends(get_db),
):
    query = db.query(Item)

    if status and status != "all":
        query = query.filter(Item.status == status)

    if search:
        search_term = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Item.name.ilike(search_term),
                Item.brand.ilike(search_term),
                Item.ean.ilike(search_term),
            )
        )

    if category:
        query = query.filter(Item.category == category)

    if location:
        query = query.filter(Item.location == location)

    # Order by expiration date ascending (nearest expiration first)
    query = query.order_by(Item.expiration_date.asc(), Item.name.asc())
    items = query.all()

    return [enrich_item(item) for item in items]


@router.post("", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
def create_item(payload: ItemCreate, db: Session = Depends(get_db)):
    item = Item(
        ean=payload.ean,
        name=payload.name,
        brand=payload.brand,
        expiration_date=payload.expiration_date,
        quantity=payload.quantity,
        category=payload.category or "Pantry",
        location=payload.location or "Fridge",
        notes=payload.notes,
        image_url=payload.image_url,
        status="active",
    )
    db.add(item)

    # If EAN is present, update or save product cache
    if payload.ean:
        clean_ean = payload.ean.strip()
        cache = db.query(ProductCache).filter(ProductCache.ean == clean_ean).first()
        if not cache:
            cache = ProductCache(
                ean=clean_ean,
                name=payload.name,
                brand=payload.brand,
                category=payload.category,
                image_url=payload.image_url,
            )
            db.add(cache)

    db.commit()
    db.refresh(item)
    return enrich_item(item)


@router.get("/{item_id}", response_model=ItemResponse)
def get_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return enrich_item(item)


@router.put("/{item_id}", response_model=ItemResponse)
def update_item(item_id: int, payload: ItemUpdate, db: Session = Depends(get_db)):
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(item, field, value)

    db.commit()
    db.refresh(item)
    return enrich_item(item)


@router.post("/{item_id}/consume", response_model=ItemResponse)
def consume_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    if item.quantity > 1:
        item.quantity -= 1
    else:
        item.quantity = 0
        item.status = "consumed"

    db.commit()
    db.refresh(item)
    return enrich_item(item)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    db.delete(item)
    db.commit()
    return None
