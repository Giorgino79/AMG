"""
Forms for Preventivi Beni/Servizi app
=====================================

Forms per gestione richieste preventivo e offerte.
"""

from django import forms
from django.forms import inlineformset_factory
from django.utils import timezone
from django_select2.forms import Select2Widget, Select2MultipleWidget
from .models import RichiestaPreventivo, VocePreventivo, Offerta, VoceOfferta, FornitorePreventivo
from anagrafica.models import Fornitore
from automezzi.models import Automezzo


class RichiestaForm(forms.ModelForm):
    """Form per creazione/modifica richiesta preventivo"""

    class Meta:
        model = RichiestaPreventivo
        fields = [
            'titolo', 'descrizione', 'tipo_richiesta', 'priorita', 'categoria',
            'luogo_consegna', 'indirizzo_consegna',
            'data_consegna_richiesta', 'data_scadenza_offerte',
            'condizioni_pagamento_richieste',
            'budget_massimo', 'approvatore',
            'note_interne', 'note_per_fornitori',
            'automezzo'
        ]
        widgets = {
            'titolo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Es: Fornitura materiale elettrico cantiere XX'
            }),
            'descrizione': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descrizione dettagliata della richiesta...'
            }),
            'tipo_richiesta': forms.Select(attrs={'class': 'form-select'}),
            'priorita': forms.Select(attrs={'class': 'form-select'}),
            'categoria': forms.Select(attrs={'class': 'form-select'}),

            'luogo_consegna': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Es: Cantiere Via Roma 1, Milano'
            }),
            'indirizzo_consegna': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Indirizzo completo di consegna'
            }),

            'data_consegna_richiesta': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'data_scadenza_offerte': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),

            'condizioni_pagamento_richieste': forms.Select(attrs={'class': 'form-select'}),
            'budget_massimo': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '0.00'
            }),
            'approvatore': Select2Widget(attrs={'class': 'form-select'}),

            'note_interne': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Note interne (non visibili ai fornitori)...'
            }),
            'note_per_fornitori': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Note visibili ai fornitori nella richiesta...'
            }),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Imposta richiedente automaticamente
        if self.user and not self.instance.pk:
            self.instance.richiedente = self.user

        # Configura campo automezzo con select personalizzato
        self.fields['automezzo'].widget = forms.Select(attrs={'class': 'form-select'})
        self.fields['automezzo'].required = False
        self.fields['automezzo'].empty_label = "-- Nessun automezzo --"

        # Personalizza le choices per mostrare numero, targa e marca/modello
        automezzi = Automezzo.objects.filter(attivo=True).order_by('numero_mezzo', 'targa')
        choices = [('', '-- Nessun automezzo --')]
        for a in automezzi:
            numero = f"N.{a.numero_mezzo}" if a.numero_mezzo else ""
            label = f"{numero} - {a.targa} - {a.marca} {a.modello}".strip(' -')
            choices.append((a.pk, label))
        self.fields['automezzo'].choices = choices


class VoceForm(forms.ModelForm):
    """Form per singola voce della richiesta"""

    class Meta:
        model = VocePreventivo
        fields = [
            'codice', 'descrizione', 'unita_misura', 'quantita',
            'prezzo_unitario_stimato', 'marca_richiesta', 'modello_richiesto',
            'note', 'obbligatoria'
        ]
        widgets = {
            'codice': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': 'Codice'
            }),
            'descrizione': forms.Textarea(attrs={
                'class': 'form-control form-control-sm',
                'rows': 2,
                'placeholder': 'Descrizione articolo/servizio...'
            }),
            'unita_misura': forms.Select(attrs={'class': 'form-select form-select-sm'}),
            'quantita': forms.NumberInput(attrs={
                'class': 'form-control form-control-sm',
                'step': '0.01',
                'min': '0.01',
                'value': '1'
            }),
            'prezzo_unitario_stimato': forms.NumberInput(attrs={
                'class': 'form-control form-control-sm',
                'step': '0.01',
                'placeholder': 'Prezzo stimato'
            }),
            'marca_richiesta': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': 'Marca preferita'
            }),
            'modello_richiesto': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': 'Modello'
            }),
            'note': forms.Textarea(attrs={
                'class': 'form-control form-control-sm',
                'rows': 2,
                'placeholder': 'Specifiche tecniche, requisiti particolari...'
            }),
            'obbligatoria': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


# Formset per gestione multipla voci
VoceFormSet = inlineformset_factory(
    RichiestaPreventivo,
    VocePreventivo,
    form=VoceForm,
    extra=1,
    can_delete=True,
    min_num=0,
    validate_min=False,
)


class SceltaFornitoriForm(forms.Form):
    """Form per selezione fornitori (esistenti + nuovi)"""

    # Fornitori esistenti
    fornitori_esistenti = forms.ModelMultipleChoiceField(
        queryset=Fornitore.objects.filter(attivo=True).order_by('ragione_sociale'),
        widget=Select2MultipleWidget(attrs={'class': 'form-select'}),
        label="Fornitori Esistenti",
        help_text="Seleziona uno o più fornitori già registrati nel sistema",
        required=False
    )

    # Nuovo fornitore 1
    fornitore_create_1_nome = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ragione sociale'
        }),
        label="Nome Fornitore"
    )
    fornitore_create_1_email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'email@esempio.it'
        }),
        label="Email"
    )

    # Nuovo fornitore 2
    fornitore_create_2_nome = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ragione sociale'
        }),
        label="Nome Fornitore"
    )
    fornitore_create_2_email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'email@esempio.it'
        }),
        label="Email"
    )

    # Nuovo fornitore 3
    fornitore_create_3_nome = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ragione sociale'
        }),
        label="Nome Fornitore"
    )
    fornitore_create_3_email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'email@esempio.it'
        }),
        label="Email"
    )

    def clean(self):
        cleaned_data = super().clean()
        fornitori_esistenti = cleaned_data.get('fornitori_esistenti')

        # Valida nuovi fornitori (se compilato nome, email è obbligatoria)
        nuovi_fornitori = []
        for i in range(1, 4):
            ragione_sociale = cleaned_data.get(f'fornitore_create_{i}_nome')
            email = cleaned_data.get(f'fornitore_create_{i}_email')

            if ragione_sociale and not email:
                self.add_error(f'fornitore_create_{i}_email', 'Email obbligatoria se inserisci il nome')
            elif email and not ragione_sociale:
                self.add_error(f'fornitore_create_{i}_nome', 'Nome obbligatorio se inserisci l\'email')
            elif ragione_sociale and email:
                nuovi_fornitori.append({'ragione_sociale': ragione_sociale.strip(), 'email': email.strip()})

        # Verifica che ci sia almeno un fornitore selezionato
        if not fornitori_esistenti and not nuovi_fornitori:
            raise forms.ValidationError(
                'Devi selezionare almeno un fornitore esistente o inserire un nuovo fornitore'
            )

        cleaned_data['nuovi_fornitori'] = nuovi_fornitori
        return cleaned_data


class OffertaForm(forms.ModelForm):
    """Form per creazione/modifica offerta"""

    class Meta:
        model = Offerta
        fields = [
            'fornitore', 'numero_offerta',
            # Importi
            'importo_merce', 'importo_trasporto', 'importo_imballo',
            'importo_installazione', 'importo_extra', 'descrizione_extra',
            'sconto_percentuale', 'sconto_importo', 'importo_totale',
            # Tempi
            'tempo_consegna_giorni', 'data_consegna_proposta', 'note_consegna',
            # Condizioni
            'termini_pagamento', 'validita_offerta_giorni',
            'garanzia_mesi', 'note_garanzia',
            # Servizi
            'trasporto_incluso', 'installazione_inclusa', 'formazione_inclusa',
            # File e note
            'file_offerta', 'note_tecniche', 'note_commerciali'
        ]
        widgets = {
            'fornitore': Select2Widget(attrs={'class': 'form-select'}),
            'numero_offerta': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Numero offerta del fornitore'
            }),

            # Importi
            'importo_merce': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01'
            }),
            'importo_trasporto': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01'
            }),
            'importo_imballo': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01'
            }),
            'importo_installazione': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01'
            }),
            'importo_extra': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01'
            }),
            'descrizione_extra': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2
            }),
            'sconto_percentuale': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '%'
            }),
            'sconto_importo': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01'
            }),
            'importo_totale': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01'
            }),

            # Tempi
            'tempo_consegna_giorni': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Giorni lavorativi'
            }),
            'data_consegna_proposta': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'note_consegna': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2
            }),

            # Condizioni
            'termini_pagamento': forms.Select(attrs={'class': 'form-select'}),
            'validita_offerta_giorni': forms.NumberInput(attrs={
                'class': 'form-control',
                'value': 30
            }),
            'garanzia_mesi': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Mesi'
            }),
            'note_garanzia': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2
            }),

            # Servizi
            'trasporto_incluso': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'installazione_inclusa': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'formazione_inclusa': forms.CheckboxInput(attrs={'class': 'form-check-input'}),

            # File e note
            'file_offerta': forms.FileInput(attrs={'class': 'form-control'}),
            'note_tecniche': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            }),
            'note_commerciali': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            }),
        }

    def __init__(self, *args, **kwargs):
        self.richiesta = kwargs.pop('richiesta', None)
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if self.richiesta:
            self.instance.richiesta = self.richiesta

        if self.user:
            self.instance.operatore_inserimento = self.user


class VoceOffertaForm(forms.ModelForm):
    """Form per singola voce dell'offerta"""

    class Meta:
        model = VoceOfferta
        fields = [
            'voce_richiesta', 'descrizione', 'marca', 'modello', 'codice_fornitore',
            'quantita', 'unita_misura', 'prezzo_unitario', 'sconto_riga', 'note'
        ]
        widgets = {
            'voce_richiesta': forms.Select(attrs={'class': 'form-select form-select-sm'}),
            'descrizione': forms.Textarea(attrs={
                'class': 'form-control form-control-sm',
                'rows': 2
            }),
            'marca': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'modello': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'codice_fornitore': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'quantita': forms.NumberInput(attrs={
                'class': 'form-control form-control-sm',
                'step': '0.01'
            }),
            'unita_misura': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'prezzo_unitario': forms.NumberInput(attrs={
                'class': 'form-control form-control-sm',
                'step': '0.01'
            }),
            'sconto_riga': forms.NumberInput(attrs={
                'class': 'form-control form-control-sm',
                'step': '0.01',
                'placeholder': '%'
            }),
            'note': forms.Textarea(attrs={
                'class': 'form-control form-control-sm',
                'rows': 2
            }),
        }


# Formset per gestione voci offerta
VoceOffertaFormSet = inlineformset_factory(
    Offerta,
    VoceOfferta,
    form=VoceOffertaForm,
    extra=1,
    can_delete=True,
)


class SceltaOffertaForm(forms.Form):
    """Form per scelta offerta vincente"""

    offerta_scelta = forms.ModelChoiceField(
        queryset=Offerta.objects.none(),
        widget=Select2Widget(attrs={'class': 'form-select'}),
        label="Seleziona Offerta",
        help_text="Seleziona l'offerta da approvare"
    )

    note_approvazione = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Note per approvazione...'
        }),
        label="Note Approvazione"
    )

    def __init__(self, *args, **kwargs):
        richiesta = kwargs.pop('richiesta', None)
        super().__init__(*args, **kwargs)

        if richiesta:
            # Mostra solo offerte valide per questa richiesta
            self.fields['offerta_scelta'].queryset = richiesta.offerte.filter(
                data_scadenza_offerta__gte=timezone.now().date()
            ).order_by('importo_totale')

            # Personalizza label per mostrare fornitore e importo
            self.fields['offerta_scelta'].label_from_instance = lambda obj: f"{obj.fornitore} - €{obj.importo_totale:,.2f}"


class RispostaFornitoreForm(forms.Form):
    """
    Form pubblico per la risposta dei fornitori alla richiesta.
    Accessibile tramite token senza autenticazione.
    """

    importo_totale = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0.00',
            'step': '0.01'
        }),
        label="Importo Totale",
        help_text="Inserire l'importo totale esclusa IVA"
    )

    tempo_consegna_giorni = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Es: 15'
        }),
        label="Tempo Consegna (giorni)",
        help_text="Giorni lavorativi per la consegna"
    )

    data_consegna_proposta = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label="Data Consegna Proposta",
        help_text="Data in cui garantite la consegna (opzionale)"
    )

    validita_offerta_giorni = forms.IntegerField(
        min_value=1,
        initial=30,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'value': 30
        }),
        label="Validità Offerta (giorni)",
        help_text="Per quanti giorni è valida questa offerta"
    )

    allegato = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf,.doc,.docx,.xls,.xlsx,.jpg,.jpeg,.png'
        }),
        label="Allegato Preventivo",
        help_text="Carica un file con il tuo preventivo dettagliato (PDF, Word, Excel, immagini - max 10MB)"
    )

    note = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Eventuali note, condizioni particolari, esclusioni...'
        }),
        label="Note"
    )

    def clean_allegato(self):
        """Valida dimensione file allegato"""
        allegato = self.cleaned_data.get('allegato')
        if allegato:
            # Limita dimensione a 10MB
            if allegato.size > 10 * 1024 * 1024:
                raise forms.ValidationError('Il file non può superare i 10MB')
        return allegato
