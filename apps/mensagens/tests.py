from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from apps.mensagens.models import Recado


@override_settings(
    CACHES={'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}},
    ALLOWED_HOSTS=['testserver', 'localhost', '127.0.0.1'],
)
class RecadoPublicTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client = Client()

    def _post(self, **kwargs):
        data = {
            'nome': 'Vovó Maria',
            'mensagem': 'Joaquim, estamos esperando você com muito amor!',
            'relacao': Recado.REL_VOVO,
            'email': 'maria@example.com',
            'website': '',
        }
        data.update(kwargs)
        return self.client.post(reverse('recadinhos'), data, follow=False)

    def test_envio_valido_fica_pendente_e_invisivel(self):
        res = self._post()
        self.assertEqual(res.status_code, 302)
        recado = Recado.objects.get()
        self.assertEqual(recado.status, Recado.STATUS_PENDING)
        page = self.client.get(reverse('recadinhos'))
        html = page.content.decode()
        self.assertNotIn(recado.mensagem, html)
        self.assertNotIn('maria@example.com', html)

    def test_aprovado_aparece_sem_email(self):
        recado = Recado.objects.create(
            nome='Vovó Maria',
            mensagem='Joaquim, estamos esperando você com muito amor!',
            email='maria@example.com',
            relacao=Recado.REL_VOVO,
            status=Recado.STATUS_APPROVED,
        )
        html = self.client.get(reverse('recadinhos')).content.decode()
        self.assertIn(recado.mensagem, html)
        self.assertIn('Vovó Maria', html)
        self.assertNotIn('maria@example.com', html)
        self.assertNotIn('|safe', html)

    def test_rejeitado_nao_aparece(self):
        Recado.objects.create(
            nome='X',
            mensagem='Não deve aparecer',
            status=Recado.STATUS_REJECTED,
        )
        html = self.client.get(reverse('recadinhos')).content.decode()
        self.assertNotIn('Não deve aparecer', html)

    def test_html_e_script_nao_sao_renderizados(self):
        recado = Recado.objects.create(
            nome='Ana',
            mensagem='<script>alert(1)</script><b>oi</b>',
            status=Recado.STATUS_APPROVED,
        )
        html = self.client.get(reverse('recadinhos')).content.decode()
        self.assertIn('&lt;script&gt;alert(1)&lt;/script&gt;', html)
        self.assertNotIn('<script>alert(1)</script>', html)
        self.assertNotIn('<b>oi</b>', html)
        self.assertIn('Ana', html)

    def test_form_remove_tags_ao_enviar(self):
        self._post(mensagem='<b>Com carinho</b>')
        recado = Recado.objects.get()
        self.assertEqual(recado.mensagem, 'Com carinho')
        self.assertEqual(recado.status, Recado.STATUS_PENDING)

    def test_mensagem_muito_longa(self):
        res = self._post(mensagem='x' * 1001)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(Recado.objects.count(), 0)
        self.assertContains(res, 'no máximo 1000')

    def test_nome_obrigatorio(self):
        res = self._post(nome='   ')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(Recado.objects.count(), 0)

    def test_honeypot_nao_grava(self):
        res = self._post(website='http://spam.test')
        self.assertEqual(res.status_code, 302)
        self.assertEqual(Recado.objects.count(), 0)
        self.assertIn('enviado=1', res.url)

    def test_rate_limit(self):
        for i in range(3):
            res = self._post(nome=f'Pessoa {i}', mensagem=f'Recado número {i} com carinho')
            self.assertEqual(res.status_code, 302)
        res = self._post(nome='Pessoa extra', mensagem='Mais um recado com carinho')
        self.assertEqual(res.status_code, 302)
        self.assertEqual(Recado.objects.count(), 3)
        follow = self.client.get(reverse('recadinhos'))
        self.assertContains(follow, 'já enviou alguns recadinhos')

    def test_paginacao_12_por_pagina(self):
        for i in range(13):
            Recado.objects.create(
                nome=f'Pessoa {i}',
                mensagem=f'Mensagem aprovada número {i}',
                status=Recado.STATUS_APPROVED,
            )
        page1 = self.client.get(reverse('recadinhos'))
        self.assertContains(page1, 'Mensagem aprovada número 12')
        self.assertContains(page1, 'Ver mais recadinhos')
        page2 = self.client.get(reverse('recadinhos'), {'page': 2})
        self.assertEqual(len(page2.context['recados']), 1)
        self.assertContains(page2, 'Mensagem aprovada número 0')

    def test_home_mostra_so_3_aprovados(self):
        for i in range(4):
            Recado.objects.create(
                nome=f'Pessoa {i}',
                mensagem=f'Home recado {i}',
                status=Recado.STATUS_APPROVED,
            )
        Recado.objects.create(
            nome='Pendente',
            mensagem='Home pendente secreto',
            status=Recado.STATUS_PENDING,
        )
        html = self.client.get(reverse('home')).content.decode()
        self.assertEqual(html.count('Home recado'), 3)
        self.assertNotIn('Home pendente secreto', html)
        self.assertIn('Ver todos os recadinhos', html)
        self.assertIn('/recadinhos/', html)

    def test_visitante_nao_escolhe_status(self):
        self.client.post(reverse('recadinhos'), {
            'nome': 'Bia',
            'mensagem': 'Quero publicar agora mesmo 123',
            'status': Recado.STATUS_APPROVED,
            'website': '',
        })
        recado = Recado.objects.get()
        self.assertEqual(recado.status, Recado.STATUS_PENDING)

    def test_confirmacao_apos_envio(self):
        res = self._post()
        page = self.client.get(res.url)
        self.assertContains(page, 'Recadinho recebido')
        self.assertNotContains(page, 'aguardando moderação')


class RecadoAdminTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser('admin', 'a@b.c', 'secret')
        self.client = Client()
        self.client.force_login(self.user)
        self.pending = Recado.objects.create(
            nome='Tia Ana',
            mensagem='Bem-vindo, Joaquim!',
            status=Recado.STATUS_PENDING,
        )

    def test_acoes_aprovar_e_rejeitar(self):
        url = reverse('admin:mensagens_recado_changelist')
        self.client.post(url, {
            'action': 'aprovar',
            'index': 0,
            '_selected_action': [str(self.pending.pk)],
        })
        self.pending.refresh_from_db()
        self.assertEqual(self.pending.status, Recado.STATUS_APPROVED)

        self.client.post(url, {
            'action': 'rejeitar',
            'index': 0,
            '_selected_action': [str(self.pending.pk)],
        })
        self.pending.refresh_from_db()
        self.assertEqual(self.pending.status, Recado.STATUS_REJECTED)

        self.client.post(url, {
            'action': 'voltar_pendente',
            'index': 0,
            '_selected_action': [str(self.pending.pk)],
        })
        self.pending.refresh_from_db()
        self.assertEqual(self.pending.status, Recado.STATUS_PENDING)

    def test_listagem_mostra_pendentes(self):
        res = self.client.get(reverse('admin:mensagens_recado_changelist'))
        self.assertContains(res, 'aguardando aprovação')
        self.assertContains(res, 'Tia Ana')
