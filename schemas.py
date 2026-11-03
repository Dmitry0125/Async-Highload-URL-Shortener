from pydantic import BaseModel, HttpUrl

class Elem(BaseModel):
    id: int
    body: str
    short_url: str
    clicks: int

    class Config:
        from_attributes = True

class URLShortenRequest(BaseModel):
    # Pydantic автоматически проверит, что строка начинается с http/https 
    # и является валидным URL-адресом. Если нет — FastAPI сам вернет 422 ошибку.
    long_url: HttpUrl 