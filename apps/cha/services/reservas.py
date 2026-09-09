"""Regras de negócio — reservas atômicas (MariaDB/SQLite)."""
from __future__ import annotations

from django.db import transaction
from django.utils import timezone

from apps.cha.models import DiaperPledge, DiaperSize, Gift, GiftReservation
from apps.mensagens.models import Message


class ReservationError(Exception):
    """Erro de negócio na reserva."""

    def __init__(self, message: str, code: str = 'error'):
        super().__init__(message)
        self.code = code


def _display_author(*, guest_name: str, is_anonymous: bool) -> str:
    if is_anonymous or not (guest_name or '').strip():
        return 'Anônimo'
    return guest_name.strip()


def _maybe_message(*, text: str, author: str, origin: str) -> Message | None:
    text = (text or '').strip()
    if not text:
        return None
    return Message.objects.create(
        text=text,
        author_display=author,
        origin=origin,
        is_published=False,
    )


@transaction.atomic
def reservar_presente(
    gift_id: int,
    *,
    quantity: int = 1,
    guest_name: str = '',
    is_anonymous: bool = False,
    message_text: str = '',
    item_name: str = '',
) -> GiftReservation:
    if quantity < 1:
        raise ReservationError('A quantidade deve ser pelo menos 1.', 'invalid_qty')

    gift = Gift.objects.select_for_update().get(pk=gift_id)

    if gift.is_open_choice():
        quantity = 1
        if not (item_name or '').strip():
            raise ReservationError(
                'Informe o presente que você vai levar.',
                'item_required',
            )

    author = _display_author(guest_name=guest_name, is_anonymous=is_anonymous)
    if not is_anonymous and not (guest_name or '').strip():
        raise ReservationError('Informe seu nome ou marque Anônimo.', 'name_required')

    if gift.meta_quantity <= 1:
        if not gift.is_available:
            raise ReservationError('Este presente já foi escolhido.', 'already_taken')
        if GiftReservation.objects.filter(gift=gift, cancelled_at__isnull=True).exists():
            raise ReservationError('Este presente já foi escolhido.', 'already_taken')
        quantity = 1
    else:
        disponivel = gift.available_qty()
        if disponivel <= 0 or not gift.is_available:
            raise ReservationError('Meta já atingida para este presente.', 'meta_reached')
        if quantity > disponivel:
            raise ReservationError(
                f'Só há {disponivel} unidade(s) disponível(is).',
                'insufficient',
            )

    msg = _maybe_message(text=message_text, author=author, origin=Message.ORIGIN_GIFT)
    reservation = GiftReservation.objects.create(
        gift=gift,
        quantity=quantity,
        guest_name='' if is_anonymous else (guest_name or '').strip(),
        item_name=(item_name or '').strip(),
        is_anonymous=is_anonymous,
        message=msg,
    )
    gift.is_available = gift.available_qty() > 0
    gift.save(update_fields=['is_available'])
    return reservation


@transaction.atomic
def cancelar_reserva_presente(reservation_id: int) -> GiftReservation:
    reservation = (
        GiftReservation.objects.select_for_update()
        .select_related('gift')
        .get(pk=reservation_id)
    )
    if reservation.cancelled_at:
        return reservation
    gift = Gift.objects.select_for_update().get(pk=reservation.gift_id)
    reservation.cancelled_at = timezone.now()
    reservation.save(update_fields=['cancelled_at'])
    gift.is_available = gift.available_qty() > 0
    gift.save(update_fields=['is_available'])
    return reservation


@transaction.atomic
def reservar_fraldas(
    size_id: int,
    quantity: int,
    *,
    guest_name: str = '',
    is_anonymous: bool = False,
    message_text: str = '',
) -> DiaperPledge:
    if quantity < 1:
        raise ReservationError('A quantidade deve ser pelo menos 1.', 'invalid_qty')

    size = DiaperSize.objects.select_for_update().get(pk=size_id)
    disponivel = size.available_packs()
    if disponivel <= 0:
        raise ReservationError('Meta já atingida para este tamanho.', 'meta_reached')
    if quantity > disponivel:
        raise ReservationError(
            f'Só há {disponivel} pacote(s) disponível(is).',
            'insufficient',
        )

    author = _display_author(guest_name=guest_name, is_anonymous=is_anonymous)
    if not is_anonymous and not (guest_name or '').strip():
        raise ReservationError('Informe seu nome ou marque Anônimo.', 'name_required')

    msg = _maybe_message(text=message_text, author=author, origin=Message.ORIGIN_DIAPER)
    return DiaperPledge.objects.create(
        size=size,
        quantity=quantity,
        guest_name='' if is_anonymous else (guest_name or '').strip(),
        is_anonymous=is_anonymous,
        message=msg,
    )


@transaction.atomic
def cancelar_pledge_fralda(pledge_id: int) -> DiaperPledge:
    pledge = DiaperPledge.objects.select_for_update().get(pk=pledge_id)
    if not pledge.cancelled_at:
        pledge.cancelled_at = timezone.now()
        pledge.save(update_fields=['cancelled_at'])
    return pledge
