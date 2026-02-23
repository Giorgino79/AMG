# fatturazionepassiva/admin.py

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import RiconoscimentoFornitore, RigaRiconoscimento, ExportRiconoscimento


class RigaRiconoscimentoInline(admin.TabularInline):
    model = RigaRiconoscimento
    extra = 0
    readonly_fields = ('get_totale_imponibile', 'get_totale_iva', 'get_totale_con_iva')
    fields = (
        'prodotto', 'tipo_origine', 'quantita_ordinata', 'quantita_riconosciuta',
        'prezzo_unitario', 'aliquota_iva', 'get_totale_imponibile', 'get_totale_iva',
        'get_totale_con_iva', 'descrizione'
    )
    
    def get_totale_imponibile(self, obj):
        if obj.pk:
            return f"€ {obj.get_totale_imponibile():.2f}"
        return "-"
    get_totale_imponibile.short_description = "Tot. Imponibile"
    
    def get_totale_iva(self, obj):
        if obj.pk:
            return f"€ {obj.get_totale_iva():.2f}"
        return "-"
    get_totale_iva.short_description = "Tot. IVA"
    
    def get_totale_con_iva(self, obj):
        if obj.pk:
            return f"€ {obj.get_totale_con_iva():.2f}"
        return "-"
    get_totale_con_iva.short_description = "Tot. con IVA"


@admin.register(RiconoscimentoFornitore)
class RiconoscimentoFornitoreAdmin(admin.ModelAdmin):
    list_display = (
        'numero_riconoscimento', 'fornitore', 'periodo_da', 'periodo_a',
        'stato', 'totale_riconoscimento_display', 'data_creazione',
        'inviato_via_email', 'azioni_admin'
    )
    list_filter = (
        'stato', 'fornitore', 'data_creazione', 'inviato_via_email',
        'include_ordini_ricevuti', 'include_ordini_da_ricevere', 'include_ricezioni_manuali'
    )
    search_fields = ('numero_riconoscimento', 'fornitore__nome', 'note')
    readonly_fields = (
        'numero_riconoscimento', 'data_creazione', 'data_modifica',
        'totale_imponibile', 'totale_iva', 'totale_riconoscimento'
    )
    
    fieldsets = (
        ('Identificazione', {
            'fields': ('numero_riconoscimento', 'fornitore', 'stato')
        }),
        ('Periodo', {
            'fields': ('periodo_da', 'periodo_a')
        }),
        ('Filtri Inclusione', {
            'fields': (
                'include_ordini_ricevuti', 'include_ordini_da_ricevere',
                'include_ricezioni_manuali'
            )
        }),
        ('Totali', {
            'fields': ('totale_imponibile', 'totale_iva', 'totale_riconoscimento'),
            'classes': ('collapse',)
        }),
        ('Gestione Utenti', {
            'fields': ('creato_da', 'confermato_da', 'data_conferma'),
            'classes': ('collapse',)
        }),
        ('Email', {
            'fields': ('inviato_via_email', 'data_invio_email', 'email_destinatario'),
            'classes': ('collapse',)
        }),
        ('Note', {
            'fields': ('note',)
        }),
        ('Timestamp', {
            'fields': ('data_creazione', 'data_modifica'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [RigaRiconoscimentoInline]
    
    def totale_riconoscimento_display(self, obj):
        return f"€ {obj.totale_riconoscimento:.2f}"
    totale_riconoscimento_display.short_description = "Totale"
    totale_riconoscimento_display.admin_order_field = "totale_riconoscimento"
    
    def azioni_admin(self, obj):
        """Azioni rapide in admin"""
        html = []
        
        # Link dettaglio frontend
        if obj.pk:
            dettaglio_url = reverse('fatturazionepassiva:dettaglio_riconoscimento', args=[obj.pk])
            html.append(f'<a href="{dettaglio_url}" target="_blank" title="Apri nel frontend">👁️</a>')
            
            # Export
            pdf_url = reverse('fatturazionepassiva:export_pdf', args=[obj.pk])
            excel_url = reverse('fatturazionepassiva:export_excel', args=[obj.pk])
            csv_url = reverse('fatturazionepassiva:export_csv', args=[obj.pk])
            
            html.append(f'<a href="{pdf_url}" title="Esporta PDF">📄</a>')
            html.append(f'<a href="{excel_url}" title="Esporta Excel">📊</a>')
            html.append(f'<a href="{csv_url}" title="Esporta CSV">📋</a>')
        
        return format_html(' | '.join(html)) if html else '-'
    azioni_admin.short_description = "Azioni"
    
    def save_model(self, request, obj, form, change):
        if not change:  # Nuovo oggetto
            obj.creato_da = request.user
        super().save_model(request, obj, form, change)


@admin.register(RigaRiconoscimento)
class RigaRiconoscimentoAdmin(admin.ModelAdmin):
    list_display = (
        'riconoscimento', 'prodotto', 'tipo_origine', 'quantita_riconosciuta',
        'prezzo_unitario', 'get_totale_con_iva_display'
    )
    list_filter = ('tipo_origine', 'riconoscimento__fornitore', 'riconoscimento__stato')
    search_fields = ('prodotto__nome_prodotto', 'riconoscimento__numero_riconoscimento', 'descrizione')
    readonly_fields = ('get_totale_imponibile', 'get_totale_iva', 'get_totale_con_iva')
    
    def get_totale_con_iva_display(self, obj):
        return f"€ {obj.get_totale_con_iva():.2f}"
    get_totale_con_iva_display.short_description = "Totale"


@admin.register(ExportRiconoscimento)
class ExportRiconoscimentoAdmin(admin.ModelAdmin):
    list_display = (
        'riconoscimento', 'tipo_export', 'nome_file', 'data_export',
        'inviato_via_email', 'email_destinatario', 'esportato_da'
    )
    list_filter = ('tipo_export', 'inviato_via_email', 'data_export')
    search_fields = ('riconoscimento__numero_riconoscimento', 'nome_file', 'email_destinatario')
    readonly_fields = ('data_export',)
    
    def has_add_permission(self, request):
        """Non permettere creazione manuale"""
        return False
