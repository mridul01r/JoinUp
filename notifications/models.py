from django.db import models
from django.conf import settings
from events.models import Event
# Create your models here.
class Notification(models.Model):

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )

    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        null=True, 
        blank=True,
        related_name='event_notification'
    )
    
    message = models.TextField()

    is_read = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

