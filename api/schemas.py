from typing import Any

from pydantic import BaseModel, model_validator

from shared.ingredient import IngredientRecord
from shared.recipe import Ingredient, Macro, Nutrition, Recipe

# Re-export shared models so routes only import from api.schemas
__all__ = ["Ingredient", "IngredientOut", "Macro", "Nutrition", "RecipeOut", "RecipesRandomOut"]


class IngredientOut(IngredientRecord):
    model_config = {"populate_by_name": True}

    @model_validator(mode="before")
    @classmethod
    def drop_mongo_id(cls, data: Any) -> Any:
        if isinstance(data, dict):
            data.pop("_id", None)
        return data


class RecipeOut(Recipe):
    """Recipe model with MongoDB _id field stripped for API responses."""

    model_config = {"populate_by_name": True}

    @model_validator(mode="before")
    @classmethod
    def drop_mongo_id(cls, data: Any) -> Any:
        if isinstance(data, dict):
            data.pop("_id", None)
        return data


class RecipesRandomOut(BaseModel):
    seed: int
    recipes: list[RecipeOut]
