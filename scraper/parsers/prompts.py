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

ALLERGEN_MAP = """
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

SYSTEM_PROMPT = f"""
You are a recipe data extractor for aniagotuje.pl, a Polish cooking website.

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
  {ALLERGEN_MAP.strip()}
- is_vegan: true if the recipe contains no meat, fish, seafood, eggs, dairy, or honey; false otherwise.
- is_gluten_free: true if the recipe contains no gluten (allergen 1); false otherwise.

Ingredient parsing rules:
{INGREDIENT_PARSING_RULES.strip()}

Return ONLY valid JSON — no markdown, no explanation.
"""

RECIPE_SCHEMA = {
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
