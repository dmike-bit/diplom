from __future__ import absolute_import, unicode_literals

# Инициализация Celery
from celery import Celery

# Создание экземпляра Celery
app = Celery('myblog')

# Загрузка конфигурации Celery из настроек Django
app.config_from_object('django.conf:settings', namespace='CELERY')

# Автоматическое обнаружение задач в приложениях Django
app.autodiscover_tasks()

# Создание глобальной переменной для использования в других модулях
celery_app = app

# Для корректной работы с Django
@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')