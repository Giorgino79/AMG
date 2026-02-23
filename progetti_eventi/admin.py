"""
Admin per app progetti_eventi.
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import Progetto, ProgettoReparto, ListaProdotti, ProdottoLista, EngineeringTask


# ============================================================================
# INLINE ADMINS
# ============================================================================

class ProgettoRepartoInline(admin.TabularInline):
    model = ProgettoReparto
    extra = 0
    fields = [
        'tipo_reparto',
        'engineering_assegnato_a',
        'engineering_stato',
        'engineering_completato',
    ]
    readonly_fields = ['engineering_completato']


class ProdottoListaInline(admin.TabularInline):
    model = ProdottoLista
    extra = 1
    fields = [
        'codice_prodotto',
        'nome_prodotto',
        'quantita',
        'peso_kg',
        'note',
    ]


# ============================================================================
# MODEL ADMINS
# ============================================================================

@admin.register(Progetto)
class ProgettoAdmin(admin.ModelAdmin):
    list_display = [
        'codice',
        'nome_evento',
        'cliente',
        'data_evento',
        'commerciale',
        'stato_badge',
        'priorita',
        'created_at',
    ]

    list_filter = [
        'stato',
        'priorita',
        'tipo_evento',
        'data_evento',
        'created_at',
    ]

    search_fields = [
        'codice',
        'nome_evento',
        'cliente__ragione_sociale',
        'location',
        'citta_location',
    ]

    readonly_fields = [
        'codice',
        'created_at',
        'updated_at',
        'created_by',
        'updated_by',
    ]

    fieldsets = [
        ('Informazioni Base', {
            'fields': [
                'codice',
                'cliente',
                'nome_evento',
                'tipo_evento',
                'descrizione_evento',
                'priorita',
            ]
        }),
        ('Date e Orari', {
            'fields': [
                'data_evento',
                'ora_inizio_evento',
                'data_fine_evento',
                'ora_fine_evento',
            ]
        }),
        ('Location', {
            'fields': [
                'location',
                'indirizzo_location',
                'cap_location',
                'citta_location',
                'provincia_location',
                'nazione_location',
            ]
        }),
        ('Logistica', {
            'fields': [
                'data_consegna_richiesta',
                'data_ritiro_richiesta',
                'note_logistica_iniziali',
            ]
        }),
        ('Commerciale', {
            'fields': [
                'commerciale',
                'budget_preventivato',
                'budget_approvato',
                'note_commerciali',
            ]
        }),
        ('Stato', {
            'fields': [
                'stato',
                'reparti_coinvolti',
            ]
        }),
        ('Metadati', {
            'fields': [
                'created_at',
                'updated_at',
                'created_by',
                'updated_by',
            ],
            'classes': ['collapse'],
        }),
    ]

    inlines = [ProgettoRepartoInline]

    def stato_badge(self, obj):
        colore = obj.stato_badge_color
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            f'var(--bs-{colore})' if colore else '#6c757d',
            obj.get_stato_display()
        )
    stato_badge.short_description = 'Stato'


@admin.register(ProgettoReparto)
class ProgettoRepartoAdmin(admin.ModelAdmin):
    list_display = [
        'progetto',
        'tipo_reparto',
        'engineering_assegnato_a',
        'engineering_completato',
        'magazzino_ready',
        'logistica_ready',
        'travel_ready',
        'scouting_ready',
    ]

    list_filter = [
        'tipo_reparto',
        'engineering_stato',
        'engineering_completato',
        'magazzino_ready',
        'logistica_ready',
    ]

    search_fields = [
        'progetto__codice',
        'progetto__nome_evento',
        'engineering_assegnato_a__first_name',
        'engineering_assegnato_a__last_name',
    ]

    readonly_fields = [
        'created_at',
        'updated_at',
    ]


@admin.register(ListaProdotti)
class ListaProdottiAdmin(admin.ModelAdmin):
    list_display = [
        'nome_lista',
        'progetto_reparto',
        'numero_prodotti',
        'approvata',
        'approvata_da',
        'stato',
        'created_at',
    ]

    list_filter = [
        'approvata',
        'stato',
        'created_at',
    ]

    search_fields = [
        'nome_lista',
        'progetto_reparto__progetto__codice',
    ]

    readonly_fields = [
        'created_at',
        'updated_at',
    ]

    inlines = [ProdottoListaInline]


@admin.register(ProdottoLista)
class ProdottoListaAdmin(admin.ModelAdmin):
    list_display = [
        'codice_prodotto',
        'nome_prodotto',
        'lista',
        'quantita',
        'categoria_prodotto',
        'priorita',
    ]

    list_filter = [
        'categoria_prodotto',
        'priorita',
    ]

    search_fields = [
        'codice_prodotto',
        'nome_prodotto',
        'lista__nome_lista',
    ]


@admin.register(EngineeringTask)
class EngineeringTaskAdmin(admin.ModelAdmin):
    list_display = [
        'titolo',
        'progetto_reparto',
        'stato',
        'data_inizio',
        'data_completamento',
        'ore_stimate',
        'ore_effettive',
    ]

    list_filter = [
        'stato',
        'created_at',
    ]

    search_fields = [
        'titolo',
        'descrizione',
        'progetto_reparto__progetto__codice',
    ]
