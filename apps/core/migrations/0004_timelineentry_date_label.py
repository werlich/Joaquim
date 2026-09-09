from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_timelineentry'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='timelineentry',
            options={
                'ordering': ['order', 'event_date', 'id'],
                'verbose_name': 'Entrada da Timeline',
                'verbose_name_plural': 'Timeline',
            },
        ),
        migrations.AddField(
            model_name='timelineentry',
            name='date_label',
            field=models.CharField(
                blank=True,
                help_text='Se preenchido, aparece no lugar da data (ex.: Há quase 15 anos).',
                max_length=80,
                verbose_name='Rótulo da data',
            ),
        ),
        migrations.AlterField(
            model_name='timelineentry',
            name='title',
            field=models.CharField(blank=True, max_length=160, verbose_name='Título'),
        ),
    ]
