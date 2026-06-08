import re

_DIACRITICS = str.maketrans("ąćęłńóśźżĄĆĘŁŃÓŚŹŻ", "acelnoszzACELNOSZZ")

_MACRO_KEYS = ("kcal", "carbs", "fat", "protein")


def ingredient_id_from_name(name: str) -> str:
    """Stable lowercase ASCII id from a Polish ingredient name."""
    slug = name.lower().strip().translate(_DIACRITICS)
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"\s+", "-", slug)
    return slug or "unknown"


def per_ingredient_nutrition(quantity: float, nutrition_per_100: dict) -> dict[str, float]:
    factor = quantity / 100
    return {key: round(factor * float(nutrition_per_100.get(key, 0)), 2) for key in _MACRO_KEYS}


def nutrition_per_100_floats(nutrition_per_100: dict) -> dict[str, float]:
    return {key: float(nutrition_per_100.get(key, 0)) for key in _MACRO_KEYS}
