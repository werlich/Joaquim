from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand

from apps.cha.management.commands.seed_gift_catalog import SLUG_BY_NAME
from apps.cha.models import DiaperSize, Gift

# Fonte versionada em static/img/presentes/
GIFT_BY_NAME = {
    'outros': 'outros.png',
}
GIFT_BY_NAME.update({k.lower(): v for k, v in SLUG_BY_NAME.items()})

DIAPER_BY_CODE = {
    'P': 'fralda_p.png',
    'M': 'fralda_m.png',
    'G': 'fralda_g.png',
}


class Command(BaseCommand):
    help = 'Aplica imagens dos presentes/fraldas a partir de static/img/presentes/'

    def handle(self, *args, **options):
        src_dir = Path(settings.BASE_DIR) / 'static' / 'img' / 'presentes'
        if not src_dir.is_dir():
            self.stderr.write(f'Diretório não encontrado: {src_dir}')
            return

        for gift in Gift.objects.all():
            key = gift.name.strip().lower()
            filename = GIFT_BY_NAME.get(key)
            if not filename:
                continue
            path = src_dir / filename
            if not path.is_file():
                self.stderr.write(f'Arquivo ausente: {path}')
                continue
            with path.open('rb') as fh:
                gift.image.save(filename, File(fh), save=True)
            self.stdout.write(f'Presente OK: {gift.name} → {filename}')

        for diaper in DiaperSize.objects.all():
            filename = DIAPER_BY_CODE.get(diaper.code.upper())
            if not filename:
                continue
            path = src_dir / filename
            if not path.is_file():
                self.stderr.write(f'Arquivo ausente: {path}')
                continue
            with path.open('rb') as fh:
                diaper.image.save(filename, File(fh), save=True)
            self.stdout.write(f'Fralda OK: {diaper.label} → {filename}')

        self.stdout.write(self.style.SUCCESS('Imagens aplicadas.'))
