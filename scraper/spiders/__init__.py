import logging

import aiohttp

from scraper.config import RANDOM_ENDPOINT, URL_BATCH_CALLS
from scraper.http_client import with_retry
from scraper.parsers.urls import derive_slug, extract_url_from_post

log = logging.getLogger(__name__)


def _dedup_key(post: dict) -> str | None:
    if slug := post.get("slug"):
        return f"slug:{slug}"
    if pid := post.get("id"):
        return f"id:{pid}"
    if url := extract_url_from_post(post):
        return f"url:{derive_slug(url)}"
    return None


async def _get_json(session: aiohttp.ClientSession, url: str) -> list[dict]:
    async with session.get(url) as resp:
        resp.raise_for_status()
        return await resp.json(content_type=None)


async def fetch_recipe_urls(
    session: aiohttp.ClientSession, calls: int = URL_BATCH_CALLS
) -> list[dict]:
    """Call the random endpoint `calls` times and return deduplicated posts."""
    seen: set[str] = set()
    results: list[dict] = []
    for _ in range(calls):
        posts = await with_retry(
            lambda: _get_json(session, RANDOM_ENDPOINT),
            label=f"GET {RANDOM_ENDPOINT}",
        )
        for post in posts:
            key = _dedup_key(post)
            if key is None or key in seen:
                continue
            seen.add(key)
            results.append(post)
    log.info("Fetched %d unique posts from random endpoint (%d calls)", len(results), calls)
    return results


async def _get_text(session: aiohttp.ClientSession, url: str) -> str:
    async with session.get(url) as resp:
        resp.raise_for_status()
        return await resp.text()


async def fetch_recipe_page(session: aiohttp.ClientSession, url: str) -> str:
    return await with_retry(lambda: _get_text(session, url), label=f"GET {url}")
