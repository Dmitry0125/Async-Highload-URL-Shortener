from fastapi import FastAPI, HTTPException, Path, Query, Body, Depends
from fastapi.responses import RedirectResponse
from hashids import Hashids
from sqlalchemy.orm import Session

from schemas import Elem, URLShortenRequest
from models import Base, Links
from database import engine, session_local

app = FastAPI() # просто объект (приложение) на основе класса FastAPI

Base.metadata.create_all(bind=engine) # Создание БД

def get_db(): # подключение к БД
    db = session_local()
    try:
        yield db
    finally:
        db.close()

hashids = Hashids(salt="my-super-secret-salt-phrase", min_length=6)

@app.post("/shorten", response_model=Elem) # без response_model будет ошибка. То есть мы всегда должны указывать модель, с которой будем работать
async def add(request: URLShortenRequest, db: Session = Depends(get_db)):
    url_to_save = str(request.long_url)

    db_link = Links(body=url_to_save, short_url="")

    db.add(db_link) #.model_dump()
    db.commit()
    db.refresh(db_link)
    
    short_hash = hashids.encode(db_link.id)
    full_short_url = f"http://127.0.0/{short_hash}"

    db_link.short_url = full_short_url
    db.commit()
    db.refresh(db_link)
    return db_link

@app.get("/all")
async def all(db: Session = Depends(get_db)):
    return db.query(Links).all()

@app.get("/{short_hash}")
async def redirect_to_long_url(short_hash: str, db: Session = Depends(get_db)):
    """
    Эндпоинт принимает короткий хэш, декодирует его в ID,
    находит оригинальную ссылку в БД и перенаправляет пользователя.
    """
    
    # 1. Декодируем хэш обратно в числовой ID
    decoded = hashids.decode(short_hash)
    
    # Если хэш невалидный (например, передали мусор), decode() вернет пустой кортеж ()
    if not decoded:
        raise HTTPException(status_code=404, detail="Неверный формат короткой ссылки")
    
    # Так как decode всегда возвращает кортеж чисел (даже если оно одно), забираем первый элемент
    db_id = decoded[0]
    
    # 2. Ищем запись в базе данных по первичному ключу (ID)
    # Это происходит мгновенно, так как по ID всегда строится индекс
    db_link = db.query(Links).filter(Links.id == db_id).first()
    
    # 3. Если ссылка не найдена в базе данных — отдаем 404 ошибку
    if db_link is None:
        raise HTTPException(status_code=404, detail="Ссылка не найдена")
    
    # 4. Делаем редирект на оригинальный URL
    # Статус 307 (Temporary Redirect) сообщает браузеру, что перенаправление временное.
    # Это заставит браузер обращаться к вашему серверу при каждом клике, что позволит вам считать статистику.
    return RedirectResponse(url=db_link.body, status_code=307)


