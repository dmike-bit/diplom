import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from .models import Notification

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_group_name = f'notifications_{self.scope["user"].id}'
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_type = text_data_json['type']
        
        if message_type == 'get_notifications':
            notifications = await self.get_user_notifications()
            await self.send(text_data=json.dumps({
                'type': 'notifications',
                'notifications': notifications
            }))

    async def send_notification(self, event):
        notification = event['notification']
        
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'new_notification',
            'notification': notification
        }))

    @database_sync_to_async
    def get_user_notifications(self):
        user = self.scope["user"]
        if user.is_anonymous:
            return []
        
        notifications = Notification.objects.filter(
            user=user, 
            is_read=False
        ).order_by('-created_date')[:10]
        
        return [
            {
                'id': n.id,
                'title': n.title,
                'message': n.message,
                'type': n.notification_type,
                'created_date': n.created_date.isoformat(),
                'is_read': n.is_read
            }
            for n in notifications
        ]

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        username = self.scope["user"].username if self.scope["user"].is_authenticated else "Anonymous"

        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'username': username
            }
        )

    # Receive message from room group
    async def chat_message(self, event):
        message = event['message']
        username = event['username']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': message,
            'username': username
        }))