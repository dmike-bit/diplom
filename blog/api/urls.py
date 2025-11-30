from django.urls import path, include  # Импортируем функции для создания URL маршрутов и включения других URL конфигураций
from rest_framework.routers import DefaultRouter  # Импортируем DefaultRouter из Django REST Framework для автоматической генерации URL
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView  # Импортируем готовые views для работы с JWT токенами
from . import views  # Импортируем все views из текущего пакета (blog.api.views)

# Создаем router и регистрируем ViewSets
router = DefaultRouter()  # Создаем экземпляр DefaultRouter для автоматической регистрации ViewSets
router.register(r'posts', views.PostViewSet)  # Регистрируем ViewSet для постов (создает URL /api/posts/)
router.register(r'comments', views.CommentViewSet)  # Регистрируем ViewSet для комментариев (создает URL /api/comments/)
router.register(r'categories', views.CategoryViewSet)  # Регистрируем ViewSet для категорий (создает URL /api/categories/)
router.register(r'users', views.UserProfileViewSet)  # Регистрируем ViewSet для пользователей (создает URL /api/users/)
router.register(r'notifications', views.NotificationViewSet)  # Регистрируем ViewSet для уведомлений (создает URL /api/notifications/)

app_name = 'api'  # Определяем имя приложения для URL reverse resolution (используется в шаблонах как 'api:name')

urlpatterns = [  # Главный список URL паттернов API приложения
    # API Routes - автоматически сгенерированные URL от ViewSets
    path('', include(router.urls)),  # Включаем все URL, сгенерированные router'ом (создает маршруты для CRUD операций)
    
    # JWT Authentication - маршруты для аутентификации через JWT токены
    path('auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),  # Получение пары токенов (access + refresh) по учетным данным
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),  # Обновление access токена с помощью refresh токена
    path('auth/register/', views.register, name='register'),  # Регистрация нового пользователя
    path('auth/login/', views.user_login, name='login'),  # Авторизация пользователя (кастомная реализация)
    path('auth/logout/', views.user_logout, name='logout'),  # Выход пользователя из системы (добавление токена в черный список)
    
    # User endpoints - маршруты для работы с пользователями
    path('profile/', views.user_profile, name='user_profile'),  # Получение профиля текущего аутентифицированного пользователя
    
    # Site info - маршруты для получения информации о сайте
    path('site-info/', views.site_info, name='site_info'),  # Получение публичной информации о сайте (название, описание, настройки)
]