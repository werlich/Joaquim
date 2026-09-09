from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cha', '0002_diapersize_image'),
    ]

    operations = [
        migrations.AddField(
            model_name='gift',
            name='meta_quantity',
            field=models.PositiveIntegerField(
                default=1,
                help_text='1 = presente único. Maior que 1 = várias unidades com barra de progresso.',
                verbose_name='Meta (quantidade)',
            ),
        ),
        migrations.AddField(
            model_name='giftreservation',
            name='quantity',
            field=models.PositiveIntegerField(default=1, verbose_name='Quantidade'),
        ),
    ]
