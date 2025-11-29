from .models import SiteSettings, Category

def site_settings(request):
    return {'site_settings': SiteSettings.load()}

def categories(request):
    return {'categories': Category.objects.all()}

def user_notifications(request):
    if request.user.is_authenticated:
        unread_count = request.user.notifications.filter(is_read=False).count()
        return {'unread_notifications_count': unread_count}
    return {'unread_notifications_count': 0}
