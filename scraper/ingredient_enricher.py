import json
import logging

from anthropic import AsyncAnthropic

log = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You are a nutritional data assistant for a Polish recipe database.

Given a list of recipe ingredients and a list of known ingredients from the database,
for each recipe ingredient you must:
1. Find the best matching database ingredient (by Polish name). Set match_id to its id, or null if no good match exists.
2. Estimate nutritional values per 100g or 100ml: kcal, carbs, fat, protein.
   Base estimates on standard Polish food composition data.

Return a JSON array with one entry per recipe ingredient, in the same order as the input.
Return ONLY valid JSON — no markdown, no explanation."""

_ENRICHMENT_SCHEMA = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "match_id": {"anyOf": [{"type": "string"}, {"type": "null"}]},
            "nutrition_per_100": {
                "type": "object",
                "properties": {
                    "kcal":    {"type": "number"},
                    "carbs":   {"type": "number"},
                    "fat":     {"type": "number"},
                    "protein": {"type": "number"},
                },
                "required": ["kcal", "carbs", "fat", "protein"],
                "additionalProperties": False,
            },
        },
        "required": ["name", "match_id", "nutrition_per_100"],
        "additionalProperties": False,
    },
}


async def enrich_ingredients(
    client: AsyncAnthropic,
    db_ingredients: list[dict],
    recipe_ingredients: list[dict],
) -> list[dict]:
    """Return enrichment data for each recipe ingredient (same order as input).

    Each result: {"name": str, "match_id": str|None, "nutrition_per_100": {kcal, carbs, fat, protein}}
    """
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
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            output_config={
                "format": {"type": "json_schema", "schema": _ENRICHMENT_SCHEMA},
            },
            system=[
                {
                    "type": "text",
                    "text": _SYSTEM_PROMPT,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            messages=[{"role": "user", "content": user_content}],
        )
    except Exception:
        log.exception("Claude API error during ingredient enrichment")
        return []

    text = next((b.text for b in response.content if b.type == "text"), None)
    if not text:
        log.warning("Empty Claude response during ingredient enrichment")
        return []

    try:
        results = json.loads(text)
    except json.JSONDecodeError:
        log.warning("Claude returned invalid JSON during enrichment: %.120s", text)
        return []

    if len(results) != len(recipe_ingredients):
        log.warning(
            "Enrichment returned %d results for %d ingredients",
            len(results), len(recipe_ingredients),
        )

    return results
