import pytest_asyncio
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from ..main import app, get_db
from ..database import Base

# Подключение к in-memory БД
DATABASE_URL = "sqlite+aiosqlite:///:memory:"
test_engine = create_async_engine(DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(bind=test_engine, expire_on_commit=False)


# Переопределяем зависимость на тестовую БД
async def override_get_db():
    async with TestSessionLocal() as session:
        yield session


app.dependency_overrides[get_db] = override_get_db


# Создание таблиц до начала тестов
@pytest_asyncio.fixture(scope="module", autouse=True)
async def setup_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await test_engine.dispose()


# Клиент FastAPI через httpx.AsyncClient + ASGITransport
@pytest_asyncio.fixture
async def async_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


# Тест на создание рецепта
@pytest.mark.asyncio
async def test_create_recipe(async_client):
    payload = {
        "title": "Борщ",
        "cook_time": 60,
        "ingredients": "Свёкла, капуста, мясо, картофель",
        "description": "Традиционный русский суп.",
    }
    response = await async_client.post("/recipes", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Борщ"
    assert data["views"] == 0


# Тест на получение всех рецептов
@pytest.mark.asyncio
async def test_get_all_recipes(async_client):
    response = await async_client.get("/recipes")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


# Тест на получение одного рецепта по ID
@pytest.mark.asyncio
async def test_get_recipe_by_id(async_client):
    response = await async_client.get("/recipes/1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["views"] == 1  # Был 0, стал 1 после запроса
