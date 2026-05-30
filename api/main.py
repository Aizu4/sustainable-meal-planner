from contextlib import asynccontextmanager

from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient

from api.config import DB_NAME, MONGO_URI
from api.ingredient_routes import router as ingredients_router
from api.routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    client = AsyncIOMotorClient(MONGO_URI)
    app.state.db = client[DB_NAME]
    yield
    client.close()


app = FastAPI(
    title="Sustainable Meal Planner",
    description="API for browsing recipes scraped from aniagotuje.pl.",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)
app.include_router(router)
app.include_router(ingredients_router)
