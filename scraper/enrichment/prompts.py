SYSTEM_PROMPT = """You are a nutritional data assistant for a Polish recipe database.

Given a list of recipe ingredients and a list of known ingredients from the database,
for each recipe ingredient you must:
1. Find the best matching database ingredient (by Polish name). Set match_id to its id, or null if no good match exists.
2. Estimate nutritional values per 100g or 100ml: kcal, carbs, fat, protein.
   Base estimates on standard Polish food composition data.

Return a JSON array with one entry per recipe ingredient, in the same order as the input.
Return ONLY valid JSON — no markdown, no explanation."""

ENRICHMENT_SCHEMA = {
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
