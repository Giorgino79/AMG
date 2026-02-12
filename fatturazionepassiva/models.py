# fatturazionepassiva/models.py

from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from decimal import Decimal
from django.core.validators import MinValueValidator
from django.utils import timezone
from django.db.models import Q, Sum
import logging

logger = logging.getLogger(__name__)


class RiconoscimentoFornitore(models.Model):
    """
    Riconoscimento periodico per fornitore - quanto ci possono fatturare
    """
    
    # IDENTIFICAZIONE
    numero_riconoscimento = models.CharField(max_length=50, unique=True, help_text="Numero riconoscimento generato automaticamente")
    data_creazione = models.DateTimeField(auto_now_add=True)
    
    # PERIODO DI RIFERIMENTO
    periodo_da = models.DateField(help_text="Data inizio periodo")
    periodo_a = models.DateField(help_text="Data fine periodo")
    
    # FORNITORE
    fornitore = models.ForeignKey('anagrafica.Fornitore', on_delete=models.PROTECT, help_text="Fornitore del riconoscimento")
    
    # STATI
    STATI_RICONOSCIMENTO = [
        ('bozza', 'Bozza'),
        ('definitivo', 'Definitivo'),
        ('inviato', 'Inviato al Fornitore'),
        ('confermato', 'Confermato dal Fornitore'),
        ('fatturato', 'Fatturato'),
        ('annullato', 'Annullato'),
    ]
    stato = models.CharField(max_length=20, choices=STATI_RICONOSCIMENTO, default='bozza')
    
    # FILTRI APPLICATI
    include_ordini_ricevuti = models.BooleanField(default=True, help_text="Include ordini già ricevuti")
    include_ordini_da_ricevere = models.BooleanField(default=False, help_text="Include ordini ancora da ricevere")
    include_ricezioni_manuali = models.BooleanField(default=True, help_text="Include ricezioni manuali (senza ordine)")
    
    # TOTALI CALCOLATI
    totale_imponibile = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text="Totale imponibile")
    totale_iva = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text="Totale IVA")
    totale_riconoscimento = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text="Totale compreso IVA")
    
    # GESTIONE UTENTI
    creato_da = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='riconoscimenti_creati')
    confermato_da = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name='riconoscimenti_confermati')
    data_conferma = models.DateTimeField(null=True, blank=True)
    
    # EMAIL E INVIO
    inviato_via_email = models.BooleanField(default=False, help_text="Inviato via email")
    data_invio_email = models.DateTimeField(null=True, blank=True)
    email_destinatario = models.EmailField(blank=True, help_text="Email di invio")
    
    # NOTE
    note = models.TextField(blank=True, help_text="Note sul riconoscimento")
    
    # TIMESTAMP
    data_modifica = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-data_creazione']
        verbose_name = "Riconoscimento Fornitore"
        verbose_name_plural = "Riconoscimenti Fornitori"
        indexes = [
            models.Index(fields=['numero_riconoscimento']),
            models.Index(fields=['fornitore']),
            models.Index(fields=['periodo_da', 'periodo_a']),
            models.Index(fields=['stato']),
            models.Index(fields=['data_creazione']),
        ]
        unique_together = [
            ('fornitore', 'periodo_da', 'periodo_a')
        ]
    
    def __str__(self):
        return f"{self.numero_riconoscimento} - {self.fornitore.nome} ({self.periodo_da} - {self.periodo_a})"
    
    def save(self, *args, **kwargs):
        """Override save per numerazione automatica e calcoli"""
        
        # Genera numero riconoscimento se nuovo
        if not self.numero_riconoscimento:
            today = timezone.now()
            prefix = f"RIC{today.strftime('%Y%m')}"
            ultimo_numero = RiconoscimentoFornitore.objects.filter(
                numero_riconoscimento__startswith=prefix
            ).count() + 1
            self.numero_riconoscimento = f"{prefix}-{ultimo_numero:03d}"
        
        # Validazioni
        self.clean()
        
        super().save(*args, **kwargs)
        
        # Ricalcola totali dopo il salvataggio
        self.ricalcola_totali()
    
    def clean(self):
        """Validazioni business"""
        if self.periodo_da and self.periodo_a and self.periodo_da > self.periodo_a:
            raise ValidationError({
                'periodo_a': 'La data fine periodo non può essere precedente alla data inizio'
            })
    
    def ricalcola_totali(self):
        """Ricalcola i totali del riconoscimento dalle righe"""
        try:
            righe = self.righe.all()
            self.totale_imponibile = sum(riga.get_totale_imponibile() for riga in righe)
            self.totale_iva = sum(riga.get_totale_iva() for riga in righe)
            self.totale_riconoscimento = self.totale_imponibile + self.totale_iva
            
            # Salva senza triggering save logic per evitare loop
            RiconoscimentoFornitore.objects.filter(pk=self.pk).update(
                totale_imponibile=self.totale_imponibile,
                totale_iva=self.totale_iva,
                totale_riconoscimento=self.totale_riconoscimento
            )
        except Exception as e:
            logger.error(f"Errore ricalcolo totali riconoscimento {self.numero_riconoscimento}: {e}")
    
    def can_modify(self):
        """Può essere modificato se in bozza"""
        return self.stato == 'bozza'
    
    def can_send(self):
        """Può essere inviato se definitivo"""
        return self.stato == 'definitivo'
    
    def can_confirm(self):
        """Può essere confermato se inviato"""
        return self.stato == 'inviato'
    
    def genera_righe_da_acquisti(self):
        """Genera automaticamente le righe dal modulo acquisti"""
        if not self.can_modify():
            raise ValidationError("Impossibile modificare riconoscimento non in bozza")
        
        # Cancella righe esistenti
        self.righe.all().delete()
        
        # Import qui per evitare circular imports
        from acquisti.models import OrdineAcquisto, RigaOrdine
        from ricezioni.models import RigaRicezione
        
        righe_create = 0
        
        # 1. ORDINI RICEVUTI (se abilitato)
        if self.include_ordini_ricevuti:
            # Trova ordini ricevuti nel periodo per questo fornitore
            ordini_ricevuti = OrdineAcquisto.objects.filter(
                fornitore=self.fornitore,
                ricevuto=True,
                data_ordine__date__gte=self.periodo_da,
                data_ordine__date__lte=self.periodo_a
            )
            
            for ordine in ordini_ricevuti:
                for riga_ordine in ordine.righe.all():
                    # Trova le ricezioni per questa riga ordine
                    ricezioni_riga = RigaRicezione.objects.filter(
                        riga_ordine_riferimento=riga_ordine,
                        ricezione__chiusa=True
                    )
                    
                    quantita_ricevuta_totale = sum(
                        r.quantita_ricevuta for r in ricezioni_riga
                    )
                    
                    if quantita_ricevuta_totale > 0:
                        RigaRiconoscimento.objects.create(
                            riconoscimento=self,
                            tipo_origine='ordine_ricevuto',
                            ordine_riferimento=ordine,
                            riga_ordine_riferimento=riga_ordine,
                            prodotto=riga_ordine.prodotto,
                            quantita_ordinata=riga_ordine.quantita_ordinata,
                            quantita_riconosciuta=quantita_ricevuta_totale,
                            prezzo_unitario=riga_ordine.prezzo_unitario,
                            aliquota_iva=riga_ordine.aliquota_iva,
                            descrizione=f"Da ordine {ordine.numero_ordine}"
                        )
                        righe_create += 1
        
        # 2. ORDINI DA RICEVERE (se abilitato)
        if self.include_ordini_da_ricevere:
            ordini_da_ricevere = OrdineAcquisto.objects.filter(
                fornitore=self.fornitore,
                inviato=True,
                ricevuto=False,
                data_ordine__date__gte=self.periodo_da,
                data_ordine__date__lte=self.periodo_a
            )
            
            for ordine in ordini_da_ricevere:
                for riga_ordine in ordine.righe.all():
                    RigaRiconoscimento.objects.create(
                        riconoscimento=self,
                        tipo_origine='ordine_da_ricevere',
                        ordine_riferimento=ordine,
                        riga_ordine_riferimento=riga_ordine,
                        prodotto=riga_ordine.prodotto,
                        quantita_ordinata=riga_ordine.quantita_ordinata,
                        quantita_riconosciuta=riga_ordine.quantita_ordinata,
                        prezzo_unitario=riga_ordine.prezzo_unitario,
                        aliquota_iva=riga_ordine.aliquota_iva,
                        descrizione=f"Da ordine {ordine.numero_ordine} (da ricevere)"
                    )
                    righe_create += 1
        
        # 3. RICEZIONI MANUALI (se abilitato)
        if self.include_ricezioni_manuali:
            from ricezioni.models import Ricezione
            
            ricezioni_manuali = Ricezione.objects.filter(
                fornitore=self.fornitore,
                ordine_riferimento__isnull=True,  # Ricezioni senza ordine
                chiusa=True,
                data_ricezione__date__gte=self.periodo_da,
                data_ricezione__date__lte=self.periodo_a
            )
            
            for ricezione in ricezioni_manuali:
                for riga_ricezione in ricezione.righe.all():
                    RigaRiconoscimento.objects.create(
                        riconoscimento=self,
                        tipo_origine='ricezione_manuale',
                        ricezione_riferimento=ricezione,
                        riga_ricezione_riferimento=riga_ricezione,
                        prodotto=riga_ricezione.prodotto,
                        quantita_riconosciuta=riga_ricezione.quantita_ricevuta,
                        prezzo_unitario=riga_ricezione.prezzo_unitario or Decimal('0.00'),
                        descrizione=f"Da ricezione manuale {ricezione.numero_ricezione}"
                    )
                    righe_create += 1
        
        logger.info(f"Generate {righe_create} righe per riconoscimento {self.numero_riconoscimento}")
        return righe_create


class RigaRiconoscimento(models.Model):
    """
    Riga di un riconoscimento fornitore
    """
    
    # RELAZIONI
    riconoscimento = models.ForeignKey(RiconoscimentoFornitore, on_delete=models.CASCADE, related_name='righe')
    
    # ORIGINE DATI
    TIPI_ORIGINE = [
        ('ordine_ricevuto', 'Da Ordine Ricevuto'),
        ('ordine_da_ricevere', 'Da Ordine da Ricevere'),
        ('ricezione_manuale', 'Da Ricezione Manuale'),
        ('manuale', 'Inserimento Manuale'),
    ]
    tipo_origine = models.CharField(max_length=20, choices=TIPI_ORIGINE, help_text="Origine del dato")
    
    # RIFERIMENTI OPZIONALI
    ordine_riferimento = models.ForeignKey('acquisti.OrdineAcquisto', on_delete=models.PROTECT, null=True, blank=True)
    riga_ordine_riferimento = models.ForeignKey('acquisti.RigaOrdine', on_delete=models.PROTECT, null=True, blank=True)
    ricezione_riferimento = models.ForeignKey('ricezioni.Ricezione', on_delete=models.PROTECT, null=True, blank=True)
    riga_ricezione_riferimento = models.ForeignKey('ricezioni.RigaRicezione', on_delete=models.PROTECT, null=True, blank=True)
    
    # PRODOTTO
    prodotto = models.ForeignKey('prodotti.Prodotto', on_delete=models.PROTECT)
    
    # QUANTITÀ
    quantita_ordinata = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Quantità ordinata (se da ordine)"
    )
    
    quantita_riconosciuta = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Quantità da riconoscere/fatturare"
    )
    
    # PREZZI
    prezzo_unitario = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Prezzo unitario senza IVA"
    )
    
    # IVA
    aliquota_iva = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=22.00,
        help_text="Aliquota IVA in percentuale"
    )
    
    # DESCRIZIONE
    descrizione = models.CharField(max_length=255, help_text="Descrizione della riga")
    note = models.TextField(blank=True, help_text="Note aggiuntive")
    
    # TIMESTAMP
    data_creazione = models.DateTimeField(auto_now_add=True)
    data_modifica = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Riga Riconoscimento"
        verbose_name_plural = "Righe Riconoscimento"
        ordering = ['riconoscimento', 'prodotto']
        indexes = [
            models.Index(fields=['riconoscimento']),
            models.Index(fields=['prodotto']),
            models.Index(fields=['tipo_origine']),
            models.Index(fields=['ordine_riferimento']),
            models.Index(fields=['ricezione_riferimento']),
        ]
    
    def __str__(self):
        return f"{self.prodotto.nome_prodotto} - Qt: {self.quantita_riconosciuta}"
    
    def save(self, *args, **kwargs):
        """Override save per ricalcoli"""
        super().save(*args, **kwargs)
        
        # Ricalcola totali riconoscimento parent
        if self.riconoscimento_id:
            self.riconoscimento.ricalcola_totali()
    
    def get_totale_imponibile(self):
        """Calcola totale imponibile della riga"""
        return self.quantita_riconosciuta * self.prezzo_unitario
    
    def get_totale_iva(self):
        """Calcola IVA della riga"""
        return self.get_totale_imponibile() * (self.aliquota_iva / 100)
    
    def get_totale_con_iva(self):
        """Calcola totale con IVA della riga"""
        return self.get_totale_imponibile() + self.get_totale_iva()
    
    def get_riferimento_display(self):
        """Descrizione del riferimento per template"""
        if self.ordine_riferimento:
            return f"Ordine {self.ordine_riferimento.numero_ordine}"
        elif self.ricezione_riferimento:
            return f"Ricezione {self.ricezione_riferimento.numero_ricezione}"
        else:
            return "Inserimento manuale"


class ExportRiconoscimento(models.Model):
    """
    Traccia degli export effettuati
    """
    
    riconoscimento = models.ForeignKey(RiconoscimentoFornitore, on_delete=models.CASCADE, related_name='export')
    
    TIPI_EXPORT = [
        ('pdf', 'PDF'),
        ('excel', 'Excel'),
        ('csv', 'CSV'),
    ]
    tipo_export = models.CharField(max_length=10, choices=TIPI_EXPORT)
    
    nome_file = models.CharField(max_length=255, help_text="Nome file generato")
    file_path = models.CharField(max_length=500, help_text="Percorso file sul server")
    
    inviato_via_email = models.BooleanField(default=False)
    email_destinatario = models.EmailField(blank=True)
    
    esportato_da = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    data_export = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-data_export']
        verbose_name = "Export Riconoscimento"
        verbose_name_plural = "Export Riconoscimenti"
    
    def __str__(self):
        return f"{self.tipo_export.upper()} - {self.riconoscimento.numero_riconoscimento}"
