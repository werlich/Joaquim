from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cha', '0003_gift_quantity'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='babyshowerevent',
            options={
                'verbose_name': 'Convite do Chá',
                'verbose_name_plural': 'Convite do Chá',
            },
        ),
        migrations.AddField(
            model_name='babyshowerevent',
            name='address',
            field=models.CharField(blank=True, max_length=255, verbose_name='Endereço'),
        ),
        migrations.AddField(
            model_name='babyshowerevent',
            name='invite_message',
            field=models.TextField(
                blank=True,
                default='Você é nosso convidado especial para celebrar a chegada do Joaquim 💚',
                verbose_name='Mensagem do convite',
            ),
        ),
        migrations.AddField(
            model_name='babyshowerevent',
            name='access_code_hash',
            field=models.CharField(
                blank=True,
                help_text='Nunca exibido. Defina um novo código no admin.',
                max_length=128,
                verbose_name='Hash do código de acesso',
            ),
        ),
        migrations.AddField(
            model_name='babyshowerevent',
            name='invite_active',
            field=models.BooleanField(default=True, verbose_name='Convite ativo'),
        ),
        migrations.AddField(
            model_name='babyshowerevent',
            name='rsvp_active',
            field=models.BooleanField(default=True, verbose_name='RSVP ativo'),
        ),
        migrations.AddField(
            model_name='babyshowerevent',
            name='whatsapp_text',
            field=models.TextField(
                blank=True,
                default='Você está convidado para o Chá de Bebê do Joaquim 💚',
                verbose_name='Texto do WhatsApp',
            ),
        ),
        migrations.CreateModel(
            name='ChaRsvp',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=120, verbose_name='Nome')),
                ('response', models.CharField(
                    choices=[
                        ('sim', 'Sim'),
                        ('talvez', 'Talvez'),
                        ('nao', 'Não poderei'),
                    ],
                    max_length=10,
                    verbose_name='Resposta',
                )),
                ('companions', models.PositiveIntegerField(default=0, verbose_name='Acompanhantes')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Data da confirmação')),
            ],
            options={
                'verbose_name': 'Confirmação de presença (RSVP)',
                'verbose_name_plural': 'Confirmações de presença (RSVP)',
                'ordering': ['-created_at'],
            },
        ),
    ]
