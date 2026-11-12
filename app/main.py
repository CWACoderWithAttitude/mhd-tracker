import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.database import Base, engine
from app.routers import admin_categories, admin_locations, items, lookup


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables
    Base.metadata.create_all(bind=engine)
    # Seed default locations and categories if table empty
    from sqlalchemy.orm import Session

    from app.models import Category, Location
    from app.routers.admin_categories import DEFAULT_CATEGORIES

    with Session(bind=engine) as db:
        if db.query(Location).count() == 0:
            for name in ["Fridge", "Pantry", "Cellar"]:
                db.add(Location(name=name))
            db.commit()
        if db.query(Category).count() == 0:
            for cat in DEFAULT_CATEGORIES:
                db.add(Category(name=cat["name"], icon=cat["icon"]))
            db.commit()
    yield


app = FastAPI(
    title="MHD Tracker API",
    description="FastAPI Backend for Food Expiration Date & Barcode Tracking",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS setup for mobile and local frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routers
app.include_router(items.router)
app.include_router(admin_locations.router)
app.include_router(admin_categories.router)
app.include_router(lookup.router)


@app.get("/api/health")
def health_check():
    return {"status": "ok", "app": "mhd-tracker"}


# Mount frontend static files if built
frontend_dist = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
if os.path.exists(frontend_dist):
    app.mount(
        "/assets",
        StaticFiles(directory=os.path.join(frontend_dist, "assets")),
        name="assets",
    )

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        file_path = os.path.join(frontend_dist, full_path)
        if full_path and os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(frontend_dist, "index.html"))
