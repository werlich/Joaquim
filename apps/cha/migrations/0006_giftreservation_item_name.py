from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cha', '0005_chaguest_password'),
    ]

    operations = [
        migrations.AddField(
            model_name='giftreservation',
            name='item_name',
            field=models.CharField(
                blank=True,
                help_text='Usado em Outros: o que a pessoa vai levar.',
                max_length=160,
                verbose_name='Presente escolhido',
            ),
        ),
    ]
