from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Event

@login_required
def home(request):
    return render(
        request,
        'events/home.html'
    )

@login_required
def event_list(request):
    events = Event.objects.filter(status='OPEN')

    return render(
        request,
        'events/event_list.html',
        {'events': events}
    )