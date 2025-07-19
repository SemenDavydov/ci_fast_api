from contextlib import asynccontextmanager
from typing import List

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from . import crud
from .database import Base, SessionLocal, engine
from .schemas import RecipeCreate, RecipeRead


# инициализация при запуске приложения
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Запуск приложения. Инициализация БД...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Таблицы БД созданы.")
    yield
    print("Завершение работы приложения.")


# Создание FastAPI-приложения с указанием lifespan
app = FastAPI(
    title="Кулинарная книга API",
    description="API для управления рецептами: создание,"
                " просмотр, детальная информация.",
    version="1.0.0",
    lifespan=lifespan,
)


# Получение сессии базы данных
async def get_db() -> AsyncSession:
    async with SessionLocal() as session:
        yield session


# Получение всех рецептов (сортировка по просмотрам и cook_time)
@app.get(
    "/recipes",
    response_model=List[RecipeRead],
    summary="Получить список всех рецептов",
    description="Список всех рецептов, отсортированных по количеству"
                " просмотров и времени приготовления.",
)
async def get_recipes(db: AsyncSession = Depends(get_db)):
    return await crud.get_all_recipes(db)


# Получение одного рецепта по ID (и +1 к просмотрам)
@app.get(
    "/recipes/{recipe_id}",
    response_model=RecipeRead,
    summary="Получить рецепт по ID",
    description="Детальная информация о рецепте по его ID."
                " Количество просмотров увеличивается.",
)
async def get_recipe(recipe_id: int, db: AsyncSession = Depends(get_db)):
    recipe = await crud.get_recipe_by_id(recipe_id, db)
    if not recipe:
        raise HTTPException(status_code=404, detail="Рецепт не найден")
    return recipe


# Создание нового рецепта
@app.post(
    "/recipes",
    summary="Создать новый рецепт",
    description="Создание нового рецепта."
                " Передай название, время, ингредиенты и описание.",
)
async def create_recipe(recipe: RecipeCreate, db: AsyncSession = Depends(get_db)):
    return await crud.create_recipe(recipe, db)
