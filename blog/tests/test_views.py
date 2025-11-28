"""
Тесты для представлений блога
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import authenticate
from django.core.paginator import Paginator
from django.http import HttpResponseForbidden
from datetime import datetime, timedelta

from blog.models import Post, Comment, Category, UserProfile, Notification
from blog.forms import RegisterForm, LoginForm, PostForm, CommentForm


class PublicViewsTest(TestCase):
    """Тесты публичных представлений"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.category = Category.objects.create(
            name='Технологии',
            description='Статьи о технологиях'
        )
        
        # Создаем несколько постов для тестирования
        self.post1 = Post.objects.create(
            title='Первый пост',
            content='Содержимое первого поста',
            author=self.user,
            category=self.category,
            status='published'
        )
        
        self.post2 = Post.objects.create(
            title='Второй пост',
            content='Содержимое второго поста',
            author=self.user,
            category=self.category,
            status='published',
            views=5
        )
        
        self.post3 = Post.objects.create(
            title='Черновик',
            content='Неопубликованный пост',
            author=self.user,
            category=self.category,
            status='draft'
        )
    
    def test_index_view(self):
        """Тест главной страницы"""
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'blog/index.html')
        
        # Проверяем, что контент содержит нужные элементы
        self.assertContains(response, 'Первый пост')
        self.assertContains(response, 'Второй пост')
        
        # Черновик не должен отображаться
        self.assertNotContains(response, 'Черновик')
        
        # Проверяем контекст
        self.assertIn('featured_posts', response.context)
        self.assertIn('latest_posts', response.context)
        self.assertIn('categories', response.context)
    
    def test_post_list_view(self):
        """Тест страницы списка постов"""
        response = self.client.get(reverse('post_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'blog/post_list.html')
        
        # Проверяем, что отображаются только опубликованные посты
        self.assertContains(response, 'Первый пост')
        self.assertContains(response, 'Второй пост')
        self.assertNotContains(response, 'Черновик')
        
        # Проверяем пагинацию и контекст
        self.assertIn('posts', response.context)
        self.assertIn('categories', response.context)
        self.assertIn('search_form', response.context)
    
    def test_post_detail_view(self):
        """Тест детальной страницы поста"""
        response = self.client.get(
            reverse('post_detail', kwargs={'pk': self.post1.pk, 'slug': self.post1.slug})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'blog/post_detail.html')
        
        # Проверяем содержимое поста
        self.assertContains(response, self.post1.title)
        self.assertContains(response, self.post1.content)
        
        # Проверяем, что счетчик просмотров увеличился
        self.post1.refresh_from_db()
        self.assertEqual(self.post1.views, 1)
        
        # Проверяем контекст
        self.assertIn('post', response.context)
        self.assertIn('comments', response.context)
        self.assertIn('comment_form', response.context)
        self.assertIn('reply_form', response.context)
    
    def test_post_detail_view_increment_views(self):
        """Тест увеличения счетчика просмотров"""
        initial_views = self.post1.views
        self.client.get(
            reverse('post_detail', kwargs={'pk': self.post1.pk, 'slug': self.post1.slug})
        )
        self.post1.refresh_from_db()
        self.assertEqual(self.post1.views, initial_views + 1)
    
    def test_post_detail_view_invalid_slug(self):
        """Тест страницы поста с неправильным слагом"""
        response = self.client.get(
            reverse('post_detail', kwargs={'pk': self.post1.pk, 'slug': 'invalid-slug'})
        )
        # Должен отработать как 404 (Django перенаправляет на 404 для несуществующих постов)
        self.assertEqual(response.status_code, 404)
    
    def test_search_view(self):
        """Тест поиска"""
        # Тест пустого поиска
        response = self.client.get(reverse('search'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'blog/search.html')
        
        # Тест поиска по содержимому
        response = self.client.get(reverse('search') + '?query=первого')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Первый пост')
        
        # Тест поиска по автору
        response = self.client.get(reverse('search') + '?query=testuser')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Первый пост')
        self.assertContains(response, 'Второй пост')
    
    def test_user_list_view(self):
        """Тест страницы списка пользователей"""
        response = self.client.get(reverse('user_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'blog/user_list.html')
        
        # Проверяем, что пользователь отображается
        self.assertContains(response, self.user.username)
        
        # Проверяем контекст
        self.assertIn('users', response.context)
    
    def test_user_profile_view(self):
        """Тест публичного профиля пользователя"""
        response = self.client.get(
            reverse('user_profile', kwargs={'username': self.user.username})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'blog/user_public_profile.html')
        
        # Проверяем содержимое
        self.assertContains(response, self.user.username)
        
        # Проверяем контекст
        self.assertIn('profile_user', response.context)
        self.assertIn('posts', response.context)
        self.assertIn('comments', response.context)
    
    def test_contact_view(self):
        """Тест страницы контактов"""
        response = self.client.get(reverse('contact'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'blog/contact.html')
        
        # Проверяем контекст
        self.assertIn('form', response.context)
        self.assertIsInstance(response.context['form'], ContactForm)


class AuthenticationViewsTest(TestCase):
    """Тесты представлений аутентификации"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_register_view_get(self):
        """Тест GET запроса на регистрацию"""
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'blog/register.html')
        
        self.assertIn('form', response.context)
        self.assertIsInstance(response.context['form'], RegisterForm)
    
    def test_register_view_post_valid_data(self):
        """Тест POST запроса на регистрацию с валидными данными"""
        data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password1': 'newpassword123',
            'password2': 'newpassword123'
        }
        
        response = self.client.post(reverse('register'), data)
        
        # После успешной регистрации должно произойти перенаправление
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='newuser').exists())
        
        # Проверяем, что пользователь автоматически аутентифицирован
        self.assertTrue('_auth_user_id' in self.client.session)
    
    def test_register_view_post_invalid_data(self):
        """Тест POST запроса на регистрацию с невалидными данными"""
        data = {
            'username': 'testuser',  # Уже существующий пользователь
            'email': 'test@example.com',  # Уже существующий email
            'password1': 'pass',
            'password2': 'differentpass'
        }
        
        response = self.client.post(reverse('register'), data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'blog/register.html')
        
        # Форма должна содержать ошибки
        self.assertTrue(response.context['form'].errors)
    
    def test_login_view_get(self):
        """Тест GET запроса на вход"""
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'blog/login.html')
        
        self.assertIn('form', response.context)
        self.assertIsInstance(response.context['form'], LoginForm)
    
    def test_login_view_post_valid_credentials(self):
        """Тест входа с валидными учетными данными"""
        data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        
        response = self.client.post(reverse('login'), data, follow=True)
        self.assertEqual(response.status_code, 200)
        
        # Пользователь должен быть аутентифицирован
        self.assertTrue('_auth_user_id' in self.client.session)
    
    def test_login_view_post_invalid_credentials(self):
        """Тест входа с невалидными учетными данными"""
        data = {
            'username': 'testuser',
            'password': 'wrongpassword'
        }
        
        response = self.client.post(reverse('login'), data)
        self.assertEqual(response.status_code, 200)
        
        # Пользователь НЕ должен быть аутентифицирован
        self.assertFalse('_auth_user_id' in self.client.session)
        
        # Должна быть показана ошибка
        messages = list(response.context['messages'])
        self.assertTrue(len(messages) > 0)
    
    def test_login_view_remember_me(self):
        """Тест функции 'запомнить меня'"""
        data = {
            'username': 'testuser',
            'password': 'testpass123',
            'remember_me': True
        }
        
        response = self.client.post(reverse('login'), data, follow=True)
        
        # После входа с 'запомнить меня' сессия должна быть постоянной
        self.assertTrue(response.client.session.get_expire_at_browser_close())
    
    def test_logout_view(self):
        """Тест выхода из системы"""
        # Сначала входим в систему
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.post(reverse('logout'), follow=True)
        self.assertEqual(response.status_code, 200)
        
        # Пользователь должен быть разлогинен
        self.assertFalse('_auth_user_id' in self.client.session)


class AuthenticatedViewsTest(TestCase):
    """Тесты представлений, требующих аутентификации"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
        
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
    
    def test_post_new_view_get(self):
        """Тест GET запроса на создание нового поста"""
        response = self.client.get(reverse('post_new'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'blog/post_edit.html')
        
        self.assertIn('form', response.context)
        self.assertIsInstance(response.context['form'], PostForm)
        self.assertEqual(response.context['title'], 'Create New Post')
    
    def test_post_new_view_post_valid_data(self):
        """Тест создания нового поста с валидными данными"""
        data = {
            'title': 'Новый пост',
            'content': 'Содержимое нового поста',
            'category': self.category.pk,
            'status': 'published'
        }
        
        response = self.client.post(reverse('post_new'), data, follow=True)
        
        # Проверяем создание поста
        self.assertTrue(Post.objects.filter(title='Новый пост').exists())
        
        # Должно произойти перенаправление на страницу поста
        post = Post.objects.get(title='Новый пост')
        self.assertRedirects(response, f'/posts/{post.pk}/{post.slug}/')
    
    def test_post_edit_view_get(self):
        """Тест GET запроса на редактирование поста"""
        response = self.client.get(reverse('post_edit', kwargs={'pk': self.post.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'blog/post_edit.html')
        
        self.assertIn('form', response.context)
        self.assertEqual(response.context['title'], 'Edit Post')
        self.assertEqual(response.context['post'], self.post)
    
    def test_post_edit_view_post(self):
        """Тест редактирования поста"""
        data = {
            'title': 'Измененный пост',
            'content': 'Измененное содержимое',
            'category': self.category.pk,
            'status': 'published'
        }
        
        response = self.client.post(
            reverse('post_edit', kwargs={'pk': self.post.pk}), 
            data, 
            follow=True
        )
        
        # Проверяем изменения
        self.post.refresh_from_db()
        self.assertEqual(self.post.title, 'Измененный пост')
        self.assertEqual(self.post.content, 'Измененное содержимое')
    
    def test_post_edit_view_forbidden_for_other_user(self):
        """Тест запрета редактирования чужого поста"""
        # Создаем другого пользователя и его пост
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='otherpass123'
        )
        
        other_post = Post.objects.create(
            title='Чужой пост',
            content='Содержимое',
            author=other_user,
            category=self.category,
            status='published'
        )
        
        response = self.client.get(reverse('post_edit', kwargs={'pk': other_post.pk}))
        self.assertEqual(response.status_code, 403)
    
    def test_profile_view(self):
        """Тест страницы профиля"""
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'blog/profile.html')
        
        # Проверяем контекст
        self.assertIn('user_posts', response.context)
        self.assertIn('user_comments', response.context)
        self.assertIn('notifications', response.context)
    
    def test_profile_edit_view_get(self):
        """Тест GET запроса на редактирование профиля"""
        response = self.client.get(reverse('profile_edit'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'blog/profile_edit.html')
        
        self.assertIn('user_form', response.context)
        self.assertIn('profile_form', response.context)
    
    def test_profile_edit_view_post(self):
        """Тест редактирования профиля"""
        data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'first_name': 'Тест',
            'last_name': 'Пользователь',
            'bio': 'Новая биография',
            'location': 'Москва'
        }
        
        response = self.client.post(reverse('profile_edit'), data, follow=True)
        
        # Проверяем обновление профиля
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Тест')
        self.assertEqual(self.user.profile.bio, 'Новая биография')
    
    def test_change_password_view_get(self):
        """Тест GET запроса на смену пароля"""
        response = self.client.get(reverse('change_password'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'blog/change_password.html')
    
    def test_comment_create_view(self):
        """Тест создания комментария"""
        data = {
            'text': 'Отличный пост!'
        }
        
        response = self.client.post(
            reverse('comment_create', kwargs={'post_pk': self.post.pk}),
            data,
            follow=True
        )
        
        # Проверяем создание комментария
        self.assertTrue(Comment.objects.filter(text='Отличный пост!').exists())
        
        # Комментарий должен быть привязан к посту и автору
        comment = Comment.objects.get(text='Отличный пост!')
        self.assertEqual(comment.post, self.post)
        self.assertEqual(comment.author, self.user)
    
    def test_reply_create_view(self):
        """Тест создания ответа на комментарий"""
        # Создаем комментарий
        comment = Comment.objects.create(
            post=self.post,
            author=self.user,
            text='Основной комментарий'
        )
        
        data = {
            'text': 'Ответ на комментарий'
        }
        
        response = self.client.post(
            reverse('reply_create', kwargs={'comment_pk': comment.pk}),
            data,
            follow=True
        )
        
        # Проверяем создание ответа
        self.assertTrue(Comment.objects.filter(text='Ответ на комментарий').exists())
        
        reply = Comment.objects.get(text='Ответ на комментарий')
        self.assertEqual(reply.parent, comment)


class BannedUserViewsTest(TestCase):
    """Тесты представлений для заблокированных пользователей"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='banneduser',
            email='banned@example.com',
            password='bannedpass123'
        )
        
        # Заблокируем пользователя
        profile = self.user.profile
        profile.is_banned = True
        profile.ban_reason = 'Нарушение правил'
        profile.save()
        
        self.client.login(username='banneduser', password='bannedpass123')
        
        self.category = Category.objects.create(
            name='Технологии',
            description='Статьи о технологиях'
        )
    
    def test_banned_user_cannot_create_posts(self):
        """Тест запрета создания постов заблокированному пользователю"""
        response = self.client.get(reverse('post_new'))
        
        # Должно быть перенаправление с сообщением об ошибке
        self.assertEqual(response.status_code, 302)
        
        # После перенаправления должно быть сообщение
        follow_response = self.client.get(response.url)
        messages = list(follow_response.context['messages'])
        self.assertTrue(any('banned' in str(message) for message in messages))
    
    def test_banned_user_cannot_comment(self):
        """Тест запрета комментирования заблокированному пользователю"""
        post = Post.objects.create(
            title='Тестовый пост',
            content='Содержимое',
            author=self.user,
            category=self.category,
            status='published'
        )
        
        data = {
            'text': 'Комментарий заблокированного пользователя'
        }
        
        response = self.client.post(
            reverse('comment_create', kwargs={'post_pk': post.pk}),
            data
        )
        
        # Должно быть перенаправление (пользователь заблокирован)
        self.assertEqual(response.status_code, 302)
        
        # Комментарий не должен быть создан
        self.assertFalse(Comment.objects.filter(text='Комментарий заблокированного пользователя').exists())


class AJAXViewsTest(TestCase):
    """Тесты AJAX представлений"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
        
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
    
    def test_post_like_view(self):
        """Тест лайка/дизлайка поста"""
        # Проверяем начальное состояние
        self.assertFalse(self.post.likes.filter(id=self.user.id).exists())
        
        # Лайкаем пост
        response = self.client.post(
            reverse('post_like', kwargs={'pk': self.post.pk}),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertTrue(data['liked'])
        self.assertEqual(data['like_count'], 1)
        
        # Проверяем, что лайк добавился
        self.assertTrue(self.post.likes.filter(id=self.user.id).exists())
        
        # Дизлайкаем пост
        response = self.client.post(
            reverse('post_like', kwargs={'pk': self.post.pk}),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        data = response.json()
        self.assertFalse(data['liked'])
        self.assertEqual(data['like_count'], 0)
    
    def test_comment_like_view(self):
        """Тест лайка/дизлайка комментария"""
        # Проверяем начальное состояние
        self.assertFalse(self.comment.likes.filter(id=self.user.id).exists())
        
        # Лайкаем комментарий
        response = self.client.post(
            reverse('comment_like', kwargs={'comment_pk': self.comment.pk}),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertTrue(data['liked'])
        self.assertEqual(data['like_count'], 1)
        
        # Проверяем, что лайк добавился
        self.assertTrue(self.comment.likes.filter(id=self.user.id).exists())
    
    def test_banned_user_cannot_like_posts(self):
        """Тест запрета лайков для заблокированного пользователя"""
        # Заблокируем пользователя
        profile = self.user.profile
        profile.is_banned = True
        profile.ban_reason = 'Нарушение правил'
        profile.save()
        
        response = self.client.post(
            reverse('post_like', kwargs={'pk': self.post.pk}),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 403)
        
        data = response.json()
        self.assertIn('error', data)
        self.assertIn('banned', data['error'])
    
    def test_mark_notification_read_view(self):
        """Тест пометки уведомления как прочитанного"""
        notification = Notification.objects.create(
            user=self.user,
            notification_type='system',
            title='Тестовое уведомление',
            message='Тестовое сообщение'
        )
        
        self.assertFalse(notification.is_read)
        
        response = self.client.post(
            reverse('mark_notification_read', kwargs={'notification_pk': notification.pk}),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertTrue(data['success'])
        
        # Проверяем, что уведомление помечено как прочитанное
        notification.refresh_from_db()
        self.assertTrue(notification.is_read)
    
    def test_get_unread_notifications_view(self):
        """Тест получения непрочитанных уведомлений"""
        # Создаем несколько уведомлений
        Notification.objects.create(
            user=self.user,
            notification_type='system',
            title='Уведомление 1',
            message='Сообщение 1'
        )
        
        Notification.objects.create(
            user=self.user,
            notification_type='system',
            title='Уведомление 2',
            message='Сообщение 2',
            is_read=True
        )
        
        response = self.client.get(
            reverse('get_unread_notifications'),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn('notifications', data)
        self.assertEqual(len(data['notifications']), 1)  # Только непрочитанное


class PaginationTest(TestCase):
    """Тесты пагинации"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.category = Category.objects.create(
            name='Технологии',
            description='Статьи о технологиях'
        )
        
        # Создаем много постов для тестирования пагинации
        self.posts_count = 15
        for i in range(self.posts_count):
            Post.objects.create(
                title=f'Пост {i+1}',
                content=f'Содержимое поста {i+1}',
                author=self.user,
                category=self.category,
                status='published'
            )
    
    def test_post_list_pagination(self):
        """Тест пагинации списка постов"""
        response = self.client.get(reverse('post_list'))
        self.assertEqual(response.status_code, 200)
        
        # По умолчанию должно показываться 10 постов (из настроек)
        posts = response.context['posts']
        self.assertEqual(len(posts), 10)
        self.assertTrue(posts.has_next())
        self.assertFalse(posts.has_previous())
    
    def test_post_list_second_page(self):
        """Тест второй страницы пагинации"""
        response = self.client.get(reverse('post_list') + '?page=2')
        self.assertEqual(response.status_code, 200)
        
        posts = response.context['posts']
        self.assertEqual(len(posts), 5)  # Осталось 5 постов
        self.assertFalse(posts.has_next())
        self.assertTrue(posts.has_previous())


class CategoryFilterTest(TestCase):
    """Тесты фильтрации по категориям"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.category1 = Category.objects.create(
            name='Технологии',
            description='Статьи о технологиях'
        )
        
        self.category2 = Category.objects.create(
            name='Наука',
            description='Научные статьи'
        )
        
        # Создаем посты для разных категорий
        Post.objects.create(
            title='Пост о технологиях',
            content='Содержимое о технологиях',
            author=self.user,
            category=self.category1,
            status='published'
        )
        
        Post.objects.create(
            title='Пост о науке',
            content='Содержимое о науке',
            author=self.user,
            category=self.category2,
            status='published'
        )
        
        Post.objects.create(
            title='Пост без категории',
            content='Содержимое без категории',
            author=self.user,
            status='published'
        )
    
    def test_filter_by_category(self):
        """Тест фильтрации по категории"""
        response = self.client.get(
            reverse('post_list') + f'?category={self.category1.pk}'
        )
        self.assertEqual(response.status_code, 200)
        
        posts = response.context['posts']
        self.assertEqual(len(posts), 1)
        self.assertEqual(posts[0].title, 'Пост о технологиях')
    
    def test_category_display_in_template(self):
        """Тест отображения категорий в шаблоне"""
        response = self.client.get(reverse('post_list'))
        self.assertEqual(response.status_code, 200)
        
        categories = response.context['categories']
        self.assertEqual(categories.count(), 2)
        
        # Проверяем, что категории отображаются в шаблоне
        self.assertContains(response, 'Технологии')
        self.assertContains(response, 'Наука')


class ErrorHandlingTest(TestCase):
    """Тесты обработки ошибок"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.category = Category.objects.create(
            name='Технологии',
            description='Статьи о технологиях'
        )
        
        self.post = Post.objects.create(
            title='Тестовый пост',
            content='Содержимое',
            author=self.user,
            category=self.category,
            status='published'
        )
    
    def test_404_for_nonexistent_post(self):
        """Тест 404 ошибки для несуществующего поста"""
        response = self.client.get(
            reverse('post_detail', kwargs={'pk': 99999, 'slug': 'nonexistent'})
        )
        self.assertEqual(response.status_code, 404)
    
    def test_403_for_forbidden_action(self):
        """Тест 403 ошибки для запрещенного действия"""
        self.client.logout()
        
        response = self.client.get(reverse('post_new'))
        self.assertEqual(response.status_code, 302)  # Перенаправление на логин
        
        # После перенаправления на логин
        response = self.client.get(response.url)
        self.assertEqual(response.status_code, 200)
    
    def test_400_for_invalid_form_data(self):
        """Тест 400 ошибки для невалидных данных формы"""
        self.client.login(username='testuser', password='testpass123')
        
        # Отправляем невалидные данные
        data = {
            'title': '',  # Пустой заголовок
            'content': 'Содержимое'
        }
        
        response = self.client.post(reverse('post_new'), data)
        self.assertEqual(response.status_code, 200)  # Возвращаемся на форму с ошибками
        self.assertTrue(response.context['form'].errors)


# Импортируем ContactForm для тестов контактной формы
from blog.forms import ContactForm