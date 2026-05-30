from fastapi import APIRouter, HTTPException, Query, Request

from api.schemas import IngredientOut

router = APIRouter(prefix="/ingredients", tags=["ingredients"])


def _db(request: Request):
    return request.app.state.db


@router.get("", response_model=list[IngredientOut], summary="List ingredients")
async def list_ingredients(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(0, ge=0, description="Maximum number of results (0 = no limit)"),
    name: str | None = Query(None, description="Filter by name substring (case-insensitive)"),
):
    """Return all ingredients, optionally filtered by name substring."""
    query: dict = {}
    if name:
        query["name"] = {"$regex": name, "$options": "i"}
    cursor = _db(request).ingredients.find(query, {"_id": 0}).skip(skip).limit(limit)
    return [IngredientOut.model_validate(doc) async for doc in cursor]


@router.get("/{slug}", response_model=IngredientOut, summary="Get ingredient by slug")
async def get_ingredient(slug: str, request: Request):
    """Return a single ingredient by its slug (e.g. `maka-pszenna`)."""
    doc = await _db(request).ingredients.find_one({"id": slug}, {"_id": 0})
    if doc is None:
        raise HTTPException(status_code=404, detail="Ingredient not found")
    return IngredientOut.model_validate(doc)
