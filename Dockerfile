# Базовый образ с установленным Python 3.13
FROM python:3.13-slim

# Отключаем буферизацию логов Python (чтобы они сразу выводились в консоль Docker) 
# и запрещаем pip создавать кэш-файлы .pyc
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# Копируем файл зависимостей
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь остальной код проекта в контейнер
COPY . .

# Команда для запуска сервера Uvicorn внутри контейнера
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]