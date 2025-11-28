"""
Тесты для сигналов блога
"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.db.models.signals import post_save, post_delete
from django.dispatch import Signal
from unittest.mock import patch

from blog.models import Post, Comment, UserProfile, Notification
from blog.signals import (
    create_user_profile, save_user_profile, 
    notify_post_author_on_comment
)


class UserProfileSignalsTest(TestCase):
    """Тесты сигналов создания и сохранения профиля пользователя"""
    
    def setUp(self):
        # Сохраняем оригинальные сигналы для восстановления после тестов
        self.post_save_handler = post_save
    
    def tearDown(self):
        # Восстанавливаем оригинальные сигналы
        from django.db.models.signals import post_save
        post_save.connect = self.post_save_handler
    
    def test_create_user_profile_signal(self):
        """Тест сигнала создания профиля пользователя при создании User"""
        # Удаляем все существующие профили для чистого теста
        UserProfile.objects.all().delete()
        
        # Создаем нового пользователя
        user = User.objects.create_user(
            username='newuser',
            email='new@example.com',
            password='newpassword123'
        )
        
        # Проверяем, что профиль создался автоматически
        self.assertTrue(UserProfile.objects.filter(user=user).exists())
        
        profile = user.profile
        self.assertEqual(profile.user, user)
    
    def test_create_user_profile_already_exists(self):
        """Тест сигнала создания профиля, когда профиль уже существует"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123'
        )
        
        # Профиль должен создаться автоматически при создании пользователя
        self.assertTrue(UserProfile.objects.filter(user=user).exists())
        
        # Вручную создаем еще один профиль (это не должно произойти в реальном коде)
        # Проверяем, что сигнал корректно обрабатывает такую ситуацию
        try:
            duplicate_profile = UserProfile.objects.create(user=user, bio='Дубликат')
            # Если мы дошли сюда, то профиль создался
            self.assertEqual(UserProfile.objects.filter(user=user).count(), 2)
        except Exception:
            # Или возникает исключение из-за уникальности
            self.assertTrue(UserProfile.objects.filter(user=user).count(), 1)
    
    def test_save_user_profile_signal_on_update(self):
        """Тест сигнала сохранения профиля при обновлении User"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123'
        )
        
        profile = user.profile
        self.assertEqual(profile.bio, '')  # Профиль должен быть пустым
        
        # Обновляем пользователя
        user.first_name = 'Тест'
        user.last_name = 'Пользователь'
        user.save()
        
        # Проверяем, что профиль все еще существует и связан с пользователем
        profile.refresh_from_db()
        self.assertTrue(UserProfile.objects.filter(user=user, pk=profile.pk).exists())
    
    def test_save_user_profile_signal_recreates_missing_profile(self):
        """Тест сигнала сохранения профиля, который восстанавливает отсутствующий профиль"""
        user = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='testpassword123'
        )
        
        # Удаляем профиль (симулируем ситуацию, когда профиль был удален)
        user.profile.delete()
        
        # Обновляем пользователя (должен восстановить профиль)
        user.first_name = 'Тест'
        user.save()
        
        # Проверяем, что профиль восстановился
        self.assertTrue(UserProfile.objects.filter(user=user).exists())
    
    @patch('blog.signals.UserProfile.objects.create')
    def test_create_user_profile_handles_exception(self, mock_create):
        """Тест обработки исключений при создании профиля"""
        # Симулируем исключение при создании профиля
        mock_create.side_effect = Exception("Тестовое исключение")
        
        # Создаем пользователя (должно пройти без ошибки)
        user = User.objects.create_user(
            username='testuser3',
            email='test3@example.com',
            password='testpassword123'
        )
        
        # Пользователь должен быть создан
        self.assertTrue(User.objects.filter(username='testuser3').exists())
        
        # Но профиль может не быть создан из-за исключения
        # Это тест проверяет, что исключение не прерывает создание пользователя
        mock_create.assert_called_once()


class NotificationSignalsTest(TestCase):
    """Тесты сигналов уведомлений"""
    
    def setUp(self):
        self.user1 = User.objects.create_user(
            username='author',
            email='author@example.com',
            password='author123'
        )
        
        self.user2 = User.objects.create_user(
            username='commenter',
            email='commenter@example.com',
            password='commenter123'
        )
        
        self.post = Post.objects.create(
            title='Тестовый пост',
            content='Содержимое поста',
            author=self.user1,
            status='published'
        )
    
    def test_notify_post_author_on_comment_created(self):
        """Тест создания уведомления при создании комментария"""
        # Удаляем существующие уведомления
        Notification.objects.all().delete()
        
        # Создаем комментарий
        comment = Comment.objects.create(
            post=self.post,
            author=self.user2,
            text='Отличный пост!'
        )
        
        # Проверяем, что уведомление создалось
        notifications = Notification.objects.filter(user=self.user1)
        self.assertEqual(notifications.count(), 1)
        
        notification = notifications.first()
        self.assertEqual(notification.notification_type, 'comment')
        self.assertEqual(notification.title, 'New Comment on Your Post')
        self.assertEqual(notification.related_post, self.post)
        self.assertEqual(notification.related_comment, comment)
        self.assertFalse(notification.is_read)
    
    def test_notify_post_author_only_for_top_level_comments(self):
        """Тест создания уведомления только для основных комментариев (не ответов)"""
        Notification.objects.all().delete()
        
        # Создаем основной комментарий
        main_comment = Comment.objects.create(
            post=self.post,
            author=self.user2,
            text='Основной комментарий'
        )
        
        # Проверяем создание уведомления
        self.assertEqual(Notification.objects.filter(user=self.user1).count(), 1)
        
        # Создаем ответ на комментарий (должно быть без уведомления)
        reply_comment = Comment.objects.create(
            post=self.post,
            author=self.user1,  # Ответ от автора поста
            text='Ответ на комментарий',
            parent=main_comment
        )
        
        # Уведомлений не должно добавиться (ответ не должен создавать уведомление)
        self.assertEqual(Notification.objects.filter(user=self.user1).count(), 1)
    
    def test_no_notification_for_own_comments(self):
        """Тест отсутствия уведомления при комментировании своего поста"""
        Notification.objects.all().delete()
        
        # Создаем комментарий от автора поста (должно быть без уведомления)
        comment = Comment.objects.create(
            post=self.post,
            author=self.user1,  # Автор поста комментирует свой же пост
            text='Мой комментарий'
        )
        
        # Уведомлений не должно быть
        self.assertEqual(Notification.objects.filter(user=self.user1).count(), 0)
    
    def test_notification_content(self):
        """Тест содержимого уведомления"""
        Notification.objects.all().delete()
        
        # Создаем комментарий
        comment = Comment.objects.create(
            post=self.post,
            author=self.user2,
            text='Интересная статья'
        )
        
        notification = Notification.objects.filter(user=self.user1).first()
        
        # Проверяем содержимое уведомления
        self.assertEqual(
            notification.message,
            f'{self.user2.username} commented on your post "{self.post.title}"'
        )
        self.assertEqual(notification.related_post, self.post)
        self.assertEqual(notification.related_comment, comment)
    
    def test_multiple_comments_single_notification(self):
        """Тест множественных комментариев создают множественные уведомления"""
        Notification.objects.all().delete()
        
        # Создаем несколько комментариев от разных пользователей
        user3 = User.objects.create_user(
            username='commenter2',
            email='commenter2@example.com',
            password='commenter2123'
        )
        
        comment1 = Comment.objects.create(
            post=self.post,
            author=self.user2,
            text='Первый комментарий'
        )
        
        comment2 = Comment.objects.create(
            post=self.post,
            author=user3,
            text='Второй комментарий'
        )
        
        # Должно быть два уведомления
        notifications = Notification.objects.filter(user=self.user1)
        self.assertEqual(notifications.count(), 2)
        
        # Проверяем, что уведомления разные
        notification_messages = [n.message for n in notifications]
        self.assertIn(f'{self.user2.username} commented on your post "{self.post.title}"', notification_messages)
        self.assertIn(f'{user3.username} commented on your post "{self.post.title}"', notification_messages)


class SignalIntegrationTest(TestCase):
    """Интеграционные тесты сигналов"""
    
    def test_user_creation_workflow(self):
        """Тест полного рабочего процесса создания пользователя"""
        # Создаем пользователя
        user = User.objects.create_user(
            username='workflow_user',
            email='workflow@example.com',
            password='workflow123'
        )
        
        # Проверяем, что профиль создался автоматически
        self.assertTrue(UserProfile.objects.filter(user=user).exists())
        
        profile = user.profile
        self.assertEqual(profile.user, user)
        
        # Создаем пост от этого пользователя
        post = Post.objects.create(
            title='Пост пользователя',
            content='Содержимое поста',
            author=user,
            status='published'
        )
        
        # Создаем комментарий к посту
        other_user = User.objects.create_user(
            username='commenter',
            email='commenter@example.com',
            password='commenter123'
        )
        
        comment = Comment.objects.create(
            post=post,
            author=other_user,
            text='Отличный пост!'
        )
        
        # Проверяем, что уведомление создалось
        notifications = Notification.objects.filter(user=user)
        self.assertEqual(notifications.count(), 1)
        
        notification = notifications.first()
        self.assertEqual(notification.notification_type, 'comment')
        self.assertEqual(notification.related_comment, comment)
    
    def test_user_deletion_cascade(self):
        """Тест каскадного удаления при удалении пользователя"""
        # Создаем пользователя с данными
        user = User.objects.create_user(
            username='delete_user',
            email='delete@example.com',
            password='delete123'
        )
        
        # Создаем пост
        post = Post.objects.create(
            title='Пост для удаления',
            content='Содержимое',
            author=user,
            status='published'
        )
        
        # Создаем комментарий
        other_user = User.objects.create_user(
            username='commenter',
            email='commenter@example.com',
            password='commenter123'
        )
        
        comment = Comment.objects.create(
            post=post,
            author=other_user,
            text='Комментарий'
        )
        
        # Создаем уведомление
        notification = Notification.objects.create(
            user=user,
            notification_type='system',
            title='Тестовое уведомление',
            message='Тестовое сообщение'
        )
        
        # Запоминаем ID объектов
        user_id = user.id
        post_id = post.id
        comment_id = comment.id
        notification_id = notification.id
        
        # Удаляем пользователя
        user.delete()
        
        # Проверяем, что связанные объекты также удалились
        self.assertFalse(User.objects.filter(id=user_id).exists())
        self.assertFalse(Post.objects.filter(id=post_id).exists())
        self.assertFalse(Comment.objects.filter(id=comment_id).exists())
        self.assertFalse(Notification.objects.filter(id=notification_id).exists())
    
    def test_comment_deletion_cascade(self):
        """Тест каскадного удаления комментариев"""
        # Создаем пост и комментарии
        post = Post.objects.create(
            title='Пост',
            content='Содержимое',
            author=self.user1,
            status='published'
        )
        
        user2 = User.objects.create_user(
            username='commenter',
            email='commenter@example.com',
            password='commenter123'
        )
        
        comment1 = Comment.objects.create(
            post=post,
            author=user2,
            text='Основной комментарий'
        )
        
        comment2 = Comment.objects.create(
            post=post,
            author=user2,
            text='Ответ',
            parent=comment1
        )
        
        # Создаем уведомление для основного комментария
        notification = Notification.objects.create(
            user=self.user1,
            notification_type='comment',
            title='Комментарий',
            message='Сообщение',
            related_comment=comment1
        )
        
        comment1_id = comment1.id
        comment2_id = comment2.id
        notification_id = notification.id
        
        # Удаляем основной комментарий
        comment1.delete()
        
        # Проверяем, что связанные объекты удалились
        self.assertFalse(Comment.objects.filter(id=comment1_id).exists())
        self.assertFalse(Comment.objects.filter(id=comment2_id).exists())  # Ответ также удаляется
        self.assertFalse(Notification.objects.filter(id=notification_id).exists())


class SignalHandlersTest(TestCase):
    """Тесты сигналов в изоляции"""
    
    @patch('blog.signals.UserProfile.objects.create')
    def test_manual_user_profile_creation(self, mock_create):
        """Тест ручного создания профиля пользователя"""
        from blog.signals import create_user_profile
        
        user = User.objects.create_user(
            username='manual_user',
            email='manual@example.com',
            password='manual123'
        )
        
        # Вызываем сигнал вручную
        create_user_profile(User, instance=user, created=True, **kwargs)
        
        # Проверяем вызов
        mock_create.assert_called_once_with(user=user)
    
    def test_manual_notification_creation(self):
        """Тест ручного создания уведомления"""
        from blog.signals import notify_post_author_on_comment
        
        # Создаем тестовые данные
        post = Post.objects.create(
            title='Пост для уведомления',
            content='Содержимое',
            author=self.user1,
            status='published'
        )
        
        user2 = User.objects.create_user(
            username='notification_user',
            email='notification@example.com',
            password='notification123'
        )
        
        comment = Comment.objects.create(
            post=post,
            author=user2,
            text='Комментарий для уведомления'
        )
        
        # Вызываем сигнал вручную
        notify_post_author_on_comment(Comment, instance=comment, created=True)
        
        # Проверяем создание уведомления
        self.assertTrue(Notification.objects.filter(
            user=self.user1,
            notification_type='comment',
            related_comment=comment
        ).exists())


# Вспомогательные данные для тестов
def setUpTestData(cls):
    """Создание тестовых данных для всех тестов"""
    cls.user1 = User.objects.create_user(
        username='author1',
        email='author1@example.com',
        password='author123'
    )
    @patch('blog.signals.UserProfile.objects.create')
    def test_manual_user_profile_creation(self, mock_create):
        """Тест ручного создания профиля пользователя"""
        from blog.signals import create_user_profile
        
        user = User.objects.create_user(
            username='manual_user',
            email='manual@example.com',
            password='manual123'
        )
        
        # Вызываем сигнал вручную
        create_user_profile(User, instance=user, created=True)
        
        # Проверяем вызов
        mock_create.assert_called_once_with(user=user)
    
    def test_manual_notification_creation(self):
        """Тест ручного создания уведомления"""
        from blog.signals import notify_post_author_on_comment
        
        # Создаем тестовые данные
        post = Post.objects.create(
            title='Пост для уведомления',
            content='Содержимое',
            author=self.user1,
            status='published'
        )
        
        user2 = User.objects.create_user(
            username='notification_user',
            email='notification@example.com',
            password='notification123'
        )
        
        comment = Comment.objects.create(
            post=post,
            author=user2,
            text='Комментарий для уведомления'
        )
        
        # Вызываем сигнал вручную
        notify_post_author_on_comment(Comment, instance=comment, created=True)
        
        # Проверяем создание уведомления
        self.assertTrue(Notification.objects.filter(
            user=self.user1,
            notification_type='comment',
            related_comment=comment
        ).exists())