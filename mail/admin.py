"""
Admin for Mail App - ModularBEF

Registrazione modelli con admin di default Django.
Tutte le funzioni saranno gestite dai templates custom.
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import (
    CompanyEmailSettings,
    EmailConfiguration,
    EmailTemplate,
    EmailFolder,
    EmailLabel,
    EmailMessage,
    EmailQueue,
    EmailStats,
    EmailLog,
    Promemoria,
    ChatConversation,
    ChatMessage,
)


# ============================================================================
# COMPANY EMAIL SETTINGS ADMIN
# ============================================================================

@admin.register(CompanyEmailSettings)
class CompanyEmailSettingsAdmin(admin.ModelAdmin):
    """Admin per configurazioni SMTP aziendali"""

    list_display = [
        'name',
        'smtp_server',
        'smtp_port',
        'is_active_badge',
        'is_verified_badge',
        'users_count',
        'last_test_at',
    ]
    list_filter = ['is_active', 'is_verified', 'use_tls', 'use_ssl']
    search_fields = ['name', 'smtp_server', 'default_from_domain']

    fieldsets = (
        ('Informazioni Generali', {
            'fields': ('name', 'is_active')
        }),
        ('Configurazione SMTP', {
            'fields': (
                'smtp_server',
                'smtp_port',
                'smtp_username',
                'smtp_password',
                'use_tls',
                'use_ssl',
            )
        }),
        ('Impostazioni Mittente', {
            'fields': (
                'allow_custom_from',
                'default_from_domain',
                'require_same_domain',
            ),
            'description': 'Controlla come gli utenti possono impostare il mittente'
        }),
        ('Limiti', {
            'fields': ('daily_limit_per_user',),
            'classes': ('collapse',)
        }),
        ('Stato', {
            'fields': ('is_verified', 'last_test_at', 'last_error'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ['is_verified', 'last_test_at']

    def is_active_badge(self, obj):
        if obj.is_active:
            return format_html('<span style="color: green;">✓ Attiva</span>')
        return format_html('<span style="color: red;">✗ Disattivata</span>')
    is_active_badge.short_description = 'Stato'

    def is_verified_badge(self, obj):
        if obj.is_verified:
            return format_html('<span style="color: green;">✓ Verificata</span>')
        return format_html('<span style="color: orange;">⚠ Non verificata</span>')
    is_verified_badge.short_description = 'Verifica'

    def users_count(self, obj):
        count = obj.user_configs.filter(config_type='company').count()
        return f"{count} utenti"
    users_count.short_description = 'Utilizzo'


# Registrazione semplice senza customizzazioni
admin.site.register(EmailConfiguration)
admin.site.register(EmailTemplate)
admin.site.register(EmailFolder)
admin.site.register(EmailLabel)
admin.site.register(EmailMessage)
admin.site.register(EmailQueue)
admin.site.register(EmailStats)
admin.site.register(EmailLog)
admin.site.register(Promemoria)
admin.site.register(ChatConversation)
admin.site.register(ChatMessage)
