import json
import logging
import re
from datetime import datetime, timezone
from urllib.parse import urlparse

from anthropic import AsyncAnthropic, DefaultAioHttpClient
from bs4 import BeautifulSoup

from scraper.config import ANTHROPIC_API_KEY, BASE_URL

log = logging.getLogger(__name__)

_CLIENT: AsyncAnthropic | None = None


def get_client() -> AsyncAnthropic:
    global _CLIENT
    if _CLIENT is None:
        _CLIENT = AsyncAnthropic(api_key=ANTHROPIC_API_KEY, http_client=DefaultAioHttpClient())
    return _CLIENT


async def close_client() -> None:
    global _CLIENT
    if _CLIENT is not None:
        await _CLIENT.close()
        _CLIENT = None


# ─── User contribution point ────────────────────────────────────────────────
# This constant drives how Claude parses Polish ingredient strings.
# The examples here cover the most common patterns, but aniagotuje.pl may use
# formats you've seen that aren't listed — add them here to improve accuracy.
#
# TODO: Refine these examples based on actual scraped pages. Consider:
#   - Fraction quantities: "1/2 szklanki mleka", "¾ łyżeczki soli"
#   - Packed units: "200g mąki" (no space) vs "200 g mąki" (with space)
#   - Unitless count nouns: "3 jajka", "2 cebule" → unit="sztuka"
#   - Pinch/dash: "szczypta soli" → quantity=null (will be dropped from output)
#   - Compound names: "oliwa z oliwek", "ser żółty starty"
#
# Ingredients with quantity=null are excluded from the saved JSON because the
# MongoDB schema requires quantity > 0 on every recipe ingredient.
INGREDIENT_PARSING_RULES = """
Parse Polish ingredient strings into {name, quantity, unit}.
Unit MUST be "g" or "ml" — convert all other units using standard equivalents.

Only set quantity=null when there is truly NO quantity at all (e.g. "do smażenia", "do smaku",
"szczypta" with no count). If a count of pieces is given, ALWAYS estimate the weight in grams
using typical food weights — do not drop the ingredient.

Use the canonical ingredient name — omit preparation details such as cut shape,
slicing style, grating, temperature, or cooking state.
Examples: "boczek wędzony w plastrach" → "boczek wędzony", "parmezan tarty" → "parmezan",
"cebula posiekana" → "cebula", "masło roztopione" → "masło".

Common conversions:
  1 szklanka (cup)    = 240 ml  (water, milk, juice) or 120 g (flour, sugar)
  1 łyżka (tbsp)      = 15 ml   (liquids) or 12 g (flour/sugar)
  1 łyżeczka (tsp)    = 5 ml    (liquids) or 4 g  (flour/sugar)
  1 kg                = 1000 g
  1 l                 = 1000 ml

Typical piece weights (estimate when count is given):
  1 jajko             ≈ 50 g
  1 cebula            ≈ 100 g
  1 ząbek czosnku     ≈ 5 g
  1 malina            ≈ 4 g
  1 truskawka         ≈ 15 g
  1 śliwka            ≈ 30 g
  1 brzoskwinia       ≈ 150 g
  1 jabłko            ≈ 180 g
  1 banan             ≈ 120 g
  1 cytryna           ≈ 100 g
  1 limonka           ≈ 60 g
  1 marchewka         ≈ 80 g
  1 ziemniak          ≈ 150 g
  1 pomidor           ≈ 120 g
  1 papryka           ≈ 150 g
  (use common sense for anything not listed)

Examples:
- "200 g mąki pszennej"        → name="mąka pszenna",    quantity=200,   unit="g"
- "1/2 szklanki mleka"         → name="mleko",            quantity=120,   unit="ml"
- "3 łyżki oliwy"              → name="oliwa z oliwek",  quantity=45,    unit="ml"
- "1 łyżeczka soli"            → name="sól",              quantity=4,     unit="g"
- "3 jajka"                    → name="jajko",            quantity=150,   unit="g"
- "100 malin"                  → name="malina",           quantity=400,   unit="g"
- "2 marchewki"                → name="marchewka",        quantity=160,   unit="g"
- "szczypta soli"              → name="sól",              quantity=null,  unit=null
- "oliwa z oliwek do smażenia" → name="oliwa z oliwek",  quantity=null,  unit=null
"""
# ────────────────────────────────────────────────────────────────────────────

_ALLERGEN_MAP = """
Allergen IDs (EU list):
  1  = Gluten (wheat, rye, barley, oats, spelt, kamut)
  2  = Crustaceans
  3  = Eggs
  4  = Fish
  5  = Peanuts
  6  = Soy
  7  = Milk / lactose
  8  = Tree nuts (almonds, hazelnuts, walnuts, cashews, pecans, pistachios, etc.)
  9  = Celery
  10 = Mustard
  11 = Sesame seeds
  12 = Sulphur dioxide / sulphites
  13 = Lupin
  14 = Molluscs
"""

_SYSTEM_PROMPT = f"""You are a recipe data extractor for aniagotuje.pl, a Polish cooking website.

Given the readable text of a recipe page, extract structured recipe data and return it as JSON.

Fields to extract (omit any field you cannot find — do not return null values):
- name: recipe title (string)
- cooking_time: total time in minutes (integer)
- servings: number of portions (integer)
- ingredients: array of objects — see parsing rules below
- steps: ordered array of instruction strings
- image_url: absolute URL of the main recipe image (string)
- nutrition: object with kcal (number) and a nested macro object containing
  carbs, protein, fat, and optionally fiber and sugar (all numbers).
  Example: {{"kcal": 320.0, "macro": {{"carbs": 40.0, "protein": 12.0, "fat": 8.0}}}}
- allergens: array of allergen IDs present in the recipe (infer from ingredients if not stated explicitly).
  {_ALLERGEN_MAP.strip()}
- is_vegan: true if the recipe contains no meat, fish, seafood, eggs, dairy, or honey; false otherwise.
- is_gluten_free: true if the recipe contains no gluten (allergen 1); false otherwise.

Ingredient parsing rules:
{INGREDIENT_PARSING_RULES.strip()}

Return ONLY valid JSON — no markdown, no explanation."""

_RECIPE_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "cooking_time": {"type": "integer"},
        "servings": {"type": "integer"},
        "ingredients": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "quantity": {"anyOf": [{"type": "number"}, {"type": "null"}]},
                    "unit": {"enum": ["g", "ml", None]},
                },
                "required": ["name", "quantity", "unit"],
                "additionalProperties": False,
            },
        },
        "steps": {"type": "array", "items": {"type": "string"}},
        "image_url": {"type": "string"},
        "nutrition": {
            "type": "object",
            "properties": {
                "kcal": {"type": "number"},
                "macro": {
                    "type": "object",
                    "properties": {
                        "carbs": {"type": "number"},
                        "protein": {"type": "number"},
                        "fat": {"type": "number"},
                        "fiber": {"type": "number"},
                        "sugar": {"type": "number"},
                    },
                    "required": ["carbs", "protein", "fat"],
                    "additionalProperties": False,
                },
            },
            "required": ["kcal", "macro"],
            "additionalProperties": False,
        },
        "allergens": {
            "type": "array",
            "items": {"type": "integer"},
        },
        "is_vegan": {"type": "boolean"},
        "is_gluten_free": {"type": "boolean"},
    },
    "required": ["name", "ingredients", "steps"],
    "additionalProperties": False,
}


def extract_url_from_post(post: dict) -> str | None:
    for key in ("url", "permalink"):
        val = post.get(key)
        if val and val.startswith("http"):
            return val
    slug = post.get("slug")
    if slug:
        return f"{BASE_URL}/{slug}"
    return None


def derive_slug(url: str) -> str:
    parts = [p for p in urlparse(url).path.split("/") if p]
    return parts[-1] if parts else "unknown"


_DIACRITICS = str.maketrans("ąćęłńóśźżĄĆĘŁŃÓŚŹŻ", "acelnoszzACELNOSZZ")


def _ingredient_id(name: str) -> str:
    """Derive a stable lowercase ASCII id from a Polish ingredient name."""
    slug = name.lower().strip().translate(_DIACRITICS)
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"\s+", "-", slug)
    return slug or "unknown"


_VALID_UNITS = {"g", "ml", None}


def _normalise(data: dict) -> dict:
    """Align Claude's output with the MongoDB recipe schema."""
    # Drop ingredients with no measurable quantity or an invalid unit.
    # This is a defensive layer — Claude may ignore the JSON schema enum constraint.
    data["ingredients"] = [
        {
            "id": _ingredient_id(ing["name"]),
            "name": ing["name"],
            "quantity": float(ing["quantity"]),
            "unit": ing.get("unit"),
        }
        for ing in data.get("ingredients", [])
        if ing.get("quantity") is not None
        and ing["quantity"] > 0
        and ing.get("unit") in _VALID_UNITS
    ]

    # Ensure cooking_time and servings are ints
    for int_field in ("cooking_time", "servings"):
        if int_field in data:
            data[int_field] = int(data[int_field])

    # Ensure all nutrition values are floats
    nutrition = data.get("nutrition")
    if nutrition:
        if "kcal" in nutrition:
            nutrition["kcal"] = float(nutrition["kcal"])
        macro = nutrition.get("macro", {})
        for key in ("carbs", "protein", "fat", "fiber", "sugar"):
            if key in macro:
                macro[key] = float(macro[key])

    return data


def _extract_page_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "aside", "noscript"]):
        tag.decompose()
    main = soup.find("main") or soup.find("article") or soup.body
    return (main or soup).get_text(separator="\n", strip=True)


async def parse_recipe(html: str, source_url: str) -> dict | None:
    page_text = _extract_page_text(html)

    try:
        response = await get_client().messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2048,
            output_config={"effort": "low", "format": {"type": "json_schema", "schema": _RECIPE_SCHEMA}},
            system=[
                {
                    "type": "text",
                    "text": _SYSTEM_PROMPT,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            messages=[
                {
                    "role": "user",
                    "content": f"Extract recipe data:\n\n{page_text[:10_000]}",
                }
            ],
        )
    except Exception:
        log.exception("Claude API error for %s", source_url)
        return None

    text = next((b.text for b in response.content if b.type == "text"), None)
    if not text:
        log.warning("Empty Claude response for %s", source_url)
        return None

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        log.warning("Claude returned invalid JSON for %s: %.120s", source_url, text)
        return None

    data = _normalise(data)
    data["source_url"] = source_url
    data["id"] = derive_slug(source_url)
    data["scraped_at"] = datetime.now(timezone.utc).isoformat()
    return data
