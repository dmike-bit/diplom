# Импорт модулей Django REST Framework
from rest_framework import viewsets, status, permissions  # Импортируем основные классы DRF: ViewSet, статусы HTTP и разрешения
from rest_framework.decorators import action, api_view, permission_classes  # Импортируем декораторы для кастомных действий и API views
from rest_framework.response import Response  # Импортируем класс для создания HTTP ответов
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAuthenticatedOrReadOnly  # Импортируем классы разрешений
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView  # Импортируем views для JWT токенов
from rest_framework_simplejwt.tokens import RefreshToken  # Импортируем класс для работы с JWT refresh токенами
from django.contrib.auth import authenticate, login, logout  # Импортируем функции аутентификации Django
from django.contrib.auth.models import User  # Импортируем модель пользователя Django
from django.db.models import Q, Count  # Импортируем Q объекты и функцию подсчета для сложных запросов к БД
from django_filters.rest_framework import DjangoFilterBackend  # Импортируем бэкенд фильтрации DRF
from blog .models import Post, Comment, Category, UserProfile, Notification  # Импортируем модели нашего приложения
from .serializers import (  # Импортируем все сериализаторы из текущего пакета
    PostSerializer, PostListSerializer, CommentSerializer,  # Сериализаторы для постов и комментариев
    CategorySerializer, UserSerializer, NotificationSerializer,  # Сериализаторы для категорий, пользователей и уведомлений
    RegisterSerializer, LoginSerializer  # Сериализаторы для регистрации и авторизации
)
from blog.views import get_site_settings, is_user_banned  # Импортируем функции из views.py основного приложения

# ViewSet для работы с категориями
class CategoryViewSet(viewsets.ModelViewSet):  # Класс ViewSet для автоматического CRUD API категорий
    queryset = Category.objects.all().annotate(post_count=Count('posts'))  # Базовый QuerySet с аннотацией количества постов в каждой категории
    serializer_class = CategorySerializer  # Класс сериализатора для категорий
    permission_classes = [IsAuthenticatedOrReadOnly]  # Разрешения: аутентифицированные пользователи могут писать, все - читать

# ViewSet для работы с постами
class PostViewSet(viewsets.ModelViewSet):  # Класс ViewSet для постов блога
    queryset = Post.objects.select_related('author', 'category').prefetch_related('comments', 'likes')  # Оптимизированный QuerySet с предзагрузкой связанных данных
    permission_classes = [IsAuthenticatedOrReadOnly]  # Разрешения: аутентифицированные пользователи могут писать, все - читать
    filter_backends = [DjangoFilterBackend]  # Бэкенд фильтрации для возможности фильтрации по полям
    filterset_fields = ['status', 'category', 'author']  # Поля, по которым разрешена фильтрация
    search_fields = ['title', 'content', 'excerpt', 'tags']  # Поля, по которым разрешен поиск
    ordering_fields = ['created_date', 'published_date', 'views', 'likes']  # Поля, по которым разрешена сортировка
    ordering = ['-published_date']  # Сортировка по умолчанию (новые посты первыми)

    def get_serializer_class(self):  # Метод выбора класса сериализатора в зависимости от действия
        if self.action == 'list':  # Если это список постов
            return PostListSerializer  # Используем сокращенный сериализатор для оптимизации
        return PostSerializer  # В остальных случаях используем полный сериализатор

    def get_queryset(self):  # Метод получения отфильтрованного QuerySet в зависимости от прав пользователя
        queryset = super().get_queryset()  # Получаем базовый QuerySet от родительского класса
        
        if self.request.user.is_anonymous:  # Если пользователь не аутентифицирован
            queryset = queryset.filter(status='published')  # Показываем только опубликованные посты
        elif not self.request.user.is_staff:  # Если пользователь не администратор
            queryset = queryset.filter(  # Показываем опубликованные посты или посты самого пользователя
                Q(status='published') | Q(author=self.request.user)
            )
        
        return queryset  # Возвращаем отфильтрованный QuerySet

    def perform_create(self, serializer):  # Метод выполняется при создании нового поста
        serializer.save(author=self.request.user)  # Автоматически устанавливаем текущего пользователя как автора

    @action(detail=True, methods=['post'])  # Кастомное действие для лайка/анлайка поста
    def like(self, request, pk=None):  # POST /posts/{id}/like/
        if is_user_banned(request.user):  # Проверяем, не заблокирован ли пользователь
            return Response({'error': 'Заблокированные пользователи не могут лайкать'}, status=status.HTTP_403_FORBIDDEN)  # Возвращаем ошибку
        
        post = self.get_object()  # Получаем объект поста по ID
        if post.likes.filter(id=request.user.id).exists():  # Проверяем, лайкнул ли уже пользователь этот пост
            post.likes.remove(request.user)  # Если да, то убираем лайк (анлайк)
            liked = False  # Флаг что пост не лайкнут
        else:  # Если не лайкнул
            post.likes.add(request.user)  # Добавляем лайк
            liked = True  # Флаг что пост лайкнут
        
        return Response({  # Возвращаем JSON ответ с результатом
            'liked': liked,  # Статус лайка (true/false)
            'like_count': post.likes.count()  # Общее количество лайков
        })

    @action(detail=True, methods=['get'])  # Кастомное действие для получения комментариев к посту
    def comments(self, request, pk=None):  # GET /posts/{id}/comments/
        post = self.get_object()  # Получаем объект поста по ID
        comments = post.comments.filter(is_active=True, parent=None).order_by('-created_date')  # Получаем активные комментарии без родителя (топ-уровень)
        serializer = CommentSerializer(comments, many=True)  # Сериализуем комментарии
        return Response(serializer.data)  # Возвращаем JSON ответ с данными комментариев

# ViewSet для работы с комментариями
class CommentViewSet(viewsets.ModelViewSet):  # Класс ViewSet для комментариев
    queryset = Comment.objects.select_related('author', 'post', 'parent').prefetch_related('replies', 'likes')  # Оптимизированный QuerySet с предзагрузкой связей
    serializer_class = CommentSerializer  # Класс сериализатора для комментариев
    permission_classes = [IsAuthenticated]  # Только аутентифицированные пользователи могут работать с комментариями

    def get_queryset(self):  # Метод получения отфильтрованного QuerySet
        return super().get_queryset().filter(is_active=True)  # Возвращаем только активные комментарии

    def perform_create(self, serializer):  # Метод выполняется при создании нового комментария
        if is_user_banned(self.request.user):  # Проверяем, не заблокирован ли пользователь
            return Response({'error': 'Заблокированные пользователи не могут комментировать'}, status=status.HTTP_403_FORBIDDEN)  # Возвращаем ошибку
        
        serializer.save(author=self.request.user)  # Автоматически устанавливаем текущего пользователя как автора комментария

    @action(detail=True, methods=['post'])  # Кастомное действие для лайка/анлайка комментария
    def like(self, request, pk=None):  # POST /comments/{id}/like/
        if is_user_banned(request.user):  # Проверяем, не заблокирован ли пользователь
            return Response({'error': 'Заблокированные пользователи не могут лайкать'}, status=status.HTTP_403_FORBIDDEN)  # Возвращаем ошибку
        
        comment = self.get_object()  # Получаем объект комментария по ID
        if comment.likes.filter(id=request.user.id).exists():  # Проверяем, лайкнул ли уже пользователь этот комментарий
            comment.likes.remove(request.user)  # Если да, то убираем лайк (анлайк)
            liked = False  # Флаг что комментарий не лайкнут
        else:  # Если не лайкнул
            comment.likes.add(request.user)  # Добавляем лайк
            liked = True  # Флаг что комментарий лайкнут
        
        return Response({  # Возвращаем JSON ответ с результатом
            'liked': liked,  # Статус лайка (true/false)
            'like_count': comment.likes.count()  # Общее количество лайков
        })

# ViewSet для работы с профилями пользователей (только чтение)
class UserProfileViewSet(viewsets.ReadOnlyModelViewSet):  # Класс ViewSet только для чтения профилей пользователей
    queryset = User.objects.all().select_related('profile').annotate(post_count=Count('blog_posts'))  # QuerySet пользователей с профилем и количеством постов
    serializer_class = UserSerializer  # Класс сериализатора для пользователей
    permission_classes = [IsAuthenticatedOrReadOnly]  # Разрешения: аутентифицированные пользователи могут писать, все - читать

    @action(detail=True, methods=['get', 'put', 'patch'])  # Кастомное действие для работы с профилем пользователя
    def profile(self, request, pk=None):  # GET/PUT/PATCH /users/{id}/profile/
        user = self.get_object()  # Получаем объект пользователя по ID
        
        if request.method == 'GET':  # Если это GET запрос (получение данных профиля)
            if user == request.user or request.user.is_staff:  # Если пользователь смотрит свой профиль или это администратор
                try:  # Пытаемся получить данные профиля
                    profile = user.profile  # Получаем объект профиля пользователя
                    return Response({  # Возвращаем полные данные профиля
                        'user': UserSerializer(user).data,  # Данные пользователя
                        'profile': {  # Данные профиля
                            'bio': profile.bio,  # Биография
                            'location': profile.location,  # Местоположение
                            'website': profile.website,  # Веб-сайт
                            'avatar': profile.avatar.url if profile.avatar else None,  # URL аватара
                            'birth_date': profile.birth_date,  # Дата рождения
                            'email_verified': profile.email_verified  # Статус верификации email
                        }
                    })
                except UserProfile.DoesNotExist:  # Если профиль не существует
                    return Response({'user': UserSerializer(user).data, 'profile': None})  # Возвращаем данные пользователя без профиля
            else:  # Если пользователь смотрит чужой профиль
                return Response(UserSerializer(user).data)  # Возвращаем только базовые данные пользователя
        
        elif request.method in ['PUT', 'PATCH']:  # Если это PUT или PATCH запрос (обновление данных)
            if user != request.user and not request.user.is_staff:  # Проверяем права доступа
                return Response({'error': 'Нет прав доступа'}, status=status.HTTP_403_FORBIDDEN)  # Возвращаем ошибку доступа
            
            # Здесь может быть логика обновления профиля
            return Response({'message': 'Profile updated successfully'})  # Возвращаем сообщение об успехе

# ViewSet для работы с уведомлениями
class NotificationViewSet(viewsets.ModelViewSet):  # Класс ViewSet для уведомлений
    queryset = Notification.objects.all()  # Базовый QuerySet для уведомлений
    serializer_class = NotificationSerializer  # Класс сериализатора для уведомлений
    permission_classes = [IsAuthenticated]  # Только аутентифицированные пользователи могут работать с уведомлениями

    def get_queryset(self):  # Метод получения отфильтрованного QuerySet
        return Notification.objects.filter(user=self.request.user)  # Возвращаем только уведомления текущего пользователя

    @action(detail=True, methods=['post'])  # Кастомное действие для отметки уведомления как прочитанное
    def mark_read(self, request, pk=None):  # POST /notifications/{id}/mark_read/
        notification = self.get_object()  # Получаем объект уведомления по ID
        notification.is_read = True  # Устанавливаем флаг прочитанности
        notification.save()  # Сохраняем изменения в БД
        return Response({'message': 'Уведомление помечено как прочитанное'})  # Возвращаем сообщение об успехе

    @action(detail=False, methods=['get'])  # Кастомное действие для получения непрочитанных уведомлений
    def unread(self, request):  # GET /notifications/unread/
        notifications = self.get_queryset().filter(is_read=False)[:10]  # Получаем последние 10 непрочитанных уведомлений
        serializer = self.get_serializer(notifications, many=True)  # Сериализуем уведомления
        return Response(serializer.data)  # Возвращаем JSON ответ с данными

# API endpoint для регистрации нового пользователя
@api_view(['POST'])  # Декоратор для создания API view
@permission_classes([AllowAny])  # Разрешения: доступ открыт всем (включая анонимных пользователей)
def register(request):  # POST /api/register/
    serializer = RegisterSerializer(data=request.data)  # Создаем сериализатор с данными из запроса
    if serializer.is_valid():  # Проверяем валидность данных
        user = serializer.save()  # Сохраняем пользователя (создаем нового)
        refresh = RefreshToken.for_user(user)  # Создаем refresh токен для пользователя
        return Response({  # Возвращаем успешный ответ с данными пользователя и токенами
            'user': UserSerializer(user).data,  # Данные пользователя
            'refresh': str(refresh),  # Refresh токен в строковом формате
            'access': str(refresh.access_token),  # Access токен в строковом формате
        }, status=status.HTTP_201_CREATED)  # HTTP статус 201 Created
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)  # Возвращаем ошибки валидации

# API endpoint для авторизации пользователя
@api_view(['POST'])  # Декоратор для создания API view
@permission_classes([AllowAny])  # Разрешения: доступ открыт всем
def user_login(request):  # POST /api/login/
    serializer = LoginSerializer(data=request.data)  # Создаем сериализатор с данными из запроса
    if serializer.is_valid():  # Проверяем валидность данных
        username = serializer.validated_data['username']  # Извлекаем имя пользователя из валидированных данных
        password = serializer.validated_data['password']  # Извлекаем пароль из валидированных данных
        
        user = authenticate(request, username=username, password=password)  # Аутентифицируем пользователя
        if user is not None:  # Если аутентификация прошла успешно
            if is_user_banned(user):  # Проверяем, не заблокирован ли пользователь
                return Response({'error': 'Аккаунт заблокирован'}, status=status.HTTP_403_FORBIDDEN)  # Возвращаем ошибку блокировки
            
            refresh = RefreshToken.for_user(user)  # Создаем refresh токен для пользователя
            return Response({  # Возвращаем успешный ответ с данными пользователя и токенами
                'user': UserSerializer(user).data,  # Данные пользователя
                'refresh': str(refresh),  # Refresh токен
                'access': str(refresh.access_token),  # Access токен
            })
        else:  # Если аутентификация не удалась
            return Response({'error': 'Неверные учетные данные'}, status=status.HTTP_401_UNAUTHORIZED)  # Возвращаем ошибку 401
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)  # Возвращаем ошибки валидации

# API endpoint для выхода пользователя из системы
@api_view(['POST'])  # Декоратор для создания API view
@permission_classes([IsAuthenticated])  # Разрешения: только аутентифицированные пользователи
def user_logout(request):  # POST /api/logout/
    try:  # Пытаемся добавить refresh токен в черный список
        refresh_token = request.data.get("refresh")  # Извлекаем refresh токен из данных запроса
        token = RefreshToken(refresh_token)  # Создаем объект RefreshToken
        token.blacklist()  # Добавляем токен в черный список (делает его недействительным)
        return Response({'message': 'Вы успешно вышли из системы'})  # Возвращаем сообщение об успехе
    except Exception:  # Если произошла ошибка
        return Response({'error': 'Неверный токен'}, status=status.HTTP_400_BAD_REQUEST)  # Возвращаем ошибку 400

# API endpoint для получения профиля текущего пользователя
@api_view(['GET'])  # Декоратор для создания API view
@permission_classes([IsAuthenticated])  # Разрешения: только аутентифицированные пользователи
def user_profile(request):  # GET /api/profile/
    user = request.user  # Получаем текущего аутентифицированного пользователя
    posts = Post.objects.filter(author=user).order_by('-created_date')[:10]  # Получаем последние 10 постов пользователя
    notifications = Notification.objects.filter(user=user, is_read=False)[:5]  # Получаем последние 5 непрочитанных уведомлений
    
    return Response({  # Возвращаем JSON ответ с данными профиля
        'user': UserSerializer(user).data,  # Данные пользователя
        'recent_posts': PostListSerializer(posts, many=True).data,  # Последние посты пользователя
        'unread_notifications': NotificationSerializer(notifications, many=True).data,  # Непрочитанные уведомления
    })

# API endpoint для получения публичной информации о сайте
@api_view(['GET'])  # Декоратор для создания API view
def site_info(request):  # GET /api/site_info/
    """Публичная информация о сайте"""  # Документация функции
    settings = get_site_settings()  # Получаем настройки сайта
    return Response({  # Возвращаем JSON ответ с публичной информацией
        'site_name': settings.site_name,  # Название сайта
        'site_description': settings.site_description,  # Описание сайта
        'posts_per_page': settings.posts_per_page,  # Количество постов на странице
        'allow_registration': settings.allow_registration,  # Разрешена ли регистрация
        'allow_comments': settings.allow_comments,  # Разрешены ли комментарии
    })
