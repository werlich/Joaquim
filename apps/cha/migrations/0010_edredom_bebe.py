from django.db import migrations
from django.db.models import F


EDREDOM = 'Edredom de bebê'
COBERTOR = 'Cobertor mais grosso'


def add_edredom(apps, schema_editor):
    Gift = apps.get_model('cha', 'Gift')
    if Gift.objects.filter(name=EDREDOM).exists():
        return
    cobertor = Gift.objects.filter(name=COBERTOR).first()
    order = cobertor.order + 1 if cobertor else 17
    Gift.objects.filter(order__gte=order).update(order=F('order') + 1)
    outros = Gift.objects.filter(name='Outros').first()
    image_name = ''
    if outros and getattr(outros, 'image', None):
        image_name = outros.image.name if hasattr(outros.image, 'name') else str(outros.image)
    Gift.objects.create(
        name=EDREDOM,
        description='Sugestão de presente para o Joaquim.',
        order=order,
        is_available=True,
        meta_quantity=1,
        image=image_name,
    )


def remove_edredom(apps, schema_editor):
    Gift = apps.get_model('cha', 'Gift')
    gift = Gift.objects.filter(name=EDREDOM).first()
    if not gift:
        return
    order = gift.order
    gift.delete()
    Gift.objects.filter(order__gt=order).update(order=F('order') - 1)


class Migration(migrations.Migration):

    dependencies = [
        ('cha', '0009_reservationlike_historico'),
    ]

    operations = [
        migrations.RunPython(add_edredom, remove_edredom),
    ]
