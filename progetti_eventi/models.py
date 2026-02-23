"""
Models per app progetti_eventi.

ARCHITETTURA:
- Progetto: entità principale creata dal commerciale
- ProgettoReparto: istanza separata per Audio/Video/Luci
- EngineeringTask: task di studio del progetto per reparto
- ListaProdotti: output dell'engineering

INTEGRAZIONE ALTRE APP:
- magazzino: riceve ProgettoReparto.id per approntamento
- travel: riceve ProgettoReparto.id per organizzare viaggi
- scouting: riceve ProgettoReparto.id per ricerca personale
- logistica: riceve ProgettoReparto.id per consegne/ritiri
"""

from django.db import models
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal

from core.models import BaseModel, BaseModelWithCode
from core.mixins import AllegatiMixin


# ============================================================================
# PROGETTO PRINCIPALE
# ============================================================================

class Progetto(BaseModelWithCode, AllegatiMixin):
    """
    Progetto evento principale creato dal commerciale.

    Il commerciale apre il progetto e seleziona i reparti coinvolti.
    Per ogni reparto viene creato automaticamente un ProgettoReparto.
    """

    CODE_PREFIX = "PRJ"
    CODE_LENGTH = 4

    # ========== CLIENTE E EVENTO ==========
    cliente = models.ForeignKey(
        'anagrafica.Cliente',
        on_delete=models.PROTECT,
        related_name='progetti_eventi',
        verbose_name="Cliente"
    )

    nome_evento = models.CharField(
        "Nome Evento",
        max_length=200,
        help_text="Es: Matrimonio Rossi, Concerto Estate 2026"
    )

    TIPO_EVENTO_CHOICES = [
        ('matrimonio', 'Matrimonio'),
        ('concerto', 'Concerto'),
        ('conferenza', 'Conferenza'),
        ('fiera', 'Fiera'),
        ('festival', 'Festival'),
        ('corporate', 'Corporate Event'),
        ('teatro', 'Teatro'),
        ('sport', 'Evento Sportivo'),
        ('televisione', 'Produzione TV'),
        ('altro', 'Altro'),
    ]
    tipo_evento = models.CharField(
        "Tipo Evento",
        max_length=20,
        choices=TIPO_EVENTO_CHOICES
    )

    descrizione_evento = models.TextField(
        "Descrizione Evento",
        blank=True,
        help_text="Descrizione dettagliata dell'evento"
    )

    # ========== DATE EVENTO ==========
    data_evento = models.DateField("Data Evento")
    ora_inizio_evento = models.TimeField("Ora Inizio", null=True, blank=True)
    data_fine_evento = models.DateField("Data Fine Evento", null=True, blank=True)
    ora_fine_evento = models.TimeField("Ora Fine", null=True, blank=True)

    # ========== LOCATION ==========
    location = models.CharField("Nome Location", max_length=300)
    indirizzo_location = models.TextField("Indirizzo Location")
    cap_location = models.CharField("CAP", max_length=10, blank=True)
    citta_location = models.CharField("Città", max_length=100)
    provincia_location = models.CharField("Provincia", max_length=2, blank=True)
    nazione_location = models.CharField("Nazione", max_length=50, default="Italia")

    coordinate_location = models.CharField(
        "Coordinate GPS",
        max_length=100,
        blank=True,
        help_text="Formato: lat,lng"
    )

    # ========== INFORMAZIONI LOGISTICHE INIZIALI ==========
    # Il commerciale fornisce date/orari indicativi che la logistica userà
    data_consegna_richiesta = models.DateTimeField(
        "Data/Ora Consegna Richiesta",
        help_text="Quando la merce deve essere consegnata alla location"
    )
    data_ritiro_richiesta = models.DateTimeField(
        "Data/Ora Ritiro Richiesta",
        help_text="Quando la merce deve essere ritirata dalla location"
    )
    note_logistica_iniziali = models.TextField(
        "Note Logistica Iniziali",
        blank=True,
        help_text="Indicazioni preliminari per la logistica (accessi, vincoli, etc.)"
    )

    # ========== COMMERCIALE ==========
    commerciale = models.ForeignKey(
        'users.User',
        on_delete=models.PROTECT,
        related_name='progetti_eventi_commerciale',
        verbose_name="Commerciale Responsabile"
    )

    # ========== REPARTI COINVOLTI ==========
    # I reparti vengono creati come ProgettoReparto separati
    # Questo campo è denormalizzato per query veloci
    reparti_coinvolti = models.JSONField(
        "Reparti Coinvolti",
        default=list,
        help_text="Lista reparti: ['audio', 'video', 'luci']"
    )

    # ========== STATO PROGETTO ==========
    STATO_CHOICES = [
        ('bozza', 'Bozza'),                         # Appena creato dal commerciale
        ('in_engineering', 'In Engineering'),        # Inviato agli ingegneri
        ('engineering_completato', 'Engineering Completato'),  # Tutti gli engineering ok
        ('in_preparazione', 'In Preparazione'),      # Magazzino/Travel/Scouting al lavoro
        ('pronto', 'Pronto'),                       # Tutto pronto per evento
        ('in_corso', 'Evento in Corso'),            # Evento attivo
        ('completato', 'Completato'),               # Evento finito
        ('annullato', 'Annullato'),
    ]
    stato = models.CharField(
        "Stato Progetto",
        max_length=30,
        choices=STATO_CHOICES,
        default='bozza'
    )

    # ========== BUDGET E COMMERCIALI ==========
    budget_preventivato = models.DecimalField(
        "Budget Preventivato",
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Budget totale del progetto"
    )

    budget_approvato = models.DecimalField(
        "Budget Approvato Cliente",
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )

    note_commerciali = models.TextField(
        "Note Commerciali",
        blank=True,
        help_text="Note riservate al team commerciale"
    )

    # ========== PRIORITÀ ==========
    PRIORITA_CHOICES = [
        ('bassa', 'Bassa'),
        ('normale', 'Normale'),
        ('alta', 'Alta'),
        ('urgente', 'Urgente'),
    ]
    priorita = models.CharField(
        "Priorità",
        max_length=10,
        choices=PRIORITA_CHOICES,
        default='normale'
    )

    # ========== TIMELINE EVENTI ==========
    data_invio_engineering = models.DateTimeField(
        "Data Invio Engineering",
        null=True,
        blank=True,
        help_text="Quando il progetto è stato inviato agli ingegneri"
    )

    data_completamento_engineering = models.DateTimeField(
        "Data Completamento Engineering",
        null=True,
        blank=True,
        help_text="Quando tutti gli engineering sono stati completati"
    )

    data_evento_concluso = models.DateTimeField(
        "Data Conclusione Evento",
        null=True,
        blank=True
    )

    # ========== PARTECIPANTI E CHAT ==========
    partecipanti = models.ManyToManyField(
        'users.User',
        related_name='progetti_partecipati',
        verbose_name="Partecipanti Progetto",
        blank=True,
        help_text="Utenti che partecipano al progetto e alla chat"
    )

    chat_progetto = models.OneToOneField(
        'mail.ChatConversation',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='progetto',
        verbose_name="Chat Progetto",
        help_text="Chat di gruppo automatica per questo progetto"
    )

    # ========== MEZZI ASSEGNATI ==========
    mezzi_assegnati = models.ManyToManyField(
        'automezzi.Automezzo',
        related_name='progetti_assegnati',
        verbose_name="Mezzi Assegnati",
        blank=True,
        help_text="Mezzi necessari per questo progetto (consegna/ritiro)"
    )

    class Meta:
        verbose_name = "Progetto Evento"
        verbose_name_plural = "Progetti Eventi"
        ordering = ['-data_evento', '-created_at']
        indexes = [
            models.Index(fields=['stato']),
            models.Index(fields=['data_evento']),
            models.Index(fields=['commerciale']),
            models.Index(fields=['cliente']),
        ]

    def __str__(self):
        return f"{self.codice} - {self.nome_evento}"

    def get_absolute_url(self):
        return reverse('progetti_eventi:progetto_detail', kwargs={'pk': self.pk})

    @classmethod
    def get_search_fields(cls):
        return ['codice', 'nome_evento', 'descrizione_evento', 'location', 'citta_location']

    def get_search_result_display(self):
        return f"{self.codice} - {self.nome_evento} ({self.data_evento.strftime('%d/%m/%Y')})"

    # ========== PROPERTIES ==========

    @property
    def stato_badge_color(self):
        """Colore badge Bootstrap per stato"""
        colori = {
            'bozza': 'secondary',
            'in_engineering': 'info',
            'engineering_completato': 'primary',
            'in_preparazione': 'warning',
            'pronto': 'success',
            'in_corso': 'danger',
            'completato': 'success',
            'annullato': 'dark',
        }
        return colori.get(self.stato, 'secondary')

    @property
    def giorni_mancanti(self):
        """Giorni mancanti all'evento"""
        if not self.data_evento:
            return None
        delta = self.data_evento - timezone.now().date()
        return delta.days

    @property
    def is_urgente(self):
        """True se l'evento è tra meno di 7 giorni"""
        giorni = self.giorni_mancanti
        return giorni is not None and giorni <= 7 and giorni >= 0

    @property
    def location_completa(self):
        """Indirizzo location formattato"""
        parts = [self.location, self.indirizzo_location]
        if self.cap_location or self.citta_location:
            parts.append(f"{self.cap_location} {self.citta_location}".strip())
        return ", ".join(filter(None, parts))

    @property
    def percentuale_completamento(self):
        """Calcola percentuale completamento basata su reparti"""
        reparti = self.reparti.all()
        if not reparti:
            return 0

        totale = reparti.count()
        completati = reparti.filter(
            engineering_completato=True,
            # Aggiungere altri check quando le app saranno collegate
        ).count()

        return int((completati / totale) * 100)

    # ========== METODI ==========

    def invia_a_engineering(self, user):
        """
        Cambia stato a 'in_engineering' e notifica gli ingegneri.
        Chiamato dal commerciale quando il progetto è pronto.
        """
        if self.stato != 'bozza':
            raise ValidationError(f"Impossibile inviare a engineering: stato attuale è {self.get_stato_display()}")

        self.stato = 'in_engineering'
        self.data_invio_engineering = timezone.now()
        self.save()

        # TODO: Inviare notifiche agli ingegneri assegnati
        # per reparto in self.reparti.all():
        #     if reparto.engineering_assegnato_a:
        #         invia_notifica(reparto.engineering_assegnato_a, ...)

    def check_engineering_completato(self):
        """
        Verifica se tutti gli engineering sono completati.
        Se sì, cambia stato a 'engineering_completato'.
        """
        if self.stato != 'in_engineering':
            return False

        tutti_completati = all(
            reparto.engineering_completato
            for reparto in self.reparti.all()
        )

        if tutti_completati:
            self.stato = 'engineering_completato'
            self.data_completamento_engineering = timezone.now()
            self.save()

            # TODO: Trigger creazione automatica task nelle altre app
            # self.genera_task_magazzino()
            # self.genera_task_logistica()
            # etc.

            return True
        return False

    def genera_task_altre_app(self):
        """
        PLACEHOLDER: Genera automaticamente task nelle app:
        - magazzino
        - logistica
        - travel
        - scouting

        Da implementare quando le app saranno create.
        """
        for reparto in self.reparti.all():
            # magazzino.RichiestaApprontamento.objects.create(
            #     progetto_reparto=reparto,
            #     data_necessita=self.data_consegna_richiesta,
            # )

            # logistica.ConsegnaEvento.objects.create(
            #     progetto_reparto=reparto,
            #     data_consegna=self.data_consegna_richiesta,
            # )

            # etc.
            pass

    def clean(self):
        """Validazioni"""
        super().clean()

        # Data fine >= data inizio
        if self.data_fine_evento and self.data_fine_evento < self.data_evento:
            raise ValidationError({
                'data_fine_evento': 'La data fine non può essere precedente alla data inizio'
            })

        # Consegna prima dell'evento
        if self.data_consegna_richiesta and self.data_evento:
            if self.data_consegna_richiesta.date() > self.data_evento:
                raise ValidationError({
                    'data_consegna_richiesta': 'La consegna deve avvenire prima dell\'evento'
                })


# ============================================================================
# PROGETTO REPARTO (Audio/Video/Luci SEPARATI)
# ============================================================================

class ProgettoReparto(BaseModel, AllegatiMixin):
    """
    Istanza di un reparto (Audio/Video/Luci) all'interno di un progetto.

    CHIAVE ARCHITETTURALE:
    - Ogni reparto è completamente SEPARATO
    - Ha il proprio stato engineering
    - Genera task separati per magazzino/travel/scouting/logistica

    COLLEGAMENTI ALTRE APP:
    - Un ProgettoReparto può avere N RichiestaApprontamento (magazzino)
    - Un ProgettoReparto può avere N ConsegnaEvento (logistica)
    - Un ProgettoReparto può avere N MissioneTecnico (travel)
    - Un ProgettoReparto può avere N RichiestaPersonale (scouting)
    """

    progetto = models.ForeignKey(
        Progetto,
        on_delete=models.CASCADE,
        related_name='reparti',
        verbose_name="Progetto"
    )

    # ========== TIPO REPARTO ==========
    TIPO_REPARTO_CHOICES = [
        ('audio', 'Audio'),
        ('video', 'Video'),
        ('luci', 'Luci'),
    ]
    tipo_reparto = models.CharField(
        "Reparto",
        max_length=10,
        choices=TIPO_REPARTO_CHOICES
    )

    # ========== ENGINEERING ==========
    engineering_assegnato_a = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='progetti_engineering_assegnati',
        verbose_name="Ingegnere Assegnato",
        help_text="Ingegnere responsabile dello studio di questo reparto"
    )

    ENGINEERING_STATO_CHOICES = [
        ('da_assegnare', 'Da Assegnare'),
        ('assegnato', 'Assegnato'),
        ('in_studio', 'In Studio'),
        ('completato', 'Completato'),
    ]
    engineering_stato = models.CharField(
        "Stato Engineering",
        max_length=20,
        choices=ENGINEERING_STATO_CHOICES,
        default='da_assegnare'
    )

    engineering_completato = models.BooleanField(
        "Engineering Completato",
        default=False,
        help_text="True quando l'ingegnere ha completato lo studio e approvato le liste prodotti"
    )

    data_assegnazione_engineering = models.DateTimeField(
        "Data Assegnazione Engineering",
        null=True,
        blank=True
    )

    data_completamento_engineering = models.DateTimeField(
        "Data Completamento Engineering",
        null=True,
        blank=True
    )

    note_engineering = models.TextField(
        "Note Engineering",
        blank=True,
        help_text="Note tecniche dell'ingegnere"
    )

    # ========== STATO GLOBALE REPARTO ==========
    # Denormalizzato per performance, aggiornato da segnali delle altre app

    magazzino_ready = models.BooleanField(
        "Magazzino Pronto",
        default=False,
        help_text="True quando tutti i prodotti sono approntati"
    )

    logistica_ready = models.BooleanField(
        "Logistica Pronta",
        default=False,
        help_text="True quando consegna/ritiro sono pianificati"
    )

    travel_ready = models.BooleanField(
        "Travel Pronto",
        default=False,
        help_text="True quando tutti i viaggi sono organizzati"
    )

    scouting_ready = models.BooleanField(
        "Scouting Completato",
        default=False,
        help_text="True quando tutto il personale è stato trovato"
    )

    # ========== INFORMAZIONI RIEPILOGATIVE ==========
    # Questi campi vengono popolati dall'engineering e usati dalle altre app

    numero_tecnici_necessari = models.PositiveIntegerField(
        "Numero Tecnici Necessari",
        default=0,
        help_text="Definito dall'engineering"
    )

    numero_facchini_necessari = models.PositiveIntegerField(
        "Numero Facchini Necessari",
        default=0,
        help_text="Definito dall'engineering"
    )

    metri_cubi_totali = models.DecimalField(
        "Metri Cubi Totali",
        max_digits=8,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Calcolato automaticamente dalle liste prodotti"
    )

    peso_totale_kg = models.DecimalField(
        "Peso Totale (kg)",
        max_digits=8,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Calcolato automaticamente dalle liste prodotti"
    )

    class Meta:
        verbose_name = "Progetto Reparto"
        verbose_name_plural = "Progetti Reparti"
        unique_together = [['progetto', 'tipo_reparto']]
        ordering = ['progetto', 'tipo_reparto']
        indexes = [
            models.Index(fields=['progetto', 'tipo_reparto']),
            models.Index(fields=['engineering_assegnato_a']),
            models.Index(fields=['engineering_stato']),
        ]

    def __str__(self):
        return f"{self.progetto.codice} - {self.get_tipo_reparto_display()}"

    def get_absolute_url(self):
        return reverse('progetti_eventi:reparto_detail', kwargs={'pk': self.pk})

    # ========== PROPERTIES ==========

    @property
    def icon(self):
        """Icona Bootstrap per il reparto"""
        icons = {
            'audio': 'volume-up',
            'video': 'camera-video',
            'luci': 'lightbulb',
        }
        return icons.get(self.tipo_reparto, 'gear')

    @property
    def stato_globale(self):
        """Calcola stato globale del reparto"""
        if not self.engineering_completato:
            return 'engineering_pending'

        if all([
            self.magazzino_ready,
            self.logistica_ready,
            self.travel_ready,
            self.scouting_ready
        ]):
            return 'pronto'

        return 'in_preparazione'

    @property
    def stato_globale_display(self):
        """Label leggibile dello stato globale"""
        stati = {
            'engineering_pending': 'In Engineering',
            'in_preparazione': 'In Preparazione',
            'pronto': 'Pronto',
        }
        return stati.get(self.stato_globale, 'Sconosciuto')

    @property
    def stato_globale_color(self):
        """Colore badge per stato globale"""
        colori = {
            'engineering_pending': 'info',
            'in_preparazione': 'warning',
            'pronto': 'success',
        }
        return colori.get(self.stato_globale, 'secondary')

    @property
    def percentuale_completamento(self):
        """Percentuale completamento generale"""
        steps = [
            self.engineering_completato,
            self.magazzino_ready,
            self.logistica_ready,
            self.travel_ready,
            self.scouting_ready,
        ]
        completati = sum(steps)
        totale = len(steps)
        return int((completati / totale) * 100)

    # ========== METODI ==========

    def assegna_engineering(self, ingegnere, user):
        """Assegna l'ingegnere al reparto"""
        self.engineering_assegnato_a = ingegnere
        self.engineering_stato = 'assegnato'
        self.data_assegnazione_engineering = timezone.now()
        self.save()

        # TODO: Notifica ingegnere
        # invia_notifica(ingegnere, f"Ti è stato assegnato {self}")

    def completa_engineering(self, user):
        """Marca engineering come completato"""
        if not self.liste_prodotti.filter(approvata=True).exists():
            raise ValidationError("Impossibile completare: nessuna lista prodotti approvata")

        self.engineering_completato = True
        self.engineering_stato = 'completato'
        self.data_completamento_engineering = timezone.now()
        self.save()

        # Trigger check sul progetto principale
        self.progetto.check_engineering_completato()

        # TODO: Genera task per altre app
        # self.genera_task_magazzino()
        # self.genera_task_logistica()
        # etc.

    def calcola_totali_da_liste(self):
        """
        Ricalcola metri_cubi_totali e peso_totale_kg dalle liste prodotti approvate.
        Chiamato quando viene approvata una lista prodotti.
        """
        liste_approvate = self.liste_prodotti.filter(approvata=True)

        metri_cubi = Decimal('0.00')
        peso = Decimal('0.00')

        for lista in liste_approvate:
            for prodotto in lista.prodotti.all():
                # TODO: integrare con app magazzino per ottenere dati reali
                # prodotto.volume_m3 e prodotto.peso_kg
                pass

        self.metri_cubi_totali = metri_cubi
        self.peso_totale_kg = peso
        self.save(update_fields=['metri_cubi_totali', 'peso_totale_kg'])

    def genera_task_magazzino(self):
        """
        PLACEHOLDER: Crea RichiestaApprontamento nell'app magazzino.
        Da implementare quando l'app magazzino sarà pronta.
        """
        # from magazzino.models import RichiestaApprontamento
        # RichiestaApprontamento.objects.create(
        #     progetto_reparto=self,
        #     data_necessita=self.progetto.data_consegna_richiesta,
        #     lista_prodotti=self.liste_prodotti.filter(approvata=True).first(),
        # )
        pass

    def genera_task_logistica(self):
        """PLACEHOLDER: Crea task consegna/ritiro nell'app logistica"""
        # from logistica.models import ConsegnaEvento, RitiroEvento
        # ConsegnaEvento.objects.create(...)
        # RitiroEvento.objects.create(...)
        pass

    def genera_task_travel(self):
        """PLACEHOLDER: Crea task viaggi nell'app travel"""
        # from travel.models import MissioneTecnico
        # for i in range(self.numero_tecnici_necessari):
        #     MissioneTecnico.objects.create(...)
        pass

    def genera_task_scouting(self):
        """PLACEHOLDER: Crea richiesta personale nell'app scouting"""
        # from scouting.models import RichiestaPersonale
        # RichiestaPersonale.objects.create(
        #     progetto_reparto=self,
        #     numero_tecnici=self.numero_tecnici_necessari,
        #     numero_facchini=self.numero_facchini_necessari,
        # )
        pass


# ============================================================================
# ENGINEERING TASK
# ============================================================================

class EngineeringTask(BaseModel, AllegatiMixin):
    """
    Task di engineering per un reparto.
    L'ingegnere studia il progetto e crea liste prodotti.
    """

    progetto_reparto = models.ForeignKey(
        ProgettoReparto,
        on_delete=models.CASCADE,
        related_name='engineering_tasks',
        verbose_name="Progetto Reparto"
    )

    titolo = models.CharField("Titolo Task", max_length=200)
    descrizione = models.TextField("Descrizione", blank=True)

    STATO_CHOICES = [
        ('da_iniziare', 'Da Iniziare'),
        ('in_corso', 'In Corso'),
        ('completato', 'Completato'),
    ]
    stato = models.CharField("Stato", max_length=20, choices=STATO_CHOICES, default='da_iniziare')

    data_inizio = models.DateTimeField("Data Inizio", null=True, blank=True)
    data_completamento = models.DateTimeField("Data Completamento", null=True, blank=True)

    ore_stimate = models.DecimalField(
        "Ore Stimate",
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )

    ore_effettive = models.DecimalField(
        "Ore Effettive",
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )

    note = models.TextField("Note", blank=True)

    class Meta:
        verbose_name = "Engineering Task"
        verbose_name_plural = "Engineering Tasks"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.titolo} - {self.progetto_reparto}"

    def inizia(self):
        """Inizia il task"""
        self.stato = 'in_corso'
        self.data_inizio = timezone.now()
        self.save()

    def completa(self):
        """Completa il task"""
        self.stato = 'completato'
        self.data_completamento = timezone.now()
        self.save()


# ============================================================================
# LISTE PRODOTTI (OUTPUT ENGINEERING)
# ============================================================================

class ListaProdotti(BaseModel, AllegatiMixin):
    """
    Lista prodotti creata dall'engineering.
    Una volta approvata, viene usata dal magazzino per l'approntamento.
    """

    progetto_reparto = models.ForeignKey(
        ProgettoReparto,
        on_delete=models.CASCADE,
        related_name='liste_prodotti',
        verbose_name="Progetto Reparto"
    )

    nome_lista = models.CharField(
        "Nome Lista",
        max_length=200,
        help_text="Es: Setup Principale, Backup, Extra"
    )

    descrizione = models.TextField("Descrizione", blank=True)

    # ========== APPROVAZIONE ==========
    approvata = models.BooleanField("Approvata", default=False)
    approvata_da = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='liste_prodotti_approvate',
        verbose_name="Approvata da"
    )
    data_approvazione = models.DateTimeField("Data Approvazione", null=True, blank=True)

    # ========== STATO ==========
    STATO_CHOICES = [
        ('bozza', 'Bozza'),
        ('in_revisione', 'In Revisione'),
        ('approvata', 'Approvata'),
        ('rifiutata', 'Rifiutata'),
    ]
    stato = models.CharField("Stato", max_length=20, choices=STATO_CHOICES, default='bozza')

    note_approvazione = models.TextField("Note Approvazione", blank=True)

    class Meta:
        verbose_name = "Lista Prodotti"
        verbose_name_plural = "Liste Prodotti"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['progetto_reparto', 'approvata']),
        ]

    def __str__(self):
        return f"{self.nome_lista} - {self.progetto_reparto}"

    def get_absolute_url(self):
        return reverse('progetti_eventi:lista_prodotti_detail', kwargs={'pk': self.pk})

    @property
    def numero_prodotti(self):
        """Numero totale prodotti nella lista"""
        return self.prodotti.count()

    @property
    def quantita_totale(self):
        """Somma delle quantità"""
        return sum(p.quantita for p in self.prodotti.all())

    def approva(self, user, note=''):
        """Approva la lista prodotti"""
        self.approvata = True
        self.approvata_da = user
        self.data_approvazione = timezone.now()
        self.stato = 'approvata'
        self.note_approvazione = note
        self.save()

        # Ricalcola totali sul reparto
        self.progetto_reparto.calcola_totali_da_liste()

        # Verifica se è la prima lista approvata
        if self.progetto_reparto.liste_prodotti.filter(approvata=True).count() == 1:
            # Può triggerare il completamento engineering se l'ingegnere decide
            pass

    def rifiuta(self, user, motivo):
        """Rifiuta la lista"""
        self.stato = 'rifiutata'
        self.note_approvazione = motivo
        self.save()


class ProdottoLista(models.Model):
    """
    Singolo prodotto nella lista engineering.

    INTEGRAZIONE MAGAZZINO:
    - Se esiste app magazzino, collegare a magazzino.Prodotto
    - Altrimenti usare campi denormalizzati
    """

    lista = models.ForeignKey(
        ListaProdotti,
        on_delete=models.CASCADE,
        related_name='prodotti',
        verbose_name="Lista"
    )

    # ========== DATI PRODOTTO ==========
    # OPZIONE A: Collegamento a magazzino (quando sarà pronto)
    # prodotto_magazzino = models.ForeignKey(
    #     'magazzino.Prodotto',
    #     on_delete=models.PROTECT,
    #     null=True,
    #     blank=True
    # )

    # OPZIONE B: Dati denormalizzati (per ora)
    codice_prodotto = models.CharField(
        "Codice Prodotto",
        max_length=100,
        help_text="Codice univoco del prodotto"
    )

    nome_prodotto = models.CharField("Nome Prodotto", max_length=200)

    categoria_prodotto = models.CharField(
        "Categoria",
        max_length=100,
        blank=True,
        help_text="Es: Casse, Microfoni, Videocamere, Fari, etc."
    )

    # ========== QUANTITÀ ==========
    quantita = models.PositiveIntegerField("Quantità", default=1)

    # ========== DIMENSIONI (opzionali) ==========
    lunghezza_cm = models.DecimalField(
        "Lunghezza (cm)",
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True
    )
    larghezza_cm = models.DecimalField(
        "Larghezza (cm)",
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True
    )
    altezza_cm = models.DecimalField(
        "Altezza (cm)",
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True
    )
    peso_kg = models.DecimalField(
        "Peso (kg)",
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True
    )

    # ========== NOTE ==========
    note = models.TextField("Note", blank=True)

    priorita = models.CharField(
        "Priorità",
        max_length=10,
        choices=[
            ('normale', 'Normale'),
            ('alta', 'Alta'),
            ('critica', 'Critica'),
        ],
        default='normale'
    )

    class Meta:
        verbose_name = "Prodotto Lista"
        verbose_name_plural = "Prodotti Lista"
        ordering = ['categoria_prodotto', 'nome_prodotto']

    def __str__(self):
        return f"{self.codice_prodotto} - {self.nome_prodotto} (x{self.quantita})"

    @property
    def volume_m3(self):
        """Calcola volume in metri cubi"""
        if all([self.lunghezza_cm, self.larghezza_cm, self.altezza_cm]):
            volume_cm3 = self.lunghezza_cm * self.larghezza_cm * self.altezza_cm
            return (volume_cm3 / 1_000_000) * self.quantita
        return None
