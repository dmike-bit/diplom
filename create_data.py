import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myblog.settings')
django.setup()

from django.contrib.auth.models import User
from blog.models import Category, SiteSettings

# Создаем категории
categories = [
    {'name': 'Технологии', 'slug': 'technologies'},
    {'name': 'Матрица', 'slug': 'matrix'},
    {'name': 'Программирование', 'slug': 'programming'},
    {'name': 'Искусственный интеллект', 'slug': 'ai'},
    {'name': 'Киберпанк', 'slug': 'cyberpunk'}
]

for cat_data in categories:
    Category.objects.get_or_create(
        name=cat_data['name'],
        slug=cat_data['slug'],
        defaults={'description': f'Категория {cat_data["name"]}'}
    )

# Создаем настройки сайта
site_settings, created = SiteSettings.objects.get_or_create(
    site_name='The Matrix Blog',
    defaults={
        'tagline': 'Добро пожаловать в Матрицу',
        'allow_registration': True,
        'posts_per_page': 10
    }
)

print("Данные созданы успешно!")
