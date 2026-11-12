from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app

# In-memory SQLite for testing with StaticPool so all connections share the memory DB
TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    return TestClient(app)


def test_health_check(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"


def test_create_and_list_items(client):
    today = date.today()
    item_payload = {
        "name": "Organic Oat Milk",
        "brand": "Oatly",
        "ean": "7394376615963",
        "expiration_date": (today + timedelta(days=5)).isoformat(),
        "quantity": 2,
        "category": "Drinks",
        "location": "Fridge",
        "notes": "Door shelf",
    }
    # Create item
    res = client.post("/api/items", json=item_payload)
    assert res.status_code == 201
    created = res.json()
    assert created["id"] is not None
    assert created["name"] == "Organic Oat Milk"
    assert created["days_left"] == 5
    item_id = created["id"]

    # List items
    res = client.get("/api/items")
    assert res.status_code == 200
    items = res.json()
    assert len(items) == 1
    assert items[0]["id"] == item_id

    # Filter search
    res = client.get("/api/items?search=Oatly")
    assert res.status_code == 200
    assert len(res.json()) == 1

    res = client.get("/api/items?search=NonExistent")
    assert res.status_code == 200
    assert len(res.json()) == 0


def test_consume_item(client):
    today = date.today()
    item_payload = {
        "name": "Yogurt",
        "expiration_date": (today + timedelta(days=3)).isoformat(),
        "quantity": 2,
    }
    res = client.post("/api/items", json=item_payload)
    item_id = res.json()["id"]

    # Consume 1: quantity should decrease to 1, still active
    res = client.post(f"/api/items/{item_id}/consume")
    assert res.status_code == 200
    assert res.json()["quantity"] == 1
    assert res.json()["status"] == "active"

    # Consume 1 more: quantity becomes 0, status becomes consumed
    res = client.post(f"/api/items/{item_id}/consume")
    assert res.status_code == 200
    assert res.json()["quantity"] == 0
    assert res.json()["status"] == "consumed"


def test_stats_calculation(client):
    today = date.today()
    # Expired item (-2 days)
    client.post(
        "/api/items",
        json={
            "name": "Expired Cheese",
            "expiration_date": (today - timedelta(days=2)).isoformat(),
            "quantity": 1,
        },
    )
    # Expiring soon item (+1 day)
    client.post(
        "/api/items",
        json={
            "name": "Expiring Salad",
            "expiration_date": (today + timedelta(days=1)).isoformat(),
            "quantity": 1,
        },
    )
    # Fresh item (+30 days)
    client.post(
        "/api/items",
        json={
            "name": "Canned Beans",
            "expiration_date": (today + timedelta(days=30)).isoformat(),
            "quantity": 3,
        },
    )

    res = client.get("/api/items/stats")
    assert res.status_code == 200
    stats = res.json()
    assert stats["total_active"] == 3
    assert stats["expired_count"] == 1
    assert stats["expiring_soon_count"] == 1
    assert stats["ok_count"] == 1


def test_delete_item(client):
    today = date.today()
    res = client.post(
        "/api/items",
        json={
            "name": "To Delete",
            "expiration_date": today.isoformat(),
            "quantity": 1,
        },
    )
    item_id = res.json()["id"]

    del_res = client.delete(f"/api/items/{item_id}")
    assert del_res.status_code == 204

    get_res = client.get(f"/api/items/{item_id}")
    assert get_res.status_code == 404


def test_location_management(client):
    # List default locations (seeded by GET endpoint when table is empty)
    res = client.get("/api/locations")
    assert res.status_code == 200
    locations = res.json()
    assert isinstance(locations, list)
    assert "Fridge" in locations

    # Add a new location
    res = client.post("/api/locations/", json={"name": "Wine Cellar"})
    assert res.status_code == 201
    created = res.json()
    assert created["name"] == "Wine Cellar"
    assert "id" in created

    # List locations again — newly added one is present
    res = client.get("/api/locations")
    assert res.status_code == 200
    locations = res.json()
    assert "Wine Cellar" in locations

    # Duplicate name must be rejected
    res = client.post("/api/locations/", json={"name": "Wine Cellar"})
    assert res.status_code == 400

    # Delete location
    res = client.delete(f"/api/locations/{created['id']}")
    assert res.status_code == 204

    # Verify deleted
    res = client.get("/api/locations")
    assert "Wine Cellar" not in res.json()


def test_locations_are_dynamic_not_hardcoded(client):
    """Verify that the locations list comes from DB and can be fully customised."""
    # Add a custom location that doesn't exist in any hardcoded list
    res = client.post("/api/locations/", json={"name": "Attic Storage"})
    assert res.status_code == 201
    loc_id = res.json()["id"]

    # It must appear in the locations endpoint
    res = client.get("/api/locations")
    assert "Attic Storage" in res.json()

    # Update the location name
    res = client.put(f"/api/locations/{loc_id}", json={"name": "Basement Shelf"})
    assert res.status_code == 200
    assert res.json()["name"] == "Basement Shelf"

    # Old name gone, new name present
    locations = client.get("/api/locations").json()
    assert "Attic Storage" not in locations
    assert "Basement Shelf" in locations


def test_category_management(client):
    # List default categories (seeded by GET endpoint when table is empty)
    res = client.get("/api/categories")
    assert res.status_code == 200
    categories = res.json()
    assert isinstance(categories, list)
    cat_names = [c["name"] for c in categories]
    assert "Dairy" in cat_names
    assert "Drinks" in cat_names
    dairy_cat = next(c for c in categories if c["name"] == "Dairy")
    assert dairy_cat["icon"] == "🥛"

    # Add a new category
    res = client.post("/api/categories/", json={"name": "Bakery", "icon": "🥐"})
    assert res.status_code == 201
    created = res.json()
    assert created["name"] == "Bakery"
    assert created["icon"] == "🥐"
    assert "id" in created

    # List categories again - newly added one is present
    res = client.get("/api/categories")
    assert res.status_code == 200
    categories = res.json()
    cat_names = [c["name"] for c in categories]
    assert "Bakery" in cat_names

    # Duplicate name must be rejected
    res = client.post("/api/categories/", json={"name": "Bakery", "icon": "🥖"})
    assert res.status_code == 400

    # Delete category
    res = client.delete(f"/api/categories/{created['id']}")
    assert res.status_code == 204

    # Verify deleted
    res = client.get("/api/categories")
    cat_names = [c["name"] for c in res.json()]
    assert "Bakery" not in cat_names


def test_categories_are_dynamic_not_hardcoded(client):
    """Verify that categories and icons come from DB and can be fully customised."""
    res = client.post("/api/categories/", json={"name": "Sweets", "icon": "🍬"})
    assert res.status_code == 201
    cat_id = res.json()["id"]

    # Verify it appears in categories endpoint
    categories = client.get("/api/categories").json()
    sweets = next((c for c in categories if c["id"] == cat_id), None)
    assert sweets is not None
    assert sweets["name"] == "Sweets"
    assert sweets["icon"] == "🍬"

    # Update category name and icon
    res = client.put(f"/api/categories/{cat_id}", json={"name": "Candy", "icon": "🍭"})
    assert res.status_code == 200
    assert res.json()["name"] == "Candy"
    assert res.json()["icon"] == "🍭"

    # Verify old name is gone, new name is present
    categories = client.get("/api/categories").json()
    assert not any(c["name"] == "Sweets" for c in categories)
    candy = next((c for c in categories if c["name"] == "Candy"), None)
    assert candy is not None
    assert candy["icon"] == "🍭"
