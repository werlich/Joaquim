"""Contagem regressiva do Chá — usa data/hora do evento e o timezone do Django."""
from __future__ import annotations

from datetime import datetime, time, timedelta
import json

from django.conf import settings
from django.utils import timezone

MSG_FAR = 'Estamos contando os dias para comemorarmos juntos 💚'
MSG_MONTH = 'Está chegando! O Chá do Joaquim está cada vez mais perto 🧸'
MSG_WEEK = 'É nesta semana! 💚'
MSG_SOON = 'Está quase na hora! 🥰'
MSG_TODAY = 'É hoje! 🎉 O Chá do Joaquim chegou!'
MSG_ENDED = 'Obrigado a todos que fizeram parte do Chá do Joaquim.'

ENDED_TITLE = '💚 Foi um dia muito especial!'

_MESES = (
    'janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho',
    'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro',
)

PHASE_MESSAGES = {
    'far': MSG_FAR,
    'month': MSG_MONTH,
    'week': MSG_WEEK,
    'soon': MSG_SOON,
    'today': MSG_TODAY,
    'ended': MSG_ENDED,
}

DAY = 86400
HOUR = 3600


def event_starts_at(event) -> datetime:
    """Início do Chá no timezone configurado no Django."""
    naive = datetime.combine(event.event_date, event.event_time)
    return timezone.make_aware(naive, timezone.get_current_timezone())


def event_ends_at(event) -> datetime:
    """Término: meia-noite do dia seguinte, no timezone do Django."""
    next_day = event.event_date + timedelta(days=1)
    naive = datetime.combine(next_day, time.min)
    return timezone.make_aware(naive, timezone.get_current_timezone())


def remaining_parts(total_seconds: float) -> dict[str, int]:
    seconds = max(0, int(total_seconds))
    days, rest = divmod(seconds, DAY)
    hours, rest = divmod(rest, HOUR)
    minutes, secs = divmod(rest, 60)
    return {
        'days': days,
        'hours': hours,
        'minutes': minutes,
        'seconds': secs,
    }


def phase_for(now: datetime, starts_at: datetime, ends_at: datetime, event_date) -> str:
    if now >= ends_at:
        return 'ended'
    local_now = timezone.localtime(now)
    if local_now.date() == event_date:
        return 'today'
    remaining = (starts_at - now).total_seconds()
    if remaining <= 0:
        return 'today'
    if remaining < 48 * HOUR:
        return 'soon'
    if remaining < 7 * DAY:
        return 'week'
    if remaining <= 30 * DAY:
        return 'month'
    return 'far'


def payload(event, now=None) -> dict:
    if now is None:
        now = timezone.now()
    if timezone.is_naive(now):
        now = timezone.make_aware(now, timezone.get_current_timezone())

    starts = event_starts_at(event)
    ends = event_ends_at(event)
    phase = phase_for(now, starts, ends, event.event_date)
    remaining = remaining_parts((starts - now).total_seconds())
    return {
        'phase': phase,
        'message': PHASE_MESSAGES[phase],
        'ended_title': ENDED_TITLE,
        'parts': remaining,
        'starts_at_iso': starts.isoformat(timespec='seconds'),
        'ends_at_iso': ends.isoformat(timespec='seconds'),
        'event_date_iso': event.event_date.isoformat(),
        'date_label': (
            f'{event.event_date.day} de {_MESES[event.event_date.month - 1]} '
            f'de {event.event_date.year}'
        ),
        'timezone': settings.TIME_ZONE,
        'ended': phase == 'ended',
        'messages_json': json.dumps(PHASE_MESSAGES, ensure_ascii=False),
    }
