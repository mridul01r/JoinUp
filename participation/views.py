from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.db.models import Count, Q
from django.core.paginator import Paginator
from .models import Participation
from events.models import Event


@login_required
@require_POST
def accept_request(request, participation_id):
    participation = get_object_or_404(Participation, id=participation_id)

    if request.user == participation.event.created_by:
        if participation.event.status != 'OPEN':
            messages.error(
                request, "This event is not open for participation.")
            return redirect(
                'event_detail',
                event_id=participation.event.id
            )

        if participation.status == 'PENDING':
            accepted_participation = participation.event.participation_requests.filter(
                status='ACCEPTED'
            ).count()

            if accepted_participation < participation.event.max_participants:
                participation.status = 'ACCEPTED'

                if accepted_participation + 1 == participation.event.max_participants:
                    participation.event.status = 'FULL'
                    participation.event.save()

                participation.save()
                messages.success(
                    request, "Participation request Accepted successfully.")
                return redirect(
                    'event_detail',
                    event_id=participation.event.id
                )
            else:
                messages.error(request, "Event is full.")
                return redirect(
                    'event_detail',
                    event_id=participation.event.id
                )
        else:
            messages.error(request, "There Is No Pending Or New Request")
            return redirect(
                'event_detail',
                event_id=participation.event.id
            )
    else:
        messages.error(
            request, "Only the event creator can manage participation requests.")
        return redirect(
            'event_detail',
            event_id=participation.event.id
        )


@login_required
@require_POST
def reject_request(request, participation_id):
    participation = get_object_or_404(Participation, id=participation_id)

    if request.user == participation.event.created_by:
        if participation.status == 'PENDING':
            participation.status = 'REJECTED'
            participation.save()
            messages.success(
                request, "Participation request rejected successfully.")
            return redirect(
                'event_detail',
                event_id=participation.event.id
            )

        else:
            messages.error(request, "There Is No Pending Or New Request")
            return redirect(
                'event_detail',
                event_id=participation.event.id
            )
    else:
        messages.error(
            request, "Only the event creator can manage participation requests.")
        return redirect(
            'event_detail',
            event_id=participation.event.id
        )


@login_required
@require_POST
def request_to_join(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    if request.user == event.created_by:
        messages.error(request, "You cannot join your own event.")
        return redirect('event_detail', event_id=event.id)

    if event.status == 'OPEN':
        accepted_participation = event.participation_requests.filter(
            status='ACCEPTED').count()

        if accepted_participation < event.max_participants:
            participation, created = Participation.objects.get_or_create(
                user=request.user,
                event=event,
                defaults={'status': 'PENDING'}
            )
            if created:
                messages.success(
                    request, "Your request has been sent successfully.")
                return redirect('event_detail', event_id=event.id)

            else:
                if participation.status == 'REJECTED':
                    participation.status = 'PENDING'
                    participation.save()

                    messages.success(
                        request, "Your request has been sent again successfully.")
                    return redirect('event_detail', event_id=event.id)

                else:
                    messages.error(
                        request,
                        "Your request already exists. Wait for the owner to change its status."
                    )
                    return redirect('event_detail', event_id=event.id)
        else:
            messages.error(
                request, 'You can not join because Event is already full')
            return redirect('event_detail', event_id=event.id)
    else:
        messages.error(request, 'Event is already full or closed by the owner')
        return redirect('event_detail', event_id=event.id)


@login_required
def owner_requests(request):
    pending_requests = Participation.objects.filter(
        event__created_by=request.user,
        status='PENDING'
    )

    return render(
        request,
        'participation/owner_requests.html',
        {'pending_requests': pending_requests}
    )


@login_required
def my_requests(request):

    my_participations = Participation.objects.filter(
        user=request.user
    ).select_related(
        'event',
        'event__category'
    )

    statistics = my_participations.aggregate(
        pending_count=Count(
            'id',
            filter=Q(status='PENDING')
        ),
        accepted_count=Count(
            'id',
            filter=Q(status='ACCEPTED')
        ),
        rejected_count=Count(
            'id',
            filter=Q(status='REJECTED')
        )
    )

    total_request = my_participations.count()
    status_filter = request.GET.get('status', '')

    accepted_rate = 0
    rejected_rate = 0
    pending_rate = 0

    if total_request > 0:
        accepted_rate = (
            statistics['accepted_count'] / total_request
        ) * 100

        rejected_rate = (
            statistics['rejected_count'] / total_request
        ) * 100

        pending_rate = (
            statistics['pending_count'] / total_request
        ) * 100

    accepted_rate = round(accepted_rate, 2)
    rejected_rate = round(rejected_rate, 2)
    pending_rate = round(pending_rate, 2)

    search_query = request.GET.get('q', '')

    if search_query:
        my_participations = my_participations.filter(
            event__title__icontains=search_query
        )
        
    if status_filter:
        my_participations = my_participations.filter(
            status=status_filter
        )

    paginator = Paginator(my_participations, 2)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        'participation/my_requests.html',
        {
            'status_filter': status_filter,
            'pending_count': statistics['pending_count'],
            'accepted_count': statistics['accepted_count'],
            'rejected_count': statistics['rejected_count'],
            'total_request': total_request,
            'accepted_rate': accepted_rate,
            'rejected_rate': rejected_rate,
            'pending_rate': pending_rate ,
            'search_query': search_query,
            'page_obj': page_obj,
            'my_participations': page_obj,
        }
    )


@login_required
@require_POST
def cancel_request(request, participation_id):
    participation = get_object_or_404(
        Participation,
        id=participation_id
    )

    event_id = participation.event.id

    if request.user == participation.user:
        if participation.status == 'PENDING':
            participation.delete()
            messages.success(
                request,
                "Your participation request has been cancelled."
            )
        else:
            messages.error(
                request,
                "Only pending requests can be cancelled."
            )
    else:
        messages.error(
            request,
            "You are not allowed to perform this action."
        )

    return redirect('event_detail', event_id=event_id)
