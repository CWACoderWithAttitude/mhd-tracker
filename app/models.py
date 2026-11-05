from datetime import datetime, timezone, date
from typing import Optional
from sqlalchemy import Column, Integer, String, Text, Date, DateTime
from app.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    ean = Column(String(64), index=True, nullable=True)
    name = Column(String(255), nullable=False)
    brand = Column(String(255), nullable=True)
    expiration_date = Column(Date, nullable=False, index=True)
    quantity = Column(Integer, default=1, nullable=False)
    category = Column(String(100), nullable=True, default="Pantry")
    location = Column(String(100), nullable=True, default="Fridge")
    notes = Column(Text, nullable=True)
    image_url = Column(String(1024), nullable=True)
    status = Column(String(50), default="active", index=True)  # active, consumed, discarded
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)


class ProductCache(Base):
    __tablename__ = "product_cache"

    ean = Column(String(64), primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    brand = Column(String(255), nullable=True)
    category = Column(String(100), nullable=True)
    image_url = Column(String(1024), nullable=True)
    fetched_at = Column(DateTime, default=utc_now, nullable=False)

