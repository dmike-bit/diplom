# Импорт необходимых модулей для мониторинга системы
from django.http import JsonResponse  # Импортируем класс для возврата JSON ответов HTTP
from django.db import connection  # Импортируем объект соединения с базой данных
from django.core.cache import cache  # Импортируем объект кэша Django
from django.contrib.auth.models import User  # Импортируем модель пользователя Django
from django.utils import timezone  # Импортируем модуль для работы с часовыми поясами
import redis  # Импортируем модуль для работы с Redis
import psutil  # Импортируем модуль для получения системной информации
import os  # Импортируем модуль для работы с операционной системой
from django.conf import settings  # Импортируем настройки Django

def health_check(request):  # Функция проверки состояния здоровья системы (мониторинг)
    """Основная проверка состояния системы"""  # Документация функции
    status = {  # Словарь для хранения статуса системы
        'status': 'healthy',  # Общий статус системы (healthy/unhealthy)
        'timestamp': timezone.now().isoformat(),  # Временная метка проверки в ISO формате
        'checks': {}  # Словарь для детальных результатов каждой проверки
    }
    
    # Проверка базы данных
    try:  # Попытка выполнить тестовое подключение к БД
        with connection.cursor() as cursor:  # Получаем курсор для выполнения SQL запросов
            cursor.execute("SELECT 1")  # Выполняем простой SQL запрос для проверки соединения
        status['checks']['database'] = {'status': 'healthy', 'message': 'Database connection OK'}  # БД работает корректно
    except Exception as e:  # Если произошла ошибка при подключении к БД
        status['checks']['database'] = {'status': 'unhealthy', 'message': str(e)}  # Записываем ошибку в результаты
        status['status'] = 'unhealthy'  # Устанавливаем общий статус как нездоровый
    
    # Проверка Redis
    try:  # Попытка подключения к Redis
        redis_client = redis.from_url(settings.REDIS_URL)  # Создаем клиент Redis из URL настроек
        redis_client.ping()  # Отправляем команду PING для проверки подключения
        status['checks']['redis'] = {'status': 'healthy', 'message': 'Redis connection OK'}  # Redis работает корректно
    except Exception as e:  # Если произошла ошибка при подключении к Redis
        status['checks']['redis'] = {'status': 'unhealthy', 'message': str(e)}  # Записываем ошибку в результаты
        status['status'] = 'unhealthy'  # Устанавливаем общий статус как нездоровый
    
    # Проверка кэша
    try:  # Попытка проверить работу кэша Django
        cache.set('health_check', 'ok', 10)  # Устанавливаем тестовое значение в кэш на 10 секунд
        cached_value = cache.get('health_check')  # Получаем значение из кэша
        if cached_value == 'ok':  # Проверяем, что значение сохранилось корректно
            status['checks']['cache'] = {'status': 'healthy', 'message': 'Cache working properly'}  # Кэш работает корректно
        else:  # Если значение не совпадает
            status['checks']['cache'] = {'status': 'unhealthy', 'message': 'Cache not working'}  # Кэш работает неправильно
            status['status'] = 'unhealthy'  # Устанавливаем общий статус как нездоровый
    except Exception as e:  # Если произошла ошибка при работе с кэшем
        status['checks']['cache'] = {'status': 'unhealthy', 'message': str(e)}  # Записываем ошибку в результаты
        status['status'] = 'unhealthy'  # Устанавливаем общий статус как нездоровый
    
    # Проверка статических файлов
    try:  # Попытка проверить наличие директории статических файлов
        static_dir = settings.STATIC_ROOT  # Получаем путь к директории статических файлов из настроек
        if os.path.exists(static_dir):  # Проверяем существование директории
            status['checks']['static_files'] = {'status': 'healthy', 'message': 'Static files directory exists'}  # Директория существует
        else:  # Если директория не существует
            status['checks']['static_files'] = {'status': 'warning', 'message': 'Static files directory not found'}  # Предупреждение
    except Exception as e:  # Если произошла ошибка при проверке
        status['checks']['static_files'] = {'status': 'unhealthy', 'message': str(e)}  # Записываем ошибку в результаты
    
    # Проверка медиа файлов
    try:  # Попытка проверить наличие директории медиа файлов
        media_dir = settings.MEDIA_ROOT  # Получаем путь к директории медиа файлов из настроек
        if os.path.exists(media_dir):  # Проверяем существование директории
            status['checks']['media_files'] = {'status': 'healthy', 'message': 'Media files directory exists'}  # Директория существует
        else:  # Если директория не существует
            status['checks']['media_files'] = {'status': 'warning', 'message': 'Media files directory not found'}  # Предупреждение
    except Exception as e:  # Если произошла ошибка при проверке
        status['checks']['media_files'] = {'status': 'unhealthy', 'message': str(e)}  # Записываем ошибку в результаты
    
    http_status = 200 if status['status'] == 'healthy' else 503  # Определяем HTTP статус код: 200 для здорового состояния, 503 для нездорового
    return JsonResponse(status, status=http_status)  # Возвращаем JSON ответ с результатами проверки и соответствующим HTTP статус кодом

def system_stats(request):  # Функция получения статистики системы
    """Статистика системы"""  # Документация функции
    stats = {  # Словарь для хранения статистики системы
        'system': {  # Статистика системы
            'cpu_percent': psutil.cpu_percent(interval=1),  # Процент использования CPU с интервалом измерения 1 секунда
            'memory_percent': psutil.virtual_memory().percent,  # Процент использования оперативной памяти
            'disk_percent': psutil.disk_usage('/').percent,  # Процент использования дискового пространства корневой директории
            'load_average': os.getloadavg() if hasattr(os, 'getloadavg') else [0, 0, 0]  # Средняя загрузка системы (1, 5, 15 минут), если функция доступна
        },
        'database': {  # Статистика базы данных
            'connections': get_db_connections()  # Количество активных соединений с базой данных
        },
        'cache': {  # Статистика кэша/Redis
            'redis_info': get_redis_info()  # Информация о Redis сервере
        },
        'django': {  # Статистика Django приложения
            'debug': settings.DEBUG,  # Режим отладки приложения
            'installed_apps': len(settings.INSTALLED_APPS),  # Количество установленных приложений Django
            'middleware': len(settings.MIDDLEWARE)  # Количество слоев middleware
        }
    }
    return JsonResponse(stats)  # Возвращаем JSON ответ со статистикой системы

def get_db_connections():  # Функция получения количества соединений с базой данных
    """Получить информацию о соединениях с БД"""  # Документация функции
    try:  # Попытка получить информацию о соединениях
        with connection.cursor() as cursor:  # Получаем курсор для выполнения SQL запросов
            cursor.execute("SELECT count(*) FROM pg_stat_activity")  # Выполняем SQL запрос для подсчета активных соединений PostgreSQL
            return cursor.fetchone()[0]  # Возвращаем количество активных соединений
    except:  # Если произошла ошибка
        return "Unknown"  # Возвращаем строку "Unknown" при ошибке

def get_redis_info():  # Функция получения информации о Redis сервере
    """Получить информацию о Redis"""  # Документация функции
    try:  # Попытка получить информацию о Redis
        redis_client = redis.from_url(settings.REDIS_URL)  # Создаем клиент Redis из URL настроек
        info = redis_client.info()  # Получаем детальную информацию о Redis сервере
        return {  # Возвращаем словарь с ключевой информацией
            'connected_clients': info.get('connected_clients', 0),  # Количество подключенных клиентов (по умолчанию 0)
            'used_memory_human': info.get('used_memory_human', '0B'),  # Используемая память в читаемом формате (по умолчанию '0B')
            'uptime_in_seconds': info.get('uptime_in_seconds', 0)  # Время работы сервера в секундах (по умолчанию 0)
        }
    except:  # Если произошла ошибка
        return "Redis not available"  # Возвращаем сообщение о недоступности Redis