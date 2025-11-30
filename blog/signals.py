# Импорт необходимых модулей Django для работы с сигналами
from django.db.models.signals import post_save, post_delete  # Импортируем сигналы после сохранения и удаления
from django.dispatch import receiver  # Импортируем декоратор для регистрации обработчиков сигналов
from django.contrib.auth.models import User  # Импортируем модель пользователя Django
from .models import UserProfile, Comment, Notification  # Импортируем наши модели приложения

# Сигнал автоматического создания профиля пользователя
@receiver(post_save, sender=User)  # Регистрируем обработчик для сигнала после сохранения объекта User
def create_user_profile(sender, instance, created, **kwargs):  # Функция-обработчик сигнала
    if created:  # Проверяем, что пользователь только что создан (а не обновлен)
        UserProfile.objects.create(user=instance)  # Создаем профиль пользователя для нового пользователя

# Сигнал автоматического сохранения профиля пользователя
@receiver(post_save, sender=User)  # Регистрируем обработчик для сигнала после сохранения объекта User
def save_user_profile(sender, instance, **kwargs):  # Функция-обработчик сигнала (вызывается при создании и обновлении)
    try:  # Пытаемся сохранить существующий профиль
        instance.profile.save()  # Сохраняем профиль пользователя
    except UserProfile.DoesNotExist:  # Если профиль не существует (может произойти при миграциях)
        UserProfile.objects.create(user=instance)  # Создаем профиль для пользователя

# Сигнал уведомления автора поста о новом комментарии
@receiver(post_save, sender=Comment)  # Регистрируем обработчик для сигнала после сохранения объекта Comment
def notify_post_author_on_comment(sender, instance, created, **kwargs):  # Функция-обработчик сигнала
    if created and not instance.parent:  # Проверяем, что комментарий новый и это не ответ на другой комментарий
        post_author = instance.post.author  # Получаем автора поста, к которому оставлен комментарий
        if post_author != instance.author:  # Проверяем, что автор поста не комментирует свой же пост
            Notification.objects.create(  # Создаем уведомление для автора поста
                user=post_author,  # Получатель уведомления - автор поста
                notification_type='comment',  # Тип уведомления - комментарий
                title='New Comment on Your Post',  # Заголовок уведомления
                message=f'{instance.author.username} commented on your post "{instance.post.title}"',  # Текст уведомления с именем комментатора и заголовком поста
                related_post=instance.post,  # Связанный пост
                related_comment=instance  # Связанный комментарий
            )
