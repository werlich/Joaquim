from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('timeline/', views.timeline, name='timeline'),
    path('manifest.webmanifest', views.webmanifest, name='webmanifest'),
    path('service-worker.js', views.service_worker, name='service_worker'),
    path('offline/', views.offline, name='offline'),
]
