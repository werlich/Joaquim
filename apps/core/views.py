import json

from django.contrib.staticfiles.storage import staticfiles_storage
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.template.loader import render_to_string
from django.views.decorators.http import require_safe

from apps.cha.access import cha_access_required
from apps.cha.models import BabyShowerEvent
from apps.core.models import Joaquimetro, TimelineEntry
from apps.core.pwa import PWA_BACKGROUND_COLOR, PWA_CACHE_VERSION, PWA_THEME_COLOR
from apps.core.timeline_meta import annotate
from apps.mensagens.models import Recado


def home(request):
    event = BabyShowerEvent.current()
    joaquimetro = Joaquimetro.current()
    joaquimetro_status = joaquimetro.status() if joaquimetro else None
    return render(request, 'core/home.html', {
        'event': event,
        'joaquimetro': joaquimetro,
        'joaquimetro_status': joaquimetro_status,
        'recados_home': Recado.objects.approved()[:3],
    })


@cha_access_required
def timeline(request):
    entries = list(TimelineEntry.objects.filter(is_published=True))
    moments, chapters, count_label, range_label = annotate(entries)
    return render(request, 'core/timeline.html', {
        'entries': entries,
        'moments': moments,
        'chapters': chapters,
        'count_label': count_label,
        'range_label': range_label,
    })


def _pwa_icon(name, size, purpose):
    return {
        'src': staticfiles_storage.url(f'img/pwa/{name}'),
        'sizes': f'{size}x{size}',
        'type': 'image/png',
        'purpose': purpose,
    }


def _no_cache(response):
    response['Cache-Control'] = 'no-cache'
    return response


@require_safe
def webmanifest(request):
    payload = {
        'name': 'Joaquim Werlich Galvão',
        'short_name': 'Joaquim',
        'description': 'Minha história começou antes mesmo de eu nascer 💚',
        'start_url': '/',
        'scope': '/',
        'display': 'standalone',
        'orientation': 'portrait-primary',
        'lang': 'pt-BR',
        'dir': 'ltr',
        'theme_color': PWA_THEME_COLOR,
        'background_color': PWA_BACKGROUND_COLOR,
        'icons': [
            _pwa_icon('icon-192.png', 192, 'any'),
            _pwa_icon('icon-512.png', 512, 'any'),
            _pwa_icon('icon-maskable-192.png', 192, 'maskable'),
            _pwa_icon('icon-maskable-512.png', 512, 'maskable'),
        ],
    }
    response = JsonResponse(payload, json_dumps_params={'ensure_ascii': False})
    response['Content-Type'] = 'application/manifest+json'
    return _no_cache(response)


@require_safe
def service_worker(request):
    precache = [
        '/offline/',
        '/manifest.webmanifest',
        staticfiles_storage.url('img/pwa/icon-192.png'),
        staticfiles_storage.url('img/pwa/icon-512.png'),
        staticfiles_storage.url('img/pwa/icon-maskable-192.png'),
        staticfiles_storage.url('img/pwa/icon-maskable-512.png'),
        staticfiles_storage.url('img/pwa/apple-touch-icon.png'),
    ]
    body = render_to_string('core/service-worker.js', {
        'cache_version': PWA_CACHE_VERSION,
        'precache_urls': json.dumps(precache),
    })
    response = HttpResponse(body, content_type='application/javascript')
    response['Service-Worker-Allowed'] = '/'
    return _no_cache(response)


@require_safe
def offline(request):
    return render(request, 'core/offline.html')
