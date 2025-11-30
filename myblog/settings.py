"""
Настройки Django для проекта myblog.

Сгенерировано командой 'django-admin startproject' с использованием Django 5.2.8.

Для получения дополнительной информации об этом файле, см.
https://docs.djangoproject.com/en/5.2/topics/settings/

Полный список настроек и их значений см.
https://docs.djangoproject.com/en/5.2/ref/settings/
"""

from pathlib import Path  # Импортируем Path для работы с путями в файловой системе
import os  # Импортируем модуль os для работы с переменными окружения
import logging.config  # Импортируем конфигурацию логирования

# Построение путей внутри проекта, например: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent  # Определяем базовую директорию проекта (родительская папка от файла settings.py)

# Helper функция для чтения переменных окружения с fallback значениями
def get_env_var(key, default=None, cast=None):  # Функция для безопасного получения переменных окружения с приведением типов
    value = os.environ.get(key, default)  # Получаем значение из переменной окружения или используем default
    if value is None:  # Если значение None
        return default  # Возвращаем значение по умолчанию
    if cast == bool and isinstance(value, str):  # Приведение строки к булевому типу
        return value.lower() in ('true', '1', 'yes', 'on')  # Преобразуем строковые значения в boolean
    if cast == int and isinstance(value, str):  # Приведение строки к целому числу
        return int(value)  # Преобразуем строку в целое число
    return value  # Возвращаем значение без изменений

def parse_csv(value):  # Функция для парсинга CSV строк в список
    if isinstance(value, str):  # Если значение является строкой
        return [item.strip() for item in value.split(',') if item.strip()]  # Разделяем по запятой и очищаем от пробелов
    return value or []  # Возвращаем список или пустой список

# ПРЕДУПРЕЖДЕНИЕ БЕЗОПАСНОСТИ: держите секретный ключ в секрете в производственной среде!
SECRET_KEY = get_env_var('SECRET_KEY', 'django-insecure-eixt@bfryfwbl-)!5fs%x_l&2hwhkhs!79o2^rp2j458*2=08s')  # Секретный ключ для подписи cookies и токенов

# ПРЕДУПРЕЖДЕНИЕ БЕЗОПАСНОСТИ: не запускайте с включенным debug в производственной среде!
DEBUG = get_env_var('DEBUG', True, cast=bool)  # Режим отладки (True для разработки, False для продакшена)

ALLOWED_HOSTS = get_env_var('ALLOWED_HOSTS', '82.202.141.206,localhost,127.0.0.1')  # Разрешенные хосты для подключения к сайту
if isinstance(ALLOWED_HOSTS, str):  # Если ALLOWED_HOSTS является строкой
    ALLOWED_HOSTS = parse_csv(ALLOWED_HOSTS)  # Преобразуем строку в список хостов

# Определение приложений
INSTALLED_APPS = [  # Список установленных Django приложений
    'django.contrib.admin',  # Встроенная админ-панель Django
    'django.contrib.auth',  # Система аутентификации Django
    'django.contrib.contenttypes',  # Framework content types для полиморфных моделей
    'django.contrib.sessions',  # Фреймворк сессий Django
    'django.contrib.messages',  # Фреймворк сообщений Django
    'django.contrib.staticfiles',  # Фреймворк для работы со статическими файлами
    
    # Сторонние приложения
    'rest_framework',  # Django REST Framework для создания API
    'rest_framework_simplejwt',  # JWT аутентификация для DRF
    'corsheaders',  # CORS заголовки для кросс-доменных запросов
    'channels',  # Django Channels для WebSocket
    'django_extensions',  # Дополнительные утилиты Django
    'debug_toolbar',  # Панель отладки Django
    'axes',  # Плагин защиты от брутфорса атак на вход
    'health_check',  # Проверка состояния системы
    'health_check.db',  # Проверка базы данных
    'health_check.cache',  # Проверка кэша
    'health_check.storage',  # Проверка хранилища файлов
    'django_filters',  # Фильтрация для Django REST Framework
    'captcha',  # Капча для форм
    
    # Локальные приложения
    'blog',  # Наше основное приложение блога
]

MIDDLEWARE = [  # Список промежуточного ПО Django
    'corsheaders.middleware.CorsMiddleware',  # Middleware для CORS заголовков (должен быть первым)
    'django.middleware.security.SecurityMiddleware',  # Middleware безопасности Django
    'django.contrib.sessions.middleware.SessionMiddleware',  # Middleware для управления сессиями
    'django.middleware.common.CommonMiddleware',  # Общие middleware Django (настройки кэширования, ETag, etc)
    'django.middleware.csrf.CsrfViewMiddleware',  # Middleware для защиты от CSRF атак
    'django.contrib.auth.middleware.AuthenticationMiddleware',  # Middleware аутентификации Django
    'django.contrib.messages.middleware.MessageMiddleware',  # Middleware для системы сообщений
    'django.middleware.clickjacking.XFrameOptionsMiddleware',  # Middleware защиты от clickjacking атак
    'axes.middleware.AxesMiddleware',  # Middleware для защиты от брутфорса
]

# Debug Toolbar middleware (только в режиме отладки)
if DEBUG:  # Если включен режим отладки
    MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')  # Добавляем Debug Toolbar middleware первым в списке

# Backend аутентификации
AUTHENTICATION_BACKENDS = [  # Список backend'ов аутентификации Django
    'axes.backends.AxesStandaloneBackend',  # Backend axes для защиты от брутфорса
    'django.contrib.auth.backends.ModelBackend',  # Стандартный backend Django для аутентификации пользователей
]

ROOT_URLCONF = 'myblog.urls'  # Основная конфигурация URL паттернов проекта

TEMPLATES = [  # Настройка системы шаблонов Django
    {  # Конфигурация Django Templates
        'BACKEND': 'django.template.backends.django.DjangoTemplates',  # Backend для рендеринга шаблонов Django
        'DIRS': [BASE_DIR / 'templates'],  # Дополнительные директории с шаблонами (общие для всего проекта)
        'APP_DIRS': True,  # Включить поиск шаблонов в директориях приложений
        'OPTIONS': {  # Дополнительные настройки шаблонов
            'context_processors': [  # Процессоры контекста (автоматически добавляют переменные во все шаблоны)
                'django.template.context_processors.request',  # Добавляет объект request во все шаблоны
                'django.contrib.auth.context_processors.auth',  # Добавляет пользователя в контекст шаблонов
                'django.contrib.messages.context_processors.messages',  # Добавляет сообщения в контекст шаблонов
                'blog.context_processors.site_settings',  # Наши кастомные настройки сайта в шаблонах
            ],
        },
    },
]

WSGI_APPLICATION = 'myblog.wsgi.application'  # WSGI приложение для традиционных HTTP запросов
ASGI_APPLICATION = 'myblog.asgi.application'  # ASGI приложение для асинхронных запросов (WebSocket, HTTP2)

# База данных
# Конфигурация на основе переменных окружения
DATABASES = {  # Настройка базы данных Django
    'default': {  # База данных по умолчанию
        'ENGINE': 'django.db.backends.postgresql',  # Backend для PostgreSQL
        'NAME': get_env_var('DB_NAME', 'myblog'),  # Имя базы данных
        'USER': get_env_var('DB_USER', 'postgres'),  # Имя пользователя БД
        'PASSWORD': get_env_var('DB_PASSWORD', 'postgres123'),  # Пароль пользователя БД
        'HOST': get_env_var('DB_HOST', 'localhost'),  # Хост БД
        'PORT': get_env_var('DB_PORT', '5432'),  # Порт БД
        'OPTIONS': {  # Дополнительные опции подключения
            'connect_timeout': 10,  # Таймаут подключения 10 секунд
        },
    }
}

# Конфигурация кэша с Redis
REDIS_URL = get_env_var('REDIS_URL', 'redis://localhost:6379/1')  # URL для подключения к Redis
CACHES = {  # Настройка системы кэширования Django
    'default': {  # Кэш по умолчанию
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',  # Backend Redis для кэширования
        'LOCATION': REDIS_URL,  # URL подключения к Redis
        'KEY_PREFIX': 'myblog',  # Префикс для всех ключей кэша
        'TIMEOUT': 300,  # Время жизни кэша (300 секунд = 5 минут)
    }
}

# Fallback для разработки без Redis
if get_env_var('USE_LOCAL_CACHE', False, cast=bool):  # Если включен локальный кэш вместо Redis
    CACHES = {  # Перенастраиваем на локальный кэш
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',  # Локальный кэш в памяти
            'LOCATION': 'unique-snowflake',  # Уникальный идентификатор кэша
        }
    }

# Конфигурация сессий
SESSION_ENGINE = 'django.contrib.sessions.backends.file'  # Движок сессий (файловый)
SESSION_CACHE_ALIAS = 'default'  # Алиас кэша для сессий
SESSION_COOKIE_AGE = 86400  # Время жизни сессии в секундах (24 часа)
SESSION_COOKIE_SECURE = False  # Безопасность cookie сессии (False для HTTP, True для HTTPS)
SESSION_COOKIE_HTTPONLY = True  # Защита от JavaScript доступа к cookie
SESSION_COOKIE_SAMESITE = 'Lax'  # Защита от CSRF через SameSite cookie

# Конфигурация Redis для Channels (WebSocket)
CHANNEL_LAYERS = {  # Настройка слоя каналов для Django Channels
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',  # Backend Redis для WebSocket каналов
        'CONFIG': {
            'hosts': [REDIS_URL],  # Список хостов Redis
        },
    },
}

# Конфигурация Django REST Framework
REST_FRAMEWORK = {  # Настройки Django REST Framework
    'DEFAULT_AUTHENTICATION_CLASSES': [  # Классы аутентификации по умолчанию
        'rest_framework_simplejwt.authentication.JWTAuthentication',  # JWT аутентификация
        'rest_framework.authentication.SessionAuthentication',  # Сессионная аутентификация Django
    ],
    'DEFAULT_PERMISSION_CLASSES': [  # Классы разрешений по умолчанию
        'rest_framework.permissions.IsAuthenticated',  # Требуется аутентификация
    ],
    'DEFAULT_RENDERER_CLASSES': [  # Классы рендеринга ответов по умолчанию
        'rest_framework.renderers.JSONRenderer',  # Рендеринг в JSON формат
    ],
    'DEFAULT_PARSER_CLASSES': [  # Классы парсинга запросов по умолчанию
        'rest_framework.parsers.JSONParser',  # Парсинг JSON данных
        'rest_framework.parsers.MultiPartParser',  # Парсинг multipart данных (файлы)
        'rest_framework.parsers.FileUploadParser',  # Парсинг файловых загрузок
    ],
    'DEFAULT_FILTER_BACKEND': [  # Бэкенды фильтрации по умолчанию
        'django_filters.rest_framework.DjangoFilterBackend',  # Фильтрация через django-filters
        'rest_framework.filters.SearchFilter',  # Поиск по тексту
        'rest_framework.filters.OrderingFilter',  # Сортировка результатов
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',  # Класс пагинации по умолчанию
    'PAGE_SIZE': 10,  # Размер страницы в пагинации
    'DEFAULT_THROTTLE_CLASSES': [  # Классы ограничения запросов по умолчанию
        'rest_framework.throttling.AnonRateThrottle',  # Ограничение для анонимных пользователей
        'rest_framework.throttling.UserRateThrottle'  # Ограничение для аутентифицированных пользователей
    ],
    'DEFAULT_THROTTLE_RATES': {  # Стандартные ограничения запросов
        'anon': '100/day',  # 100 запросов в день для анонимных пользователей
        'user': '1000/day'  # 1000 запросов в день для аутентифицированных пользователей
    }
}

# Настройки JWT токенов
from datetime import timedelta  # Импортируем timedelta для настройки времени жизни токенов
SIMPLE_JWT = {  # Настройки Simple JWT токенов
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),  # Время жизни access токена (60 минут)
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),  # Время жизни refresh токена (7 дней)
    'ROTATE_REFRESH_TOKENS': True,  # Генерация нового refresh токена при каждом обновлении
}

# Настройки CORS
CORS_ALLOWED_ORIGINS = [  # Список разрешенных источников для CORS запросов
    "http://localhost:3000",  # Локальный фронтенд на порту 3000
    "http://127.0.0.1:3000",  # Локальный фронтенд на порту 3000 (альтернативный адрес)
    "http://localhost:8080",  # Локальный фронтенд на порту 8080
    "http://127.0.0.1:8080",  # Локальный фронтенд на порту 8080 (альтернативный адрес)
    "https://localhost:3000",  # HTTPS локальный фронтенд на порту 3000
    "https://127.0.0.1:3000",  # HTTPS локальный фронтенд на порту 3000 (альтернативный адрес)
    "https://localhost:8080",  # HTTPS локальный фронтенд на порту 8080
    "https://127.0.0.1:8080",  # HTTPS локальный фронтенд на порту 8080 (альтернативный адрес)
    "https://82.202.141.206",  # Домен продакшена
]

CORS_ALLOW_CREDENTIALS = True  # Разрешить передачу cookies и headers авторизации
CORS_ALLOW_ALL_ORIGINS = False  # Не разрешать все источники (используем белый список)
CORS_PREFLIGHT_MAX_AGE = 86400  # Кэширование preflight запросов на 24 часа

# Настройки безопасности
SECURE_BROWSER_XSS_FILTER = True  # Включить XSS фильтр браузера
SECURE_CONTENT_TYPE_NOSNIFF = True  # Запретить MIME sniffing контента
X_FRAME_OPTIONS = 'DENY'  # Запретить встраивание в iframe (защита от clickjacking)

# SSL настройки с поддержкой переменных окружения
SECURE_SSL_REDIRECT = get_env_var('SECURE_SSL_REDIRECT', False, cast=bool)  # Перенаправление на HTTPS
SECURE_COOP = get_env_var('SECURE_COOP', True, cast=bool)  # Cross-Origin Opener Policy
SECURE_CROSS_ORIGIN_OPENER_POLICY = get_env_var('SECURE_COOP', True, cast=bool)  # Настройка COOP

if not DEBUG and SECURE_SSL_REDIRECT:  # Если продакшен и включено HTTPS перенаправление
    SECURE_HSTS_SECONDS = 31536000  # Время HSTS (1 год в секундах)
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True  # Включить HSTS для поддоменов
    SECURE_HSTS_PRELOAD = True  # Разрешить добавление в HSTS preload list
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')  # Заголовок для определения HTTPS
    if SECURE_COOP:  # Если включен COOP
        SECURE_CROSS_ORIGIN_OPENER_POLICY = 'same-origin'  # Настроить COOP как same-origin

# Валидация паролей
AUTH_PASSWORD_VALIDATORS = [  # Список валидаторов паролей Django
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',  # Валидатор схожести пароля с атрибутами пользователя
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',  # Валидатор минимальной длины пароля
        'OPTIONS': {
            'min_length': 8,  # Минимальная длина пароля 8 символов
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',  # Валидатор против популярных паролей
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',  # Валидатор против числовых паролей
    },
]

# Конфигурация Axes (безопасность входа)
AXES_FAILURE_LIMIT = 5  # Максимальное количество неудачных попыток входа
AXES_COOLOFF_TIME = 1  # Время блокировки после превышения лимита (1 час)
AXES_LOCKOUT_PARAMETERS = ["ip_address", "username"]  # Параметры для определения блокировки (IP и имя пользователя)
AXES_USE_USER_AGENT = True  # Использовать User-Agent для дополнительной защиты

# Отключение предупреждения о тестовом ключе reCAPTCHA
SILENCED_SYSTEM_CHECKS = ['captcha.recaptcha_test_key_error']  # Игнорировать предупреждение о тестовом ключе капчи

# Конфигурация логирования (только консоль для Docker)
LOGGING = {  # Настройка системы логирования Django
    'version': 1,  # Версия схемы конфигурации логирования
    'disable_existing_loggers': False,  # Не отключать существующие логгеры
    'formatters': {  # Форматтеры логов
        'simple': {  # Простой формат логов
            'format': '{levelname} {message}',  # Формат: уровень сообщения
            'style': '{',  # Стиль форматирования
        },
    },
    'handlers': {  # Обработчики логов
        'console': {  # Консольный обработчик
            'level': 'INFO',  # Уровень логирования INFO и выше
            'class': 'logging.StreamHandler',  # Обработчик для вывода в консоль
            'formatter': 'simple',  # Использовать простой форматтер
        },
    },
    'root': {  # Корневой логгер
        'handlers': ['console'],  # Использовать консольный обработчик
        'level': 'INFO',  # Уровень логирования INFO и выше
    },
    'loggers': {  # Конфигурация логгеров для конкретных модулей
        'django': {  # Логгер Django
            'handlers': ['console'],  # Использовать консольный обработчик
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),  # Уровень логирования из переменной окружения или INFO
            'propagate': False,  # Не передавать сообщения родительским логгерам
        },
        'myblog': {  # Логгер нашего проекта
            'handlers': ['console'],  # Использовать консольный обработчик
            'level': 'DEBUG',  # Уровень логирования DEBUG (детальный)
            'propagate': False,  # Не передавать сообщения родительским логгерам
        },
    },
}

# Интернационализация
LANGUAGE_CODE = 'ru-ru'  # Код языка по умолчанию (русский)
TIME_ZONE = 'Europe/Moscow'  # Часовой пояс проекта
USE_I18N = True  # Включить поддержку интернационализации
USE_TZ = True  # Включить поддержку часовых поясов

# Статические файлы (CSS, JavaScript, изображения)
STATIC_URL = '/static/'  # URL для доступа к статическим файлам
STATIC_ROOT = BASE_DIR / 'staticfiles'  # Директория для собранных статических файлов в продакшене
STATICFILES_DIRS = [  # Дополнительные директории со статическими файлами
    BASE_DIR / 'static',  # Директория статических файлов проекта
]

# Медиа файлы
MEDIA_URL = '/media/'  # URL для доступа к загруженным файлам пользователей
MEDIA_ROOT = BASE_DIR / 'media'  # Директория для хранения загруженных файлов

# WhiteNoise временно отключен
# STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'  # Хранилище статических файлов Django

# Тип поля первичного ключа по умолчанию
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'  # Использовать BigAutoField для первичных ключей

# Кастомная модель пользователя
AUTH_USER_MODEL = 'auth.User'  # Использовать стандартную модель User Django (можно изменить на кастомную)

# Конфигурация email
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'  # Backend для отправки email через SMTP
EMAIL_HOST = get_env_var('EMAIL_HOST', 'localhost')  # SMTP сервер для отправки email
EMAIL_PORT = get_env_var('EMAIL_PORT', 587, cast=int)  # Порт SMTP сервера
EMAIL_USE_TLS = get_env_var('EMAIL_USE_TLS', True, cast=bool)  # Использовать TLS шифрование для SMTP
EMAIL_HOST_USER = get_env_var('EMAIL_HOST_USER', '')  # Имя пользователя для SMTP аутентификации
EMAIL_HOST_PASSWORD = get_env_var('EMAIL_HOST_PASSWORD', '')  # Пароль для SMTP аутентификации
DEFAULT_FROM_EMAIL = get_env_var('DEFAULT_FROM_EMAIL', 'noreply@myblog.com')  # Email отправителя по умолчанию

# Конфигурация Celery (асинхронные задачи)
CELERY_BROKER_URL = get_env_var('CELERY_BROKER_URL', 'redis://localhost:6379/2')  # URL брокера сообщений Celery
CELERY_RESULT_BACKEND = get_env_var('CELERY_RESULT_BACKEND', 'redis://localhost:6379/3')  # URL бэкенда результатов Celery
CELERY_ACCEPT_CONTENT = ['json']  # Типы контента, принимаемые Celery
CELERY_TASK_SERIALIZER = 'json'  # Сериализатор задач Celery
CELERY_RESULT_SERIALIZER = 'json'  # Сериализатор результатов Celery
CELERY_TIMEZONE = TIME_ZONE  # Часовой пояс для Celery

# Debug Toolbar (только в разработке)
if DEBUG:  # Если включен режим отладки
    INTERNAL_IPS = [  # Список внутренних IP адресов для показа Debug Toolbar
        '127.0.0.1',  # Локальный адрес
    ]
    
    DEBUG_TOOLBAR_CONFIG = {  # Конфигурация Debug Toolbar
        'SHOW_TOOLBAR_CALLBACK': lambda request: DEBUG and request.META.get('REMOTE_ADDR') in INTERNAL_IPS,  # Показать toolbar только для локальных запросов
    }

# Проверка состояния системы
HEALTH_CHECK = {  # Настройки health check (мониторинг системы)
    'DISK_USAGE_MAX': 90,  # Максимальное использование диска в процентах
    'MEMORY_MIN': 100,  # Минимальное количество доступной памяти в МБ
}

# Конфигурация Sentry (опционально)
SENTRY_DSN = get_env_var('SENTRY_DSN')  # DSN ключ для подключения к Sentry (мониторинг ошибок)
if SENTRY_DSN:  # Если DSN настроен
    try:
        import sentry_sdk  # Импортируем Sentry SDK для мониторинга ошибок
        from sentry_sdk.integrations.django import DjangoIntegration  # Интеграция с Django
        from sentry_sdk.integrations.celery import CeleryIntegration  # Интеграция с Celery
        from sentry_sdk.integrations.redis import RedisIntegration  # Интеграция с Redis
        
        sentry_sdk.init(  # Инициализируем Sentry SDK
            dsn=SENTRY_DSN,  # DSN ключ сервера Sentry
            integrations=[  # Список интеграций
                DjangoIntegration(),  # Интеграция с Django
                CeleryIntegration(),  # Интеграция с Celery
                RedisIntegration(),  # Интеграция с Redis
            ],
            traces_sample_rate=0.1,  # Процент трассировки запросов (10%)
            send_default_pii=False,  # Не отправлять персональные данные
            environment='production' if not DEBUG else 'development',  # Окружение приложения
        )
    except ImportError:  # Если Sentry SDK не установлен
        pass  # Ничего не делаем

# Ограничение скорости запросов
RATELIMIT_USE_CACHE = 'default'  # Использовать кэш по умолчанию для rate limiting

# Настройки загрузки файлов
FILE_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB - максимальный размер файла для загрузки в память
DATA_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB - максимальный размер данных для загрузки
FILE_UPLOAD_PERMISSIONS = 0o644  # Права доступа для загружаемых файлов
FILE_UPLOAD_DIRECTORY_PERMISSIONS = 0o755  # Права доступа для директорий загрузки

# Настройки админ-панели
ADMIN_URL = 'admin/'  # URL для доступа к админ-панели
ADMIN_SITE_HEADER = 'Матрица Блог'  # Заголовок админ-панели
ADMIN_SITE_TITLE = 'Матрица Блог'  # Заголовок страницы админ-панели
ADMIN_INDEX_TITLE = 'Панель управления блогом'  # Заголовок главной страницы админ-панели

# Настройки компрессора
COMPRESS_ENABLED = True  # Включить компрессию статических файлов
COMPRESS_OFFLINE = True  # Компрессия в режиме offline (предварительная компиляция)
COMPRESS_CSS_FILTERS = [  # Фильтры для компрессии CSS
    'compressor.filters.css_default.CssAbsoluteFilter',  # Фильтр для абсолютных путей CSS
    'compressor.filters.cssmin.CSSMinFilter',  # Минификация CSS
]
COMPRESS_JS_FILTERS = [  # Фильтры для компрессии JavaScript
    'compressor.filters.jsmin.JSMinFilter',  # Минификация JavaScript
]

# Создание директории логов
LOGS_DIR = BASE_DIR / 'logs'  # Определяем путь к директории логов
LOGS_DIR.mkdir(exist_ok=True)  # Создаем директорию логов, если она не существует
