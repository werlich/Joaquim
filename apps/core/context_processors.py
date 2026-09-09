from django.conf import settings

from .models import SiteSection
from .news import latest_news


def site_nav(request):
    return {
        'nav_sections': SiteSection.objects.filter(is_published=True),
    }


def google_analytics(request):
    host = request.get_host().split(':')[0].lower()
    ids = getattr(settings, 'GA_MEASUREMENT_IDS', {})
    measurement_id = ids.get(host, getattr(settings, 'GA_MEASUREMENT_ID_DEFAULT', ''))
    return {'ga_measurement_id': measurement_id}


def site_news(request):
    return {'site_news': latest_news()}
