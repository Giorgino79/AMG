"""
Models for Trasporti app
=========================

Sistema completo di gestione trasporti merci.
Supporta pacchi, carichi parziali (LTL) e camion completi (FTL).
"""

from django.db import models
from django.conf import settings
from django.contrib.contenttypes.fields import GenericRelation
from django.utils import timezone
from core.mixins.procurement import ProcurementTargetMixin
from core.models_legacy import SearchMixin
import uuid
from decimal import Decimal


# ============================================
# 1. RICHIESTA TRASPORTO (Principale)
# ============================================

class RichiestaTrasporto(ProcurementTargetMixin, SearchMixin, models.Model):
    """
    Richiesta di trasporto merci.
    Supporta sia pacchi che camion completi.
    """

    # Identificazione
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    numero = models.CharField(max_length=50, unique=True, editable=False)  # TRS-2026-001
    titolo = models.CharField(max_length=200, verbose_name="Titolo")
    descrizione = models.TextField(blank=True, verbose_name="Descrizione")

    # Tipo trasporto
    TIPO_CHOICES = [
        ('PACCO', 'Pacco/Colli (Corriere Express)'),
        ('LTL', 'Carico Parziale (LTL - Groupage)'),
        ('FTL', 'Camion Completo (FTL - Dedicato)'),
        ('SPECIALE', 'Trasporto Speciale'),
    ]
    tipo_trasporto = models.CharField(
        max_length=20,
        choices=TIPO_CHOICES,
        verbose_name="Tipo Trasporto"
    )

    # Stato workflow (simile a preventivi)
    STATO_CHOICES = [
        ('BOZZA', 'Bozza'),
        ('RICHIESTA_INVIATA', 'Richiesta Inviata'),
        ('OFFERTE_RICEVUTE', 'Offerte Ricevute'),
        ('IN_VALUTAZIONE', 'In Valutazione'),
        ('APPROVATA', 'Approvata'),
        ('CONFERMATA', 'Confermata'),
        ('IN_CORSO', 'Trasporto in Corso'),
        ('CONSEGNATO', 'Consegnato'),
        ('ANNULLATA', 'Annullata'),
    ]
    stato = models.CharField(
        max_length=30,
        choices=STATO_CHOICES,
        default='BOZZA',
        verbose_name="Stato"
    )

    # Priorità
    PRIORITA_CHOICES = [
        ('BASSA', 'Bassa'),
        ('NORMALE', 'Normale'),
        ('ALTA', 'Alta'),
        ('URGENTE', 'Urgente'),
    ]
    priorita = models.CharField(
        max_length=10,
        choices=PRIORITA_CHOICES,
        default='NORMALE',
        verbose_name="Priorità"
    )

    # Percorso - RITIRO
    indirizzo_ritiro = models.TextField(verbose_name="Indirizzo Ritiro")
    cap_ritiro = models.CharField(max_length=10, verbose_name="CAP Ritiro")
    citta_ritiro = models.CharField(max_length=100, verbose_name="Città Ritiro")
    provincia_ritiro = models.CharField(max_length=2, verbose_name="Provincia Ritiro")
    nazione_ritiro = models.CharField(max_length=2, default='IT', verbose_name="Nazione Ritiro")

    # Percorso - CONSEGNA
    indirizzo_consegna = models.TextField(verbose_name="Indirizzo Consegna")
    cap_consegna = models.CharField(max_length=10, verbose_name="CAP Consegna")
    citta_consegna = models.CharField(max_length=100, verbose_name="Città Consegna")
    provincia_consegna = models.CharField(max_length=2, verbose_name="Provincia Consegna")
    nazione_consegna = models.CharField(max_length=2, default='IT', verbose_name="Nazione Consegna")

    # Coordinate (per calcolo distanza)
    lat_ritiro = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        null=True,
        blank=True,
        verbose_name="Latitudine Ritiro"
    )
    lon_ritiro = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        null=True,
        blank=True,
        verbose_name="Longitudine Ritiro"
    )
    lat_consegna = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        null=True,
        blank=True,
        verbose_name="Latitudine Consegna"
    )
    lon_consegna = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        null=True,
        blank=True,
        verbose_name="Longitudine Consegna"
    )
    distanza_km = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="Distanza (km)"
    )  # Calcolata automaticamente

    # Date e orari - RITIRO
    data_ritiro_richiesta = models.DateField(verbose_name="Data Ritiro Richiesta")
    ora_ritiro_dalle = models.TimeField(null=True, blank=True, verbose_name="Ora Ritiro Dalle")
    ora_ritiro_alle = models.TimeField(null=True, blank=True, verbose_name="Ora Ritiro Alle")

    # Date e orari - CONSEGNA
    data_consegna_richiesta = models.DateField(verbose_name="Data Consegna Richiesta")
    ora_consegna_dalle = models.TimeField(null=True, blank=True, verbose_name="Ora Consegna Dalle")
    ora_consegna_alle = models.TimeField(null=True, blank=True, verbose_name="Ora Consegna Alle")

    # Merci - Caratteristiche generali
    tipo_merce = models.CharField(
        max_length=200,
        verbose_name="Tipo Merce",
        help_text="Es: Mobili, Elettronica, Alimentari, etc."
    )
    valore_merce = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Valore Merce"
    )
    valuta = models.CharField(max_length=3, default='EUR', verbose_name="Valuta")

    # Flags speciali
    merce_fragile = models.BooleanField(default=False, verbose_name="Merce Fragile")
    merce_deperibile = models.BooleanField(default=False, verbose_name="Merce Deperibile")
    merce_pericolosa = models.BooleanField(default=False, verbose_name="Merce Pericolosa (ADR)")
    codice_adr = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Codice ADR",
        help_text="Es: UN1203 per benzina"
    )

    temperatura_controllata = models.BooleanField(
        default=False,
        verbose_name="Temperatura Controllata"
    )
    temperatura_min = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="Temperatura Min (°C)"
    )
    temperatura_max = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="Temperatura Max (°C)"
    )

    # Assicurazione
    assicurazione_richiesta = models.BooleanField(
        default=False,
        verbose_name="Assicurazione Richiesta"
    )
    massimale_assicurazione = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Massimale Assicurazione"
    )

    # Servizi aggiuntivi
    scarico_a_piano = models.BooleanField(default=False, verbose_name="Scarico a Piano")
    numero_piano = models.IntegerField(null=True, blank=True, verbose_name="Numero Piano")
    presenza_montacarichi = models.BooleanField(default=False, verbose_name="Presenza Montacarichi")

    # Tracking
    tracking_richiesto = models.BooleanField(default=True, verbose_name="Tracking Richiesto")
    packing_list_richiesto = models.BooleanField(default=False, verbose_name="Packing List Richiesto")

    # Budget
    budget_massimo = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Budget Massimo"
    )

    # Workflow (come preventivi)
    richiedente = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='trasporti_richiesti',
        verbose_name="Richiedente"
    )
    operatore = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='trasporti_gestiti',
        verbose_name="Operatore"
    )
    approvatore = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='trasporti_approvati',
        verbose_name="Approvatore"
    )

    # Fornitori/Trasportatori
    trasportatori = models.ManyToManyField(
        'anagrafica.Fornitore',
        through='TrasportatoreOfferta',
        blank=True,
        verbose_name="Trasportatori"
    )
    offerta_approvata = models.ForeignKey(
        'OffertaTrasporto',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='+',
        verbose_name="Offerta Approvata"
    )

    # Date workflow
    data_creazione = models.DateTimeField(auto_now_add=True, verbose_name="Data Creazione")
    data_invio_richiesta = models.DateTimeField(null=True, blank=True, verbose_name="Data Invio Richiesta")
    data_valutazione = models.DateTimeField(null=True, blank=True, verbose_name="Data Valutazione")
    data_approvazione = models.DateTimeField(null=True, blank=True, verbose_name="Data Approvazione")
    data_conferma = models.DateTimeField(null=True, blank=True, verbose_name="Data Conferma")
    data_ritiro_effettivo = models.DateTimeField(null=True, blank=True, verbose_name="Data Ritiro Effettivo")
    data_consegna_effettiva = models.DateTimeField(null=True, blank=True, verbose_name="Data Consegna Effettiva")

    # Note
    note_interne = models.TextField(blank=True, verbose_name="Note Interne")
    note_ritiro = models.TextField(
        blank=True,
        verbose_name="Note Ritiro",
        help_text="Es: Suonare al citofono Rossi, accesso dal retro"
    )
    note_consegna = models.TextField(
        blank=True,
        verbose_name="Note Consegna",
        help_text="Es: Chiamare prima della consegna"
    )

    # Allegati (CMR, packing list, etc.)
    allegati = GenericRelation('core.Allegato')

    class Meta:
        verbose_name = "Richiesta Trasporto"
        verbose_name_plural = "Richieste Trasporto"
        ordering = ['-data_creazione']

    def __str__(self):
        return f"{self.numero} - {self.titolo}"

    @classmethod
    def get_search_fields(cls):
        """Campi ricercabili nella ricerca globale"""
        return ['numero', 'titolo', 'citta_ritiro', 'citta_consegna', 'tipo_merce']

    def get_search_result_display(self):
        """Testo visualizzato nei risultati di ricerca"""
        return f"{self.numero} - {self.titolo} ({self.citta_ritiro} → {self.citta_consegna})"

    def get_absolute_url(self):
        """URL per navigare al dettaglio della richiesta trasporto"""
        from django.urls import reverse
        return reverse('trasporti:richiesta_detail', kwargs={'pk': self.pk})

    def save(self, *args, **kwargs):
        # Genera numero automaticamente
        if not self.numero:
            self.numero = self.generate_numero()
        super().save(*args, **kwargs)

    @classmethod
    def generate_numero(cls):
        """Genera numero progressivo TRS-YYYY-NNN"""
        from django.db.models import Max
        import datetime

        anno_corrente = datetime.date.today().year
        prefix = f"TRS-{anno_corrente}-"

        # Trova ultimo numero dell'anno
        ultima = cls.objects.filter(numero__startswith=prefix).aggregate(Max('numero'))
        ultimo_numero = ultima['numero__max']

        if ultimo_numero:
            # Estrae numero progressivo
            ultimo_progressivo = int(ultimo_numero.split('-')[-1])
            nuovo_progressivo = ultimo_progressivo + 1
        else:
            nuovo_progressivo = 1

        return f"{prefix}{nuovo_progressivo:03d}"

    @property
    def peso_totale_kg(self):
        """Peso totale di tutti i colli"""
        totale = self.colli.aggregate(
            totale=models.Sum(models.F('peso_kg') * models.F('quantita'))
        )['totale']
        return totale or Decimal('0.00')

    @property
    def volume_totale_m3(self):
        """Volume totale di tutti i colli"""
        totale = self.colli.aggregate(
            totale=models.Sum(models.F('volume_m3') * models.F('quantita'))
        )['totale']
        return totale or Decimal('0.0000')

    @property
    def numero_colli_totali(self):
        """Numero totale colli"""
        totale = self.colli.aggregate(models.Sum('quantita'))['quantita__sum']
        return totale or 0

    @property
    def pallet_totali(self):
        """Pallet totali"""
        totale = self.colli.filter(tipo='PALLET').aggregate(models.Sum('quantita'))['quantita__sum']
        return totale or 0

    @property
    def offerte_totali(self):
        """Numero offerte ricevute"""
        return self.offerte.count()

    @property
    def offerte_valide(self):
        """Numero offerte non scadute"""
        return self.offerte.filter(
            models.Q(data_scadenza_offerta__isnull=True) |
            models.Q(data_scadenza_offerta__gte=timezone.now().date())
        ).count()

    @property
    def percorso_completo(self):
        """Ritorna stringa percorso completo"""
        return f"{self.citta_ritiro} ({self.provincia_ritiro}) → {self.citta_consegna} ({self.provincia_consegna})"

    @property
    def ha_allegati(self):
        """Verifica se la richiesta ha allegati"""
        return self.allegati.exists()

    @property
    def conta_allegati(self):
        """Conta il numero di allegati"""
        return self.allegati.count()


# ============================================
# 2. COLLO (Dettaglio Merci)
# ============================================

class Collo(models.Model):
    """
    Singolo collo o gruppo di colli identici.
    Supporta dimensioni, peso, tipo imballaggio.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    richiesta = models.ForeignKey(
        RichiestaTrasporto,
        on_delete=models.CASCADE,
        related_name='colli',
        verbose_name="Richiesta"
    )

    # Quantità
    quantita = models.IntegerField(default=1, verbose_name="Quantità")  # N colli identici

    # Tipo imballaggio
    TIPO_CHOICES = [
        ('SCATOLA', 'Scatola'),
        ('PALLET', 'Pallet'),
        ('BUSTA', 'Busta'),
        ('CILINDRO', 'Cilindro/Tubo'),
        ('CASSA', 'Cassa di legno'),
        ('SACCO', 'Sacco'),
        ('ALTRO', 'Altro'),
    ]
    tipo = models.CharField(
        max_length=20,
        choices=TIPO_CHOICES,
        default='SCATOLA',
        verbose_name="Tipo Imballaggio"
    )

    # Dimensioni (singolo collo)
    lunghezza_cm = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        verbose_name="Lunghezza (cm)"
    )
    larghezza_cm = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        verbose_name="Larghezza (cm)"
    )
    altezza_cm = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        verbose_name="Altezza (cm)"
    )

    # Peso (singolo collo)
    peso_kg = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        verbose_name="Peso (kg)"
    )

    # Volume calcolato (singolo collo)
    volume_m3 = models.DecimalField(
        max_digits=8,
        decimal_places=4,
        editable=False,
        verbose_name="Volume (m³)"
    )

    # Descrizione contenuto
    descrizione = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Descrizione Contenuto"
    )

    # Flags
    fragile = models.BooleanField(default=False, verbose_name="Fragile")
    stackable = models.BooleanField(default=True, verbose_name="Impilabile")  # Impilabile

    ordine = models.IntegerField(default=0, verbose_name="Ordine")  # Per ordinamento nella lista

    class Meta:
        verbose_name = "Collo"
        verbose_name_plural = "Colli"
        ordering = ['ordine', 'id']

    def save(self, *args, **kwargs):
        # Calcola volume automaticamente (L x W x H / 1.000.000)
        self.volume_m3 = (
            self.lunghezza_cm * self.larghezza_cm * self.altezza_cm
        ) / Decimal('1000000')
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.quantita}x {self.tipo} ({self.peso_kg}kg)"

    @property
    def peso_totale(self):
        """Peso totale (peso singolo * quantità)"""
        return self.peso_kg * self.quantita

    @property
    def volume_totale(self):
        """Volume totale (volume singolo * quantità)"""
        return self.volume_m3 * self.quantita


# ============================================
# 3. TRASPORTATORE-OFFERTA (Through Model)
# ============================================

class TrasportatoreOfferta(models.Model):
    """
    Collegamento tra RichiestaTrasporto e Fornitore (trasportatore).
    Traccia email, risposte, solleciti.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    richiesta = models.ForeignKey(
        RichiestaTrasporto,
        on_delete=models.CASCADE,
        verbose_name="Richiesta"
    )
    trasportatore = models.ForeignKey(
        'anagrafica.Fornitore',
        on_delete=models.CASCADE,
        verbose_name="Trasportatore"
    )

    # Tracking email
    email_inviata = models.BooleanField(default=False, verbose_name="Email Inviata")
    data_invio = models.DateTimeField(null=True, blank=True, verbose_name="Data Invio")
    email_letta = models.BooleanField(default=False, verbose_name="Email Letta")
    data_lettura = models.DateTimeField(null=True, blank=True, verbose_name="Data Lettura")

    # Tracking risposta
    ha_risposto = models.BooleanField(default=False, verbose_name="Ha Risposto")
    data_risposta = models.DateTimeField(null=True, blank=True, verbose_name="Data Risposta")

    # Solleciti
    numero_solleciti = models.IntegerField(default=0, verbose_name="Numero Solleciti")
    data_ultimo_sollecito = models.DateTimeField(null=True, blank=True, verbose_name="Data Ultimo Sollecito")

    # Token accesso sicuro
    token_accesso = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    # Note
    note_trasportatore = models.TextField(blank=True, verbose_name="Note Trasportatore")

    class Meta:
        unique_together = ['richiesta', 'trasportatore']
        verbose_name = "Trasportatore Offerta"
        verbose_name_plural = "Trasportatori Offerte"

    def __str__(self):
        return f"{self.trasportatore} - {self.richiesta.numero}"

    @property
    def giorni_senza_risposta(self):
        """Giorni senza risposta dal primo invio"""
        if not self.data_invio or self.ha_risposto:
            return 0
        delta = timezone.now() - self.data_invio
        return delta.days


# ============================================
# 4. OFFERTA TRASPORTO (Preventivo)
# ============================================

class OffertaTrasporto(models.Model):
    """
    Offerta ricevuta da un trasportatore.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    richiesta = models.ForeignKey(
        RichiestaTrasporto,
        on_delete=models.CASCADE,
        related_name='offerte',
        verbose_name="Richiesta"
    )
    trasportatore = models.ForeignKey(
        'anagrafica.Fornitore',
        on_delete=models.PROTECT,
        verbose_name="Trasportatore"
    )

    # Identificazione offerta
    numero_offerta = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Numero Offerta",
        help_text="Numero assegnato dal trasportatore"
    )

    # Prezzi
    importo_trasporto = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Importo Trasporto"
    )
    importo_assicurazione = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Importo Assicurazione"
    )
    importo_pedaggi = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Importo Pedaggi"
    )
    importo_extra = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Importo Extra"
    )
    descrizione_extra = models.TextField(
        blank=True,
        verbose_name="Descrizione Extra"
    )

    importo_totale = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Importo Totale"
    )
    valuta = models.CharField(max_length=3, default='EUR', verbose_name="Valuta")

    # Prezzi unitari (opzionali)
    prezzo_per_km = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Prezzo per km"
    )
    prezzo_per_kg = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Prezzo per kg"
    )

    # Tempi - RITIRO
    data_ritiro_proposta = models.DateField(verbose_name="Data Ritiro Proposta")
    ora_ritiro_dalle = models.TimeField(null=True, blank=True, verbose_name="Ora Ritiro Dalle")
    ora_ritiro_alle = models.TimeField(null=True, blank=True, verbose_name="Ora Ritiro Alle")

    # Tempi - CONSEGNA
    data_consegna_prevista = models.DateField(verbose_name="Data Consegna Prevista")
    ora_consegna_dalle = models.TimeField(null=True, blank=True, verbose_name="Ora Consegna Dalle")
    ora_consegna_alle = models.TimeField(null=True, blank=True, verbose_name="Ora Consegna Alle")

    tempo_transito_giorni = models.IntegerField(verbose_name="Tempo Transito (giorni)")

    # Mezzo e conducente
    TIPO_MEZZO_CHOICES = [
        ('FURGONE', 'Furgone'),
        ('CAMION_CENTINATO', 'Camion Centinato'),
        ('CAMION_FRIGO', 'Camion Frigo'),
        ('CAMION_SPONDA', 'Camion con Sponda'),
        ('CAMION_PIANALE', 'Camion Pianale'),
        ('BILICO', 'Bilico/Articolato'),
        ('ALTRO', 'Altro'),
    ]
    tipo_mezzo = models.CharField(
        max_length=30,
        choices=TIPO_MEZZO_CHOICES,
        blank=True,
        verbose_name="Tipo Mezzo"
    )
    targa_mezzo = models.CharField(max_length=20, blank=True, verbose_name="Targa Mezzo")
    capienza_kg = models.IntegerField(null=True, blank=True, verbose_name="Capienza (kg)")
    capienza_m3 = models.IntegerField(null=True, blank=True, verbose_name="Capienza (m³)")

    conducente_nome = models.CharField(max_length=200, blank=True, verbose_name="Nome Conducente")
    conducente_telefono = models.CharField(max_length=50, blank=True, verbose_name="Telefono Conducente")

    # Condizioni commerciali
    termini_pagamento = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Termini Pagamento",
        help_text="Es: 30gg DFFM"
    )
    validita_offerta_giorni = models.IntegerField(
        default=7,
        verbose_name="Validità Offerta (giorni)"
    )

    # Servizi inclusi
    tracking_incluso = models.BooleanField(default=False, verbose_name="Tracking Incluso")
    assicurazione_inclusa = models.BooleanField(default=False, verbose_name="Assicurazione Inclusa")
    scarico_a_piano_incluso = models.BooleanField(default=False, verbose_name="Scarico a Piano Incluso")

    # Tracking (se approvata)
    numero_tracking = models.CharField(max_length=200, blank=True, verbose_name="Numero Tracking")
    link_tracking = models.URLField(blank=True, verbose_name="Link Tracking")

    # File
    file_offerta = models.FileField(
        upload_to='trasporti/offerte/',
        blank=True,
        verbose_name="File Offerta"
    )

    # Note
    note_tecniche = models.TextField(blank=True, verbose_name="Note Tecniche")
    note_commerciali = models.TextField(blank=True, verbose_name="Note Commerciali")

    # Workflow
    data_ricevimento = models.DateTimeField(auto_now_add=True, verbose_name="Data Ricevimento")
    data_scadenza_offerta = models.DateField(null=True, blank=True, verbose_name="Data Scadenza Offerta")
    confermata = models.BooleanField(default=False, verbose_name="Confermata")
    data_conferma = models.DateTimeField(null=True, blank=True, verbose_name="Data Conferma")
    operatore_inserimento = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Operatore Inserimento"
    )

    # Collegamento ordine (se implementato in acquisti)
    numero_ordine = models.CharField(max_length=50, blank=True, verbose_name="Numero Ordine")

    # Allegati
    allegati = GenericRelation('core.Allegato')

    class Meta:
        unique_together = ['richiesta', 'trasportatore']
        verbose_name = "Offerta Trasporto"
        verbose_name_plural = "Offerte Trasporto"
        ordering = ['importo_totale']  # Ordina per prezzo

    def __str__(self):
        return f"{self.trasportatore} - €{self.importo_totale}"

    def save(self, *args, **kwargs):
        # Calcola data scadenza se non impostata
        if not self.data_scadenza_offerta and self.validita_offerta_giorni:
            from datetime import timedelta
            self.data_scadenza_offerta = (
                timezone.now().date() + timedelta(days=self.validita_offerta_giorni)
            )
        super().save(*args, **kwargs)

    @property
    def is_scaduta(self):
        """Verifica se offerta è scaduta"""
        if not self.data_scadenza_offerta:
            return False
        return self.data_scadenza_offerta < timezone.now().date()

    @property
    def giorni_validita_rimanenti(self):
        """Giorni di validità rimanenti"""
        if not self.data_scadenza_offerta:
            return None
        delta = self.data_scadenza_offerta - timezone.now().date()
        return max(0, delta.days)

    @property
    def ha_allegati(self):
        """Verifica se l'offerta ha allegati"""
        return self.allegati.exists()

    @property
    def conta_allegati(self):
        """Conta il numero di allegati"""
        return self.allegati.count()


# ============================================
# 5. PARAMETRO VALUTAZIONE (Opzionale)
# ============================================

class ParametroValutazione(models.Model):
    """
    Parametri per confronto offerte (come in preventivi).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    offerta = models.ForeignKey(
        OffertaTrasporto,
        on_delete=models.CASCADE,
        related_name='parametri',
        verbose_name="Offerta"
    )

    descrizione = models.CharField(
        max_length=200,
        verbose_name="Descrizione",
        help_text="Es: Affidabilità, Recensioni, Esperienza"
    )
    valore = models.CharField(max_length=200, verbose_name="Valore")
    ordine = models.IntegerField(default=0, verbose_name="Ordine")

    creato_da = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='parametri_trasporti',
        verbose_name="Creato Da"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creato il")

    class Meta:
        verbose_name = "Parametro Valutazione"
        verbose_name_plural = "Parametri Valutazione"
        ordering = ['ordine']

    def __str__(self):
        return f"{self.descrizione}: {self.valore}"


# ============================================
# 6. INTEGRAZIONE API (Configurazione)
# ============================================

class ConfigurazioneAPITrasporto(models.Model):
    """
    Configurazione API per corrieri e broker.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    PROVIDER_CHOICES = [
        ('BRT', 'BRT'),
        ('GLS', 'GLS'),
        ('DHL', 'DHL Express'),
        ('UPS', 'UPS'),
        ('FEDEX', 'FedEx'),
        ('TNT', 'TNT'),
        ('TIMOCOM', 'TimoCom'),
        ('TRANSEU', 'Trans.eu'),
        ('WTRANSNET', 'Wtransnet'),
        ('GOOGLE_MAPS', 'Google Maps API'),
    ]
    provider = models.CharField(
        max_length=50,
        choices=PROVIDER_CHOICES,
        unique=True,
        verbose_name="Provider"
    )

    api_key = models.CharField(max_length=500, verbose_name="API Key")
    api_secret = models.CharField(max_length=500, blank=True, verbose_name="API Secret")
    api_endpoint = models.URLField(verbose_name="API Endpoint")

    attivo = models.BooleanField(default=True, verbose_name="Attivo")

    # Configurazioni specifiche (JSON)
    configurazione_extra = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Configurazione Extra"
    )

    ultimo_test = models.DateTimeField(null=True, blank=True, verbose_name="Ultimo Test")
    ultimo_test_successo = models.BooleanField(default=False, verbose_name="Ultimo Test Successo")

    class Meta:
        verbose_name = "Configurazione API Trasporto"
        verbose_name_plural = "Configurazioni API Trasporto"

    def __str__(self):
        status = 'Attivo' if self.attivo else 'Disattivo'
        return f"{self.provider} ({status})"


# ============================================
# 7. LOG TRACKING
# ============================================

class EventoTracking(models.Model):
    """
    Eventi di tracking della spedizione.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    offerta = models.ForeignKey(
        OffertaTrasporto,
        on_delete=models.CASCADE,
        related_name='eventi_tracking',
        verbose_name="Offerta"
    )

    TIPO_EVENTO_CHOICES = [
        ('RICHIESTA_INVIATA', 'Richiesta Inviata'),
        ('OFFERTA_RICEVUTA', 'Offerta Ricevuta'),
        ('OFFERTA_ACCETTATA', 'Offerta Accettata'),
        ('IN_CARICAMENTO', 'In Caricamento'),
        ('RITIRATO', 'Ritirato'),
        ('IN_TRANSITO', 'In Transito'),
        ('IN_CONSEGNA', 'In Consegna'),
        ('CONSEGNATO', 'Consegnato'),
        ('PROBLEMI', 'Problemi/Ritardo'),
        ('ANNULLATO', 'Annullato'),
    ]
    tipo_evento = models.CharField(
        max_length=50,
        choices=TIPO_EVENTO_CHOICES,
        verbose_name="Tipo Evento"
    )

    data_evento = models.DateTimeField(auto_now_add=True, verbose_name="Data Evento")
    localita = models.CharField(max_length=200, blank=True, verbose_name="Località")

    nota = models.TextField(blank=True, verbose_name="Nota")

    # Se da API esterna
    source_api = models.CharField(max_length=50, blank=True, verbose_name="Source API")
    external_id = models.CharField(max_length=200, blank=True, verbose_name="External ID")

    class Meta:
        verbose_name = "Evento Tracking"
        verbose_name_plural = "Eventi Tracking"
        ordering = ['-data_evento']

    def __str__(self):
        return f"{self.tipo_evento} - {self.data_evento.strftime('%d/%m/%Y %H:%M')}"
