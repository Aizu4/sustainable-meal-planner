import logging

import aiohttp

from scraper.config import RANDOM_ENDPOINT

log = logging.getLogger(__name__)


async def fetch_recipe_urls(session: aiohttp.ClientSession, calls: int = 5) -> list[dict]:
    """Call the random endpoint `calls` times and return deduplicated posts."""
    seen: set[str] = set()
    results: list[dict] = []
    for _ in range(calls):
        async with session.get(RANDOM_ENDPOINT) as resp:
            resp.raise_for_status()
            posts = await resp.json(content_type=None)
        for post in posts:
            key = post.get("slug") or post.get("id") or post.get("url") or str(post)
            if key not in seen:
                seen.add(key)
                results.append(post)
    log.info("Fetched %d unique posts from random endpoint (%d calls)", len(results), calls)
    return results


async def fetch_recipe_page(session: aiohttp.ClientSession, url: str) -> str:
    async with session.get(url) as resp:
        resp.raise_for_status()
        return await resp.text()
