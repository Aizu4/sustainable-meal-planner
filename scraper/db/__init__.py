import logging
from typing import Type

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pydantic import BaseModel, ValidationError
from pymongo import UpdateOne

from shared.ingredient import IngredientRecord
from shared.recipe import Recipe

log = logging.getLogger(__name__)


def get_motor_client(uri: str) -> AsyncIOMotorClient:
    return AsyncIOMotorClient(uri)


def _validate(model: Type[BaseModel], data: dict, kind: str) -> bool:
    try:
        model.model_validate(data)
        return True
    except ValidationError as exc:
        log.error("%s %s failed Pydantic validation — skipping upsert:\n%s",
                  kind, data.get("id"), exc)
        return False


async def recipe_exists(db: AsyncIOMotorDatabase, slug: str) -> bool:
    return await db.recipes.count_documents({"id": slug}, limit=1) > 0


async def upsert_recipe(db: AsyncIOMotorDatabase, recipe: dict) -> None:
    if not _validate(Recipe, recipe, "Recipe"):
        return
    await db.recipes.update_one(
        {"id": recipe["id"]},
        {"$set": recipe},
        upsert=True,
    )
    log.info("Upserted recipe %s", recipe["id"])


async def get_all_ingredients(db: AsyncIOMotorDatabase) -> list[dict]:
    return [doc async for doc in db.ingredients.find({}, {"id": 1, "name": 1, "_id": 0})]


async def upsert_ingredient(db: AsyncIOMotorDatabase, ingredient: dict) -> None:
    if not _validate(IngredientRecord, ingredient, "Ingredient"):
        return
    await db.ingredients.update_one(
        {"id": ingredient["id"]},
        {"$set": ingredient},
        upsert=True,
    )
    log.info("Upserted ingredient %s", ingredient["id"])


async def bulk_upsert_ingredients(db: AsyncIOMotorDatabase, ingredients: list[dict]) -> None:
    valid = [ing for ing in ingredients if _validate(IngredientRecord, ing, "Ingredient")]
    if not valid:
        return
    ops = [UpdateOne({"id": ing["id"]}, {"$set": ing}, upsert=True) for ing in valid]
    await db.ingredients.bulk_write(ops, ordered=False)
    log.info("Bulk-upserted %d ingredients", len(valid))
