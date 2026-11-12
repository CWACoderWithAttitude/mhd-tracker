from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ItemBase(BaseModel):
    ean: Optional[str] = None
    name: str = Field(..., min_length=1, max_length=255)
    brand: Optional[str] = None
    expiration_date: date
    quantity: int = Field(default=1, ge=0)
    category: Optional[str] = "Pantry"
    location: Optional[str] = "Fridge"
    notes: Optional[str] = None
    image_url: Optional[str] = None


class ItemCreate(ItemBase):
    pass


class ItemUpdate(BaseModel):
    ean: Optional[str] = None
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    brand: Optional[str] = None
    expiration_date: Optional[date] = None
    quantity: Optional[int] = Field(None, ge=0)
    category: Optional[str] = None
    location: Optional[str] = None
    notes: Optional[str] = None
    image_url: Optional[str] = None
    status: Optional[str] = None  # active, consumed, discarded


class ItemResponse(ItemBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: str
    created_at: datetime
    updated_at: datetime
    days_left: int = 0


# ---- Location Schemas -----------------------------------------------------
class LocationBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)


class LocationCreate(LocationBase):
    pass


class LocationUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)


class LocationResponse(LocationBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


# ---- Category Schemas -----------------------------------------------------
class CategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    icon: Optional[str] = Field(None, max_length=50)


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    icon: Optional[str] = Field(None, max_length=50)


class CategoryResponse(CategoryBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


class ProductLookupResponse(BaseModel):
    found: bool
    ean: str
    name: Optional[str] = None
    brand: Optional[str] = None
    category: Optional[str] = None
    image_url: Optional[str] = None
    source: str = "none"


class DashboardStats(BaseModel):
    total_active: int
    expired_count: int
    expiring_soon_count: int  # <= 3 days
    ok_count: int
