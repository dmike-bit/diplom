from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q, Count
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.http import require_POST
from django.contrib.auth.models import User
from .models import Post, Comment, UserProfile, Category, Notification, SiteSettings
from .forms import RegisterForm, LoginForm, PostForm, CommentForm, ReplyForm, UserProfileForm, UserUpdateForm, SearchForm, ContactForm

def get_site_settings():
    return SiteSettings.load()

def is_user_banned(user):
    if not user.is_authenticated:
        return False
    try:
        return user.profile.is_currently_banned()
    except UserProfile.DoesNotExist:
        UserProfile.objects.create(user=user)
        return False

def index(request):
    site_settings = get_site_settings()
    posts_list = Post.objects.filter(status='published').select_related('author', 'category').prefetch_related('comments')
    
    featured_posts = posts_list.order_by('-views')[:3]
    latest_posts = posts_list.order_by('-published_date')[:6]
    categories = Category.objects.annotate(post_count=Count('posts'))
    
    context = {
        'featured_posts': featured_posts,
        'latest_posts': latest_posts,
        'categories': categories,
        'site_settings': site_settings,
    }
    return render(request, 'blog/index.html', context)

def post_list(request):
    site_settings = get_site_settings()
    posts_list = Post.objects.filter(status='published').select_related('author', 'category')
    
    category_id = request.GET.get('category')
    if category_id:
        posts_list = posts_list.filter(category_id=category_id)
    
    search_form = SearchForm(request.GET)
    if search_form.is_valid() and search_form.cleaned_data['query']:
        query = search_form.cleaned_data['query']
        posts_list = posts_list.filter(Q(title__icontains=query) | Q(content__icontains=query) | Q(excerpt__icontains=query) | Q(tags__icontains=query))
    
    paginator = Paginator(posts_list, site_settings.posts_per_page)
    page = request.GET.get('page')
    try:
        posts = paginator.page(page)
    except PageNotAnInteger:
        posts = paginator.page(1)
    except EmptyPage:
        posts = paginator.page(paginator.num_pages)
    
    categories = Category.objects.annotate(post_count=Count('posts'))
    
    context = {
        'posts': posts,
        'categories': categories,
        'search_form': search_form,
        'site_settings': site_settings,
    }
    return render(request, 'blog/post_list.html', context)

def post_detail(request, pk, slug=None):
    post = get_object_or_404(Post.objects.select_related('author', 'category').prefetch_related('comments__author'), pk=pk, status='published')
    post.views += 1
    post.save()
    
    comments = post.comments.filter(is_active=True, parent=None).order_by('-created_date')
    
    comment_form = CommentForm()
    reply_form = ReplyForm()
    
    user_liked = False
    if request.user.is_authenticated:
        user_liked = post.likes.filter(id=request.user.id).exists()
    
    context = {
        'post': post,
        'comments': comments,
        'comment_form': comment_form,
        'reply_form': reply_form,
        'user_liked': user_liked,
        'site_settings': get_site_settings(),
    }
    return render(request, 'blog/post_detail.html', context)

@login_required
def post_new(request):
    if is_user_banned(request.user):
        messages.error(request, 'You are banned and cannot create posts.')
        return redirect('index')
    
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            if post.status == 'published':
                post.published_date = timezone.now()
            post.save()
            messages.success(request, 'Post created successfully!')
            return redirect('post_detail', pk=post.pk, slug=post.slug)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PostForm()
    
    # Добавляем категории в контекст
    categories = Category.objects.all()
    
    context = {
        'form': form,
        'title': 'Create New Post',
        'categories': categories,  # Добавляем категории
        'site_settings': get_site_settings(),
    }
    return render(request, 'blog/post_edit.html', context)

@login_required
def post_edit(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if post.author != request.user and not request.user.is_staff:
        return HttpResponseForbidden("You don't have permission to edit this post.")
    
    if is_user_banned(request.user):
        messages.error(request, 'You are banned and cannot edit posts.')
        return redirect('post_detail', pk=post.pk, slug=post.slug)
    
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            post = form.save()
            messages.success(request, 'Post updated successfully!')
            return redirect('post_detail', pk=post.pk, slug=post.slug)
    else:
        form = PostForm(instance=post)
    
    # Добавляем категории в контекст
    categories = Category.objects.all()
    
    context = {
        'form': form,
        'title': 'Edit Post',
        'post': post,
        'categories': categories,  # Добавляем категории
        'site_settings': get_site_settings(),
    }
    return render(request, 'blog/post_edit.html', context)

@login_required
@require_POST
def post_like(request, pk):
    if is_user_banned(request.user):
        return JsonResponse({'error': 'You are banned'}, status=403)
    
    post = get_object_or_404(Post, pk=pk)
    if post.likes.filter(id=request.user.id).exists():
        post.likes.remove(request.user)
        liked = False
    else:
        post.likes.add(request.user)
        liked = True
    
    return JsonResponse({'liked': liked, 'like_count': post.like_count()})

def register(request):
    site_settings = get_site_settings()
    if not site_settings.allow_registration:
        messages.error(request, 'Registration is currently disabled.')
        return redirect('index')
    
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            # UserProfile создается автоматически через сигналы - НЕ создаем здесь!
            login(request, user, backend="django.contrib.auth.backends.ModelBackend")
            messages.success(request, 'Welcome to the Matrix! Your account has been created.')
            return redirect('index')
    else:
        form = RegisterForm()
    
    context = {'form': form, 'site_settings': site_settings}
    return render(request, 'blog/register.html', context)

def user_login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            remember_me = form.cleaned_data.get('remember_me', False)
            
            user = authenticate(request, username=username, password=password)
            if user is not None:
                if is_user_banned(user):
                    messages.error(request, 'Your account has been banned.')
                    return render(request, 'blog/login.html', {'form': form})
                
                login(request, user)
                if not remember_me:
                    request.session.set_expiry(0)
                
                messages.success(request, f'Welcome back, {user.username}!')
                next_url = request.GET.get('next', 'index')
                return redirect(next_url)
            else:
                messages.error(request, 'Invalid username or password.')
    else:
        form = LoginForm()
    
    context = {'form': form, 'site_settings': get_site_settings()}
    return render(request, 'blog/login.html', context)

@login_required
def user_logout(request):
    logout(request)
    messages.info(request, 'You have been logged out successfully.')
    return redirect('index')

@login_required
@require_POST
def comment_create(request, post_pk):
    if is_user_banned(request.user):
        messages.error(request, 'You are banned and cannot comment.')
        return redirect('post_detail', pk=post_pk)
    
    post = get_object_or_404(Post, pk=post_pk)
    form = CommentForm(request.POST)
    
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.author = request.user
        comment.save()
        messages.success(request, 'Your comment has been posted.')
    
    return redirect('post_detail', pk=post_pk, slug=post.slug)

@login_required
@require_POST
def reply_create(request, comment_pk):
    if is_user_banned(request.user):
        messages.error(request, 'You are banned and cannot reply.')
        return redirect('index')
    
    parent_comment = get_object_or_404(Comment, pk=comment_pk)
    form = ReplyForm(request.POST)
    
    if form.is_valid():
        reply = form.save(commit=False)
        reply.post = parent_comment.post
        reply.author = request.user
        reply.parent = parent_comment
        reply.save()
        messages.success(request, 'Your reply has been posted.')
    
    return redirect('post_detail', pk=parent_comment.post.pk, slug=parent_comment.post.slug)

@login_required
@require_POST
def comment_like(request, comment_pk):
    if is_user_banned(request.user):
        return JsonResponse({'error': 'You are banned'}, status=403)
    
    comment = get_object_or_404(Comment, pk=comment_pk)
    if comment.likes.filter(id=request.user.id).exists():
        comment.likes.remove(request.user)
        liked = False
    else:
        comment.likes.add(request.user)
        liked = True
    
    return JsonResponse({'liked': liked, 'like_count': comment.like_count()})

@login_required
def profile(request):
    user_posts = Post.objects.filter(author=request.user).order_by('-created_date')
    user_comments = Comment.objects.filter(author=request.user).order_by('-created_date')
    notifications = Notification.objects.filter(user=request.user, is_read=False)[:5]
    
    context = {
        'user_posts': user_posts,
        'user_comments': user_comments,
        'notifications': notifications,
        'site_settings': get_site_settings(),
    }
    return render(request, 'blog/profile.html', context)

@login_required
def profile_edit(request):
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = UserProfileForm(request.POST, request.FILES, instance=request.user.profile)
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Your profile has been updated!')
            return redirect('profile')
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = UserProfileForm(instance=request.user.profile)
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'site_settings': get_site_settings(),
    }
    return render(request, 'blog/profile_edit.html', context)

@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password has been changed!')
            return redirect('profile')
    else:
        form = PasswordChangeForm(request.user)
    
    context = {'form': form, 'site_settings': get_site_settings()}
    return render(request, 'blog/change_password.html', context)

def user_list(request):
    users = User.objects.filter(is_active=True).select_related('profile').order_by('-date_joined')
    paginator = Paginator(users, 20)
    page = request.GET.get('page')
    try:
        users_page = paginator.page(page)
    except PageNotAnInteger:
        users_page = paginator.page(1)
    except EmptyPage:
        users_page = paginator.page(paginator.num_pages)
    
    context = {'users': users_page, 'site_settings': get_site_settings()}
    return render(request, 'blog/user_list.html', context)

def user_profile(request, username):
    user = get_object_or_404(User, username=username)
    posts = Post.objects.filter(author=user, status='published').order_by('-published_date')
    comments = Comment.objects.filter(author=user, is_active=True).order_by('-created_date')[:10]
    
    context = {
        'profile_user': user,
        'posts': posts,
        'comments': comments,
        'site_settings': get_site_settings(),
    }
    return render(request, 'blog/user_public_profile.html', context)

def search(request):
    form = SearchForm(request.GET)
    results = []
    
    if form.is_valid() and form.cleaned_data['query']:
        query = form.cleaned_data['query']
        search_in = form.cleaned_data['search_in']
        
        if search_in in ['all', 'posts']:
            posts = Post.objects.filter(Q(title__icontains=query) | Q(content__icontains=query) | Q(excerpt__icontains=query) | Q(tags__icontains=query), status='published')
            results.extend(posts)
        
        if search_in in ['all', 'users']:
            users = User.objects.filter(Q(username__icontains=query) | Q(first_name__icontains=query) | Q(last_name__icontains=query) | Q(email__icontains=query))
            results.extend(users)
    
    context = {
        'form': form,
        'results': results,
        'query': form.cleaned_data.get('query', ''),
        'site_settings': get_site_settings(),
    }
    return render(request, 'blog/search.html', context)

def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            messages.success(request, 'Your message has been sent! We will get back to you soon.')
            return redirect('contact')
    else:
        form = ContactForm()
    
    context = {'form': form, 'site_settings': get_site_settings()}
    return render(request, 'blog/contact.html', context)

@login_required
@require_POST
def mark_notification_read(request, notification_pk):
    notification = get_object_or_404(Notification, pk=notification_pk, user=request.user)
    notification.is_read = True
    notification.save()
    return JsonResponse({'success': True})

@login_required
def get_unread_notifications(request):
    notifications = Notification.objects.filter(user=request.user, is_read=False)[:10]
    data = [{'id': n.id, 'title': n.title, 'message': n.message, 'created_date': n.created_date.strftime('%Y-%m-%d %H:%M'), 'type': n.notification_type} for n in notifications]
    return JsonResponse({'notifications': data})
