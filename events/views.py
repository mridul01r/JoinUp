from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import ExpressionWrapper, FloatField
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.db.models import F, Value
from django.contrib import messages
from django.utils import timezone
from datetime import date
from .models import Event
from .models import Category
from .forms import EventForm

@login_required
def home(request):
    return render(
        request,
        'events/home.html'
    )

@login_required
def event_list(request):
    events = Event.objects.filter(
        status='OPEN'
    ).select_related(
        'category',
        'created_by'
    ).annotate(
        accepted_count=Count(
            'participation_requests',
            filter=Q(participation_requests__status='ACCEPTED')
        )
    ).annotate(
        available_spots=F('max_participants') - F('accepted_count')
    ).annotate(
        occupancy_percentage=ExpressionWrapper(
            F('accepted_count') * 100.0 / F('max_participants'),
            output_field=FloatField()
        )
    )
    categories = Category.objects.all()

    category_id = request.GET.get('category')
    search_query = request.GET.get('q', '')
    location_query = request.GET.get('location', '')

    # date_query = request.GET.get('date', '')
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')

    if search_query:
        events = events.filter(title__icontains=search_query)

    if category_id:
        events = events.filter(category__id=category_id)

    if location_query:
        events = events.filter(location__icontains=location_query)

    if start_date and end_date :
        start = date.fromisoformat(start_date)
        end = date.fromisoformat(end_date)

        if start > end:
            messages.error(
                request,
                'Invalid date range. Start date must be earlier than or equal to the end date.'
            )
            return redirect('event_list')
        
    if start_date:
        events = events.filter(event_date__date__gte=start_date)

    if end_date:
        events = events.filter(event_date__date__lte=end_date)

    sort_by = request.GET.get('sort', 'upcoming')

    if sort_by == 'upcoming':
        events = events.filter(
            event_date__gte=timezone.now()
        ).order_by('event_date')

    elif sort_by == 'newest':
        events = events.order_by('-created_at')

    elif sort_by == 'oldest':
        events = events.order_by('created_at')

    else:
        sort_by = 'upcoming'
        events = events.filter(
            event_date__gte=timezone.now()
        ).order_by('event_date')

    paginator = Paginator(events, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        'events/event_list.html',
        {
            'events': page_obj,
            'search_query': search_query,
            'categories': categories,
            'category_id': category_id,
            'location_query': location_query,
            # 'date_query': date_query,
            'start_date': start_date,
            'end-date': end_date,
            'page_obj': page_obj,
            'sort_by': sort_by
        }
    )

@login_required
def create_event(request):

    if request.method == 'POST':
        form = EventForm(request.POST)

        if form.is_valid():
            event = form.save(commit=False)
            event.created_by = request.user
            event.save()

            return redirect('event_list')

    else:
        form = EventForm()

    return render(request, 'events/create_event.html', {'form': form})

@login_required
def edit_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    if request.user != event.created_by:
        messages.error(request, "You are not allowed to edit this event.")
        return redirect('event_list')

    accepted_participations = event.participation_requests.filter(
        status='ACCEPTED'
    ).count()

    if accepted_participations > 0 or event.status == 'CANCELLED':
        messages.error(
            request,
            "You cannot edit an event that has accepted participants or is cancelled."
        )
        return redirect('event_list')

    if request.method == 'POST':
        form = EventForm(request.POST, instance=event)

        if form.is_valid():
            form.save()
            messages.success(request, "Event updated successfully!")
            return redirect('event_list')

    else:
        form = EventForm(instance=event)

    return render(request, 'events/edit_event.html', {'form': form})

@login_required
@require_POST
def delete_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    if request.user != event.created_by:
        messages.error(
            request,
            "You are not allowed to delete this event."
        )
        return redirect('event_list')

    accepted_participations = event.participation_requests.filter(
        status='ACCEPTED'
    ).count()

    if accepted_participations > 0 or event.status == 'CANCELLED':
        messages.error(
            request,
            "You cannot delete an event that is cancelled or has accepted participants."
        )
        return redirect('event_list')

    event.delete()

    messages.success(request, "Event successfully deleted.")
    return redirect('event_list')


@login_required
def event_detail(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    request_status = event.participation_requests.filter(
        user=request.user
    ).first()

    accepted_participants = event.participation_requests.filter(
        status='ACCEPTED'
    ).count()
    available_spots = event.max_participants - accepted_participants

    return render(
        request,
        'events/event_detail.html',
        {
            'event': event,
            'accepted_participants': accepted_participants,
            'available_spots': available_spots,
            'request_status': request_status
        }
    )