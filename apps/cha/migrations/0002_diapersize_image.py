from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cha', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='diapersize',
            name='image',
            field=models.ImageField(
                blank=True,
                null=True,
                upload_to='diapers/',
                verbose_name='Imagem',
            ),
        ),
    ]
