"""
Admin for Trasporti app
=======================

Configurazione admin con inline per colli ed eventi tracking.
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import (
    RichiestaTrasporto, Collo, TrasportatoreOfferta,
    OffertaTrasporto, ParametroValutazione,
    ConfigurazioneAPITrasporto, EventoTracking
)


# ============================================
# INLINE ADMIN
# ============================================

class ColloInline(admin.TabularInline):
    """Inline per gestione colli"""
    model = Collo
    extra = 1
    fields = ['quantita', 'tipo', 'lunghezza_cm', 'larghezza_cm', 'altezza_cm', 'peso_kg', 'descrizione', 'fragile', 'stackable']
    readonly_fields = []


class TrasportatoreOffertaInline(admin.TabularInline):
    """Inline per gestione trasportatori"""
    model = TrasportatoreOfferta
    extra = 0
    fields = ['trasportatore', 'email_inviata', 'ha_risposto', 'data_invio', 'data_risposta']
    readonly_fields = ['token_accesso', 'data_invio', 'data_risposta']


class ParametroValutazioneInline(admin.TabularInline):
    """Inline per parametri valutazione"""
    model = ParametroValutazione
    extra = 0
    fields = ['descrizione', 'valore', 'ordine']


class EventoTrackingInline(admin.TabularInline):
    """Inline per eventi tracking"""
    model = EventoTracking
    extra = 0
    fields = ['tipo_evento', 'data_evento', 'localita', 'nota']
    readonly_fields = ['data_evento']
    ordering = ['-data_evento']


# ============================================
# MODEL ADMIN
# ============================================

@admin.register(RichiestaTrasporto)
class RichiestaTrasportoAdmin(admin.ModelAdmin):
    """Admin per richieste trasporto"""

    list_display = [
        'numero', 'titolo', 'tipo_trasporto', 'stato_display',
        'priorita_display', 'percorso_display', 'richiedente',
        'data_creazione', 'colli_count'
    ]
    list_filter = ['stato', 'priorita', 'tipo_trasporto', 'data_creazione']
    search_fields = ['numero', 'titolo', 'citta_ritiro', 'citta_consegna']
    readonly_fields = ['numero', 'data_creazione']
    inlines = [ColloInline, TrasportatoreOffertaInline]

    fieldsets = (
        ('Informazioni Generali', {
            'fields': ('numero', 'titolo', 'descrizione', 'tipo_trasporto', 'stato', 'priorita')
        }),
        ('Percorso - Ritiro', {
            'fields': ('indirizzo_ritiro', 'cap_ritiro', 'citta_ritiro', 'provincia_ritiro', 'nazione_ritiro',
                      'lat_ritiro', 'lon_ritiro', 'data_ritiro_richiesta', 'ora_ritiro_dalle', 'ora_ritiro_alle', 'note_ritiro')
        }),
        ('Percorso - Consegna', {
            'fields': ('indirizzo_consegna', 'cap_consegna', 'citta_consegna', 'provincia_consegna', 'nazione_consegna',
                      'lat_consegna', 'lon_consegna', 'data_consegna_richiesta', 'ora_consegna_dalle', 'ora_consegna_alle', 'note_consegna')
        }),
        ('Caratteristiche Merce', {
            'fields': ('tipo_merce', 'valore_merce', 'valuta', 'merce_fragile', 'merce_deperibile',
                      'merce_pericolosa', 'codice_adr', 'temperatura_controllata', 'temperatura_min', 'temperatura_max')
        }),
        ('Servizi Aggiuntivi', {
            'fields': ('assicurazione_richiesta', 'massimale_assicurazione', 'scarico_a_piano',
                      'numero_piano', 'presenza_montacarichi', 'tracking_richiesto', 'packing_list_richiesto')
        }),
        ('Workflow', {
            'fields': ('richiedente', 'operatore', 'approvatore', 'budget_massimo',
                      'offerta_approvata', 'note_interne')
        }),
        ('Date', {
            'fields': ('data_creazione', 'data_invio_richiesta', 'data_valutazione',
                      'data_approvazione', 'data_ritiro_effettivo', 'data_consegna_effettiva'),
            'classes': ('collapse',)
        }),
    )

    def stato_display(self, obj):
        colors = {
            'BOZZA': 'secondary',
            'RICHIESTA_INVIATA': 'primary',
            'OFFERTE_RICEVUTE': 'info',
            'IN_VALUTAZIONE': 'warning',
            'APPROVATA': 'success',
            'IN_CORSO': 'info',
            'CONSEGNATO': 'success',
            'ANNULLATA': 'danger',
        }
        color = colors.get(obj.stato, 'secondary')
        return format_html(
            '<span class="badge bg-{}">{}</span>',
            color, obj.get_stato_display()
        )
    stato_display.short_description = 'Stato'

    def priorita_display(self, obj):
        colors = {'BASSA': 'secondary', 'NORMALE': 'info', 'ALTA': 'warning', 'URGENTE': 'danger'}
        color = colors.get(obj.priorita, 'secondary')
        return format_html('<span class="badge bg-{}">{}</span>', color, obj.get_priorita_display())
    priorita_display.short_description = 'Priorità'

    def percorso_display(self, obj):
        return f"{obj.citta_ritiro} → {obj.citta_consegna}"
    percorso_display.short_description = 'Percorso'

    def colli_count(self, obj):
        return obj.numero_colli_totali
    colli_count.short_description = 'N° Colli'


@admin.register(Collo)
class ColloAdmin(admin.ModelAdmin):
    """Admin per colli"""

    list_display = ['richiesta', 'quantita', 'tipo', 'dimensioni_display', 'peso_kg', 'volume_m3', 'fragile']
    list_filter = ['tipo', 'fragile', 'stackable']
    search_fields = ['richiesta__numero', 'descrizione']
    readonly_fields = ['volume_m3']

    def dimensioni_display(self, obj):
        return f"{obj.lunghezza_cm} x {obj.larghezza_cm} x {obj.altezza_cm} cm"
    dimensioni_display.short_description = 'Dimensioni (L x W x H)'


@admin.register(TrasportatoreOfferta)
class TrasportatoreOffertaAdmin(admin.ModelAdmin):
    """Admin per trasportatori-offerte"""

    list_display = ['richiesta', 'trasportatore', 'email_status', 'risposta_status', 'giorni_senza_risposta']
    list_filter = ['email_inviata', 'ha_risposto']
    search_fields = ['richiesta__numero', 'trasportatore__ragione_sociale']
    readonly_fields = ['token_accesso', 'data_invio', 'data_lettura', 'data_risposta']

    def email_status(self, obj):
        if obj.email_letta:
            return format_html('<span style="color: green;">✓ Letta</span>')
        elif obj.email_inviata:
            return format_html('<span style="color: orange;">✓ Inviata</span>')
        return format_html('<span style="color: red;">✗ Non inviata</span>')
    email_status.short_description = 'Email'

    def risposta_status(self, obj):
        if obj.ha_risposto:
            return format_html('<span style="color: green;">✓ Ricevuta</span>')
        return format_html('<span style="color: orange;">⏳ In attesa</span>')
    risposta_status.short_description = 'Risposta'


@admin.register(OffertaTrasporto)
class OffertaTrasportoAdmin(admin.ModelAdmin):
    """Admin per offerte trasporto"""

    list_display = [
        'richiesta', 'trasportatore', 'importo_display',
        'data_ritiro_proposta', 'data_consegna_prevista',
        'tempo_transito_giorni', 'tipo_mezzo', 'scadenza_display'
    ]
    list_filter = ['tipo_mezzo', 'tracking_incluso', 'assicurazione_inclusa']
    search_fields = ['richiesta__numero', 'trasportatore__ragione_sociale', 'numero_offerta']
    readonly_fields = ['data_ricevimento']
    inlines = [ParametroValutazioneInline, EventoTrackingInline]

    fieldsets = (
        ('Informazioni Generali', {
            'fields': ('richiesta', 'trasportatore', 'numero_offerta', 'operatore_inserimento')
        }),
        ('Prezzi', {
            'fields': ('importo_trasporto', 'importo_assicurazione', 'importo_pedaggi',
                      'importo_extra', 'descrizione_extra', 'importo_totale', 'valuta',
                      'prezzo_per_km', 'prezzo_per_kg')
        }),
        ('Tempi', {
            'fields': ('data_ritiro_proposta', 'ora_ritiro_dalle', 'ora_ritiro_alle',
                      'data_consegna_prevista', 'ora_consegna_dalle', 'ora_consegna_alle',
                      'tempo_transito_giorni')
        }),
        ('Mezzo e Conducente', {
            'fields': ('tipo_mezzo', 'targa_mezzo', 'capienza_kg', 'capienza_m3',
                      'conducente_nome', 'conducente_telefono')
        }),
        ('Condizioni e Servizi', {
            'fields': ('termini_pagamento', 'validita_offerta_giorni', 'data_scadenza_offerta',
                      'tracking_incluso', 'assicurazione_inclusa', 'scarico_a_piano_incluso')
        }),
        ('Tracking', {
            'fields': ('numero_tracking', 'link_tracking', 'numero_ordine')
        }),
        ('File e Note', {
            'fields': ('file_offerta', 'note_tecniche', 'note_commerciali')
        }),
    )

    def importo_display(self, obj):
        return format_html('<strong>€{:,.2f}</strong>', obj.importo_totale)
    importo_display.short_description = 'Importo Totale'

    def scadenza_display(self, obj):
        if obj.is_scaduta:
            return format_html('<span style="color: red;">Scaduta</span>')
        giorni = obj.giorni_validita_rimanenti
        if giorni is None:
            return '-'
        if giorni <= 2:
            color = 'red'
        elif giorni <= 5:
            color = 'orange'
        else:
            color = 'green'
        return format_html('<span style="color: {};">{} giorni</span>', color, giorni)
    scadenza_display.short_description = 'Validità'


@admin.register(ParametroValutazione)
class ParametroValutazioneAdmin(admin.ModelAdmin):
    """Admin per parametri valutazione"""

    list_display = ['offerta', 'descrizione', 'valore', 'ordine', 'creato_da']
    list_filter = ['descrizione']
    search_fields = ['offerta__richiesta__numero', 'descrizione', 'valore']


@admin.register(ConfigurazioneAPITrasporto)
class ConfigurazioneAPITrasportoAdmin(admin.ModelAdmin):
    """Admin per configurazioni API"""

    list_display = ['provider', 'attivo', 'ultimo_test', 'test_status']
    list_filter = ['provider', 'attivo', 'ultimo_test_successo']
    readonly_fields = ['ultimo_test']

    fieldsets = (
        ('Provider', {
            'fields': ('provider', 'attivo')
        }),
        ('Credenziali API', {
            'fields': ('api_key', 'api_secret', 'api_endpoint')
        }),
        ('Configurazione Extra', {
            'fields': ('configurazione_extra',),
            'classes': ('collapse',)
        }),
        ('Test', {
            'fields': ('ultimo_test', 'ultimo_test_successo')
        }),
    )

    def test_status(self, obj):
        if obj.ultimo_test_successo:
            return format_html('<span style="color: green;">✓ Successo</span>')
        return format_html('<span style="color: red;">✗ Fallito</span>')
    test_status.short_description = 'Ultimo Test'


@admin.register(EventoTracking)
class EventoTrackingAdmin(admin.ModelAdmin):
    """Admin per eventi tracking"""

    list_display = ['offerta', 'tipo_evento', 'data_evento', 'localita', 'source_api']
    list_filter = ['tipo_evento', 'source_api', 'data_evento']
    search_fields = ['offerta__richiesta__numero', 'localita', 'nota']
    readonly_fields = ['data_evento']

    fieldsets = (
        ('Evento', {
            'fields': ('offerta', 'tipo_evento', 'data_evento', 'localita', 'nota')
        }),
        ('Sorgente Esterna', {
            'fields': ('source_api', 'external_id'),
            'classes': ('collapse',)
        }),
    )
