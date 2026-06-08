from contextlib import asynccontextmanager
from typing import AsyncIterator

from anthropic import AsyncAnthropic, DefaultAioHttpClient

from scraper.config import ANTHROPIC_API_KEY


@asynccontextmanager
async def anthropic_client() -> AsyncIterator[AsyncAnthropic]:
    client = AsyncAnthropic(api_key=ANTHROPIC_API_KEY, http_client=DefaultAioHttpClient())
    try:
        yield client
    finally:
        await client.close()
