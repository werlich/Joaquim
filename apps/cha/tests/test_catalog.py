from django.core.management import call_command
from django.test import TestCase

from apps.cha.management.commands.seed_gift_catalog import CATALOG, SLUG_BY_NAME
from apps.cha.models import Gift


class GiftCatalogTests(TestCase):
    def test_edredom_fica_abaixo_do_cobertor_com_imagem_de_outros(self):
        names = [name for name, _meta, _order in CATALOG]
        self.assertEqual(names.index('Edredom de bebê'), names.index('Cobertor mais grosso') + 1)
        self.assertEqual(SLUG_BY_NAME['Edredom de bebê'], SLUG_BY_NAME['Outros'])
        call_command('seed_gift_catalog', verbosity=0)
        cobertor = Gift.objects.get(name='Cobertor mais grosso')
        edredom = Gift.objects.get(name='Edredom de bebê')
        self.assertGreater(edredom.order, cobertor.order)
        self.assertEqual(edredom.meta_quantity, 1)
