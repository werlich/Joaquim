from datetime import date, datetime, time, timezone as dt_timezone

from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from apps.cha.countdown import (
    MSG_ENDED,
    MSG_FAR,
    MSG_MONTH,
    MSG_SOON,
    MSG_TODAY,
    MSG_WEEK,
    event_ends_at,
    event_starts_at,
    payload,
    remaining_parts,
)
from apps.cha.models import BabyShowerEvent
from apps.core.models import Joaquimetro


def _sp(dt: datetime) -> datetime:
    return timezone.make_aware(dt, timezone.get_current_timezone())


def _event(**kwargs):
    defaults = {
        'title': 'Chá de Bebê do Joaquim',
        'location': 'Casa',
        'event_date': date(2026, 10, 18),
        'event_time': time(12, 0),
        'is_active': True,
    }
    defaults.update(kwargs)
    return BabyShowerEvent(**defaults)


class CountdownLogicTests(SimpleTestCase):
    def test_remaining_never_negative(self):
        self.assertEqual(
            remaining_parts(-90),
            {'days': 0, 'hours': 0, 'minutes': 0, 'seconds': 0},
        )
        self.assertEqual(
            remaining_parts(90061),
            {'days': 1, 'hours': 1, 'minutes': 1, 'seconds': 1},
        )

    def test_starts_and_ends_use_django_timezone(self):
        event = _event()
        starts = event_starts_at(event)
        ends = event_ends_at(event)
        self.assertEqual(str(starts.tzinfo), 'America/Sao_Paulo')
        self.assertEqual(starts.isoformat(timespec='seconds'), '2026-10-18T12:00:00-03:00')
        self.assertEqual(ends.isoformat(timespec='seconds'), '2026-10-19T00:00:00-03:00')

    def test_phase_messages(self):
        event = _event()
        cases = [
            (datetime(2026, 9, 1, 12, 0), MSG_FAR, 'far'),
            (datetime(2026, 9, 18, 12, 0), MSG_MONTH, 'month'),
            (datetime(2026, 10, 12, 12, 0), MSG_WEEK, 'week'),
            (datetime(2026, 10, 16, 13, 0), MSG_SOON, 'soon'),
            (datetime(2026, 10, 18, 8, 0), MSG_TODAY, 'today'),
            (datetime(2026, 10, 18, 15, 0), MSG_TODAY, 'today'),
            (datetime(2026, 10, 19, 0, 0), MSG_ENDED, 'ended'),
        ]
        for naive, message, phase in cases:
            data = payload(event, now=_sp(naive))
            self.assertEqual(data['phase'], phase, naive)
            self.assertEqual(data['message'], message, naive)

    def test_today_uses_sao_paulo_calendar_not_utc(self):
        event = _event()
        # 02:00 UTC = 23:00 do dia 17 em São Paulo → ainda não é o dia do Chá.
        utc_eve = datetime(2026, 10, 18, 2, 0, tzinfo=dt_timezone.utc)
        data = payload(event, now=utc_eve)
        self.assertEqual(data['phase'], 'soon')
        # 04:00 UTC = 01:00 do dia 18 em São Paulo → é hoje.
        utc_day = datetime(2026, 10, 18, 4, 0, tzinfo=dt_timezone.utc)
        data = payload(event, now=utc_day)
        self.assertEqual(data['phase'], 'today')

    def test_after_start_units_are_zero(self):
        event = _event()
        data = payload(event, now=_sp(datetime(2026, 10, 18, 12, 30)))
        self.assertEqual(data['phase'], 'today')
        self.assertEqual(data['parts']['days'], 0)
        self.assertEqual(data['parts']['hours'], 0)
        self.assertEqual(data['parts']['seconds'], 0)


@override_settings(ALLOWED_HOSTS=['testserver', 'localhost', '127.0.0.1'])
class HomeCountdownTests(TestCase):
    def setUp(self):
        self.event = BabyShowerEvent.objects.create(
            title='Chá de Bebê do Joaquim',
            location='Rua Pedro Bagio, nº 28',
            address='Santa Gema — Colombo - PR',
            event_date=date(2026, 10, 18),
            event_time=time(12, 0),
            is_active=True,
        )

        Joaquimetro.objects.create(due_date=date(2027, 1, 13), is_active=True)

    def test_home_renders_countdown_from_database(self):
        res = self.client.get(reverse('home'))
        self.assertEqual(res.status_code, 200)
        html = res.content.decode()
        self.assertIn('id="cha-countdown"', html)
        self.assertIn('data-starts-at="2026-10-18T12:00:00-03:00"', html)
        self.assertIn('data-tz="America/Sao_Paulo"', html)
        self.assertIn('🧸 Ver convite', html)
        self.assertIn('/cha/', html)
        self.assertIn('18 de outubro de 2026', html)
        self.assertIn('cha-countdown.js', html)
        self.assertIn('Joaquímetro', html)

    def test_javascript_has_no_hardcoded_event_date(self):
        from pathlib import Path
        js = Path('static/js/cha-countdown.js').read_text(encoding='utf-8')
        self.assertNotIn('2026-10-18', js)
        self.assertNotIn('T12:00:00', js)
