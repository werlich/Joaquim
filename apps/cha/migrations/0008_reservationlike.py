import django.db.models.deletion
from django.db import migrations, models


def zerar_curtidas_sem_autoria(apps, schema_editor):
    """Curtidas antigas eram anônimas (sessão): sem autor, não contam."""
    GiftReservation = apps.get_model('cha', 'GiftReservation')
    GiftReservation.objects.filter(likes__gt=0).update(likes=0)


class Migration(migrations.Migration):

    dependencies = [
        ('cha', '0007_giftreservation_likes'),
    ]

    operations = [
        migrations.CreateModel(
            name='ReservationLike',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Curtido em')),
                ('guest', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='gift_likes',
                    to='cha.chaguest',
                )),
                ('reservation', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='like_records',
                    to='cha.giftreservation',
                )),
            ],
            options={
                'verbose_name': 'Curtida',
                'verbose_name_plural': 'Curtidas',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddConstraint(
            model_name='reservationlike',
            constraint=models.UniqueConstraint(
                fields=('reservation', 'guest'), name='uniq_like_por_convidado'
            ),
        ),
        migrations.RunPython(zerar_curtidas_sem_autoria, migrations.RunPython.noop),
    ]
