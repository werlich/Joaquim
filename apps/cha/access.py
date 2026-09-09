"""Acesso ao conteúdo privado do Chá / Timeline (sessão + rate limit)."""
from __future__ import annotations

from functools import wraps
from urllib.parse import urlencode

from django.core.cache import cache
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse

SESSION_KEY = 'cha_access_ok'
SESSION_GUEST_ID = 'cha_guest_id'
RATE_LIMIT_MAX = 5
RATE_LIMIT_WINDOW = 600  # 10 minutos

# Destinos internos permitidos após login (evita open redirect).
_ALLOWED_NEXT_PREFIXES = ('/timeline/', '/cha/presentes/', '/cha/')


def _client_ip(request) -> str:
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR') or 'unknown'


def rate_limit_key(request) -> str:
    return f'cha_invite_fail:{_client_ip(request)}'


def is_rate_limited(request) -> bool:
    return int(cache.get(rate_limit_key(request), 0) or 0) >= RATE_LIMIT_MAX


def register_failed_attempt(request) -> int:
    key = rate_limit_key(request)
    try:
        return int(cache.incr(key))
    except ValueError:
        cache.set(key, 1, RATE_LIMIT_WINDOW)
        return 1


def clear_failed_attempts(request) -> None:
    cache.delete(rate_limit_key(request))


def has_cha_access(request) -> bool:
    return bool(request.session.get(SESSION_KEY))


def grant_cha_access(request, guest=None) -> None:
    request.session[SESSION_KEY] = True
    if guest is not None:
        request.session[SESSION_GUEST_ID] = guest.pk
    request.session.modified = True


def safe_next_url(raw: str | None, default: str | None = None) -> str:
    """Aceita só paths relativos internos; senão usa o default (presentes)."""
    fallback = default or reverse('cha_presentes')
    if not raw:
        return fallback
    path = raw.strip()
    if not path.startswith('/') or path.startswith('//'):
        return fallback
    if any(path == p or path.startswith(p) for p in _ALLOWED_NEXT_PREFIXES):
        return path
    return fallback


def cha_access_required(view_func):
    """Exige sessão autorizada; senão redireciona para o convite (ou JSON 403)."""

    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if has_cha_access(request):
            return view_func(request, *args, **kwargs)
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse(
                {'ok': False, 'error': 'Acesso não autorizado.', 'code': 'unauthorized'},
                status=403,
            )
        login_url = reverse('cha_bebe')
        next_path = request.get_full_path()
        if next_path and next_path != login_url:
            login_url = f'{login_url}?{urlencode({"next": next_path})}'
        return redirect(login_url)

    return _wrapped
