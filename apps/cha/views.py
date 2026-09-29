from django.contrib import messages
from django.db import IntegrityError, models, transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from .access import (
    SESSION_GUEST_ID,
    cha_access_required,
    clear_failed_attempts,
    grant_cha_access,
    has_cha_access,
    is_rate_limited,
    register_failed_attempt,
    safe_next_url,
)
from .forms import ChaLoginForm, ChaRegisterForm, ChaRsvpForm, DiaperPledgeForm, GiftReservationForm
from .models import (
    BabyShowerEvent,
    ChaGuest,
    ChaRsvp,
    DiaperPledge,
    DiaperSize,
    Gift,
    GiftReservation,
    ReservationLike,
)
from .services.reservas import ReservationError, reservar_fraldas, reservar_presente


def _gift_cards():
    gifts = (
        Gift.objects.select_related('category')
        .prefetch_related(
            models.Prefetch(
                'reservations',
                queryset=GiftReservation.objects.filter(cancelled_at__isnull=True)
                .select_related('message')
                .prefetch_related(
                    models.Prefetch(
                        'like_records',
                        queryset=ReservationLike.objects.filter(
                            removed_at__isnull=True
                        )
                        .select_related('guest')
                        .order_by('created_at', 'id'),
                    )
                )
                .order_by('created_at', 'id'),
            )
        )
        .all()
    )
    cards = []
    for g in gifts:
        choosers = list(g.reservations.all())
        qty = g.is_qty_gift()
        open_choice = g.is_open_choice()
        res = choosers[-1] if choosers else None
        cards.append({
            'gift': g,
            'reservation': res,
            'taken': (not g.is_available) and not qty,
            'qty_mode': qty,
            'open_choice': open_choice,
            'choosers': choosers if qty or open_choice else [],
            'meta_reached': g.meta_reached() if qty else (not g.is_available),
        })
    return cards


def _diapers():
    return list(
        DiaperSize.objects.prefetch_related(
            models.Prefetch(
                'pledges',
                queryset=DiaperPledge.objects.filter(cancelled_at__isnull=True)
                .select_related('message')
                .order_by('created_at', 'id'),
                to_attr='choosers',
            )
        )
    )


def _current_guest(request):
    """Convidado autenticado por nome + senha (None em sessão antiga/sem login)."""
    guest_id = request.session.get(SESSION_GUEST_ID)
    if not guest_id:
        return None
    return ChaGuest.objects.filter(pk=guest_id).first()


def _liked_ids(guest) -> list[int]:
    if guest is None:
        return []
    return list(
        ReservationLike.objects.filter(
            guest=guest, removed_at__isnull=True
        ).values_list('reservation_id', flat=True)
    )


def cha_bebe(request):
    """Convite digital público."""
    event = BabyShowerEvent.current()
    if event and not event.invite_active:
        return render(request, 'cha/convite_off.html', {'event': event})

    next_url = safe_next_url(request.GET.get('next'))
    return render(request, 'cha/convite.html', {
        'event': event,
        'already_authorized': has_cha_access(request),
        'rate_limited': is_rate_limited(request),
        'next_url': next_url,
    })


@require_POST
def cha_acesso(request):
    event = BabyShowerEvent.current()
    if not event or not event.invite_active:
        messages.error(request, 'O convite não está disponível no momento.')
        return redirect('cha_bebe')

    if is_rate_limited(request):
        messages.error(
            request,
            'Muitas tentativas. Aguarde alguns minutos e tente novamente.',
        )
        return redirect('cha_bebe')

    mode = (request.POST.get('mode') or 'register').strip().lower()
    if mode == 'login':
        return _cha_login(request)
    return _cha_register(request)


def _cha_register(request):
    form = ChaRegisterForm(request.POST)
    if not form.is_valid():
        err = next(iter(form.errors.values()), None)
        messages.error(
            request,
            err[0] if err else 'Preencha nome e senha para criar seu acesso.',
        )
        return redirect('cha_bebe')

    name = form.cleaned_data['name']
    name_key = ChaGuest.name_to_key(name)
    if ChaGuest.objects.filter(name_key=name_key).exists():
        messages.error(
            request,
            'Esse nome já tem senha. Use “Já tenho senha” para entrar.',
        )
        return redirect('cha_bebe')

    guest = ChaGuest(name=name, name_key=name_key, last_login_at=timezone.now())
    guest.set_password(form.cleaned_data['password'])
    try:
        guest.save()
    except IntegrityError:
        messages.error(
            request,
            'Esse nome já tem senha. Use “Já tenho senha” para entrar.',
        )
        return redirect('cha_bebe')

    clear_failed_attempts(request)
    grant_cha_access(request, guest=guest)
    messages.success(request, f'Bem-vindo(a), {guest.name}! Guarde sua senha para voltar.')
    return redirect(safe_next_url(request.POST.get('next')))


def _cha_login(request):
    form = ChaLoginForm(request.POST)
    if not form.is_valid():
        messages.error(request, 'Informe nome e senha.')
        return redirect('cha_bebe')

    guest = ChaGuest.find_by_name(form.cleaned_data['name'])
    if guest and guest.check_password(form.cleaned_data['password']):
        clear_failed_attempts(request)
        guest.last_login_at = timezone.now()
        guest.save(update_fields=['last_login_at'])
        grant_cha_access(request, guest=guest)
        return redirect(safe_next_url(request.POST.get('next')))

    register_failed_attempt(request)
    if is_rate_limited(request):
        messages.error(
            request,
            'Muitas tentativas. Aguarde alguns minutos e tente novamente.',
        )
    else:
        messages.error(request, 'Nome ou senha incorretos. Tente novamente.')
    return redirect('cha_bebe')


@cha_access_required
def cha_presentes(request):
    event = BabyShowerEvent.current()
    guest = _current_guest(request)
    return render(request, 'cha/presentes.html', {
        'event': event,
        'gift_cards': _gift_cards(),
        'diapers': _diapers(),
        'liked_ids': _liked_ids(guest),
        'can_like': guest is not None,
    })


@require_POST
def cha_rsvp(request):
    event = BabyShowerEvent.current()
    if not event or not event.rsvp_active:
        messages.error(request, 'Confirmação de presença indisponível.')
        return redirect('cha_bebe')

    form = ChaRsvpForm(request.POST)
    if not form.is_valid():
        messages.error(request, 'Não foi possível salvar sua resposta. Verifique os campos.')
        return redirect('cha_bebe')

    ChaRsvp.objects.create(
        name=(form.cleaned_data.get('name') or '').strip(),
        response=form.cleaned_data['response'],
        companions=form.cleaned_data.get('companions') or 0,
    )
    messages.success(request, 'Obrigado! Sua resposta foi registrada.')
    return redirect('cha_bebe')


def cha_legado_redirect(request):
    return redirect('cha_bebe', permanent=True)


@require_POST
@cha_access_required
def reservar_presente_view(request, gift_id):
    gift = get_object_or_404(Gift, pk=gift_id)
    form = GiftReservationForm(request.POST)
    if not form.is_valid():
        return JsonResponse({'ok': False, 'errors': form.errors}, status=400)
    try:
        res = reservar_presente(
            gift.pk,
            quantity=form.cleaned_data.get('quantity') or 1,
            guest_name=form.cleaned_data.get('guest_name') or '',
            is_anonymous=bool(form.cleaned_data.get('is_anonymous')),
            message_text=form.cleaned_data.get('message') or '',
            item_name=form.cleaned_data.get('item_name') or '',
        )
    except ReservationError as exc:
        return JsonResponse({'ok': False, 'error': str(exc), 'code': exc.code}, status=409)
    except Gift.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'Presente não encontrado.'}, status=404)
    gift.refresh_from_db()
    note = (res.message.text if res.message_id and res.message else '') or ''
    return JsonResponse({
        'ok': True,
        'reservation_id': res.pk,
        'likes': res.likes,
        'like_url': reverse('curtir_escolha', args=[res.pk]),
        'gift_id': gift.pk,
        'qty_mode': gift.is_qty_gift(),
        'chosen': gift.chosen_qty(),
        'available': gift.available_qty(),
        'meta': gift.meta_quantity,
        'progress': gift.progress_pct(),
        'meta_reached': gift.meta_reached(),
        'display': f'Já escolhido — {res.display_name}',
        'guest': res.display_name,
        'chooser': res.choice_label,
        'message': note,
        'open_choice': gift.is_open_choice(),
    })


@require_POST
@cha_access_required
def reservar_fralda_view(request, size_id):
    size = get_object_or_404(DiaperSize, pk=size_id)
    form = DiaperPledgeForm(request.POST)
    if not form.is_valid():
        return JsonResponse({'ok': False, 'errors': form.errors}, status=400)
    try:
        pledge = reservar_fraldas(
            size.pk,
            form.cleaned_data['quantity'],
            guest_name=form.cleaned_data.get('guest_name') or '',
            is_anonymous=bool(form.cleaned_data.get('is_anonymous')),
            message_text=form.cleaned_data.get('message') or '',
        )
    except ReservationError as exc:
        return JsonResponse({'ok': False, 'error': str(exc), 'code': exc.code}, status=409)
    size.refresh_from_db()
    return JsonResponse({
        'ok': True,
        'size_id': size.pk,
        'chosen': size.chosen_packs(),
        'available': size.available_packs(),
        'meta': size.meta_packs,
        'progress': size.progress_pct(),
        'meta_reached': size.meta_reached(),
        'guest': pledge.display_name,
        'chooser': pledge.display_name,
        'quantity': pledge.quantity,
        'message': (pledge.message.text if pledge.message else ''),
    })


@require_POST
@cha_access_required
def curtir_escolha_view(request, reservation_id):
    """Curte/descurte uma escolha; a curtida fica registrada no nome do convidado."""
    guest = _current_guest(request)
    if guest is None:
        return JsonResponse(
            {
                'ok': False,
                'error': 'Entre com seu nome e senha para curtir.',
                'code': 'login_required',
            },
            status=403,
        )
    # O MariaDB ignora unique com condição, então a linha da reserva é travada
    # para serializar cliques simultâneos do mesmo convidado.
    with transaction.atomic():
        res = get_object_or_404(
            GiftReservation.objects.select_for_update(),
            pk=reservation_id,
            cancelled_at__isnull=True,
        )
        vigentes = ReservationLike.objects.filter(
            reservation=res, guest=guest, removed_at__isnull=True
        )
        if vigentes.exists():
            # Descurtir guarda a data: a linha continua no histórico.
            vigentes.update(removed_at=timezone.now())
            liked = False
        else:
            ReservationLike.objects.create(reservation=res, guest=guest)
            liked = True
        names = list(
            dict.fromkeys(
                ReservationLike.objects.filter(
                    reservation=res, removed_at__isnull=True
                )
                .order_by('created_at', 'id')
                .values_list('guest__name', flat=True)
            )
        )
        GiftReservation.objects.filter(pk=res.pk).update(likes=len(names))
    return JsonResponse({
        'ok': True,
        'liked': liked,
        'likes': len(names),
        'likers': ', '.join(names),
    })
