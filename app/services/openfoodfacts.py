import logging
from typing import Optional, Dict, Any
import httpx

logger = logging.getLogger(__name__)

OPEN_FOOD_FACTS_URL = "https://world.openfoodfacts.org/api/v2/product/{ean}.json"
HEADERS = {
    "User-Agent": "MHDTracker - Python/FastAPI/HomeLab - Version 0.1"
}


async def fetch_open_food_facts(ean: str) -> Optional[Dict[str, Any]]:
    """
    Look up product information on Open Food Facts by EAN / barcode.
    Returns a dict with name, brand, category, image_url or None if not found.
    """
    clean_ean = ean.strip()
    if not clean_ean:
        return None

    url = OPEN_FOOD_FACTS_URL.format(ean=clean_ean)
    try:
        async with httpx.AsyncClient(timeout=4.0) as client:
            response = await client.get(url, headers=HEADERS)
            if response.status_code != 200:
                logger.info(f"OpenFoodFacts returned status {response.status_code} for EAN {clean_ean}")
                return None

            data = response.json()
            if data.get("status") != 1:
                return None

            product = data.get("product", {})
            name = (
                product.get("product_name")
                or product.get("product_name_de")
                or product.get("product_name_en")
                or product.get("generic_name")
            )
            brand = product.get("brands")
            if brand and "," in brand:
                brand = brand.split(",")[0].strip()

            image_url = product.get("image_front_url") or product.get("image_url")
            
            # Categories mapping
            categories_tags = product.get("categories_tags", [])
            category = "Pantry"
            if categories_tags:
                first_cat = categories_tags[0].lower()
                if "dairy" in first_cat or "milch" in first_cat or "cheese" in first_cat:
                    category = "Dairy"
                elif "meat" in first_cat or "fleisch" in first_cat or "wurst" in first_cat:
                    category = "Meat"
                elif "beverage" in first_cat or "getraenk" in first_cat or "drink" in first_cat:
                    category = "Drinks"
                elif "fruit" in first_cat or "vegetable" in first_cat or "gemuese" in first_cat:
                    category = "Produce"
                elif "frozen" in first_cat or "tiefkuehl" in first_cat:
                    category = "Frozen"
                elif "snack" in first_cat or "sweet" in first_cat:
                    category = "Snacks"

            return {
                "ean": clean_ean,
                "name": name or f"Product {clean_ean}",
                "brand": brand,
                "category": category,
                "image_url": image_url,
                "source": "openfoodfacts"
            }
    except Exception as e:
        logger.warning(f"Error fetching from Open Food Facts for EAN {clean_ean}: {e}")
        return None
