from django.db import models
from django.conf import settings
from core.mixins import AllegatiMixin
from core.models_legacy import SearchMixin


def libretto_upload_path(instance, filename):
    return f"automezzi/libretti/{instance.targa}/{filename}"


def assicurazione_upload_path(instance, filename):
    return f"automezzi/assicurazioni/{instance.targa}/{filename}"


def scontrino_upload_path(instance, filename):
    return f"automezzi/rifornimenti/{instance.automezzo.targa}/scontrini/{filename}"


def allegati_manutenzione_path(instance, filename):
    return f"automezzi/manutenzioni/{instance.automezzo.targa}/allegati/{filename}"


def allegato_evento_path(instance, filename):
    return f"automezzi/eventi/{instance.automezzo.targa}/{filename}"


# Upload paths per Gruppi Elettrogeni
def manuale_gruppo_upload_path(instance, filename):
    return f"gruppi/manuali/{instance.matricola}/{filename}"


def certificato_gruppo_upload_path(instance, filename):
    return f"gruppi/certificati/{instance.matricola}/{filename}"


def allegati_manutenzione_gruppo_path(instance, filename):
    return f"gruppi/manutenzioni/{instance.gruppo.matricola}/allegati/{filename}"


def allegato_evento_gruppo_path(instance, filename):
    return f"gruppi/eventi/{instance.gruppo.matricola}/{filename}"


class Automezzo(AllegatiMixin, SearchMixin, models.Model):
    numero_mezzo = models.IntegerField(
        blank=True, null=True, help_text="Numero identificativo del mezzo"
    )
    targa = models.CharField(max_length=10, unique=True)
    marca = models.CharField(max_length=50)
    modello = models.CharField(max_length=50)
    anno_immatricolazione = models.PositiveIntegerField()
    chilometri_attuali = models.PositiveIntegerField(default=0)
    attivo = models.BooleanField(default=True)
    disponibile = models.BooleanField(default=True)
    bloccata = models.BooleanField(default=False)
    motivo_blocco = models.TextField(blank=True, null=True)
    libretto_fronte = models.FileField(
        upload_to=libretto_upload_path,
        blank=True,
        null=True,
        help_text="Fronte del libretto di circolazione",
    )
    libretto_retro = models.FileField(
        upload_to=libretto_upload_path,
        blank=True,
        null=True,
        help_text="Retro del libretto di circolazione",
    )
    assicurazione = models.FileField(
        upload_to=assicurazione_upload_path,
        blank=True,
        null=True,
        help_text="File della polizza assicurativa",
    )
    data_revisione = models.DateField(
        blank=True, null=True, help_text="Data ultima revisione"
    )
    assegnato_a = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="automezzi_assegnati",
    )
    carta_carburante = models.CharField(
        max_length=50,
        blank=True,
        help_text="Numero carta carburante associata al mezzo",
    )
    pin_carta_carburante = models.CharField(
        max_length=10,
        blank=True,
        help_text="PIN della carta carburante",
    )

    def __str__(self):
        return f"{self.targa} - {self.marca} {self.modello}"

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('automezzi:automezzo_detail', kwargs={'pk': self.pk})

    @classmethod
    def get_search_fields(cls):
        """Campi ricercabili nella ricerca globale"""
        return ['targa', 'marca', 'modello', 'carta_carburante']

    def get_search_result_display(self):
        """Testo visualizzato nei risultati di ricerca"""
        return f"{self.targa} - {self.marca} {self.modello}"

    @property
    def eta(self):
        from datetime import date

        return date.today().year - self.anno_immatricolazione

    def manutenzioni_count(self):
        return self.manutenzioni.count()

    def rifornimenti_count(self):
        return self.rifornimenti.count()

    def eventi_count(self):
        return self.eventi.count()


class Gruppo(AllegatiMixin, SearchMixin, models.Model):
    """Modello per gestire i gruppi elettrogeni"""

    TIPO_MOTORE_CHOICES = [
        ('diesel', 'Diesel'),
        ('benzina', 'Benzina'),
        ('gas', 'Gas'),
        ('ibrido', 'Ibrido'),
    ]

    TIPO_RAFFREDDAMENTO_CHOICES = [
        ('aria', 'Raffreddamento ad Aria'),
        ('acqua', 'Raffreddamento ad Acqua'),
    ]

    FREQUENZA_CHOICES = [
        ('50', '50 Hz'),
        ('60', '60 Hz'),
        ('50/60', '50/60 Hz'),
    ]

    # Identificazione
    numero_gruppo = models.IntegerField(
        blank=True, null=True, help_text="Numero identificativo del gruppo"
    )
    matricola = models.CharField(
        max_length=50, unique=True, help_text="Matricola/Seriale del gruppo elettrogeno"
    )
    marca = models.CharField(max_length=50)
    modello = models.CharField(max_length=50)
    anno_produzione = models.PositiveIntegerField()

    # Stato operativo
    attivo = models.BooleanField(default=True)
    disponibile = models.BooleanField(default=True)
    bloccato = models.BooleanField(default=False)
    motivo_blocco = models.TextField(blank=True, null=True)

    # Caratteristiche tecniche
    potenza_kva = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        help_text="Potenza apparente in kVA"
    )
    potenza_kw = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        help_text="Potenza attiva in kW"
    )
    tipo_motore = models.CharField(
        max_length=10,
        choices=TIPO_MOTORE_CHOICES,
        default='diesel'
    )
    cilindrata = models.PositiveIntegerField(
        blank=True, null=True, help_text="Cilindrata in cc"
    )
    numero_cilindri = models.PositiveIntegerField(
        blank=True, null=True
    )
    capacita_serbatoio = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Capacità serbatoio in litri"
    )
    consumo_orario = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Consumo medio orario in litri/ora"
    )
    tipo_raffreddamento = models.CharField(
        max_length=10,
        choices=TIPO_RAFFREDDAMENTO_CHOICES,
        default='aria'
    )
    tensione_uscita = models.CharField(
        max_length=50,
        blank=True,
        help_text="Tensione di uscita (es: 230/400V)"
    )
    frequenza = models.CharField(
        max_length=10,
        choices=FREQUENZA_CHOICES,
        default='50'
    )

    # Contatori e manutenzione programmata
    ore_lavoro_attuali = models.PositiveIntegerField(
        default=0,
        help_text="Ore di funzionamento totali"
    )
    ore_ultima_manutenzione = models.PositiveIntegerField(
        default=0,
        help_text="Ore al momento dell'ultima manutenzione"
    )
    intervallo_manutenzione_ore = models.PositiveIntegerField(
        default=250,
        help_text="Intervallo in ore tra le manutenzioni"
    )

    # Date manutenzioni componenti
    data_ultimo_cambio_olio = models.DateField(
        blank=True, null=True
    )
    data_ultimo_cambio_filtro_aria = models.DateField(
        blank=True, null=True
    )
    data_ultimo_cambio_filtro_carburante = models.DateField(
        blank=True, null=True
    )
    data_ultimo_cambio_filtro_olio = models.DateField(
        blank=True, null=True
    )
    data_ultima_revisione_batteria = models.DateField(
        blank=True, null=True
    )
    data_ultima_prova_funzionamento = models.DateField(
        blank=True, null=True,
        help_text="Data dell'ultima prova di funzionamento"
    )

    # Documenti
    manuale_uso = models.FileField(
        upload_to=manuale_gruppo_upload_path,
        blank=True,
        null=True,
        help_text="Manuale d'uso e manutenzione"
    )
    certificato_conformita = models.FileField(
        upload_to=certificato_gruppo_upload_path,
        blank=True,
        null=True,
        help_text="Certificato di conformità"
    )
    scheda_tecnica = models.FileField(
        upload_to=certificato_gruppo_upload_path,
        blank=True,
        null=True,
        help_text="Scheda tecnica del costruttore"
    )

    # Assegnazione
    assegnato_a = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="gruppi_assegnati",
    )

    # Note e ubicazione
    ubicazione = models.CharField(
        max_length=200,
        blank=True,
        help_text="Ubicazione fisica del gruppo"
    )
    note = models.TextField(blank=True)

    def __str__(self):
        return f"{self.matricola} - {self.marca} {self.modello} ({self.potenza_kva} kVA)"

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('automezzi:gruppo_detail', kwargs={'pk': self.pk})

    @classmethod
    def get_search_fields(cls):
        """Campi ricercabili nella ricerca globale"""
        return ['matricola', 'marca', 'modello', 'ubicazione']

    def get_search_result_display(self):
        """Testo visualizzato nei risultati di ricerca"""
        return f"{self.matricola} - {self.marca} {self.modello} ({self.potenza_kva} kVA)"

    @property
    def eta(self):
        from datetime import date
        return date.today().year - self.anno_produzione

    @property
    def ore_prossima_manutenzione(self):
        """Calcola le ore alla prossima manutenzione"""
        return self.ore_ultima_manutenzione + self.intervallo_manutenzione_ore

    @property
    def ore_alla_manutenzione(self):
        """Ore rimanenti alla prossima manutenzione"""
        return self.ore_prossima_manutenzione - self.ore_lavoro_attuali

    @property
    def necessita_manutenzione(self):
        """True se il gruppo ha superato le ore per la manutenzione"""
        return self.ore_lavoro_attuali >= self.ore_prossima_manutenzione

    @property
    def percentuale_manutenzione(self):
        """Percentuale di utilizzo rispetto alla prossima manutenzione"""
        if self.intervallo_manutenzione_ore == 0:
            return 0
        ore_dall_ultima = self.ore_lavoro_attuali - self.ore_ultima_manutenzione
        return min(int((ore_dall_ultima / self.intervallo_manutenzione_ore) * 100), 100)

    def manutenzioni_count(self):
        return self.manutenzioni_gruppo.count()

    def eventi_count(self):
        return self.eventi_gruppo.count()

    class Meta:
        verbose_name = "Gruppo Elettrogeno"
        verbose_name_plural = "Gruppi Elettrogeni"
        ordering = ['matricola']


class Manutenzione(AllegatiMixin, models.Model):
    STATO_CHOICES = [
        ("aperta", "Manutenzione Aperta"),
        ("in_corso", "In Corso"),
        ("terminata", "Terminata"),
    ]

    automezzo = models.ForeignKey(
        Automezzo, on_delete=models.CASCADE, related_name="manutenzioni"
    )
    data_apertura = models.DateTimeField(
        auto_now_add=True,
        null=True,
        help_text="Data e ora di apertura della manutenzione",
    )
    data_prevista = models.DateField(
        null=True, help_text="Data prevista per l'intervento di manutenzione"
    )
    descrizione = models.CharField(max_length=255)

    # Nuovo campo stato (sostituisce il booleano completata)
    stato = models.CharField(
        max_length=10,
        choices=STATO_CHOICES,
        default="aperta",
        help_text="Stato della manutenzione",
    )

    # Nuovi campi richiesti
    fornitore = models.ForeignKey(
        "anagrafica.Fornitore",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Fornitore/Officina che esegue la manutenzione",
    )
    luogo = models.CharField(
        max_length=200,
        blank=True,
        help_text="Luogo dove viene eseguita la manutenzione",
    )

    # Campo costo ora opzionale (verrà compilato quando terminata)
    costo = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Costo della manutenzione (da compilare al termine)",
    )

    # Campi utente
    seguito_da = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="manutenzioni_seguite",
        help_text="Utente che ha aperto e segue la pratica di manutenzione",
    )
    responsabile = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="manutenzioni_responsabile",
        help_text="Responsabile dell'esecuzione della manutenzione",
    )
    allegati = models.FileField(
        upload_to=allegati_manutenzione_path,
        blank=True,
        null=True,
        help_text="Allegati della manutenzione (fatture, ricevute ecc.)",
    )

    # Campi per gestione responsabile e inizio lavori
    data_inizio_manutenzione = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Data e ora di inizio della manutenzione (impostata quando il responsabile compila il form)",
    )
    foglio_accettazione = models.FileField(
        upload_to=allegati_manutenzione_path,
        blank=True,
        null=True,
        help_text="Foglio di accettazione firmato dall'officina",
    )
    note_responsabile = models.TextField(
        blank=True,
        help_text="Note del responsabile (nome addetto, dettagli consegna, ecc.)",
    )

    # Campi per completamento finale
    note_finali = models.TextField(
        blank=True, help_text="Note finali sulla manutenzione completata"
    )
    fattura_fornitore = models.FileField(
        upload_to=allegati_manutenzione_path,
        blank=True,
        null=True,
        help_text="Fattura del fornitore per la manutenzione",
    )
    data_completamento = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Data e ora di completamento della manutenzione",
    )

    # Campo legacy da mantenere per compatibilità (deprecato)
    completata = models.BooleanField(
        default=False, help_text="[DEPRECATO] Usa il campo 'stato'"
    )

    def __str__(self):
        return f"{self.automezzo} - {self.data_prevista} - {self.descrizione}"

    @property
    def is_completata(self):
        """Verifica se la manutenzione è completata basandosi sul nuovo campo stato"""
        return self.stato == "terminata"

    def save(self, *args, **kwargs):
        """Override save per sincronizzare il campo legacy completata con stato"""
        # Sincronizza il campo legacy con il nuovo campo stato
        self.completata = self.stato == "terminata"
        super().save(*args, **kwargs)


class AllegatoManutenzione(models.Model):
    """Modello per allegati aggiuntivi delle manutenzioni"""

    manutenzione = models.ForeignKey(
        Manutenzione, on_delete=models.CASCADE, related_name="allegati_aggiuntivi"
    )
    nome = models.CharField(max_length=200, help_text="Nome descrittivo dell'allegato")
    file = models.FileField(
        upload_to=allegati_manutenzione_path, help_text="File allegato"
    )
    data_upload = models.DateTimeField(auto_now_add=True)
    caricato_da = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        verbose_name = "Allegato Manutenzione"
        verbose_name_plural = "Allegati Manutenzione"
        ordering = ["-data_upload"]

    def __str__(self):
        return f"{self.manutenzione} - {self.nome}"


class Rifornimento(AllegatiMixin, models.Model):
    automezzo = models.ForeignKey(
        Automezzo, on_delete=models.CASCADE, related_name="rifornimenti"
    )
    data = models.DateField()
    litri = models.DecimalField(max_digits=6, decimal_places=2)
    costo_totale = models.DecimalField(max_digits=7, decimal_places=2)
    chilometri = models.PositiveIntegerField(
        help_text="Chilometraggio al momento del rifornimento"
    )
    scontrino = models.FileField(
        upload_to=scontrino_upload_path,
        blank=True,
        null=True,
        help_text="Foto dello scontrino del rifornimento",
    )

    def __str__(self):
        return f"{self.automezzo} - {self.data} - {self.litri}L"


class EventoAutomezzo(AllegatiMixin, models.Model):
    TIPO_EVENTO_CHOICES = [
        ("incidente", "Incidente"),
        ("furto", "Furto"),
        ("fermo", "Fermo amministrativo"),
        ("guasto", "Guasto/avaria"),
        ("altro", "Altro"),
    ]

    automezzo = models.ForeignKey(
        Automezzo, on_delete=models.CASCADE, related_name="eventi"
    )
    tipo = models.CharField(max_length=20, choices=TIPO_EVENTO_CHOICES)
    data_evento = models.DateField()
    descrizione = models.TextField(blank=True)
    costo = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
    dipendente_coinvolto = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="eventi_coinvolto",
    )
    file_allegato = models.FileField(
        upload_to=allegato_evento_path,
        blank=True,
        null=True,
        help_text="Foto, verbali, documenti relativi all'evento",
    )
    risolto = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.automezzo} - {self.get_tipo_display()} - {self.data_evento}"


def affidamento_video_upload_path(instance, filename):
    return f"automezzi/affidamenti/{instance.automezzo.targa}/consegna/{filename}"


def affidamento_video_rientro_upload_path(instance, filename):
    return f"automezzi/affidamenti/{instance.automezzo.targa}/rientro/{filename}"


class AffidamentoMezzo(AllegatiMixin, models.Model):
    STATO_CHOICES = [
        ("in_attesa", "In attesa di accettazione"),
        ("accettato", "Accettato"),
        ("in_corso", "In corso"),
        ("completato", "Completato"),
    ]

    CARBURANTE_CHOICES = [
        ("vuoto", "Vuoto"),
        ("1/4", "1/4"),
        ("1/2", "1/2"),
        ("3/4", "3/4"),
        ("pieno", "Pieno"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="affidamenti_mezzo",
        help_text="Dipendente a cui viene affidato il mezzo",
    )
    automezzo = models.ForeignKey(
        Automezzo,
        on_delete=models.CASCADE,
        related_name="affidamenti",
    )
    data_inizio = models.DateField(help_text="Data inizio affidamento")
    data_fine = models.DateField(help_text="Data fine prevista affidamento")
    video_stato_vettura = models.FileField(
        upload_to=affidamento_video_upload_path,
        blank=True,
        null=True,
        help_text="Video dello stato della vettura alla consegna",
    )
    km_iniziali = models.PositiveIntegerField(help_text="Chilometri alla consegna")
    km_finali = models.PositiveIntegerField(
        blank=True,
        null=True,
        help_text="Chilometri al rientro",
    )
    scopo_viaggio = models.CharField(
        max_length=200,
        help_text="Scopo del viaggio / trasferta",
    )
    carburante = models.CharField(
        max_length=10,
        choices=CARBURANTE_CHOICES,
        help_text="Livello carburante alla consegna",
    )
    note = models.TextField(
        blank=True,
        help_text="Note aggiuntive sull'affidamento",
    )
    firma_accettazione = models.BooleanField(
        default=False,
        help_text="Firma digitale per accettazione del mezzo",
    )
    token_accettazione = models.UUIDField(
        unique=True,
        editable=False,
        help_text="Token univoco per il link di accettazione",
    )
    data_accettazione = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Data e ora di accettazione",
    )
    stato = models.CharField(
        max_length=15,
        choices=STATO_CHOICES,
        default="in_attesa",
    )
    # Campi rientro
    video_rientro = models.FileField(
        upload_to=affidamento_video_rientro_upload_path,
        blank=True,
        null=True,
        help_text="Video dello stato della vettura al rientro",
    )
    note_rientro = models.TextField(
        blank=True,
        help_text="Note al rientro del mezzo",
    )
    data_rientro = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Data e ora effettiva del rientro",
    )
    # Campi danni veicolo
    danni_consegna = models.JSONField(
        default=list,
        blank=True,
        help_text="Lista danni presenti alla consegna: [{'area': 'cofano_anteriore', 'x': 50, 'y': 30, 'tipo': 'graffio', 'note': '...'}]",
    )
    danni_rientro = models.JSONField(
        default=list,
        blank=True,
        help_text="Lista danni presenti al rientro",
    )
    # Meta
    data_creazione = models.DateTimeField(auto_now_add=True)
    creato_da = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="affidamenti_creati",
    )

    class Meta:
        verbose_name = "Affidamento Mezzo"
        verbose_name_plural = "Affidamenti Mezzi"
        ordering = ["-data_creazione"]

    def __str__(self):
        return f"{self.automezzo.targa} → {self.user.get_full_name() or self.user.username} ({self.data_inizio} - {self.data_fine})"

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('automezzi:affidamento_detail', kwargs={'pk': self.pk})

    def save(self, *args, **kwargs):
        if not self.token_accettazione:
            import uuid
            self.token_accettazione = uuid.uuid4()
        super().save(*args, **kwargs)


# automezzi/models2.py - Modelli aggiuntivi per espansione funzionalità
from django.db import models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal
from datetime import date, timedelta


# === UPLOAD PATHS ===
def spesa_viaggio_upload_path(instance, filename):
    return f"automezzi/spese_viaggio/{instance.automezzo.targa}/{instance.data_spesa.year}/{filename}"


def intervento_upload_path(instance, filename):
    return f"automezzi/interventi/{instance.automezzo.targa}/{instance.tipo}/{filename}"


def controllo_upload_path(instance, filename):
    return f"automezzi/controlli/{instance.automezzo.targa}/{instance.tipo_controllo}/{filename}"


# === MODELLI PER GRUPPI ELETTROGENI ===

class ManutenzioneGruppo(AllegatiMixin, models.Model):
    """Manutenzioni per gruppi elettrogeni"""

    STATO_CHOICES = [
        ("aperta", "Manutenzione Aperta"),
        ("in_corso", "In Corso"),
        ("terminata", "Terminata"),
    ]

    gruppo = models.ForeignKey(
        Gruppo, on_delete=models.CASCADE, related_name="manutenzioni_gruppo"
    )
    data_apertura = models.DateTimeField(
        auto_now_add=True,
        null=True,
        help_text="Data e ora di apertura della manutenzione",
    )
    data_prevista = models.DateField(
        null=True, help_text="Data prevista per l'intervento di manutenzione"
    )
    descrizione = models.CharField(max_length=255)

    stato = models.CharField(
        max_length=10,
        choices=STATO_CHOICES,
        default="aperta",
        help_text="Stato della manutenzione",
    )

    fornitore = models.ForeignKey(
        "anagrafica.Fornitore",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Fornitore/Officina che esegue la manutenzione",
    )
    luogo = models.CharField(
        max_length=200,
        blank=True,
        help_text="Luogo dove viene eseguita la manutenzione",
    )

    costo = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Costo della manutenzione (da compilare al termine)",
    )

    # Ore lavoro al momento della manutenzione
    ore_lavoro = models.PositiveIntegerField(
        blank=True,
        null=True,
        help_text="Ore di funzionamento al momento della manutenzione"
    )

    # Campi utente
    seguito_da = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="manutenzioni_gruppo_seguite",
        help_text="Utente che ha aperto e segue la pratica di manutenzione",
    )
    responsabile = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="manutenzioni_gruppo_responsabile",
        help_text="Responsabile dell'esecuzione della manutenzione",
    )

    data_inizio_manutenzione = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Data e ora di inizio della manutenzione",
    )

    note_responsabile = models.TextField(
        blank=True,
        help_text="Note del responsabile",
    )

    # Campo finale
    data_completamento = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Data e ora di completamento della manutenzione",
    )

    note_finali = models.TextField(
        blank=True,
        help_text="Note finali e dettagli del lavoro svolto",
    )

    # Interventi specifici eseguiti
    cambio_olio = models.BooleanField(default=False)
    cambio_filtro_aria = models.BooleanField(default=False)
    cambio_filtro_carburante = models.BooleanField(default=False)
    cambio_filtro_olio = models.BooleanField(default=False)
    revisione_batteria = models.BooleanField(default=False)
    prova_funzionamento = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.gruppo.matricola} - {self.descrizione} - {self.get_stato_display()}"

    class Meta:
        verbose_name = "Manutenzione Gruppo"
        verbose_name_plural = "Manutenzioni Gruppi"
        ordering = ['-data_apertura']


class EventoGruppo(AllegatiMixin, models.Model):
    """Eventi relativi ai gruppi elettrogeni"""

    TIPO_EVENTO_CHOICES = [
        ("guasto", "Guasto/avaria"),
        ("fermo", "Fermo tecnico"),
        ("surriscaldamento", "Surriscaldamento"),
        ("mancato_avvio", "Mancato avvio"),
        ("perdita_olio", "Perdita olio"),
        ("perdita_carburante", "Perdita carburante"),
        ("batteria_scarica", "Batteria scarica"),
        ("altro", "Altro"),
    ]

    gruppo = models.ForeignKey(
        Gruppo, on_delete=models.CASCADE, related_name="eventi_gruppo"
    )
    tipo = models.CharField(max_length=30, choices=TIPO_EVENTO_CHOICES)
    data_evento = models.DateField()
    ore_lavoro = models.PositiveIntegerField(
        blank=True,
        null=True,
        help_text="Ore di funzionamento al momento dell'evento"
    )
    descrizione = models.TextField(blank=True)
    costo = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
    dipendente_coinvolto = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="eventi_gruppo_coinvolto",
    )
    file_allegato = models.FileField(
        upload_to=allegato_evento_gruppo_path,
        blank=True,
        null=True,
        help_text="Foto, verbali, documenti relativi all'evento",
    )
    risolto = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.gruppo.matricola} - {self.get_tipo_display()} - {self.data_evento}"

    class Meta:
        verbose_name = "Evento Gruppo"
        verbose_name_plural = "Eventi Gruppi"
        ordering = ['-data_evento']


def affidamento_gruppo_video_upload_path(instance, filename):
    return f"gruppi/affidamenti/{instance.gruppo.matricola}/consegna/{filename}"


def affidamento_gruppo_video_rientro_upload_path(instance, filename):
    return f"gruppi/affidamenti/{instance.gruppo.matricola}/rientro/{filename}"


class AffidamentoGruppo(AllegatiMixin, models.Model):
    """Affidamento di gruppi elettrogeni ai dipendenti"""

    STATO_CHOICES = [
        ("in_attesa", "In attesa di accettazione"),
        ("accettato", "Accettato"),
        ("in_corso", "In corso"),
        ("completato", "Completato"),
    ]

    CARBURANTE_CHOICES = [
        ("vuoto", "Vuoto"),
        ("1/4", "1/4"),
        ("1/2", "1/2"),
        ("3/4", "3/4"),
        ("pieno", "Pieno"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="affidamenti_gruppo",
        help_text="Dipendente a cui viene affidato il gruppo",
    )
    gruppo = models.ForeignKey(
        Gruppo,
        on_delete=models.CASCADE,
        related_name="affidamenti_gruppo",
    )
    data_inizio = models.DateField(help_text="Data inizio affidamento")
    data_fine = models.DateField(help_text="Data fine prevista affidamento")
    video_stato_gruppo = models.FileField(
        upload_to=affidamento_gruppo_video_upload_path,
        blank=True,
        null=True,
        help_text="Video dello stato del gruppo alla consegna",
    )
    ore_iniziali = models.PositiveIntegerField(help_text="Ore lavoro alla consegna")
    ore_finali = models.PositiveIntegerField(
        blank=True,
        null=True,
        help_text="Ore lavoro al rientro",
    )
    scopo_utilizzo = models.CharField(
        max_length=200,
        help_text="Scopo dell'utilizzo / cantiere",
    )
    destinazione = models.CharField(
        max_length=200,
        blank=True,
        help_text="Luogo di destinazione del gruppo",
    )
    carburante = models.CharField(
        max_length=10,
        choices=CARBURANTE_CHOICES,
        help_text="Livello carburante alla consegna",
    )
    note = models.TextField(
        blank=True,
        help_text="Note aggiuntive sull'affidamento",
    )
    firma_accettazione = models.BooleanField(
        default=False,
        help_text="Dipendente ha accettato l'affidamento",
    )
    data_accettazione = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Data e ora di accettazione",
    )
    stato = models.CharField(
        max_length=20,
        choices=STATO_CHOICES,
        default="in_attesa",
    )

    # Campi per il rientro
    video_stato_gruppo_rientro = models.FileField(
        upload_to=affidamento_gruppo_video_rientro_upload_path,
        blank=True,
        null=True,
        help_text="Video dello stato del gruppo al rientro",
    )
    data_rientro_effettivo = models.DateField(
        blank=True,
        null=True,
        help_text="Data effettiva di rientro",
    )
    carburante_rientro = models.CharField(
        max_length=10,
        choices=CARBURANTE_CHOICES,
        blank=True,
        help_text="Livello carburante al rientro",
    )
    note_rientro = models.TextField(
        blank=True,
        help_text="Note sul rientro e condizioni del gruppo",
    )
    danni_riscontrati = models.TextField(
        blank=True,
        help_text="Eventuali danni riscontrati al rientro",
    )

    class Meta:
        verbose_name = "Affidamento Gruppo"
        verbose_name_plural = "Affidamenti Gruppi"
        ordering = ['-data_inizio']

    def __str__(self):
        return f"{self.gruppo.matricola} - {self.user.get_full_name()} ({self.data_inizio})"


# === CATEGORIE E TIPOLOGIE ===
class CategoriaSpesa(models.Model):
    """Categorizzazione delle spese per reporting"""

    nome = models.CharField(max_length=50, unique=True)
    descrizione = models.TextField(blank=True)
    codice = models.CharField(
        max_length=10, unique=True, help_text="Codice per export contabili"
    )
    categoria_padre = models.ForeignKey(
        "self", on_delete=models.CASCADE, null=True, blank=True
    )
    attiva = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Categorie Spesa"

    def __str__(self):
        return f"{self.codice} - {self.nome}"


class TipologiaIntervento(models.Model):
    """Tipologie di interventi di manutenzione"""

    FREQUENZA_CHOICES = [
        ("una_tantum", "Una tantum"),
        ("giornaliera", "Giornaliera"),
        ("settimanale", "Settimanale"),
        ("mensile", "Mensile"),
        ("trimestrale", "Trimestrale"),
        ("semestrale", "Semestrale"),
        ("annuale", "Annuale"),
        ("per_chilometri", "Per chilometri"),
        ("ordinario", "Intervento Ordinario"),
        ("straordinario", "Intervento Straordinario"),
    ]

    nome = models.CharField(max_length=100)
    descrizione = models.TextField(blank=True)
    categoria_spesa = models.ForeignKey(CategoriaSpesa, on_delete=models.CASCADE)
    frequenza_consigliata = models.CharField(
        max_length=20, choices=FREQUENZA_CHOICES, default="una_tantum"
    )
    km_intervallo = models.PositiveIntegerField(
        null=True, blank=True, help_text="Intervallo in km se frequenza per_chilometri"
    )
    costo_medio_previsto = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True
    )
    tempo_medio_ore = models.DecimalField(
        max_digits=4, decimal_places=1, null=True, blank=True
    )
    critico = models.BooleanField(
        default=False, help_text="Intervento critico per sicurezza"
    )
    attivo = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Tipologie Intervento"

    def __str__(self):
        return self.nome


# === SPESE DI VIAGGIO ===
class SpesaViaggio(models.Model):
    """Spese sostenute durante viaggi/trasferte con automezzi"""

    TIPO_SPESA_CHOICES = [
        ("carburante", "Carburante"),
        ("pedaggi", "Pedaggi autostradali"),
        ("parcheggi", "Parcheggi"),
        ("lavaggio", "Lavaggio auto"),
        ("vitto", "Vitto e alloggio"),
        ("multe", "Multe e sanzioni"),
        ("riparazioni", "Riparazioni urgenti"),
        ("altro", "Altro"),
    ]

    automezzo = models.ForeignKey(
        "Automezzo", on_delete=models.CASCADE, related_name="spese_viaggio"
    )
    data_spesa = models.DateField()
    tipo_spesa = models.CharField(max_length=20, choices=TIPO_SPESA_CHOICES)
    categoria_spesa = models.ForeignKey(CategoriaSpesa, on_delete=models.CASCADE)

    # Dati spesa
    importo = models.DecimalField(max_digits=8, decimal_places=2)
    descrizione = models.CharField(max_length=200)
    note = models.TextField(blank=True)

    # Localizzazione
    luogo = models.CharField(
        max_length=100, blank=True, help_text="Città/località della spesa"
    )
    km_automezzo = models.PositiveIntegerField(
        help_text="Chilometri al momento della spesa"
    )

    # Gestione
    dipendente = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    scontrino = models.FileField(
        upload_to=spesa_viaggio_upload_path, blank=True, null=True
    )
    rimborsabile = models.BooleanField(default=True)
    rimborsata = models.BooleanField(default=False)
    data_rimborso = models.DateField(null=True, blank=True)

    # Meta
    data_inserimento = models.DateTimeField(auto_now_add=True)
    data_modifica = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Spese Viaggio"
        ordering = ["-data_spesa"]

    def __str__(self):
        return f"{self.automezzo.targa} - {self.get_tipo_spesa_display()} - €{self.importo}"


# === INTERVENTI DETTAGLIATI ===
class InterventoManutenzione(models.Model):
    """Interventi di manutenzione dettagliati (espansione di Manutenzione)"""

    STATO_CHOICES = [
        ("programmato", "Programmato"),
        ("in_corso", "In corso"),
        ("sospeso", "Sospeso"),
        ("completato", "Completato"),
        ("annullato", "Annullato"),
    ]

    PRIORITA_CHOICES = [
        ("bassa", "Bassa"),
        ("normale", "Normale"),
        ("alta", "Alta"),
        ("critica", "Critica"),
    ]

    # Relazioni
    automezzo = models.ForeignKey(
        "Automezzo", on_delete=models.CASCADE, related_name="interventi_manutenzione"
    )
    manutenzione_base = models.OneToOneField(
        "Manutenzione",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Collegamento a record manutenzione base esistente",
    )
    tipologia = models.ForeignKey(TipologiaIntervento, on_delete=models.CASCADE)

    # Programmazione
    data_programmata = models.DateField()
    data_inizio = models.DateField(null=True, blank=True)
    data_completamento = models.DateField(null=True, blank=True)
    km_programmati = models.PositiveIntegerField(
        help_text="Km automezzo quando programmato"
    )
    km_effettivi = models.PositiveIntegerField(
        null=True, blank=True, help_text="Km effettivi al completamento"
    )

    # Dettagli
    descrizione_dettagliata = models.TextField()
    priorita = models.CharField(
        max_length=10, choices=PRIORITA_CHOICES, default="normale"
    )
    stato = models.CharField(
        max_length=15, choices=STATO_CHOICES, default="programmato"
    )

    # Risorse
    officina = models.CharField(max_length=100, blank=True)
    responsabile_tecnico = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="interventi_responsabile",
    )
    tempo_previsto_ore = models.DecimalField(
        max_digits=4, decimal_places=1, null=True, blank=True
    )
    tempo_effettivo_ore = models.DecimalField(
        max_digits=4, decimal_places=1, null=True, blank=True
    )

    # Costi
    costo_previsto = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True
    )
    costo_manodopera = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True
    )
    costo_ricambi = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True
    )
    costo_extra = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True
    )

    # Documentazione
    allegati = models.FileField(upload_to=intervento_upload_path, blank=True, null=True)
    note_tecniche = models.TextField(blank=True)

    # Meta
    data_creazione = models.DateTimeField(auto_now_add=True)
    data_ultima_modifica = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Interventi Manutenzione"
        ordering = ["-data_programmata"]

    def __str__(self):
        return (
            f"{self.automezzo.targa} - {self.tipologia.nome} - {self.data_programmata}"
        )

    @property
    def costo_totale(self):
        """Calcola costo totale effettivo"""
        costi = [
            self.costo_manodopera or 0,
            self.costo_ricambi or 0,
            self.costo_extra or 0,
        ]
        return sum(costi) if any(costi) else self.costo_previsto

    @property
    def giorni_ritardo(self):
        """Calcola giorni di ritardo rispetto alla programmazione"""
        if self.stato == "completato" and self.data_completamento:
            delta = self.data_completamento - self.data_programmata
            return max(0, delta.days)
        elif self.stato in ["programmato", "in_corso"]:
            delta = date.today() - self.data_programmata
            return max(0, delta.days)
        return 0


# === RICAMBI E MATERIALI ===
class Ricambio(models.Model):
    """Catalogo ricambi per automezzi"""

    codice_ricambio = models.CharField(max_length=50, unique=True)
    nome = models.CharField(max_length=100)
    descrizione = models.TextField(blank=True)

    # Classificazione
    categoria = models.CharField(max_length=50)
    marca_compatibile = models.CharField(
        max_length=50, blank=True, help_text="Marca veicolo compatibile"
    )
    modello_compatibile = models.CharField(max_length=50, blank=True)

    # Prezzi e fornitori
    prezzo_listino = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True
    )
    fornitore_principale = models.CharField(max_length=100, blank=True)

    # Gestione scorte
    scorta_minima = models.PositiveIntegerField(default=0)
    scorta_attuale = models.PositiveIntegerField(default=0)

    attivo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.codice_ricambio} - {self.nome}"


class RicambioUsato(models.Model):
    """Ricambi utilizzati in un intervento"""

    intervento = models.ForeignKey(
        InterventoManutenzione, on_delete=models.CASCADE, related_name="ricambi_usati"
    )
    ricambio = models.ForeignKey(Ricambio, on_delete=models.CASCADE)
    quantita = models.PositiveIntegerField(default=1)
    prezzo_unitario = models.DecimalField(max_digits=8, decimal_places=2)

    def __str__(self):
        return f"{self.ricambio.nome} x{self.quantita}"

    @property
    def costo_totale(self):
        return self.quantita * self.prezzo_unitario


# === CONTROLLI E ISPEZIONI ===
class ControlloAutomezzo(models.Model):
    """Controlli periodici e ispezioni"""

    TIPO_CONTROLLO_CHOICES = [
        ("settimanale", "Controllo settimanale"),
        ("mensile", "Controllo mensile"),
        ("pre_viaggio", "Controllo pre-viaggio"),
        ("post_viaggio", "Controllo post-viaggio"),
        ("straordinario", "Controllo straordinario"),
        ("ispettivo", "Ispezione"),
    ]

    ESITO_CHOICES = [
        ("ok", "OK - Nessun problema"),
        ("attenzione", "Attenzione - Controllo necessario"),
        ("intervento", "Intervento richiesto"),
        ("fermo", "Fermo macchina"),
    ]

    automezzo = models.ForeignKey(
        "Automezzo", on_delete=models.CASCADE, related_name="controlli"
    )
    tipo_controllo = models.CharField(max_length=20, choices=TIPO_CONTROLLO_CHOICES)
    data_controllo = models.DateField()
    km_controllo = models.PositiveIntegerField()

    # Responsabile
    controllore = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True
    )

    # Elementi controllati
    controllo_freni = models.CharField(
        max_length=10, choices=ESITO_CHOICES, default="ok"
    )
    controllo_pneumatici = models.CharField(
        max_length=10, choices=ESITO_CHOICES, default="ok"
    )
    controllo_luci = models.CharField(
        max_length=10, choices=ESITO_CHOICES, default="ok"
    )
    controllo_fluidi = models.CharField(
        max_length=10, choices=ESITO_CHOICES, default="ok"
    )
    controllo_carrozzeria = models.CharField(
        max_length=10, choices=ESITO_CHOICES, default="ok"
    )
    controllo_interni = models.CharField(
        max_length=10, choices=ESITO_CHOICES, default="ok"
    )

    # Esito generale
    esito_generale = models.CharField(
        max_length=10, choices=ESITO_CHOICES, default="ok"
    )
    note = models.TextField(blank=True)
    azioni_richieste = models.TextField(blank=True, help_text="Azioni da intraprendere")

    # Documentazione
    foto_allegati = models.FileField(
        upload_to=controllo_upload_path, blank=True, null=True
    )

    data_creazione = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Controlli Automezzo"
        ordering = ["-data_controllo"]

    def __str__(self):
        return f"{self.automezzo.targa} - {self.get_tipo_controllo_display()} - {self.data_controllo}"

    @property
    def problemi_rilevati(self):
        """Conta quanti controlli hanno dato esito diverso da OK"""
        controlli = [
            self.controllo_freni,
            self.controllo_pneumatici,
            self.controllo_luci,
            self.controllo_fluidi,
            self.controllo_carrozzeria,
            self.controllo_interni,
        ]
        return sum(1 for controllo in controlli if controllo != "ok")


# # === STATISTICHE AVANZATE INTEGRATE CON DISTRIBUZIONE ===
# class StatisticheConsumoViaggio(models.Model):
#     """Statistiche consumi basate sui dati dell'app distribuzione - integrazione con Giro"""

#     # # Relazione con il giro di distribuzione
#     # giro = models.OneToOneField(
#     #     'distribuzione.Giro',
#     #     on_delete=models.CASCADE,
#     #     related_name='statistiche_consumo',
#     #     help_text="Giro di distribuzione da cui estrarre i dati"
#     # )

#     # Dati estratti automaticamente dal giro
#     automezzo = models.ForeignKey('Automezzo', on_delete=models.CASCADE, related_name='statistiche_viaggio')
#     autista = models.ForeignKey(
#         'distribuzione.Autista',
#         on_delete=models.CASCADE,
#         help_text="Autista estratto dal giro"
#     )

#     # Dati viaggio (estratti da Giro)
#     data_viaggio = models.DateField(help_text="Data del viaggio (da giro.data_giro)")
#     targa = models.CharField(max_length=20, help_text="Targa estratta da giro.targa_mezzo_utilizzato")

#     # Chilometraggio (da Giro)
#     km_partenza = models.PositiveIntegerField(help_text="Km partenza (da giro.km_partenza)")
#     km_rientro = models.PositiveIntegerField(help_text="Km rientro (da giro.km_rientro)")
#     km_percorsi = models.PositiveIntegerField(default=0, help_text="Calcolato: km_rientro - km_partenza")

#     # Rifornimento (da Giro)
#     litri_rifornimento = models.DecimalField(
#         max_digits=8, decimal_places=2, null=True, blank=True,
#         help_text="Litri riforniti (da giro.litri_rifornimento)"
#     )
#     costo_rifornimento = models.DecimalField(
#         max_digits=8, decimal_places=2, null=True, blank=True,
#         help_text="Costo rifornimento (da giro.costo_rifornimento)"
#     )
#     foto_scontrino = models.ImageField(
#         upload_to='statistiche_viaggio/scontrini/',
#         null=True, blank=True,
#         help_text="Foto scontrino rifornimento (da giro.foto_scontrino_rifornimento)"
#     )

#     # Calcoli automatici
#     consumo_viaggio_100km = models.DecimalField(
#         max_digits=5, decimal_places=2, null=True, blank=True,
#         help_text="Consumo per questo viaggio (L/100km)"
#     )
#     costo_per_km_viaggio = models.DecimalField(
#         max_digits=6, decimal_places=3, null=True, blank=True,
#         help_text="Costo carburante per km di questo viaggio"
#     )
#     costo_per_litro = models.DecimalField(
#         max_digits=5, decimal_places=3, null=True, blank=True,
#         help_text="Prezzo al litro per questo rifornimento"
#     )

#     # Dati carico (estratti da giro per analisi efficienza)
#     peso_trasportato = models.DecimalField(
#         max_digits=8, decimal_places=2, null=True, blank=True,
#         help_text="Peso totale trasportato (da giro.peso_totale)"
#     )
#     numero_consegne = models.PositiveIntegerField(
#         default=0,
#         help_text="Numero di consegne effettuate"
#     )

#     # Efficienza calcolata
#     kg_per_km = models.DecimalField(
#         max_digits=6, decimal_places=2, null=True, blank=True,
#         help_text="Efficienza: kg trasportati per km percorso"
#     )
#     costo_per_kg_km = models.DecimalField(
#         max_digits=8, decimal_places=4, null=True, blank=True,
#         help_text="Costo carburante per kg*km trasportato"
#     )

#     # Meta
#     data_creazione = models.DateTimeField(auto_now_add=True)
#     data_calcolo = models.DateTimeField(auto_now=True)

#     class Meta:
#         verbose_name = "Statistiche Consumo Viaggio"
#         verbose_name_plural = "Statistiche Consumo Viaggi"
#         ordering = ['-data_viaggio']

#     def __str__(self):
#         return f"{self.targa} - {self.autista} - {self.data_viaggio}"

#     def save(self, *args, **kwargs):
#         """Override save per estrarre automaticamente dati dal giro"""
#         if self.giro:
#             # Estrai dati dal giro
#             self.automezzo = self.giro.autista.mezzo_assegnato
#             self.autista = self.giro.autista
#             self.data_viaggio = self.giro.data_giro
#             self.targa = self.giro.targa_mezzo_utilizzato or (self.automezzo.targa if self.automezzo else '')

#             # Dati chilometraggio
#             if self.giro.km_partenza:
#                 self.km_partenza = self.giro.km_partenza
#             if self.giro.km_rientro:
#                 self.km_rientro = self.giro.km_rientro

#             # Calcola km percorsi
#             if self.km_partenza and self.km_rientro:
#                 self.km_percorsi = self.km_rientro - self.km_partenza

#             # Dati rifornimento
#             self.litri_rifornimento = self.giro.litri_rifornimento
#             self.costo_rifornimento = self.giro.costo_rifornimento
#             if self.giro.foto_scontrino_rifornimento:
#                 self.foto_scontrino = self.giro.foto_scontrino_rifornimento

#             # Dati carico
#             self.peso_trasportato = self.giro.peso_totale

#             # Conta consegne dal giro
#             if hasattr(self.giro, 'assegnazioni'):
#                 self.numero_consegne = self.giro.assegnazioni.filter(
#                     stato__in=['consegnato', 'completato']
#                 ).count()

#             # Calcola statistiche
#             self.calcola_statistiche()

#         super().save(*args, **kwargs)

#     def calcola_statistiche(self):
#         """
#         Calcola statistiche CORRETTE per singolo viaggio
#         IMPORTANTE: Non calcola consumi dal rifornimento del viaggio corrente!
#         I consumi vengono calcolati su periodi più lunghi con algoritmi separati.
#         """

#         # ❌ NON calcolare consumo dal rifornimento del viaggio corrente!
#         # Motivo: il serbatoio non era vuoto all'inizio del viaggio

#         # ✅ Calcoli CORRETTI solo per il viaggio singolo:

#         # Costo per litro (QUESTO è corretto - del rifornimento specifico)
#         if self.costo_rifornimento and self.litri_rifornimento and self.litri_rifornimento > 0:
#             self.costo_per_litro = self.costo_rifornimento / self.litri_rifornimento

#         # Efficienza trasporto (QUESTO è corretto - peso/km del viaggio)
#         if self.peso_trasportato and self.km_percorsi and self.km_percorsi > 0:
#             self.kg_per_km = self.peso_trasportato / self.km_percorsi

#         # ✅ I consumi e costi/km verranno calcolati da algoritmi separati
#         # che analizzano più viaggi nel tempo usando km_rifornimento

#     @classmethod
#     def crea_da_giro(cls, giro):
#         """Factory method per creare statistiche da un giro completato"""
#         if giro.stato not in ['completato', 'chiuso']:
#             return None

#         # Controlla se esistono già statistiche per questo giro
#         if hasattr(giro, 'statistiche_consumo'):
#             return giro.statistiche_consumo

#         # Crea nuove statistiche
#         return cls.objects.create(giro=giro)


class StatisticheConsumo(models.Model):
    """Statistiche aggregate sui consumi per automezzo (basate su StatisticheConsumoViaggio)"""

    automezzo = models.OneToOneField(
        "Automezzo", on_delete=models.CASCADE, related_name="statistiche_consumo"
    )

    # Periodo di calcolo
    data_inizio_periodo = models.DateField()
    data_fine_periodo = models.DateField()

    # Aggregazioni dai viaggi
    numero_viaggi = models.PositiveIntegerField(default=0)
    km_totali_periodo = models.PositiveIntegerField(default=0)
    litri_totali_periodo = models.DecimalField(
        max_digits=10, decimal_places=2, default=0
    )
    costo_totale_periodo = models.DecimalField(
        max_digits=10, decimal_places=2, default=0
    )

    # Medie calcolate
    consumo_medio_100km = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    costo_medio_per_km = models.DecimalField(
        max_digits=6, decimal_places=3, null=True, blank=True
    )
    media_litri_per_viaggio = models.DecimalField(
        max_digits=6, decimal_places=2, null=True, blank=True
    )
    media_km_per_viaggio = models.DecimalField(
        max_digits=6, decimal_places=1, null=True, blank=True
    )

    # Best/Worst performance
    miglior_consumo_100km = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    peggior_consumo_100km = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    # viaggio_piu_efficiente = models.ForeignKey(
    #     StatisticheConsumoViaggio,
    #     on_delete=models.SET_NULL,
    #     null=True, blank=True,
    #     related_name='+',
    #     help_text="Riferimento al viaggio più efficiente"
    # )

    # Meta
    data_calcolo = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Statistiche Consumo Aggregate"

    def __str__(self):
        return f"{self.automezzo.targa} - Consumi {self.data_inizio_periodo}/{self.data_fine_periodo}"

    def ricalcola_da_viaggi(self):
        """
        Ricalcola statistiche CORRETTE basandosi sui viaggi nel periodo
        Usa algoritmo di calcolo consumo realistico con rifornimenti sequenziali
        """
        # viaggi = StatisticheConsumoViaggio.objects.filter(
        #     automezzo=self.automezzo,
        #     data_viaggio__range=[self.data_inizio_periodo, self.data_fine_periodo],
        #     km_percorsi__gt=0  # Solo viaggi con dati validi
        # ).order_by('data_viaggio')

        # if not viaggi.exists():
        #     return

        # # Aggregazioni base
        # self.numero_viaggi = viaggi.count()
        # self.km_totali_periodo = sum(v.km_percorsi for v in viaggi if v.km_percorsi)

        # # ✅ CALCOLO CONSUMI REALISTICO
        # consumo_medio = self.calcola_consumo_realistico(viaggi)
        # if consumo_medio:
        #     self.consumo_medio_100km = consumo_medio

        # # Calcoli sui rifornimenti
        # viaggi_con_rifornimento = [v for v in viaggi if v.costo_rifornimento and v.costo_rifornimento > 0]
        # if viaggi_con_rifornimento:
        #     self.litri_totali_periodo = sum(v.litri_rifornimento or 0 for v in viaggi_con_rifornimento)
        #     self.costo_totale_periodo = sum(v.costo_rifornimento or 0 for v in viaggi_con_rifornimento)

        #     # Costo medio al litro (media pesata)
        #     if self.litri_totali_periodo > 0:
        #         costo_medio_litro = self.costo_totale_periodo / self.litri_totali_periodo

        #         # Stima costo per km usando consumo medio
        #         if self.consumo_medio_100km:
        #             consumo_per_km = self.consumo_medio_100km / 100
        #             self.costo_medio_per_km = consumo_per_km * costo_medio_litro

        # # Medie viaggi
        # if self.numero_viaggi > 0:
        #     self.media_km_per_viaggio = self.km_totali_periodo / self.numero_viaggi
        #     if viaggi_con_rifornimento:
        #         self.media_litri_per_viaggio = self.litri_totali_periodo / len(viaggi_con_rifornimento)

    def calcola_consumo_realistico(self, viaggi):
        """
        Calcola consumo medio realistico usando sequenze rifornimento → km

        Logica: Quando faccio rifornimento ai km X con Y litri,
        questi Y litri mi serviranno per i prossimi km fino al rifornimento successivo
        """
        viaggi_con_km_rifornimento = [
            v
            for v in viaggi
            if v.giro
            and hasattr(v.giro, "km_rifornimento")
            and v.giro.km_rifornimento
            and v.litri_rifornimento
            and v.litri_rifornimento > 0
        ]

        if len(viaggi_con_km_rifornimento) < 2:
            return None

        consumi_calcolati = []

        for i in range(len(viaggi_con_km_rifornimento) - 1):
            viaggio_corrente = viaggi_con_km_rifornimento[i]
            viaggio_successivo = viaggi_con_km_rifornimento[i + 1]

            # Km percorsi con il carburante del rifornimento corrente
            km_con_carburante = (
                viaggio_successivo.giro.km_rifornimento
                - viaggio_corrente.giro.km_rifornimento
            )

            if km_con_carburante > 0:
                # Consumo per 100km
                consumo_100km = (
                    viaggio_corrente.litri_rifornimento / km_con_carburante
                ) * 100

                # Filtro valori anomali (consumo troppo basso/alto)
                if 5 <= consumo_100km <= 80:  # Range realistico per veicoli commerciali
                    consumi_calcolati.append(consumo_100km)

        if consumi_calcolati:
            # Media escludendo outliers (rimuovi 10% estremi)
            consumi_calcolati.sort()
            n = len(consumi_calcolati)
            start_idx = max(0, int(n * 0.1))
            end_idx = min(n, int(n * 0.9))

            if end_idx > start_idx:
                consumi_filtrati = consumi_calcolati[start_idx:end_idx]
                return round(sum(consumi_filtrati) / len(consumi_filtrati), 2)

        return None


class StatisticheCosto(models.Model):
    """Statistiche sui costi per automezzo"""

    automezzo = models.OneToOneField(
        "Automezzo", on_delete=models.CASCADE, related_name="statistiche_costo"
    )

    # Periodo
    anno = models.PositiveIntegerField()
    trimestre = models.PositiveIntegerField(
        null=True, blank=True, choices=[(1, 1), (2, 2), (3, 3), (4, 4)]
    )

    # Costi per categoria
    costo_carburante = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    costo_manutenzioni = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    costo_spese_viaggio = models.DecimalField(
        max_digits=10, decimal_places=2, default=0
    )
    costo_interventi = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    costo_documenti = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Assicurazioni, bolli, revisioni",
    )
    costo_eventi = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, help_text="Multe, incidenti, ecc"
    )

    # Totali
    costo_totale = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    km_percorsi = models.PositiveIntegerField(default=0)
    costo_per_km = models.DecimalField(
        max_digits=6, decimal_places=3, null=True, blank=True
    )

    # Meta
    data_calcolo = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Statistiche Costo"
        unique_together = ["automezzo", "anno", "trimestre"]

    def __str__(self):
        periodo = f"{self.anno}"
        if self.trimestre:
            periodo += f" Q{self.trimestre}"
        return f"{self.automezzo.targa} - Costi {periodo}"

    def calcola_totale(self):
        """Ricalcola il costo totale"""
        costi = [
            self.costo_carburante,
            self.costo_manutenzioni,
            self.costo_spese_viaggio,
            self.costo_interventi,
            self.costo_documenti,
            self.costo_eventi,
        ]
        self.costo_totale = sum(costi)

        if self.km_percorsi > 0:
            self.costo_per_km = self.costo_totale / self.km_percorsi
