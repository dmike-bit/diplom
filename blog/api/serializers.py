from rest_framework import serializers  # Импортируем модуль serializers из Django REST Framework
from django.contrib.auth.models import User  # Импортируем модель пользователя Django
from blog.models import Post, Comment, Category, UserProfile, Notification  # Импортируем модели нашего приложения

# Сериализатор для модели Category
class CategorySerializer(serializers.ModelSerializer):  # Базовый сериализатор на основе модели Category
    post_count = serializers.IntegerField(read_only=True)  # Дополнительное поле для количества постов (только для чтения)
    
    class Meta:  # Метакласс с настройками сериализатора
        model = Category  # Модель для сериализации
        fields = ['id', 'name', 'description', 'color', 'created_date', 'post_count']  # Поля для включения в сериализацию

# Сериализатор для модели User
class UserSerializer(serializers.ModelSerializer):  # Базовый сериализатор на основе модели User
    profile = serializers.SerializerMethodField()  # Дополнительное поле для профиля пользователя (кастомный метод)
    post_count = serializers.IntegerField(read_only=True)  # Дополнительное поле для количества постов пользователя
    
    class Meta:  # Метакласс с настройками сериализатора
        model = User  # Модель для сериализации
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'date_joined', 'profile', 'post_count']  # Включаемые поля
    
    def get_profile(self, obj):  # Метод для получения данных профиля пользователя
        try:  # Пытаемся получить профиль пользователя
            profile = obj.profile  # Получаем объект профиля пользователя
            return {  # Возвращаем словарь с данными профиля
                'bio': profile.bio,  # Биография пользователя
                'location': profile.location,  # Местоположение пользователя
                'website': profile.website,  # Веб-сайт пользователя
                'avatar': profile.avatar.url if profile.avatar else None,  # URL аватара (если есть)
                'email_verified': profile.email_verified  # Статус верификации email
            }
        except UserProfile.DoesNotExist:  # Если профиль не существует
            return {}  # Возвращаем пустой словарь

# Сериализатор для модели UserProfile
class UserProfileSerializer(serializers.ModelSerializer):  # Базовый сериализатор на основе модели UserProfile
    user = UserSerializer(read_only=True)  # Поле user с вложенным сериализатором User (только для чтения)
    
    class Meta:  # Метакласс с настройками сериализатора
        model = UserProfile  # Модель для сериализации
        fields = ['user', 'bio', 'location', 'website', 'avatar', 'birth_date', 'email_verified']  # Включаемые поля

# Сериализатор для модели Comment
class CommentSerializer(serializers.ModelSerializer):  # Базовый сериализатор на основе модели Comment
    author = UserSerializer(read_only=True)  # Поле author с вложенным сериализатором User (только для чтения)
    replies = serializers.SerializerMethodField()  # Дополнительное поле для ответов на комментарий (рекурсия)
    like_count = serializers.IntegerField(read_only=True)  # Дополнительное поле для количества лайков комментария
    
    class Meta:  # Метакласс с настройками сериализатора
        model = Comment  # Модель для сериализации
        fields = ['id', 'post', 'author', 'parent', 'text', 'created_date', 'updated_date', 'is_active', 'likes', 'like_count', 'replies']  # Включаемые поля
        read_only_fields = ['author', 'created_date', 'updated_date', 'likes']  # Поля только для чтения (не редактируются)
    
    def get_replies(self, obj):  # Метод для получения ответов на комментарий
        if obj.replies.exists():  # Проверяем, есть ли ответы на этот комментарий
            return CommentSerializer(obj.replies.filter(is_active=True), many=True).data  # Сериализуем ответы рекурсивно
        return []  # Возвращаем пустой список, если ответов нет

# Сериализатор для модели Post (полная версия)
class PostSerializer(serializers.ModelSerializer):  # Базовый сериализатор на основе модели Post
    author = UserSerializer(read_only=True)  # Поле author с вложенным сериализатором User (только для чтения)
    category = CategorySerializer(read_only=True)  # Поле category с вложенным сериализатором Category (только для чтения)
    comments = serializers.SerializerMethodField()  # Дополнительное поле для комментариев к посту
    like_count = serializers.IntegerField(read_only=True)  # Дополнительное поле для количества лайков поста
    comment_count = serializers.IntegerField(read_only=True)  # Дополнительное поле для количества комментариев к посту
    
    class Meta:  # Метакласс с настройками сериализатора
        model = Post  # Модель для сериализации
        fields = ['id', 'title', 'slug', 'content', 'excerpt', 'author', 'category', 'status', 'created_date', 'published_date', 'updated_date', 'image', 'views', 'likes', 'tags', 'like_count', 'comment_count', 'comments']  # Включаемые поля
        read_only_fields = ['author', 'created_date', 'published_date', 'updated_date', 'views', 'likes']  # Поля только для чтения
    
    def get_comments(self, obj):  # Метод для получения комментариев к посту
        comments = obj.comments.filter(is_active=True, parent=None).order_by('-created_date')[:5]  # Получаем 5 последних активных комментариев без родителя
        return CommentSerializer(comments, many=True).data  # Сериализуем комментарии и возвращаем данные

# Сериализатор для модели Post (сокращенная версия для списков)
class PostListSerializer(serializers.ModelSerializer):  # Базовый сериализатор на основе модели Post (оптимизированный для списков)
    author = UserSerializer(read_only=True)  # Поле author с вложенным сериализатором User (только для чтения)
    category = CategorySerializer(read_only=True)  # Поле category с вложенным сериализатором Category (только для чтения)
    like_count = serializers.IntegerField(read_only=True)  # Дополнительное поле для количества лайков поста
    comment_count = serializers.IntegerField(read_only=True)  # Дополнительное поле для количества комментариев к посту
    
    class Meta:  # Метакласс с настройками сериализатора
        model = Post  # Модель для сериализации
        fields = ['id', 'title', 'slug', 'excerpt', 'author', 'category', 'status', 'created_date', 'published_date', 'image', 'views', 'likes', 'tags', 'like_count', 'comment_count']  # Включаемые поля (без полного content и comments для оптимизации)

# Сериализатор для модели Notification
class NotificationSerializer(serializers.ModelSerializer):  # Базовый сериализатор на основе модели Notification
    class Meta:  # Метакласс с настройками сериализатора
        model = Notification  # Модель для сериализации
        fields = ['id', 'notification_type', 'title', 'message', 'is_read', 'created_date', 'related_post', 'related_comment']  # Включаемые поля

# Сериализатор для регистрации пользователей
class RegisterSerializer(serializers.ModelSerializer):  # Базовый сериализатор на основе модели User для регистрации
    password = serializers.CharField(write_only=True, min_length=8)  # Поле пароля (только для записи, минимум 8 символов)
    password_confirm = serializers.CharField(write_only=True)  # Поле подтверждения пароля (только для записи)
    
    class Meta:  # Метакласс с настройками сериализатора
        model = User  # Модель для сериализации
        fields = ['username', 'email', 'first_name', 'last_name', 'password', 'password_confirm']  # Включаемые поля
    
    def validate(self, data):  # Метод валидации данных перед созданием объекта
        if data['password'] != data['password_confirm']:  # Проверяем совпадение паролей
            raise serializers.ValidationError("Пароли не совпадают")  # Выбрасываем ошибку валидации
        return data  # Возвращаем данные если валидация прошла успешно
    
    def create(self, validated_data):  # Метод создания пользователя с валидированными данными
        validated_data.pop('password_confirm')  # Удаляем поле подтверждения пароля (не нужно в модели)
        user = User.objects.create_user(**validated_data)  # Создаем пользователя с помощью метода create_user
        return user  # Возвращаем созданного пользователя

# Сериализатор для авторизации пользователей
class LoginSerializer(serializers.Serializer):  # Базовый сериализатор (не наследуется от ModelSerializer)
    username = serializers.CharField()  # Поле имени пользователя
    password = serializers.CharField(write_only=True)  # Поле пароля (только для записи)
