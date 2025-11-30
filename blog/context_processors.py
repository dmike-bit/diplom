# Импорт моделей для контекстных процессоров
from .models import SiteSettings, Category  # Импортируем модели настроек сайта и категорий

# Контекстный процессор для настроек сайта
def site_settings(request):  # Функция контекстного процессора, вызывается для каждого HTTP запроса
    return {'site_settings': SiteSettings.load()}  # Возвращаем словарь с настройками сайта, доступными во всех шаблонах

# Контекстный процессор для категорий
def categories(request):  # Функция контекстного процессора для получения всех категорий
    return {'categories': Category.objects.all()}  # Возвращаем словарь со всеми категориями постов для использования в навигации

# Контекстный процессор для уведомлений пользователя
def user_notifications(request):  # Функция контекстного процессора для получения количества непрочитанных уведомлений
    if request.user.is_authenticated:  # Проверяем, аутентифицирован ли пользователь
        unread_count = request.user.notifications.filter(is_read=False).count()  # Подсчитываем количество непрочитанных уведомлений
        return {'unread_notifications_count': unread_count}  # Возвращаем количество непрочитанных уведомлений
    return {'unread_notifications_count': 0}  # Если пользователь не аутентифицирован, возвращаем 0
