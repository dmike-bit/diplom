from django.core.management.base import BaseCommand
from blog.models import Category, SiteSettings, Post, UserProfile
from django.contrib.auth.models import User
from django.utils import timezone

class Command(BaseCommand):
    help = 'Create sample data for the blog'

    def handle(self, *args, **options):
        # Создаем настройки сайта
        SiteSettings.objects.get_or_create(
            pk=1,
            defaults={
                'site_name': 'The Matrix Blog',
                'site_description': 'Welcome to the Matrix. The choice is yours.',
                'admin_email': 'admin@matrix.com',
                'posts_per_page': 10,
                'allow_registration': True,
                'allow_comments': True,
            }
        )

        # Создаем категории
        categories_data = [
            {'name': 'Hacking', 'color': '#00ff41', 'description': 'The art of hacking the system'},
            {'name': 'Programming', 'color': '#00ccff', 'description': 'Code that breaks the matrix'},
            {'name': 'Security', 'color': '#ff4444', 'description': 'Staying safe in the digital world'},
            {'name': 'News', 'color': '#ffff00', 'description': 'Latest matrix updates'},
            {'name': 'Tutorials', 'color': '#ff00ff', 'description': 'Learn to bend the rules'},
        ]

        for cat_data in categories_data:
            Category.objects.get_or_create(name=cat_data['name'], defaults=cat_data)

        # Создаем тестового пользователя
        user, created = User.objects.get_or_create(
            username='neo',
            defaults={
                'email': 'neo@matrix.com',
                'first_name': 'Thomas',
                'last_name': 'Anderson'
            }
        )
        if created:
            user.set_password('redpill')
            user.save()

        # Создаем тестовые посты
        if created:
            hacking_cat = Category.objects.get(name='Hacking')
            news_cat = Category.objects.get(name='News')
            
            Post.objects.get_or_create(
                title='Welcome to the Matrix',
                defaults={
                    'content': 'This is your last chance. After this, there is no turning back. You take the blue pill... the story ends, you wake up in your bed and believe whatever you want to believe. You take the red pill... you stay in Wonderland and I show you how deep the rabbit-hole goes.',
                    'author': user,
                    'category': news_cat,
                    'status': 'published',
                    'published_date': timezone.now(),
                    'excerpt': 'The choice is yours. Red pill or blue pill?',
                    'tags': 'matrix, redpill, bluepill'
                }
            )
            
            Post.objects.get_or_create(
                title='How to Hack the Mainframe',
                defaults={
                    'content': 'The first rule of hacking: there are no rules. The system is designed to keep you in, but with the right knowledge, you can break free. Learn the patterns, understand the code, and you\'ll see the truth behind the illusion.',
                    'author': user,
                    'category': hacking_cat,
                    'status': 'published',
                    'published_date': timezone.now(),
                    'excerpt': 'Breaking free from the system requires understanding its weaknesses.',
                    'tags': 'hacking, mainframe, freedom'
                }
            )

        self.stdout.write(self.style.SUCCESS('Successfully created sample data!'))
        self.stdout.write(self.style.SUCCESS('Test user: neo / redpill'))
        self.stdout.write(self.style.SUCCESS('Admin: Create with: python manage.py createsuperuser'))
