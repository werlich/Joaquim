from django.test import Client, TestCase
from django.urls import reverse

from apps.cha.access import SESSION_GUEST_ID, SESSION_KEY
from apps.cha.models import ChaGuest, Gift, GiftReservation, ReservationLike


def _guest(name, password='senha123'):
    guest = ChaGuest(name=name, name_key=ChaGuest.name_to_key(name))
    guest.set_password(password)
    guest.save()
    return guest


def _logged_client(guest):
    client = Client()
    session = client.session
    session[SESSION_KEY] = True
    session[SESSION_GUEST_ID] = guest.pk
    session.save()
    return client


class CurtirEscolhaTests(TestCase):
    def setUp(self):
        self.gift = Gift.objects.create(name='Body', order=1, is_available=False)
        self.res = GiftReservation.objects.create(gift=self.gift, guest_name='Ana')
        self.url = reverse('curtir_escolha', args=[self.res.pk])
        self.guest = _guest('Maria Silva')
        self.client = _logged_client(self.guest)

    def test_curtida_registra_autor(self):
        res = self.client.post(self.url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(
            res.json(),
            {'ok': True, 'liked': True, 'likes': 1, 'likers': 'Maria Silva'},
        )
        like = ReservationLike.objects.get()
        self.assertEqual(like.guest, self.guest)
        self.assertEqual(like.reservation, self.res)

    def test_descurtir_guarda_historico(self):
        self.client.post(self.url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        res = self.client.post(self.url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(
            res.json(), {'ok': True, 'liked': False, 'likes': 0, 'likers': ''}
        )
        like = ReservationLike.objects.get()
        self.assertIsNotNone(like.removed_at)
        self.assertFalse(like.is_current)

    def test_recurtir_apos_descurtir_mantem_as_duas_linhas(self):
        for _ in range(3):  # curte, descurte, curte
            self.client.post(self.url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(ReservationLike.objects.count(), 2)
        self.assertEqual(
            ReservationLike.objects.filter(removed_at__isnull=True).count(), 1
        )
        self.res.refresh_from_db()
        self.assertEqual(self.res.likes, 1)

    def test_uma_curtida_por_convidado(self):
        self.client.post(self.url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        outra_sessao = _logged_client(self.guest)
        outra_sessao.post(self.url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.res.refresh_from_db()
        self.assertEqual(self.res.likes, 0)
        self.assertEqual(
            ReservationLike.objects.filter(removed_at__isnull=True).count(), 0
        )

    def test_convidados_diferentes_somam(self):
        joao = _guest('João')
        self.client.post(self.url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        _logged_client(joao).post(self.url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.res.refresh_from_db()
        self.assertEqual(self.res.likes, 2)
        self.assertEqual(
            sorted(ReservationLike.objects.values_list('guest__name', flat=True)),
            ['João', 'Maria Silva'],
        )

    def test_curtida_removida_nao_conta_na_pagina(self):
        self.client.post(self.url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.client.post(self.url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        page = self.client.get(reverse('cha_presentes'))
        self.assertNotContains(page, 'is-liked')
        self.assertNotContains(page, 'Curtiram: Maria Silva')

    def test_relatorio_pdf(self):
        import os
        import tempfile

        from django.core.management import call_command

        self.client.post(self.url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.client.post(self.url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        _logged_client(_guest('João')).post(
            self.url, HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        destino = os.path.join(tempfile.mkdtemp(), 'curtidas.pdf')
        call_command('relatorio_curtidas', out=destino)
        self.assertTrue(os.path.getsize(destino) > 1000)

    def test_curtida_persiste_para_o_mesmo_login(self):
        self.client.post(self.url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        nova_sessao = _logged_client(self.guest)
        page = nova_sessao.get(reverse('cha_presentes'))
        self.assertContains(page, 'chooser-like js-like is-liked')
        self.assertContains(page, 'Curtiram: Maria Silva')

    def test_botao_aparece_na_lista(self):
        page = self.client.get(reverse('cha_presentes'))
        self.assertContains(page, 'chooser-like js-like')
        self.assertContains(page, self.url)

    def test_sessao_sem_login_nao_curte(self):
        sem_login = Client()
        session = sem_login.session
        session[SESSION_KEY] = True
        session.save()
        res = sem_login.post(self.url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(res.status_code, 403)
        self.assertEqual(res.json()['code'], 'login_required')
        self.assertEqual(ReservationLike.objects.count(), 0)

    def test_sessao_sem_login_ve_botao_bloqueado(self):
        sem_login = Client()
        session = sem_login.session
        session[SESSION_KEY] = True
        session.save()
        page = sem_login.get(reverse('cha_presentes'))
        self.assertContains(page, 'chooser-like is-locked')
        self.assertNotContains(page, 'chooser-like js-like')

    def test_exige_acesso(self):
        anonimo = Client()
        res = anonimo.post(self.url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(res.status_code, 403)

    def test_reserva_cancelada_nao_curte(self):
        from django.utils import timezone

        self.res.cancelled_at = timezone.now()
        self.res.save(update_fields=['cancelled_at'])
        res = self.client.post(self.url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(res.status_code, 404)
