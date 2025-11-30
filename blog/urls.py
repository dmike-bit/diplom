# Импорт необходимых модулей Django для работы с URL
from django.urls import path  # Импортируем функцию path для определения URL паттернов
from django.contrib.auth import views as auth_views  # Импортируем встроенные представления Django для аутентификации
from . import views  # Импортируем все представления из текущего приложения

# Список URL паттернов приложения блога
urlpatterns = [
    # ================================ ГЛАВНЫЕ СТРАНИЦЫ ================================
    path('', views.index, name='index'),  # Главная страница блога (корень приложения)
    path('posts/', views.post_list, name='post_list'),  # Список всех постов блога
    path('search/', views.search, name='search'),  # Поисковая страница для поиска постов
    path('contact/', views.contact, name='contact'),  # Страница с формой обратной связи
    
    # ================================ РАБОТА С ПОСТАМИ ================================
    path('post/<int:pk>/<slug:slug>/', views.post_detail, name='post_detail'),  # Детальная страница поста (с ID и slug)
    path('post/<int:pk>/', views.post_detail, name='post_detail_short'),  # Детальная страница поста (только с ID - короткая версия)
    path('post/new/', views.post_new, name='post_new'),  # Страница создания нового поста
    path('post/<int:pk>/edit/', views.post_edit, name='post_edit'),  # Страница редактирования поста
    path('post/<int:pk>/like/', views.post_like, name='post_like'),  # Обработчик лайка поста (AJAX)
    
    # ================================ РАБОТА С КОММЕНТАРИЯМИ ================================
    path('post/<int:post_pk>/comment/', views.comment_create, name='comment_create'),  # Создание нового комментария к посту
    path('comment/<int:comment_pk>/reply/', views.reply_create, name='reply_create'),  # Ответ на комментарий (вложенный комментарий)
    path('comment/<int:comment_pk>/like/', views.comment_like, name='comment_like'),  # Обработчик лайка комментария (AJAX)
    
    # ================================ АУТЕНТИФИКАЦИЯ ПОЛЬЗОВАТЕЛЕЙ ================================
    path('register/', views.register, name='register'),  # Страница регистрации нового пользователя
    path('login/', views.user_login, name='login'),  # Страница входа в систему
    path('logout/', views.user_logout, name='logout'),  # Выход из системы
    
    # ================================ ПРОФИЛИ ПОЛЬЗОВАТЕЛЕЙ ================================
    path('profile/', views.profile, name='profile'),  # Страница профиля текущего пользователя
    path('profile/edit/', views.profile_edit, name='profile_edit'),  # Страница редактирования профиля
    path('profile/change-password/', views.change_password, name='change_password'),  # Страница смены пароля
    path('users/', views.user_list, name='user_list'),  # Список всех пользователей блога
    path('user/<str:username>/', views.user_profile, name='user_profile'),  # Публичная страница профиля пользователя
    
    # ================================ УВЕДОМЛЕНИЯ ================================
    path('notification/<int:notification_pk>/read/', views.mark_notification_read, name='mark_notification_read'),  # Отметка уведомления как прочитанное
    path('notifications/unread/', views.get_unread_notifications, name='get_unread_notifications'),  # Получение списка непрочитанных уведомлений
    
    # ================================ СБРОС ПАРОЛЯ ================================
    path('password-reset/', auth_views.PasswordResetView.as_view(template_name='blog/password_reset.html'), name='password_reset'),  # Запрос на сброс пароля
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='blog/password_reset_done.html'), name='password_reset_done'),  # Подтверждение отправки ссылки на сброс
    path('password-reset-confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='blog/password_reset_confirm.html'), name='password_reset_confirm'),  # Подтверждение сброса пароля с токеном
    path('password-reset-complete/', auth_views.PasswordResetCompleteView.as_view(template_name='blog/password_reset_complete.html'), name='password_reset_complete'),  # Завершение процесса сброса пароля
]
