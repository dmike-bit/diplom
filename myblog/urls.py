"""
Конфигурация URL для проекта myblog.

Список `urlpatterns` связывает URL-адреса с представлениями. Для получения дополнительной информации смотрите:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Примеры:
Функциональные представления
    1. Добавьте импорт:  from my_app import views
    2. Добавьте URL в urlpatterns:  path('', views.home, name='home')
Классовые представления
    1. Добавьте импорт:  from other_app.views import Home
    2. Добавьте URL в urlpatterns:  path('', Home.as_view(), name='home')
Подключение другого URLconf
    1. Импортируйте функцию include(): from django.urls import include, path
    2. Добавьте URL в urlpatterns:  path('blog/', include('blog.urls'))
"""

# ИМПОРТЫ НЕОБХОДИМЫХ МОДУЛЕЙ
from django.contrib import admin  # Встроенный модуль администрирования Django (админ-панель)
from django.urls import path, include  # Модули для создания URL маршрутов (path для простых маршрутов, include для включения других URLconf)
from django.conf import settings  # Настройки Django проекта (доступ к переменным из settings.py)
from django.conf.urls.static import static  # Утилиты для работы со статическими и медиа файлами в режиме разработки
from blog.views_health import health_check, system_stats  # Импорт функций проверки состояния системы и получения статистики

urlpatterns = [  # Главный список URL маршрутов проекта Django
    path('admin/', admin.site.urls),  # Маршрут к встроенной панели администратора Django (управление пользователями, контентом и т.д.)
    path('api/', include('blog.api.urls', namespace='api')),  # Включение всех REST API маршрутов приложения blog с пространством имен 'api' (для генерации URL)
    path('health/', health_check, name='health_check'),  # REST API endpoint для проверки состояния здоровья системы (мониторинг доступности всех сервисов)
    path('stats/', system_stats, name='system_stats'),  # REST API endpoint для получения статистики системы (загрузка CPU, памяти, соединения с БД и т.д.)
    path('', include('blog.urls')),  # Включение URL маршрутов основного приложения blog в корневой маршрут (главный сайт блога)
]

# НАСТРОЙКИ ДЛЯ РЕЖИМА РАЗРАБОТКИ
# Debug toolbar в режиме разработки (только когда DEBUG=True)
if settings.DEBUG:  # Проверяем, что мы находимся в режиме разработки (не в продакшене)
    import debug_toolbar  # Импорт Debug Toolbar для отладки Django (инструмент для профилирования и анализа запросов)
    urlpatterns += [path('__debug__/', include(debug_toolbar.urls))]  # Подключаем Debug Toolbar UI (доступен по адресу /__debug__/)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)  # Подключаем обслуживание медиа файлов в режиме разработки (загруженные пользователями файлы)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)  # Подключаем обслуживание статических файлов в режиме разработки (CSS, JS, изображения)
