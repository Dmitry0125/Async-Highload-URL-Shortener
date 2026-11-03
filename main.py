import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from hashids import Hashids
from dotenv import load_dotenv

from schemas import Elem, URLShortenRequest
from models import Base, Links
from database import engine, async_session_local

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(lifespan=lifespan) # просто объект (приложение) на основе класса FastAPI

# Base.metadata.create_all(bind=engine) # Создание БД

async def get_db(): # подключение к БД
    async with async_session_local() as db:
        try:
            yield db
        finally:
            await db.close()

SECRET_SALT = os.environ.get("HASHIDS_SALT", "fallback-salt")
hashids = Hashids(salt=SECRET_SALT, min_length=6)

@app.post("/shorten", response_model=Elem) # без response_model будет ошибка. То есть мы всегда должны указывать модель, с которой будем работать
async def add(request: URLShortenRequest, db: AsyncSession = Depends(get_db)):
    """
    Короткую ссылку формируем на лету, отдавая её только пользователю. В самой БД она не хранится, 
    а при получении короткой ссылки в методе @app.get("/{short_hash}") на лету расшифровываем id, ищем в БД и отдаём результат
    """
    url_to_save = str(request.long_url)

    db_link = Links(body=url_to_save)
    db.add(db_link) #.model_dump()
    await db.commit()
    await db.refresh(db_link) # для объекта db_link будут подтянуты поля id и clicks
    
    short_hash = hashids.encode(db_link.id)

    return Elem(
        id=db_link.id,
        body=db_link.body,
        short_url=f"http://127.0.0.1/{short_hash}",
        clicks = db_link.clicks
    )

@app.get("/all")
async def get_all_links(db: AsyncSession = Depends(get_db)):
    """
    Служебный метод чтобы смотреть что находится в БД
    """
    result = await db.execute(select(Links)) # из сырого контейнера с табличными строками (await db.execute(...)) выбираем SELECT * FROM links (select(Links)) - получается двумерный массив строк
    all_results = result.scalars().all() # преобразуем каждую строку в чистый Python-объект класса Links (.scalars()) и собирает все преобразованные объекты в Python список (.all())
    if len(all_results)==0:
        return "База данных пока пустая"
    return all_results
    

@app.get("/{short_hash}")
async def redirect_to_long_url(short_hash: str, db: AsyncSession = Depends(get_db)):

    decoded = hashids.decode(short_hash)
    if not decoded:
        raise HTTPException(status_code=404, detail="Неверный формат короткой ссылки")
    
    db_id = decoded[0]
    
    result = await db.execute(select(Links).where(Links.id == db_id))
    db_link = result.scalars().first()
    
    if db_link is None:
        raise HTTPException(status_code=404, detail="Ссылка не найдена")

    db_link.clicks +=1

    await db.commit()
    
    return RedirectResponse(url=db_link.body, status_code=307)

@app.get("/stat/{short_hash}")
async def stat_clicks(short_hash: str, db: AsyncSession = Depends(get_db)):
    decoded = hashids.decode(short_hash)
    if not decoded:
        raise HTTPException(status_code=404, detail="Неверный формат короткой ссылки")
        
    db_id = decoded[0]
    
    result = await db.execute(select(Links).where(Links.id == db_id))

    db_link = result.scalars().first()

    if db_link is None:
            raise HTTPException(status_code=404, detail="Ссылка не найдена")

    return {
        "short_hash": short_hash,
        "original_url": db_link.body,
        "clicks": db_link.clicks  # Обращаемся напрямую к свойству объекта!
    }

