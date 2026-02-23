# prodotti/forms.py
"""
PRODOTTI FORMS - Forms per anagrafica prodotti
==============================================
"""

from django import forms
from .models import Categoria, Prodotto
from anagrafica.models import Fornitore


class CategoriaForm(forms.ModelForm):
    """Form per gestione categorie prodotti"""

    class Meta:
        model = Categoria
        fields = ["nome_categoria", "icona", "descrizione", "attiva"]
        widgets = {
            "nome_categoria": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Nome della categoria"}
            ),
            "descrizione": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Descrizione dettagliata della categoria",
                }
            ),
            "icona": forms.FileInput(
                attrs={"class": "form-control", "accept": "image/*"}
            ),
            "attiva": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class ProdottoForm(forms.ModelForm):
    """
    Form per anagrafica prodotti.
    Gestisce solo dati anagrafici, QR/barcode e codici.
    """

    # Campo per validare EAN opzionalmente (checkbox)
    valida_ean = forms.BooleanField(
        required=False,
        initial=False,
        label="Valida codice EAN",
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
        help_text="Attiva per verificare il checksum EAN-13"
    )

    # Scelta QR code: generare o importare
    QRCODE_CHOICES = [
        ('nessuno', 'Nessun QR Code'),
        ('genera', 'Genera QR Code automatico'),
        ('importa', 'Importa QR Code esterno'),
    ]
    qrcode_opzione = forms.ChoiceField(
        choices=QRCODE_CHOICES,
        required=False,
        initial='genera',
        label="QR Code",
        widget=forms.RadioSelect(attrs={"class": "form-check-input"}),
    )

    # Scelta barcode: EAN o importare
    BARCODE_CHOICES = [
        ('nessuno', 'Nessun Barcode'),
        ('da_ean', 'Usa codice EAN come barcode'),
        ('importa', 'Importa Barcode esterno'),
    ]
    barcode_opzione = forms.ChoiceField(
        choices=BARCODE_CHOICES,
        required=False,
        initial='da_ean',
        label="Barcode",
        widget=forms.RadioSelect(attrs={"class": "form-check-input"}),
    )

    class Meta:
        model = Prodotto
        fields = [
            # Relazioni
            "categoria",
            "fornitore_principale",
            # Informazioni base
            "nome_prodotto",
            "descrizione_breve",
            "descrizione_completa",
            # Codici
            "ean",
            "codice_interno",
            "codice_fornitore",
            # QR e Barcode
            "qrcode_data",
            "qrcode_image",
            "barcode_data",
            "barcode_image",
            # Caratteristiche
            "tipo_prodotto",
            "misura",
            "peso_netto",
            "peso_lordo",
            "volume",
            "dimensioni",
            # Fiscale
            "aliquota_iva",
            # Stato
            "attivo",
            "novita",
            "in_evidenza",
            "merce_deperibile",
            # Media e note
            "immagine",
            "note_interne",
        ]
        widgets = {
            "categoria": forms.Select(attrs={"class": "form-select"}),
            "fornitore_principale": forms.Select(attrs={"class": "form-select"}),
            "nome_prodotto": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Nome commerciale del prodotto"}
            ),
            "descrizione_breve": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Descrizione breve"}
            ),
            "descrizione_completa": forms.Textarea(
                attrs={"class": "form-control", "rows": 3, "placeholder": "Descrizione dettagliata"}
            ),
            "ean": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "1234567890123", "maxlength": 13}
            ),
            "codice_interno": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Codice interno aziendale"}
            ),
            "codice_fornitore": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Codice del fornitore"}
            ),
            "qrcode_data": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Dati QR (auto-generati se vuoto)"}
            ),
            "qrcode_image": forms.FileInput(
                attrs={"class": "form-control", "accept": "image/*"}
            ),
            "barcode_data": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Dati barcode (usa EAN se vuoto)"}
            ),
            "barcode_image": forms.FileInput(
                attrs={"class": "form-control", "accept": "image/*"}
            ),
            "tipo_prodotto": forms.Select(attrs={"class": "form-select"}),
            "misura": forms.Select(attrs={"class": "form-select"}),
            "peso_netto": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.001", "min": "0"}
            ),
            "peso_lordo": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.001", "min": "0"}
            ),
            "volume": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.001", "min": "0"}
            ),
            "dimensioni": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Es: 10x5x3 cm"}
            ),
            "aliquota_iva": forms.Select(attrs={"class": "form-select"}),
            "attivo": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "novita": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "in_evidenza": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "merce_deperibile": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "immagine": forms.FileInput(
                attrs={"class": "form-control", "accept": "image/*"}
            ),
            "note_interne": forms.Textarea(
                attrs={"class": "form-control", "rows": 2, "placeholder": "Note interne"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtro categorie attive
        self.fields["categoria"].queryset = Categoria.objects.filter(attiva=True)
        # Filtro fornitori attivi
        self.fields["fornitore_principale"].queryset = Fornitore.objects.filter(
            attivo=True
        ).order_by('ragione_sociale')
        self.fields["fornitore_principale"].empty_label = "-- Nessun fornitore --"

        # Se editing, imposta le opzioni QR/barcode
        if self.instance and self.instance.pk:
            if self.instance.qrcode_image:
                self.fields['qrcode_opzione'].initial = 'importa'
            elif self.instance.qrcode_data:
                self.fields['qrcode_opzione'].initial = 'genera'

            if self.instance.barcode_image:
                self.fields['barcode_opzione'].initial = 'importa'
            elif self.instance.barcode_data:
                self.fields['barcode_opzione'].initial = 'da_ean'

    def clean(self):
        cleaned_data = super().clean()
        ean = cleaned_data.get("ean", "")
        valida_ean = cleaned_data.get("valida_ean", False)

        # Validazione EAN solo se richiesto e presente
        if valida_ean and ean:
            if not ean.isdigit() or len(ean) != 13:
                self.add_error('ean', "EAN deve essere di 13 cifre numeriche")
            else:
                # Checksum EAN-13
                digits = [int(d) for d in ean]
                checksum = sum(d * (1 if i % 2 == 0 else 3) for i, d in enumerate(digits[:-1]))
                calculated_check = (10 - (checksum % 10)) % 10
                if calculated_check != digits[-1]:
                    self.add_error('ean', f"Checksum EAN non valido (cifra di controllo attesa: {calculated_check})")

        return cleaned_data


class ProdottoSearchForm(forms.Form):
    """Form per ricerca prodotti"""

    search = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Cerca per nome, EAN, codice...",
            }
        ),
        label="Ricerca",
    )

    categoria = forms.ModelChoiceField(
        queryset=Categoria.objects.filter(attiva=True),
        required=False,
        empty_label="Tutte le categorie",
        widget=forms.Select(attrs={"class": "form-select"}),
        label="Categoria",
    )

    fornitore = forms.ModelChoiceField(
        queryset=Fornitore.objects.filter(attivo=True).order_by('ragione_sociale'),
        required=False,
        empty_label="Tutti i fornitori",
        widget=forms.Select(attrs={"class": "form-select"}),
        label="Fornitore",
    )

    attivo = forms.ChoiceField(
        choices=[("", "Tutti"), ("true", "Solo attivi"), ("false", "Solo disattivi")],
        required=False,
        widget=forms.Select(attrs={"class": "form-select"}),
        label="Stato",
    )

    tipo_prodotto = forms.ChoiceField(
        choices=[("", "Tutti i tipi")] + list(Prodotto.TipoProdotto.choices),
        required=False,
        widget=forms.Select(attrs={"class": "form-select"}),
        label="Tipo",
    )


class LottiProdottoFilterForm(forms.Form):
    """Form per filtrare lotti di un prodotto per date ordine e ricezione."""

    data_ordine_da = forms.DateField(
        required=False,
        label="Data ordine da",
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    data_ordine_a = forms.DateField(
        required=False,
        label="Data ordine a",
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    data_ricezione_da = forms.DateField(
        required=False,
        label="Data ricezione da",
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    data_ricezione_a = forms.DateField(
        required=False,
        label="Data ricezione a",
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )

    def filter_queryset(self, queryset):
        """Applica filtri al queryset."""
        if self.is_valid():
            if self.cleaned_data.get('data_ordine_da'):
                queryset = queryset.filter(
                    ricezione__ordine_acquisto__data_ordine__date__gte=self.cleaned_data['data_ordine_da']
                )
            if self.cleaned_data.get('data_ordine_a'):
                queryset = queryset.filter(
                    ricezione__ordine_acquisto__data_ordine__date__lte=self.cleaned_data['data_ordine_a']
                )
            if self.cleaned_data.get('data_ricezione_da'):
                queryset = queryset.filter(
                    ricezione__data_ricezione__date__gte=self.cleaned_data['data_ricezione_da']
                )
            if self.cleaned_data.get('data_ricezione_a'):
                queryset = queryset.filter(
                    ricezione__data_ricezione__date__lte=self.cleaned_data['data_ricezione_a']
                )
        return queryset
