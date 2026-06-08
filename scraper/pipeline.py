import asyncio
import json
import logging

import aiohttp
from anthropic import AsyncAnthropic
from motor.motor_asyncio import AsyncIOMotorDatabase

from scraper.config import RECIPES_OUTPUT_DIR
from scraper.db import bulk_upsert_ingredients, recipe_exists, upsert_recipe
from scraper.enrichment import enrich_ingredients
from scraper.nutrition import nutrition_per_100_floats, per_ingredient_nutrition
from scraper.parsers import derive_slug, parse_recipe
from scraper.spiders import fetch_recipe_page
from shared.errors import FatalScrapeError, TransientScrapeError

log = logging.getLogger(__name__)


def _apply_enrichments(recipe: dict, enrichments: list[dict]) -> list[dict]:
    """Mutate recipe ingredients with nutrition + ingredient_id; return new DB ingredients to insert."""
    new_ingredients: list[dict] = []
    for ing, enr in zip(recipe["ingredients"], enrichments):
        n100 = enr.get("nutrition_per_100") or {}
        if n100:
            ing["nutrition"] = per_ingredient_nutrition(ing["quantity"], n100)

        match_id = enr.get("match_id")
        if match_id:
            ing["ingredient_id"] = match_id
            continue

        new_ingredients.append({
            "id": ing["id"],
            "name": ing["name"].capitalize(),
            "nutrition_per_100": nutrition_per_100_floats(n100),
        })
        ing["ingredient_id"] = ing["id"]
    return new_ingredients


def _dump_recipe_json(recipe: dict) -> None:
    if RECIPES_OUTPUT_DIR is None:
        return
    RECIPES_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out = RECIPES_OUTPUT_DIR / f"{recipe['id']}.json"
    out.write_text(json.dumps(recipe, indent=2, ensure_ascii=False), encoding="utf-8")
    log.info("Wrote %s", out)


async def scrape_one(
    session: aiohttp.ClientSession,
    sem: asyncio.Semaphore,
    url: str,
    db: AsyncIOMotorDatabase,
    client: AsyncAnthropic,
    db_ingredients: list[dict],
) -> bool:
    """Returns True if a new recipe was saved, False if skipped or failed."""
    async with sem:
        slug = derive_slug(url)
        try:
            if await recipe_exists(db, slug):
                log.info("Already in DB, skipping %s", slug)
                return False

            html = await fetch_recipe_page(session, url)
            recipe = await parse_recipe(client, html, url)
            enrichments = await enrich_ingredients(client, db_ingredients, recipe["ingredients"])

            new_ingredients = _apply_enrichments(recipe, enrichments)
            if new_ingredients:
                await bulk_upsert_ingredients(db, new_ingredients)
            await upsert_recipe(db, recipe)
            _dump_recipe_json(recipe)
            return True
        except FatalScrapeError as exc:
            log.error("Skipping %s — fatal: %s", slug, exc)
            return False
        except TransientScrapeError as exc:
            log.warning("Skipping %s — transient (exhausted retries): %s", slug, exc)
            return False
        except Exception:
            log.exception("Unexpected error scraping %s", url)
            return False
