from datetime import date, datetime
from types import SimpleNamespace

from django.test import RequestFactory, SimpleTestCase, TestCase, override_settings
from django.utils import timezone

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
        self.assertIn('data-pwa-news-text', html)
        self.assertIn('Tem novidade no blog do Joaquim', html)
        self.assertIn('pwa.js?v=3', html)
        self.assertIn('recado-avisos.js', html)
        self.assertNotIn('id="staff-recado-toast"', html)

        feed = self.client.get('/novidades.json')
        self.assertEqual(feed.status_code, 200)
        self.assertEqual(feed['Cache-Control'], 'no-store')
        self.assertEqual(feed.json()['pending_count'], 0)
        self.assertEqual(feed.json()['revision'], '')

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
        self.assertNotIn('id="staff-recado-toast"', home)
        public = self.client.get('/novidades.json').json()
        self.assertEqual(public['revision'], f't{entry.id}-r{recado.id}')
        self.assertEqual(public['pending_count'], 0)

        from django.contrib.auth.models import User
        User.objects.create_superuser('admin', 'a@b.c', 'secret')
        self.client.login(username='admin', password='secret')
        staff_home = self.client.get('/').content.decode()
        self.assertIn('id="staff-recado-toast"', staff_home)
        self.assertIn('data-pending="1"', staff_home)
        staff_feed = self.client.get('/novidades.json').json()
        self.assertEqual(staff_feed['pending_count'], 1)


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
        self.assertIn('/novidades.json', body)
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
        self.assertIn('recado-avisos.js', html)
        self.assertIn('apple-mobile-web-app-capable', html)


class BlogUpdatesHomeTests(TestCase):
    def test_home_lista_interacoes_do_blog(self):
        from apps.cha.models import ChaRsvp, Gift, GiftReservation
        from apps.core.models import TimelineEntry
        from apps.mensagens.models import Recado

        TimelineEntry.objects.create(
            event_date=date(2026, 8, 18),
            body='18/08 - Morfologica de segundo trimestre.',
            is_published=True,
        )
        Recado.objects.create(
            nome='Vovó',
            mensagem='Estamos ansiosos para te conhecer!',
            status=Recado.STATUS_APPROVED,
        )
        Recado.objects.create(
            nome='Tia',
            mensagem='Ainda não.',
            status=Recado.STATUS_PENDING,
        )
        gift = Gift.objects.create(name='Mantas', meta_quantity=3, order=18)
        GiftReservation.objects.create(
            gift=gift, guest_name='Maria Silva', quantity=1,
        )
        ChaRsvp.objects.create(name='João', response='sim')

        recado = Recado.objects.get(nome='Vovó')
        recado.created_at = timezone.make_aware(
            datetime(2026, 9, 28, 22, 15),
        )
        recado.save(update_fields=['created_at'])

        html = self.client.get('/').content.decode()
        self.assertIn('Últimas atualizações', html)
        self.assertIn('Vovó deixou um recadinho', html)
        self.assertIn('28/09/2026', html)
        self.assertIn('22:15', html)
        self.assertNotIn('Tia deixou um recadinho', html)
        self.assertIn('Novo momento na jornada', html)
        self.assertIn('Morfológica 2º trimestre', html)
        self.assertIn('Maria Silva escolheu um presente', html)
        self.assertIn('João registrou presença', html)
        i_updates = html.find('Últimas atualizações')
        i_recados = html.find('Recadinhos para mim')
        self.assertGreater(i_updates, 0)
        self.assertGreater(i_recados, i_updates)

    def test_home_pagina_atualizacoes_em_10(self):
        from apps.mensagens.models import Recado

        for i in range(11):
            Recado.objects.create(
                nome=f'Pessoa {i:02d}',
                mensagem=f'Recado número {i}',
                status=Recado.STATUS_APPROVED,
            )
        home = self.client.get('/').content.decode()
        self.assertEqual(home.count('deixou um recadinho'), 10)
        self.assertIn('?atualizacoes=2#blog-updates-title', home)
        self.assertIn('Pessoa 10 deixou um recadinho', home)
        self.assertNotIn('Pessoa 00 deixou um recadinho', home)
        page2 = self.client.get('/?atualizacoes=2').content.decode()
        self.assertIn('Pessoa 00 deixou um recadinho', page2)
        self.assertEqual(page2.count('deixou um recadinho'), 1)
        self.assertIn('?atualizacoes=1#blog-updates-title', page2)


@override_settings(
    INTERACTION_NOTIFY_EMAIL='fernanda@werlich.com.br',
    SITE_URL='https://joaquim.werlich.com.br',
    DEFAULT_FROM_EMAIL='Joaquim <noreply@joaquim.werlich.com.br>',
)
class InteractionEmailTests(TestCase):
    def test_recado_envia_email(self):
        from django.core import mail

        from apps.mensagens.models import Recado

        Recado.objects.create(
            nome='Vovó',
            mensagem='Bem-vindo, Joaquim!',
            status=Recado.STATUS_PENDING,
        )
        self.assertEqual(len(mail.outbox), 1)
        msg = mail.outbox[0]
        self.assertEqual(msg.to, ['fernanda@werlich.com.br'])
        self.assertIn('Vovó deixou um recadinho', msg.subject)
        self.assertIn('Bem-vindo, Joaquim!', msg.body)
        self.assertIn('https://joaquim.werlich.com.br/recadinhos/', msg.body)

    def test_presente_e_presenca_enviam_email(self):
        from django.core import mail

        from apps.cha.models import ChaRsvp, Gift, GiftReservation

        gift = Gift.objects.create(name='Mantas', meta_quantity=3)
        GiftReservation.objects.create(gift=gift, guest_name='Maria Silva')
        ChaRsvp.objects.create(name='João', response='sim')
        assuntos = [m.subject for m in mail.outbox]
        self.assertTrue(any('Maria Silva escolheu um presente' in s for s in assuntos))
        self.assertTrue(any('João registrou presença' in s for s in assuntos))
        self.assertTrue(all(m.to == ['fernanda@werlich.com.br'] for m in mail.outbox))

    def test_formulario_publico_de_recado_dispara_email(self):
        from django.core import mail
        from django.urls import reverse

        from apps.mensagens.models import Recado

        res = self.client.post(reverse('recadinhos'), {
            'nome': 'Tia Ana',
            'mensagem': 'Estamos ansiosos!',
            'relacao': Recado.REL_TIO,
            'website': '',
        })
        self.assertEqual(res.status_code, 302)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Tia Ana deixou um recadinho', mail.outbox[0].subject)

