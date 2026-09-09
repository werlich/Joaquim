from django.contrib import admin
from django.db.models import Case, IntegerField, Value, When

from .models import Message, Recado


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('author_display', 'origin', 'is_published', 'created_at', 'short_text')
    list_filter = ('is_published', 'origin')
    search_fields = ('text', 'author_display')
    list_editable = ('is_published',)

    @admin.display(description='Mensagem')
    def short_text(self, obj):
        return obj.text[:60]


@admin.register(Recado)
class RecadoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'relacao', 'created_at', 'status')
    list_filter = ('status', 'created_at')
    search_fields = ('nome', 'mensagem')
    readonly_fields = ('created_at',)
    fields = ('nome', 'relacao', 'email', 'mensagem', 'status', 'created_at')
    actions = ('aprovar', 'rejeitar', 'voltar_pendente')
    date_hierarchy = 'created_at'
    list_per_page = 50

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(
            _pending_rank=Case(
                When(status=Recado.STATUS_PENDING, then=Value(0)),
                default=Value(1),
                output_field=IntegerField(),
            )
        ).order_by('_pending_rank', '-created_at', '-id')

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        pending = Recado.objects.filter(status=Recado.STATUS_PENDING).count()
        if pending:
            extra_context['title'] = (
                f'Recadinhos — {pending} aguardando aprovação'
            )
        return super().changelist_view(request, extra_context=extra_context)

    @admin.action(description='✅ Aprovar recados selecionados')
    def aprovar(self, request, queryset):
        updated = queryset.update(status=Recado.STATUS_APPROVED)
        self.message_user(request, f'{updated} recado(s) aprovado(s).')

    @admin.action(description='❌ Rejeitar recados selecionados')
    def rejeitar(self, request, queryset):
        updated = queryset.update(status=Recado.STATUS_REJECTED)
        self.message_user(request, f'{updated} recado(s) rejeitado(s).')

    @admin.action(description='⏳ Voltar para pendente')
    def voltar_pendente(self, request, queryset):
        updated = queryset.update(status=Recado.STATUS_PENDING)
        self.message_user(request, f'{updated} recado(s) voltaram para pendente.')
