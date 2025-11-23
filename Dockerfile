# Multi-stage build для оптимизации размера образа
FROM python:3.11-slim as builder

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Создаем пользователя для безопасности
RUN groupadd -r django && useradd -r -g django django

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем requirements и устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Финальный образ
FROM python:3.11-slim

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Создаем пользователя
RUN groupadd -r django && useradd -r -g django django

# Создаем необходимые директории
RUN mkdir -p /app /app/staticfiles /app/media /app/logs && \
    chown -R django:django /app

# Копируем Python пакеты из builder stage
COPY --from=builder /root/.local /home/django/.local

# Переключаемся на пользователя django
USER django

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем исходный код
COPY --chown=django:django . .

# Добавляем .local/bin в PATH
ENV PATH=/home/django/.local/bin:$PATH

# Собираем статические файлы
RUN python manage.py collectstatic --noinput

# Создаем миграции
RUN python manage.py makemigrations

# Открываем порт
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1

# Запускаем приложение
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "--timeout", "120", "--keepalive", "5", "myblog.wsgi:application"]