"""
Convenience script to populate sample grocery items with varying expiration dates.
Run: uv run python seed_demo.py
"""
from datetime import date, timedelta
from app.database import SessionLocal, Base, engine
from app.models import Item

def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    today = date.today()

    sample_items = [
        {
            "name": "Fresh Organic Milk 1L",
            "brand": "Berchtesgadener Land",
            "ean": "4008400404127",
            "expiration_date": today + timedelta(days=2),
            "quantity": 1,
            "category": "Dairy",
            "location": "Fridge",
            "notes": "Door shelf",
            "status": "active"
        },
        {
            "name": "Greek Yogurt 500g",
            "brand": "Total Fage",
            "ean": "5201051000047",
            "expiration_date": today + timedelta(days=6),
            "quantity": 2,
            "category": "Dairy",
            "location": "Fridge",
            "notes": "Middle compartment",
            "status": "active"
        },
        {
            "name": "Nutella Hazelnut Spread 450g",
            "brand": "Ferrero",
            "ean": "3017620422003",
            "expiration_date": today + timedelta(days=180),
            "quantity": 1,
            "category": "Pantry",
            "location": "Pantry",
            "image_url": "https://images.openfoodfacts.org/images/products/301/762/042/2003/front_en.879.400.jpg",
            "status": "active"
        },
        {
            "name": "Sliced Gouda Cheese",
            "brand": "Milbona",
            "ean": "2000000000001",
            "expiration_date": today - timedelta(days=1),
            "quantity": 1,
            "category": "Dairy",
            "location": "Fridge",
            "notes": "Check smell before eating",
            "status": "active"
        },
    ]

    for item_data in sample_items:
        item = Item(**item_data)
        db.add(item)

    db.commit()
    print(f"Successfully seeded {len(sample_items)} sample items into mhd_tracker.db!")
    db.close()

if __name__ == "__main__":
    seed()
