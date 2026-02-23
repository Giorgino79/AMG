"""
ACQUISTI MODELS - Sistema gestione ordini di acquisto
===================================================

Modelli per gestire gli ordini di acquisto (ODA):
- OrdineAcquisto: Ordine principale con stati semplificati
- Integrazione con preventivi_beni e trasporti
"""

from django.db import models
from django.conf import settings
from django.utils import timezone
from django.contrib.contenttypes.fields import GenericRelation, GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from decimal import Decimal

# Import dei mixin dal core
from core.models_legacy import SearchMixin


class OrdineAcquisto(SearchMixin, models.Model):
    """
    Ordine di Acquisto (ODA) - Modello principale
    Supporta preventivi_beni e trasporti tramite GenericForeignKey
    """

    # IDENTIFICAZIONE
    numero_ordine = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        help_text="Numero ODA generato automaticamente (ODA-YYYY-NNN)"
    )
    data_ordine = models.DateTimeField(auto_now_add=True)
    data_consegna_richiesta = models.DateField(
        help_text="Data richiesta per la consegna"
    )

    # TIPO ORIGINE
    TIPO_ORIGINE_CHOICES = [
        ('PREVENTIVO', 'Preventivo Beni/Servizi'),
        ('TRASPORTO', 'Trasporto'),
        ('MANUALE', 'Inserimento Manuale'),
    ]
    tipo_origine = models.CharField(
        max_length=20,
        choices=TIPO_ORIGINE_CHOICES,
        default='MANUALE',
        help_text="Tipo di documento che ha generato l'ordine"
    )

    # RELAZIONE GENERICA per collegare a preventivi_beni o trasporti
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Tipo di oggetto collegato (RichiestaPreventivo o RichiestaTrasporto)"
    )
    object_id = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="ID dell'oggetto collegato"
    )
    oggetto_origine = GenericForeignKey('content_type', 'object_id')

    # RELAZIONI SPECIFICHE (opzionali, per query dirette)
    richiesta_preventivo = models.ForeignKey(
        'preventivi_beni.RichiestaPreventivo',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='ordini_acquisto',
        help_text="Richiesta preventivo che ha generato questo ordine"
    )
    richiesta_trasporto = models.ForeignKey(
        'trasporti.RichiestaTrasporto',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='ordini_acquisto',
        help_text="Richiesta trasporto che ha generato questo ordine"
    )

    # FORNITORE
    fornitore = models.ForeignKey(
        'anagrafica.Fornitore',
        on_delete=models.PROTECT,
        related_name='ordini_acquisto',
        help_text="Fornitore dell'ordine"
    )

    # STATI ODA - SEMPLIFICATI
    STATI_CHOICES = [
        ('CREATO', 'Creato'),
        ('RICEVUTO', 'Ricevuto'),
        ('PAGATO', 'Pagato'),
    ]
    stato = models.CharField(
        max_length=20,
        choices=STATI_CHOICES,
        default='CREATO',
        help_text="Stato attuale dell'ordine"
    )

    # DATI COMMERCIALI
    imponibile = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Importo imponibile (netto)"
    )
    aliquota_iva = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('22.00'),
        help_text="Aliquota IVA in percentuale"
    )
    importo_iva = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Importo IVA calcolato"
    )
    importo_totale = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="Importo totale dell'ordine (imponibile + IVA)"
    )
    valuta = models.CharField(max_length=3, default='EUR')
    termini_pagamento = models.CharField(
        max_length=200,
        blank=True,
        help_text="Condizioni di pagamento"
    )
    tempi_consegna = models.CharField(
        max_length=200,
        blank=True,
        help_text="Tempi di consegna previsti"
    )

    # DESCRIZIONE ORDINE
    oggetto_ordine = models.CharField(
        max_length=500,
        blank=True,
        help_text="Oggetto/descrizione dell'ordine"
    )
    descrizione_dettagliata = models.TextField(
        blank=True,
        help_text="Descrizione dettagliata dei beni/servizi"
    )

    # GESTIONE WORKFLOW
    creato_da = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='ordini_acquisto_creati',
        help_text="Utente che ha creato l'ordine"
    )

    # RICEVIMENTO
    data_ricevimento = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Data di ricevimento della merce"
    )
    ricevuto_da = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        related_name='ordini_acquisto_ricevuti',
        on_delete=models.PROTECT,
        help_text="Utente che ha confermato il ricevimento"
    )

    # PAGAMENTO
    data_pagamento = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Data di pagamento"
    )
    pagato_da = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        related_name='ordini_acquisto_pagati',
        on_delete=models.PROTECT,
        help_text="Utente che ha confermato il pagamento"
    )

    # NOTE E RIFERIMENTI
    note_ordine = models.TextField(
        blank=True,
        help_text="Note generali sull'ordine"
    )
    riferimento_fornitore = models.CharField(
        max_length=100,
        blank=True,
        help_text="Riferimento/numero offerta del fornitore"
    )

    # ALLEGATI
    allegati = GenericRelation('core.Allegato', related_query_name='ordine_acquisto')

    # TIMESTAMP
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Ordine di Acquisto"
        verbose_name_plural = "Ordini di Acquisto"
        ordering = ['-data_ordine']
        indexes = [
            models.Index(fields=['numero_ordine']),
            models.Index(fields=['stato']),
            models.Index(fields=['fornitore']),
            models.Index(fields=['data_ordine']),
            models.Index(fields=['tipo_origine']),
        ]

    def __str__(self):
        return f"{self.numero_ordine} - {self.fornitore.ragione_sociale} - €{self.importo_totale}"

    @classmethod
    def get_search_fields(cls):
        """Campi ricercabili nella ricerca globale"""
        return ['numero_ordine', 'oggetto_ordine', 'riferimento_fornitore']

    def get_search_result_display(self):
        """Testo visualizzato nei risultati di ricerca"""
        return f"{self.numero_ordine} - {self.fornitore.ragione_sociale}"

    def get_absolute_url(self):
        """URL per navigare al dettaglio dell'ordine"""
        from django.urls import reverse
        return reverse('acquisti:ordine_detail', kwargs={'pk': self.pk})

    def save(self, *args, **kwargs):
        """Override save per numerazione automatica e calcolo IVA"""
        if not self.numero_ordine:
            self.numero_ordine = self.genera_numero_oda()

        # Calcola IVA e totale se imponibile è impostato
        if self.imponibile and self.imponibile > 0:
            self.importo_iva = (self.imponibile * self.aliquota_iva / Decimal('100')).quantize(Decimal('0.01'))
            self.importo_totale = self.imponibile + self.importo_iva
        elif self.importo_totale and self.importo_totale > 0 and (not self.imponibile or self.imponibile == 0):
            # Scorporo IVA dal totale se imponibile non è impostato
            self.imponibile = (self.importo_totale / (1 + self.aliquota_iva / Decimal('100'))).quantize(Decimal('0.01'))
            self.importo_iva = self.importo_totale - self.imponibile

        super().save(*args, **kwargs)

    @classmethod
    def genera_numero_oda(cls):
        """Genera numero ODA automatico: ODA-YYYY-NNN"""
        year = timezone.now().year
        last_order = cls.objects.filter(
            numero_ordine__startswith=f'ODA-{year}-'
        ).order_by('-numero_ordine').first()

        if last_order:
            try:
                last_num = int(last_order.numero_ordine.split('-')[-1])
                new_num = last_num + 1
            except (ValueError, IndexError):
                new_num = 1
        else:
            new_num = 1

        return f'ODA-{year}-{new_num:03d}'

    # METODI DI STATO
    def puo_essere_ricevuto(self):
        """Verifica se l'ordine può essere segnato come ricevuto"""
        return self.stato == 'CREATO'

    def puo_essere_pagato(self):
        """Verifica se l'ordine può essere segnato come pagato"""
        return self.stato == 'RICEVUTO'

    def segna_come_ricevuto(self, utente):
        """Segna l'ordine come ricevuto"""
        if self.puo_essere_ricevuto():
            self.stato = 'RICEVUTO'
            self.data_ricevimento = timezone.now()
            self.ricevuto_da = utente
            self.save()
            return True
        return False

    def segna_come_pagato(self, utente):
        """Segna l'ordine come pagato"""
        if self.puo_essere_pagato():
            self.stato = 'PAGATO'
            self.data_pagamento = timezone.now()
            self.pagato_da = utente
            self.save()
            return True
        return False

    def get_stato_css_class(self):
        """Classe CSS Bootstrap per badge dello stato"""
        css_classes = {
            'CREATO': 'warning',
            'RICEVUTO': 'info',
            'PAGATO': 'success',
        }
        return css_classes.get(self.stato, 'secondary')

    def get_giorni_dalla_creazione(self):
        """Calcola i giorni dalla creazione dell'ordine"""
        return (timezone.now() - self.data_ordine).days

    @property
    def titolo_display(self):
        """Titolo per visualizzazione"""
        if self.oggetto_ordine:
            return self.oggetto_ordine
        if self.richiesta_preventivo:
            return self.richiesta_preventivo.titolo
        if self.richiesta_trasporto:
            return self.richiesta_trasporto.titolo
        return f"Ordine {self.numero_ordine}"

    @property
    def origine_display(self):
        """Visualizza l'origine dell'ordine"""
        if self.richiesta_preventivo:
            return f"Preventivo {self.richiesta_preventivo.numero}"
        if self.richiesta_trasporto:
            return f"Trasporto {self.richiesta_trasporto.numero}"
        return "Manuale"

    # METODI PER ALLEGATI
    def get_allegati_attivi(self):
        """Ritorna gli allegati per questo ordine"""
        return self.allegati.all()

    def has_allegati(self):
        """Verifica se l'ordine ha allegati"""
        return self.allegati.exists()
