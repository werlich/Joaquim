from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_timelineentry_image_2'),
    ]

    operations = [
        migrations.AddField(
            model_name='timelineentry',
            name='image_3',
            field=models.ImageField(
                blank=True,
                null=True,
                upload_to='timeline/',
                verbose_name='Imagem 3',
            ),
        ),
        migrations.AddField(
            model_name='timelineentry',
            name='image_4',
            field=models.ImageField(
                blank=True,
                null=True,
                upload_to='timeline/',
                verbose_name='Imagem 4',
            ),
        ),
    ]
