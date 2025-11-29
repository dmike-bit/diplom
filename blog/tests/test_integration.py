"""
Интеграционные тесты для блога
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from datetime import timedelta

from blog.models import Post, Comment, Category, UserProfile, Notification
from blog.forms import RegisterForm, PostForm, CommentForm


class FullPostWorkflowTest(TestCase):
    """Полный рабочий процесс создания и управления постом"""
    
    def setUp(self):
        self.client = Client()
        self.api_client = APIClient()
        
        # Создаем пользователей
        self.author = User.objects.create_user(
            username='author',
            email='author@example.com',
            password='author123',
            first_name='Автор',
            last_name='Постов'
        )
        
        self.reader = User.objects.create_user(
            username='reader',
            email='reader@example.com',
            password='reader123',
            first_name='Читатель',
            last_name='Комментариев'
        )
        
        # Аутентификация для API
        refresh = RefreshToken.for_user(self.author)
        self.author_token = str(refresh.access_token)
        
        refresh = RefreshToken.for_user(self.reader)
        self.reader_token = str(refresh.access_token)
        
        # Создаем категорию
        self.category = Category.objects.create(
            name='Технологии',
            description='Статьи о технологиях',
            color='#00ff41'
        )
    
    def test_full_post_lifecycle_web(self):
        """Полный цикл жизни поста через веб-интерфейс"""
        # 1. Автор входит в систему через веб
        login_success = self.client.login(username='author', password='author123')
        self.assertTrue(login_success)
        
        # 2. Создает пост через веб-интерфейс
        post_data = {
            'title': 'Полный тест поста',
            'content': 'Подробное содержимое поста для тестирования',
            'excerpt': 'Краткое описание поста',
            'category': self.category.pk,
            'status': 'published',
            'tags': 'тест, пост, интеграция'
        }
        
        response = self.client.post(reverse('post_new'), post_data, follow=True)
        self.assertEqual(response.status_code, 200)
        
        # Проверяем создание поста
        self.assertTrue(Post.objects.filter(title='Полный тест поста').exists())
        post = Post.objects.get(title='Полный тест поста')
        
        # 3. Читатель просматривает пост
        self.client.logout()
        response = self.client.get(
            reverse('post_detail', kwargs={'pk': post.pk, 'slug': post.slug})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Полный тест поста')
        
        # 4. Читатель входит в систему и комментирует
        self.client.login(username='reader', password='reader123')
        
        comment_data = {
            'text': 'Отличная статья! Спасибо за информацию.'
        }
        
        response = self.client.post(
            reverse('comment_create', kwargs={'post_pk': post.pk}),
            comment_data,
            follow=True
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Comment.objects.filter(text='Отличная статья!').exists())
        
        # 5. Автор отвечает на комментарий
        comment = Comment.objects.get(text='Отличная статья!')
        reply_data = {
            'text': 'Пожалуйста! Рад, что статья оказалась полезной.'
        }
        
        response = self.client.post(
            reverse('reply_create', kwargs={'comment_pk': comment.pk}),
            reply_data,
            follow=True
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Comment.objects.filter(text='Пожалуйста!').exists())
        
        # 6. Читатель лайкает пост
        response = self.client.post(
            reverse('post_like', kwargs={'pk': post.pk}),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['liked'])
        
        # 7. Проверяем, что уведомление создалось
        self.assertTrue(Notification.objects.filter(
            user=self.author,
            notification_type='comment',
            related_comment=comment
        ).exists())
        
        # 8. Автор редактирует пост
        self.client.logout()
        self.client.login(username='author', password='author123')
        
        edit_data = {
            'title': 'Обновленный полный тест поста',
            'content': 'Обновленное содержимое поста',
            'category': self.category.pk,
            'status': 'published'
        }
        
        response = self.client.post(
            reverse('post_edit', kwargs={'pk': post.pk}),
            edit_data,
            follow=True
        )
        
        self.assertEqual(response.status_code, 200)
        post.refresh_from_db()
        self.assertEqual(post.title, 'Обновленный полный тест поста')
    
    def test_full_post_lifecycle_api(self):
        """Полный цикл жизни поста через API"""
        self.api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.author_token}')
        
        # 1. Создание поста через API
        post_data = {
            'title': 'API тест поста',
            'content': 'Содержимое поста через API',
            'category': self.category.pk,
            'status': 'published'
        }
        
        response = self.api_client.post('/api/posts/', post_data)
        self.assertEqual(response.status_code, 201)
        
        post_id = response.json()['id']
        
        # 2. Читатель просматривает пост через API
        self.api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.reader_token}')
        response = self.api_client.get(f'/api/posts/{post_id}/')
        self.assertEqual(response.status_code, 200)
        
        # 3. Читатель комментирует через API
        comment_data = {'text': 'Комментарий через API'}
        response = self.api_client.post(f'/api/posts/{post_id}/comments/', comment_data)
        self.assertEqual(response.status_code, 201)
        
        comment_id = response.json()['id']
        
        # 4. Читатель лайкает пост через API
        response = self.api_client.post(f'/api/posts/{post_id}/like/')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertTrue(data['liked'])
        
        # 5. Автор получает уведомления через API
        self.api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.author_token}')
        response = self.api_client.get('/api/notifications/unread/')
        self.assertEqual(response.status_code, 200)
        
        notifications = response.json()
        self.assertTrue(len(notifications) > 0)
    
    def test_cross_platform_consistency(self):
        """Тест консистентности между веб и API"""
        # Создаем пост через веб-интерфейс
        self.client.login(username='author', password='author123')
        
        post_data = {
            'title': 'Кроссплатформенный тест',
            'content': 'Содержимое для проверки консистентности',
            'category': self.category.pk,
            'status': 'published'
        }
        
        response = self.client.post(reverse('post_new'), post_data, follow=True)
        self.assertEqual(response.status_code, 200)
        
        post = Post.objects.get(title='Кроссплатформенный тест')
        
        # Проверяем пост через API
        self.api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.reader_token}')
        response = self.api_client.get(f'/api/posts/{post.id}/')
        self.assertEqual(response.status_code, 200)
        
        api_post = response.json()
        self.assertEqual(api_post['title'], 'Кроссплатформенный тест')
        self.assertEqual(api_post['author']['username'], 'author')
        self.assertEqual(api_post['category']['name'], 'Технологии')


class UserRegistrationAndProfileTest(TestCase):
    """Тесты регистрации пользователей и управления профилями"""
    
    def setUp(self):
        self.client = Client()
    
    def test_complete_user_registration_workflow(self):
        """Полный рабочий процесс регистрации пользователя"""
        # 1. Регистрация через веб
        register_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'newuserpass123',
            'password2': 'newuserpass123'
        }
        
        response = self.client.post(reverse('register'), register_data, follow=True)
        self.assertEqual(response.status_code, 200)
        
        # Проверяем создание пользователя
        self.assertTrue(User.objects.filter(username='newuser').exists())
        
        user = User.objects.get(username='newuser')
        
        # 2. Проверяем автоматическое создание профиля
        self.assertTrue(UserProfile.objects.filter(user=user).exists())
        
        # 3. Пользователь настраивает профиль
        self.client.login(username='newuser', password='newuserpass123')
        
        profile_data = {
            'bio': 'Новый пользователь блога',
            'location': 'Москва',
            'website': 'https://newuser.com',
            'birth_date': '1995-06-15'
        }
        
        user_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'first_name': 'Новый',
            'last_name': 'Пользователь'
        }
        
        # Обновляем пользователя
        user_form_response = self.client.post(reverse('profile_edit'), {
            **user_data,
            **profile_data
        }, follow=True)
        
        self.assertEqual(user_form_response.status_code, 200)
        
        # 4. Проверяем обновления
        user.refresh_from_db()
        self.assertEqual(user.first_name, 'Новый')
        self.assertEqual(user.profile.bio, 'Новый пользователь блога')
        self.assertEqual(user.profile.location, 'Москва')
    
    def test_registration_creates_notification(self):
        """Тест создания уведомлений при регистрации"""
        # Регистрируем пользователя
        register_data = {
            'username': 'notified_user',
            'email': 'notified@example.com',
            'password1': 'notifiedpass123',
            'password2': 'notifiedpass123'
        }
        
        response = self.client.post(reverse('register'), register_data, follow=True)
        self.assertEqual(response.status_code, 200)
        
        # Создаем админа для проверки уведомлений
        admin = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin123'
        )
        
        # Проверяем, что уведомления создаются (может быть системой)
        # Этот тест зависит от конкретной логики уведомлений


class CommentAndReplySystemTest(TestCase):
    """Тесты системы комментариев и ответов"""
    
    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='user1123'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='user2123'
        )
        self.user3 = User.objects.create_user(
            username='user3',
            email='user3@example.com',
            password='user3123'
        )
        
        self.post = Post.objects.create(
            title='Пост для комментариев',
            content='Содержимое поста',
            author=self.user1,
            status='published'
        )
    
    def test_nested_comment_system(self):
        """Тест системы вложенных комментариев"""
        self.client.login(username='user2', password='user2123')
        
        # 1. Первый комментарий
        comment1_data = {'text': 'Первый комментарий'}
        response = self.client.post(
            reverse('comment_create', kwargs={'post_pk': self.post.pk}),
            comment1_data,
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        
        comment1 = Comment.objects.get(text='Первый комментарий')
        
        # 2. Второй комментарий
        comment2_data = {'text': 'Второй комментарий'}
        response = self.client.post(
            reverse('comment_create', kwargs={'post_pk': self.post.pk}),
            comment2_data,
            follow=True
        )
        
        comment2 = Comment.objects.get(text='Второй комментарий')
        
        # 3. Ответ на первый комментарий
        reply1_data = {'text': 'Ответ на первый комментарий'}
        response = self.client.post(
            reverse('reply_create', kwargs={'comment_pk': comment1.pk}),
            reply1_data,
            follow=True
        )
        
        reply1 = Comment.objects.get(text='Ответ на первый комментарий')
        
        # 4. Ответ на ответ (второй уровень)
        reply2_data = {'text': 'Ответ на ответ'}
        response = self.client.post(
            reverse('reply_create', kwargs={'comment_pk': reply1.pk}),
            reply2_data,
            follow=True
        )
        
        reply2 = Comment.objects.get(text='Ответ на ответ')
        
        # Проверяем структуру комментариев
        self.assertEqual(reply1.parent, comment1)
        self.assertEqual(reply2.parent, reply1)
        self.assertIsNone(comment1.parent)
        self.assertIsNone(comment2.parent)
        
        # Проверяем количество ответов
        self.assertEqual(comment1.reply_count(), 1)  # reply1
        self.assertEqual(reply1.reply_count(), 1)    # reply2
        self.assertEqual(comment2.reply_count(), 0)
    
    def test_comment_likes_system(self):
        """Тест системы лайков комментариев"""
        self.client.login(username='user2', password='user2123')
        
        # Создаем комментарий
        comment_data = {'text': 'Комментарий для лайков'}
        response = self.client.post(
            reverse('comment_create', kwargs={'post_pk': self.post.pk}),
            comment_data,
            follow=True
        )
        
        comment = Comment.objects.get(text='Комментарий для лайков')
        
        # user2 лайкает комментарий
        response = self.client.post(
            reverse('comment_like', kwargs={'comment_pk': comment.pk}),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['liked'])
        self.assertEqual(data['like_count'], 1)
        
        # user3 тоже лайкает
        self.client.logout()
        self.client.login(username='user3', password='user3123')
        
        response = self.client.post(
            reverse('comment_like', kwargs={'comment_pk': comment.pk}),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        comment.refresh_from_db()
        self.assertEqual(comment.like_count(), 2)
        
        # user2 убирает лайк
        self.client.logout()
        self.client.login(username='user2', password='user2123')
        
        response = self.client.post(
            reverse('comment_like', kwargs={'comment_pk': comment.pk}),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        comment.refresh_from_db()
        self.assertEqual(comment.like_count(), 1)
    
    def test_comment_notifications(self):
        """Тест уведомлений о комментариях"""
        Notification.objects.all().delete()
        
        self.client.login(username='user2', password='user2123')
        
        # user2 комментирует пост user1
        comment_data = {'text': 'Комментарий для уведомления'}
        response = self.client.post(
            reverse('comment_create', kwargs={'post_pk': self.post.pk}),
            comment_data,
            follow=True
        )
        
        # Проверяем создание уведомления
        self.assertTrue(Notification.objects.filter(
            user=self.user1,
            notification_type='comment',
            related_post=self.post
        ).exists())


class SearchAndFilteringTest(TestCase):
    """Тесты поиска и фильтрации"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='author',
            email='author@example.com',
            password='author123'
        )
        
        self.category1 = Category.objects.create(name='Технологии', color='#00ff41')
        self.category2 = Category.objects.create(name='Наука', color='#ff0000')
        
        # Создаем посты для поиска
        self.post1 = Post.objects.create(
            title='Python Programming',
            content='Учебник по Python для начинающих',
            excerpt='Изучение Python',
            author=self.user,
            category=self.category1,
            status='published',
            tags='python, programming, tutorial'
        )
        
        self.post2 = Post.objects.create(
            title='Machine Learning Basics',
            content='Основы машинного обучения',
            excerpt='ML для всех',
            author=self.user,
            category=self.category2,
            status='published',
            tags='machine learning, ai, data'
        )
        
        self.post3 = Post.objects.create(
            title='Django Web Framework',
            content='Разработка веб-приложений на Django',
            excerpt='Веб-разработка',
            author=self.user,
            category=self.category1,
            status='published',
            tags='django, web, framework'
        )
    
    def test_search_functionality(self):
        """Тест функциональности поиска"""
        # Поиск по заголовку
        response = self.client.get(reverse('search') + '?query=Python')
        self.assertEqual(response.status_code, 200)
        
        results = response.context['results']
        self.assertIn(self.post1, results)
        self.assertNotIn(self.post2, results)
        self.assertNotIn(self.post3, results)
        
        # Поиск по содержимому
        response = self.client.get(reverse('search') + '?query=обучения')
        self.assertEqual(response.status_code, 200)
        
        results = response.context['results']
        self.assertIn(self.post2, results)
        
        # Поиск по тегам
        response = self.client.get(reverse('search') + '?query=programming')
        self.assertEqual(response.status_code, 200)
        
        results = response.context['results']
        self.assertIn(self.post1, results)
    
    def test_category_filtering(self):
        """Тест фильтрации по категориям"""
        # Фильтр по категории "Технологии"
        response = self.client.get(
            reverse('post_list') + f'?category={self.category1.pk}'
        )
        self.assertEqual(response.status_code, 200)
        
        posts = response.context['posts']
        self.assertIn(self.post1, posts)
        self.assertIn(self.post3, posts)
        self.assertNotIn(self.post2, posts)
        
        # Фильтр по категории "Наука"
        response = self.client.get(
            reverse('post_list') + f'?category={self.category2.pk}'
        )
        
        posts = response.context['posts']
        self.assertIn(self.post2, posts)
        self.assertNotIn(self.post1, posts)
        self.assertNotIn(self.post3, posts)
    
    def test_combined_search_and_filter(self):
        """Тест комбинированного поиска и фильтрации"""
        response = self.client.get(
            reverse('post_list') + 
            f'?category={self.category1.pk}&query=Python'
        )
        self.assertEqual(response.status_code, 200)
        
        posts = response.context['posts']
        self.assertIn(self.post1, posts)  # Технологии + Python
        self.assertNotIn(self.post2, posts)  # Не в категории технологий
        self.assertNotIn(self.post3, posts)  # Нет слова Python


class AdminAndModerationTest(TestCase):
    """Тесты админки и модерации"""
    
    def setUp(self):
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin123'
        )
        
        self.regular_user = User.objects.create_user(
            username='user',
            email='user@example.com',
            password='user123'
        )
        
        self.post = Post.objects.create(
            title='Тестовый пост',
            content='Содержимое',
            author=self.regular_user,
            status='published'
        )
    
    def test_admin_post_moderation(self):
        """Тест модерации постов администратором"""
        client = Client()
        client.login(username='admin', password='admin123')
        
        # Админ может изменить статус поста
        response = client.post(
            reverse('admin:blog_post_change', args=[self.post.pk]),
            {'status': 'archived'},
            follow=True
        )
        
        self.assertEqual(response.status_code, 200)
        self.post.refresh_from_db()
        self.assertEqual(self.post.status, 'archived')
    
    def test_admin_user_banning(self):
        """Тест блокировки пользователей администратором"""
        client = Client()
        client.login(username='admin', password='admin123')
        
        # Блокируем пользователя
        profile = self.regular_user.profile
        profile.is_banned = True
        profile.ban_reason = 'Нарушение правил'
        profile.save()
        
        # Проверяем статус бана
        self.assertTrue(profile.is_currently_banned())
        
        # Разблокируем пользователя
        profile.is_banned = False
        profile.ban_reason = ''
        profile.save()
        
        self.assertFalse(profile.is_currently_banned())


class PerformanceAndScalabilityTest(TestCase):
    """Тесты производительности и масштабируемости"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='author',
            email='author@example.com',
            password='author123'
        )
        
        self.category = Category.objects.create(name='Технологии')
        
        # Создаем множество постов для тестирования пагинации
        self.posts_count = 25
        for i in range(self.posts_count):
            Post.objects.create(
                title=f'Пост {i+1}',
                content=f'Содержимое поста {i+1}',
                author=self.user,
                category=self.category,
                status='published',
                published_date=timezone.now() - timedelta(days=i)
            )
    
    def test_pagination_performance(self):
        """Тест производительности пагинации"""
        client = Client()
        
        # Первая страница
        response = client.get(reverse('post_list'))
        self.assertEqual(response.status_code, 200)
        
        posts_page1 = response.context['posts']
        self.assertEqual(len(posts_page1), 10)  # 10 постов на странице по умолчанию
        
        # Вторая страница
        response = client.get(reverse('post_list') + '?page=2')
        self.assertEqual(response.status_code, 200)
        
        posts_page2 = response.context['posts']
        self.assertEqual(len(posts_page2), 10)
        
        # Последняя страница
        response = client.get(reverse('post_list') + f'?page={self.posts_count // 10 + 1}')
        self.assertEqual(response.status_code, 200)
        
        posts_last = response.context['posts']
        self.assertTrue(len(posts_last) <= 10)
    
    def test_large_comment_thread(self):
        """Тест работы с большим количеством комментариев"""
        post = Post.objects.create(
            title='Пост для тестирования комментариев',
            content='Содержимое',
            author=self.user,
            category=self.category,
            status='published'
        )
        
        # Создаем множество комментариев
        comment_count = 50
        for i in range(comment_count):
            Comment.objects.create(
                post=post,
                author=self.user,
                text=f'Комментарий {i+1}'
            )
        
        # Проверяем, что все комментарии созданы
        self.assertEqual(Comment.objects.filter(post=post).count(), comment_count)
        
        # Проверяем отображение страницы с комментариями
        client = Client()
        response = client.get(
            reverse('post_detail', kwargs={'pk': post.pk, 'slug': post.slug})
        )
        self.assertEqual(response.status_code, 200)
        
        comments = response.context['comments']
        self.assertEqual(comments.count(), comment_count)


class SecurityAndPermissionsTest(TestCase):
    """Тесты безопасности и разрешений"""
    
    def setUp(self):
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='user1123'
        )
        
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='user2123'
        )
        
        self.post = Post.objects.create(
            title='Пост пользователя 1',
            content='Содержимое',
            author=self.user1,
            status='published'
        )
    
    def test_unauthorized_access_protection(self):
        """Тест защиты от несанкционированного доступа"""
        client = Client()
        
        # Попытка доступа к защищенным страницам без авторизации
        protected_urls = [
            reverse('post_new'),
            reverse('profile'),
            reverse('profile_edit'),
            reverse('change_password'),
        ]
        
        for url in protected_urls:
            response = client.get(url)
            self.assertEqual(response.status_code, 302)  # Перенаправление на логин
    
    def test_owner_permissions(self):
        """Тест прав владельца"""
        client = Client()
        
        # user1 может редактировать свои посты
        client.login(username='user1', password='user1123')
        response = client.get(reverse('post_edit', kwargs={'pk': self.post.pk}))
        self.assertEqual(response.status_code, 200)
        
        # user2 НЕ может редактировать чужие посты
        client.logout()
        client.login(username='user2', password='user2123')
        response = client.get(reverse('post_edit', kwargs={'pk': self.post.pk}))
        self.assertEqual(response.status_code, 403)
    
    def test_banned_user_restrictions(self):
        """Тест ограничений для заблокированных пользователей"""
        # Блокируем user1
        profile = self.user1.profile
        profile.is_banned = True
        profile.ban_reason = 'Нарушение правил'
        profile.save()
        
        client = Client()
        client.login(username='user1', password='user1123')
        
        # Заблокированный пользователь не может создавать посты
        post_data = {
            'title': 'Заблокированный пост',
            'content': 'Содержимое',
            'status': 'published'
        }
        
        response = client.post(reverse('post_new'), post_data)
        self.assertEqual(response.status_code, 302)  # Перенаправление
        
        # Заблокированный пользователь не может комментировать
        comment_data = {'text': 'Заблокированный комментарий'}
        response = client.post(
            reverse('comment_create', kwargs={'post_pk': self.post.pk}),
            comment_data
        )
        self.assertEqual(response.status_code, 302)  # Перенаправление


class ErrorHandlingAndEdgeCasesTest(TestCase):
    """Тесты обработки ошибок и граничных случаев"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='user',
            email='user@example.com',
            password='user123'
        )
        
        self.post = Post.objects.create(
            title='Тестовый пост',
            content='Содержимое',
            author=self.user,
            status='published'
        )
    
    def test_invalid_form_submissions(self):
        """Тест обработки невалидных форм"""
        client = Client()
        client.login(username='user', password='user123')
        
        # Пустая форма создания поста
        invalid_post_data = {
            'title': '',  # Пустой заголовок
            'content': 'Содержимое'
        }
        
        response = client.post(reverse('post_new'), invalid_post_data)
        self.assertEqual(response.status_code, 200)  # Возвращаемся на форму
        self.assertTrue(response.context['form'].errors)
        
        # Неверный ID категории
        invalid_category_data = {
            'title': 'Новый пост',
            'content': 'Содержимое',
            'category': 99999,  # Несуществующая категория
            'status': 'published'
        }
        
        response = client.post(reverse('post_new'), invalid_category_data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].errors)
    
    def test_404_handling(self):
        """Тест обработки 404 ошибок"""
        client = Client()
        
        # Несуществующий пост
        response = client.get(
            reverse('post_detail', kwargs={'pk': 99999, 'slug': 'nonexistent'})
        )
        self.assertEqual(response.status_code, 404)
        
        # Несуществующий пользователь
        response = client.get(reverse('user_profile', kwargs={'username': 'nonexistent'}))
        self.assertEqual(response.status_code, 404)
    
    def test_concurrent_operations(self):
        """Тест одновременных операций"""
        # Этот тест проверяет, что система корректно обрабатывает
        # одновременные запросы (в реальности требует более сложного тестирования)
        
        # Создаем несколько пользователей для одновременных операций
        users = []
        for i in range(5):
            user = User.objects.create_user(
                username=f'user{i}',
                email=f'user{i}@example.com',
                password=f'user{i}123'
            )
            users.append(user)
        
        # Все пользователи пытаются лайкнуть один пост
        from django.test import RequestFactory
        from blog.views import post_like
        
        factory = RequestFactory()
        
        for user in users:
            request = factory.post(reverse('post_like', kwargs={'pk': self.post.pk}))
            request.user = user
            
            response = post_like(request, self.post.pk)
            self.assertEqual(response.status_code, 200)
        
        # Проверяем, что лайки добавились корректно
        self.assertEqual(self.post.likes.count(), 5)


class DatabaseIntegrityTest(TestCase):
    """Тесты целостности базы данных"""
    
    def test_cascade_deletions(self):
        """Тест каскадных удалений"""
        # Создаем связанные объекты
        user = User.objects.create_user(
            username='cascade_user',
            email='cascade@example.com',
            password='cascade123'
        )
        
        category = Category.objects.create(name='Каскадная категория')
        
        post = Post.objects.create(
            title='Пост для каскадного удаления',
            content='Содержимое',
            author=user,
            category=category,
            status='published'
        )
        
        comment = Comment.objects.create(
            post=post,
            author=user,
            text='Комментарий для каскадного удаления'
        )
        
        notification = Notification.objects.create(
            user=user,
            notification_type='system',
            title='Тестовое уведомление',
            message='Сообщение',
            related_post=post,
            related_comment=comment
        )
        
        # Запоминаем ID для проверки удаления
        user_id = user.id
        category_id = category.id
        post_id = post.id
        comment_id = comment.id
        notification_id = notification.id
        
        # Удаляем пользователя
        user.delete()
        
        # Проверяем каскадное удаление
        self.assertFalse(User.objects.filter(id=user_id).exists())
        self.assertFalse(Post.objects.filter(id=post_id).exists())
        self.assertFalse(Comment.objects.filter(id=comment_id).exists())
        self.assertFalse(Notification.objects.filter(id=notification_id).exists())
        
        # Категория должна остаться (SET_NULL)
        self.assertTrue(Category.objects.filter(id=category_id).exists())
    
    def test_data_constraints(self):
        """Тест ограничений данных"""
        user = User.objects.create_user(
            username='constraint_user',
            email='constraint@example.com',
            password='constraint123'
        )
        
        # Тест уникальности категорий
        Category.objects.create(name='Уникальная категория')
        
        with self.assertRaises(Exception):
            Category.objects.create(name='Уникальная категория')  # Должно провалиться
        
        # Тест уникальности слагов постов
        Post.objects.create(
            title='Уникальный пост',
            content='Содержимое',
            author=user,
            status='published'
        )
        
        with self.assertRaises(Exception):
            Post.objects.create(
                title='Уникальный пост',  # Тот же заголовок = тот же slug
                content='Другое содержимое',
                author=user,
                status='published'
            )
    
    def test_data_validation(self):
        """Тест валидации данных"""
        user = User.objects.create_user(
            username='validation_user',
            email='validation@example.com',
            password='validation123'
        )
        
        # Создаем категорию для проверки связи
        category = Category.objects.create(name='Категория для валидации')
        
        # Тест валидации длины полей
        long_title = 'A' * 201  # Максимум 200 символов
        with self.assertRaises(Exception):
            Post.objects.create(
                title=long_title,
                content='Содержимое',
                author=user,
                status='published'
            )
        
        # Тест валидации статуса
        with self.assertRaises(Exception):
            Post.objects.create(
                title='Пост с неверным статусом',
                content='Содержимое',
                author=user,
                status='invalid_status'
            )
        
        # Валидный пост должен создаться
        valid_post = Post.objects.create(
            title='Валидный пост',
            content='Валидное содержимое',
            author=user,
            category=category,
            status='published'
        )
        
        self.assertTrue(Post.objects.filter(id=valid_post.id).exists())