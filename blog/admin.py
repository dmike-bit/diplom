from django.contrib import admin  # Встроенный модуль администрирования Django
from django.contrib.auth.models import User, Group  # Модели пользователей и групп Django
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin  # Базовый класс админки пользователей
from django.utils import timezone  # Утилиты для работы с временем
from django.utils.html import format_html  # Утилита для безопасного форматирования HTML
from .models import Post, Comment, UserProfile, Category, Notification, SiteSettings  # Модели приложения blog

# Inline форма для отображения профиля пользователя в админке пользователя
class UserProfileInline(admin.StackedInline):  # Inline форма для встроенного редактирования профиля
    model = UserProfile  # Модель профиля пользователя
    can_delete = False  # Нельзя удалить профиль через inline форму
    verbose_name_plural = 'Profile'  # Название в множественном числе в админке
    fields = ['bio', 'location', 'website', 'avatar', 'birth_date', 'is_banned', 'ban_reason', 'ban_expires', 'email_verified']  # Поля для отображения
    readonly_fields = ['created_at', 'updated_at']  # Поля только для чтения

# Расширенная админ-панель для пользователей
class UserAdmin(BaseUserAdmin):  # Кастомная админ-панель для пользователей
    inlines = [UserProfileInline]  # Включаем inline форму профиля
    list_display = ['username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active', 'get_banned_status', 'date_joined']  # Колонки в списке пользователей
    list_filter = ['is_staff', 'is_superuser', 'is_active', 'profile__is_banned', 'date_joined']  # Фильтры в боковой панели
    search_fields = ['username', 'email', 'first_name', 'last_name']  # Поля для поиска
    actions = ['ban_users', 'unban_users', 'activate_users', 'deactivate_users']  # Действия над выбранными пользователями
    
    def get_banned_status(self, obj):  # Метод для получения статуса блокировки
        try:
            return obj.profile.is_banned  # Проверяем статус блокировки из профиля
        except UserProfile.DoesNotExist:
            return False  # Если профиль не существует, считаем что не заблокирован
    get_banned_status.short_description = 'Banned'  # Название колонки в админке
    get_banned_status.boolean = True  # Отображать как иконку boolean (зеленая/красная)

    def ban_users(self, request, queryset):  # Действие блокировки пользователей
        for user in queryset:  # Перебираем выбранных пользователей
            profile, created = UserProfile.objects.get_or_create(user=user)  # Создаем или получаем профиль пользователя
            profile.is_banned = True  # Устанавливаем флаг блокировки
            profile.ban_reason = "Banned by admin"  # Устанавливаем причину блокировки
            profile.save()  # Сохраняем изменения
        self.message_user(request, f"{queryset.count()} users have been banned.")  # Показываем сообщение о результате
    ban_users.short_description = "Ban selected users"  # Описание действия в админке

    def unban_users(self, request, queryset):  # Действие разблокировки пользователей
        for user in queryset:  # Перебираем выбранных пользователей
            profile, created = UserProfile.objects.get_or_create(user=user)  # Создаем или получаем профиль
            profile.is_banned = False  # Снимаем флаг блокировки
            profile.ban_reason = ""  # Очищаем причину блокировки
            profile.ban_expires = None  # Сбрасываем время истечения блокировки
            profile.save()  # Сохраняем изменения
        self.message_user(request, f"{queryset.count()} users have been unbanned.")  # Сообщение о результате
    unban_users.short_description = "Unban selected users"  # Описание действия

# Админ-панель для категорий
class CategoryAdmin(admin.ModelAdmin):  # Класс админки для модели Category
    list_display = ['name', 'color_display', 'post_count', 'created_date']  # Колонки в списке категорий
    list_filter = ['created_date']  # Фильтр по дате создания
    search_fields = ['name', 'description']  # Поиск по названию и описанию
    
    def color_display(self, obj):  # Метод для отображения цвета категории
        return format_html('<span style="display: inline-block; width: 20px; height: 20px; background-color: {}; border: 1px solid #555;"></span> {}', obj.color, obj.color)  # HTML для отображения цветного квадратика
    color_display.short_description = 'Color'  # Название колонки
    
    def post_count(self, obj):  # Метод подсчета постов в категории
        return obj.posts.count()  # Количество связанных постов
    post_count.short_description = 'Posts'  # Название колонки

# Админ-панель для постов
class PostAdmin(admin.ModelAdmin):  # Класс админки для модели Post
    list_display = ['title', 'author', 'category', 'status', 'published_date', 'view_count', 'like_count', 'comment_count']  # Колонки в списке постов
    list_filter = ['status', 'category', 'created_date', 'published_date', 'author']  # Фильтры по статусу, категории, датам и автору
    search_fields = ['title', 'content', 'excerpt', 'tags']  # Поиск по заголовку, содержимому, описанию и тегам
    list_editable = ['status']  # Поле статуса редактируется прямо в списке
    readonly_fields = ['views', 'created_date', 'updated_date', 'published_date']  # Поля только для чтения
    prepopulated_fields = {'slug': ['title']}  # Автоматическая генерация slug из заголовка
    date_hierarchy = 'published_date'  # Иерархический фильтр по дате публикации
    filter_horizontal = ['likes']  # Горизонтальный фильтр для лайков
    actions = ['publish_posts', 'unpublish_posts', 'archive_posts']  # Действия над постами
    
    def view_count(self, obj):  # Метод отображения количества просмотров
        return obj.views  # Возвращаем количество просмотров
    view_count.short_description = 'Views'  # Название колонки
    
    def like_count(self, obj):  # Метод отображения количества лайков
        return obj.like_count()  # Вызываем метод модели для подсчета лайков
    like_count.short_description = 'Likes'  # Название колонки
    
    def comment_count(self, obj):  # Метод отображения количества комментариев
        return obj.comment_count()  # Вызываем метод модели для подсчета комментариев
    comment_count.short_description = 'Comments'  # Название колонки
    
    def publish_posts(self, request, queryset):  # Действие публикации постов
        updated = queryset.update(status='published', published_date=timezone.now())  # Обновляем статус и дату публикации
        self.message_user(request, f"{updated} posts have been published.")  # Сообщение о результате
    publish_posts.short_description = "Publish selected posts"  # Описание действия

# Админ-панель для комментариев
class CommentAdmin(admin.ModelAdmin):  # Класс админки для модели Comment
    list_display = ['author', 'post_preview', 'text_preview', 'is_active', 'created_date', 'like_count', 'reply_count']  # Колонки в списке комментариев
    list_filter = ['is_active', 'created_date', 'post__category']  # Фильтры по активности, дате и категории поста
    search_fields = ['text', 'author__username', 'post__title']  # Поиск по тексту, автору и заголовку поста
    list_editable = ['is_active']  # Поле активности редактируется в списке
    readonly_fields = ['created_date', 'updated_date']  # Поля только для чтения
    actions = ['activate_comments', 'deactivate_comments']  # Действия активации/деактивации комментариев
    
    def post_preview(self, obj):  # Превью поста для комментария
        return obj.post.title[:50] + '...' if len(obj.post.title) > 50 else obj.post.title  # Обрезаем длинные заголовки
    post_preview.short_description = 'Post'  # Название колонки
    
    def text_preview(self, obj):  # Превью текста комментария
        return obj.text[:100] + '...' if len(obj.text) > 100 else obj.text  # Обрезаем длинный текст
    text_preview.short_description = 'Comment'  # Название колонки
    
    def like_count(self, obj):  # Количество лайков комментария
        return obj.like_count()  # Вызываем метод модели
    like_count.short_description = 'Likes'  # Название колонки
    
    def reply_count(self, obj):  # Количество ответов на комментарий
        return obj.reply_count()  # Вызываем метод модели
    reply_count.short_description = 'Replies'  # Название колонки
    
    def activate_comments(self, request, queryset):  # Действие активации комментариев
        updated = queryset.update(is_active=True)  # Обновляем поле активности
        self.message_user(request, f"{updated} comments have been activated.")  # Сообщение о результате
    activate_comments.short_description = "Activate selected comments"  # Описание действия

# Админ-панель для уведомлений
class NotificationAdmin(admin.ModelAdmin):  # Класс админки для модели Notification
    list_display = ['user', 'notification_type', 'title_preview', 'is_read', 'created_date']  # Колонки в списке уведомлений
    list_filter = ['notification_type', 'is_read', 'created_date']  # Фильтры по типу, статусу и дате
    search_fields = ['title', 'message', 'user__username']  # Поиск по заголовку, сообщению и пользователю
    readonly_fields = ['created_date']  # Поля только для чтения
    actions = ['mark_as_read', 'mark_as_unread']  # Действия для отметки прочитанности
    
    def title_preview(self, obj):  # Превью заголовка уведомления
        return obj.title[:50] + '...' if len(obj.title) > 50 else obj.title  # Обрезаем длинные заголовки
    title_preview.short_description = 'Title'  # Название колонки

# Админ-панель для настроек сайта (Singleton)
class SiteSettingsAdmin(admin.ModelAdmin):  # Класс админки для модели SiteSettings
    list_display = ['site_name', 'admin_email', 'allow_registration', 'allow_comments', 'maintenance_mode']  # Основные настройки в списке
    
    def has_add_permission(self, request):  # Разрешение на добавление новых настроек
        return not SiteSettings.objects.exists()  # Запрещаем создавать более одной настройки

# Отключаем стандартные админки User и Group
admin.site.unregister(User)  # Удаляем стандартную админку пользователей
admin.site.unregister(Group)  # Удаляем стандартную админку групп

# Регистрируем кастомные админки
admin.site.register(User, UserAdmin)  # Регистрируем кастомную админку пользователей
admin.site.register(Category, CategoryAdmin)  # Регистрируем админку категорий
admin.site.register(Post, PostAdmin)  # Регистрируем админку постов
admin.site.register(Comment, CommentAdmin)  # Регистрируем админку комментариев
admin.site.register(Notification, NotificationAdmin)  # Регистрируем админку уведомлений
admin.site.register(SiteSettings, SiteSettingsAdmin)  # Регистрируем админку настроек сайта

# Настройка заголовков админ-панели
admin.site.site_header = "The Matrix Blog - Administration"  # Заголовок в шапке админки
admin.site.site_title = "Matrix Control Panel"  # Заголовок страницы
admin.site.index_title = "Welcome to the Matrix Control Panel"  # Заголовок главной страницы админки
