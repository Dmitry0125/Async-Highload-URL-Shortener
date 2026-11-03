from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker

ASYNC_SQL_DB_URL = 'sqlite+aiosqlite:///./shortlink.db'

engine = create_async_engine(ASYNC_SQL_DB_URL, connect_args={"check_same_thread": False})

async_session_local = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False
)

Base = declarative_base()
