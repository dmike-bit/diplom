from django.contrib import admin
from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils import timezone
from django.utils.html import format_html
from .models import Post, Comment, UserProfile, Category, Notification, SiteSettings

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    fields = ['bio', 'location', 'website', 'avatar', 'birth_date', 'is_banned', 'ban_reason', 'ban_expires', 'email_verified']
    readonly_fields = ['created_at', 'updated_at']

class UserAdmin(BaseUserAdmin):
    inlines = [UserProfileInline]
    list_display = ['username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active', 'get_banned_status', 'date_joined']
    list_filter = ['is_staff', 'is_superuser', 'is_active', 'profile__is_banned', 'date_joined']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    actions = ['ban_users', 'unban_users', 'activate_users', 'deactivate_users']
    
    def get_banned_status(self, obj):
        try:
            return obj.profile.is_banned
        except UserProfile.DoesNotExist:
            return False
    get_banned_status.short_description = 'Banned'
    get_banned_status.boolean = True

    def ban_users(self, request, queryset):
        for user in queryset:
            profile, created = UserProfile.objects.get_or_create(user=user)
            profile.is_banned = True
            profile.ban_reason = "Banned by admin"
            profile.save()
        self.message_user(request, f"{queryset.count()} users have been banned.")
    ban_users.short_description = "Ban selected users"

    def unban_users(self, request, queryset):
        for user in queryset:
            profile, created = UserProfile.objects.get_or_create(user=user)
            profile.is_banned = False
            profile.ban_reason = ""
            profile.ban_expires = None
            profile.save()
        self.message_user(request, f"{queryset.count()} users have been unbanned.")
    unban_users.short_description = "Unban selected users"

class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'color_display', 'post_count', 'created_date']
    list_filter = ['created_date']
    search_fields = ['name', 'description']
    
    def color_display(self, obj):
        return format_html('<span style="display: inline-block; width: 20px; height: 20px; background-color: {}; border: 1px solid #555;"></span> {}', obj.color, obj.color)
    color_display.short_description = 'Color'
    
    def post_count(self, obj):
        return obj.posts.count()
    post_count.short_description = 'Posts'

class PostAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'category', 'status', 'published_date', 'view_count', 'like_count', 'comment_count']
    list_filter = ['status', 'category', 'created_date', 'published_date', 'author']
    search_fields = ['title', 'content', 'excerpt', 'tags']
    list_editable = ['status']
    readonly_fields = ['views', 'created_date', 'updated_date', 'published_date']
    prepopulated_fields = {'slug': ['title']}
    date_hierarchy = 'published_date'
    filter_horizontal = ['likes']
    actions = ['publish_posts', 'unpublish_posts', 'archive_posts']
    
    def view_count(self, obj):
        return obj.views
    view_count.short_description = 'Views'
    
    def like_count(self, obj):
        return obj.like_count()
    like_count.short_description = 'Likes'
    
    def comment_count(self, obj):
        return obj.comment_count()
    comment_count.short_description = 'Comments'
    
    def publish_posts(self, request, queryset):
        updated = queryset.update(status='published', published_date=timezone.now())
        self.message_user(request, f"{updated} posts have been published.")
    publish_posts.short_description = "Publish selected posts"

class CommentAdmin(admin.ModelAdmin):
    list_display = ['author', 'post_preview', 'text_preview', 'is_active', 'created_date', 'like_count', 'reply_count']
    list_filter = ['is_active', 'created_date', 'post__category']
    search_fields = ['text', 'author__username', 'post__title']
    list_editable = ['is_active']
    readonly_fields = ['created_date', 'updated_date']
    actions = ['activate_comments', 'deactivate_comments']
    
    def post_preview(self, obj):
        return obj.post.title[:50] + '...' if len(obj.post.title) > 50 else obj.post.title
    post_preview.short_description = 'Post'
    
    def text_preview(self, obj):
        return obj.text[:100] + '...' if len(obj.text) > 100 else obj.text
    text_preview.short_description = 'Comment'
    
    def like_count(self, obj):
        return obj.like_count()
    like_count.short_description = 'Likes'
    
    def reply_count(self, obj):
        return obj.reply_count()
    reply_count.short_description = 'Replies'
    
    def activate_comments(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} comments have been activated.")
    activate_comments.short_description = "Activate selected comments"

class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'notification_type', 'title_preview', 'is_read', 'created_date']
    list_filter = ['notification_type', 'is_read', 'created_date']
    search_fields = ['title', 'message', 'user__username']
    readonly_fields = ['created_date']
    actions = ['mark_as_read', 'mark_as_unread']
    
    def title_preview(self, obj):
        return obj.title[:50] + '...' if len(obj.title) > 50 else obj.title
    title_preview.short_description = 'Title'

class SiteSettingsAdmin(admin.ModelAdmin):
    list_display = ['site_name', 'admin_email', 'allow_registration', 'allow_comments', 'maintenance_mode']
    
    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()

admin.site.unregister(User)
admin.site.unregister(Group)
admin.site.register(User, UserAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Post, PostAdmin)
admin.site.register(Comment, CommentAdmin)
admin.site.register(Notification, NotificationAdmin)
admin.site.register(SiteSettings, SiteSettingsAdmin)

admin.site.site_header = "The Matrix Blog - Administration"
admin.site.site_title = "Matrix Control Panel"
admin.site.index_title = "Welcome to the Matrix Control Panel"
