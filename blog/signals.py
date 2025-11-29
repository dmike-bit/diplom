from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import UserProfile, Comment, Notification

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    try:
        instance.profile.save()
    except UserProfile.DoesNotExist:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=Comment)
def notify_post_author_on_comment(sender, instance, created, **kwargs):
    if created and not instance.parent:
        post_author = instance.post.author
        if post_author != instance.author:
            Notification.objects.create(
                user=post_author,
                notification_type='comment',
                title='New Comment on Your Post',
                message=f'{instance.author.username} commented on your post "{instance.post.title}"',
                related_post=instance.post,
                related_comment=instance
            )
