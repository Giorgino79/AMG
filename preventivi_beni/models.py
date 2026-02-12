"""
Models for Preventivi Beni/Servizi app
======================================

Sistema completo di gestione preventivi per beni e servizi.
Workflow identico all'app trasporti:
BOZZA → RICHIESTA_INVIATA → OFFERTE_RICEVUTE → IN_VALUTAZIONE → APPROVATA → CONFERMATA → ORDINATO
"""

from django.db import models
from django.conf import settings
from django.contrib.contenttypes.fields import GenericRelation
from django.utils import timezone
from core.mixins.procurement import ProcurementTargetMixin
import uuid
from decimal import Decimal


# ============================================
# 1. RICHIESTA PREVENTIVO (Principale)
# ============================================

class RichiestaPreventivo(ProcurementTargetMixin, models.Model):
    """
    Richiesta di preventivo per beni o servizi.
    """

    # Identificazione
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    numero = models.CharField(max_length=50, unique=True, editable=False)  # PBN-2026-001
    titolo = models.CharField(max_length=200, verbose_name="Titolo")
    descrizione = models.TextField(blank=True, verbose_name="Descrizione")

    # Tipo richiesta
    TIPO_CHOICES = [
        ('BENI', 'Beni/Materiali'),
        ('SERVIZI', 'Servizi'),
        ('MISTO', 'Beni e Servizi'),
        ('MANUTENZIONE', 'Manutenzione'),
        ('CONSULENZA', 'Consulenza'),
    ]
    tipo_richiesta = models.CharField(
        max_length=20,
        choices=TIPO_CHOICES,
        default='BENI',
        verbose_name="Tipo Richiesta"
    )

    # Stato workflow (identico a trasporti)
    STATO_CHOICES = [
        ('BOZZA', 'Bozza'),
        ('RICHIESTA_INVIATA', 'Richiesta Inviata'),
        ('OFFERTE_RICEVUTE', 'Offerte Ricevute'),
        ('IN_VALUTAZIONE', 'In Valutazione'),
        ('APPROVATA', 'Approvata'),
        ('CONFERMATA', 'Confermata'),
        ('ORDINATO', 'Ordine Emesso'),
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

    # Categoria merceologica
    CATEGORIA_CHOICES = [
        ('MATERIALI', 'Materiali da costruzione'),
        ('FERRAMENTA', 'Ferramenta'),
        ('ELETTRICO', 'Materiale elettrico'),
        ('IDRAULICA', 'Materiale idraulico'),
        ('ATTREZZATURE', 'Attrezzature e macchinari'),
        ('UFFICIO', 'Materiale ufficio'),
        ('IT', 'IT e informatica'),
        ('SERVIZI_TECNICI', 'Servizi tecnici'),
        ('SERVIZI_PROF', 'Servizi professionali'),
        ('MANUTENZIONE', 'Manutenzione'),
        ('ALTRO', 'Altro'),
    ]
    categoria = models.CharField(
        max_length=30,
        choices=CATEGORIA_CHOICES,
        blank=True,
        verbose_name="Categoria"
    )

    # Luogo consegna/esecuzione
    luogo_consegna = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Luogo Consegna/Esecuzione"
    )
    indirizzo_consegna = models.TextField(
        blank=True,
        verbose_name="Indirizzo Completo"
    )

    # Date richieste
    data_consegna_richiesta = models.DateField(
        null=True,
        blank=True,
        verbose_name="Data Consegna Richiesta"
    )
    data_scadenza_offerte = models.DateField(
        null=True,
        blank=True,
        verbose_name="Scadenza Ricezione Offerte"
    )

    # Budget
    budget_massimo = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Budget Massimo"
    )
    valuta = models.CharField(max_length=3, default='EUR', verbose_name="Valuta")

    # Condizioni richieste
    CONDIZIONI_PAGAMENTO_CHOICES = [
        ('', '-- Non specificato --'),
        ('CONTANTI', 'Contanti'),
        ('30GG', '30 giorni'),
        ('60GG', '60 giorni'),
        ('90GG', '90 giorni'),
        ('30GG_DFFM', '30 giorni DFFM'),
        ('60GG_DFFM', '60 giorni DFFM'),
        ('ANTICIPATO', 'Pagamento anticipato'),
    ]
    condizioni_pagamento_richieste = models.CharField(
        max_length=20,
        choices=CONDIZIONI_PAGAMENTO_CHOICES,
        blank=True,
        verbose_name="Condizioni Pagamento Richieste"
    )

    # Workflow (come trasporti)
    richiedente = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='preventivi_beni_richiesti',
        verbose_name="Richiedente"
    )
    operatore = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='preventivi_beni_gestiti',
        verbose_name="Operatore"
    )
    approvatore = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='preventivi_beni_approvati',
        verbose_name="Approvatore"
    )

    # Fornitori
    fornitori = models.ManyToManyField(
        'anagrafica.Fornitore',
        through='FornitorePreventivo',
        blank=True,
        verbose_name="Fornitori"
    )
    offerta_approvata = models.ForeignKey(
        'Offerta',
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

    # Note
    note_interne = models.TextField(blank=True, verbose_name="Note Interne")
    note_per_fornitori = models.TextField(
        blank=True,
        verbose_name="Note per Fornitori",
        help_text="Queste note saranno visibili ai fornitori nella richiesta"
    )

    # Automezzo collegato (opzionale)
    automezzo = models.ForeignKey(
        'automezzi.Automezzo',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='richieste_preventivo',
        verbose_name="Automezzo",
        help_text="Se selezionato, il libretto fronte verrà allegato alla richiesta"
    )

    # Allegati (specifiche tecniche, disegni, etc.)
    allegati = GenericRelation('core.Allegato')

    class Meta:
        verbose_name = "Richiesta Preventivo Beni"
        verbose_name_plural = "Richieste Preventivi Beni"
        ordering = ['-data_creazione']

    def __str__(self):
        return f"{self.numero} - {self.titolo}"

    def save(self, *args, **kwargs):
        # Genera numero automaticamente
        if not self.numero:
            self.numero = self.generate_numero()
        super().save(*args, **kwargs)

    @classmethod
    def generate_numero(cls):
        """Genera numero progressivo PBN-YYYY-NNN"""
        from django.db.models import Max
        import datetime

        anno_corrente = datetime.date.today().year
        prefix = f"PBN-{anno_corrente}-"

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
    def importo_totale_stimato(self):
        """Importo totale stimato dalle voci"""
        totale = self.voci.aggregate(
            totale=models.Sum(models.F('prezzo_unitario_stimato') * models.F('quantita'))
        )['totale']
        return totale or Decimal('0.00')

    @property
    def numero_voci(self):
        """Numero totale voci"""
        return self.voci.count()

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
    def fornitori_contattati(self):
        """Numero fornitori a cui è stata inviata la richiesta"""
        return self.fornitorepreventivo_set.filter(email_inviata=True).count()

    @property
    def ha_allegati(self):
        """Verifica se la richiesta ha allegati"""
        return self.allegati.exists()

    @property
    def conta_allegati(self):
        """Conta il numero di allegati"""
        return self.allegati.count()

    @property
    def fornitori_risposto(self):
        """Numero fornitori che hanno risposto"""
        return self.fornitorepreventivo_set.filter(ha_risposto=True).count()


# ============================================
# 2. VOCE PREVENTIVO (Dettaglio Richiesta)
# ============================================

class VocePreventivo(models.Model):
    """
    Singola voce/riga della richiesta di preventivo.
    Rappresenta un bene o servizio richiesto.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    richiesta = models.ForeignKey(
        RichiestaPreventivo,
        on_delete=models.CASCADE,
        related_name='voci',
        verbose_name="Richiesta"
    )

    # Descrizione articolo/servizio
    codice = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Codice Articolo",
        help_text="Codice interno o riferimento"
    )
    descrizione = models.TextField(verbose_name="Descrizione")

    # Unità di misura
    UNITA_CHOICES = [
        ('PZ', 'Pezzi'),
        ('NR', 'Numero'),
        ('KG', 'Kg'),
        ('MT', 'Metri'),
        ('MQ', 'Metri quadri'),
        ('MC', 'Metri cubi'),
        ('LT', 'Litri'),
        ('H', 'Ore'),
        ('GG', 'Giorni'),
        ('CORPO', 'A corpo'),
        ('CONF', 'Confezione'),
        ('CF', 'Cartone/Fardello'),
        ('PL', 'Pallet'),
    ]
    unita_misura = models.CharField(
        max_length=10,
        choices=UNITA_CHOICES,
        default='PZ',
        verbose_name="Unità di Misura"
    )

    # Quantità
    quantita = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Quantità"
    )

    # Prezzo stimato (opzionale, per budget)
    prezzo_unitario_stimato = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Prezzo Unitario Stimato"
    )

    # Specifiche tecniche
    marca_richiesta = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Marca Richiesta",
        help_text="Marca preferita o equivalente"
    )
    modello_richiesto = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Modello Richiesto"
    )

    # Note aggiuntive per questa voce
    note = models.TextField(
        blank=True,
        verbose_name="Note",
        help_text="Specifiche tecniche, requisiti particolari"
    )

    # Obbligatorietà
    obbligatoria = models.BooleanField(
        default=True,
        verbose_name="Voce Obbligatoria",
        help_text="Se deselezionato, il fornitore può omettere questa voce"
    )

    ordine = models.IntegerField(default=0, verbose_name="Ordine")

    class Meta:
        verbose_name = "Voce Preventivo"
        verbose_name_plural = "Voci Preventivo"
        ordering = ['ordine', 'id']

    def __str__(self):
        return f"{self.quantita} {self.unita_misura} - {self.descrizione[:50]}"

    @property
    def importo_stimato(self):
        """Importo stimato (quantità * prezzo stimato)"""
        if self.prezzo_unitario_stimato:
            return self.quantita * self.prezzo_unitario_stimato
        return None


# ============================================
# 3. FORNITORE-PREVENTIVO (Through Model)
# ============================================

class FornitorePreventivo(models.Model):
    """
    Collegamento tra RichiestaPreventivo e Fornitore.
    Traccia email, risposte, solleciti.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    richiesta = models.ForeignKey(
        RichiestaPreventivo,
        on_delete=models.CASCADE,
        verbose_name="Richiesta"
    )
    fornitore = models.ForeignKey(
        'anagrafica.Fornitore',
        on_delete=models.CASCADE,
        verbose_name="Fornitore"
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

    # Token accesso sicuro (per link pubblico risposta)
    token_accesso = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    # Note
    note_fornitore = models.TextField(blank=True, verbose_name="Note Fornitore")

    class Meta:
        unique_together = ['richiesta', 'fornitore']
        verbose_name = "Fornitore Preventivo"
        verbose_name_plural = "Fornitori Preventivi"

    def __str__(self):
        return f"{self.fornitore} - {self.richiesta.numero}"

    @property
    def giorni_senza_risposta(self):
        """Giorni senza risposta dal primo invio"""
        if not self.data_invio or self.ha_risposto:
            return 0
        delta = timezone.now() - self.data_invio
        return delta.days


# ============================================
# 4. OFFERTA (Preventivo ricevuto)
# ============================================

class Offerta(models.Model):
    """
    Offerta/preventivo ricevuto da un fornitore.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    richiesta = models.ForeignKey(
        RichiestaPreventivo,
        on_delete=models.CASCADE,
        related_name='offerte',
        verbose_name="Richiesta"
    )
    fornitore = models.ForeignKey(
        'anagrafica.Fornitore',
        on_delete=models.PROTECT,
        verbose_name="Fornitore"
    )

    # Identificazione offerta
    numero_offerta = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Numero Offerta",
        help_text="Numero assegnato dal fornitore"
    )

    # Importi
    importo_merce = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Importo Merce/Servizi"
    )
    importo_trasporto = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Importo Trasporto"
    )
    importo_imballo = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Importo Imballo"
    )
    importo_installazione = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Importo Installazione"
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

    # Sconti
    sconto_percentuale = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name="Sconto %"
    )
    sconto_importo = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Sconto Importo"
    )

    importo_totale = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Importo Totale"
    )
    valuta = models.CharField(max_length=3, default='EUR', verbose_name="Valuta")

    # Tempi consegna
    tempo_consegna_giorni = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="Tempo Consegna (giorni)"
    )
    data_consegna_proposta = models.DateField(
        null=True,
        blank=True,
        verbose_name="Data Consegna Proposta"
    )
    note_consegna = models.TextField(
        blank=True,
        verbose_name="Note Consegna"
    )

    # Condizioni commerciali
    CONDIZIONI_PAGAMENTO_CHOICES = [
        ('', '-- Non specificato --'),
        ('CONTANTI', 'Contanti'),
        ('30GG', '30 giorni'),
        ('60GG', '60 giorni'),
        ('90GG', '90 giorni'),
        ('30GG_DFFM', '30 giorni DFFM'),
        ('60GG_DFFM', '60 giorni DFFM'),
        ('ANTICIPATO', 'Pagamento anticipato'),
    ]
    termini_pagamento = models.CharField(
        max_length=50,
        choices=CONDIZIONI_PAGAMENTO_CHOICES,
        blank=True,
        verbose_name="Termini Pagamento"
    )
    validita_offerta_giorni = models.IntegerField(
        default=30,
        verbose_name="Validità Offerta (giorni)"
    )

    # Garanzia
    garanzia_mesi = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="Garanzia (mesi)"
    )
    note_garanzia = models.TextField(
        blank=True,
        verbose_name="Note Garanzia"
    )

    # Servizi inclusi
    trasporto_incluso = models.BooleanField(default=False, verbose_name="Trasporto Incluso")
    installazione_inclusa = models.BooleanField(default=False, verbose_name="Installazione Inclusa")
    formazione_inclusa = models.BooleanField(default=False, verbose_name="Formazione Inclusa")

    # File
    file_offerta = models.FileField(
        upload_to='preventivi_beni/offerte/',
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

    # Collegamento ordine acquisto
    numero_ordine = models.CharField(max_length=50, blank=True, verbose_name="Numero Ordine")

    # Allegati
    allegati = GenericRelation('core.Allegato')

    class Meta:
        unique_together = ['richiesta', 'fornitore']
        verbose_name = "Offerta"
        verbose_name_plural = "Offerte"
        ordering = ['importo_totale']  # Ordina per prezzo

    def __str__(self):
        return f"{self.fornitore} - €{self.importo_totale}"

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
# 5. VOCE OFFERTA (Dettaglio offerta)
# ============================================

class VoceOfferta(models.Model):
    """
    Singola voce dell'offerta, corrispondente a una voce richiesta.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    offerta = models.ForeignKey(
        Offerta,
        on_delete=models.CASCADE,
        related_name='voci',
        verbose_name="Offerta"
    )
    voce_richiesta = models.ForeignKey(
        VocePreventivo,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Voce Richiesta",
        help_text="Collegamento alla voce originale della richiesta"
    )

    # Descrizione (può differire dalla richiesta)
    descrizione = models.TextField(verbose_name="Descrizione")

    # Marca/modello offerti
    marca = models.CharField(max_length=100, blank=True, verbose_name="Marca")
    modello = models.CharField(max_length=100, blank=True, verbose_name="Modello")
    codice_fornitore = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Codice Fornitore"
    )

    # Quantità e prezzo
    quantita = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Quantità"
    )
    unita_misura = models.CharField(max_length=10, default='PZ', verbose_name="U.M.")
    prezzo_unitario = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Prezzo Unitario"
    )
    sconto_riga = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name="Sconto %"
    )
    importo_riga = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Importo Riga"
    )

    # Note
    note = models.TextField(blank=True, verbose_name="Note")

    ordine = models.IntegerField(default=0, verbose_name="Ordine")

    class Meta:
        verbose_name = "Voce Offerta"
        verbose_name_plural = "Voci Offerta"
        ordering = ['ordine', 'id']

    def __str__(self):
        return f"{self.quantita} {self.unita_misura} - {self.descrizione[:50]}"

    def save(self, *args, **kwargs):
        # Calcola importo riga
        prezzo_scontato = self.prezzo_unitario * (1 - self.sconto_riga / 100)
        self.importo_riga = self.quantita * prezzo_scontato
        super().save(*args, **kwargs)


# ============================================
# 6. PARAMETRO VALUTAZIONE
# ============================================

class ParametroValutazione(models.Model):
    """
    Parametri per confronto offerte.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    offerta = models.ForeignKey(
        Offerta,
        on_delete=models.CASCADE,
        related_name='parametri',
        verbose_name="Offerta"
    )

    descrizione = models.CharField(
        max_length=200,
        verbose_name="Descrizione",
        help_text="Es: Tempo consegna, Garanzia, Assistenza"
    )
    valore = models.CharField(max_length=200, verbose_name="Valore")
    ordine = models.IntegerField(default=0, verbose_name="Ordine")

    creato_da = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='parametri_preventivi_beni',
        verbose_name="Creato Da"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creato il")

    class Meta:
        verbose_name = "Parametro Valutazione"
        verbose_name_plural = "Parametri Valutazione"
        ordering = ['ordine']

    def __str__(self):
        return f"{self.descrizione}: {self.valore}"
