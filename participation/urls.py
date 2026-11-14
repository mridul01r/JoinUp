from django.urls import path
from . import views

urlpatterns = [
    path(
        'accept/<int:participation_id>/',
        views.accept_request,
        name='accept_request'
    ),
    path(
        'reject/<int:participation_id>/',
        views.reject_request,
        name='reject_request'
    ),
    path(
        'request/<int:event_id>/',
        views.request_to_join,
        name='request_to_join'
    ),
    path(
        'owner/requests/',
        views.owner_requests,
        name='owner_requests'
    ),
]