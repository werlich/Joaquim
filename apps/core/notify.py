"""Aviso por e-mail de cada interação do blog."""
from __future__ import annotations

import logging

from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


def notify_interaction(*, title: str, detail: str = '', path: str = '/') -> None:
    destino = (getattr(settings, 'INTERACTION_NOTIFY_EMAIL', '') or '').strip()
    if not destino:
        return
    site = (getattr(settings, 'SITE_URL', '') or 'https://joaquim.werlich.com.br').rstrip('/')
    linhas = [title.strip()]
    if detail.strip():
        linhas += ['', detail.strip()]
    linhas += ['', f'Ver no blog: {site}{path}']
    corpo = '\n'.join(linhas)
    assunto = f'[Joaquim] {title.strip()}'[:180]
    try:
        send_mail(
            assunto,
            corpo,
            settings.DEFAULT_FROM_EMAIL,
            [destino],
            fail_silently=False,
        )
    except Exception:
        logger.exception('Não foi possível avisar %s sobre: %s', destino, title)
