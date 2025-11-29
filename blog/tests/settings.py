"""
Настройки для тестов блога
"""

# Переопределяем настройки для тестирования
import os
import sys

# Добавляем путь к родительскому каталогу
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Простейшие настройки для тестов
TEST_DATABASE_NAME = ':memory:'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': TEST_DATABASE_NAME,
    }
}

# Упрощенная конфигурация для тестов
DEBUG = True
SECRET_KEY = 'test-secret-key-for-testing-only'

# Обязательные настройки для приложения
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'blog',
]

MIDDLEWARE = [
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
]

ROOT_URLCONF = 'blog.urls'

# Временная зона для тестов
TIME_ZONE = 'Europe/Moscow'
USE_TZ = True

# Отключаем миграции для скорости
class DisableMigrations:
    def __contains__(self, item):
        return True
    
    def __getitem__(self, item):
        return None

MIGRATION_MODULES = DisableMigrations()

# Настройки логирования для тестов
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.NullHandler',
        },
    },
    'root': {
        'handlers': ['console'],
    },
}

# Настройки для тестирования медиа файлов
MEDIA_ROOT = '/tmp/test_media/'
FILE_UPLOAD_TEMP_DIR = '/tmp/test_uploads/'

# Отключаем кеширование для чистоты тестов
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

# Настройки для Django REST Framework в тестах
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.MultiPartParser',
    ],
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/day',
        'user': '1000/day'
    }
}

# JWT настройки для тестов
from datetime import timedelta
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
}

# Отключаем отправку email в тестах
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# Настройки для Celery (отключаем для тестов)
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# Упрощенные настройки безопасности для тестов
SECURE_SSL_REDIRECT = False
SECURE_HSTS_SECONDS = 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False

# Отключаем CORS для тестов (если включен)
CORS_ALLOW_ALL_ORIGINS = True

# Настройки для Django Debug Toolbar (отключаем)
INTERNAL_IPS = []

# Подавляем предупреждения
SILENCED_SYSTEM_CHECKS = []