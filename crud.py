from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from .models import Recipe
from .schemas import RecipeCreate


async def get_all_recipes(db: AsyncSession):
    stmt = select(Recipe).order_by(Recipe.views.desc(), Recipe.cook_time)
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_recipe_by_id(recipe_id: int, db: AsyncSession):
    recipe = await db.get(Recipe, recipe_id)
    if recipe:
        recipe.views += 1
        await db.commit()
        await db.refresh(recipe)
    return recipe


async def create_recipe(recipe_data: RecipeCreate, db: AsyncSession):
    recipe = Recipe(**recipe_data.dict())
    db.add(recipe)
    await db.commit()
    await db.refresh(recipe)
    return recipe
