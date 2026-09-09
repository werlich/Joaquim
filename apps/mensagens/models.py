from django.core.validators import MaxLengthValidator
from django.db import models


class Message(models.Model):
    ORIGIN_GIFT = 'gift'
    ORIGIN_DIAPER = 'diaper'
    ORIGIN_MANUAL = 'manual'
    ORIGIN_CHOICES = [
        (ORIGIN_GIFT, 'Presente'),
        (ORIGIN_DIAPER, 'Fralda'),
        (ORIGIN_MANUAL, 'Manual'),
    ]

    text = models.TextField('Mensagem')
    author_display = models.CharField('Autor (exibição)', max_length=120)
    origin = models.CharField(max_length=20, choices=ORIGIN_CHOICES, default=ORIGIN_MANUAL)
    is_published = models.BooleanField('Publicada', default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Mensagem'
        verbose_name_plural = 'Mensagens'

    def __str__(self):
        return f'{self.author_display}: {self.text[:40]}'


class RecadoQuerySet(models.QuerySet):
    def approved(self):
        return self.filter(status=self.model.STATUS_APPROVED)


class Recado(models.Model):
    STATUS_PENDING = 'pendente'
    STATUS_APPROVED = 'aprovado'
    STATUS_REJECTED = 'rejeitado'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pendente'),
        (STATUS_APPROVED, 'Aprovado'),
        (STATUS_REJECTED, 'Rejeitado'),
    ]

    REL_FAMILIA = 'familia'
    REL_VOVO = 'vovo'
    REL_TIO = 'tio'
    REL_PRIMO = 'primo'
    REL_AMIGO = 'amigo'
    REL_CONVIDADO = 'convidado'
    REL_OUTRO = 'outro'
    RELACAO_CHOICES = [
        (REL_FAMILIA, 'Família'),
        (REL_VOVO, 'Vovô/Vovó'),
        (REL_TIO, 'Tio/Tia'),
        (REL_PRIMO, 'Primo/Prima'),
        (REL_AMIGO, 'Amigo da família'),
        (REL_CONVIDADO, 'Convidado'),
        (REL_OUTRO, 'Outro'),
    ]
    RELACAO_ICON = {
        REL_FAMILIA: '👨‍👩‍👧',
        REL_VOVO: '👵',
        REL_TIO: '🎀',
        REL_PRIMO: '💚',
        REL_AMIGO: '💚',
        REL_CONVIDADO: '💌',
        REL_OUTRO: '💚',
    }

    nome = models.CharField('Nome', max_length=100)
    mensagem = models.TextField('Recado', validators=[MaxLengthValidator(1000)])
    email = models.EmailField('E-mail', blank=True)
    relacao = models.CharField(
        'Relação',
        max_length=50,
        choices=RELACAO_CHOICES,
        blank=True,
    )
    status = models.CharField(
        'Status',
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        db_index=True,
    )
    created_at = models.DateTimeField('Data', auto_now_add=True)

    objects = RecadoQuerySet.as_manager()

    class Meta:
        ordering = ['-created_at', '-id']
        verbose_name = 'Recadinho'
        verbose_name_plural = 'Recadinhos'

    def __str__(self):
        return f'{self.nome}: {self.mensagem[:40]}'

    @property
    def relacao_label(self) -> str:
        return self.get_relacao_display() if self.relacao else ''

    @property
    def relacao_icon(self) -> str:
        return self.RELACAO_ICON.get(self.relacao, '💚')
