#!/bin/bash
set -e

# Инициализация Django
export DJANGO_SETTINGS_MODULE=myblog.settings
python manage.py shell -c "from django.core.management import execute_from_command_line; execute_from_command_line()" || echo "Django initialized"

# Запуск Celery worker
celery -A myblog worker --loglevel=info