import os
import pytest
import redis.asyncio as aioredis
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from httpx import AsyncClient, ASGITransport

from models import Base
from database import get_db
import database
from main import app

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine_test = create_async_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
async_session_test = async_sessionmaker(bind=engine_test, class_=AsyncSession, expire_on_commit=False)

@pytest.fixture(scope="function", autouse=True)
async def prepare_database():
    """Перед каждым тестом создает чистые таблицы, после — удаляет их"""
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture(scope="function")
async def db_session():
    """Фикстура для работы с тестовой сессией БД"""
    async with async_session_test() as session:
        yield session

@pytest.fixture(scope="function")
async def client(db_session):
    """Асинхронный HTTP-клиент, который полностью изолирует и БД, и Redis под текущий тест"""
    
    redis_host = os.getenv("REDIS_HOST", "localhost")
    redis_port = os.getenv("REDIS_PORT", "6379")
    test_redis = aioredis.from_url(f"redis://{redis_host}:{redis_port}", decode_responses=True)
    
    await test_redis.flushdb()
    
    old_redis = database.redis_client
    database.redis_client = test_redis

    # Подменяем базу данных
    async def _get_test_db():
        yield db_session
    app.dependency_overrides[get_db] = _get_test_db
    
    # Запускаем виртуальный клиент для отправки запросов
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
        
    # После окончания теста возвращаем всё назад и закрываем соединения
    app.dependency_overrides.clear()
    await test_redis.aclose()
    database.redis_client = old_redis
