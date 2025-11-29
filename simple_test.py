#!/usr/bin/env python3
"""
Простой тест для проверки работоспособности системы тестирования
"""

import os
import sys
import django
from django.conf import settings

# Настройка минимального Django окружения
if not settings.configured:
    settings.configure(
        DEBUG=True,
        SECRET_KEY='test-secret-key-for-testing',
        INSTALLED_APPS=[
            'django.contrib.contenttypes',
            'django.contrib.auth',
            'blog',
        ],
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': ':memory:',
            }
        },
        USE_TZ=True,
    )

django.setup()

# Создание таблиц в памяти
from django.core.management import execute_from_command_line
execute_from_command_line(['manage.py', 'migrate', '--run-syncdb'])

# Тестирование
from django.test import TestCase
from django.contrib.auth.models import User
from blog.models import Post, Category

class SimpleBlogTest(TestCase):
    """Простые тесты блога"""
    
    def setUp(self):
        # Создаем тестового пользователя
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Создаем тестовую категорию
        self.category = Category.objects.create(
            name='Тестовая категория',
            description='Описание категории'
        )
    
    def test_user_creation(self):
        """Тест создания пользователя"""
        self.assertEqual(self.user.username, 'testuser')
        self.assertEqual(self.user.email, 'test@example.com')
        self.assertTrue(self.user.check_password('testpass123'))
    
    def test_category_creation(self):
        """Тест создания категории"""
        self.assertEqual(self.category.name, 'Тестовая категория')
        self.assertEqual(self.category.description, 'Описание категории')
    
    def test_post_creation(self):
        """Тест создания поста"""
        post = Post.objects.create(
            title='Тестовый пост',
            content='Содержимое тестового поста',
            author=self.user,
            category=self.category,
            status='published'
        )
        
        self.assertEqual(post.title, 'Тестовый пост')
        self.assertEqual(post.content, 'Содержимое тестового поста')
        self.assertEqual(post.author, self.user)
        self.assertEqual(post.category, self.category)
        self.assertEqual(post.status, 'published')
        self.assertTrue(post.published_date)
    
    def test_post_slug_generation(self):
        """Тест генерации слага"""
        post = Post.objects.create(
            title='Тестовое название поста',
            content='Содержимое',
            author=self.user,
            category=self.category,
            status='published'
        )
        
        self.assertTrue(post.slug)
        self.assertIn('testovoe-nazvanie-posta', post.slug)
    
    def test_post_str_representation(self):
        """Тест строкового представления поста"""
        post = Post.objects.create(
            title='Тестовый пост',
            content='Содержимое',
            author=self.user,
            status='published'
        )
        
        self.assertEqual(str(post), 'Тестовый пост')

if __name__ == '__main__':
    print("🧪 Запуск простых тестов блога...")
    
    # Создаем набор тестов
    from django.test.utils import get_runner
    from django.conf import settings
    
    TestRunner = get_runner(settings)
    test_runner = TestRunner(verbosity=2, interactive=False, keepdb=False)
    
    # Запускаем тесты
    failures = test_runner.run_tests(['__main__'])
    
    if failures:
        print(f"❌ {failures} тестов провалились")
        sys.exit(1)
    else:
        print("✅ Все тесты прошли успешно!")
        sys.exit(0)