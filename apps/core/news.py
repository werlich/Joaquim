from django.db.models import Max

from apps.core.models import TimelineEntry
from apps.mensagens.models import Recado


def latest_news():
    timeline_id = (
        TimelineEntry.objects.filter(is_published=True).aggregate(Max('id'))['id__max']
        or 0
    )
    recado_id = Recado.objects.approved().aggregate(Max('id'))['id__max'] or 0
    pending_count = Recado.objects.filter(status=Recado.STATUS_PENDING).count()
    if not timeline_id and not recado_id:
        revision = ''
    else:
        revision = f't{timeline_id}-r{recado_id}'
    return {
        'revision': revision,
        'timeline_id': timeline_id,
        'recado_id': recado_id,
        'pending_count': pending_count,
    }


def news_for_request(request):
    news = latest_news()
    staff = bool(getattr(request, 'user', None) and request.user.is_staff)
    if not staff:
        news = dict(news)
        news['pending_count'] = 0
    return news
