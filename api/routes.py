import random as _random

from fastapi import APIRouter, HTTPException, Query, Request

from api.schemas import RecipeOut, RecipesRandomOut

router = APIRouter(prefix="/recipes", tags=["recipes"])


def _db(request: Request):
    return request.app.state.db


def _build_query(
    name: str | None,
    allergies: str | None,
    vegan: bool | None,
    gluten_free: bool | None,
) -> dict:
    query: dict = {}
    if name:
        query["name"] = {"$regex": name, "$options": "i"}
    if allergies:
        ids = [int(a) for a in allergies.split(",") if a.strip()]
        if ids:
            query["allergens"] = {"$nin": ids}
    if vegan is not None:
        query["is_vegan"] = vegan
    if gluten_free is not None:
        query["is_gluten_free"] = gluten_free
    return query


@router.get("", response_model=list[RecipeOut], summary="List recipes")
async def list_recipes(
    request: Request,
    skip: int = Query(0, ge=0, description="Number of recipes to skip"),
    limit: int = Query(0, ge=0, description="Maximum number of recipes to return (0 = no limit)"),
    name: str | None = Query(None, description="Filter by name substring (case-insensitive)"),
    allergies: str | None = Query(None, description="Comma-separated allergen IDs to exclude (e.g. 1,3,4)"),
    vegan: bool | None = Query(None, description="true = vegan only, false = non-vegan only, omit = both"),
    gluten_free: bool | None = Query(None, description="true = gluten-free only, false = with gluten only, omit = both"),
):
    """Return a paginated list of recipes with optional dietary and allergen filters."""
    query = _build_query(name, allergies, vegan, gluten_free)
    cursor = _db(request).recipes.find(query, {"_id": 0}).skip(skip).limit(limit)
    return [RecipeOut.model_validate(doc) async for doc in cursor]


@router.get("/random", response_model=RecipesRandomOut, summary="Shuffled recipes")
async def random_recipes(
    request: Request,
    seed: int | None = Query(None, description="Random seed for reproducible shuffle; generated randomly if omitted"),
    skip: int = Query(0, ge=0, description="Number of recipes to skip in the shuffled list"),
    limit: int = Query(1, ge=1, description="Number of recipes to return from the shuffled list"),
    allergies: str | None = Query(None, description="Comma-separated allergen IDs to exclude (e.g. 1,3,4)"),
    vegan: bool | None = Query(None, description="true = vegan only, false = non-vegan only, omit = both"),
    gluten_free: bool | None = Query(None, description="true = gluten-free only, false = with gluten only, omit = both"),
):
    """Return recipes in a seeded-random order. Same seed always produces the same shuffle."""
    if seed is None:
        seed = _random.randint(0, 2**32 - 1)

    query = _build_query(None, allergies, vegan, gluten_free)
    ids = [
        doc["id"]
        async for doc in _db(request).recipes.find(query, {"id": 1, "_id": 0}).sort("id", 1)
    ]
    if not ids:
        raise HTTPException(status_code=404, detail="No recipes match the given filters")

    rng = _random.Random(seed)
    rng.shuffle(ids)
    page_ids = ids[skip: skip + limit]

    docs = {
        doc["id"]: doc
        async for doc in _db(request).recipes.find(
            {"id": {"$in": page_ids}}, {"_id": 0}
        )
    }
    recipes = [RecipeOut.model_validate(docs[id_]) for id_ in page_ids if id_ in docs]
    return RecipesRandomOut(seed=seed, recipes=recipes)


@router.get("/search", response_model=list[RecipeOut], summary="Search recipes")
async def search_recipes(
    request: Request,
    q: str = Query(..., min_length=1, description="Search term matched against recipe names"),
    limit: int = Query(20, ge=1, description="Maximum number of results"),
):
    """Search recipes by name (case-insensitive substring match)."""
    cursor = _db(request).recipes.find(
        {"name": {"$regex": q, "$options": "i"}},
        {"_id": 0},
    ).limit(limit)
    return [RecipeOut.model_validate(doc) async for doc in cursor]


@router.get("/{slug}", response_model=RecipeOut, summary="Get recipe by slug")
async def get_recipe(slug: str, request: Request):
    """Return a single recipe by its slug identifier (e.g. `pierogi-ze-szpinakiem`)."""
    doc = await _db(request).recipes.find_one({"id": slug}, {"_id": 0})
    if doc is None:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return RecipeOut.model_validate(doc)
