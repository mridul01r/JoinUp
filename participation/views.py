from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from .models import Participation

from events.models import Event
from .models import Participation

@login_required
def accept_request(request, participation_id) :
    participation = get_object_or_404(Participation, id=participation_id)

    if request.user == participation.event.created_by :
        if participation.status == 'PENDING' :
            accepted_participation = participation.event.participation_requests.filter(
                status='ACCEPTED'
            ).count()


            if accepted_participation < participation.event.max_participants :
                participation.status = 'ACCEPTED'

                if accepted_participation + 1 == participation.event.max_participants :
                    participation.event.status='FULL'
                    participation.event.save()

                participation.save()
                messages.success(request, "Participation request Accepted successfully.")
                return redirect('home')
            else :
                messages.error(request, "Event is full.")
                return redirect('home')
        else :
            messages.error(request, "There Is No Pending Or New Request")
            return redirect('home')
    else :
        messages.error(request, "Only the event creator can manage participation requests.")
        return redirect('home')


@login_required
def reject_request(request, participation_id) :
    participation = get_object_or_404(Participation, id=participation_id)

    if request.user == participation.event.created_by :
        if participation.status == 'PENDING' :
            participation.status = 'REJECTED'
            participation.save()
            messages.success(request, "Participation request rejected successfully.")
            return redirect('home')
        
        else :
            messages.error(request, "There Is No Pending Or New Request")
            return redirect('home')
    else :
        messages.error(request, "Only the event creator can manage participation requests.")
        return redirect('home')


@login_required
@require_POST
def request_to_join(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    if request.user == event.created_by:
        messages.error(request, "You cannot join your own event.")
        return redirect('home')
    
    if event.status == 'OPEN' :
        accepted_participation = event.participation_requests.filter(status='ACCEPTED').count()

        if accepted_participation < event.max_participants :
            participation, created = Participation.objects.get_or_create(
                user=request.user,
                event=event,
                defaults={'status': 'PENDING'}
            )
            if created :
                messages.success(request, "Your request has been sent successfully.")
                return redirect('home')
            else :
                messages.error(request, "Your request already exits. Wait for Owner to change it's status")
                return redirect('home')
        else :
            messages.error(request, 'You can not join because Event is already full')
            return redirect('home')
    else :
        messages.error(request, 'Event is already full or closed by the owner')
        return redirect('home')

        