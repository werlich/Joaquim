from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_timelineentry_date_label'),
    ]

    operations = [
        migrations.AddField(
            model_name='timelineentry',
            name='image_2',
            field=models.ImageField(
                blank=True,
                null=True,
                upload_to='timeline/',
                verbose_name='Imagem 2',
            ),
        ),
    ]
