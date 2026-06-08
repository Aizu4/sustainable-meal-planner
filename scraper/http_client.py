import asyncio
import logging
from typing import Awaitable, Callable, TypeVar

import aiohttp

from scraper.config import HTTP_BACKOFF_BASE_SECONDS, HTTP_MAX_RETRIES
from shared.errors import FatalScrapeError, TransientScrapeError

log = logging.getLogger(__name__)

T = TypeVar("T")


def classify_http_error(exc: BaseException) -> Exception:
    if isinstance(exc, aiohttp.ClientResponseError):
        if 400 <= exc.status < 500:
            return FatalScrapeError(f"HTTP {exc.status} for {exc.request_info.url}")
        return TransientScrapeError(f"HTTP {exc.status} for {exc.request_info.url}")
    if isinstance(exc, (aiohttp.ClientConnectionError, asyncio.TimeoutError)):
        return TransientScrapeError(str(exc) or exc.__class__.__name__)
    return exc


async def with_retry(
    op: Callable[[], Awaitable[T]],
    *,
    label: str,
    max_retries: int = HTTP_MAX_RETRIES,
    base_delay: float = HTTP_BACKOFF_BASE_SECONDS,
) -> T:
    attempt = 0
    while True:
        try:
            return await op()
        except FatalScrapeError:
            raise
        except Exception as exc:
            classified = classify_http_error(exc)
            if isinstance(classified, FatalScrapeError):
                raise classified from exc
            attempt += 1
            if attempt > max_retries:
                if isinstance(classified, TransientScrapeError):
                    raise classified from exc
                raise TransientScrapeError(f"{label}: {exc}") from exc
            delay = base_delay * (2 ** (attempt - 1))
            log.warning("%s failed (attempt %d/%d): %s — retrying in %.1fs",
                        label, attempt, max_retries, exc, delay)
            await asyncio.sleep(delay)
