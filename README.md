# 🧠 Матрица Блог

Современный блог на Django с поддержкой API, WebSocket и Docker.

## ✨ Возможности

- **Блог система** с постами и комментариями
- **Система пользователей** с профилями
- **Real-time уведомления** через WebSocket
- **REST API** для мобильных приложений
- **JWT аутентификация**
- **Админ панель** для управления

## 🛠️ Быстрый запуск

### Docker (рекомендуется)

```bash
# Клонирование
git clone <repository-url>
cd myblog

# Настройка
cp .env.example .env

# Запуск
docker-compose up -d --build

# Инициализация
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
docker-compose exec web python manage.py collectstatic --noinput
```

### Доступ

- **Сайт**: http://localhost
- **Админка**: http://localhost/admin
- **API**: http://localhost/api/

## 📁 Структура

```
├── blog/              # Основное приложение
│   ├── api/          # REST API
│   ├── models.py     # Модели данных
│   ├── views.py      # Представления
│   └── templates/    # HTML шаблоны
├── myblog/           # Конфигурация проекта
├── docker-compose.yml
└── requirements.txt
```

## 🔧 Технологии

- Django + Django REST Framework
- PostgreSQL + Redis
- Nginx + Docker
- Celery для фоновых задач
- WebSocket через Channels

---

Современное решение для создания блогов.