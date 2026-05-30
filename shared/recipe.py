"""
Canonical Pydantic models for a recipe document.

These models are derived from mongodb/schemas/recipe_schema.js and must stay in sync
with it. The JSON schema is the source of truth — update it first, then update here.

Constraint mapping (MongoDB → Pydantic):
  bsonType: "string"              → str
  bsonType: "int"                 → int
  bsonType: "double"              → float
  bsonType: "bool"                → bool
  required: [...]                 → field with no default
  minimum: N                      → Field(ge=N)
  exclusiveMinimum: true          → Field(gt=0)   (MongoDB always pairs with minimum: 0)
  minItems: N                     → Field(min_length=N)
  optional field                  → T | None = None
"""

from typing import Literal

from pydantic import BaseModel, Field

from shared.ingredient import IngredientNutrition


class Ingredient(BaseModel):
    # required: ["id", "name", "quantity"]
    id: str
    name: str
    quantity: float = Field(gt=0)           # minimum: 0, exclusiveMinimum: true
    unit: Literal["g", "ml"] | None = None  # enum: ["g", "ml"]
    ingredient_id: str | None = None
    nutrition: IngredientNutrition | None = None


class Macro(BaseModel):
    # required: ["carbs", "protein", "fat"]
    carbs: float = Field(ge=0)
    protein: float = Field(ge=0)
    fat: float = Field(ge=0)
    fiber: float | None = Field(default=None, ge=0)
    sugar: float | None = Field(default=None, ge=0)


class Nutrition(BaseModel):
    # required: ["kcal", "macro"]
    kcal: float = Field(ge=0)
    macro: Macro


class Recipe(BaseModel):
    # required: ["id", "name", "ingredients"]
    id: str
    name: str
    ingredients: list[Ingredient] = Field(min_length=1)  # minItems: 1

    source_url: str | None = None
    image_url: str | None = None
    cooking_time: int | None = Field(default=None, ge=0)   # minimum: 0
    servings: int | None = Field(default=None, ge=1)        # minimum: 1
    is_vegan: bool | None = None
    is_gluten_free: bool | None = None
    allergens: list[int] | None = None
    scraped_at: str | None = None
    steps: list[str] = []
    nutrition: Nutrition | None = None
