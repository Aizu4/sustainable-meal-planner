from pydantic import BaseModel, Field


class IngredientNutrition(BaseModel):
    kcal: float = Field(ge=0)
    carbs: float = Field(ge=0)
    fat: float = Field(ge=0)
    protein: float = Field(ge=0)


class IngredientRecord(BaseModel):
    id: str
    name: str
    nutrition_per_100: IngredientNutrition
