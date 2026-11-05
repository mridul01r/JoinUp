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
]