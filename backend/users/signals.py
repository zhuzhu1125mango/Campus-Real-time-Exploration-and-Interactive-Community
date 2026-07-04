from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import PointsRecord, UserActivity

User = get_user_model()

LEVEL_THRESHOLDS = [0, 50, 200, 500, 1000, 2000, 5000, 10000]

def update_user_level(user):
    level = 1
    for i, threshold in enumerate(LEVEL_THRESHOLDS):
        if user.points >= threshold:
            level = i + 1
        else:
            break
    if level != user.level:
        user.level = level
        user.save(update_fields=['level'])

@receiver(post_save, sender=PointsRecord)
def update_user_points_and_level(sender, instance, created, **kwargs):
    if created:
        user = instance.user
        user.points += instance.points
        user.save(update_fields=['points'])
        update_user_level(user)

@receiver(post_save, sender=User)
def create_points_record_on_register(sender, instance, created, **kwargs):
    if created:
        PointsRecord.objects.create(
            user=instance,
            action='register',
            points=10,
            description='注册奖励'
        )