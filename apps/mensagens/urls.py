from django.urls import path

from . import views

urlpatterns = [
    path('recadinhos/', views.recadinhos, name='recadinhos'),
]
