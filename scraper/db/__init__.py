import logging

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pydantic import ValidationError

from shared.ingredient import IngredientRecord
from shared.recipe import Recipe

log = logging.getLogger(__name__)


def get_motor_client(uri: str) -> AsyncIOMotorClient:
    return AsyncIOMotorClient(uri)


async def recipe_exists(db: AsyncIOMotorDatabase, slug: str) -> bool:
    return await db.recipes.count_documents({"id": slug}, limit=1) > 0


async def upsert_recipe(db: AsyncIOMotorDatabase, recipe: dict) -> None:
    # First pass: Pydantic validation (Python-side)
    try:
        Recipe.model_validate(recipe)
    except ValidationError as exc:
        log.error("Recipe %s failed Pydantic validation — skipping upsert:\n%s", recipe.get("id"), exc)
        return

    # Second pass: MongoDB validator runs on write
    await db.recipes.update_one(
        {"id": recipe["id"]},
        {"$set": recipe},
        upsert=True,
    )
    log.info("Upserted %s", recipe["id"])


async def get_all_ingredients(db: AsyncIOMotorDatabase) -> list[dict]:
    return [doc async for doc in db.ingredients.find({}, {"id": 1, "name": 1, "_id": 0})]


async def upsert_ingredient(db: AsyncIOMotorDatabase, ingredient: dict) -> None:
    try:
        IngredientRecord.model_validate(ingredient)
    except ValidationError as exc:
        log.error("Ingredient %s failed validation — skipping: %s", ingredient.get("id"), exc)
        return
    await db.ingredients.update_one(
        {"id": ingredient["id"]},
        {"$set": ingredient},
        upsert=True,
    )
    log.info("Upserted ingredient %s", ingredient["id"])
