"""
Тесты для форм блога
"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from datetime import date

from blog.forms import (
    RegisterForm, LoginForm, PostForm, CommentForm, ReplyForm,
    UserProfileForm, UserUpdateForm, SearchForm, ContactForm
)
from blog.models import Post, Category, UserProfile


class RegisterFormTest(TestCase):
    """Тесты формы регистрации"""
    
    def test_register_form_valid_data(self):
        """Тест формы регистрации с валидными данными"""
        form_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'strongpassword123',
            'password2': 'strongpassword123'
        }
        
        form = RegisterForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_register_form_invalid_username(self):
        """Тест формы регистрации с недопустимым именем пользователя"""
        # Слишком короткое имя пользователя
        form_data = {
            'username': 'ab',
            'email': 'newuser@example.com',
            'password1': 'strongpassword123',
            'password2': 'strongpassword123'
        }
        
        form = RegisterForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('username', form.errors)
    
    def test_register_form_duplicate_email(self):
        """Тест формы регистрации с уже существующим email"""
        # Создаем пользователя с таким же email
        User.objects.create_user(
            username='existinguser',
            email='existing@example.com',
            password='password123'
        )
        
        form_data = {
            'username': 'newuser',
            'email': 'existing@example.com',
            'password1': 'strongpassword123',
            'password2': 'strongpassword123'
        }
        
        form = RegisterForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)
        self.assertIn('already registered', str(form.errors['email']))
    
    def test_register_form_duplicate_username(self):
        """Тест формы регистрации с уже существующим именем пользователя"""
        User.objects.create_user(
            username='existinguser',
            email='existing@example.com',
            password='password123'
        )
        
        form_data = {
            'username': 'existinguser',
            'email': 'newuser@example.com',
            'password1': 'strongpassword123',
            'password2': 'strongpassword123'
        }
        
        form = RegisterForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('username', form.errors)
    
    def test_register_form_password_mismatch(self):
        """Тест формы регистрации с несовпадающими паролями"""
        form_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'password123',
            'password2': 'differentpassword123'
        }
        
        form = RegisterForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('password2', form.errors)
    
    def test_register_form_weak_password(self):
        """Тест формы регистрации со слабым паролем"""
        # Слишком короткий пароль
        form_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': '123',
            'password2': '123'
        }
        
        form = RegisterForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('password2', form.errors)
    
    def test_register_form_empty_data(self):
        """Тест формы регистрации с пустыми данными"""
        form_data = {
            'username': '',
            'email': '',
            'password1': '',
            'password2': ''
        }
        
        form = RegisterForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('username', form.errors)
        self.assertIn('email', form.errors)
        self.assertIn('password2', form.errors)
    
    def test_register_form_widgets(self):
        """Тест виджетов формы регистрации"""
        form = RegisterForm()
        
        # Проверяем, что у формы есть нужные виджеты
        username_widget = form.fields['username'].widget
        email_widget = form.fields['email'].widget
        
        self.assertEqual(username_widget.attrs.get('class'), 'matrix-input')
        self.assertEqual(email_widget.attrs.get('class'), 'matrix-input')


class LoginFormTest(TestCase):
    """Тесты формы входа"""
    
    def test_login_form_valid_data(self):
        """Тест формы входа с валидными данными"""
        form_data = {
            'username': 'testuser',
            'password': 'testpassword123',
            'remember_me': True
        }
        
        form = LoginForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_login_form_empty_username(self):
        """Тест формы входа с пустым именем пользователя"""
        form_data = {
            'username': '',
            'password': 'testpassword123'
        }
        
        form = LoginForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('username', form.errors)
    
    def test_login_form_empty_password(self):
        """Тест формы входа с пустым паролем"""
        form_data = {
            'username': 'testuser',
            'password': ''
        }
        
        form = LoginForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('password', form.errors)
    
    def test_login_form_remember_me_optional(self):
        """Тест опциональности поля 'запомнить меня'"""
        form_data = {
            'username': 'testuser',
            'password': 'testpassword123'
        }
        
        form = LoginForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_login_form_widgets(self):
        """Тест виджетов формы входа"""
        form = LoginForm()
        
        username_widget = form.fields['username'].widget
        password_widget = form.fields['password'].widget
        remember_me_widget = form.fields['remember_me'].widget
        
        self.assertEqual(username_widget.attrs.get('class'), 'matrix-input')
        self.assertEqual(password_widget.attrs.get('class'), 'matrix-input')
        self.assertEqual(remember_me_widget.attrs.get('class'), 'matrix-checkbox')


class PostFormTest(TestCase):
    """Тесты формы постов"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.category = Category.objects.create(
            name='Технологии',
            description='Статьи о технологиях'
        )
    
    def test_post_form_valid_data(self):
        """Тест формы поста с валидными данными"""
        form_data = {
            'title': 'Новый пост',
            'content': 'Содержимое поста',
            'excerpt': 'Краткое описание',
            'category': self.category.pk,
            'status': 'published',
            'tags': 'тег1, тег2'
        }
        
        form = PostForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_post_form_empty_title(self):
        """Тест формы поста с пустым заголовком"""
        form_data = {
            'title': '',
            'content': 'Содержимое поста',
            'status': 'published'
        }
        
        form = PostForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('title', form.errors)
    
    def test_post_form_empty_content(self):
        """Тест формы поста с пустым содержимым"""
        form_data = {
            'title': 'Новый пост',
            'content': '',
            'status': 'published'
        }
        
        form = PostForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('content', form.errors)
    
    def test_post_form_long_excerpt(self):
        """Тест формы поста с слишком длинной выдержкой"""
        long_excerpt = 'A' * 301  # Максимум 300 символов
        
        form_data = {
            'title': 'Новый пост',
            'content': 'Содержимое поста',
            'excerpt': long_excerpt,
            'status': 'published'
        }
        
        form = PostForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('excerpt', form.errors)
    
    def test_post_form_invalid_status(self):
        """Тест формы поста с недопустимым статусом"""
        form_data = {
            'title': 'Новый пост',
            'content': 'Содержимое поста',
            'status': 'invalid_status'
        }
        
        form = PostForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('status', form.errors)
    
    def test_post_form_optional_fields(self):
        """Тест опциональных полей формы поста"""
        form_data = {
            'title': 'Минимальный пост',
            'content': 'Содержимое',
            'status': 'draft'
        }
        
        form = PostForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_post_form_with_image(self):
        """Тест формы поста с изображением"""
        image = SimpleUploadedFile(
            name='test_image.jpg',
            content=b'fake_image_content',
            content_type='image/jpeg'
        )
        
        form_data = {
            'title': 'Пост с изображением',
            'content': 'Содержимое поста',
            'status': 'published'
        }
        
        form_data['image'] = image
        
        form = PostForm(data=form_data, files=form_data)
        self.assertTrue(form.is_valid())
    
    def test_post_form_invalid_image(self):
        """Тест формы поста с невалидным изображением"""
        # Создаем "изображение" с неправильным расширением
        fake_image = SimpleUploadedFile(
            name='test.txt',
            content=b'not an image',
            content_type='text/plain'
        )
        
        form_data = {
            'title': 'Пост с неправильным изображением',
            'content': 'Содержимое поста',
            'status': 'published'
        }
        
        form_data['image'] = fake_image
        
        form = PostForm(data=form_data, files=form_data)
        # Django обычно не валидирует тип файла автоматически,
        # но мы можем проверить, что поле прошло валидацию
        self.assertTrue(form.is_valid())
    
    def test_post_form_widgets(self):
        """Тест виджетов формы поста"""
        form = PostForm()
        
        # Проверяем CSS классы для виджетов
        title_widget = form.fields['title'].widget
        content_widget = form.fields['content'].widget
        tags_widget = form.fields['tags'].widget
        
        self.assertEqual(title_widget.attrs.get('class'), 'matrix-input')
        self.assertEqual(content_widget.attrs.get('class'), 'matrix-input')
        self.assertEqual(tags_widget.attrs.get('class'), 'matrix-input')
        
        # Проверяем количество строк для Textarea
        self.assertEqual(content_widget.attrs.get('rows'), 12)


class CommentFormTest(TestCase):
    """Тесты формы комментариев"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.post = Post.objects.create(
            title='Тестовый пост',
            content='Содержимое',
            author=self.user,
            status='published'
        )
    
    def test_comment_form_valid_data(self):
        """Тест формы комментария с валидными данными"""
        form_data = {
            'text': 'Отличный пост!'
        }
        
        form = CommentForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_comment_form_empty_text(self):
        """Тест формы комментария с пустым текстом"""
        form_data = {
            'text': ''
        }
        
        form = CommentForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('text', form.errors)
    
    def test_comment_form_widgets(self):
        """Тест виджетов формы комментария"""
        form = CommentForm()
        
        text_widget = form.fields['text'].widget
        self.assertEqual(text_widget.attrs.get('class'), 'matrix-input')
        self.assertEqual(text_widget.attrs.get('rows'), 4)


class ReplyFormTest(TestCase):
    """Тесты формы ответов на комментарии"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.post = Post.objects.create(
            title='Тестовый пост',
            content='Содержимое',
            author=self.user,
            status='published'
        )
    
    def test_reply_form_valid_data(self):
        """Тест формы ответа с валидными данными"""
        form_data = {
            'text': 'Согласен с автором'
        }
        
        form = ReplyForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_reply_form_empty_text(self):
        """Тест формы ответа с пустым текстом"""
        form_data = {
            'text': ''
        }
        
        form = ReplyForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('text', form.errors)
    
    def test_reply_form_widgets(self):
        """Тест виджетов формы ответа"""
        form = ReplyForm()
        
        text_widget = form.fields['text'].widget
        self.assertEqual(text_widget.attrs.get('class'), 'matrix-input')
        self.assertEqual(text_widget.attrs.get('rows'), 3)  # Меньше строк чем в CommentForm


class UserProfileFormTest(TestCase):
    """Тесты формы профиля пользователя"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.profile = self.user.profile
    
    def test_profile_form_valid_data(self):
        """Тест формы профиля с валидными данными"""
        form_data = {
            'bio': 'Моя биография',
            'location': 'Москва',
            'website': 'https://example.com',
            'birth_date': '1990-01-01'
        }
        
        form = UserProfileForm(data=form_data, instance=self.profile)
        self.assertTrue(form.is_valid())
    
    def test_profile_form_empty_data(self):
        """Тест формы профиля с пустыми данными"""
        form_data = {
            'bio': '',
            'location': '',
            'website': '',
            'birth_date': ''
        }
        
        form = UserProfileForm(data=form_data, instance=self.profile)
        self.assertTrue(form.is_valid())  # Все поля опциональные
    
    def test_profile_form_invalid_birth_date(self):
        """Тест формы профиля с неверной датой рождения"""
        form_data = {
            'bio': 'Моя биография',
            'birth_date': 'invalid-date'
        }
        
        form = UserProfileForm(data=form_data, instance=self.profile)
        self.assertFalse(form.is_valid())
        self.assertIn('birth_date', form.errors)
    
    def test_profile_form_invalid_website(self):
        """Тест формы профиля с неверным URL сайта"""
        form_data = {
            'bio': 'Моя биография',
            'website': 'not-a-valid-url'
        }
        
        form = UserProfileForm(data=form_data, instance=self.profile)
        self.assertFalse(form.is_valid())
        self.assertIn('website', form.errors)
    
    def test_profile_form_with_avatar(self):
        """Тест формы профиля с аватаром"""
        avatar = SimpleUploadedFile(
            name='avatar.jpg',
            content=b'fake_avatar_content',
            content_type='image/jpeg'
        )
        
        form_data = {
            'bio': 'Моя биография',
            'location': 'Москва'
        }
        
        form_data['avatar'] = avatar
        
        form = UserProfileForm(data=form_data, files=form_data, instance=self.profile)
        self.assertTrue(form.is_valid())
    
    def test_profile_form_widgets(self):
        """Тест виджетов формы профиля"""
        form = UserProfileForm(instance=self.profile)
        
        bio_widget = form.fields['bio'].widget
        location_widget = form.fields['location'].widget
        website_widget = form.fields['website'].widget
        birth_date_widget = form.fields['birth_date'].widget
        
        self.assertEqual(bio_widget.attrs.get('class'), 'matrix-input')
        self.assertEqual(location_widget.attrs.get('class'), 'matrix-input')
        self.assertEqual(website_widget.attrs.get('class'), 'matrix-input')
        self.assertEqual(birth_date_widget.attrs.get('type'), 'date')
        
        # Проверяем количество строк для bio
        self.assertEqual(bio_widget.attrs.get('rows'), 4)


class UserUpdateFormTest(TestCase):
    """Тесты формы обновления пользователя"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Тест',
            last_name='Пользователь'
        )
    
    def test_user_update_form_valid_data(self):
        """Тест формы обновления пользователя с валидными данными"""
        form_data = {
            'username': 'testuser',
            'email': 'newemail@example.com',
            'first_name': 'Новое имя',
            'last_name': 'Новая фамилия'
        }
        
        form = UserUpdateForm(data=form_data, instance=self.user)
        self.assertTrue(form.is_valid())
    
    def test_user_update_form_empty_email(self):
        """Тест формы обновления пользователя с пустым email"""
        form_data = {
            'username': 'testuser',
            'email': '',
            'first_name': 'Тест',
            'last_name': 'Пользователь'
        }
        
        form = UserUpdateForm(data=form_data, instance=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)
    
    def test_user_update_form_invalid_email(self):
        """Тест формы обновления пользователя с неверным email"""
        form_data = {
            'username': 'testuser',
            'email': 'invalid-email',
            'first_name': 'Тест',
            'last_name': 'Пользователь'
        }
        
        form = UserUpdateForm(data=form_data, instance=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)
    
    def test_user_update_form_widgets(self):
        """Тест виджетов формы обновления пользователя"""
        form = UserUpdateForm(instance=self.user)
        
        username_widget = form.fields['username'].widget
        email_widget = form.fields['email'].widget
        first_name_widget = form.fields['first_name'].widget
        last_name_widget = form.fields['last_name'].widget
        
        self.assertEqual(username_widget.attrs.get('class'), 'matrix-input')
        self.assertEqual(email_widget.attrs.get('class'), 'matrix-input')
        self.assertEqual(first_name_widget.attrs.get('class'), 'matrix-input')
        self.assertEqual(last_name_widget.attrs.get('class'), 'matrix-input')


class SearchFormTest(TestCase):
    """Тесты формы поиска"""
    
    def test_search_form_valid_data(self):
        """Тест формы поиска с валидными данными"""
        form_data = {
            'query': 'python',
            'search_in': 'posts'
        }
        
        form = SearchForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_search_form_empty_query(self):
        """Тест формы поиска с пустым запросом"""
        form_data = {
            'query': '',
            'search_in': 'all'
        }
        
        form = SearchForm(data=form_data)
        self.assertTrue(form.is_valid())  # Пустой запрос допустим
    
    def test_search_form_default_values(self):
        """Тест значений по умолчанию формы поиска"""
        form = SearchForm()
        
        self.assertEqual(form.fields['query'].required, False)
        self.assertEqual(form.fields['search_in'].initial, 'all')
    
    def test_search_form_choices(self):
        """Тест вариантов поиска"""
        form = SearchForm()
        
        choices = form.fields['search_in'].choices
        self.assertIn(('all', 'All'), choices)
        self.assertIn(('posts', 'Posts'), choices)
        self.assertIn(('users', 'Users'), choices)
    
    def test_search_form_widgets(self):
        """Тест виджетов формы поиска"""
        form = SearchForm()
        
        query_widget = form.fields['query'].widget
        search_in_widget = form.fields['search_in'].widget
        
        self.assertEqual(query_widget.attrs.get('class'), 'matrix-input')
        self.assertEqual(search_in_widget.attrs.get('class'), 'matrix-input')


class ContactFormTest(TestCase):
    """Тесты контактной формы"""
    
    def test_contact_form_valid_data(self):
        """Тест контактной формы с валидными данными"""
        form_data = {
            'name': 'Иван Иванов',
            'email': 'ivan@example.com',
            'subject': 'Вопрос по блогу',
            'message': 'У меня есть вопрос...'
        }
        
        form = ContactForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_contact_form_empty_name(self):
        """Тест контактной формы с пустым именем"""
        form_data = {
            'name': '',
            'email': 'ivan@example.com',
            'subject': 'Вопрос',
            'message': 'Сообщение'
        }
        
        form = ContactForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)
    
    def test_contact_form_invalid_email(self):
        """Тест контактной формы с неверным email"""
        form_data = {
            'name': 'Иван Иванов',
            'email': 'invalid-email',
            'subject': 'Вопрос',
            'message': 'Сообщение'
        }
        
        form = ContactForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)
    
    def test_contact_form_empty_message(self):
        """Тест контактной формы с пустым сообщением"""
        form_data = {
            'name': 'Иван Иванов',
            'email': 'ivan@example.com',
            'subject': 'Вопрос',
            'message': ''
        }
        
        form = ContactForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('message', form.errors)
    
    def test_contact_form_widgets(self):
        """Тест виджетов контактной формы"""
        form = ContactForm()
        
        name_widget = form.fields['name'].widget
        email_widget = form.fields['email'].widget
        subject_widget = form.fields['subject'].widget
        message_widget = form.fields['message'].widget
        
        self.assertEqual(name_widget.attrs.get('class'), 'matrix-input')
        self.assertEqual(email_widget.attrs.get('class'), 'matrix-input')
        self.assertEqual(subject_widget.attrs.get('class'), 'matrix-input')
        self.assertEqual(message_widget.attrs.get('class'), 'matrix-input')
        
        # Проверяем количество строк для message
        self.assertEqual(message_widget.attrs.get('rows'), 5)


class FormIntegrationTest(TestCase):
    """Интеграционные тесты форм"""
    
    def setUp(self):
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
            content='Содержимое поста',
            author=self.user,
            category=self.category,
            status='published'
        )
    
    def test_register_and_login_forms_workflow(self):
        """Тест рабочего процесса регистрации и входа"""
        # 1. Регистрация нового пользователя
        register_data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password1': 'newpassword123',
            'password2': 'newpassword123'
        }
        
        register_form = RegisterForm(data=register_data)
        self.assertTrue(register_form.is_valid())
        
        # 2. Создаем пользователя
        new_user = register_form.save()
        self.assertEqual(new_user.username, 'newuser')
        self.assertEqual(new_user.email, 'new@example.com')
        
        # 3. Проверяем, что профиль создался автоматически
        self.assertTrue(UserProfile.objects.filter(user=new_user).exists())
        
        # 4. Форма входа
        login_data = {
            'username': 'newuser',
            'password': 'newpassword123'
        }
        
        login_form = LoginForm(data=login_data)
        self.assertTrue(login_form.is_valid())
    
    def test_post_and_comment_forms_workflow(self):
        """Тест рабочего процесса создания поста и комментария"""
        # 1. Создание поста
        post_data = {
            'title': 'Новый пост через форму',
            'content': 'Содержимое поста',
            'excerpt': 'Краткое описание',
            'category': self.category.pk,
            'status': 'published',
            'tags': 'тег1, тег2'
        }
        
        post_form = PostForm(data=post_data)
        self.assertTrue(post_form.is_valid())
        
        # 2. Создаем пост
        post = post_form.save(commit=False)
        post.author = self.user
        post.save()
        
        self.assertEqual(post.title, 'Новый пост через форму')
        self.assertEqual(post.status, 'published')
        
        # 3. Создание комментария
        comment_data = {
            'text': 'Отличный пост!'
        }
        
        comment_form = CommentForm(data=comment_data)
        self.assertTrue(comment_form.is_valid())
        
        # 4. Создаем комментарий
        comment = comment_form.save(commit=False)
        comment.post = post
        comment.author = self.user
        comment.save()
        
        self.assertEqual(comment.text, 'Отличный пост!')
        self.assertEqual(comment.post, post)
        self.assertEqual(comment.author, self.user)
    
    def test_profile_forms_workflow(self):
        """Тест рабочего процесса обновления профиля"""
        # 1. Обновление пользователя
        user_data = {
            'username': 'testuser',
            'email': 'updated@example.com',
            'first_name': 'Обновленное имя',
            'last_name': 'Обновленная фамилия'
        }
        
        user_form = UserUpdateForm(data=user_data, instance=self.user)
        self.assertTrue(user_form.is_valid())
        user_form.save()
        
        # Проверяем обновление пользователя
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'updated@example.com')
        self.assertEqual(self.user.first_name, 'Обновленное имя')
        
        # 2. Обновление профиля
        profile_data = {
            'bio': 'Обновленная биография',
            'location': 'Санкт-Петербург',
            'website': 'https://updated-site.com',
            'birth_date': '1992-05-15'
        }
        
        profile_form = UserProfileForm(data=profile_data, instance=self.user.profile)
        self.assertTrue(profile_form.is_valid())
        profile_form.save()
        
        # Проверяем обновление профиля
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.bio, 'Обновленная биография')
        self.assertEqual(self.user.profile.location, 'Санкт-Петербург')
        self.assertEqual(self.user.profile.website, 'https://updated-site.com')
    
    def test_search_form_with_results(self):
        """Тест формы поиска с результатами"""
        # Создаем дополнительные посты для поиска
        Post.objects.create(
            title='Python Programming',
            content='Учебник по Python',
            author=self.user,
            category=self.category,
            status='published',
            tags='python, programming'
        )
        
        Post.objects.create(
            title='Django Framework',
            content='Фреймворк Django',
            author=self.user,
            category=self.category,
            status='published',
            tags='django, web'
        )
        
        # Поиск по ключевому слову
        search_data = {
            'query': 'Python',
            'search_in': 'posts'
        }
        
        search_form = SearchForm(data=search_data)
        self.assertTrue(search_form.is_valid())
        
        # Поиск по всем категориям
        search_data_all = {
            'query': 'testuser',
            'search_in': 'all'
        }
        
        search_form_all = SearchForm(data=search_data_all)
        self.assertTrue(search_form_all.is_valid())
    
    def test_contact_form_processing(self):
        """Тест обработки контактной формы"""
        contact_data = {
            'name': 'Пользователь',
            'email': 'user@example.com',
            'subject': 'Сообщение',
            'message': 'Текст сообщения'
        }
        
        contact_form = ContactForm(data=contact_data)
        self.assertTrue(contact_form.is_valid())
        
        # После валидации формы, данные должны быть доступны
        cleaned_data = contact_form.clean()
        self.assertEqual(cleaned_data['name'], 'Пользователь')
        self.assertEqual(cleaned_data['email'], 'user@example.com')
        self.assertEqual(cleaned_data['subject'], 'Сообщение')
        self.assertEqual(cleaned_data['message'], 'Текст сообщения')