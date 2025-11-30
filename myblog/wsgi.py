"""
Конфигурация WSGI для проекта myblog.

Этот файл предоставляет WSGI приложение как модульную переменную с именем ``application``.

Для получения дополнительной информации по этому файлу см.
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os  # Импортируем модуль os для работы с переменными окружения и системными функциями

from django.core.wsgi import get_wsgi_application  # Импортируем функцию для создания WSGI приложения Django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myblog.settings')  # Устанавливаем модуль настроек Django как настройки по умолчанию для WSGI приложения

application = get_wsgi_application()  # Создаем и экспортируем WSGI приложение Django, которое будет использоваться веб-сервером (Apache, Nginx + Gunicorn и т.д.)
