from urllib.parse import quote_plus

from django.db import models
from django.db.models import Sum, Q


class BabyShowerEvent(models.Model):
    title = models.CharField('Título', max_length=120, default='Chá de Bebê')
    location = models.CharField('Local', max_length=255)
    address = models.CharField('Endereço', max_length=255, blank=True)
    event_date = models.DateField('Data')
    event_time = models.TimeField('Horário')
    info_text = models.TextField('Texto informativo', blank=True)
    invite_message = models.TextField(
        'Mensagem do convite',
        blank=True,
        default='Você é nosso convidado especial para celebrar a chegada do Joaquim 💚',
    )
    access_code_hash = models.CharField(
        'Hash do código de acesso',
        max_length=128,
        blank=True,
        help_text='Nunca exibido. Defina um novo código no admin.',
    )
    invite_active = models.BooleanField('Convite ativo', default=True)
    rsvp_active = models.BooleanField('RSVP ativo', default=True)
    whatsapp_text = models.TextField(
        'Texto do WhatsApp',
        blank=True,
        default='Você está convidado para o Chá de Bebê do Joaquim 💚',
    )
    is_active = models.BooleanField('Ativo', default=True)

    class Meta:
        verbose_name = 'Convite do Chá'
        verbose_name_plural = 'Convite do Chá'

    def __str__(self):
        return self.title

    @classmethod
    def current(cls):
        return cls.objects.filter(is_active=True).order_by('-id').first()

    def set_access_code(self, raw_code: str) -> None:
        from django.contrib.auth.hashers import make_password
        code = (raw_code or '').strip()
        if not code:
            return
        self.access_code_hash = make_password(code)

    def check_access_code(self, raw_code: str) -> bool:
        from django.contrib.auth.hashers import check_password
        if not self.access_code_hash or not (raw_code or '').strip():
            return False
        return check_password(raw_code.strip(), self.access_code_hash)

    @property
    def time_label(self) -> str:
        if not self.event_time:
            return ''
        return f'a partir das {self.event_time.strftime("%H:%M")}'

    def starts_at(self):
        from .countdown import event_starts_at
        return event_starts_at(self)

    def countdown(self, now=None) -> dict:
        from .countdown import payload
        return payload(self, now=now)

    def maps_query(self) -> str:
        raw = ', '.join(
            p.strip() for p in (self.location, self.address) if p and p.strip()
        )
        if not raw:
            return ''
        raw = (
            raw.replace('n°', '')
            .replace('nº', '')
            .replace('—', ',')
            .replace('–', ',')
            .replace(' - ', ', ')
        )
        parts = []
        for chunk in raw.split(','):
            chunk = ' '.join(chunk.split())
            if chunk:
                parts.append(chunk)
        return ', '.join(parts)

    def maps_embed_url(self) -> str:
        query = self.maps_query()
        if not query:
            return ''
        return (
            'https://maps.google.com/maps?q='
            f'{quote_plus(query)}&output=embed&hl=pt-BR'
        )

    def maps_link_url(self) -> str:
        query = self.maps_query()
        if not query:
            return ''
        return (
            'https://www.google.com/maps/search/?api=1&query='
            f'{quote_plus(query)}'
        )


class ChaGuest(models.Model):
    """Convidado que cria senha própria para acessar o chá."""
    name = models.CharField('Nome', max_length=120)
    name_key = models.CharField('Nome (chave)', max_length=120, unique=True, db_index=True)
    password_hash = models.CharField('Hash da senha', max_length=128)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    last_login_at = models.DateTimeField('Último acesso', null=True, blank=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Convidado (senha)'
        verbose_name_plural = 'Convidados (senhas)'

    def __str__(self):
        return self.name

    @staticmethod
    def normalize_name(raw: str) -> str:
        return ' '.join((raw or '').strip().split())

    @classmethod
    def name_to_key(cls, raw: str) -> str:
        return cls.normalize_name(raw).casefold()

    def set_password(self, raw_password: str) -> None:
        from django.contrib.auth.hashers import make_password
        self.password_hash = make_password(raw_password)

    def check_password(self, raw_password: str) -> bool:
        from django.contrib.auth.hashers import check_password
        if not self.password_hash or not raw_password:
            return False
        return check_password(raw_password, self.password_hash)

    @classmethod
    def find_by_name(cls, raw_name: str):
        key = cls.name_to_key(raw_name)
        if not key:
            return None
        return cls.objects.filter(name_key=key).first()


class ChaRsvp(models.Model):
    RESPONSE_SIM = 'sim'
    RESPONSE_TALVEZ = 'talvez'
    RESPONSE_NAO = 'nao'
    RESPONSE_CHOICES = [
        (RESPONSE_SIM, 'Sim'),
        (RESPONSE_TALVEZ, 'Talvez'),
        (RESPONSE_NAO, 'Não poderei'),
    ]

    name = models.CharField('Nome', max_length=120, blank=True)
    response = models.CharField('Resposta', max_length=10, choices=RESPONSE_CHOICES)
    companions = models.PositiveIntegerField('Acompanhantes', default=0)
    created_at = models.DateTimeField('Data da confirmação', auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Confirmação de presença (RSVP)'
        verbose_name_plural = 'Confirmações de presença (RSVP)'

    def __str__(self):
        who = self.name.strip() or 'Anônimo'
        return f'{who} — {self.get_response_display()}'


class GiftCategory(models.Model):
    name = models.CharField('Nome', max_length=80)
    order = models.PositiveIntegerField('Ordem', default=0)

    class Meta:
        ordering = ['order', 'id']
        verbose_name = 'Categoria de presente'
        verbose_name_plural = 'Categorias de presentes'

    def __str__(self):
        return self.name


class Gift(models.Model):
    name = models.CharField('Nome', max_length=160)
    description = models.TextField('Descrição', blank=True)
    category = models.ForeignKey(
        GiftCategory, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='gifts', verbose_name='Categoria',
    )
    image = models.ImageField('Imagem', upload_to='gifts/', blank=True, null=True)
    order = models.PositiveIntegerField('Ordem', default=0)
    is_available = models.BooleanField('Disponível', default=True)
    meta_quantity = models.PositiveIntegerField(
        'Meta (quantidade)',
        default=1,
        help_text='1 = presente único. Maior que 1 = várias unidades com barra de progresso.',
    )

    class Meta:
        ordering = ['order', 'id']
        verbose_name = 'Presente'
        verbose_name_plural = 'Presentes'

    def __str__(self):
        return self.name

    def is_qty_gift(self):
        return self.meta_quantity > 1

    def is_open_choice(self):
        return self.name.strip().casefold() == 'outros'

    def active_reservation(self):
        return self.reservations.filter(cancelled_at__isnull=True).order_by('-id').first()

    def active_reservations(self):
        return self.reservations.filter(cancelled_at__isnull=True).order_by('created_at', 'id')

    def chosen_qty(self):
        total = self.reservations.filter(cancelled_at__isnull=True).aggregate(
            s=Sum('quantity')
        )['s']
        return int(total or 0)

    def available_qty(self):
        return max(0, self.meta_quantity - self.chosen_qty())

    def meta_reached(self):
        return self.available_qty() <= 0 and self.meta_quantity > 0

    def progress_pct(self):
        if self.meta_quantity <= 0:
            return 0
        pct = int(round(100 * self.chosen_qty() / self.meta_quantity))
        return max(0, min(100, pct))


class GiftReservation(models.Model):
    gift = models.ForeignKey(Gift, on_delete=models.CASCADE, related_name='reservations')
    quantity = models.PositiveIntegerField('Quantidade', default=1)
    guest_name = models.CharField('Nome do convidado', max_length=120, blank=True)
    item_name = models.CharField(
        'Presente escolhido',
        max_length=160,
        blank=True,
        help_text='Usado em Outros: o que a pessoa vai levar.',
    )
    is_anonymous = models.BooleanField('Anônimo', default=False)
    message = models.ForeignKey(
        'mensagens.Message', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='gift_reservations',
    )
    likes = models.PositiveIntegerField('Curtidas', default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Reserva de presente'
        verbose_name_plural = 'Reservas de presentes'

    def __str__(self):
        who = 'Anônimo' if self.is_anonymous else (self.guest_name or '—')
        status = 'cancelada' if self.cancelled_at else 'ativa'
        qty = f' x{self.quantity}' if self.quantity > 1 else ''
        return f'{self.gift.name}{qty} — {who} ({status})'

    @property
    def display_name(self):
        if self.is_anonymous or not self.guest_name.strip():
            return 'Anônimo'
        return self.guest_name.strip()

    @property
    def choice_label(self):
        name = self.display_name
        item = (self.item_name or '').strip()
        if item:
            return f'{name} — {item}'
        return name

    @property
    def likers_label(self):
        """Nomes de quem curtiu — a curtida é sempre de um convidado com senha."""
        nomes = (
            lk.guest.name for lk in self.like_records.all() if lk.removed_at is None
        )
        return ', '.join(dict.fromkeys(nomes))


class ReservationLike(models.Model):
    """Curtida rastreável: sempre ligada ao convidado que tem login e senha.

    Descurtir não apaga a linha: grava `removed_at`, preservando o histórico.
    """
    reservation = models.ForeignKey(
        GiftReservation, on_delete=models.CASCADE, related_name='like_records'
    )
    guest = models.ForeignKey(
        ChaGuest, on_delete=models.CASCADE, related_name='gift_likes'
    )
    created_at = models.DateTimeField('Curtido em', auto_now_add=True)
    removed_at = models.DateTimeField('Descurtido em', null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['reservation', 'guest'],
                condition=models.Q(removed_at__isnull=True),
                name='uniq_like_vigente_por_convidado',
            ),
        ]
        verbose_name = 'Curtida'
        verbose_name_plural = 'Curtidas'

    def __str__(self):
        verbo = 'curtiu' if self.is_current else 'descurtiu'
        return f'{self.guest.name} {verbo} {self.reservation.display_name}'

    @property
    def is_current(self) -> bool:
        return self.removed_at is None


class DiaperSize(models.Model):
    code = models.CharField('Código', max_length=10, unique=True)
    label = models.CharField('Rótulo', max_length=40)
    meta_packs = models.PositiveIntegerField('Meta (pacotes)', default=0)
    order = models.PositiveIntegerField('Ordem', default=0)
    image = models.ImageField('Imagem', upload_to='diapers/', blank=True, null=True)

    class Meta:
        ordering = ['order', 'id']
        verbose_name = 'Tamanho de fralda'
        verbose_name_plural = 'Tamanhos de fralda'

    def __str__(self):
        return self.label

    def chosen_packs(self):
        total = self.pledges.filter(cancelled_at__isnull=True).aggregate(
            s=Sum('quantity')
        )['s']
        return int(total or 0)

    def available_packs(self):
        return max(0, self.meta_packs - self.chosen_packs())

    def meta_reached(self):
        return self.available_packs() <= 0 and self.meta_packs > 0

    def progress_pct(self):
        if self.meta_packs <= 0:
            return 0
        pct = int(round(100 * self.chosen_packs() / self.meta_packs))
        return max(0, min(100, pct))


class DiaperPledge(models.Model):
    size = models.ForeignKey(DiaperSize, on_delete=models.CASCADE, related_name='pledges')
    quantity = models.PositiveIntegerField('Quantidade (pacotes)')
    guest_name = models.CharField('Nome do convidado', max_length=120, blank=True)
    is_anonymous = models.BooleanField('Anônimo', default=False)
    message = models.ForeignKey(
        'mensagens.Message', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='diaper_pledges',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Escolha de fraldas'
        verbose_name_plural = 'Escolhas de fraldas'

    def __str__(self):
        who = 'Anônimo' if self.is_anonymous else (self.guest_name or '—')
        return f'{self.size.code} x{self.quantity} — {who}'

    @property
    def display_name(self):
        if self.is_anonymous or not self.guest_name.strip():
            return 'Anônimo'
        return self.guest_name.strip()


class GalleryPhoto(models.Model):
    event = models.ForeignKey(
        BabyShowerEvent, on_delete=models.CASCADE, related_name='photos',
        null=True, blank=True,
    )
    image = models.ImageField('Foto', upload_to='gallery/')
    caption = models.CharField('Legenda', max_length=200, blank=True)
    order = models.PositiveIntegerField('Ordem', default=0)
    is_published = models.BooleanField('Publicada', default=True)

    class Meta:
        ordering = ['order', 'id']
        verbose_name = 'Foto da galeria'
        verbose_name_plural = 'Fotos da galeria'

    def __str__(self):
        return self.caption or f'Foto #{self.pk}'
