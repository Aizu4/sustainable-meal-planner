import asyncio
import json
import logging

import aiohttp
from motor.motor_asyncio import AsyncIOMotorDatabase

from scraper.config import (
    MONGO_URI,
    DB_NAME,
    RECIPES_OUTPUT_DIR,
    REQUEST_CONCURRENCY,
    REQUEST_TIMEOUT,
    SCRAPE_INTERVAL_MINUTES,
    USER_AGENT,
)
from scraper.db import get_motor_client, get_all_ingredients, recipe_exists, upsert_ingredient, upsert_recipe
from scraper.ingredient_enricher import enrich_ingredients
from scraper.parsers import close_client, derive_slug, extract_url_from_post, get_client, parse_recipe
from scraper.spiders import fetch_recipe_page, fetch_recipe_urls

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger(__name__)


async def scrape_one(
    session: aiohttp.ClientSession,
    sem: asyncio.Semaphore,
    url: str,
    db: AsyncIOMotorDatabase,
) -> bool:
    """Returns True if a new recipe was scraped, False if skipped."""
    async with sem:
        try:
            slug = derive_slug(url)
            if await recipe_exists(db, slug):
                log.info("Already in DB, skipping %s", slug)
                return False

            html = await fetch_recipe_page(session, url)
            recipe = await parse_recipe(html, url)
            if recipe is None:
                return

            client = get_client()
            db_ingredients = await get_all_ingredients(db)
            enrichments = await enrich_ingredients(client, db_ingredients, recipe["ingredients"])

            for ing, enr in zip(recipe["ingredients"], enrichments):
                n100 = enr.get("nutrition_per_100") or {}
                if n100:
                    qty = ing["quantity"]
                    ing["nutrition"] = {
                        "kcal":    round(qty / 100 * float(n100.get("kcal", 0)), 2),
                        "carbs":   round(qty / 100 * float(n100.get("carbs", 0)), 2),
                        "fat":     round(qty / 100 * float(n100.get("fat", 0)), 2),
                        "protein": round(qty / 100 * float(n100.get("protein", 0)), 2),
                    }

                match_id = enr.get("match_id")
                if match_id:
                    ing["ingredient_id"] = match_id
                else:
                    new_ingredient = {
                        "id": ing["id"],
                        "name": ing["name"].capitalize(),
                        "nutrition_per_100": {
                            "kcal":    float(n100.get("kcal", 0)),
                            "carbs":   float(n100.get("carbs", 0)),
                            "fat":     float(n100.get("fat", 0)),
                            "protein": float(n100.get("protein", 0)),
                        },
                    }
                    await upsert_ingredient(db, new_ingredient)
                    ing["ingredient_id"] = ing["id"]

            await upsert_recipe(db, recipe)

            if RECIPES_OUTPUT_DIR is not None:
                RECIPES_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
                out = RECIPES_OUTPUT_DIR / f"{recipe['id']}.json"
                out.write_text(json.dumps(recipe, indent=2, ensure_ascii=False), encoding="utf-8")
                log.info("Written %s", out)
            return True
        except Exception:
            log.exception("Failed to scrape %s", url)
            return False


async def run_once(db: AsyncIOMotorDatabase) -> None:
    headers = {"User-Agent": USER_AGENT}
    async with aiohttp.ClientSession(timeout=REQUEST_TIMEOUT, headers=headers) as session:
        posts = await fetch_recipe_urls(session)
        urls = [u for post in posts if (u := extract_url_from_post(post))]
        log.info("Fetched %d URLs", len(urls))

        sem = asyncio.Semaphore(REQUEST_CONCURRENCY)
        results = await asyncio.gather(*(scrape_one(session, sem, url, db) for url in urls))

    new_count = sum(1 for r in results if r)
    log.info("Run complete: %d new, %d skipped out of %d URLs", new_count, len(urls) - new_count, len(urls))
    await close_client()


async def run_loop() -> None:
    client = get_motor_client(MONGO_URI)
    db = client[DB_NAME]
    log.info("Connected to MongoDB — scraping every %d minutes", SCRAPE_INTERVAL_MINUTES)
    try:
        while True:
            log.info("Starting scrape run")
            await run_once(db)
            log.info("Scrape run complete — sleeping %d minutes", SCRAPE_INTERVAL_MINUTES)
            await asyncio.sleep(SCRAPE_INTERVAL_MINUTES * 60)
    finally:
        client.close()
