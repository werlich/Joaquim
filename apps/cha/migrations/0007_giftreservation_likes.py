from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cha', '0006_giftreservation_item_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='giftreservation',
            name='likes',
            field=models.PositiveIntegerField(default=0, verbose_name='Curtidas'),
        ),
    ]
