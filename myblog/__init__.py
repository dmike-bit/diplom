from __future__ import absolute_import, unicode_literals  # Импорт будущих возможностей Python для абсолютного импорта и unicode-строк (для совместимости с Python 2 и 3)

# Инициализация Celery
from celery import Celery  # Импорт основного класса Celery для создания экземпляра Celery приложения

# Создание экземпляра Celery
app = Celery('myblog')  # Создаем экземпляр Celery с именем проекта 'myblog' (это имя будет использоваться для команд Celery и идентификации)

# Загрузка конфигурации Celery из настроек Django
app.config_from_object('django.conf:settings', namespace='CELERY')  # Загружаем настройки Celery из файла settings.py Django (все настройки должны иметь префикс CELERY_)

# Автоматическое обнаружение задач в приложениях Django
app.autodiscover_tasks()  # Автоматически обнаруживает файлы tasks.py во всех установленных приложениях Django и регистрирует найденные задачи Celery

# Создание глобальной переменной для использования в других модулях
celery_app = app  # Создаем глобальную переменную celery_app для удобного доступа к экземпляру Celery из других модулей проекта

# Для корректной работы с Django
@app.task(bind=True)  # Декоратор для создания задачи Celery, bind=True означает, что задача привязана к экземпляру (первый аргумент self)
def debug_task(self):  # Тестовая задача для отладки Celery (проверка работоспособности)
    print(f'Request: {self.request!r}')  # Выводит информацию о запросе задачи в консоль (используется для отладки)