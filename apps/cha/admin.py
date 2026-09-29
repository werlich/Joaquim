from django import forms
from django.contrib import admin, messages
from django.db.models import Count, Q, Sum
from django.shortcuts import redirect, render
from django.urls import path

from .forms import ChaRsvpForm
from .models import (
    BabyShowerEvent, ChaGuest, ChaRsvp, DiaperPledge, DiaperSize, GalleryPhoto,
    Gift, GiftCategory, GiftReservation, ReservationLike,
)
from .services.reservas import cancelar_pledge_fralda, cancelar_reserva_presente


class BabyShowerEventAdminForm(forms.ModelForm):
    new_access_code = forms.CharField(
        label='Novo código de acesso',
        required=False,
        widget=forms.PasswordInput(render_value=False, attrs={'autocomplete': 'new-password'}),
        help_text='Deixe em branco para manter o código atual. O valor nunca é exibido depois de salvo.',
    )

    class Meta:
        model = BabyShowerEvent
        fields = (
            'title', 'invite_message', 'event_date', 'event_time',
            'location', 'address', 'info_text', 'whatsapp_text',
            'invite_active', 'rsvp_active', 'is_active',
        )

    def save(self, commit=True):
        obj = super().save(commit=False)
        raw = self.cleaned_data.get('new_access_code') or ''
        if raw.strip():
            obj.set_access_code(raw)
        if commit:
            obj.save()
        return obj


@admin.register(BabyShowerEvent)
class BabyShowerEventAdmin(admin.ModelAdmin):
    form = BabyShowerEventAdminForm
    list_display = (
        'title', 'event_date', 'event_time', 'location',
        'invite_active', 'rsvp_active', 'has_code', 'is_active',
    )
    list_editable = ('invite_active', 'rsvp_active', 'is_active')
    exclude = ('access_code_hash',)

    @admin.display(boolean=True, description='Código definido')
    def has_code(self, obj):
        return bool(obj.access_code_hash)


@admin.register(ChaGuest)
class ChaGuestAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at', 'last_login_at')
    search_fields = ('name',)
    readonly_fields = ('name', 'name_key', 'password_hash', 'created_at', 'last_login_at')


@admin.register(ChaRsvp)
class ChaRsvpAdmin(admin.ModelAdmin):
    list_display = ('name', 'response', 'companions', 'created_at')
    list_filter = ('response',)
    readonly_fields = ('created_at',)
    search_fields = ('name',)
    change_list_template = 'admin/cha/charsvp/change_list.html'

    def _resumo_presenca(self):
        totais = ChaRsvp.objects.aggregate(
            total=Count('id'),
            sim=Count('id', filter=Q(response=ChaRsvp.RESPONSE_SIM)),
            talvez=Count('id', filter=Q(response=ChaRsvp.RESPONSE_TALVEZ)),
            nao=Count('id', filter=Q(response=ChaRsvp.RESPONSE_NAO)),
            acompanhantes_sim=Sum(
                'companions',
                filter=Q(response=ChaRsvp.RESPONSE_SIM),
            ),
            acompanhantes_talvez=Sum(
                'companions',
                filter=Q(response=ChaRsvp.RESPONSE_TALVEZ),
            ),
        )
        pessoas_sim = (totais['sim'] or 0) + (totais['acompanhantes_sim'] or 0)
        pessoas_talvez = (totais['talvez'] or 0) + (totais['acompanhantes_talvez'] or 0)
        return {
            'totais': totais,
            'pessoas_esperadas': pessoas_sim,
            'pessoas_talvez': pessoas_talvez,
            'total_participantes': pessoas_sim,
        }

    def get_urls(self):
        info = (self.opts.app_label, self.opts.model_name)
        custom = [
            path(
                'formulario/',
                self.admin_site.admin_view(self.formulario_view),
                name='%s_%s_formulario' % info,
            ),
        ]
        return custom + super().get_urls()

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context.update(self._resumo_presenca())
        return super().changelist_view(request, extra_context=extra_context)

    def formulario_view(self, request):
        form = ChaRsvpForm()
        if request.method == 'POST':
            form = ChaRsvpForm(request.POST)
            if form.is_valid():
                ChaRsvp.objects.create(
                    name=(form.cleaned_data.get('name') or '').strip(),
                    response=form.cleaned_data['response'],
                    companions=form.cleaned_data.get('companions') or 0,
                )
                self.message_user(
                    request,
                    'Confirmação de presença registrada.',
                    messages.SUCCESS,
                )
                return redirect('admin:cha_charsvp_formulario')
        context = {
            **self.admin_site.each_context(request),
            **self._resumo_presenca(),
            'opts': self.opts,
            'form': form,
            'confirmacoes': list(ChaRsvp.objects.order_by('name', 'id')),
            'title': 'Formulário de presença',
        }
        return render(request, 'admin/cha/charsvp/formulario.html', context)


@admin.register(GiftCategory)
class GiftCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'order')
    list_editable = ('order',)


class GiftReservationInline(admin.TabularInline):
    model = GiftReservation
    extra = 0
    readonly_fields = ('quantity', 'guest_name', 'item_name', 'is_anonymous', 'message', 'created_at', 'cancelled_at')
    can_delete = False


@admin.register(Gift)
class GiftAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'meta_quantity', 'is_available', 'order')
    list_filter = ('is_available', 'category')
    list_editable = ('order', 'is_available', 'meta_quantity')
    inlines = [GiftReservationInline]


@admin.action(description='Cancelar reservas selecionadas')
def cancel_gift_reservations(modeladmin, request, queryset):
    n = 0
    for res in queryset.filter(cancelled_at__isnull=True):
        cancelar_reserva_presente(res.pk)
        n += 1
    modeladmin.message_user(request, f'{n} reserva(s) cancelada(s).', messages.SUCCESS)


@admin.register(GiftReservation)
class GiftReservationAdmin(admin.ModelAdmin):
    list_display = (
        'gift', 'display_name', 'item_name', 'is_anonymous', 'likes',
        'created_at', 'cancelled_at',
    )
    list_filter = ('is_anonymous',)
    actions = [cancel_gift_reservations]
    readonly_fields = ('created_at', 'cancelled_at', 'likes')


@admin.register(ReservationLike)
class ReservationLikeAdmin(admin.ModelAdmin):
    list_display = (
        'guest', 'presente', 'escolhido_por', 'situacao', 'created_at', 'removed_at',
    )
    list_filter = ('guest', 'removed_at')
    search_fields = ('guest__name', 'reservation__guest_name', 'reservation__gift__name')
    readonly_fields = ('reservation', 'guest', 'created_at', 'removed_at')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('guest', 'reservation', 'reservation__gift')

    @admin.display(description='Presente', ordering='reservation__gift__name')
    def presente(self, obj):
        return obj.reservation.gift.name

    @admin.display(description='Escolhido por')
    def escolhido_por(self, obj):
        return obj.reservation.display_name

    @admin.display(boolean=True, description='Vigente')
    def situacao(self, obj):
        return obj.is_current


@admin.register(DiaperSize)
class DiaperSizeAdmin(admin.ModelAdmin):
    list_display = ('label', 'code', 'meta_packs', 'chosen', 'available', 'order', 'has_image')
    list_editable = ('meta_packs', 'order')

    @admin.display(description='Escolhidos')
    def chosen(self, obj):
        return obj.chosen_packs()

    @admin.display(description='Disponíveis')
    def available(self, obj):
        return obj.available_packs()

    @admin.display(boolean=True, description='Imagem')
    def has_image(self, obj):
        return bool(obj.image)


@admin.action(description='Cancelar escolhas selecionadas (devolve estoque)')
def cancel_diaper_pledges(modeladmin, request, queryset):
    n = 0
    for p in queryset.filter(cancelled_at__isnull=True):
        cancelar_pledge_fralda(p.pk)
        n += 1
    modeladmin.message_user(request, f'{n} escolha(s) cancelada(s).', messages.SUCCESS)


@admin.register(DiaperPledge)
class DiaperPledgeAdmin(admin.ModelAdmin):
    list_display = ('size', 'quantity', 'display_name', 'created_at', 'cancelled_at')
    list_filter = ('size',)
    actions = [cancel_diaper_pledges]


@admin.register(GalleryPhoto)
class GalleryPhotoAdmin(admin.ModelAdmin):
    list_display = ('caption', 'event', 'is_published', 'order')
    list_editable = ('is_published', 'order')
    list_filter = ('is_published',)
