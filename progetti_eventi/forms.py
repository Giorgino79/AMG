"""
Forms per app progetti_eventi.
"""

from django import forms
from django.forms import inlineformset_factory
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, Row, Column, Submit, Button, HTML
from crispy_forms.bootstrap import TabHolder, Tab
from django.contrib.auth import get_user_model
from django_select2.forms import Select2MultipleWidget
from automezzi.models import Automezzo

from .models import Progetto, ProgettoReparto, ListaProdotti, ProdottoLista, EngineeringTask

User = get_user_model()


# ============================================================================
# PROGETTO FORMS
# ============================================================================

class ProgettoForm(forms.ModelForm):
    """
    Form per creazione/modifica progetto.
    Include MultipleChoiceField per selezione reparti.
    """

    reparti_coinvolti = forms.MultipleChoiceField(
        label="Reparti Coinvolti",
        choices=ProgettoReparto.TIPO_REPARTO_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=True,
        help_text="Seleziona i reparti che dovranno lavorare a questo progetto"
    )

    partecipanti = forms.ModelMultipleChoiceField(
        label="Partecipanti Chat Progetto",
        queryset=User.objects.filter(is_active=True).order_by('first_name', 'last_name', 'username'),
        widget=Select2MultipleWidget(attrs={
            'data-placeholder': 'Seleziona partecipanti...',
            'class': 'form-control'
        }),
        required=False,
        help_text="Utenti che parteciperanno alla chat di progetto. Il commerciale viene aggiunto automaticamente."
    )

    mezzi_assegnati = forms.ModelMultipleChoiceField(
        label="Mezzi Assegnati",
        queryset=Automezzo.objects.filter(attivo=True, bloccata=False).order_by('numero_mezzo', 'targa'),
        widget=Select2MultipleWidget(attrs={
            'data-placeholder': 'Seleziona mezzi per consegna/ritiro...',
            'class': 'form-control'
        }),
        required=False,
        help_text="Mezzi necessari per consegna e ritiro. La disponibilità verrà verificata in base alle date del progetto."
    )

    class Meta:
        model = Progetto
        fields = [
            # Cliente e Evento
            'cliente',
            'nome_evento',
            'tipo_evento',
            'descrizione_evento',

            # Date
            'data_evento',
            'ora_inizio_evento',
            'data_fine_evento',
            'ora_fine_evento',

            # Location
            'location',
            'indirizzo_location',
            'cap_location',
            'citta_location',
            'provincia_location',
            'nazione_location',
            'coordinate_location',

            # Logistica Iniziale
            'data_consegna_richiesta',
            'data_ritiro_richiesta',
            'note_logistica_iniziali',

            # Mezzi (custom field)
            'mezzi_assegnati',

            # Reparti (custom field)
            'reparti_coinvolti',

            # Partecipanti chat (custom field)
            'partecipanti',

            # Budget
            'budget_preventivato',
            'budget_approvato',

            # Priorità e Note
            'priorita',
            'note_commerciali',
        ]

        widgets = {
            'data_evento': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'ora_inizio_evento': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'data_fine_evento': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'ora_fine_evento': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'data_consegna_richiesta': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'data_ritiro_richiesta': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'descrizione_evento': forms.Textarea(attrs={'rows': 3}),
            'indirizzo_location': forms.Textarea(attrs={'rows': 2}),
            'note_logistica_iniziali': forms.Textarea(attrs={'rows': 3}),
            'note_commerciali': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Se in modifica, pre-popola i reparti coinvolti
        if self.instance and self.instance.pk:
            self.fields['reparti_coinvolti'].initial = self.instance.reparti_coinvolti
            self.fields['partecipanti'].initial = self.instance.partecipanti.all()
            self.fields['mezzi_assegnati'].initial = self.instance.mezzi_assegnati.all()

        # Personalizza il label per partecipanti: mostra username e nome completo
        self.fields['partecipanti'].label_from_instance = lambda obj: (
            f"{obj.username} - {obj.get_full_name()}" if obj.get_full_name()
            else obj.username
        )

        # Personalizza il label per mezzi: mostra numero mezzo e targa
        self.fields['mezzi_assegnati'].label_from_instance = lambda obj: (
            f"N.{obj.numero_mezzo} - {obj.targa}" if obj.numero_mezzo
            else f"{obj.targa}"
        )

        # Crispy Forms Helper
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            TabHolder(
                Tab(
                    'Informazioni Generali',
                    Row(
                        Column('cliente', css_class='col-md-6'),
                        Column('tipo_evento', css_class='col-md-6'),
                    ),
                    'nome_evento',
                    'descrizione_evento',
                    Row(
                        Column('priorita', css_class='col-md-6'),
                        Column('budget_preventivato', css_class='col-md-6'),
                    ),
                ),
                Tab(
                    'Date e Orari',
                    Row(
                        Column('data_evento', css_class='col-md-6'),
                        Column('ora_inizio_evento', css_class='col-md-6'),
                    ),
                    Row(
                        Column('data_fine_evento', css_class='col-md-6'),
                        Column('ora_fine_evento', css_class='col-md-6'),
                    ),
                ),
                Tab(
                    'Location',
                    'location',
                    'indirizzo_location',
                    Row(
                        Column('cap_location', css_class='col-md-3'),
                        Column('citta_location', css_class='col-md-5'),
                        Column('provincia_location', css_class='col-md-2'),
                        Column('nazione_location', css_class='col-md-2'),
                    ),
                    'coordinate_location',
                ),
                Tab(
                    'Logistica',
                    HTML('<p class="text-muted">Date e orari indicativi per la consegna e il ritiro. Verranno raffinati dalla logistica.</p>'),
                    Row(
                        Column('data_consegna_richiesta', css_class='col-md-6'),
                        Column('data_ritiro_richiesta', css_class='col-md-6'),
                    ),
                    'note_logistica_iniziali',
                    Fieldset(
                        'Mezzi Necessari',
                        HTML('<p class="text-muted small">Seleziona i mezzi necessari per consegna e ritiro. Il sistema verificherà la disponibilità in base alle date del progetto.</p>'),
                        'mezzi_assegnati',
                        css_class='mt-3'
                    ),
                ),
                Tab(
                    'Reparti e Partecipanti',
                    Fieldset(
                        'Reparti Coinvolti',
                        'reparti_coinvolti',
                        css_class='mb-4'
                    ),
                    Fieldset(
                        'Partecipanti Chat Progetto',
                        HTML('<p class="text-muted small">Seleziona gli utenti che parteciperanno alla chat di progetto. Verrà creata automaticamente una chat di gruppo.</p>'),
                        'partecipanti',
                        css_class='mb-4'
                    ),
                    'note_commerciali',
                    'budget_approvato',
                ),
            ),
            HTML('<hr>'),
            Row(
                Column(
                    Submit('submit', 'Salva Progetto', css_class='btn btn-primary btn-lg'),
                    css_class='col-md-6'
                ),
                Column(
                    HTML('<a href="{% url "progetti_eventi:progetto_list" %}" class="btn btn-secondary btn-lg">Annulla</a>'),
                    css_class='col-md-6 text-end'
                ),
            ),
        )

    def clean(self):
        cleaned_data = super().clean()

        # Validazione date
        data_evento = cleaned_data.get('data_evento')
        data_fine_evento = cleaned_data.get('data_fine_evento')
        data_consegna = cleaned_data.get('data_consegna_richiesta')
        data_ritiro = cleaned_data.get('data_ritiro_richiesta')

        if data_fine_evento and data_evento and data_fine_evento < data_evento:
            raise forms.ValidationError("La data fine evento non può essere precedente alla data inizio")

        if data_consegna and data_evento:
            if data_consegna.date() > data_evento:
                raise forms.ValidationError("La consegna deve avvenire prima dell'evento")

        # Almeno un reparto
        reparti = cleaned_data.get('reparti_coinvolti')
        if not reparti:
            raise forms.ValidationError("Devi selezionare almeno un reparto")

        # Validazione disponibilità mezzi
        mezzi_selezionati = cleaned_data.get('mezzi_assegnati')
        if mezzi_selezionati and data_consegna and data_ritiro:
            # Controlla disponibilità mezzi nel periodo
            from django.db.models import Q

            # Periodo del progetto (da consegna a ritiro)
            data_inizio = data_consegna.date()
            data_fine = data_ritiro.date()

            mezzi_non_disponibili = []

            for mezzo in mezzi_selezionati:
                # Cerca progetti che usano questo mezzo nello stesso periodo
                # Escludi il progetto corrente se siamo in modifica
                progetti_conflitto = Progetto.objects.filter(
                    mezzi_assegnati=mezzo,
                    deleted_at__isnull=True
                ).filter(
                    # Sovrapposizione date: progetto inizia prima della nostra fine E finisce dopo il nostro inizio
                    data_consegna_richiesta__date__lte=data_fine,
                    data_ritiro_richiesta__date__gte=data_inizio
                )

                # Se siamo in modifica, escludi il progetto corrente
                if self.instance and self.instance.pk:
                    progetti_conflitto = progetti_conflitto.exclude(pk=self.instance.pk)

                if progetti_conflitto.exists():
                    conflitti = [f"{p.codice} ({p.nome_evento})" for p in progetti_conflitto[:3]]
                    mezzi_non_disponibili.append(
                        f"Mezzo {mezzo.targa}: già assegnato a {', '.join(conflitti)}"
                    )

            if mezzi_non_disponibili:
                raise forms.ValidationError({
                    'mezzi_assegnati': [
                        "I seguenti mezzi non sono disponibili nel periodo selezionato:",
                        *mezzi_non_disponibili
                    ]
                })

        return cleaned_data


# ============================================================================
# PROGETTO REPARTO FORMS
# ============================================================================

class ProgettoRepartoForm(forms.ModelForm):
    """
    Form per assegnazione engineering e gestione reparto.
    """

    class Meta:
        model = ProgettoReparto
        fields = [
            'engineering_assegnato_a',
            'note_engineering',
            'numero_tecnici_necessari',
            'numero_facchini_necessari',
        ]

        widgets = {
            'note_engineering': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Filtra solo ingegneri (users con permesso)
        from users.models import User
        self.fields['engineering_assegnato_a'].queryset = User.objects.filter(
            is_active=True
        ).order_by('first_name', 'last_name')


# ============================================================================
# LISTE PRODOTTI FORMS
# ============================================================================

class ListaProdottiForm(forms.ModelForm):
    """
    Form per creazione lista prodotti.
    """

    class Meta:
        model = ListaProdotti
        fields = [
            'nome_lista',
            'descrizione',
        ]

        widgets = {
            'descrizione': forms.Textarea(attrs={'rows': 3}),
        }


class ProdottoListaForm(forms.ModelForm):
    """
    Form per singolo prodotto nella lista.
    """

    class Meta:
        model = ProdottoLista
        fields = [
            'codice_prodotto',
            'nome_prodotto',
            'categoria_prodotto',
            'quantita',
            'lunghezza_cm',
            'larghezza_cm',
            'altezza_cm',
            'peso_kg',
            'note',
            'priorita',
        ]

        widgets = {
            'note': forms.Textarea(attrs={'rows': 2}),
        }


# Formset per prodotti
ProdottoListaFormSet = inlineformset_factory(
    ListaProdotti,
    ProdottoLista,
    form=ProdottoListaForm,
    extra=5,  # 5 righe vuote iniziali
    can_delete=True,
    min_num=1,  # Almeno 1 prodotto
    validate_min=True,
)


# ============================================================================
# ENGINEERING TASK FORMS
# ============================================================================

class EngineeringTaskForm(forms.ModelForm):
    """
    Form per creazione task engineering.
    """

    class Meta:
        model = EngineeringTask
        fields = [
            'titolo',
            'descrizione',
            'ore_stimate',
            'note',
        ]

        widgets = {
            'descrizione': forms.Textarea(attrs={'rows': 4}),
            'note': forms.Textarea(attrs={'rows': 3}),
        }
