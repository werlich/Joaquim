"""Antispam leve para recados públicos: honeypot + rate limit por IP."""
from __future__ import annotations

from django.core.cache import cache

RATE_LIMIT_MAX = 3
RATE_LIMIT_WINDOW = 600  # 10 minutos


def client_ip(request) -> str:
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR') or 'unknown'


def rate_limit_key(request) -> str:
    return f'recado:{client_ip(request)}'


def is_rate_limited(request) -> bool:
    return int(cache.get(rate_limit_key(request), 0) or 0) >= RATE_LIMIT_MAX


def register_submission(request) -> int:
    key = rate_limit_key(request)
    try:
        return int(cache.incr(key))
    except ValueError:
        cache.set(key, 1, RATE_LIMIT_WINDOW)
        return 1
