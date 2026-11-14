from django.urls import path
from . import views

urlpatterns = [
    path('home/', views.home, name='home'),
    path(
        '',
        views.event_list,
        name='event_list'
    )
]