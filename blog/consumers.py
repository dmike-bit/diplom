import json  # Импортируем модуль для работы с JSON данными
from channels.generic.websocket import AsyncWebsocketConsumer  # Импортируем базовый класс для асинхронных WebSocket потребителей
from channels.db import database_sync_to_async  # Импортируем декоратор для синхронных операций с БД в асинхронных потребителях
from django.contrib.auth.models import User  # Импортируем модель пользователя Django
from .models import Notification  # Импортируем модель уведомлений

# Потребитель WebSocket для real-time уведомлений
class NotificationConsumer(AsyncWebsocketConsumer):  # Класс для обработки WebSocket подключений уведомлений
    async def connect(self):  # Метод вызывается при подключении WebSocket
        self.room_group_name = f'notifications_{self.scope["user"].id}'  # Создаем уникальное имя группы для каждого пользователя
        
        # Присоединяемся к группе комнат
        await self.channel_layer.group_add(  # Добавляем пользователя в группу для широковещательных сообщений
            self.room_group_name,  # Имя группы
            self.channel_name  # Имя канала текущего подключения
        )
        
        await self.accept()  # Принимаем WebSocket соединение

    async def disconnect(self, close_code):  # Метод вызывается при отключении WebSocket
        # Выходим из группы комнат
        await self.channel_layer.group_discard(  # Удаляем пользователя из группы
            self.room_group_name,  # Имя группы
            self.channel_name  # Имя канала
        )

    async def receive(self, text_data):  # Метод для получения сообщений от WebSocket клиента
        text_data_json = json.loads(text_data)  # Парсим JSON данные из входящего сообщения
        message_type = text_data_json['type']  # Извлекаем тип сообщения
        
        if message_type == 'get_notifications':  # Если клиент запрашивает уведомления
            notifications = await self.get_user_notifications()  # Получаем уведомления пользователя
            await self.send(text_data=json.dumps({  # Отправляем ответ клиенту
                'type': 'notifications',  # Тип ответа
                'notifications': notifications  # Данные уведомлений
            }))

    async def send_notification(self, event):  # Метод для отправки уведомлений (вызывается группой)
        notification = event['notification']  # Получаем данные уведомления из события
        
        # Отправляем сообщение в WebSocket
        await self.send(text_data=json.dumps({  # Отправляем JSON сообщение клиенту
            'type': 'new_notification',  # Тип сообщения - новое уведомление
            'notification': notification  # Данные уведомления
        }))

    @database_sync_to_async  # Декоратор для безопасного доступа к БД из асинхронного кода
    def get_user_notifications(self):  # Метод получения уведомлений пользователя из БД
        user = self.scope["user"]  # Получаем пользователя из scope WebSocket соединения
        if user.is_anonymous:  # Проверяем, аутентифицирован ли пользователь
            return []  # Если анонимный, возвращаем пустой список
        
        notifications = Notification.objects.filter(  # Запрос к базе данных уведомлений
            user=user,  # Фильтруем по текущему пользователю
            is_read=False  # Только непрочитанные уведомления
        ).order_by('-created_date')[:10]  # Сортируем по дате создания и берем последние 10
        
        return [  # Возвращаем список словарей с данными уведомлений
            {
                'id': n.id,  # ID уведомления
                'title': n.title,  # Заголовок уведомления
                'message': n.message,  # Сообщение уведомления
                'type': n.notification_type,  # Тип уведомления
                'created_date': n.created_date.isoformat(),  # Дата создания в ISO формате
                'is_read': n.is_read  # Статус прочитанности
            }
            for n in notifications  # Проходим по всем уведомлениям
        ]

# Потребитель WebSocket для чата
class ChatConsumer(AsyncWebsocketConsumer):  # Класс для обработки WebSocket подключений чата
    async def connect(self):  # Метод вызывается при подключении к чат-комнате
        self.room_name = self.scope['url_route']['kwargs']['room_name']  # Извлекаем имя комнаты из URL маршрута
        self.room_group_name = f'chat_{self.room_name}'  # Создаем имя группы чата

        # Присоединяемся к группе чата
        await self.channel_layer.group_add(  # Добавляем пользователя в группу чат-комнаты
            self.room_group_name,  # Имя группы чата
            self.channel_name  # Имя канала
        )

        await self.accept()  # Принимаем WebSocket соединение

    async def disconnect(self, close_code):  # Метод вызывается при отключении от чата
        # Выходим из группы чата
        await self.channel_layer.group_discard(  # Удаляем пользователя из группы чата
            self.room_group_name,  # Имя группы
            self.channel_name  # Имя канала
        )

    # Получаем сообщение от WebSocket клиента
    async def receive(self, text_data):  # Метод для обработки входящих сообщений чата
        text_data_json = json.loads(text_data)  # Парсим JSON данные сообщения
        message = text_data_json['message']  # Извлекаем текст сообщения
        username = self.scope["user"].username if self.scope["user"].is_authenticated else "Anonymous"  # Получаем имя пользователя или "Anonymous"

        # Отправляем сообщение в группу чата
        await self.channel_layer.group_send(  # Отправляем сообщение всем участникам чата
            self.room_group_name,  # Имя группы чата
            {  # Данные сообщения
                'type': 'chat_message',  # Тип события
                'message': message,  # Текст сообщения
                'username': username  # Имя отправителя
            }
        )

    # Получаем сообщение от группы чата
    async def chat_message(self, event):  # Метод для обработки сообщений от группы
        message = event['message']  # Получаем текст сообщения из события
        username = event['username']  # Получаем имя отправителя

        # Отправляем сообщение в WebSocket
        await self.send(text_data=json.dumps({  # Отправляем JSON сообщение клиенту
            'type': 'chat_message',  # Тип сообщения
            'message': message,  # Текст сообщения
            'username': username  # Имя отправителя
        }))