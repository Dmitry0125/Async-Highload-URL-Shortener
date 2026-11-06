import pytest
from httpx import AsyncClient
from sqlalchemy.future import select
from models import Links

# Жестко фиксируем loop_scope для этого модуля тестов
pytestmark = pytest.mark.asyncio(loop_scope="module")

@pytest.mark.asyncio
async def test_shorten_url_success(client: AsyncClient):
    """Тест успешного сокращения ссылки"""
    payload = {"long_url": "https://yandex.ru"}
    
    # Отправляем виртуальный POST запрос
    response = await client.post("/shorten", json=payload)
    
    # Проверяем HTTP-статус
    assert response.status_code == 200
    
    data = response.json()
    # Проверяем, что в ответе прилетели нужные поля
    assert "id" in data
    assert data["body"] == "https://yandex.ru/"
    assert "short_url" in data
    assert data["clicks"] == 0

@pytest.mark.asyncio
async def test_redirect_to_long_url(client: AsyncClient):
    """Тест создания ссылки и последующего редиректа по хэшу"""
    # 1. Сначала создаем укороченную ссылку
    payload = {"long_url": "https://google.com"}
    create_response = await client.post("/shorten", json=payload)
    short_url = create_response.json()["short_url"]
    
    # Вытаскиваем хэш из полученной ссылки (забираем то, что после последнего слеша)
    short_hash = short_url.split("/")[-1]
    
    # 2. Пытаемся перейти по этому хэшу
    # Отключаем автоматический редирект (follow_redirects=False), чтобы поймать статус 307
    redirect_response = await client.get(f"/{short_hash}", follow_redirects=False)
    
    assert redirect_response.status_code == 307
    assert redirect_response.headers["location"] == "https://google.com/"

@pytest.mark.asyncio
async def test_rate_limiting_works(client: AsyncClient):
    """Тест работы SlowAPI: 6-й запрос на создание ссылки должен быть заблокирован"""
    payload = {"long_url": "https://habr.com"}
    
    # Отправляем 5 разрешенных запросов подряд
    for _ in range(5):
        response = await client.post("/shorten", json=payload)
        assert response.status_code == 200
        
    # 6-й запрос должен наткнуться на лимит
    bad_response = await client.post("/shorten", json=payload)
    
    assert bad_response.status_code == 429
    assert "Rate limit exceeded" in bad_response.json()["error"]
