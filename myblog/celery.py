import os  # Импортируем модуль os для работы с переменными окружения и системными функциями
import django  # Импортируем модуль django для инициализации Django приложения
from celery import Celery  # Импортируем основной класс Celery для создания экземпляра Celery

# Установка настроек Django для Celery
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myblog.settings')  # Устанавливаем модуль настроек Django как настройки по умолчанию для Celery

# Инициализация Django
django.setup()  # Инициализируем Django приложение, загружаем все настройки, модели, приложения (обязательно для корректной работы Celery с Django)

# Создание экземпляра Celery
app = Celery('myblog')  # Создаем экземпляр Celery с именем проекта 'myblog' (это имя используется для команд Celery и идентификации воркеров)

# Загрузка конфигурации из настроек Django
app.config_from_object('django.conf:settings', namespace='CELERY')  # Загружаем настройки Celery из файла settings.py Django (все настройки должны иметь префикс CELERY_)

# Автоматическое обнаружение задач в Django приложениях
app.autodiscover_tasks()  # Автоматически обнаруживает файлы tasks.py во всех установленных приложениях Django и регистрирует найденные задачи Celery

# Создание базовой задачи для тестирования
@app.task(bind=True)  # Декоратор для создания задачи Celery, bind=True означает, что задача привязана к экземпляру (первый аргумент self)
def debug_task(self):  # Тестовая задача для проверки работоспособности Celery
    print(f'Request: {self.request!r}')  # Выводит информацию о запросе задачи в консоль (используется для отладки)
    return "Celery работает!"  # Возвращает сообщение о том, что Celery функционирует корректно