from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cha', '0004_invite_rsvp'),
    ]

    operations = [
        migrations.CreateModel(
            name='ChaGuest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=120, verbose_name='Nome')),
                ('name_key', models.CharField(db_index=True, max_length=120, unique=True, verbose_name='Nome (chave)')),
                ('password_hash', models.CharField(max_length=128, verbose_name='Hash da senha')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Criado em')),
                ('last_login_at', models.DateTimeField(blank=True, null=True, verbose_name='Último acesso')),
            ],
            options={
                'verbose_name': 'Convidado (senha)',
                'verbose_name_plural': 'Convidados (senhas)',
                'ordering': ['name'],
            },
        ),
    ]
