from django.core.management.base import BaseCommand

from apps.cha.models import Gift

# (name, meta_quantity, order)
CATALOG = [
    ('Berço portátil', 1, 10),
    ('Kit potes para higiene', 1, 11),
    ('Carrinho e bebê conforto', 1, 12),
    ('Cesto para roupas sujas', 1, 13),
    ('Lixeira anti odor', 1, 14),
    ('Lençol para berço portátil', 3, 15),
    ('Cobertor mais grosso', 1, 16),
    ('Mantas', 3, 17),
    ('Cueiros', 10, 18),
    ('Fraldas de pano de diversos tamanhos', 20, 19),
    ('Toalha de banho grande', 1, 20),
    ('Trocador portátil', 1, 21),
    ('Sling', 1, 22),
    ('Almofada amamentação', 1, 23),
    ('Kit saquinhos maternidade', 1, 24),
    ('Ruído branco', 1, 25),
    ('Sabonete líquido', 3, 26),
    ('Colônia para bebê', 1, 27),
    ('Creme para bebê', 1, 28),
    ('Óleo para bebê', 1, 29),
    ('Lenço umedecido', 5, 30),
    ('Termômetro Infravermelho', 1, 31),
    ('Limpador nasal', 1, 32),
    ('Outros', 50, 33),
]

ESCOLHA_IMG = 'item_a_sua_escolha.png'

SLUG_BY_NAME = {
    'Berço portátil': 'berco_portatil.png',
    'Kit potes para higiene': 'kit_potes_higiene.png',
    'Carrinho e bebê conforto': 'carrinho_bebe_conforto.png',
    'Cesto para roupas sujas': ESCOLHA_IMG,
    'Lixeira anti odor': 'lixeira_anti_odor.png',
    'Lençol para berço portátil': ESCOLHA_IMG,
    'Cobertor mais grosso': ESCOLHA_IMG,
    'Mantas': ESCOLHA_IMG,
    'Cueiros': ESCOLHA_IMG,
    'Fraldas de pano de diversos tamanhos': ESCOLHA_IMG,
    'Toalha de banho grande': ESCOLHA_IMG,
    'Trocador portátil': ESCOLHA_IMG,
    'Sling': ESCOLHA_IMG,
    'Almofada amamentação': ESCOLHA_IMG,
    'Kit saquinhos maternidade': ESCOLHA_IMG,
    'Ruído branco': ESCOLHA_IMG,
    'Sabonete líquido': ESCOLHA_IMG,
    'Colônia para bebê': ESCOLHA_IMG,
    'Creme para bebê': ESCOLHA_IMG,
    'Óleo para bebê': ESCOLHA_IMG,
    'Lenço umedecido': ESCOLHA_IMG,
    'Termômetro Infravermelho': ESCOLHA_IMG,
    'Limpador nasal': ESCOLHA_IMG,
    'Outros': 'outros.png',
}


class Command(BaseCommand):
    help = 'Cadastra/atualiza o catálogo de presentes do chá (sem apagar existentes)'

    def handle(self, *args, **options):
        for name, meta, order in CATALOG:
            gift, created = Gift.objects.get_or_create(
                name=name,
                defaults={
                    'category': None,
                    'meta_quantity': meta,
                    'order': order,
                    'is_available': True,
                    'description': 'Sugestão de presente para o Joaquim.',
                },
            )
            updated = []
            if gift.meta_quantity != meta:
                gift.meta_quantity = meta
                updated.append('meta_quantity')
            if gift.order != order:
                gift.order = order
                updated.append('order')
            if gift.category_id is not None:
                gift.category = None
                updated.append('category')
            # Recalcula disponibilidade com base nas reservas
            gift.is_available = gift.available_qty() > 0
            updated.append('is_available')
            if updated:
                gift.save(update_fields=list(dict.fromkeys(updated)))
            self.stdout.write(
                f'{"+" if created else "="} {name} (meta={meta})'
            )
        n = Gift.objects.exclude(category__isnull=True).update(category=None)
        if n:
            self.stdout.write(f'Categoria removida de {n} presente(s).')
        self.stdout.write(self.style.SUCCESS(f'Catálogo ok ({len(CATALOG)} itens).'))
