#!/usr/bin/env python3
"""
Скрипт для быстрого запуска Django проекта в локальной разработке.
Запускает проект с минимальными зависимостями.
"""

import os
import sys
import subprocess
from pathlib import Path

def install_basic_dependencies():
    """Установка базовых зависимостей для локальной разработки"""
    basic_deps = [
        'Django==5.2.8',
        'django-crispy-forms==2.1',
        'crispy-bootstrap5==0.7',
        'Pillow==10.1.0'
    ]
    
    print("📦 Установка базовых зависимостей...")
    for dep in basic_deps:
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', dep])
            print(f"✅ Установлен: {dep}")
        except subprocess.CalledProcessError as e:
            print(f"❌ Ошибка установки {dep}: {e}")
            return False
    return True

def setup_database():
    """Настройка базы данных и создание миграций"""
    print("🗄️ Настройка базы данных...")
    
    commands = [
        ['python', 'manage.py', 'migrate', '--settings=myblog.settings_local'],
        ['python', 'manage.py', 'collectstatic', '--noinput', '--settings=myblog.settings_local']
    ]
    
    for cmd in commands:
        try:
            subprocess.check_call(cmd)
            print(f"✅ Выполнено: {' '.join(cmd)}")
        except subprocess.CalledProcessError as e:
            print(f"❌ Ошибка выполнения команды: {e}")
            return False
    return True

def check_superuser():
    """Проверка наличия суперпользователя"""
    try:
        result = subprocess.run([
            'python', 'manage.py', 'shell', '--settings=myblog.settings_local',
            '-c', 'from django.contrib.auth.models import User; print("superuser_exists:", User.objects.filter(is_superuser=True).exists())'
        ], capture_output=True, text=True)
        
        if 'superuser_exists: False' in result.stdout:
            print("👤 Создание суперпользователя...")
            try:
                subprocess.check_call([
                    'python', 'manage.py', 'createsuperuser', '--settings=myblog.settings_local'
                ])
                print("✅ Суперпользователь создан")
            except subprocess.CalledProcessError:
                print("⚠️ Создание суперпользователя пропущено (можно создать позже)")
        else:
            print("✅ Суперпользователь уже существует")
    except subprocess.CalledProcessError:
        print("⚠️ Не удалось проверить суперпользователя")

def run_server():
    """Запуск сервера разработки"""
    print("🚀 Запуск сервера разработки...")
    print("🌐 Сервер будет доступен по адресу: http://127.0.0.1:8000")
    print("🔧 Админка: http://127.0.0.1:8000/admin")
    print("📱 API: http://127.0.0.1:8000/api/")
    print("\n💡 Для остановки сервера нажмите Ctrl+C")
    
    try:
        subprocess.call([
            'python', 'manage.py', 'runserver', 
            '--settings=myblog.settings_local',
            '--verbosity=2'
        ])
    except KeyboardInterrupt:
        print("\n👋 Сервер остановлен")

def main():
    """Основная функция"""
    print("🐍 Django Матрица Блог - Быстрый запуск")
    print("=" * 50)
    
    # Проверка наличия виртуального окружения
    venv_path = Path('venv')
    if not venv_path.exists() and not os.environ.get('VIRTUAL_ENV'):
        print("⚠️ Виртуальное окружение не обнаружено")
        print("💡 Рекомендуется создать виртуальное окружение:")
        print("   python -m venv venv")
        print("   source venv/bin/activate  # Linux/Mac")
        print("   venv\\Scripts\\activate     # Windows")
        print()
        response = input("Продолжить без виртуального окружения? (y/n): ")
        if response.lower() != 'y':
            return
    
    # Проверка Django
    try:
        import django
        print(f"✅ Django {django.get_version()} обнаружен")
    except ImportError:
        print("❌ Django не установлен")
        return
    
    # Установка зависимостей
    if not install_basic_dependencies():
        print("❌ Не удалось установить зависимости")
        return
    
    # Настройка БД
    if not setup_database():
        print("❌ Не удалось настроить базу данных")
        return
    
    # Проверка суперпользователя
    check_superuser()
    
    print("\n" + "=" * 50)
    print("🎉 Настройка завершена!")
    print("🔄 Запуск сервера...")
    
    # Запуск сервера
    run_server()

if __name__ == '__main__':
    main()