# Базовый образ с установленным Python 3.11
FROM python:3.11-slim

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