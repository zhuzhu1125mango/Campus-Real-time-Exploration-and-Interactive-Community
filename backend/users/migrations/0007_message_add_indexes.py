# Generated manually for adding Message indexes

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0006_user_level_user_points_pointsrecord'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='message',
            index=models.Index(fields=['sender', 'receiver', 'created_at'], name='users_messag_sender__6c4c50_idx'),
        ),
        migrations.AddIndex(
            model_name='message',
            index=models.Index(fields=['receiver', 'is_read', 'sender'], name='users_messag_receive_3e2c3e_idx'),
        ),
    ]
