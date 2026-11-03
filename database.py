import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker

# 1. Динамически считываем параметры из .env с безопасными дефолтами для локальной разработки
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
POSTGRES_DB = os.getenv("POSTGRES_DB", "database_db")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")

# 2. Формируем асинхронную строку подключения под драйвер asyncpg
DATABASE_URL = f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

# 3. Инициализируем асинхронный движок SQLAlchemy
# echo=False чтобы не засорять логи SQL-запросами
engine = create_async_engine(
    DATABASE_URL, 
    echo=False,
    pool_pre_ping=True,  # Автопроверка живых соединений в пуле
    pool_size=10,
    max_overflow=20
)

# 4. Создаем фабрику асинхронных сессий
async_session_local = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False
)

# 5. Функция-зависимость (Dependency) для FastAPI эндпоинтов
async def get_db(): # подключение к БД
    async with async_session_local() as db:
        try:
            yield db
        finally:
            await db.close()
