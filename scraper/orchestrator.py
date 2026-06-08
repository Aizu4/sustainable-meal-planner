import asyncio
import logging

import aiohttp
from motor.motor_asyncio import AsyncIOMotorDatabase

from scraper.anthropic_client import anthropic_client
from scraper.config import (
    DB_NAME,
    MONGO_URI,
    REQUEST_CONCURRENCY,
    REQUEST_TIMEOUT,
    SCRAPE_INTERVAL_MINUTES,
    USER_AGENT,
)
from scraper.db import get_all_ingredients, get_motor_client
from scraper.parsers import extract_url_from_post
from scraper.pipeline import scrape_one
from scraper.spiders import fetch_recipe_urls

log = logging.getLogger(__name__)


async def run_once(db: AsyncIOMotorDatabase) -> None:
    headers = {"User-Agent": USER_AGENT}
    async with aiohttp.ClientSession(timeout=REQUEST_TIMEOUT, headers=headers) as session, \
            anthropic_client() as client:
        posts = await fetch_recipe_urls(session)
        urls = [u for post in posts if (u := extract_url_from_post(post))]
        log.info("Fetched %d URLs", len(urls))

        db_ingredients = await get_all_ingredients(db)
        sem = asyncio.Semaphore(REQUEST_CONCURRENCY)
        results = await asyncio.gather(
            *(scrape_one(session, sem, url, db, client, db_ingredients) for url in urls)
        )

    new_count = sum(1 for r in results if r)
    log.info("Run complete: %d new, %d skipped out of %d URLs",
             new_count, len(urls) - new_count, len(urls))


async def run_loop() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    mongo = get_motor_client(MONGO_URI)
    db = mongo[DB_NAME]
    log.info("Connected to MongoDB — scraping every %d minutes", SCRAPE_INTERVAL_MINUTES)
    try:
        while True:
            log.info("Starting scrape run")
            await run_once(db)
            log.info("Scrape run complete — sleeping %d minutes", SCRAPE_INTERVAL_MINUTES)
            await asyncio.sleep(SCRAPE_INTERVAL_MINUTES * 60)
    finally:
        mongo.close()
