from django.test import TestCase
from django.urls import reverse

from apps.cha.access import SESSION_GUEST_ID, SESSION_KEY
from apps.cha.models import ChaGuest, DiaperPledge, DiaperSize, Gift
from apps.cha.services.reservas import reservar_fraldas, reservar_presente
from apps.mensagens.models import Message


def _logged_client():
    from django.test import Client

    guest = ChaGuest(name='Maria', name_key='maria')
    guest.set_password('senha123')
    guest.save()
    client = Client()
    session = client.session
    session[SESSION_KEY] = True
    session[SESSION_GUEST_ID] = guest.pk
    session.save()
    return client


class FraldaComentariosTests(TestCase):
    def setUp(self):
        self.size = DiaperSize.objects.create(
            code='G', label='FRALDA G', meta_packs=5, order=1
        )
        self.client = _logged_client()

    def test_comentario_publicado_aparece_na_lista(self):
        reservar_fraldas(
            self.size.pk,
            1,
            guest_name='Titia',
            message_text='Que vc venha com muita saúde Joaquim',
        )
        msg = Message.objects.get(origin=Message.ORIGIN_DIAPER)
        self.assertTrue(msg.is_published)
        page = self.client.get(reverse('cha_presentes'))
        self.assertContains(page, 'Titia')
        self.assertContains(page, 'Que vc venha com muita saúde Joaquim')

    def test_json_devolve_mensagem(self):
        res = self.client.post(
            reverse('reservar_fralda', args=[self.size.pk]),
            {
                'quantity': 2,
                'guest_name': 'Tia Ninha',
                'message': 'Ansiosa pela sua chegada',
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data['ok'])
        self.assertEqual(data['chooser'], 'Tia Ninha')
        self.assertEqual(data['quantity'], 2)
        self.assertEqual(data['message'], 'Ansiosa pela sua chegada')
        self.assertEqual(DiaperPledge.objects.count(), 1)
        self.assertTrue(Message.objects.get().is_published)


class PresenteComentariosTests(TestCase):
    def setUp(self):
        self.gift = Gift.objects.create(name='Carrinho', order=1, is_available=True)
        self.client = _logged_client()

    def test_comentario_de_presente_nasce_publicado(self):
        res = reservar_presente(
            self.gift.pk,
            guest_name='Fernanda',
            message_text='Amamos você, Joaquim',
        )
        self.assertTrue(res.message.is_published)
        page = self.client.get(reverse('cha_presentes'))
        self.assertContains(page, 'Amamos você, Joaquim')

