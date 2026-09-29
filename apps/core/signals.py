from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.cha.models import ChaRsvp, DiaperPledge, GiftReservation, ReservationLike
from apps.core.models import TimelineEntry
from apps.core.notify import notify_interaction
from apps.core.timeline_meta import display_title
from apps.mensagens.models import Recado


@receiver(post_save, sender=Recado)
def avisar_recado(sender, instance, created, **kwargs):
    if not created:
        return
    estado = (
        'aguardando aprovação'
        if instance.status == Recado.STATUS_PENDING
        else instance.get_status_display()
    )
    notify_interaction(
        title=f'{instance.nome} deixou um recadinho ({estado})',
        detail=instance.mensagem,
        path='/recadinhos/',
    )


@receiver(post_save, sender=TimelineEntry)
def avisar_jornada(sender, instance, created, **kwargs):
    if not created or not instance.is_published:
        return
    notify_interaction(
        title='Novo momento na jornada',
        detail=display_title(instance),
        path='/timeline/',
    )


@receiver(post_save, sender=GiftReservation)
def avisar_presente(sender, instance, created, **kwargs):
    if not created or instance.cancelled_at:
        return
    presente = (instance.item_name or instance.gift.name).strip()
    notify_interaction(
        title=f'{instance.display_name} escolheu um presente',
        detail=presente,
        path='/cha/presentes/',
    )


@receiver(post_save, sender=DiaperPledge)
def avisar_fralda(sender, instance, created, **kwargs):
    if not created or instance.cancelled_at:
        return
    notify_interaction(
        title=f'{instance.display_name} escolheu fraldas',
        detail=f'{instance.size.label} × {instance.quantity}',
        path='/cha/presentes/',
    )


@receiver(post_save, sender=ChaRsvp)
def avisar_presenca(sender, instance, created, **kwargs):
    if not created:
        return
    who = (instance.name or '').strip() or 'Alguém'
    notify_interaction(
        title=f'{who} registrou presença',
        detail=instance.get_response_display(),
        path='/cha/',
    )


@receiver(post_save, sender=ReservationLike)
def avisar_curtida(sender, instance, created, **kwargs):
    if not created or instance.removed_at:
        return
    presente = (
        instance.reservation.item_name or instance.reservation.gift.name
    ).strip()
    notify_interaction(
        title=f'{instance.guest.name} curtiu um presente',
        detail=presente,
        path='/cha/presentes/',
    )
