from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Category
from app.schemas import (
    CategoryCreate,
    CategoryResponse,
    CategoryUpdate,
)

router = APIRouter(prefix="/api/categories", tags=["Admin - Categories"])

DEFAULT_CATEGORIES = [
    {"name": "Dairy", "icon": "🥛"},
    {"name": "Pantry", "icon": "🥫"},
    {"name": "Produce", "icon": "🥦"},
    {"name": "Meat", "icon": "🥩"},
    {"name": "Drinks", "icon": "🧃"},
    {"name": "Frozen", "icon": "❄️"},
    {"name": "Snacks", "icon": "🍫"},
    {"name": "Other", "icon": "📦"},
]


def get_category_or_404(db: Session, category_id: int) -> Category:
    cat = db.query(Category).filter(Category.id == category_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    return cat


@router.get("", response_model=List[CategoryResponse])
def list_categories(db: Session = Depends(get_db)):
    if db.query(Category).count() == 0:
        for item in DEFAULT_CATEGORIES:
            db.add(Category(name=item["name"], icon=item["icon"]))
        db.commit()
    return db.query(Category).order_by(Category.id).all()


@router.post("/", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(payload: CategoryCreate, db: Session = Depends(get_db)):
    existing = db.query(Category).filter(Category.name == payload.name).first()
    if existing:
        raise HTTPException(
            status_code=400, detail="Category with this name already exists"
        )
    cat = Category(name=payload.name, icon=payload.icon)
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat


@router.put("/{category_id}", response_model=CategoryResponse)
def update_category(
    category_id: int, payload: CategoryUpdate, db: Session = Depends(get_db)
):
    cat = get_category_or_404(db, category_id)
    if payload.name is not None:
        existing = (
            db.query(Category)
            .filter(Category.name == payload.name, Category.id != category_id)
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=400, detail="Another category with this name already exists"
            )
        cat.name = payload.name
    if payload.icon is not None:
        cat.icon = payload.icon
    db.commit()
    db.refresh(cat)
    return cat


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(category_id: int, db: Session = Depends(get_db)):
    cat = get_category_or_404(db, category_id)
    db.delete(cat)
    db.commit()
    return None
