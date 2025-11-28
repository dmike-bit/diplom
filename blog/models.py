from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse
from django.core.exceptions import ValidationError

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=7, default='#00ff41')
    created_date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']
    
    def __str__(self):
        return self.name

class Post(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ]
    
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    content = models.TextField()
    excerpt = models.TextField(max_length=300, blank=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blog_posts')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='posts')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    created_date = models.DateTimeField(default=timezone.now)
    published_date = models.DateTimeField(blank=True, null=True)
    updated_date = models.DateTimeField(auto_now=True)
    image = models.ImageField(upload_to='posts/%Y/%m/%d/', blank=True, null=True)
    views = models.PositiveIntegerField(default=0)
    likes = models.ManyToManyField(User, related_name='post_likes', blank=True)
    tags = models.CharField(max_length=200, blank=True)
    
    class Meta:
        ordering = ['-published_date', '-created_date']
    
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse('post_detail', kwargs={'pk': self.pk, 'slug': self.slug})
    
    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            base_slug = slugify(self.title)
            if not base_slug:
                base_slug = 'post'
            self.slug = base_slug
            counter = 1
            while Post.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                self.slug = f"{base_slug}-{counter}"
                counter += 1
        if self.status == 'published' and not self.published_date:
            self.published_date = timezone.now()
        if not self.excerpt and self.content:
            self.excerpt = self.content[:297] + '...' if len(self.content) > 300 else self.content
        super().save(*args, **kwargs)
    
    def like_count(self):
        return self.likes.count()
    
    def comment_count(self):
        return self.comments.filter(is_active=True).count()
    
    def is_published(self):
        return self.status == 'published'

class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blog_comments')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    text = models.TextField()
    created_date = models.DateTimeField(default=timezone.now)
    updated_date = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    likes = models.ManyToManyField(User, related_name='comment_likes', blank=True)
    
    class Meta:
        ordering = ['-created_date']
    
    def __str__(self):
        return f'Comment by {self.author} on {self.post}'
    
    def reply_count(self):
        return self.replies.filter(is_active=True).count()
    
    def like_count(self):
        return self.likes.count()

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(max_length=500, blank=True)
    location = models.CharField(max_length=100, blank=True)
    website = models.URLField(blank=True)
    avatar = models.ImageField(upload_to='avatars/%Y/%m/%d/', blank=True, null=True)
    birth_date = models.DateField(null=True, blank=True)
    is_banned = models.BooleanField(default=False)
    ban_reason = models.TextField(blank=True)
    ban_expires = models.DateTimeField(null=True, blank=True)
    email_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f'{self.user.username} Profile'
    
    def is_currently_banned(self):
        if not self.is_banned:
            return False
        if self.ban_expires and timezone.now() > self.ban_expires:
            self.is_banned = False
            self.save()
            return False
        return True

class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('comment', 'New Comment'),
        ('reply', 'Reply to Comment'),
        ('like_post', 'Post Liked'),
        ('like_comment', 'Comment Liked'),
        ('system', 'System'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    related_post = models.ForeignKey(Post, on_delete=models.CASCADE, null=True, blank=True)
    related_comment = models.ForeignKey(Comment, on_delete=models.CASCADE, null=True, blank=True)
    is_read = models.BooleanField(default=False)
    created_date = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-created_date']
    
    def __str__(self):
        return f'Notification for {self.user.username}: {self.title}'

class SiteSettings(models.Model):
    site_name = models.CharField(max_length=100, default='The Matrix Blog')
    site_description = models.TextField(default='Welcome to the Matrix. The choice is yours.')
    admin_email = models.EmailField(default='admin@matrix.com')
    posts_per_page = models.PositiveIntegerField(default=10)
    allow_registration = models.BooleanField(default=True)
    allow_comments = models.BooleanField(default=True)
    moderate_comments = models.BooleanField(default=False)
    maintenance_mode = models.BooleanField(default=False)
    
    class Meta:
        verbose_name_plural = "Site Settings"
    
    def save(self, *args, **kwargs):
        if not self.pk and SiteSettings.objects.exists():
            raise ValidationError('There can be only one SiteSettings instance')
        return super().save(*args, **kwargs)
    
    @classmethod
    def load(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj
