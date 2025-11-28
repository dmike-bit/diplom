import os
import django
from celery import Celery

# Установка настроек Django для Celery
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myblog.settings')

# Инициализация Django
django.setup()

# Создание экземпляра Celery
app = Celery('myblog')

# Загрузка конфигурации из настроек Django
app.config_from_object('django.conf:settings', namespace='CELERY')

# Автоматическое обнаружение задач в Django приложениях
app.autodiscover_tasks()

# Создание базовой задачи для тестирования
@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
    return "Celery работает!"