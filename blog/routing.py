# Импорт необходимых модулей Django для работы с WebSocket
from django.urls import re_path  # Импортируем функцию re_path для создания URL паттернов с регулярными выражениями
from . import consumers  # Импортируем модуль с потребителями (consumers) WebSocket

# Список URL паттернов для WebSocket подключений
websocket_urlpatterns = [
    re_path(r'ws/notifications/$', consumers.NotificationConsumer.as_asgi()),  # WebSocket для уведомлений (отправка real-time уведомлений пользователям)
    re_path(r'ws/chat/(?P<room_name>\w+)/$', consumers.ChatConsumer.as_asgi()),  # WebSocket для чат-комнат (динамический параметр room_name)
]