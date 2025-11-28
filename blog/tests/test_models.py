"""
Тесты для моделей блога
"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from datetime import datetime, timedelta
import tempfile
import os

from blog.models import Post, Comment, Category, UserProfile, Notification, SiteSettings


class CategoryModelTest(TestCase):
    """Тесты для модели Category"""
    
    def setUp(self):
        self.category = Category.objects.create(
            name='Технологии',
            description='Статьи о технологиях',
            color='#00ff41'
        )
    
    def test_category_creation(self):
        """Тест создания категории"""
        self.assertEqual(self.category.name, 'Технологии')
        self.assertEqual(self.category.color, '#00ff41')
        self.assertTrue(self.category.created_date)
    
    def test_category_str_representation(self):
        """Тест строкового представления категории"""
        self.assertEqual(str(self.category), 'Технологии')
    
    def test_category_ordering(self):
        """Тест сортировки категорий"""
        cat2 = Category.objects.create(name='Наука', color='#ff0000')
        cat1 = Category.objects.create(name='Бизнес', color='#0000ff')
        
        categories = list(Category.objects.all())
        self.assertEqual(categories[0].name, 'Бизнес')
        self.assertEqual(categories[1].name, 'Наука')
        self.assertEqual(categories[2].name, 'Технологии')
    
    def test_category_unique_name(self):
        """Тест уникальности имени категории"""
        with self.assertRaises(Exception):
            Category.objects.create(name='Технологии')


class PostModelTest(TestCase):
    """Тесты для модели Post"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.category = Category.objects.create(name='Тест')
        
        # Создаем тестовое изображение
        self.image = SimpleUploadedFile(
            name='test_image.jpg',
            content=b'fake_image_content',
            content_type='image/jpeg'
        )
    
    def test_post_creation(self):
        """Тест создания поста"""
        post = Post.objects.create(
            title='Тестовый пост',
            content='Содержимое поста',
            author=self.user,
            category=self.category,
            status='published'
        )
        
        self.assertEqual(post.title, 'Тестовый пост')
        self.assertEqual(post.author, self.user)
        self.assertEqual(post.category, self.category)
        self.assertEqual(post.status, 'published')
        self.assertTrue(post.published_date)
        self.assertTrue(post.slug)
    
    def test_post_slug_generation(self):
        """Тест генерации слага"""
        post = Post.objects.create(
            title='Тест поста с длинным названием',
            content='Содержимое поста',
            author=self.user
        )
        
        self.assertTrue(post.slug)
        self.assertIn('test-posta-s-dlinnym-nazvaniem', post.slug)
    
    def test_post_excerpt_auto_generation(self):
        """Тест автоматической генерации выдержки"""
        content = 'A' * 350  # Создаем контент длиннее 300 символов
        post = Post.objects.create(
            title='Пост',
            content=content,
            author=self.user
        )
        
        self.assertTrue(post.excerpt)
        self.assertEqual(len(post.excerpt), 300)
        self.assertTrue(post.excerpt.endswith('...'))
    
    def test_post_published_date_on_status_change(self):
        """Тест установки даты публикации при изменении статуса"""
        post = Post.objects.create(
            title='Черновик',
            content='Содержимое',
            author=self.user,
            status='draft'
        )
        
        self.assertIsNone(post.published_date)
        
        # Меняем статус на published
        post.status = 'published'
        post.save()
        
        self.assertIsNotNone(post.published_date)
    
    def test_post_like_count(self):
        """Тест подсчета лайков"""
        post = Post.objects.create(
            title='Пост для лайков',
            content='Содержимое',
            author=self.user
        )
        
        self.assertEqual(post.like_count(), 0)
        
        # Добавляем лайки
        post.likes.add(self.user)
        self.assertEqual(post.like_count(), 1)
    
    def test_post_comment_count(self):
        """Тест подсчета комментариев"""
        post = Post.objects.create(
            title='Пост для комментариев',
            content='Содержимое',
            author=self.user
        )
        
        comment = Comment.objects.create(
            post=post,
            author=self.user,
            text='Отличный пост!'
        )
        
        self.assertEqual(post.comment_count(), 1)
    
    def test_post_is_published(self):
        """Тест метода проверки публикации"""
        published_post = Post.objects.create(
            title='Опубликованный пост',
            content='Содержимое',
            author=self.user,
            status='published'
        )
        
        draft_post = Post.objects.create(
            title='Черновик',
            content='Содержимое',
            author=self.user,
            status='draft'
        )
        
        self.assertTrue(published_post.is_published())
        self.assertFalse(draft_post.is_published())
    
    def test_post_get_absolute_url(self):
        """Тест получения абсолютного URL"""
        post = Post.objects.create(
            title='Пост',
            content='Содержимое',
            author=self.user,
            status='published'
        )
        
        url = post.get_absolute_url()
        self.assertIn(f'/posts/{post.pk}/{post.slug}/', url)


class CommentModelTest(TestCase):
    """Тесты для модели Comment"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.post = Post.objects.create(
            title='Пост',
            content='Содержимое',
            author=self.user
        )
    
    def test_comment_creation(self):
        """Тест создания комментария"""
        comment = Comment.objects.create(
            post=self.post,
            author=self.user,
            text='Отличный пост!'
        )
        
        self.assertEqual(comment.post, self.post)
        self.assertEqual(comment.author, self.user)
        self.assertEqual(comment.text, 'Отличный пост!')
        self.assertTrue(comment.is_active)
    
    def test_comment_str_representation(self):
        """Тест строкового представления комментария"""
        comment = Comment.objects.create(
            post=self.post,
            author=self.user,
            text='Комментарий'
        )
        
        expected = f'Comment by {self.user.username} on {self.post.title}'
        self.assertEqual(str(comment), expected)
    
    def test_comment_reply_count(self):
        """Тест подсчета ответов"""
        comment = Comment.objects.create(
            post=self.post,
            author=self.user,
            text='Основной комментарий'
        )
        
        # Создаем ответ на комментарий
        reply = Comment.objects.create(
            post=self.post,
            author=self.user,
            text='Ответ на комментарий',
            parent=comment
        )
        
        self.assertEqual(comment.reply_count(), 1)
    
    def test_comment_like_count(self):
        """Тест подсчета лайков комментария"""
        comment = Comment.objects.create(
            post=self.post,
            author=self.user,
            text='Комментарий для лайков'
        )
        
        self.assertEqual(comment.like_count(), 0)
        
        comment.likes.add(self.user)
        self.assertEqual(comment.like_count(), 1)


class UserProfileModelTest(TestCase):
    """Тесты для модели UserProfile"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_profile_creation(self):
        """Тест создания профиля пользователя"""
        # Profile должен создаваться автоматически через сигналы
        self.assertTrue(UserProfile.objects.filter(user=self.user).exists())
        
        profile = self.user.profile
        self.assertEqual(profile.user, self.user)
    
    def test_profile_str_representation(self):
        """Тест строкового представления профиля"""
        profile = self.user.profile
        expected = f'{self.user.username} Profile'
        self.assertEqual(str(profile), expected)
    
    def test_profile_ban_functionality(self):
        """Тест функционала бана"""
        profile = self.user.profile
        
        # Тест активного бана
        profile.is_banned = True
        profile.ban_reason = 'Нарушение правил'
        profile.ban_expires = timezone.now() + timedelta(days=7)
        profile.save()
        
        self.assertTrue(profile.is_currently_banned())
        
        # Тест истечения бана
        profile.ban_expires = timezone.now() - timedelta(days=1)
        profile.save()
        
        self.assertFalse(profile.is_currently_banned())
        self.assertFalse(profile.is_banned)  # Должен автоматически сброситься


class NotificationModelTest(TestCase):
    """Тесты для модели Notification"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.post = Post.objects.create(
            title='Пост',
            content='Содержимое',
            author=self.user
        )
    
    def test_notification_creation(self):
        """Тест создания уведомления"""
        notification = Notification.objects.create(
            user=self.user,
            notification_type='system',
            title='Добро пожаловать!',
            message='Добро пожаловать в блог!'
        )
        
        self.assertEqual(notification.user, self.user)
        self.assertEqual(notification.notification_type, 'system')
        self.assertFalse(notification.is_read)
    
    def test_notification_str_representation(self):
        """Тест строкового представления уведомления"""
        notification = Notification.objects.create(
            user=self.user,
            notification_type='system',
            title='Тестовое уведомление',
            message='Тестовое сообщение'
        )
        
        expected = f'Notification for {self.user.username}: Тестовое уведомление'
        self.assertEqual(str(notification), expected)


class SiteSettingsModelTest(TestCase):
    """Тесты для модели SiteSettings"""
    
    def test_site_settings_singleton(self):
        """Тест синглтона настроек сайта"""
        # Создаем первые настройки
        settings1 = SiteSettings.objects.create(
            site_name='Тестовый блог',
            site_description='Описание блога'
        )
        
        # Пытаемся создать вторые настройки (должно быть запрещено)
        with self.assertRaises(ValidationError):
            SiteSettings.objects.create(
                site_name='Другой блог',
                site_description='Другое описание'
            )
    
    def test_site_settings_load_method(self):
        """Тест метода load()"""
        # Если настроек нет, они должны создаться
        settings = SiteSettings.load()
        self.assertIsNotNone(settings)
        self.assertEqual(settings.site_name, 'The Matrix Blog')
        
        # Если настройки есть, должен вернуться существующий объект
        settings.site_name = 'Измененное имя'
        settings.save()
        
        loaded_settings = SiteSettings.load()
        self.assertEqual(loaded_settings.site_name, 'Измененное имя')
        self.assertEqual(loaded_settings.pk, settings.pk)


class PostOrderingTest(TestCase):
    """Тесты сортировки постов"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_post_ordering_by_published_date(self):
        """Тест сортировки по дате публикации"""
        now = timezone.now()
        
        post1 = Post.objects.create(
            title='Первый пост',
            content='Содержимое',
            author=self.user,
            status='published',
            published_date=now - timedelta(days=2)
        )
        
        post2 = Post.objects.create(
            title='Второй пост',
            content='Содержимое',
            author=self.user,
            status='published',
            published_date=now
        )
        
        post3 = Post.objects.create(
            title='Третий пост',
            content='Содержимое',
            author=self.user,
            status='published',
            published_date=now - timedelta(days=1)
        )
        
        posts = list(Post.objects.all())
        
        # Посты должны быть отсортированы по убыванию даты публикации
        self.assertEqual(posts[0], post2)  # Самый новый
        self.assertEqual(posts[1], post3)
        self.assertEqual(posts[2], post1)  # Самый старый


class PostImageFieldTest(TestCase):
    """Тесты для поля изображения в постах"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_post_with_image(self):
        """Тест поста с изображением"""
        image = SimpleUploadedFile(
            name='test_image.jpg',
            content=b'fake_image_content',
            content_type='image/jpeg'
        )
        
        post = Post.objects.create(
            title='Пост с изображением',
            content='Содержимое',
            author=self.user,
            image=image
        )
        
        self.assertTrue(post.image)
        self.assertIn('posts/', post.image.name)
    
    def test_post_without_image(self):
        """Тест поста без изображения"""
        post = Post.objects.create(
            title='Пост без изображения',
            content='Содержимое',
            author=self.user
        )
        
        self.assertFalse(post.image)


class CommentOrderingTest(TestCase):
    """Тесты сортировки комментариев"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.post = Post.objects.create(
            title='Пост',
            content='Содержимое',
            author=self.user
        )
    
    def test_comment_ordering_by_created_date(self):
        """Тест сортировки комментариев по дате создания"""
        now = timezone.now()
        
        comment1 = Comment.objects.create(
            post=self.post,
            author=self.user,
            text='Первый комментарий',
            created_date=now - timedelta(hours=2)
        )
        
        comment2 = Comment.objects.create(
            post=self.post,
            author=self.user,
            text='Второй комментарий',
            created_date=now
        )
        
        comment3 = Comment.objects.create(
            post=self.post,
            author=self.user,
            text='Третий комментарий',
            created_date=now - timedelta(hours=1)
        )
        
        comments = list(Comment.objects.all())
        
        # Комментарии должны быть отсортированы по убыванию даты создания
        self.assertEqual(comments[0], comment2)  # Самый новый
        self.assertEqual(comments[1], comment3)
        self.assertEqual(comments[2], comment1)  # Самый старый