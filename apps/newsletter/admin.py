from django.contrib import admin

from .models import SuscriptorNewsletter


@admin.register(SuscriptorNewsletter)
class SuscriptorNewsletterAdmin(admin.ModelAdmin):
    list_display = ('email', 'activo', 'usuario', 'fecha_suscripcion')
    list_filter = ('activo', 'fecha_suscripcion')
    search_fields = ('email', 'usuario__username', 'usuario__email')
    readonly_fields = ('token', 'fecha_suscripcion', 'fecha_actualizacion')
