"""
Models for Mail App - ModularBEF

Sistema completo per gestione email, promemoria e chat interna.
Include invio/ricezione email, template, code, statistiche, promemoria e chat.
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.validators import MinValueValidator, MaxValueValidator, EmailValidator
from django.utils import timezone
from django.urls import reverse
from core.models import BaseModel, BaseModelSimple
from core.mixins import AllegatiMixin
import hashlib

User = get_user_model()


# ============================================================================
# EMAIL MODELS
# ============================================================================


class EmailConfiguration(BaseModel):
    """
    Configurazione email per utente (SMTP + IMAP).

    Permette ad ogni utente di configurare il proprio account email
    per invio e ricezione messaggi.
    """

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='mail_config',
        verbose_name="Utente"
    )

    # ===== SMTP Configuration =====
    display_name = models.CharField(
        "Nome Visualizzato",
        max_length=200,
        help_text="Nome che apparirà come mittente"
    )
    email_address = models.EmailField(
        "Indirizzo Email",
        validators=[EmailValidator()],
        help_text="Indirizzo email completo"
    )
    smtp_server = models.CharField("Server SMTP", max_length=255)
    smtp_port = models.IntegerField(
        "Porta SMTP",
        default=587,
        validators=[MinValueValidator(1), MaxValueValidator(65535)]
    )
    smtp_username = models.CharField("Username SMTP", max_length=255)
    smtp_password = models.CharField(
        "Password SMTP",
        max_length=255,
        help_text="TODO: Criptare con django-cryptography"
    )
    use_tls = models.BooleanField("Usa TLS", default=True)
    use_ssl = models.BooleanField("Usa SSL", default=False)

    # ===== IMAP Configuration =====
    imap_server = models.CharField(
        "Server IMAP",
        max_length=255,
        blank=True,
        help_text="Server per ricezione email"
    )
    imap_port = models.IntegerField(
        "Porta IMAP",
        default=993,
        validators=[MinValueValidator(1), MaxValueValidator(65535)]
    )
    imap_username = models.CharField("Username IMAP", max_length=255, blank=True)
    imap_password = models.CharField(
        "Password IMAP",
        max_length=255,
        blank=True,
        help_text="TODO: Criptare"
    )
    imap_use_tls = models.BooleanField("IMAP usa TLS", default=False)
    imap_use_ssl = models.BooleanField("IMAP usa SSL", default=True)
    imap_enabled = models.BooleanField(
        "IMAP Abilitato",
        default=False,
        help_text="Abilita ricezione automatica email"
    )
    last_imap_sync = models.DateTimeField(
        "Ultima Sincronizzazione IMAP",
        null=True,
        blank=True
    )
    last_imap_error = models.TextField("Ultimo Errore IMAP", blank=True)

    # ===== Status & Limits =====
    is_verified = models.BooleanField(
        "Configurazione Verificata",
        default=False,
        help_text="Configurazione testata con successo"
    )
    last_test_at = models.DateTimeField("Ultimo Test", null=True, blank=True)
    last_error = models.TextField("Ultimo Errore", blank=True)

    daily_limit = models.IntegerField(
        "Limite Giornaliero",
        default=500,
        validators=[MinValueValidator(1)],
        help_text="Numero massimo email/giorno"
    )
    hourly_limit = models.IntegerField(
        "Limite Orario",
        default=50,
        validators=[MinValueValidator(1)],
        help_text="Numero massimo email/ora"
    )

    class Meta:
        verbose_name = "Configurazione Email"
        verbose_name_plural = "Configurazioni Email"
        ordering = ['user__username']

    def __str__(self):
        return f"{self.user.username} - {self.email_address}"

    @property
    def is_configured(self):
        """Verifica se la configurazione SMTP è completa"""
        return all([
            self.email_address,
            self.smtp_server,
            self.smtp_username,
            self.smtp_password,
        ])

    @property
    def is_imap_configured(self):
        """Verifica se la configurazione IMAP è completa"""
        return all([
            self.imap_enabled,
            self.imap_server,
            self.imap_username,
            self.imap_password,
        ])


class EmailTemplate(BaseModel):
    """
    Template riutilizzabili per email.

    Supporta variabili con sintassi {{variabile}} per personalizzazione.
    """

    CATEGORY_CHOICES = [
        ('preventivi', 'Preventivi'),
        ('automezzi', 'Automezzi'),
        ('stabilimenti', 'Stabilimenti'),
        ('acquisti', 'Acquisti'),
        ('fatturazione', 'Fatturazione'),
        ('anagrafica', 'Anagrafica'),
        ('hr', 'Risorse Umane'),
        ('comunicazioni', 'Comunicazioni'),
        ('sistema', 'Sistema'),
        ('generico', 'Generico'),
    ]

    nome = models.CharField("Nome Template", max_length=200, unique=True)
    slug = models.SlugField("Slug", max_length=200, unique=True)
    descrizione = models.TextField("Descrizione", blank=True)

    categoria = models.CharField(
        "Categoria",
        max_length=50,
        choices=CATEGORY_CHOICES,
        default='generico'
    )

    # Content
    subject = models.CharField("Oggetto", max_length=500)
    content_html = models.TextField(
        "Contenuto HTML",
        help_text="Supporta variabili {{nome_variabile}}"
    )
    content_text = models.TextField(
        "Contenuto Testo",
        blank=True,
        help_text="Versione testo semplice (opzionale)"
    )

    # Variables
    available_variables = models.JSONField(
        "Variabili Disponibili",
        default=list,
        blank=True,
        help_text="Lista variabili: ['nome', 'cognome', 'azienda']"
    )
    sample_data = models.JSONField(
        "Dati Esempio",
        default=dict,
        blank=True,
        help_text="Dati esempio per preview: {'nome': 'Mario', 'cognome': 'Rossi'}"
    )

    # Status
    is_system = models.BooleanField(
        "Template Sistema",
        default=False,
        help_text="Template di sistema (non modificabile)"
    )

    # Stats
    usage_count = models.IntegerField("Utilizzi", default=0, editable=False)

    class Meta:
        verbose_name = "Template Email"
        verbose_name_plural = "Template Email"
        ordering = ['categoria', 'nome']

    def __str__(self):
        return f"{self.nome} ({self.get_categoria_display()})"

    def render(self, context):
        """
        Renderizza il template con il contesto fornito.

        Args:
            context (dict): Dizionario variabili {nome: valore}

        Returns:
            tuple: (subject, html_content, text_content)
        """
        subject = self.subject
        html = self.content_html
        text = self.content_text or ""

        # Simple variable substitution
        for key, value in context.items():
            placeholder = f"{{{{{key}}}}}"  # {{variabile}}
            subject = subject.replace(placeholder, str(value))
            html = html.replace(placeholder, str(value))
            text = text.replace(placeholder, str(value))

        return subject, html, text

    def increment_usage(self):
        """Incrementa contatore utilizzi"""
        self.usage_count += 1
        self.save(update_fields=['usage_count'])


class EmailFolder(BaseModelSimple):
    """
    Cartelle per organizzare email (stile Gmail).
    """

    FOLDER_TYPE_CHOICES = [
        ('inbox', 'Posta in Arrivo'),
        ('sent', 'Inviati'),
        ('drafts', 'Bozze'),
        ('trash', 'Cestino'),
        ('spam', 'Spam'),
        ('archive', 'Archivio'),
        ('custom', 'Personalizzata'),
    ]

    config = models.ForeignKey(
        EmailConfiguration,
        on_delete=models.CASCADE,
        related_name='folders',
        verbose_name="Configurazione"
    )
    name = models.CharField("Nome Cartella", max_length=100)
    folder_type = models.CharField(
        "Tipo Cartella",
        max_length=20,
        choices=FOLDER_TYPE_CHOICES,
        default='custom'
    )

    # Stats (denormalized for performance)
    total_messages = models.IntegerField("Totale Messaggi", default=0)
    unread_messages = models.IntegerField("Non Letti", default=0)

    class Meta:
        verbose_name = "Cartella Email"
        verbose_name_plural = "Cartelle Email"
        unique_together = [('config', 'name')]
        ordering = ['folder_type', 'name']

    def __str__(self):
        return f"{self.config.user.username} - {self.name}"

    def update_message_count(self):
        """Aggiorna contatori messaggi"""
        messages = self.messages.all()
        self.total_messages = messages.count()
        self.unread_messages = messages.filter(is_read=False).count()
        self.save(update_fields=['total_messages', 'unread_messages'])

    def update_counts(self):
        """Aggiorna contatori messaggi"""
        messages = self.messages.all()
        self.total_messages = messages.count()
        self.unread_messages = messages.filter(is_read=False).count()
        self.save(update_fields=['total_messages', 'unread_messages'])


class EmailLabel(BaseModel):
    """
    Etichette Gmail-style per categorizzare email.
    """

    configuration = models.ForeignKey(
        EmailConfiguration,
        on_delete=models.CASCADE,
        related_name='labels',
        verbose_name="Configurazione"
    )
    name = models.CharField("Nome Etichetta", max_length=100)
    slug = models.SlugField("Slug", max_length=100)
    color = models.CharField(
        "Colore",
        max_length=7,
        default='#4285f4',
        help_text="Colore esadecimale es. #4285f4"
    )
    icon = models.CharField(
        "Icona",
        max_length=50,
        default='tag',
        help_text="Nome icona Bootstrap Icons (es. 'tag', 'star')"
    )
    order = models.IntegerField("Ordine", default=0)

    is_visible = models.BooleanField("Visibile", default=True)
    is_system = models.BooleanField("Etichetta Sistema", default=False)

    # Stats
    message_count = models.IntegerField("N. Messaggi", default=0, editable=False)

    class Meta:
        verbose_name = "Etichetta Email"
        verbose_name_plural = "Etichette Email"
        unique_together = [('configuration', 'slug')]
        ordering = ['order', 'name']

    def __str__(self):
        return f"{self.name} ({self.configuration.user.username})"

    def update_message_count(self):
        """Aggiorna contatore messaggi"""
        self.message_count = self.messages.count()
        self.save(update_fields=['message_count'])


class EmailMessage(BaseModel, AllegatiMixin):
    """
    Messaggio email (in arrivo o in uscita).

    Usa AllegatiMixin per gestione allegati automatica.
    """

    DIRECTION_CHOICES = [
        ('incoming', 'In Arrivo'),
        ('outgoing', 'In Uscita'),
    ]

    STATUS_CHOICES = [
        ('draft', 'Bozza'),
        ('pending', 'In Attesa'),
        ('queued', 'In Coda'),
        ('sending', 'Invio in Corso'),
        ('sent', 'Inviato'),
        ('delivered', 'Consegnato'),
        ('failed', 'Fallito'),
        ('bounced', 'Respinto'),
        ('received', 'Ricevuto'),
    ]

    # Configuration
    sender_config = models.ForeignKey(
        EmailConfiguration,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name="Configurazione Mittente"
    )
    folder = models.ForeignKey(
        EmailFolder,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='messages',
        verbose_name="Cartella"
    )

    # Identification
    message_id = models.CharField(
        "Message-ID",
        max_length=500,
        blank=True,
        db_index=True,
        help_text="Message-ID header del server"
    )
    thread_id = models.CharField(
        "Thread ID",
        max_length=500,
        blank=True,
        db_index=True,
        help_text="ID conversazione"
    )
    server_uid = models.CharField(
        "Server UID",
        max_length=100,
        blank=True,
        help_text="UID del messaggio sul server IMAP"
    )

    # Recipients
    to_addresses = models.JSONField(
        "Destinatari",
        default=list,
        help_text="Lista email destinatari"
    )
    cc_addresses = models.JSONField("CC", default=list, blank=True)
    bcc_addresses = models.JSONField("BCC", default=list, blank=True)

    # Sender
    from_address = models.EmailField("Da (Email)")
    from_name = models.CharField("Da (Nome)", max_length=200, blank=True)
    reply_to = models.EmailField("Reply-To", blank=True)

    # Content
    subject = models.CharField("Oggetto", max_length=998)
    content_html = models.TextField("Contenuto HTML", blank=True)
    content_text = models.TextField("Contenuto Testo", blank=True)
    template_used = models.ForeignKey(
        EmailTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='messages',
        verbose_name="Template Usato"
    )
    content_size = models.IntegerField(
        "Dimensione Contenuto (bytes)",
        default=0,
        editable=False
    )

    # Attachments info (AllegatiMixin provides .allegati property)
    has_attachments = models.BooleanField("Ha Allegati", default=False)
    attachments_info = models.JSONField(
        "Info Allegati",
        default=list,
        blank=True,
        help_text="Metadata allegati per quick access"
    )

    # Direction & Status
    direction = models.CharField(
        "Direzione",
        max_length=20,
        choices=DIRECTION_CHOICES,
        default='outgoing',
        db_index=True
    )
    status = models.CharField(
        "Stato",
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        db_index=True
    )

    # Flags
    is_read = models.BooleanField("Letto", default=False, db_index=True)
    is_flagged = models.BooleanField("Importante", default=False)
    is_spam = models.BooleanField("Spam", default=False)

    # Labels (many-to-many)
    labels = models.ManyToManyField(
        EmailLabel,
        blank=True,
        related_name='messages',
        verbose_name="Etichette"
    )

    # Delivery
    smtp_response = models.TextField("Risposta SMTP", blank=True)
    error_message = models.TextField("Messaggio Errore", blank=True)
    delivery_attempts = models.IntegerField("Tentativi Consegna", default=0)

    # Generic Relation (collega a qualsiasi model)
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Tipo Oggetto Collegato"
    )
    object_id = models.CharField("ID Oggetto Collegato", max_length=255, blank=True)
    related_object = GenericForeignKey('content_type', 'object_id')
    related_description = models.CharField(
        "Descrizione Collegamento",
        max_length=500,
        blank=True
    )

    # Dates
    sent_at = models.DateTimeField("Inviato il", null=True, blank=True)
    received_at = models.DateTimeField("Ricevuto il", null=True, blank=True)

    class Meta:
        verbose_name = "Messaggio Email"
        verbose_name_plural = "Messaggi Email"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['sender_config', 'folder']),
            models.Index(fields=['message_id']),
            models.Index(fields=['direction', 'status']),
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        direction_icon = "📤" if self.direction == 'outgoing' else "📥"
        return f"{direction_icon} {self.subject[:50]}"

    def save(self, *args, **kwargs):
        """Override save per calcolare content_size"""
        self.content_size = len(self.content_html) + len(self.content_text)
        super().save(*args, **kwargs)

    @property
    def content_hash(self):
        """Hash MD5 del contenuto per deduplicazione"""
        content = f"{self.subject}{self.content_text}{self.content_html}"
        return hashlib.md5(content.encode()).hexdigest()

    def mark_as_sent(self):
        """Segna come inviato con successo"""
        self.status = 'sent'
        self.sent_at = timezone.now()
        self.save(update_fields=['status', 'sent_at', 'updated_at'])

    def mark_as_failed(self, error_msg):
        """Segna come fallito"""
        self.status = 'failed'
        self.error_message = error_msg
        self.delivery_attempts += 1
        self.save(update_fields=['status', 'error_message', 'delivery_attempts', 'updated_at'])

    def mark_as_read(self):
        """Segna come letto"""
        if not self.is_read:
            self.is_read = True
            self.save(update_fields=['is_read', 'updated_at'])
            if self.folder:
                self.folder.update_counts()

    def toggle_flag(self):
        """Toggle flag importante"""
        self.is_flagged = not self.is_flagged
        self.save(update_fields=['is_flagged', 'updated_at'])

    def get_absolute_url(self):
        """URL dettaglio messaggio"""
        return reverse('mail:message_detail', kwargs={'pk': self.pk})


class EmailQueue(BaseModel):
    """
    Coda per invio email asincrono/schedulato.
    """

    STATUS_CHOICES = [
        ('pending', 'In Attesa'),
        ('processing', 'In Elaborazione'),
        ('sent', 'Inviato'),
        ('failed', 'Fallito'),
        ('cancelled', 'Annullato'),
    ]

    config = models.ForeignKey(
        EmailConfiguration,
        on_delete=models.CASCADE,
        related_name='queued_messages',
        verbose_name="Configurazione"
    )

    # Recipients
    to_addresses = models.JSONField("Destinatari", default=list)
    cc_addresses = models.JSONField("CC", default=list, blank=True)
    bcc_addresses = models.JSONField("BCC", default=list, blank=True)

    # Content
    subject = models.CharField("Oggetto", max_length=998)
    content_html = models.TextField("Contenuto HTML", blank=True)
    content_text = models.TextField("Contenuto Testo", blank=True)

    # Priority & Scheduling
    priority = models.IntegerField(
        "Priorità",
        default=5,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text="1=massima, 10=minima"
    )
    scheduled_at = models.DateTimeField(
        "Programmato per",
        default=timezone.now
    )

    # Retry logic
    max_attempts = models.IntegerField("Max Tentativi", default=3)
    attempt_count = models.IntegerField("Tentativi Effettuati", default=0)

    # Status
    status = models.CharField(
        "Stato",
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        db_index=True
    )
    error_message = models.TextField("Messaggio Errore", blank=True)
    sent_at = models.DateTimeField("Inviato il", null=True, blank=True)

    # Generic Relation
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    object_id = models.CharField(max_length=255, blank=True)
    source_object = GenericForeignKey('content_type', 'object_id')

    class Meta:
        verbose_name = "Email in Coda"
        verbose_name_plural = "Email in Coda"
        ordering = ['priority', 'scheduled_at', 'created_at']
        indexes = [
            models.Index(fields=['status', 'scheduled_at']),
            models.Index(fields=['config', 'status']),
        ]

    def __str__(self):
        return f"Queue: {self.subject[:50]} ({self.get_status_display()})"


class EmailStats(BaseModelSimple):
    """
    Statistiche giornaliere email per configurazione.
    """

    config = models.ForeignKey(
        EmailConfiguration,
        on_delete=models.CASCADE,
        related_name='stats',
        verbose_name="Configurazione"
    )
    date = models.DateField("Data", default=timezone.now)

    # General counters
    emails_sent = models.IntegerField("Email Inviate", default=0)
    emails_failed = models.IntegerField("Email Fallite", default=0)
    emails_bounced = models.IntegerField("Email Respinte", default=0)
    emails_received = models.IntegerField("Email Ricevute", default=0)

    # Category breakdown
    preventivi_sent = models.IntegerField("Preventivi Inviati", default=0)
    automezzi_sent = models.IntegerField("Automezzi Inviati", default=0)
    acquisti_sent = models.IntegerField("Acquisti Inviati", default=0)
    hr_sent = models.IntegerField("HR Inviati", default=0)
    comunicazioni_sent = models.IntegerField("Comunicazioni Inviate", default=0)

    class Meta:
        verbose_name = "Statistiche Email"
        verbose_name_plural = "Statistiche Email"
        unique_together = [('config', 'date')]
        ordering = ['-date']

    def __str__(self):
        return f"{self.config.user.username} - {self.date}"

    @property
    def success_rate(self):
        """Calcola percentuale successo"""
        total = self.emails_sent + self.emails_failed
        if total == 0:
            return 0
        return (self.emails_sent / total) * 100


class EmailLog(BaseModelSimple):
    """
    Log completo di tutte le operazioni email (audit trail).
    """

    EVENT_TYPE_CHOICES = [
        ('send', 'Invio'),
        ('receive', 'Ricezione'),
        ('sync', 'Sincronizzazione'),
        ('error', 'Errore'),
        ('config', 'Configurazione'),
        ('test', 'Test'),
    ]

    config = models.ForeignKey(
        EmailConfiguration,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='logs',
        verbose_name="Configurazione"
    )
    message = models.ForeignKey(
        EmailMessage,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='logs',
        verbose_name="Messaggio"
    )

    # Event
    event_type = models.CharField(
        "Tipo Evento",
        max_length=20,
        choices=EVENT_TYPE_CHOICES,
        db_index=True
    )
    event_description = models.CharField("Descrizione", max_length=500)
    event_data = models.JSONField(
        "Dati Evento",
        default=dict,
        blank=True
    )

    # Result
    success = models.BooleanField("Successo", default=True)
    error_message = models.TextField("Messaggio Errore", blank=True)

    # Context
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Utente"
    )
    ip_address = models.GenericIPAddressField("Indirizzo IP", null=True, blank=True)
    user_agent = models.CharField("User Agent", max_length=500, blank=True)

    timestamp = models.DateTimeField("Data/Ora", default=timezone.now, db_index=True)

    class Meta:
        verbose_name = "Log Email"
        verbose_name_plural = "Log Email"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['config', 'event_type']),
            models.Index(fields=['-timestamp']),
        ]

    def __str__(self):
        return f"{self.get_event_type_display()} - {self.timestamp}"


# ============================================================================
# PROMEMORIA MODELS
# ============================================================================


class Promemoria(BaseModel, AllegatiMixin):
    """
    Sistema promemoria/note per utenti.

    Permette di creare promemoria con date scadenza, priorità, allegati.
    Usa AllegatiMixin per allegare file.
    """

    PRIORITY_CHOICES = [
        ('bassa', 'Bassa'),
        ('media', 'Media'),
        ('alta', 'Alta'),
        ('urgente', 'Urgente'),
    ]

    STATUS_CHOICES = [
        ('pending', 'In Attesa'),
        ('in_progress', 'In Corso'),
        ('completed', 'Completato'),
        ('cancelled', 'Annullato'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='promemoria',
        verbose_name="Creato da"
    )

    assegnato_a = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='promemoria_assegnati',
        verbose_name="Assegnato a",
        null=True,
        blank=True,
        help_text="Utente a cui è assegnato il promemoria. Se vuoto, assegnato al creatore."
    )

    titolo = models.CharField("Titolo", max_length=200)
    descrizione = models.TextField("Descrizione", blank=True)

    # Priority & Status
    priorita = models.CharField(
        "Priorità",
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='media'
    )
    stato = models.CharField(
        "Stato",
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        db_index=True
    )

    # Dates
    data_scadenza = models.DateTimeField(
        "Data Scadenza",
        null=True,
        blank=True,
        help_text="Scadenza promemoria"
    )
    completato_il = models.DateTimeField("Completato il", null=True, blank=True)

    # Notifications
    notifica_email = models.BooleanField(
        "Notifica Email",
        default=False,
        help_text="Invia email alla scadenza"
    )
    notifica_giorni_prima = models.IntegerField(
        "Giorni Preavviso",
        default=1,
        validators=[MinValueValidator(0)],
        help_text="Giorni prima della scadenza per notifica"
    )
    notificato = models.BooleanField("Notifica Inviata", default=False)

    # Generic Relation (collega a qualsiasi oggetto)
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Tipo Oggetto Collegato"
    )
    object_id = models.CharField("ID Oggetto Collegato", max_length=255, blank=True)
    related_object = GenericForeignKey('content_type', 'object_id')

    # Tags
    tags = models.JSONField(
        "Tag",
        default=list,
        blank=True,
        help_text="Lista tag: ['lavoro', 'urgente', 'cliente']"
    )
    
    class Meta:
        verbose_name = "Promemoria"
        verbose_name_plural = "Promemoria"
        ordering = ['-data_scadenza', '-created_at']
        indexes = [
            models.Index(fields=['user', 'stato']),
            models.Index(fields=['data_scadenza']),
        ]

    def __str__(self):
        return f"{self.titolo} ({self.user.username})"

    @property
    def is_scaduto(self):
        """Verifica se il promemoria è scaduto"""
        if not self.data_scadenza:
            return False
        return timezone.now() > self.data_scadenza and self.stato != 'completed'

    @property
    def giorni_alla_scadenza(self):
        """Calcola giorni rimanenti alla scadenza"""
        if not self.data_scadenza:
            return None
        delta = self.data_scadenza - timezone.now()
        return delta.days

    def mark_as_completed(self):
        """Segna come completato"""
        self.stato = 'completed'
        self.completato_il = timezone.now()
        self.save(update_fields=['stato', 'completato_il', 'updated_at'])

    def get_absolute_url(self):
        """URL dettaglio promemoria"""
        return reverse('mail:promemoria_detail', kwargs={'pk': self.pk})


# ============================================================================
# CHAT MODELS
# ============================================================================


class ChatConversation(BaseModel):
    """
    Conversazione chat tra utenti.

    Supporta chat 1-to-1 e di gruppo.
    """

    TYPE_CHOICES = [
        ('direct', 'Diretta (1-to-1)'),
        ('group', 'Gruppo'),
    ]

    titolo = models.CharField(
        "Titolo Conversazione",
        max_length=200,
        blank=True,
        help_text="Opzionale per chat dirette"
    )
    tipo = models.CharField(
        "Tipo",
        max_length=20,
        choices=TYPE_CHOICES,
        default='direct'
    )

    # Participants
    partecipanti = models.ManyToManyField(
        User,
        related_name='chat_conversations',
        verbose_name="Partecipanti"
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='chat_conversations_created',
        verbose_name="Creata da"
    )

    # Settings
    is_archived = models.BooleanField("Archiviata", default=False)
    is_muted = models.BooleanField("Silenziata", default=False)

    # Stats (denormalized)
    last_message_at = models.DateTimeField(
        "Ultimo Messaggio",
        null=True,
        blank=True,
        db_index=True
    )
    messages_count = models.IntegerField("N. Messaggi", default=0, editable=False)

    class Meta:
        verbose_name = "Conversazione Chat"
        verbose_name_plural = "Conversazioni Chat"
        ordering = ['-last_message_at', '-created_at']
        indexes = [
            models.Index(fields=['-last_message_at']),
        ]

    def __str__(self):
        if self.titolo:
            return self.titolo
        # Auto-generate title for direct chats
        if self.tipo == 'direct':
            users = self.partecipanti.all()[:2]
            return f"Chat: {' & '.join([u.username for u in users])}"
        return f"Chat di Gruppo #{self.pk}"

    def update_last_message(self):
        """Aggiorna timestamp ultimo messaggio"""
        last_msg = self.messages.order_by('-created_at').first()
        if last_msg:
            self.last_message_at = last_msg.created_at
            self.messages_count = self.messages.count()
            self.save(update_fields=['last_message_at', 'messages_count', 'updated_at'])


class ChatMessage(BaseModel, AllegatiMixin):
    """
    Messaggio chat.

    Supporta testo, allegati, typing indicators, read receipts.
    Usa AllegatiMixin per allegare file/immagini.
    """

    conversation = models.ForeignKey(
        ChatConversation,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name="Conversazione"
    )
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='chat_messages_sent',
        verbose_name="Mittente"
    )

    # Content
    contenuto = models.TextField("Contenuto")

    # Reply to (threading)
    reply_to = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='replies',
        verbose_name="In Risposta a"
    )

    # Status
    is_edited = models.BooleanField("Modificato", default=False)
    edited_at = models.DateTimeField("Modificato il", null=True, blank=True)
    is_deleted = models.BooleanField("Eliminato", default=False)

    # Read tracking
    read_by = models.ManyToManyField(
        User,
        related_name='chat_messages_read',
        blank=True,
        verbose_name="Letto da"
    )

    # Reactions (emoji reactions)
    reactions = models.JSONField(
        "Reazioni",
        default=dict,
        blank=True,
        help_text="{'👍': [user_id1, user_id2], '❤️': [user_id3]}"
    )

    class Meta:
        verbose_name = "Messaggio Chat"
        verbose_name_plural = "Messaggi Chat"
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['conversation', 'created_at']),
        ]

    def __str__(self):
        preview = self.contenuto[:50]
        return f"{self.sender.username}: {preview}"

    def save(self, *args, **kwargs):
        """Override save per aggiornare conversation"""
        super().save(*args, **kwargs)
        self.conversation.update_last_message()

    def mark_as_read_by(self, user):
        """Segna come letto da utente"""
        self.read_by.add(user)

    def add_reaction(self, user, emoji):
        """Aggiungi reazione emoji"""
        if emoji not in self.reactions:
            self.reactions[emoji] = []
        if user.id not in self.reactions[emoji]:
            self.reactions[emoji].append(user.id)
            self.save(update_fields=['reactions', 'updated_at'])

    def remove_reaction(self, user, emoji):
        """Rimuovi reazione"""
        if emoji in self.reactions and user.id in self.reactions[emoji]:
            self.reactions[emoji].remove(user.id)
            if not self.reactions[emoji]:
                del self.reactions[emoji]
            self.save(update_fields=['reactions', 'updated_at'])
