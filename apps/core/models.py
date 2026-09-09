from calendar import monthrange
from datetime import date

from django.db import models
from django.utils import timezone

# Gestação usada na barra: 9 meses no total (sem data de DUM).
PREGNANCY_MONTHS = 9


class SiteSection(models.Model):
    slug = models.SlugField(unique=True)
    title = models.CharField('Título', max_length=80)
    url_name = models.CharField(
        'Nome da URL Django',
        max_length=80,
        blank=True,
        help_text='Ex.: home, cha_bebe. Vazio = seção futura (sem link).',
    )
    is_published = models.BooleanField('Publicada', default=False)
    order = models.PositiveIntegerField('Ordem', default=0)

    class Meta:
        ordering = ['order', 'id']
        verbose_name = 'Seção do site'
        verbose_name_plural = 'Seções do site'

    def __str__(self):
        return self.title


def _add_months(d: date, months: int) -> date:
    m = d.month - 1 + months
    y = d.year + m // 12
    m = m % 12 + 1
    day = min(d.day, monthrange(y, m)[1])
    return date(y, m, day)


def _months_between(start: date, end: date) -> int:
    """Meses calendário completos de start até end (end >= start)."""
    if end < start:
        return -_months_between(end, start)
    months = (end.year - start.year) * 12 + (end.month - start.month)
    if end.day < start.day:
        months -= 1
    return months


class Joaquimetro(models.Model):
    due_date = models.DateField('Data prevista de nascimento')
    birth_date = models.DateField('Data de nascimento', null=True, blank=True)
    is_active = models.BooleanField('Ativo', default=True)

    class Meta:
        verbose_name = 'Joaquímetro'
        verbose_name_plural = 'Joaquímetro'

    def __str__(self):
        return f'Joaquímetro (previsto {self.due_date})'

    @classmethod
    def current(cls):
        return cls.objects.filter(is_active=True).order_by('-id').first()

    def pregnancy_start(self):
        return _add_months(self.due_date, -PREGNANCY_MONTHS)

    def progress_pct(self, today=None) -> int:
        """% da gestação (9 meses) já percorrida até a data prevista."""
        if today is None:
            today = timezone.localdate()
        if self.birth_date and self.birth_date <= today:
            return 100
        start = self.pregnancy_start()
        total = (self.due_date - start).days or 1
        done = (today - start).days
        pct = int(round(100 * done / total))
        return max(0, min(100, pct))

    def status(self, today=None):
        """Retorna mode/days/months/progress/message para a home."""
        if today is None:
            today = timezone.localdate()

        if self.birth_date and self.birth_date <= today:
            days = (today - self.birth_date).days
            months = _months_between(self.birth_date, today)
            if days == 0:
                message = 'Joaquim chegou hoje! 💚'
            elif months >= 1:
                unit = '1 mês' if months == 1 else f'{months} meses'
                message = f'Joaquim está conosco há {unit} 💚'
            elif days == 1:
                message = 'Joaquim está conosco há 1 dia 💚'
            else:
                message = f'Joaquim está conosco há {days} dias 💚'
            return {
                'mode': 'arrived',
                'days': days,
                'months': months,
                'months_done': PREGNANCY_MONTHS,
                'months_total': PREGNANCY_MONTHS,
                'progress': 100,
                'due_label': self.due_date.strftime('%d/%m/%Y'),
                'message': message,
            }

        days = (self.due_date - today).days
        months_left = _months_between(today, self.due_date) if days > 0 else 0
        months_done = max(0, min(PREGNANCY_MONTHS, PREGNANCY_MONTHS - months_left))

        if days > 1:
            message = f'Faltam {days} dias para a chegada prevista do Joaquim!'
        elif days == 1:
            message = 'Falta 1 dia para a chegada prevista do Joaquim!'
        elif days == 0:
            message = 'Chegou o grande dia da chegada prevista do Joaquim!'
        else:
            atrasados = abs(days)
            if atrasados == 1:
                message = 'A previsão era ontem — qualquer momento o Joaquim chega!'
            else:
                message = (
                    f'A previsão foi há {atrasados} dias — '
                    'qualquer momento o Joaquim chega!'
                )

        return {
            'mode': 'countdown',
            'days': days,
            'months': months_left,
            'months_done': months_done,
            'months_total': PREGNANCY_MONTHS,
            'progress': self.progress_pct(today),
            'due_label': self.due_date.strftime('%d/%m/%Y'),
            'message': message,
        }


class TimelineEntry(models.Model):
    event_date = models.DateField('Data')
    date_label = models.CharField(
        'Rótulo da data',
        max_length=80,
        blank=True,
        help_text='Se preenchido, aparece no lugar da data (ex.: Há quase 15 anos).',
    )
    title = models.CharField('Título', max_length=160, blank=True)
    body = models.TextField('Texto', blank=True)
    image = models.ImageField('Imagem', upload_to='timeline/', blank=True, null=True)
    image_2 = models.ImageField('Imagem 2', upload_to='timeline/', blank=True, null=True)
    image_3 = models.ImageField('Imagem 3', upload_to='timeline/', blank=True, null=True)
    image_4 = models.ImageField('Imagem 4', upload_to='timeline/', blank=True, null=True)
    image_5 = models.ImageField('Imagem 5', upload_to='timeline/', blank=True, null=True)
    image_6 = models.ImageField('Imagem 6', upload_to='timeline/', blank=True, null=True)
    order = models.PositiveIntegerField('Ordem', default=0)
    is_published = models.BooleanField('Publicada', default=True)

    class Meta:
        ordering = ['order', 'event_date', 'id']
        verbose_name = 'Entrada da Timeline'
        verbose_name_plural = 'Timeline'

    def __str__(self):
        label = self.date_label or self.event_date.strftime('%d/%m/%Y')
        heading = self.title or (self.body[:40] + '…' if self.body else 'Sem título')
        return f'{label} — {heading}'

    def display_date(self):
        return (self.date_label or '').strip() or self.event_date.strftime('%d/%m/%Y')

    def photos(self):
        return [
            img for img in (
                self.image, self.image_2, self.image_3,
                self.image_4, self.image_5, self.image_6,
            ) if img
        ]
