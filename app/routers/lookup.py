from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Item, ProductCache
from app.schemas import ProductLookupResponse
from app.services.openfoodfacts import fetch_open_food_facts

router = APIRouter(prefix="/api/lookup", tags=["Lookup"])


@router.get("/ean/{ean}", response_model=ProductLookupResponse)
async def lookup_ean(ean: str, db: Session = Depends(get_db)):
    clean_ean = ean.strip()

    # 1. Check local product cache
    cached = db.query(ProductCache).filter(ProductCache.ean == clean_ean).first()
    if cached:
        return ProductLookupResponse(
            found=True,
            ean=cached.ean,
            name=cached.name,
            brand=cached.brand,
            category=cached.category,
            image_url=cached.image_url,
            source="cache",
        )

    # 2. Check if already entered in items
    existing_item = (
        db.query(Item).filter(Item.ean == clean_ean).order_by(Item.id.desc()).first()
    )
    if existing_item:
        # Cache for next time
        new_cache = ProductCache(
            ean=clean_ean,
            name=existing_item.name,
            brand=existing_item.brand,
            category=existing_item.category,
            image_url=existing_item.image_url,
        )
        db.add(new_cache)
        db.commit()
        return ProductLookupResponse(
            found=True,
            ean=clean_ean,
            name=existing_item.name,
            brand=existing_item.brand,
            category=existing_item.category,
            image_url=existing_item.image_url,
            source="existing_item",
        )

    # 3. Query Open Food Facts
    off_data = await fetch_open_food_facts(clean_ean)
    if off_data:
        new_cache = ProductCache(
            ean=clean_ean,
            name=off_data["name"],
            brand=off_data.get("brand"),
            category=off_data.get("category"),
            image_url=off_data.get("image_url"),
        )
        db.add(new_cache)
        db.commit()
        return ProductLookupResponse(
            found=True,
            ean=clean_ean,
            name=off_data["name"],
            brand=off_data.get("brand"),
            category=off_data.get("category"),
            image_url=off_data.get("image_url"),
            source="openfoodfacts",
        )

    return ProductLookupResponse(
        found=False,
        ean=clean_ean,
        name=None,
        brand=None,
        category="Pantry",
        image_url=None,
        source="not_found",
    )
