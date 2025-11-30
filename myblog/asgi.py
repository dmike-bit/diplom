"""
Конфигурация ASGI для проекта myblog.

Этот файл предоставляет ASGI приложение как модульную переменную с именем ``application``.

Для получения дополнительной информации по этому файлу см.
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os  # Импортируем модуль os для работы с переменными окружения
from django.core.asgi import get_asgi_application  # Импортируем функцию для создания ASGI приложения Django
from channels.routing import ProtocolTypeRouter, URLRouter  # Импортируем маршрутизаторы Django Channels для разных типов протоколов
from channels.auth import AuthMiddlewareStack  # Импортируем middleware для аутентификации в WebSocket каналах
from channels.security.websocket import AllowedHostsOriginValidator  # Импортием валидатор безопасности для WebSocket

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myblog.settings')  # Устанавливаем модуль настроек Django по умолчанию

# Инициализация ASGI приложения Django заранее, чтобы убедиться, что AppRegistry
# заполнен перед импортом кода, который может в нем нуждаться.
django_asgi_app = get_asgi_application()  # Создаем основное ASGI приложение Django

from blog.routing import websocket_urlpatterns  # Импортируем URL паттерны WebSocket из нашего приложения blog

application = ProtocolTypeRouter({  # Создаем основное ASGI приложение с поддержкой разных протоколов
    "http": django_asgi_app,  # Обработчик HTTP запросов (традиционные веб-запросы)
    "websocket": AllowedHostsOriginValidator(  # Обработчик WebSocket соединений с проверкой разрешенных хостов
        AuthMiddlewareStack(  # Стек middleware для аутентификации WebSocket соединений
            URLRouter(  # Маршрутизатор для WebSocket URL паттернов
                websocket_urlpatterns  # Список WebSocket URL паттернов из приложения blog
            )
        )
    ),
})
