from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import views

# Создаем router и регистрируем ViewSets
router = DefaultRouter()
router.register(r'posts', views.PostViewSet)
router.register(r'comments', views.CommentViewSet)
router.register(r'categories', views.CategoryViewSet)
router.register(r'users', views.UserProfileViewSet)
router.register(r'notifications', views.NotificationViewSet)

app_name = 'api'

urlpatterns = [
    # API Routes
    path('', include(router.urls)),
    
    # JWT Authentication
    path('auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/register/', views.register, name='register'),
    path('auth/login/', views.user_login, name='login'),
    path('auth/logout/', views.user_logout, name='logout'),
    
    # User endpoints
    path('profile/', views.user_profile, name='user_profile'),
    
    # Site info
    path('site-info/', views.site_info, name='site_info'),
]