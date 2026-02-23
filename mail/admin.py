"""
Admin for Mail App - ModularBEF

Registrazione modelli con admin di default Django.
Tutte le funzioni saranno gestite dai templates custom.
"""

from django.contrib import admin
from .models import (
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
