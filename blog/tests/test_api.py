"""
Тесты для API блога
"""

from django.test import TestCase, APITestCase
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from datetime import datetime, timedelta

from blog.models import Post, Comment, Category, UserProfile, Notification
from blog.api.serializers import (
    PostSerializer, PostListSerializer, CommentSerializer,
    CategorySerializer, UserSerializer, NotificationSerializer,
    RegisterSerializer, LoginSerializer
)


class APITestCaseMixin:
    """Миксин для API тестов с аутентификацией"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Тест',
            last_name='Пользователь'
        )
        
        self.other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='otherpass123'
        )
        
        self.category = Category.objects.create(
            name='Технологии',
            description='Статьи о технологиях',
            color='#00ff41'
        )
        
        # Создаем токены для аутентификации
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)
        self.refresh_token = str(refresh)
        
        # Создаем тестовый пост
        self.post = Post.objects.create(
            title='Тестовый пост',
            content='Содержимое поста',
            author=self.user,
            category=self.category,
            status='published'
        )
        
        # Создаем тестовый комментарий
        self.comment = Comment.objects.create(
            post=self.post,
            author=self.user,
            text='Тестовый комментарий'
        )


class CategoryAPITest(APITestCaseMixin, APITestCase):
    """Тесты API категорий"""
    
    def test_get_category_list_unauthorized(self):
        """Тест получения списка категорий без аутентификации"""
        response = self.client.get('/api/categories/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_get_category_list_authorized(self):
        """Тест получения списка категорий с аутентификацией"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        response = self.client.get('/api/categories/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        categories = response.json()
        self.assertEqual(len(categories), 1)
        self.assertEqual(categories[0]['name'], 'Технологии')
        self.assertEqual(categories[0]['post_count'], 1)
    
    def test_create_category_unauthorized(self):
        """Тест создания категории без аутентификации"""
        data = {'name': 'Наука', 'description': 'Научные статьи', 'color': '#ff0000'}
        response = self.client.post('/api/categories/', data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_create_category_authorized(self):
        """Тест создания категории с аутентификацией"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        data = {'name': 'Наука', 'description': 'Научные статьи', 'color': '#ff0000'}
        response = self.client.post('/api/categories/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        self.assertTrue(Category.objects.filter(name='Наука').exists())
    
    def test_get_category_detail(self):
        """Тест получения детальной информации о категории"""
        response = self.client.get(f'/api/categories/{self.category.pk}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertEqual(data['name'], 'Технологии')
        self.assertEqual(data['post_count'], 1)


class PostAPITest(APITestCaseMixin, APITestCase):
    """Тесты API постов"""
    
    def test_get_post_list_unauthorized(self):
        """Тест получения списка постов без аутентификации"""
        response = self.client.get('/api/posts/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        posts = response.json()
        self.assertEqual(len(posts['results']), 1)  # Один опубликованный пост
        
        # Черновики не должны отображаться
        draft_post = Post.objects.create(
            title='Черновик',
            content='Содержимое',
            author=self.user,
            category=self.category,
            status='draft'
        )
        
        response = self.client.get('/api/posts/')
        posts = response.json()
        self.assertEqual(len(posts['results']), 1)
    
    def test_get_post_list_authorized(self):
        """Тест получения списка постов с аутентификацией"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        response = self.client.get('/api/posts/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        posts = response.json()
        self.assertEqual(len(posts['results']), 1)
    
    def test_get_post_detail(self):
        """Тест получения детальной информации о посте"""
        response = self.client.get(f'/api/posts/{self.post.pk}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertEqual(data['title'], 'Тестовый пост')
        self.assertEqual(data['author']['username'], 'testuser')
        self.assertEqual(data['category']['name'], 'Технологии')
        self.assertIn('comments', data)
        self.assertIn('like_count', data)
        self.assertIn('comment_count', data)
    
    def test_create_post_unauthorized(self):
        """Тест создания поста без аутентификации"""
        data = {
            'title': 'Новый пост',
            'content': 'Содержимое нового поста',
            'category': self.category.pk,
            'status': 'published'
        }
        response = self.client.post('/api/posts/', data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_create_post_authorized(self):
        """Тест создания поста с аутентификацией"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        data = {
            'title': 'Новый пост',
            'content': 'Содержимое нового поста',
            'category': self.category.pk,
            'status': 'published'
        }
        response = self.client.post('/api/posts/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        self.assertTrue(Post.objects.filter(title='Новый пост').exists())
        
        created_post = Post.objects.get(title='Новый пост')
        self.assertEqual(created_post.author, self.user)
        self.assertEqual(created_post.status, 'published')
    
    def test_update_post_owner(self):
        """Тест редактирования поста владельцем"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        
        data = {
            'title': 'Измененный пост',
            'content': 'Измененное содержимое',
            'category': self.category.pk,
            'status': 'published'
        }
        
        response = self.client.put(f'/api/posts/{self.post.pk}/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.post.refresh_from_db()
        self.assertEqual(self.post.title, 'Измененный пост')
    
    def test_update_post_other_user(self):
        """Тест редактирования чужого поста"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        
        # Создаем пост другого пользователя
        other_post = Post.objects.create(
            title='Чужой пост',
            content='Содержимое',
            author=self.other_user,
            category=self.category,
            status='published'
        )
        
        data = {
            'title': 'Измененный пост',
            'content': 'Измененное содержимое',
            'category': self.category.pk,
            'status': 'published'
        }
        
        response = self.client.put(f'/api/posts/{other_post.pk}/', data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_delete_post_owner(self):
        """Тест удаления поста владельцем"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        
        response = self.client.delete(f'/api/posts/{self.post.pk}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        self.assertFalse(Post.objects.filter(pk=self.post.pk).exists())
    
    def test_post_like_unauthorized(self):
        """Тест лайка поста без аутентификации"""
        response = self.client.post(f'/api/posts/{self.post.pk}/like/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_post_like_authorized(self):
        """Тест лайка поста с аутентификацией"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        
        # Лайкаем пост
        response = self.client.post(f'/api/posts/{self.post.pk}/like/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertTrue(data['liked'])
        self.assertEqual(data['like_count'], 1)
        
        # Проверяем, что лайк добавился
        self.assertTrue(self.post.likes.filter(id=self.user.id).exists())
        
        # Дизлайкаем пост
        response = self.client.post(f'/api/posts/{self.post.pk}/like/')
        data = response.json()
        self.assertFalse(data['liked'])
        self.assertEqual(data['like_count'], 0)
    
    def test_post_filtering(self):
        """Тест фильтрации постов"""
        # Создаем посты с разными статусами
        Post.objects.create(
            title='Черновик',
            content='Содержимое',
            author=self.user,
            category=self.category,
            status='draft'
        )
        
        Post.objects.create(
            title='Опубликованный',
            content='Содержимое',
            author=self.user,
            category=self.category,
            status='published'
        )
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        
        # Фильтр по статусу
        response = self.client.get('/api/posts/?status=published')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        posts = response.json()['results']
        self.assertEqual(len(posts), 2)  # Оригинальный + новый опубликованный
        
        # Фильтр по категории
        response = self.client.get(f'/api/posts/?category={self.category.pk}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        posts = response.json()['results']
        self.assertEqual(len(posts), 3)  # Все посты в этой категории
    
    def test_post_search(self):
        """Тест поиска по постам"""
        Post.objects.create(
            title='Python Tutorial',
            content='Учебник по Python',
            author=self.user,
            category=self.category,
            status='published'
        )
        
        response = self.client.get('/api/posts/?search=Python')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        posts = response.json()['results']
        self.assertEqual(len(posts), 1)
        self.assertEqual(posts[0]['title'], 'Python Tutorial')
    
    def test_post_ordering(self):
        """Тест сортировки постов"""
        # Создаем посты с разными датами
        post2 = Post.objects.create(
            title='Второй пост',
            content='Содержимое',
            author=self.user,
            category=self.category,
            status='published',
            created_date=timezone.now() - timedelta(days=1)
        )
        
        post3 = Post.objects.create(
            title='Третий пост',
            content='Содержимое',
            author=self.user,
            category=self.category,
            status='published',
            created_date=timezone.now() - timedelta(days=2)
        )
        
        response = self.client.get('/api/posts/?ordering=-created_date')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        posts = response.json()['results']
        
        # Посты должны быть отсортированы по убыванию даты создания
        self.assertEqual(posts[0]['title'], 'Тестовый пост')  # Самый новый
        self.assertEqual(posts[1]['title'], 'Второй пост')
        self.assertEqual(posts[2]['title'], 'Третий пост')  # Самый старый


class CommentAPITest(APITestCaseMixin, APITestCase):
    """Тесты API комментариев"""
    
    def test_get_comment_list_unauthorized(self):
        """Тест получения списка комментариев без аутентификации"""
        response = self.client.get(f'/api/posts/{self.post.pk}/comments/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        comments = response.json()
        self.assertEqual(len(comments), 1)
        self.assertEqual(comments[0]['text'], 'Тестовый комментарий')
    
    def test_create_comment_unauthorized(self):
        """Тест создания комментария без аутентификации"""
        data = {'text': 'Новый комментарий'}
        response = self.client.post(f'/api/posts/{self.post.pk}/comments/', data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_create_comment_authorized(self):
        """Тест создания комментария с аутентификацией"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        data = {'text': 'Новый комментарий'}
        response = self.client.post(f'/api/posts/{self.post.pk}/comments/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        self.assertTrue(Comment.objects.filter(text='Новый комментарий').exists())
        
        created_comment = Comment.objects.get(text='Новый комментарий')
        self.assertEqual(created_comment.author, self.user)
        self.assertEqual(created_comment.post, self.post)
    
    def test_comment_reply(self):
        """Тест создания ответа на комментарий"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        data = {'text': 'Ответ на комментарий'}
        response = self.client.post(f'/api/comments/{self.comment.pk}/replies/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        self.assertTrue(Comment.objects.filter(text='Ответ на комментарий').exists())
        
        reply = Comment.objects.get(text='Ответ на комментарий')
        self.assertEqual(reply.parent, self.comment)
        self.assertEqual(reply.author, self.user)
    
    def test_comment_like_unauthorized(self):
        """Тест лайка комментария без аутентификации"""
        response = self.client.post(f'/api/comments/{self.comment.pk}/like/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_comment_like_authorized(self):
        """Тест лайка комментария с аутентификацией"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        
        # Лайкаем комментарий
        response = self.client.post(f'/api/comments/{self.comment.pk}/like/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertTrue(data['liked'])
        self.assertEqual(data['like_count'], 1)
        
        # Проверяем, что лайк добавился
        self.assertTrue(self.comment.likes.filter(id=self.user.id).exists())
    
    def test_comment_update_other_user(self):
        """Тест редактирования чужого комментария"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        
        # Создаем комментарий другого пользователя
        other_comment = Comment.objects.create(
            post=self.post,
            author=self.other_user,
            text='Чужой комментарий'
        )
        
        data = {'text': 'Измененный текст'}
        response = self.client.patch(f'/api/comments/{other_comment.pk}/', data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class UserProfileAPITest(APITestCaseMixin, APITestCase):
    """Тесты API профилей пользователей"""
    
    def test_get_user_profile_list(self):
        """Тест получения списка пользователей"""
        response = self.client.get('/api/users/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        users = response.json()['results']
        self.assertEqual(len(users), 2)
        self.assertEqual(users[0]['username'], 'otheruser')
        self.assertEqual(users[1]['username'], 'testuser')
    
    def test_get_own_profile(self):
        """Тест получения своего профиля"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        response = self.client.get(f'/api/users/{self.user.pk}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertEqual(data['username'], 'testuser')
        self.assertIn('profile', data)
        self.assertIn('post_count', data)
    
    def test_get_other_user_profile(self):
        """Тест получения чужого профиля"""
        response = self.client.get(f'/api/users/{self.other_user.pk}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertEqual(data['username'], 'otheruser')
        # Для чужого профиля должна отображаться только базовая информация
        self.assertNotIn('profile', data)
    
    def test_user_profile_action(self):
        """Тест действия profile для пользователя"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        response = self.client.get(f'/api/users/{self.user.pk}/profile/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertIn('user', data)
        self.assertIn('profile', data)
        self.assertEqual(data['profile']['bio'], '')


class NotificationAPITest(APITestCaseMixin, APITestCase):
    """Тесты API уведомлений"""
    
    def setUp(self):
        super().setUp()
        # Создаем несколько уведомлений
        self.notification1 = Notification.objects.create(
            user=self.user,
            notification_type='system',
            title='Уведомление 1',
            message='Сообщение 1'
        )
        
        self.notification2 = Notification.objects.create(
            user=self.user,
            notification_type='comment',
            title='Уведомление 2',
            message='Сообщение 2',
            is_read=True
        )
        
        self.notification3 = Notification.objects.create(
            user=self.other_user,
            notification_type='system',
            title='Чужое уведомление',
            message='Чужое сообщение'
        )
    
    def test_get_notification_list_own(self):
        """Тест получения списка своих уведомлений"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        response = self.client.get('/api/notifications/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        notifications = response.json()['results']
        # Должны быть только свои уведомления
        self.assertEqual(len(notifications), 2)
        self.assertEqual(notifications[0]['title'], 'Уведомление 2')
        self.assertEqual(notifications[1]['title'], 'Уведомление 1')
    
    def test_get_unread_notifications(self):
        """Тест получения непрочитанных уведомлений"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        response = self.client.get('/api/notifications/unread/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        notifications = response.json()
        self.assertEqual(len(notifications), 1)
        self.assertEqual(notifications[0]['title'], 'Уведомление 1')
        self.assertFalse(notifications[0]['is_read'])
    
    def test_mark_notification_read(self):
        """Тест пометки уведомления как прочитанного"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        response = self.client.post(f'/api/notifications/{self.notification1.pk}/mark_read/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.notification1.refresh_from_db()
        self.assertTrue(self.notification1.is_read)


class AuthenticationAPITest(APITestCase):
    """Тесты аутентификации API"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_register_api(self):
        """Тест регистрации через API"""
        data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'first_name': 'Новый',
            'last_name': 'Пользователь',
            'password': 'newpassword123',
            'password_confirm': 'newpassword123'
        }
        
        response = self.client.post('/api/auth/register/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Проверяем создание пользователя
        self.assertTrue(User.objects.filter(username='newuser').exists())
        
        # Проверяем возвращаемые данные
        data = response.json()
        self.assertIn('user', data)
        self.assertIn('access', data)
        self.assertIn('refresh', data)
    
    def test_register_invalid_data(self):
        """Тест регистрации с невалидными данными"""
        data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password': '123',  # Слишком короткий пароль
            'password_confirm': '456'  # Пароли не совпадают
        }
        
        response = self.client.post('/api/auth/register/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_login_api(self):
        """Тест входа через API"""
        data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        
        response = self.client.post('/api/auth/login/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertIn('user', data)
        self.assertIn('access', data)
        self.assertIn('refresh', data)
        self.assertEqual(data['user']['username'], 'testuser')
    
    def test_login_invalid_credentials(self):
        """Тест входа с неверными учетными данными"""
        data = {
            'username': 'testuser',
            'password': 'wrongpassword'
        }
        
        response = self.client.post('/api/auth/login/', data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_user_profile_api(self):
        """Тест получения профиля пользователя через API"""
        # Сначала входим в систему
        login_data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        login_response = self.client.post('/api/auth/login/', login_data)
        access_token = login_response.json()['access']
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        response = self.client.get('/api/auth/profile/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertIn('user', data)
        self.assertIn('recent_posts', data)
        self.assertIn('unread_notifications', data)


class SiteInfoAPITest(APITestCase):
    """Тесты публичной информации о сайте"""
    
    def test_site_info(self):
        """Тест получения информации о сайте"""
        response = self.client.get('/api/site/info/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertIn('site_name', data)
        self.assertIn('site_description', data)
        self.assertIn('posts_per_page', data)
        self.assertIn('allow_registration', data)
        self.assertIn('allow_comments', data)


class SerializerTest(TestCase):
    """Тесты сериализаторов"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Тест',
            last_name='Пользователь'
        )
        
        self.category = Category.objects.create(
            name='Технологии',
            description='Статьи о технологиях'
        )
        
        self.post = Post.objects.create(
            title='Тестовый пост',
            content='Содержимое поста',
            author=self.user,
            category=self.category,
            status='published'
        )
        
        self.comment = Comment.objects.create(
            post=self.post,
            author=self.user,
            text='Тестовый комментарий'
        )
    
    def test_post_serializer(self):
        """Тест сериализатора поста"""
        serializer = PostSerializer(self.post)
        
        data = serializer.data
        self.assertEqual(data['title'], 'Тестовый пост')
        self.assertEqual(data['author']['username'], 'testuser')
        self.assertEqual(data['category']['name'], 'Технологии')
        self.assertIn('like_count', data)
        self.assertIn('comment_count', data)
        self.assertIn('comments', data)
    
    def test_post_list_serializer(self):
        """Тест сериализатора списка постов"""
        serializer = PostListSerializer(self.post)
        
        data = serializer.data
        self.assertEqual(data['title'], 'Тестовый пост')
        self.assertEqual(data['author']['username'], 'testuser')
        self.assertEqual(data['category']['name'], 'Технологии')
        self.assertIn('like_count', data)
        self.assertEqual(data['comment_count'], 1)
        self.assertNotIn('comments', data)  # Комментарии не должны быть в списке
    
    def test_comment_serializer(self):
        """Тест сериализатора комментария"""
        serializer = CommentSerializer(self.comment)
        
        data = serializer.data
        self.assertEqual(data['text'], 'Тестовый комментарий')
        self.assertEqual(data['author']['username'], 'testuser')
        self.assertEqual(data['post'], self.post.pk)
        self.assertIn('replies', data)
        self.assertIn('like_count', data)
    
    def test_category_serializer(self):
        """Тест сериализатора категории"""
        serializer = CategorySerializer(self.category)
        
        data = serializer.data
        self.assertEqual(data['name'], 'Технологии')
        self.assertEqual(data['description'], 'Статьи о технологиях')
        self.assertEqual(data['post_count'], 1)
    
    def test_user_serializer(self):
        """Тест сериализатора пользователя"""
        serializer = UserSerializer(self.user)
        
        data = serializer.data
        self.assertEqual(data['username'], 'testuser')
        self.assertEqual(data['first_name'], 'Тест')
        self.assertEqual(data['last_name'], 'Пользователь')
        self.assertEqual(data['post_count'], 1)
        self.assertIn('profile', data)


class PermissionTest(APITestCaseMixin, APITestCase):
    """Тесты прав доступа"""
    
    def test_read_only_for_unauthenticated(self):
        """Тест разрешений только на чтение для неаутентифицированных пользователей"""
        # Неаутентифицированный пользователь может только читать
        response = self.client.get('/api/categories/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        response = self.client.get('/api/posts/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        response = self.client.post('/api/categories/', {'name': 'Наука'})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        response = self.client.post('/api/posts/', {'title': 'Новый пост', 'content': 'Содержимое'})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_owner_permissions(self):
        """Тест прав владельца"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        
        # Владелец может редактировать и удалять свои посты
        response = self.client.patch(f'/api/posts/{self.post.pk}/', {
            'title': 'Измененный пост',
            'content': 'Измененное содержимое'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Владелец может удалять свои посты
        new_post = Post.objects.create(
            title='Удаляемый пост',
            content='Содержимое',
            author=self.user,
            category=self.category,
            status='published'
        )
        
        response = self.client.delete(f'/api/posts/{new_post.pk}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
    
    def test_staff_permissions(self):
        """Тест прав администратора"""
        # Делаем пользователя администратором
        self.user.is_staff = True
        self.user.save()
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        
        # Администратор может редактировать любые посты
        other_post = Post.objects.create(
            title='Чужой пост',
            content='Содержимое',
            author=self.other_user,
            category=self.category,
            status='published'
        )
        
        response = self.client.patch(f'/api/posts/{other_post.pk}/', {
            'title': 'Измененный пост',
            'content': 'Измененное содержимое'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)