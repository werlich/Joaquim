from django.urls import path

from . import views

urlpatterns = [
    path('cha/', views.cha_bebe, name='cha_bebe'),
    path('cha/acesso/', views.cha_acesso, name='cha_acesso'),
    path('cha/presentes/', views.cha_presentes, name='cha_presentes'),
    path('cha/confirmar-presenca/', views.cha_rsvp, name='cha_rsvp'),
    path(
        'cha/presentes/<int:gift_id>/reservar/',
        views.reservar_presente_view,
        name='reservar_presente',
    ),
    path(
        'cha/fraldas/<int:size_id>/reservar/',
        views.reservar_fralda_view,
        name='reservar_fralda',
    ),
    path(
        'cha/presentes/escolha/<int:reservation_id>/curtir/',
        views.curtir_escolha_view,
        name='curtir_escolha',
    ),
    # Legado
    path('cha-de-bebe/', views.cha_legado_redirect),
    path(
        'cha-de-bebe/presentes/<int:gift_id>/reservar/',
        views.reservar_presente_view,
        name='reservar_presente_legado',
    ),
    path(
        'cha-de-bebe/fraldas/<int:size_id>/reservar/',
        views.reservar_fralda_view,
        name='reservar_fralda_legado',
    ),
]
