from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('posts/', views.post_list, name='post_list'),
    path('search/', views.search, name='search'),
    path('contact/', views.contact, name='contact'),
    
    path('post/<int:pk>/<slug:slug>/', views.post_detail, name='post_detail'),
    path('post/<int:pk>/', views.post_detail, name='post_detail_short'),
    path('post/new/', views.post_new, name='post_new'),
    path('post/<int:pk>/edit/', views.post_edit, name='post_edit'),
    path('post/<int:pk>/like/', views.post_like, name='post_like'),
    
    path('post/<int:post_pk>/comment/', views.comment_create, name='comment_create'),
    path('comment/<int:comment_pk>/reply/', views.reply_create, name='reply_create'),
    path('comment/<int:comment_pk>/like/', views.comment_like, name='comment_like'),
    
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('profile/change-password/', views.change_password, name='change_password'),
    path('users/', views.user_list, name='user_list'),
    path('user/<str:username>/', views.user_profile, name='user_profile'),
    
    path('notification/<int:notification_pk>/read/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/unread/', views.get_unread_notifications, name='get_unread_notifications'),
    
    path('password-reset/', auth_views.PasswordResetView.as_view(template_name='blog/password_reset.html'), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='blog/password_reset_done.html'), name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='blog/password_reset_confirm.html'), name='password_reset_confirm'),
    path('password-reset-complete/', auth_views.PasswordResetCompleteView.as_view(template_name='blog/password_reset_complete.html'), name='password_reset_complete'),
]
