from datetime import date, time
import os

from django.core.management.base import BaseCommand

from apps.cha.models import BabyShowerEvent, DiaperSize, Gift, GiftCategory
from apps.core.models import Joaquimetro, SiteSection


class Command(BaseCommand):
    help = 'Cria seções, evento, fraldas P/M/G e presentes de exemplo'

    def handle(self, *args, **options):
        sections = [
            ('inicio', 'Início', 'home', True, 1),
            ('cha-de-bebe', 'Chá de Bebê', 'cha_bebe', True, 2),
            ('timeline', 'Timeline', 'timeline', True, 3),
            ('recadinhos', '💌 Recadinhos', 'recadinhos', True, 4),
            ('nascimento', 'Nascimento', '', False, 5),
            ('momentos', 'Momentos', '', False, 6),
            ('fotos', 'Fotos', '', False, 7),
        ]
        for slug, title, url_name, pub, order in sections:
            SiteSection.objects.update_or_create(
                slug=slug,
                defaults={
                    'title': title,
                    'url_name': url_name,
                    'is_published': pub,
                    'order': order,
                },
            )

        event_fields = {
            'title': 'Chá de Bebê do Joaquim',
            'location': 'Rua Pedro Bagio, nº 28',
            'address': 'Santa Gema — Colombo - PR',
            'event_date': date(2026, 10, 18),
            'event_time': time(12, 0),
            'info_text': (
                'Será uma alegria celebrar a chegada do Joaquim com vocês.'
            ),
            'invite_message': (
                'Você é nosso convidado especial para celebrar '
                'a chegada do Joaquim 💚'
            ),
            'invite_active': True,
            'rsvp_active': True,
        }
        event, created = BabyShowerEvent.objects.get_or_create(
            is_active=True,
            defaults=event_fields,
        )
        if not created:
            for field in (
                'location', 'address', 'event_date', 'event_time',
            ):
                setattr(event, field, event_fields[field])
            event.save(update_fields=[
                'location', 'address', 'event_date', 'event_time',
            ])
        env_code = os.environ.get('CHA_INVITE_CODE', '').strip()
        if env_code and not event.access_code_hash:
            event.set_access_code(env_code)
            event.save(update_fields=['access_code_hash'])
            self.stdout.write('Código de acesso definido via CHA_INVITE_CODE.')

        for code, label, meta, order in [
            ('P', 'FRALDA P', 6, 1),
            ('M', 'FRALDA M', 20, 2),
            ('G', 'FRALDA G', 14, 3),
        ]:
            DiaperSize.objects.update_or_create(
                code=code,
                defaults={'label': label, 'meta_packs': meta, 'order': order},
            )

        if not Gift.objects.exists():
            for i, name in enumerate([
                'Outros',
            ], start=1):
                Gift.objects.create(
                    name=name,
                    description='Sugestão de presente para o Joaquim.',
                    order=i,
                )

        Joaquimetro.objects.get_or_create(
            is_active=True,
            defaults={
                'due_date': date(2027, 1, 4),
                'birth_date': None,
            },
        )

        self.stdout.write(self.style.SUCCESS(f'Seed ok. Evento: {event}'))
