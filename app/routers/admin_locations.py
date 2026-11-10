from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Location
from app.schemas import (
    LocationCreate,
    LocationUpdate,
    LocationResponse,
)

router = APIRouter(prefix="/api/locations", tags=["Admin - Locations"])

# Helper to get location or raise 404
def get_location_or_404(db: Session, location_id: int) -> Location:
    loc = db.query(Location).filter(Location.id == location_id).first()
    if not loc:
        raise HTTPException(status_code=404, detail="Location not found")
    return loc

@router.get("", response_model=List[str])
def list_locations(db: Session = Depends(get_db)):
    # Ensure default locations exist
    if db.query(Location).count() == 0:
        for name in ["Fridge", "Pantry", "Cellar"]:
            db.add(Location(name=name))
        db.commit()
    # Return just the names for compatibility with existing tests
    names = db.query(Location.name).order_by(Location.name).all()
    return [n[0] for n in names]


@router.post("/", response_model=LocationResponse, status_code=status.HTTP_201_CREATED)
def create_location(payload: LocationCreate, db: Session = Depends(get_db)):
    # Ensure unique name
    existing = db.query(Location).filter(Location.name == payload.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Location with this name already exists")
    loc = Location(name=payload.name)
    db.add(loc)
    db.commit()
    db.refresh(loc)
    return loc

@router.put("/{location_id}", response_model=LocationResponse)
def update_location(location_id: int, payload: LocationUpdate, db: Session = Depends(get_db)):
    loc = get_location_or_404(db, location_id)
    if payload.name:
        # check uniqueness
        existing = db.query(Location).filter(Location.name == payload.name, Location.id != location_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Another location with this name already exists")
        loc.name = payload.name
    db.commit()
    db.refresh(loc)
    return loc

@router.delete("/{location_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_location(location_id: int, db: Session = Depends(get_db)):
    loc = get_location_or_404(db, location_id)
    db.delete(loc)
    db.commit()
    return None
