from django.db import models  # Импорт модуля для работы с моделями Django
from django.contrib.auth.models import User  # Импорт стандартной модели пользователя Django
from django.utils import timezone  # Импорт утилит для работы с временными зонами
from django.urls import reverse  # Импорт функции для генерации URL
from django.core.exceptions import ValidationError  # Импорт исключений для валидации

# Модель категорий для группировки постов в блоге
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)  # Название категории (уникальное, до 100 символов)
    description = models.TextField(blank=True)  # Описание категории (необязательное поле)
    color = models.CharField(max_length=7, default='#00ff41')  # Цвет категории в HEX формате для UI
    created_date = models.DateTimeField(auto_now_add=True)  # Дата создания категории (автоматически устанавливается)
    
    class Meta:
        verbose_name_plural = "Categories"  # Множественное название для админ панели
        ordering = ['name']  # Сортировка по названию
    
    def __str__(self):
        return self.name  # Строковое представление категории

# Модель постов блога - основная модель для хранения статей
class Post(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Черновик'),  # Статус: черновик
        ('published', 'Опубликован'),  # Статус: опубликован
        ('archived', 'Архивирован'),  # Статус: архивирован
    ]
    
    title = models.CharField(max_length=200)  # Заголовок поста (до 200 символов)
    slug = models.SlugField(max_length=200, unique=True, blank=True)  # URL-friendly версия заголовка (уникальная)
    content = models.TextField()  # Основное содержимое поста
    excerpt = models.TextField(max_length=300, blank=True)  # Краткое описание поста (до 300 символов)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blog_posts')  # Автор поста
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='posts')  # Категория поста
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')  # Статус публикации
    created_date = models.DateTimeField(default=timezone.now)  # Дата создания
    published_date = models.DateTimeField(blank=True, null=True)  # Дата публикации (только для опубликованных постов)
    updated_date = models.DateTimeField(auto_now=True)  # Дата последнего обновления
    image = models.ImageField(upload_to='posts/%Y/%m/%d/', blank=True, null=True)  # Изображение поста
    views = models.PositiveIntegerField(default=0)  # Счетчик просмотров
    likes = models.ManyToManyField(User, related_name='post_likes', blank=True)  # Пользователи, которые лайкнули пост
    tags = models.CharField(max_length=200, blank=True)  # Теги для поиска и группировки
    
    class Meta:
        ordering = ['-published_date', '-created_date']  # Сортировка: сначала новые опубликованные, затем черновики
    
    def __str__(self):
        return self.title  # Строковое представление поста
    
    def get_absolute_url(self):
        return reverse('post_detail', kwargs={'pk': self.pk, 'slug': self.slug})  # Абсолютный URL поста
    
    def save(self, *args, **kwargs):
        # Автоматическая генерация slug если он не заполнен
        if not self.slug:
            from django.utils.text import slugify
            base_slug = slugify(self.title)  # Создаем базовый slug из заголовка
            if not base_slug:
                base_slug = 'post'  # Fallback slug если заголовок пустой
            self.slug = base_slug
            counter = 1
            # Делаем slug уникальным, добавляя номер если такой slug уже существует
            while Post.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                self.slug = f"{base_slug}-{counter}"
                counter += 1
        # Устанавливаем дату публикации при смене статуса на "опубликован"
        if self.status == 'published' and not self.published_date:
            self.published_date = timezone.now()
        # Автоматически создаем excerpt из content если он не заполнен
        if not self.excerpt and self.content:
            self.excerpt = self.content[:297] + '...' if len(self.content) > 300 else self.content
        super().save(*args, **kwargs)  # Сохраняем объект
    
    def like_count(self):
        return self.likes.count()  # Количество лайков поста
    
    def comment_count(self):
        return self.comments.filter(is_active=True).count()  # Количество активных комментариев
    
    def is_published(self):
        return self.status == 'published'  # Проверка статуса публикации

# Модель комментариев к постам с поддержкой вложенности (ответы на комментарии)
class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')  # Связанный пост
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blog_comments')  # Автор комментария
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')  # Родительский комментарий (для ответов)
    text = models.TextField()  # Текст комментария
    created_date = models.DateTimeField(default=timezone.now)  # Дата создания
    updated_date = models.DateTimeField(auto_now=True)  # Дата последнего редактирования
    is_active = models.BooleanField(default=True)  # Активность комментария (для модерации)
    likes = models.ManyToManyField(User, related_name='comment_likes', blank=True)  # Пользователи, лайкнувшие комментарий
    
    class Meta:
        ordering = ['-created_date']  # Сортировка: сначала новые комментарии
    
    def __str__(self):
        return f'Comment by {self.author} on {self.post}'  # Строковое представление
    
    def reply_count(self):
        return self.replies.filter(is_active=True).count()  # Количество ответов на комментарий
    
    def like_count(self):
        return self.likes.count()  # Количество лайков комментария

# Модель профиля пользователя с дополнительной информацией
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')  # Связанный пользователь
    bio = models.TextField(max_length=500, blank=True)  # Биография пользователя
    location = models.CharField(max_length=100, blank=True)  # Местоположение
    website = models.URLField(blank=True)  # Личный сайт
    avatar = models.ImageField(upload_to='avatars/%Y/%m/%d/', blank=True, null=True)  # Аватар пользователя
    birth_date = models.DateField(null=True, blank=True)  # Дата рождения
    is_banned = models.BooleanField(default=False)  # Флаг блокировки
    ban_reason = models.TextField(blank=True)  # Причина блокировки
    ban_expires = models.DateTimeField(null=True, blank=True)  # Дата окончания блокировки
    email_verified = models.BooleanField(default=False)  # Подтверждение email
    created_at = models.DateTimeField(auto_now_add=True)  # Дата создания профиля
    updated_at = models.DateTimeField(auto_now=True)  # Дата обновления профиля
    
    def __str__(self):
        return f'{self.user.username} Profile'  # Строковое представление профиля
    
    def is_currently_banned(self):
        if not self.is_banned:
            return False  # Не заблокирован
        # Проверяем, не истекла ли блокировка
        if self.ban_expires and timezone.now() > self.ban_expires:
            self.is_banned = False  # Снимаем блокировку если время истекло
            self.save()
            return False
        return True  # Все еще заблокирован

# Модель уведомлений для пользователей
class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('comment', 'Новый комментарий'),  # Новый комментарий к посту
        ('reply', 'Ответ на комментарий'),  # Ответ на комментарий
        ('like_post', 'Лайк поста'),  # Лайк поста
        ('like_comment', 'Лайк комментария'),  # Лайк комментария
        ('system', 'Системное'),  # Системное уведомление
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')  # Получатель уведомления
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)  # Тип уведомления
    title = models.CharField(max_length=200)  # Заголовок уведомления
    message = models.TextField()  # Текст уведомления
    related_post = models.ForeignKey(Post, on_delete=models.CASCADE, null=True, blank=True)  # Связанный пост
    related_comment = models.ForeignKey(Comment, on_delete=models.CASCADE, null=True, blank=True)  # Связанный комментарий
    is_read = models.BooleanField(default=False)  # Статус прочтения
    created_date = models.DateTimeField(default=timezone.now)  # Дата создания
    
    class Meta:
        ordering = ['-created_date']  # Сортировка: сначала новые уведомления
    
    def __str__(self):
        return f'Notification for {self.user.username}: {self.title}'  # Строковое представление

# Модель глобальных настроек сайта (Singleton)
class SiteSettings(models.Model):
    site_name = models.CharField(max_length=100, default='The Matrix Blog')  # Название сайта
    site_description = models.TextField(default='Welcome to the Matrix. The choice is yours.')  # Описание сайта
    admin_email = models.EmailField(default='admin@matrix.com')  # Email администратора
    posts_per_page = models.PositiveIntegerField(default=10)  # Количество постов на странице
    allow_registration = models.BooleanField(default=True)  # Разрешить регистрацию
    allow_comments = models.BooleanField(default=True)  # Разрешить комментарии
    moderate_comments = models.BooleanField(default=False)  # Модерация комментариев
    maintenance_mode = models.BooleanField(default=False)  # Режим технического обслуживания
    
    class Meta:
        verbose_name_plural = "Site Settings"  # Множественное название в админ панели
    
    def save(self, *args, **kwargs):
        # Ограничение: может существовать только один экземпляр настроек
        if not self.pk and SiteSettings.objects.exists():
            raise ValidationError('There can be only one SiteSettings instance')
        return super().save(*args, **kwargs)
    
    @classmethod
    def load(cls):
        # Получаем или создаем единственный экземпляр настроек
        obj, created = cls.objects.get_or_create(pk=1)
        return obj
