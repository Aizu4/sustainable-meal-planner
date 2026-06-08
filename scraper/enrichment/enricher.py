import json
import logging

from anthropic import AsyncAnthropic

from scraper.config import INGREDIENT_ENRICHER_MODEL
from scraper.enrichment.prompts import ENRICHMENT_SCHEMA, SYSTEM_PROMPT
from shared.errors import FatalScrapeError, TransientScrapeError

log = logging.getLogger(__name__)


async def enrich_ingredients(
    client: AsyncAnthropic,
    db_ingredients: list[dict],
    recipe_ingredients: list[dict],
) -> list[dict]:
    if not recipe_ingredients:
        return []

    db_list = "\n".join(f"- id={ing['id']}, name={ing['name']}" for ing in db_ingredients)
    recipe_list = "\n".join(
        f"- name={ing['name']}, quantity={ing['quantity']} {ing.get('unit') or ''}"
        for ing in recipe_ingredients
    )
    user_content = f"Recipe ingredients:\n{recipe_list}\n\nDatabase ingredients:\n{db_list or '(empty)'}"

    try:
        response = await client.messages.create(
            model=INGREDIENT_ENRICHER_MODEL,
            max_tokens=1024,
            output_config={
                "format": {"type": "json_schema", "schema": ENRICHMENT_SCHEMA},
            },
            system=[
                {
                    "type": "text",
                    "text": SYSTEM_PROMPT,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            messages=[{"role": "user", "content": user_content}],
        )
    except Exception as exc:
        raise TransientScrapeError(f"Claude enrich_ingredients failed: {exc}") from exc

    text = next((b.text for b in response.content if b.type == "text"), None)
    if not text:
        raise FatalScrapeError("Empty Claude response during ingredient enrichment")

    try:
        results = json.loads(text)
    except json.JSONDecodeError as exc:
        raise FatalScrapeError(
            f"Claude returned invalid JSON during enrichment: {text[:120]!r}"
        ) from exc

    if len(results) != len(recipe_ingredients):
        raise FatalScrapeError(
            f"Enrichment returned {len(results)} results for {len(recipe_ingredients)} ingredients"
        )

    return results
