from django.apps import AppConfig  # Импортируем базовый класс конфигурации приложения Django

# Конфигурационный класс приложения блога
class BlogConfig(AppConfig):  # Класс конфигурации для приложения blog
    default_auto_field = 'django.db.models.BigAutoField'  # Поле по умолчанию для AutoField в моделях (использует BigAutoField для больших ID)
    name = 'blog'  # Название приложения
    verbose_name = 'Matrix Blog'  # Читаемое название для админ-панели и интерфейса
    
    def ready(self):  # Метод вызывается при инициализации приложения Django
        import blog.signals  # Импортируем файл signals для регистрации обработчиков сигналов
