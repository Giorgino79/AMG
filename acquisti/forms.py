"""
ACQUISTI FORMS - Forms per gestione ordini di acquisto
=====================================================

Forms per:
- Ricerca ordini
- Creazione manuale ordini
- Cambio stato ordini
"""

from django import forms
from django.db.models import Q
from .models import OrdineAcquisto
from anagrafica.models import Fornitore


class RicercaOrdiniForm(forms.Form):
    """
    Form di ricerca per dashboard ordini
    """

    fornitore = forms.ModelChoiceField(
        queryset=Fornitore.objects.filter(attivo=True).order_by('ragione_sociale'),
        required=False,
        empty_label="Tutti i fornitori",
        widget=forms.Select(attrs={
            'class': 'form-control',
        })
    )

    titolo = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Cerca nell\'oggetto ordine...'
        })
    )

    stato = forms.ChoiceField(
        choices=[('', 'Tutti gli stati')] + OrdineAcquisto.STATI_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control',
        })
    )

    tipo_origine = forms.ChoiceField(
        choices=[('', 'Tutte le origini')] + OrdineAcquisto.TIPO_ORIGINE_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control',
        })
    )

    def filter_queryset(self, queryset):
        """
        Applica i filtri al queryset
        """
        if self.is_valid():
            # Filtro fornitore
            if self.cleaned_data.get('fornitore'):
                queryset = queryset.filter(fornitore=self.cleaned_data['fornitore'])

            # Filtro titolo
            if self.cleaned_data.get('titolo'):
                titolo_search = self.cleaned_data['titolo']
                queryset = queryset.filter(
                    Q(oggetto_ordine__icontains=titolo_search) |
                    Q(note_ordine__icontains=titolo_search) |
                    Q(numero_ordine__icontains=titolo_search)
                )

            # Filtro stato
            if self.cleaned_data.get('stato'):
                queryset = queryset.filter(stato=self.cleaned_data['stato'])

            # Filtro tipo origine
            if self.cleaned_data.get('tipo_origine'):
                queryset = queryset.filter(tipo_origine=self.cleaned_data['tipo_origine'])

        return queryset


class CreaOrdineForm(forms.ModelForm):
    """
    Form per creazione manuale ordine di acquisto
    """

    class Meta:
        model = OrdineAcquisto
        fields = [
            'fornitore',
            'oggetto_ordine',
            'descrizione_dettagliata',
            'imponibile',
            'aliquota_iva',
            'termini_pagamento',
            'tempi_consegna',
            'data_consegna_richiesta',
            'note_ordine',
            'riferimento_fornitore'
        ]
        widgets = {
            'fornitore': forms.Select(attrs={'class': 'form-control'}),
            'oggetto_ordine': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Oggetto dell\'ordine'
            }),
            'descrizione_dettagliata': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Descrizione dettagliata dei beni/servizi...'
            }),
            'imponibile': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Importo netto'
            }),
            'aliquota_iva': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'max': '100',
                'placeholder': '22.00'
            }),
            'termini_pagamento': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'es. 30 giorni DFFM'
            }),
            'tempi_consegna': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'es. 15 giorni lavorativi'
            }),
            'data_consegna_richiesta': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'note_ordine': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Note aggiuntive...'
            }),
            'riferimento_fornitore': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Riferimento/numero offerta del fornitore'
            })
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Ordina fornitori per ragione sociale
        self.fields['fornitore'].queryset = Fornitore.objects.filter(
            attivo=True
        ).order_by('ragione_sociale')

    def save(self, commit=True):
        """
        Salva l'ordine di acquisto.
        """
        instance = super().save(commit=False)

        # Imposta il creatore
        if not instance.pk and self.user:
            instance.creato_da = self.user

        # Tipo origine manuale
        instance.tipo_origine = 'MANUALE'

        if commit:
            instance.save()
            self.save_m2m()

        return instance


class CambiaStatoOrdineForm(forms.Form):
    """
    Form per cambiare lo stato di un ordine
    """

    AZIONI_CHOICES = [
        ('segna_ricevuto', 'Segna come RICEVUTO'),
        ('segna_pagato', 'Segna come PAGATO'),
    ]

    azione = forms.ChoiceField(
        choices=AZIONI_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    note = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Note sul cambio di stato (opzionale)...'
        })
    )

    def __init__(self, ordine, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ordine = ordine

        # Filtra le azioni disponibili in base allo stato attuale
        available_choices = []

        if ordine.puo_essere_ricevuto():
            available_choices.append(('segna_ricevuto', 'Segna come RICEVUTO'))

        if ordine.puo_essere_pagato():
            available_choices.append(('segna_pagato', 'Segna come PAGATO'))

        self.fields['azione'].choices = available_choices

        # Disabilita il form se nessuna azione disponibile
        if not available_choices:
            self.fields['azione'].choices = [('', 'Nessuna azione disponibile')]
            self.fields['azione'].widget.attrs['disabled'] = True


class OrdineDettaglioForm(forms.ModelForm):
    """
    Form per visualizzazione/modifica dettagli ordine
    """

    class Meta:
        model = OrdineAcquisto
        fields = [
            'note_ordine',
            'riferimento_fornitore'
        ]
        widgets = {
            'note_ordine': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4
            }),
            'riferimento_fornitore': forms.TextInput(attrs={
                'class': 'form-control'
            })
        }


class ReportOrdiniForm(forms.Form):
    """
    Form per filtri report ordini in attesa fattura.
    Permette di filtrare per periodo, fornitore, stato e tipo origine.
    """

    STATO_REPORT_CHOICES = [
        ('', 'Tutti gli stati'),
        ('RICEVUTO', 'Ricevuti - In attesa fattura'),
        ('CREATO', 'Creati - In attesa consegna'),
        ('PAGATO', 'Pagati'),
    ]

    data_da = forms.DateField(
        required=False,
        label="Da data",
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )

    data_a = forms.DateField(
        required=False,
        label="A data",
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )

    fornitore = forms.ModelChoiceField(
        queryset=Fornitore.objects.filter(attivo=True).order_by('ragione_sociale'),
        required=False,
        empty_label="Tutti i fornitori",
        widget=forms.Select(attrs={
            'class': 'form-control',
        })
    )

    stato = forms.ChoiceField(
        choices=STATO_REPORT_CHOICES,
        required=False,
        initial='RICEVUTO',
        widget=forms.Select(attrs={
            'class': 'form-control',
        })
    )

    tipo_origine = forms.ChoiceField(
        choices=[('', 'Tutte le origini')] + OrdineAcquisto.TIPO_ORIGINE_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control',
        })
    )

    def filter_queryset(self, queryset):
        """
        Applica i filtri al queryset degli ordini
        """
        if self.is_valid():
            # Filtro data da
            if self.cleaned_data.get('data_da'):
                queryset = queryset.filter(data_ordine__date__gte=self.cleaned_data['data_da'])

            # Filtro data a
            if self.cleaned_data.get('data_a'):
                queryset = queryset.filter(data_ordine__date__lte=self.cleaned_data['data_a'])

            # Filtro fornitore
            if self.cleaned_data.get('fornitore'):
                queryset = queryset.filter(fornitore=self.cleaned_data['fornitore'])

            # Filtro stato
            if self.cleaned_data.get('stato'):
                queryset = queryset.filter(stato=self.cleaned_data['stato'])

            # Filtro tipo origine
            if self.cleaned_data.get('tipo_origine'):
                queryset = queryset.filter(tipo_origine=self.cleaned_data['tipo_origine'])

        return queryset
