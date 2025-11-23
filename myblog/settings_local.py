"""
Локальные настройки для разработки без дополнительных зависимостей.
Используйте этот файл для запуска проекта без Docker.
"""

from .settings import *

# Отключаем сложные зависимости для локальной разработки
DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# Используем SQLite для простоты
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Отключаем Redis - используем локальный кэш
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

# Отключаем Channels для локальной разработки
ASGI_APPLICATION = None
CHANNEL_LAYERS = {}

# Отключаем сложные middleware
INSTALLED_APPS = [
    app for app in INSTALLED_APPS if app not in [
        'channels',
        'health_check',
        'health_check.db', 
        'health_check.cache',
        'health_check.storage',
        'captcha',
        'corsheaders',
        'axes',
    ]
]

MIDDLEWARE = [
    middleware for middleware in MIDDLEWARE if middleware not in [
        'corsheaders.middleware.CorsMiddleware',
        'channels.middleware.ChannelNameMiddleware',
        'axes.middleware.AxesMiddleware',
    ]
]

# Отключаем CORS для локальной разработки
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

# Упрощенная конфигурация REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser',
    ],
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,
}

# Отключаем debug toolbar при необходимости
try:
    INSTALLED_APPS.remove('debug_toolbar')
    MIDDLEWARE.remove('debug_toolbar.middleware.DebugToolbarMiddleware')
except ValueError:
    pass

# Отключаем.axes
try:
    INSTALLED_APPS.remove('axes')
except ValueError:
    pass

# Email для локальной разработки
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Упрощенное логирование
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

print("🐍 Загружены локальные настройки для разработки")