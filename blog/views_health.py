from django.http import JsonResponse
from django.db import connection
from django.core.cache import cache
from django.contrib.auth.models import User
from django.utils import timezone
import redis
import psutil
import os
from django.conf import settings

def health_check(request):
    """Основная проверка состояния системы"""
    status = {
        'status': 'healthy',
        'timestamp': timezone.now().isoformat(),
        'checks': {}
    }
    
    # Проверка базы данных
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        status['checks']['database'] = {'status': 'healthy', 'message': 'Database connection OK'}
    except Exception as e:
        status['checks']['database'] = {'status': 'unhealthy', 'message': str(e)}
        status['status'] = 'unhealthy'
    
    # Проверка Redis
    try:
        redis_client = redis.from_url(settings.REDIS_URL)
        redis_client.ping()
        status['checks']['redis'] = {'status': 'healthy', 'message': 'Redis connection OK'}
    except Exception as e:
        status['checks']['redis'] = {'status': 'unhealthy', 'message': str(e)}
        status['status'] = 'unhealthy'
    
    # Проверка кэша
    try:
        cache.set('health_check', 'ok', 10)
        cached_value = cache.get('health_check')
        if cached_value == 'ok':
            status['checks']['cache'] = {'status': 'healthy', 'message': 'Cache working properly'}
        else:
            status['checks']['cache'] = {'status': 'unhealthy', 'message': 'Cache not working'}
            status['status'] = 'unhealthy'
    except Exception as e:
        status['checks']['cache'] = {'status': 'unhealthy', 'message': str(e)}
        status['status'] = 'unhealthy'
    
    # Проверка статических файлов
    try:
        static_dir = settings.STATIC_ROOT
        if os.path.exists(static_dir):
            status['checks']['static_files'] = {'status': 'healthy', 'message': 'Static files directory exists'}
        else:
            status['checks']['static_files'] = {'status': 'warning', 'message': 'Static files directory not found'}
    except Exception as e:
        status['checks']['static_files'] = {'status': 'unhealthy', 'message': str(e)}
    
    # Проверка медиа файлов
    try:
        media_dir = settings.MEDIA_ROOT
        if os.path.exists(media_dir):
            status['checks']['media_files'] = {'status': 'healthy', 'message': 'Media files directory exists'}
        else:
            status['checks']['media_files'] = {'status': 'warning', 'message': 'Media files directory not found'}
    except Exception as e:
        status['checks']['media_files'] = {'status': 'unhealthy', 'message': str(e)}
    
    http_status = 200 if status['status'] == 'healthy' else 503
    return JsonResponse(status, status=http_status)

def system_stats(request):
    """Статистика системы"""
    stats = {
        'system': {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_percent': psutil.disk_usage('/').percent,
            'load_average': os.getloadavg() if hasattr(os, 'getloadavg') else [0, 0, 0]
        },
        'database': {
            'connections': get_db_connections()
        },
        'cache': {
            'redis_info': get_redis_info()
        },
        'django': {
            'debug': settings.DEBUG,
            'installed_apps': len(settings.INSTALLED_APPS),
            'middleware': len(settings.MIDDLEWARE)
        }
    }
    return JsonResponse(stats)

def get_db_connections():
    """Получить информацию о соединениях с БД"""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT count(*) FROM pg_stat_activity")
            return cursor.fetchone()[0]
    except:
        return "Unknown"

def get_redis_info():
    """Получить информацию о Redis"""
    try:
        redis_client = redis.from_url(settings.REDIS_URL)
        info = redis_client.info()
        return {
            'connected_clients': info.get('connected_clients', 0),
            'used_memory_human': info.get('used_memory_human', '0B'),
            'uptime_in_seconds': info.get('uptime_in_seconds', 0)
        }
    except:
        return "Redis not available"