
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages

from .models import Notification


@login_required
def notification_list(request):
    notifications = Notification.objects.filter(
        recipient=request.user
    ).select_related('event').order_by('-created_at')

    return render(
        request,
        'notifications/my_notifications.html',
        {'notifications': notifications}
    )


@login_required
@require_POST
def mark_as_read(request, notification_id):
    notification = get_object_or_404(
        Notification,
        id=notification_id,
        recipient=request.user
    )

    notification.is_read = True
    notification.save(update_fields=['is_read'])

    messages.success(request, 'You have marked the message as read.')

    return redirect('notification_list')
