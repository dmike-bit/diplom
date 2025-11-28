#!/usr/bin/env python3
"""
Скрипт для запуска тестов блога Matrix Blog

Зависимости:
pip install -r requirements.txt
pip install -r requirements-test.txt

Или минимальные зависимости:
pip install Django==4.2.7 djangorestframework djangorestframework-simplejwt pillow
"""

import os
import sys
import subprocess
import argparse

def run_tests():
    """Запуск тестов"""
    print("🚀 Запуск тестов Matrix Blog...")
    
    # Команды для запуска тестов
    commands = [
        ["python3", "manage.py", "test", "blog.tests.test_models", "--verbosity=2"],
        ["python3", "manage.py", "test", "blog.tests.test_forms", "--verbosity=2"],
        ["python3", "manage.py", "test", "blog.tests.test_signals", "--verbosity=2"],
    ]
    
    for cmd in commands:
        print(f"\n▶️  Выполняется: {' '.join(cmd)}")
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ {cmd[3]} - УСПЕШНО")
                if result.stdout:
                    print(result.stdout[-500:])  # Последние 500 символов вывода
            else:
                print(f"❌ {cmd[3]} - ОШИБКА")
                print(result.stderr)
                if result.stdout:
                    print(result.stdout[-500:])
        except Exception as e:
            print(f"❌ Ошибка выполнения {cmd[3]}: {e}")

def install_dependencies():
    """Установка зависимостей"""
    print("📦 Установка зависимостей...")
    
    try:
        print("Устанавливаем основные зависимости...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
        
        print("Устанавливаем тестовые зависимости...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements-test.txt"], check=True)
        
        print("✅ Зависимости установлены")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка установки зависимостей: {e}")
        return False

def check_dependencies():
    """Проверка зависимостей"""
    print("🔍 Проверка зависимостей...")
    
    required = ["django", "rest_framework", "django_filters"]
    missing = []
    
    for package in required:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package}")
            missing.append(package)
    
    if missing:
        print(f"\n⚠️  Отсутствующие зависимости: {', '.join(missing)}")
        return False
    
    return True

def main():
    parser = argparse.ArgumentParser(description="Запуск тестов Matrix Blog")
    parser.add_argument("--install", action="store_true", help="Установить зависимости")
    parser.add_argument("--check", action="store_true", help="Проверить зависимости")
    parser.add_argument("--coverage", action="store_true", help="Запуск с покрытием")
    
    args = parser.parse_args()
    
    if args.check:
        check_dependencies()
        return
    
    if args.install:
        install_dependencies()
        return
    
    if args.coverage:
        print("📊 Запуск тестов с покрытием...")
        try:
            subprocess.run(["coverage", "run", "--source='.'", "manage.py", "test", "blog.tests", "--verbosity=1"], check=True)
            subprocess.run(["coverage", "report"], check=True)
            subprocess.run(["coverage", "html"], check=True)
            print("📈 Отчет о покрытии создан в htmlcov/")
        except subprocess.CalledProcessError as e:
            print(f"❌ Ошибка запуска с покрытием: {e}")
        return
    
    # Основная логика
    if not check_dependencies():
        print("\n❌ Не все зависимости установлены. Используйте --install для установки.")
        return
    
    run_tests()

if __name__ == "__main__":
    main()