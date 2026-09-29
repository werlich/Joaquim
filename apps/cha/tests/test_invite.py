from datetime import date, time

from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from apps.cha.access import RATE_LIMIT_MAX, SESSION_KEY, rate_limit_key
from apps.cha.models import BabyShowerEvent, ChaGuest, ChaRsvp, Gift


@override_settings(
    CACHES={'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}},
)
class InviteAccessTests(TestCase):
    def setUp(self):
        cache.clear()
        self.event = BabyShowerEvent.objects.create(
            title='Chá de Bebê do Joaquim',
            location='Casa',
            address='Rua das Flores, 10',
            event_date=date(2026, 9, 20),
            event_time=time(15, 0),
            invite_active=True,
            rsvp_active=True,
            is_active=True,
        )
        self.gift = Gift.objects.create(name='Body', order=1)
        self.client = Client()

    def test_presentes_sem_autorizacao_redireciona(self):
        res = self.client.get(reverse('cha_presentes'))
        self.assertEqual(res.status_code, 302)
        self.assertEqual(res.url, '/cha/?next=%2Fcha%2Fpresentes%2F')

    def test_timeline_sem_autorizacao_redireciona(self):
        res = self.client.get('/timeline/')
        self.assertEqual(res.status_code, 302)
        self.assertEqual(res.url, '/cha/?next=%2Ftimeline%2F')

    def test_login_redireciona_para_next(self):
        guest = ChaGuest(name='Ana', name_key='ana')
        guest.set_password('segredo')
        guest.save()
        res = self.client.post(reverse('cha_acesso'), {
            'mode': 'login',
            'name': 'Ana',
            'password': 'segredo',
            'next': '/timeline/',
        })
        self.assertEqual(res.status_code, 302)
        self.assertEqual(res.url, '/timeline/')
        self.assertTrue(self.client.session.get(SESSION_KEY))

    def test_criar_senha_libera_acesso(self):
        res = self.client.post(reverse('cha_acesso'), {
            'mode': 'register',
            'name': 'Maria Silva',
            'password': 'amor123',
            'password_confirm': 'amor123',
        })
        self.assertEqual(res.status_code, 302)
        self.assertEqual(res.url, reverse('cha_presentes'))
        self.assertTrue(self.client.session.get(SESSION_KEY))
        self.assertEqual(ChaGuest.objects.count(), 1)
        guest = ChaGuest.objects.get()
        self.assertEqual(guest.name, 'Maria Silva')
        self.assertTrue(guest.check_password('amor123'))
        page = self.client.get(reverse('cha_presentes'))
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, 'Body')

    def test_senha_divergente(self):
        res = self.client.post(reverse('cha_acesso'), {
            'mode': 'register',
            'name': 'Maria',
            'password': 'amor123',
            'password_confirm': 'outra',
        })
        self.assertEqual(res.status_code, 302)
        self.assertFalse(self.client.session.get(SESSION_KEY))
        self.assertEqual(ChaGuest.objects.count(), 0)

    def test_nome_duplicado(self):
        ChaGuest.objects.create(
            name='Maria',
            name_key='maria',
            password_hash='x',
        )
        # set real hash
        g = ChaGuest.objects.get(name_key='maria')
        g.set_password('antiga')
        g.save()

        res = self.client.post(reverse('cha_acesso'), {
            'mode': 'register',
            'name': 'MARIA',
            'password': 'nova123',
            'password_confirm': 'nova123',
        })
        self.assertEqual(res.status_code, 302)
        self.assertFalse(self.client.session.get(SESSION_KEY))
        self.assertEqual(ChaGuest.objects.count(), 1)

    def test_login_com_senha(self):
        guest = ChaGuest(name='João', name_key='joão')
        guest.set_password('segredo')
        guest.save()

        res = self.client.post(reverse('cha_acesso'), {
            'mode': 'login',
            'name': 'joão',
            'password': 'segredo',
        })
        self.assertEqual(res.status_code, 302)
        self.assertEqual(res.url, reverse('cha_presentes'))
        self.assertTrue(self.client.session.get(SESSION_KEY))

    def test_login_incorreto(self):
        guest = ChaGuest(name='João', name_key='joão')
        guest.set_password('segredo')
        guest.save()

        res = self.client.post(reverse('cha_acesso'), {
            'mode': 'login',
            'name': 'João',
            'password': 'errado',
        })
        self.assertEqual(res.status_code, 302)
        self.assertFalse(self.client.session.get(SESSION_KEY))

    def test_acesso_direto_url_privada(self):
        res = self.client.get('/cha/presentes/')
        self.assertEqual(res.status_code, 302)

    def test_rate_limiting(self):
        for _ in range(RATE_LIMIT_MAX):
            self.client.post(reverse('cha_acesso'), {
                'mode': 'login',
                'name': 'X',
                'password': 'y',
            })
        guest = ChaGuest(name='Ok', name_key='ok')
        guest.set_password('ok123')
        guest.save()
        res = self.client.post(reverse('cha_acesso'), {
            'mode': 'login',
            'name': 'Ok',
            'password': 'ok123',
        })
        self.assertEqual(res.status_code, 302)
        self.assertFalse(self.client.session.get(SESSION_KEY))
        page = self.client.get(reverse('cha_bebe'))
        self.assertContains(page, 'Muitas tentativas')

    def test_rsvp(self):
        res = self.client.post(reverse('cha_rsvp'), {
            'response': 'sim',
            'name': 'Maria',
            'companions': 2,
        })
        self.assertEqual(res.status_code, 302)
        self.assertEqual(ChaRsvp.objects.count(), 1)
        r = ChaRsvp.objects.get()
        self.assertEqual(r.name, 'Maria')
        self.assertEqual(r.response, 'sim')
        self.assertEqual(r.companions, 2)

    def test_convite_desativado(self):
        self.event.invite_active = False
        self.event.save(update_fields=['invite_active'])
        page = self.client.get(reverse('cha_bebe'))
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, 'indisponível')

    def test_csrf_protecao_acesso(self):
        c = Client(enforce_csrf_checks=True)
        res = c.post(reverse('cha_acesso'), {
            'mode': 'register',
            'name': 'Ana',
            'password': 'abc123',
            'password_confirm': 'abc123',
        })
        self.assertEqual(res.status_code, 403)

    def test_senha_nao_exposta_no_html(self):
        page = self.client.get(reverse('cha_bebe'))
        html = page.content.decode()
        self.assertIn('Criar senha', html)
        self.assertIn('Já tenho senha', html)
        self.assertNotIn('password_hash', html)

    def test_reserva_exige_acesso(self):
        res = self.client.post(
            reverse('reservar_presente', args=[self.gift.pk]),
            {'guest_name': 'Ana', 'quantity': 1},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(res.status_code, 403)


class ChaRsvpAdminFormTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser('admin', 'a@b.c', 'secret')
        self.client = Client()
        self.client.force_login(self.user)

    def test_anonimo_nao_abre_formulario(self):
        anon = Client()
        res = anon.get(reverse('admin:cha_charsvp_formulario'))
        self.assertEqual(res.status_code, 302)

    def test_botao_e_formulario_na_listagem(self):
        page = self.client.get(reverse('admin:cha_charsvp_changelist'))
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, 'Formulário de presença')
        self.assertContains(page, reverse('admin:cha_charsvp_formulario'))
        self.assertContains(page, 'Total de participantes:')

    def test_formulario_salva_confirmacao(self):
        form_url = reverse('admin:cha_charsvp_formulario')
        page = self.client.get(form_url)
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, 'Registrar nova confirmação')
        res = self.client.post(form_url, {
            'response': 'sim',
            'name': 'Tia Ana',
            'companions': 1,
        })
        self.assertRedirects(res, form_url)
        rsvp = ChaRsvp.objects.get()
        self.assertEqual(rsvp.name, 'Tia Ana')
        self.assertEqual(rsvp.response, 'sim')
        self.assertEqual(rsvp.companions, 1)
        lista = self.client.get(form_url)
        self.assertContains(lista, 'Tia Ana')
        self.assertContains(lista, 'Total de participantes: 2')
        self.assertContains(lista, 'Pessoas (sim): 2')
