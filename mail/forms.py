"""
Forms for Mail App - ModularBEF

Forms con crispy-forms per gestione email, promemoria e chat.
"""

from django import forms
from django.contrib.auth import get_user_model
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field, Submit, Div, HTML, Row, Column
from .models import (
    EmailConfiguration,
    EmailTemplate,
    EmailMessage,
    Promemoria,
    ChatConversation,
    ChatMessage,
)

User = get_user_model()


# ============================================================================
# EMAIL CONFIGURATION FORMS
# ============================================================================


class EmailConfigurationForm(forms.ModelForm):
    """Form per configurazione email utente (SMTP + IMAP)"""

    class Meta:
        model = EmailConfiguration
        fields = [
            'display_name',
            'email_address',
            'smtp_server',
            'smtp_port',
            'smtp_username',
            'smtp_password',
            'use_tls',
            'use_ssl',
            'imap_server',
            'imap_port',
            'imap_username',
            'imap_password',
            'imap_use_tls',
            'imap_use_ssl',
            'imap_enabled',
            'daily_limit',
            'hourly_limit',
        ]
        widgets = {
            'smtp_password': forms.PasswordInput(render_value=True),
            'imap_password': forms.PasswordInput(render_value=True),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False  # Don't render form tag
        self.helper.layout = Layout(
            HTML('<h5 class="border-bottom pb-2 mb-3">Configurazione SMTP (Invio)</h5>'),
            Row(
                Column('display_name', css_class='col-md-6'),
                Column('email_address', css_class='col-md-6'),
            ),
            Row(
                Column('smtp_server', css_class='col-md-6'),
                Column('smtp_port', css_class='col-md-6'),
            ),
            Row(
                Column('smtp_username', css_class='col-md-6'),
                Column('smtp_password', css_class='col-md-6'),
            ),
            Row(
                Column('use_tls', css_class='col-md-6'),
                Column('use_ssl', css_class='col-md-6'),
            ),
            HTML('<hr class="my-4">'),
            HTML('<h5 class="border-bottom pb-2 mb-3">Configurazione IMAP (Ricezione)</h5>'),
            Row(
                Column('imap_server', css_class='col-md-6'),
                Column('imap_port', css_class='col-md-6'),
            ),
            Row(
                Column('imap_username', css_class='col-md-6'),
                Column('imap_password', css_class='col-md-6'),
            ),
            Row(
                Column('imap_use_tls', css_class='col-md-4'),
                Column('imap_use_ssl', css_class='col-md-4'),
                Column('imap_enabled', css_class='col-md-4'),
            ),
            HTML('<hr class="my-4">'),
            HTML('<h5 class="border-bottom pb-2 mb-3">Limiti</h5>'),
            Row(
                Column('daily_limit', css_class='col-md-6'),
                Column('hourly_limit', css_class='col-md-6'),
            ),
        )


# ============================================================================
# EMAIL TEMPLATE FORMS
# ============================================================================


class EmailTemplateForm(forms.ModelForm):
    """Form per template email"""

    class Meta:
        model = EmailTemplate
        fields = [
            'nome',
            'slug',
            'descrizione',
            'categoria',
            'subject',
            'content_html',
            'content_text',
            'available_variables',
            'sample_data',
            'is_system',
        ]
        widgets = {
            'content_html': forms.Textarea(attrs={'rows': 10}),
            'content_text': forms.Textarea(attrs={'rows': 8}),
            'descrizione': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('nome', css_class='col-md-6'),
                Column('slug', css_class='col-md-6'),
            ),
            Row(
                Column('categoria', css_class='col-md-6'),
                Column('is_system', css_class='col-md-6'),
            ),
            'descrizione',
            'subject',
            HTML('<div class="alert alert-info"><small>'
                 'Usa {{variabile}} per inserire variabili dinamiche'
                 '</small></div>'),
            'content_html',
            'content_text',
            Row(
                Column('available_variables', css_class='col-md-6'),
                Column('sample_data', css_class='col-md-6'),
            ),
        )


# ============================================================================
# EMAIL MESSAGE FORMS
# ============================================================================


class ComposeEmailForm(forms.ModelForm):
    """Form per comporre nuova email"""

    template = forms.ModelChoiceField(
        queryset=EmailTemplate.objects.filter(is_active=True),
        required=False,
        label="Usa Template",
        help_text="Seleziona un template predefinito (opzionale)"
    )

    # Override fields to use textarea for JSON fields
    to_addresses = forms.CharField(
        label="A",
        widget=forms.Textarea(attrs={
            'rows': 2,
            'placeholder': 'destinatario@example.com, altro@example.com'
        }),
        help_text="Indirizzi email separati da virgola"
    )
    cc_addresses = forms.CharField(
        label="CC",
        required=False,
        widget=forms.Textarea(attrs={
            'rows': 2,
            'placeholder': 'cc@example.com'
        }),
        help_text="Opzionale - separati da virgola"
    )
    bcc_addresses = forms.CharField(
        label="BCC",
        required=False,
        widget=forms.Textarea(attrs={
            'rows': 2,
            'placeholder': 'bcc@example.com'
        }),
        help_text="Opzionale - separati da virgola"
    )

    class Meta:
        model = EmailMessage
        fields = [
            'to_addresses',
            'cc_addresses',
            'bcc_addresses',
            'subject',
            'content_text',
        ]
        widgets = {
            'content_text': forms.Textarea(attrs={
                'rows': 15,
                'placeholder': 'Scrivi qui il contenuto della tua email...'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False  # Don't render form tag
        self.helper.layout = Layout(
            'template',
            'to_addresses',
            Row(
                Column('cc_addresses', css_class='col-md-6'),
                Column('bcc_addresses', css_class='col-md-6'),
            ),
            'subject',
            'content_text',
        )

    def clean_to_addresses(self):
        """Converti stringa CSV in lista"""
        data = self.cleaned_data['to_addresses']
        if isinstance(data, str):
            return [email.strip() for email in data.split(',') if email.strip()]
        return data

    def clean_cc_addresses(self):
        """Converti stringa CSV in lista"""
        data = self.cleaned_data.get('cc_addresses', '')
        if not data:
            return []
        if isinstance(data, str):
            return [email.strip() for email in data.split(',') if email.strip()]
        return data

    def clean_bcc_addresses(self):
        """Converti stringa CSV in lista"""
        data = self.cleaned_data.get('bcc_addresses', '')
        if not data:
            return []
        if isinstance(data, str):
            return [email.strip() for email in data.split(',') if email.strip()]
        return data


# ============================================================================
# PROMEMORIA FORMS
# ============================================================================


class PromemoriaForm(forms.ModelForm):
    """Form per promemoria"""

    class Meta:
        model = Promemoria
        fields = [
            'titolo',
            'descrizione',
            'assegnato_a',
            'priorita',
            'stato',
            'data_scadenza',
            'notifica_email',
            'notifica_giorni_prima',
            'tags',
        ]
        widgets = {
            'data_scadenza': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'form-control'
            }),
            'descrizione': forms.Textarea(attrs={'rows': 4}),
            'assegnato_a': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtra solo utenti attivi per assegnato_a
        self.fields['assegnato_a'].queryset = User.objects.filter(is_active=True).order_by('first_name', 'last_name')
        self.fields['assegnato_a'].label_from_instance = lambda obj: obj.get_full_name() or obj.username

        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            'titolo',
            'descrizione',
            Row(
                Column('assegnato_a', css_class='col-md-6'),
                Column('priorita', css_class='col-md-3'),
                Column('stato', css_class='col-md-3'),
            ),
            'data_scadenza',
            HTML('<hr class="my-3">'),
            HTML('<h6>Notifiche</h6>'),
            Row(
                Column('notifica_email', css_class='col-md-6'),
                Column('notifica_giorni_prima', css_class='col-md-6'),
            ),
            'tags',
        )


# ============================================================================
# CHAT FORMS
# ============================================================================


class ChatConversationForm(forms.ModelForm):
    """Form per creare conversazione chat"""

    class Meta:
        model = ChatConversation
        fields = [
            'titolo',
            'tipo',
            'partecipanti',
        ]
        widgets = {
            'partecipanti': forms.SelectMultiple(attrs={'class': 'form-select', 'size': 6}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Row(
                Column('titolo', css_class='col-md-8'),
                Column('tipo', css_class='col-md-4'),
            ),
            Field('partecipanti', css_class='form-select'),
        )


class ChatMessageForm(forms.ModelForm):
    """Form per messaggio chat"""

    class Meta:
        model = ChatMessage
        fields = ['contenuto']
        widgets = {
            'contenuto': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Scrivi un messaggio...',
                'class': 'form-control'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_show_labels = False
        self.helper.layout = Layout(
            'contenuto',
        )
