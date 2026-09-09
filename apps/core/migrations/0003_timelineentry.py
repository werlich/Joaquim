from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_joaquimetro'),
    ]

    operations = [
        migrations.CreateModel(
            name='TimelineEntry',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('event_date', models.DateField(verbose_name='Data')),
                ('title', models.CharField(max_length=160, verbose_name='Título')),
                ('body', models.TextField(blank=True, verbose_name='Texto')),
                ('image', models.ImageField(blank=True, null=True, upload_to='timeline/', verbose_name='Imagem')),
                ('order', models.PositiveIntegerField(default=0, verbose_name='Ordem')),
                ('is_published', models.BooleanField(default=True, verbose_name='Publicada')),
            ],
            options={
                'verbose_name': 'Entrada da Timeline',
                'verbose_name_plural': 'Timeline',
                'ordering': ['event_date', 'order', 'id'],
            },
        ),
    ]
