from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cha', '0008_reservationlike'),
    ]

    operations = [
        migrations.AddField(
            model_name='reservationlike',
            name='removed_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Descurtido em'),
        ),
        migrations.RemoveConstraint(
            model_name='reservationlike',
            name='uniq_like_por_convidado',
        ),
        migrations.AddConstraint(
            model_name='reservationlike',
            constraint=models.UniqueConstraint(
                condition=models.Q(('removed_at__isnull', True)),
                fields=('reservation', 'guest'),
                name='uniq_like_vigente_por_convidado',
            ),
        ),
    ]
