from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_timelineentry_image_3_image_4'),
    ]

    operations = [
        migrations.AddField(
            model_name='timelineentry',
            name='image_5',
            field=models.ImageField(
                blank=True,
                null=True,
                upload_to='timeline/',
                verbose_name='Imagem 5',
            ),
        ),
        migrations.AddField(
            model_name='timelineentry',
            name='image_6',
            field=models.ImageField(
                blank=True,
                null=True,
                upload_to='timeline/',
                verbose_name='Imagem 6',
            ),
        ),
    ]
