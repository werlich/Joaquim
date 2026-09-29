from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time

from django.urls import reverse
from django.utils import timezone

from apps.cha.models import ChaRsvp, GiftReservation, ReservationLike
from apps.core.models import TimelineEntry
from apps.core.timeline_meta import display_title
from apps.mensagens.models import Recado

LIMIT = 10
PER_KIND = 40


@dataclass
class BlogUpdate:
    at: datetime
    kind: str
    icon: str
    title: str
    detail: str
    url: str
    show_time: bool = True


def _aware(value: datetime) -> datetime:
    if timezone.is_naive(value):
        return timezone.make_aware(value)
    return value


def _clip(texto: str, n: int = 90) -> str:
    texto = (texto or '').strip()
    if len(texto) <= n:
        return texto
    return texto[: n - 1].rstrip() + '…'


def latest_blog_updates() -> list[BlogUpdate]:
    items: list[BlogUpdate] = []

    recados_url = reverse('recadinhos')
    for recado in Recado.objects.approved()[:PER_KIND]:
        items.append(BlogUpdate(
            at=_aware(recado.created_at),
            kind='recado',
            icon='💌',
            title=f'{recado.nome} deixou um recadinho',
            detail=_clip(recado.mensagem),
            url=recados_url,
        ))

    jornada_url = reverse('timeline')
    for entry in TimelineEntry.objects.filter(is_published=True).order_by('-id')[:PER_KIND]:
        at = timezone.make_aware(datetime.combine(entry.event_date, time(12, 0)))
        items.append(BlogUpdate(
            at=at,
            kind='jornada',
            icon='🌱',
            title='Novo momento na jornada',
            detail=display_title(entry),
            url=jornada_url,
            show_time=False,
        ))

    presentes_url = reverse('cha_presentes')
    reservas = (
        GiftReservation.objects.filter(cancelled_at__isnull=True)
        .select_related('gift')[:PER_KIND]
    )
    for res in reservas:
        who = res.display_name
        presente = (res.item_name or res.gift.name).strip()
        items.append(BlogUpdate(
            at=_aware(res.created_at),
            kind='presente',
            icon='🎁',
            title=f'{who} escolheu um presente',
            detail=_clip(presente),
            url=presentes_url,
        ))

    cha_url = reverse('cha_bebe')
    for rsvp in ChaRsvp.objects.all()[:PER_KIND]:
        who = (rsvp.name or '').strip() or 'Alguém'
        items.append(BlogUpdate(
            at=_aware(rsvp.created_at),
            kind='presenca',
            icon='📅',
            title=f'{who} registrou presença',
            detail=rsvp.get_response_display(),
            url=cha_url,
        ))

    likes = (
        ReservationLike.objects.filter(removed_at__isnull=True)
        .select_related('guest', 'reservation', 'reservation__gift')[:PER_KIND]
    )
    for like in likes:
        who = like.guest.name
        presente = (
            like.reservation.item_name or like.reservation.gift.name
        ).strip()
        items.append(BlogUpdate(
            at=_aware(like.created_at),
            kind='curtida',
            icon='💚',
            title=f'{who} curtiu um presente',
            detail=_clip(presente),
            url=presentes_url,
        ))

    items.sort(key=lambda item: (item.at, item.kind), reverse=True)
    return items
