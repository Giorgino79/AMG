"""
Forms for Trasporti app
=======================

Forms per gestione richieste trasporto e offerte.
"""

from django import forms
from django.forms import inlineformset_factory
from django_select2.forms import Select2Widget, Select2MultipleWidget
from .models import RichiestaTrasporto, Collo, OffertaTrasporto, TrasportatoreOfferta
from anagrafica.models import Fornitore


class RichiestaTrasportoForm(forms.ModelForm):
    """Form per creazione/modifica richiesta trasporto"""

    class Meta:
        model = RichiestaTrasporto
        fields = [
            'titolo', 'descrizione', 'tipo_trasporto', 'priorita',
            # Ritiro
            'indirizzo_ritiro', 'cap_ritiro', 'citta_ritiro', 'provincia_ritiro', 'nazione_ritiro',
            'data_ritiro_richiesta', 'ora_ritiro_dalle', 'ora_ritiro_alle', 'note_ritiro',
            # Consegna
            'indirizzo_consegna', 'cap_consegna', 'citta_consegna', 'provincia_consegna', 'nazione_consegna',
            'data_consegna_richiesta', 'ora_consegna_dalle', 'ora_consegna_alle', 'note_consegna',
            # Merce
            'tipo_merce', 'valore_merce', 'merce_fragile', 'merce_deperibile',
            'merce_pericolosa', 'codice_adr', 'temperatura_controllata', 'temperatura_min', 'temperatura_max',
            # Servizi
            'assicurazione_richiesta', 'massimale_assicurazione',
            'scarico_a_piano', 'numero_piano', 'presenza_montacarichi',
            'tracking_richiesto', 'packing_list_richiesto',
            # Budget
            'budget_massimo', 'approvatore', 'note_interne'
        ]
        widgets = {
            'titolo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Es: Trasporto merci Roma-Milano'}),
            'descrizione': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'tipo_trasporto': forms.Select(attrs={'class': 'form-select'}),
            'priorita': forms.Select(attrs={'class': 'form-select'}),

            # Ritiro
            'indirizzo_ritiro': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'cap_ritiro': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '00000'}),
            'citta_ritiro': forms.TextInput(attrs={'class': 'form-control'}),
            'provincia_ritiro': forms.TextInput(attrs={'class': 'form-control', 'maxlength': 2, 'placeholder': 'RM'}),
            'nazione_ritiro': forms.TextInput(attrs={'class': 'form-control', 'maxlength': 2, 'value': 'IT'}),
            'data_ritiro_richiesta': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'ora_ritiro_dalle': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'ora_ritiro_alle': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'note_ritiro': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Es: Suonare al citofono Rossi'}),

            # Consegna
            'indirizzo_consegna': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'cap_consegna': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '00000'}),
            'citta_consegna': forms.TextInput(attrs={'class': 'form-control'}),
            'provincia_consegna': forms.TextInput(attrs={'class': 'form-control', 'maxlength': 2, 'placeholder': 'MI'}),
            'nazione_consegna': forms.TextInput(attrs={'class': 'form-control', 'maxlength': 2, 'value': 'IT'}),
            'data_consegna_richiesta': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'ora_consegna_dalle': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'ora_consegna_alle': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'note_consegna': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),

            # Merce
            'tipo_merce': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Es: Mobili, Elettronica, etc.'}),
            'valore_merce': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'codice_adr': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Es: UN1203'}),
            'temperatura_min': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '°C'}),
            'temperatura_max': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '°C'}),

            # Servizi
            'massimale_assicurazione': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'numero_piano': forms.NumberInput(attrs={'class': 'form-control'}),

            # Budget
            'budget_massimo': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'approvatore': Select2Widget(attrs={'class': 'form-select'}),
            'note_interne': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Imposta richiedente automaticamente
        if self.user and not self.instance.pk:
            self.instance.richiedente = self.user


class ColloForm(forms.ModelForm):
    """Form per singolo collo"""

    class Meta:
        model = Collo
        fields = [
            'quantita', 'tipo', 'lunghezza_cm', 'larghezza_cm', 'altezza_cm',
            'peso_kg', 'descrizione', 'fragile', 'stackable'
        ]
        widgets = {
            'quantita': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'min': 1, 'value': 1}),
            'tipo': forms.Select(attrs={'class': 'form-select form-select-sm'}),
            'lunghezza_cm': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'step': '0.01', 'placeholder': 'cm'}),
            'larghezza_cm': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'step': '0.01', 'placeholder': 'cm'}),
            'altezza_cm': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'step': '0.01', 'placeholder': 'cm'}),
            'peso_kg': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'step': '0.01', 'placeholder': 'kg'}),
            'descrizione': forms.TextInput(attrs={'class': 'form-control form-control-sm', 'placeholder': 'Descrizione contenuto'}),
            'fragile': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'stackable': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


# Formset per gestione multipla colli
ColloFormSet = inlineformset_factory(
    RichiestaTrasporto,
    Collo,
    form=ColloForm,
    extra=1,
    can_delete=True,
    min_num=1,
    validate_min=True,
)


class SceltaTrasportatoriForm(forms.Form):
    """Form per selezione trasportatori (esistenti + nuovi)"""

    # Fornitori esistenti
    trasportatori_esistenti = forms.ModelMultipleChoiceField(
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
            'placeholder': 'Nome del trasportatore'
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
            'placeholder': 'Nome del trasportatore'
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
            'placeholder': 'Nome del trasportatore'
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
        trasportatori_esistenti = cleaned_data.get('trasportatori_esistenti')

        # Valida nuovi fornitori (se compilato nome, email è obbligatoria)
        nuovi_fornitori = []
        for i in range(1, 4):
            ragione_sociale = cleaned_data.get(f'fornitore_create_{i}_nome')
            email = cleaned_data.get(f'fornitore_create_{i}_email')

            if ragione_sociale and not email:
                self.add_error(f'fornitore_create_{i}_email', 'Email obbligatoria se inserisci la ragione_sociale')
            elif email and not ragione_sociale:
                self.add_error(f'fornitore_create_{i}_nome', 'Nome obbligatorio se inserisci l\'email')
            elif ragione_sociale and email:
                nuovi_fornitori.append({'ragione_sociale': ragione_sociale.strip(), 'email': email.strip()})

        # Verifica che ci sia almeno un trasportatore selezionato
        if not trasportatori_esistenti and not nuovi_fornitori:
            raise forms.ValidationError(
                'Devi selezionare almeno un fornitore esistente o inserire un nuovo fornitore'
            )

        cleaned_data['nuovi_fornitori'] = nuovi_fornitori
        return cleaned_data


class OffertaTrasportoForm(forms.ModelForm):
    """Form per creazione/modifica offerta trasporto"""

    class Meta:
        model = OffertaTrasporto
        fields = [
            'trasportatore', 'numero_offerta',
            # Prezzi
            'importo_trasporto', 'importo_assicurazione', 'importo_pedaggi',
            'importo_extra', 'descrizione_extra', 'importo_totale',
            'prezzo_per_km', 'prezzo_per_kg',
            # Tempi
            'data_ritiro_proposta', 'ora_ritiro_dalle', 'ora_ritiro_alle',
            'data_consegna_prevista', 'ora_consegna_dalle', 'ora_consegna_alle',
            'tempo_transito_giorni',
            # Mezzo
            'tipo_mezzo', 'targa_mezzo', 'capienza_kg', 'capienza_m3',
            'conducente_nome', 'conducente_telefono',
            # Condizioni
            'termini_pagamento', 'validita_offerta_giorni',
            'tracking_incluso', 'assicurazione_inclusa', 'scarico_a_piano_incluso',
            # File e note
            'file_offerta', 'note_tecniche', 'note_commerciali'
        ]
        widgets = {
            'trasportatore': Select2Widget(attrs={'class': 'form-select'}),
            'numero_offerta': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Numero offerta trasportatore'}),

            # Prezzi
            'importo_trasporto': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'importo_assicurazione': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'importo_pedaggi': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'importo_extra': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'descrizione_extra': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'importo_totale': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'prezzo_per_km': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'prezzo_per_kg': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),

            # Tempi
            'data_ritiro_proposta': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'ora_ritiro_dalle': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'ora_ritiro_alle': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'data_consegna_prevista': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'ora_consegna_dalle': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'ora_consegna_alle': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'tempo_transito_giorni': forms.NumberInput(attrs={'class': 'form-control'}),

            # Mezzo
            'tipo_mezzo': forms.Select(attrs={'class': 'form-select'}),
            'targa_mezzo': forms.TextInput(attrs={'class': 'form-control'}),
            'capienza_kg': forms.NumberInput(attrs={'class': 'form-control'}),
            'capienza_m3': forms.NumberInput(attrs={'class': 'form-control'}),
            'conducente_nome': forms.TextInput(attrs={'class': 'form-control'}),
            'conducente_telefono': forms.TextInput(attrs={'class': 'form-control'}),

            # Condizioni
            'termini_pagamento': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Es: 30gg DFFM'}),
            'validita_offerta_giorni': forms.NumberInput(attrs={'class': 'form-control', 'value': 7}),

            # File e note
            'file_offerta': forms.FileInput(attrs={'class': 'form-control'}),
            'note_tecniche': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'note_commerciali': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        self.richiesta = kwargs.pop('richiesta', None)
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if self.richiesta:
            self.instance.richiesta = self.richiesta

        if self.user:
            self.instance.operatore_inserimento = self.user


class SceltaOffertaForm(forms.Form):
    """Form per scelta offerta vincente"""

    offerta_scelta = forms.ModelChoiceField(
        queryset=OffertaTrasporto.objects.none(),
        widget=Select2Widget(attrs={'class': 'form-select'}),
        label="Seleziona Offerta",
        help_text="Seleziona l'offerta da approvare"
    )

    note_approvazione = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Note per approvazione...'}),
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

            # Personalizza label per mostrare trasportatore e importo
            self.fields['offerta_scelta'].label_from_instance = lambda obj: f"{obj.trasportatore.nome} - €{obj.importo_totale:,.2f}"


# Import necessario per SceltaOffertaForm
from django.utils import timezone


class RispostaFornitoreForm(forms.Form):
    """
    Form pubblico per la risposta dei fornitori alla richiesta di trasporto.
    Accessibile tramite token senza autenticazione.
    """

    importo_imponibile = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0.00',
            'step': '0.01'
        }),
        label="Importo Imponibile",
        help_text="Inserire l'importo esclusa IVA"
    )

    data_ritiro_garantita = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label="Data Ritiro Garantita",
        help_text="Data in cui garantite il ritiro della merce"
    )

    data_consegna_garantita = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label="Data Consegna Garantita",
        help_text="Data in cui garantite la consegna della merce"
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
            'placeholder': 'Eventuali note o condizioni particolari...'
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

    def clean(self):
        """Validazione cross-field"""
        cleaned_data = super().clean()
        data_ritiro = cleaned_data.get('data_ritiro_garantita')
        data_consegna = cleaned_data.get('data_consegna_garantita')

        if data_ritiro and data_consegna:
            if data_consegna < data_ritiro:
                raise forms.ValidationError(
                    'La data di consegna non può essere precedente alla data di ritiro'
                )

        return cleaned_data
