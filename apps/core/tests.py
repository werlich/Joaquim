from datetime import date
from types import SimpleNamespace

from django.test import RequestFactory, SimpleTestCase, TestCase, override_settings

from apps.core.context_processors import google_analytics
from apps.core.news import latest_news
from apps.core.timeline_meta import (
    body_if_not_duplicate,
    chapter_key,
    date_badge,
    display_body,
    display_title,
    is_featured,
    kind_for,
    moment_count_label,
    range_label,
)


def _entry(**kwargs):
    defaults = {
        'title': '',
        'body': '',
        'date_label': '',
        'event_date': date(2026, 6, 1),
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


class TimelineMetaTests(SimpleTestCase):
    def test_chapters_by_date(self):
        self.assertEqual(chapter_key(_entry(event_date=date(2011, 1, 1))), 'antes')
        self.assertEqual(
            chapter_key(_entry(event_date=date(2026, 5, 2), body='estava grávida de mim')),
            'cheguei',
        )
        self.assertEqual(
            chapter_key(_entry(event_date=date(2026, 5, 14), body='Primeira ecografia')),
            'coracao',
        )
        self.assertEqual(chapter_key(_entry(event_date=date(2026, 6, 25))), 'trimestre1')
        self.assertEqual(chapter_key(_entry(event_date=date(2026, 8, 18))), 'trimestre2')

    def test_featured_and_icons(self):
        self.assertTrue(is_featured(_entry(body='morfologica de segundo trimestre')))
        self.assertTrue(is_featured(_entry(body='descobriram que eu era um menino')))
        self.assertEqual(kind_for(_entry(body='segunda ecografia')), 'exam')
        self.assertEqual(kind_for(_entry(body='Meu irmãozinho Marley')), 'pets')
        self.assertEqual(kind_for(_entry(body='primeiro presente da vovó')), 'gift')

    def test_title_strips_date_prefix(self):
        e = _entry(body='18/08 - Morfologica de segundo trimestre. Texto longo.')
        self.assertEqual(display_title(e), 'Morfológica 2º trimestre')
        self.assertEqual(
            display_title(_entry(body='14/05 - Primeira ecografia. Eu era um grãozinho.')),
            'Primeira ecografia',
        )
        self.assertEqual(
            display_title(_entry(body='Olha a minha família ❤️')),
            'Minha família',
        )
        self.assertEqual(
            display_title(_entry(body='Jesus deu para eles meus 5 irmãozinhos: Ted, Marley')),
            'Os irmãozinhos',
        )

    def test_body_typo_and_badge(self):
        e = _entry(
            body='se conheceram na escola há quase 15 anos atrás.',
            event_date=date(2026, 5, 14),
        )
        self.assertIn('há quase 15 anos.', display_body(e))
        self.assertNotIn('atrás', display_body(e))
        self.assertEqual(date_badge(e), '14 MAI 2026')
        self.assertEqual(
            date_badge(_entry(date_label='8 semanas', event_date=date(2026, 5, 25))),
            '8 semanas',
        )

    def test_stats_labels(self):
        self.assertEqual(moment_count_label(22), '22 momentos registrados')
        self.assertEqual(moment_count_label(1), '1 momento registrado')
        label = range_label([
            _entry(event_date=date(2011, 1, 1)),
            _entry(event_date=date(2026, 5, 2)),
        ])
        self.assertEqual(label, 'Maio de 2026 → hoje')

    def test_hides_body_when_same_as_title(self):
        title = 'Olha a minha família ❤️'
        self.assertEqual(body_if_not_duplicate(title, title), '')
        self.assertEqual(body_if_not_duplicate(title, title + '.'), '')
        self.assertEqual(
            body_if_not_duplicate(
                'Mamãe e papai descobriram que eu era um menino',
                '11/06 - Mamãe e papai descobriram que eu era um menino',
            ),
            '',
        )
        longer = 'Olha a minha família ❤️ E os irmãozinhos também.'
        self.assertEqual(body_if_not_duplicate(title, longer), longer)


class TimelinePageTests(TestCase):
    def _grant_access(self):
        from apps.cha.access import SESSION_KEY
        session = self.client.session
        session[SESSION_KEY] = True
        session.save()

    def test_timeline_requires_access(self):
        response = self.client.get('/timeline/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/cha/', response['Location'])
        self.assertIn('next=', response['Location'])

    def test_empty_journey_renders_hero(self):
        self._grant_access()
        response = self.client.get('/timeline/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'A Jornada do Joaquim')
        self.assertContains(response, 'Minha história começou antes mesmo de eu nascer')
        self.assertContains(response, 'A timeline ainda está sendo escrita')

    def test_closing_appears_after_entries(self):
        from apps.core.models import TimelineEntry
        self._grant_access()
        TimelineEntry.objects.create(
            event_date=date(2026, 5, 2),
            body='A mamãe descobriu que estava grávida de mim.',
            is_published=True,
            order=1,
        )
        response = self.client.get('/timeline/')
        self.assertContains(response, 'e minha história continua')
        self.assertContains(response, 'Próximo capítulo')
        self.assertContains(response, 'momento registrado')


class JoaquimetroHomeTests(TestCase):
    def test_home_uses_calculated_progress_not_a_fixed_percent(self):
        from datetime import time

        from apps.cha.models import BabyShowerEvent
        from apps.core.models import Joaquimetro

        meter = Joaquimetro.objects.create(due_date=date(2027, 1, 4), is_active=True)
        BabyShowerEvent.objects.create(
            title='Chá de Bebê do Joaquim',
            location='Casa',
            event_date=date(2026, 10, 18),
            event_time=time(12, 0),
            is_active=True,
        )
        status = meter.status()
        html = self.client.get('/').content.decode()
        self.assertIn(f'{status["progress"]}%', html)
        self.assertIn(f'aria-valuenow="{status["progress"]}"', html)
        self.assertIn(f'--target: {status["progress"]}%', html)
        if status['progress'] != 55:
            self.assertNotIn('>55%</p>', html)
        self.assertIn('da jornada até eu conhecer vocês', html)
        self.assertIn('de 9 meses', html)
        self.assertIn('Chegada prevista', html)
        self.assertIn('data-starts-at="2026-10-18T12:00:00-03:00"', html)
        self.assertIn('id="cha-countdown"', html)
        self.assertLess(html.find('id="joaquimetro"'), html.find('id="cha-countdown"'))
        self.assertIn('joaquimetro.js', html)
        self.assertIn('cha-countdown.js', html)


class SiteNewsTests(TestCase):
    def test_empty_when_nothing_published(self):
        news = latest_news()
        self.assertEqual(news['revision'], '')
        self.assertEqual(news['timeline_id'], 0)
        self.assertEqual(news['recado_id'], 0)
        html = self.client.get('/').content.decode()
        self.assertIn('id="pwa-news-toast"', html)
        self.assertIn('data-news-revision=""', html)
        self.assertIn('Tem novidade no blog do Joaquim', html)
        self.assertIn('pwa.js?v=2', html)

    def test_token_follows_published_timeline_and_approved_recado(self):
        from datetime import date

        from apps.core.models import TimelineEntry
        from apps.mensagens.models import Recado

        draft = TimelineEntry.objects.create(
            event_date=date(2026, 5, 2),
            body='Rascunho',
            is_published=False,
        )
        pending = Recado.objects.create(
            nome='Tia',
            mensagem='Aguardando aprovação',
            status=Recado.STATUS_PENDING,
        )
        news = latest_news()
        self.assertEqual(news['revision'], '')
        self.assertNotIn(str(draft.id), news['revision'])
        self.assertNotIn(str(pending.id), news['revision'])

        entry = TimelineEntry.objects.create(
            event_date=date(2026, 6, 1),
            body='Nova entrada na jornada',
            is_published=True,
        )
        news = latest_news()
        self.assertEqual(news['revision'], f't{entry.id}-r0')
        self.assertEqual(news['timeline_id'], entry.id)

        recado = Recado.objects.create(
            nome='Vovó',
            mensagem='Bem-vindo, Joaquim!',
            status=Recado.STATUS_APPROVED,
        )
        news = latest_news()
        self.assertEqual(news['revision'], f't{entry.id}-r{recado.id}')
        home = self.client.get('/').content.decode()
        self.assertIn(f'data-news-revision="t{entry.id}-r{recado.id}"', home)
        self.assertIn(f'data-news-timeline="{entry.id}"', home)
        self.assertIn(f'data-news-recado="{recado.id}"', home)


@override_settings(
    ALLOWED_HOSTS=[
        'npcp.signau.cc',
        'www.npcp.signau.cc',
        'joaquim.werlich.com.br',
        'localhost',
        '127.0.0.1',
    ]
)
class GoogleAnalyticsContextTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def _id_for(self, host):
        request = self.factory.get('/', HTTP_HOST=host)
        return google_analytics(request)['ga_measurement_id']

    def test_npcp_uses_signau_measurement_id(self):
        self.assertEqual(self._id_for('npcp.signau.cc'), 'G-3G29SCX6ZJ')
        self.assertEqual(self._id_for('www.npcp.signau.cc'), 'G-3G29SCX6ZJ')
        self.assertEqual(self._id_for('npcp.signau.cc:443'), 'G-3G29SCX6ZJ')

    def test_other_hosts_use_default_measurement_id(self):
        self.assertEqual(self._id_for('joaquim.werlich.com.br'), 'G-90QRG4LWN0')
        self.assertEqual(self._id_for('localhost'), 'G-90QRG4LWN0')
        self.assertEqual(self._id_for('127.0.0.1:8000'), 'G-90QRG4LWN0')


class GoogleAnalyticsPageTests(TestCase):
    @override_settings(ALLOWED_HOSTS=['npcp.signau.cc', 'joaquim.werlich.com.br'])
    def test_home_embeds_gtag_for_host(self):
        npcp = self.client.get('/', HTTP_HOST='npcp.signau.cc')
        self.assertContains(npcp, 'gtag/js?id=G-3G29SCX6ZJ')
        self.assertContains(npcp, "gtag('config', 'G-3G29SCX6ZJ')")
        self.assertNotContains(npcp, 'G-90QRG4LWN0')

        werlich = self.client.get('/', HTTP_HOST='joaquim.werlich.com.br')
        self.assertContains(werlich, 'gtag/js?id=G-90QRG4LWN0')
        self.assertContains(werlich, "gtag('config', 'G-90QRG4LWN0')")
        self.assertNotContains(werlich, 'G-3G29SCX6ZJ')


class PwaTests(TestCase):
    def test_manifest_headers_and_payload(self):
        response = self.client.get('/manifest.webmanifest')
        self.assertEqual(response.status_code, 200)
        self.assertIn('application/manifest+json', response['Content-Type'])
        self.assertEqual(response['Cache-Control'], 'no-cache')
        data = response.json()
        self.assertEqual(data['name'], 'Joaquim Werlich Galvão')
        self.assertEqual(data['short_name'], 'Joaquim')
        self.assertEqual(data['start_url'], '/')
        self.assertEqual(data['scope'], '/')
        self.assertEqual(data['display'], 'standalone')
        self.assertEqual(data['theme_color'], '#7AAB97')
        self.assertEqual(data['background_color'], '#F7F6F0')
        purposes = {icon['purpose'] for icon in data['icons']}
        self.assertEqual(purposes, {'any', 'maskable'})

    def test_service_worker_scope_and_exclusions(self):
        response = self.client.get('/service-worker.js')
        self.assertEqual(response.status_code, 200)
        self.assertIn('javascript', response['Content-Type'])
        self.assertEqual(response['Service-Worker-Allowed'], '/')
        self.assertEqual(response['Cache-Control'], 'no-cache')
        body = response.content.decode()
        self.assertIn("request.method !== 'GET'", body)
        self.assertIn('/admin/', body)
        self.assertIn('/cha/acesso', body)
        self.assertIn('/reservar/', body)
        self.assertIn('joaquim-static-', body)
        self.assertIn('Never intercept POST', body)
        self.assertNotIn('cache.put(event.request) for POST', body)

    def test_offline_page_renders(self):
        response = self.client.get('/offline/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Você está offline')
        self.assertContains(response, 'Tentar novamente')
        self.assertContains(response, 'Voltar ao início')
        self.assertContains(response, 'rel="manifest"')
        html = self.client.get('/').content.decode()
        self.assertIn('/manifest.webmanifest', html)
        self.assertIn('pwa.js', html)
        self.assertIn('apple-mobile-web-app-capable', html)

