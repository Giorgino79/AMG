from django.contrib import admin
from .models import SessioneAllestimento, RigaProdotto


class RigaProdottoInline(admin.TabularInline):
    model = RigaProdotto
    extra = 0
    readonly_fields = ['data_completamento', 'completata_da']


@admin.register(SessioneAllestimento)
class SessioneAllestimentoAdmin(admin.ModelAdmin):
    list_display = ['nome_evento', 'luogo', 'data_creazione', 'completata', 'righe_completate', 'righe_totali']
    list_filter = ['completata', 'data_creazione']
    search_fields = ['nome_evento', 'luogo']
    inlines = [RigaProdottoInline]


@admin.register(RigaProdotto)
class RigaProdottoAdmin(admin.ModelAdmin):
    list_display = ['descrizione', 'quantita_richiesta', 'quantita_allestita', 'completata', 'sessione']
    list_filter = ['completata', 'sessione']
    search_fields = ['descrizione']
