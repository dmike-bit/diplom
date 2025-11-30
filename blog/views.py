# Импорты Django для работы с HTTP запросами, аутентификацией, моделями и формами
from django.shortcuts import render, redirect, get_object_or_404  # Базовые функции представлений
from django.contrib.auth import login, authenticate, logout, update_session_auth_hash  # Аутентификация пользователей
from django.contrib.auth.decorators import login_required  # Декоратор для ограничения доступа
from django.contrib.auth.forms import PasswordChangeForm  # Форма смены пароля
from django.contrib import messages  # Система сообщений Django
from django.utils import timezone  # Утилиты для работы с временем
from django.db.models import Q, Count  # ORM запросы и агрегация
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger  # Пагинация
from django.http import JsonResponse, HttpResponseForbidden  # HTTP ответы
from django.views.decorators.http import require_POST  # Декоратор для POST запросов
from django.contrib.auth.models import User  # Модель пользователя Django
from .models import Post, Comment, UserProfile, Category, Notification, SiteSettings  # Модели приложения
from .forms import RegisterForm, LoginForm, PostForm, CommentForm, ReplyForm, UserProfileForm, UserUpdateForm, SearchForm, ContactForm  # Формы приложения

def get_site_settings():
    """Получить настройки сайта (Singleton паттерн)"""
    return SiteSettings.load()

def is_user_banned(user):
    """Проверить, заблокирован ли пользователь"""
    if not user.is_authenticated:
        return False  # Гость не может быть заблокирован
    try:
        return user.profile.is_currently_banned()  # Проверяем статус блокировки
    except UserProfile.DoesNotExist:
        UserProfile.objects.create(user=user)  # Создаем профиль если не существует
        return False

def index(request):
    """Главная страница блога - отображает избранные и последние посты"""
    site_settings = get_site_settings()  # Получаем настройки сайта
    posts_list = Post.objects.filter(status='published').select_related('author', 'category').prefetch_related('comments')
    
    featured_posts = posts_list.order_by('-views')[:3]  # Топ 3 самых просматриваемых постов
    latest_posts = posts_list.order_by('-published_date')[:6]  # 6 последних постов
    categories = Category.objects.annotate(post_count=Count('posts'))  # Категории с количеством постов
    
    context = {
        'featured_posts': featured_posts,
        'latest_posts': latest_posts,
        'categories': categories,
        'site_settings': site_settings,
    }
    return render(request, 'blog/index.html', context)

def post_list(request):
    """Страница со списком всех постов с поддержкой фильтрации, поиска и пагинации"""
    site_settings = get_site_settings()
    posts_list = Post.objects.filter(status='published').select_related('author', 'category')
    
    category_id = request.GET.get('category')  # Получаем ID категории из URL параметров
    if category_id:
        posts_list = posts_list.filter(category_id=category_id)  # Фильтруем по категории
    
    search_form = SearchForm(request.GET)
    if search_form.is_valid() and search_form.cleaned_data['query']:
        query = search_form.cleaned_data['query']
        # Поиск по заголовку, содержимому, краткому описанию и тегам
        posts_list = posts_list.filter(
            Q(title__icontains=query) | Q(content__icontains=query) |
            Q(excerpt__icontains=query) | Q(tags__icontains=query)
        )
    
    paginator = Paginator(posts_list, site_settings.posts_per_page)  # Пагинация
    page = request.GET.get('page')
    try:
        posts = paginator.page(page)  # Получаем нужную страницу
    except PageNotAnInteger:
        posts = paginator.page(1)  # Если страница не число, показываем первую
    except EmptyPage:
        posts = paginator.page(paginator.num_pages)  # Если страница вне диапазона, показываем последнюю
    
    categories = Category.objects.annotate(post_count=Count('posts'))  # Категории с количеством постов
    
    context = {
        'posts': posts,
        'categories': categories,
        'search_form': search_form,
        'site_settings': site_settings,
    }
    return render(request, 'blog/post_list.html', context)

def post_detail(request, pk, slug=None):
    """Детальная страница поста с комментариями и формой лайка"""
    # Получаем пост с связанными данными для оптимизации запросов
    post = get_object_or_404(
        Post.objects.select_related('author', 'category').prefetch_related('comments__author'),
        pk=pk, status='published'
    )
    post.views += 1  # Увеличиваем счетчик просмотров
    post.save()
    
    # Получаем только родительские комментарии (без ответов) в порядке убывания
    comments = post.comments.filter(is_active=True, parent=None).order_by('-created_date')
    
    comment_form = CommentForm()  # Форма для нового комментария
    reply_form = ReplyForm()  # Форма для ответа на комментарий
    
    user_liked = False
    if request.user.is_authenticated:
        user_liked = post.likes.filter(id=request.user.id).exists()  # Проверяем, лайкнул ли пользователь пост
    
    context = {
        'post': post,
        'comments': comments,
        'comment_form': comment_form,
        'reply_form': reply_form,
        'user_liked': user_liked,
        'site_settings': get_site_settings(),
    }
    return render(request, 'blog/post_detail.html', context)

@login_required  # Только авторизованные пользователи
def post_new(request):
    """Создание нового поста"""
    if is_user_banned(request.user):
        messages.error(request, 'Вы заблокированы и не можете создавать посты.')
        return redirect('index')
    
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)  # Обрабатываем отправленную форму
        if form.is_valid():
            post = form.save(commit=False)  # Сохраняем пост без фиксации в БД
            post.author = request.user  # Устанавливаем автора
            if post.status == 'published':
                post.published_date = timezone.now()  # Устанавливаем дату публикации
            post.save()  # Сохраняем в базу данных
            messages.success(request, 'Пост успешно создан!')
            return redirect('post_detail', pk=post.pk, slug=post.slug)  # Перенаправляем на детальную страницу
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки ниже.')
    else:
        form = PostForm()  # Показываем пустую форму
    
    categories = Category.objects.all()  # Получаем все категории для выбора
    
    context = {
        'form': form,
        'title': 'Создать новый пост',
        'categories': categories,
        'site_settings': get_site_settings(),
    }
    return render(request, 'blog/post_edit.html', context)  # Используем один шаблон для создания и редактирования

@login_required  # Только авторизованные пользователи
def post_edit(request, pk):
    """Редактирование существующего поста"""
    post = get_object_or_404(Post, pk=pk)  # Получаем пост или 404 ошибка
    # Проверяем права доступа: автор поста или админ
    if post.author != request.user and not request.user.is_staff:
        return HttpResponseForbidden("У вас нет прав на редактирование этого поста.")
    
    if is_user_banned(request.user):
        messages.error(request, 'Вы заблокированы и не можете редактировать посты.')
        return redirect('post_detail', pk=post.pk, slug=post.slug)
    
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, instance=post)  # Заполняем форму данными поста
        if form.is_valid():
            post = form.save()  # Сохраняем обновленный пост
            messages.success(request, 'Пост успешно обновлен!')
            return redirect('post_detail', pk=post.pk, slug=post.slug)
    else:
        form = PostForm(instance=post)  # Заполняем форму текущими данными поста
    
    categories = Category.objects.all()
    
    context = {
        'form': form,
        'title': 'Редактировать пост',
        'post': post,
        'categories': categories,
        'site_settings': get_site_settings(),
    }
    return render(request, 'blog/post_edit.html', context)

@login_required  # Только авторизованные пользователи
@require_POST  # Только POST запросы
def post_like(request, pk):
    """AJAX обработчик лайков постов"""
    if is_user_banned(request.user):
        return JsonResponse({'error': 'Вы заблокированы'}, status=403)
    
    post = get_object_or_404(Post, pk=pk)  # Получаем пост
    
    # Переключаем статус лайка: если уже лайкнут - убираем, иначе добавляем
    if post.likes.filter(id=request.user.id).exists():
        post.likes.remove(request.user)  # Убираем лайк
        liked = False
    else:
        post.likes.add(request.user)  # Добавляем лайк
        liked = True
    
    # Возвращаем JSON ответ с новым статусом и количеством лайков
    return JsonResponse({'liked': liked, 'like_count': post.like_count()})

def register(request):
    """Регистрация нового пользователя"""
    site_settings = get_site_settings()
    # Проверяем, разрешена ли регистрация в настройках сайта
    if not site_settings.allow_registration:
        messages.error(request, 'Регистрация временно отключена.')
        return redirect('index')
    
    if request.method == 'POST':
        form = RegisterForm(request.POST)  # Обрабатываем форму регистрации
        if form.is_valid():
            user = form.save()  # Сохраняем нового пользователя
            # UserProfile создается автоматически через сигналы Django - НЕ создаем здесь!
            login(request, user, backend="django.contrib.auth.backends.ModelBackend")  # Автоматический вход после регистрации
            messages.success(request, 'Добро пожаловать в Матрицу! Ваш аккаунт создан.')
            return redirect('index')
    else:
        form = RegisterForm()  # Показываем пустую форму регистрации
    
    context = {'form': form, 'site_settings': site_settings}
    return render(request, 'blog/register.html', context)

def user_login(request):
    """Вход пользователя в систему"""
    if request.method == 'POST':
        form = LoginForm(request.POST)  # Обрабатываем форму входа
        if form.is_valid():
            username = form.cleaned_data['username']  # Получаем логин
            password = form.cleaned_data['password']  # Получаем пароль
            remember_me = form.cleaned_data.get('remember_me', False)  # Запомнить ли пользователя
            
            user = authenticate(request, username=username, password=password)  # Аутентификация
            if user is not None:
                if is_user_banned(user):  # Проверяем статус блокировки
                    messages.error(request, 'Ваш аккаунт заблокирован.')
                    return render(request, 'blog/login.html', {'form': form})
                
                login(request, user)  # Входим в систему
                if not remember_me:
                    request.session.set_expiry(0)  # Сессия истекает при закрытии браузера
                
                messages.success(request, f'С возвращением, {user.username}!')
                next_url = request.GET.get('next', 'index')  # Перенаправляем на следующую страницу
                return redirect(next_url)
            else:
                messages.error(request, 'Неверный логин или пароль.')
    else:
        form = LoginForm()  # Показываем пустую форму входа
    
    context = {'form': form, 'site_settings': get_site_settings()}
    return render(request, 'blog/login.html', context)

@login_required  # Только для авторизованных пользователей
def user_logout(request):
    """Выход пользователя из системы"""
    logout(request)  # Завершаем сессию
    messages.info(request, 'Вы успешно вышли из системы.')
    return redirect('index')

@login_required  # Только авторизованные пользователи
@require_POST  # Только POST запросы
def comment_create(request, post_pk):
    """Создание нового комментария к посту"""
    if is_user_banned(request.user):
        messages.error(request, 'Вы заблокированы и не можете комментировать.')
        return redirect('post_detail', pk=post_pk)
    
    post = get_object_or_404(Post, pk=post_pk)  # Получаем пост
    form = CommentForm(request.POST)  # Обрабатываем форму комментария
    
    if form.is_valid():
        comment = form.save(commit=False)  # Сохраняем без фиксации в БД
        comment.post = post  # Связываем комментарий с постом
        comment.author = request.user  # Устанавливаем автора комментария
        comment.save()  # Сохраняем в базу данных
        messages.success(request, 'Ваш комментарий опубликован.')
    
    return redirect('post_detail', pk=post_pk, slug=post.slug)  # Возвращаемся к посту

@login_required  # Только авторизованные пользователи
@require_POST  # Только POST запросы
def reply_create(request, comment_pk):
    """Создание ответа на комментарий (вложенный комментарий)"""
    if is_user_banned(request.user):
        messages.error(request, 'Вы заблокированы и не можете отвечать.')
        return redirect('index')
    
    parent_comment = get_object_or_404(Comment, pk=comment_pk)  # Получаем родительский комментарий
    form = ReplyForm(request.POST)  # Обрабатываем форму ответа
    
    if form.is_valid():
        reply = form.save(commit=False)  # Сохраняем без фиксации в БД
        reply.post = parent_comment.post  # Связываем ответ с постом
        reply.author = request.user  # Устанавливаем автора ответа
        reply.parent = parent_comment  # Устанавливаем родительский комментарий
        reply.save()  # Сохраняем в базу данных
        messages.success(request, 'Ваш ответ опубликован.')
    
    return redirect('post_detail', pk=parent_comment.post.pk, slug=parent_comment.post.slug)

@login_required  # Только авторизованные пользователи
@require_POST  # Только POST запросы
def comment_like(request, comment_pk):
    """AJAX обработчик лайков комментариев"""
    if is_user_banned(request.user):
        return JsonResponse({'error': 'Вы заблокированы'}, status=403)
    
    comment = get_object_or_404(Comment, pk=comment_pk)  # Получаем комментарий
    
    # Переключаем статус лайка
    if comment.likes.filter(id=request.user.id).exists():
        comment.likes.remove(request.user)  # Убираем лайк
        liked = False
    else:
        comment.likes.add(request.user)  # Добавляем лайк
        liked = True
    
    # Возвращаем JSON ответ
    return JsonResponse({'liked': liked, 'like_count': comment.like_count()})

@login_required  # Только для авторизованных пользователей
def profile(request):
    """Личный кабинет пользователя - показывает посты, комментарии и уведомления"""
    user_posts = Post.objects.filter(author=request.user).order_by('-created_date')  # Посты пользователя
    user_comments = Comment.objects.filter(author=request.user).order_by('-created_date')  # Комментарии пользователя
    notifications = Notification.objects.filter(user=request.user, is_read=False)[:5]  # Последние 5 непрочитанных уведомлений
    
    context = {
        'user_posts': user_posts,
        'user_comments': user_comments,
        'notifications': notifications,
        'site_settings': get_site_settings(),
    }
    return render(request, 'blog/profile.html', context)

@login_required  # Только для авторизованных пользователей
def profile_edit(request):
    """Редактирование профиля пользователя"""
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)  # Форма обновления данных пользователя
        profile_form = UserProfileForm(request.POST, request.FILES, instance=request.user.profile)  # Форма профиля
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()  # Сохраняем обновленные данные пользователя
            profile_form.save()  # Сохраняем обновленный профиль
            messages.success(request, 'Ваш профиль обновлен!')
            return redirect('profile')
    else:
        user_form = UserUpdateForm(instance=request.user)  # Заполняем формы текущими данными
        profile_form = UserProfileForm(instance=request.user.profile)
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'site_settings': get_site_settings(),
    }
    return render(request, 'blog/profile_edit.html', context)

@login_required  # Только для авторизованных пользователей
def change_password(request):
    """Смена пароля пользователя"""
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)  # Встроенная форма Django для смены пароля
        if form.is_valid():
            user = form.save()  # Сохраняем новый пароль
            update_session_auth_hash(request, user)  # Обновляем hash сессии чтобы пользователь остался авторизованным
            messages.success(request, 'Ваш пароль изменен!')
            return redirect('profile')
    else:
        form = PasswordChangeForm(request.user)  # Показываем пустую форму
    
    context = {'form': form, 'site_settings': get_site_settings()}
    return render(request, 'blog/change_password.html', context)

def user_list(request):
    """Список всех пользователей сайта с пагинацией"""
    users = User.objects.filter(is_active=True).select_related('profile').order_by('-date_joined')  # Только активные пользователи
    paginator = Paginator(users, 20)  # 20 пользователей на страницу
    page = request.GET.get('page')
    try:
        users_page = paginator.page(page)  # Получаем нужную страницу
    except PageNotAnInteger:
        users_page = paginator.page(1)  # По умолчанию первая страница
    except EmptyPage:
        users_page = paginator.page(paginator.num_pages)  # Последняя страница если номер больше максимума
    
    context = {'users': users_page, 'site_settings': get_site_settings()}
    return render(request, 'blog/user_list.html', context)

def user_profile(request, username):
    """Публичный профиль пользователя - доступен всем посетителям"""
    user = get_object_or_404(User, username=username)  # Получаем пользователя по username или 404
    posts = Post.objects.filter(author=user, status='published').order_by('-published_date')  # Опубликованные посты автора
    comments = Comment.objects.filter(author=user, is_active=True).order_by('-created_date')[:10]  # Последние 10 активных комментариев
    
    context = {
        'profile_user': user,  # Пользователь чей профиль просматривается
        'posts': posts,
        'comments': comments,
        'site_settings': get_site_settings(),
    }
    return render(request, 'blog/user_public_profile.html', context)

def search(request):
    """Поиск по постам и пользователям"""
    form = SearchForm(request.GET)  # Форма поиска с GET параметрами
    results = []  # Список результатов поиска
    
    if form.is_valid() and form.cleaned_data['query']:
        query = form.cleaned_data['query']  # Поисковый запрос
        search_in = form.cleaned_data['search_in']  # Где искать (посты, пользователи или все)
        
        if search_in in ['all', 'posts']:
            # Поиск по постам: заголовок, содержимое, краткое описание, теги
            posts = Post.objects.filter(
                Q(title__icontains=query) | Q(content__icontains=query) |
                Q(excerpt__icontains=query) | Q(tags__icontains=query),
                status='published'
            )
            results.extend(posts)  # Добавляем посты к результатам
        
        if search_in in ['all', 'users']:
            # Поиск по пользователям: логин, имя, фамилия, email
            users = User.objects.filter(
                Q(username__icontains=query) | Q(first_name__icontains=query) |
                Q(last_name__icontains=query) | Q(email__icontains=query)
            )
            results.extend(users)  # Добавляем пользователей к результатам
    
    context = {
        'form': form,
        'results': results,
        'query': form.cleaned_data.get('query', ''),  # Передаем поисковый запрос обратно в форму
        'site_settings': get_site_settings(),
    }
    return render(request, 'blog/search.html', context)

def contact(request):
    """Страница обратной связи - форма для отправки сообщений администрации"""
    if request.method == 'POST':
        form = ContactForm(request.POST)  # Обрабатываем отправленную форму
        if form.is_valid():
            messages.success(request, 'Ваше сообщение отправлено! Мы свяжемся с вами в ближайшее время.')
            return redirect('contact')  # Очищаем форму после успешной отправки
    else:
        form = ContactForm()  # Показываем пустую форму
    
    context = {'form': form, 'site_settings': get_site_settings()}
    return render(request, 'blog/contact.html', context)

@login_required  # Только для авторизованных пользователей
@require_POST  # Только POST запросы
def mark_notification_read(request, notification_pk):
    """AJAX обработчик отметки уведомления как прочитанное"""
    notification = get_object_or_404(Notification, pk=notification_pk, user=request.user)  # Получаем уведомление или 404
    notification.is_read = True  # Отмечаем как прочитанное
    notification.save()  # Сохраняем изменения
    return JsonResponse({'success': True})  # Возвращаем JSON подтверждение

@login_required  # Только для авторизованных пользователей
def get_unread_notifications(request):
    """AJAX обработчик получения списка непрочитанных уведомлений"""
    notifications = Notification.objects.filter(user=request.user, is_read=False)[:10]  # Последние 10 непрочитанных
    # Преобразуем в JSON-совместимый формат
    data = [
        {
            'id': n.id,
            'title': n.title,
            'message': n.message,
            'created_date': n.created_date.strftime('%Y-%m-%d %H:%M'),
            'type': n.notification_type
        }
        for n in notifications
    ]
    return JsonResponse({'notifications': data})  # Возвращаем список уведомлений
