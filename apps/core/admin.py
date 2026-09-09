from django.contrib import admin
from .models import Joaquimetro, SiteSection, TimelineEntry


@admin.register(SiteSection)
class SiteSectionAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'url_name', 'is_published', 'order')
    list_editable = ('is_published', 'order')
    prepopulated_fields = {'slug': ('title',)}


@admin.register(Joaquimetro)
class JoaquimetroAdmin(admin.ModelAdmin):
    list_display = ('due_date', 'birth_date', 'is_active', 'preview')
    list_editable = ('is_active',)

    @admin.display(description='Mensagem atual')
    def preview(self, obj):
        return obj.status()['message']


@admin.register(TimelineEntry)
class TimelineEntryAdmin(admin.ModelAdmin):
    list_display = ('display_date', 'title', 'is_published', 'order')
    list_editable = ('is_published', 'order')
    list_filter = ('is_published',)
    date_hierarchy = 'event_date'
    fields = (
        'order', 'event_date', 'date_label', 'title', 'body',
        'image', 'image_2', 'image_3', 'image_4', 'image_5', 'image_6', 'is_published',
    )

    @admin.display(description='Quando')
    def display_date(self, obj):
        return obj.display_date()
