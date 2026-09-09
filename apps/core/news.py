from django.db.models import Max

from apps.core.models import TimelineEntry
from apps.mensagens.models import Recado


def latest_news():
    timeline_id = (
        TimelineEntry.objects.filter(is_published=True).aggregate(Max('id'))['id__max']
        or 0
    )
    recado_id = Recado.objects.approved().aggregate(Max('id'))['id__max'] or 0
    if not timeline_id and not recado_id:
        return {
            'revision': '',
            'timeline_id': 0,
            'recado_id': 0,
        }
    return {
        'revision': f't{timeline_id}-r{recado_id}',
        'timeline_id': timeline_id,
        'recado_id': recado_id,
    }
