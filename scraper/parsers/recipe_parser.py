import json
import logging
from datetime import datetime, timezone

from anthropic import AsyncAnthropic
from bs4 import BeautifulSoup

from scraper.config import MAX_PAGE_TEXT_CHARS, RECIPE_PARSER_MODEL
from scraper.nutrition import ingredient_id_from_name
from scraper.parsers.prompts import RECIPE_SCHEMA, SYSTEM_PROMPT
from scraper.parsers.urls import derive_slug
from shared.errors import FatalScrapeError, TransientScrapeError

log = logging.getLogger(__name__)

_VALID_UNITS = {"g", "ml", None}


def _extract_page_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "aside", "noscript"]):
        tag.decompose()
    main = soup.find("main") or soup.find("article") or soup.body
    return (main or soup).get_text(separator="\n", strip=True)


def _normalise(data: dict) -> dict:
    # Defensive: Claude may ignore the JSON schema enum constraint on unit.
    data["ingredients"] = [
        {
            "id": ingredient_id_from_name(ing["name"]),
            "name": ing["name"],
            "quantity": float(ing["quantity"]),
            "unit": ing.get("unit"),
        }
        for ing in data.get("ingredients", [])
        if ing.get("quantity") is not None
        and ing["quantity"] > 0
        and ing.get("unit") in _VALID_UNITS
    ]

    for int_field in ("cooking_time", "servings"):
        if int_field in data:
            data[int_field] = int(data[int_field])

    nutrition = data.get("nutrition")
    if nutrition:
        if "kcal" in nutrition:
            nutrition["kcal"] = float(nutrition["kcal"])
        macro = nutrition.get("macro", {})
        for key in ("carbs", "protein", "fat", "fiber", "sugar"):
            if key in macro:
                macro[key] = float(macro[key])

    return data


async def parse_recipe(client: AsyncAnthropic, html: str, source_url: str) -> dict:
    page_text = _extract_page_text(html)
    if len(page_text) > MAX_PAGE_TEXT_CHARS:
        log.warning("Page text truncated from %d to %d chars for %s",
                    len(page_text), MAX_PAGE_TEXT_CHARS, source_url)
        page_text = page_text[:MAX_PAGE_TEXT_CHARS]

    try:
        response = await client.messages.create(
            model=RECIPE_PARSER_MODEL,
            max_tokens=2048,
            output_config={"effort": "low", "format": {"type": "json_schema", "schema": RECIPE_SCHEMA}},
            system=[
                {
                    "type": "text",
                    "text": SYSTEM_PROMPT,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            messages=[
                {
                    "role": "user",
                    "content": f"Extract recipe data:\n\n{page_text}",
                }
            ],
        )
    except Exception as exc:
        raise TransientScrapeError(f"Claude parse_recipe failed for {source_url}: {exc}") from exc

    text = next((b.text for b in response.content if b.type == "text"), None)
    if not text:
        raise FatalScrapeError(f"Empty Claude response for {source_url}")

    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise FatalScrapeError(
            f"Claude returned invalid JSON for {source_url}: {text[:120]!r}"
        ) from exc

    data = _normalise(data)
    if not data["ingredients"]:
        raise FatalScrapeError(f"No valid ingredients parsed for {source_url}")

    data["source_url"] = source_url
    data["id"] = derive_slug(source_url)
    data["scraped_at"] = datetime.now(timezone.utc).isoformat()
    return data
