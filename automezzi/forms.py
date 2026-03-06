from django import forms
from .models import (
    Automezzo,
    Manutenzione,
    AllegatoManutenzione,
    Rifornimento,
    EventoAutomezzo,
    AffidamentoMezzo,
    Gruppo,
    ManutenzioneGruppo,
    EventoGruppo,
    AffidamentoGruppo,
)


class AutomezzoForm(forms.ModelForm):
    class Meta:
        model = Automezzo
        fields = [
            "numero_mezzo",
            "targa",
            "marca",
            "modello",
            "anno_immatricolazione",
            "chilometri_attuali",
            "attivo",
            "disponibile",
            "bloccata",
            "motivo_blocco",
            "libretto_fronte",
            "libretto_retro",
            "assicurazione",
            "data_revisione",
            "assegnato_a",
            "carta_carburante",
            "pin_carta_carburante",
        ]
        widgets = {
            "data_revisione": forms.DateInput(attrs={"type": "date"}),
            "motivo_blocco": forms.Textarea(attrs={"rows": 2}),
        }


class ManutenzioneForm(forms.ModelForm):
    """Form base per la manutenzione (usato per aggiornamenti)"""

    class Meta:
        model = Manutenzione
        fields = [
            "automezzo",
            "data_prevista",
            "descrizione",
            "stato",
            "fornitore",
            "luogo",
            "costo",
            "seguito_da",
            "responsabile",
            "allegati",
        ]
        widgets = {
            "data_prevista": forms.DateInput(attrs={"type": "date"}),
            "descrizione": forms.Textarea(attrs={"rows": 3}),
            "luogo": forms.TextInput(
                attrs={"placeholder": "Es. Officina Rossi, Via Roma 10, Milano"}
            ),
        }


class ManutenzioneCreateForm(forms.ModelForm):
    """Form specifico per l'apertura di una nuova manutenzione (Automezzi o Gruppi)"""
    
    gruppo = forms.ModelChoiceField(
        queryset=None,
        required=False,
        label="Gruppo Elettrogeno",
        help_text="Seleziona il gruppo elettrogeno (alternativo all'automezzo)"
    )

    class Meta:
        model = Manutenzione
        fields = [
            "automezzo",
            "data_prevista",
            "descrizione",
            "fornitore",
            "luogo",
            "responsabile",
            "allegati",
        ]
        widgets = {
            "data_prevista": forms.DateInput(attrs={"type": "date"}),
            "descrizione": forms.Textarea(
                attrs={
                    "rows": 3,
                    "placeholder": "Descrivi il tipo di manutenzione da eseguire...",
                }
            ),
            "luogo": forms.TextInput(
                attrs={"placeholder": "Es. Officina Rossi, Via Roma 10, Milano"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Importo qui per evitare circular imports
        from .models import Gruppo
        
        # Imposta queryset per gruppi
        self.fields['gruppo'].queryset = Gruppo.objects.filter(attivo=True)
        
        # Per le nuove manutenzioni, il stato è sempre "aperta"
        self.instance.stato = "aperta"

        # Rendi campi opzionali
        self.fields["automezzo"].required = False
        self.fields["fornitore"].required = False
        self.fields["luogo"].required = False
        self.fields["responsabile"].required = False
        self.fields["allegati"].required = False

    def clean(self):
        cleaned_data = super().clean()
        automezzo = cleaned_data.get('automezzo')
        gruppo = cleaned_data.get('gruppo')

        # Validazione XOR: deve essere selezionato SOLO uno tra automezzo e gruppo
        if not automezzo and not gruppo:
            raise forms.ValidationError(
                "Devi selezionare un Automezzo OPPURE un Gruppo Elettrogeno."
            )
        
        if automezzo and gruppo:
            raise forms.ValidationError(
                "Puoi selezionare solo un Automezzo O un Gruppo Elettrogeno, non entrambi."
            )

        return cleaned_data


class ManutenzioneUpdateForm(forms.ModelForm):
    """Form specifico per l'aggiornamento dello stato manutenzione"""

    class Meta:
        model = Manutenzione
        fields = [
            "automezzo",
            "data_prevista",
            "descrizione",
            "stato",
            "fornitore",
            "luogo",
            "costo",
            "seguito_da",
            "responsabile",
            "allegati",
        ]
        widgets = {
            "data_prevista": forms.DateInput(attrs={"type": "date"}),
            "descrizione": forms.Textarea(attrs={"rows": 3}),
            "luogo": forms.TextInput(
                attrs={"placeholder": "Es. Officina Rossi, Via Roma 10, Milano"}
            ),
            "costo": forms.NumberInput(attrs={"step": "0.01", "placeholder": "0.00"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Rendi il campo seguito_da read-only (non modificabile)
        if "seguito_da" in self.fields:
            self.fields["seguito_da"].widget.attrs["readonly"] = True
            self.fields["seguito_da"].help_text = (
                "Utente che ha aperto la pratica (non modificabile)"
            )

        # Rendi il costo obbligatorio solo per stato "terminata"
        if self.instance and hasattr(self.instance, "stato"):
            if self.instance.stato == "terminata":
                self.fields["costo"].required = True
                self.fields["costo"].help_text = (
                    "Il costo è obbligatorio per manutenzioni terminate"
                )
            else:
                self.fields["costo"].required = False
                self.fields["costo"].help_text = (
                    "Il costo può essere inserito quando la manutenzione è terminata"
                )


class ManutenzioneResponsabileForm(forms.ModelForm):
    """Form specifico per il responsabile che porta il mezzo in manutenzione"""

    class Meta:
        model = Manutenzione
        fields = ["foglio_accettazione", "note_responsabile"]
        widgets = {
            "note_responsabile": forms.Textarea(
                attrs={
                    "rows": 3,
                    "placeholder": "Inserire nome dell'addetto con cui si ha parlato e altre note importanti...",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Personalizza i campi
        self.fields["foglio_accettazione"].help_text = (
            "Carica il foglio di accettazione firmato dall'officina"
        )
        self.fields["note_responsabile"].help_text = (
            "Nome dell'addetto, dettagli sulla consegna, condizioni del mezzo, ecc."
        )


class ManutenzioneFinaleForm(forms.ModelForm):
    """Form specifico per il completamento finale della manutenzione"""

    class Meta:
        model = Manutenzione
        fields = ["costo", "note_finali", "fattura_fornitore"]
        widgets = {
            "costo": forms.NumberInput(
                attrs={"step": "0.01", "placeholder": "0.00", "required": True}
            ),
            "note_finali": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": "Note finali sulla manutenzione, eventuali problemi risolti, raccomandazioni...",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Costo obbligatorio per il completamento
        self.fields["costo"].required = True
        self.fields["costo"].help_text = (
            "Costo totale della manutenzione (indicare l'imponibile fattura, non importo ivato)"
        )

        # Personalizza altri campi
        self.fields["note_finali"].help_text = (
            "Riepilogo del lavoro svolto, parti sostituite, raccomandazioni future"
        )
        self.fields["fattura_fornitore"].help_text = (
            "Carica la fattura ricevuta dal fornitore"
        )


class AllegatoManutenzioneForm(forms.ModelForm):
    """Form per aggiungere allegati aggiuntivi alla manutenzione"""

    class Meta:
        model = AllegatoManutenzione
        fields = ["nome", "file"]
        widgets = {
            "nome": forms.TextInput(
                attrs={
                    "placeholder": "Es. Foto danni, Preventivo alternativo, Documento garanzia..."
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["nome"].help_text = "Nome descrittivo per identificare l'allegato"
        self.fields["file"].help_text = "Seleziona il file da allegare"


class RifornimentoForm(forms.ModelForm):
    gruppo = forms.ModelChoiceField(
        queryset=None,
        required=False,
        label="Gruppo Elettrogeno",
        help_text="Seleziona il gruppo elettrogeno (alternativo all'automezzo)"
    )

    class Meta:
        model = Rifornimento
        fields = [
            "automezzo",
            "data",
            "litri",
            "costo_totale",
            "chilometri",
            "scontrino",
        ]
        widgets = {
            "data": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Importo qui per evitare circular imports
        from .models import Gruppo

        # Imposta queryset per gruppi
        self.fields['gruppo'].queryset = Gruppo.objects.filter(attivo=True)

        # Rendi automezzo opzionale
        self.fields["automezzo"].required = False

    def clean(self):
        cleaned_data = super().clean()
        automezzo = cleaned_data.get('automezzo')
        gruppo = cleaned_data.get('gruppo')

        # Validazione XOR: deve essere selezionato SOLO uno tra automezzo e gruppo
        if not automezzo and not gruppo:
            raise forms.ValidationError(
                "Devi selezionare un Automezzo OPPURE un Gruppo Elettrogeno."
            )

        if automezzo and gruppo:
            raise forms.ValidationError(
                "Puoi selezionare solo un Automezzo O un Gruppo Elettrogeno, non entrambi."
            )

        return cleaned_data


class EventoAutomezzoForm(forms.ModelForm):
    gruppo = forms.ModelChoiceField(
        queryset=None,
        required=False,
        label="Gruppo Elettrogeno",
        help_text="Seleziona il gruppo elettrogeno (alternativo all'automezzo)"
    )

    class Meta:
        model = EventoAutomezzo
        fields = [
            "automezzo",
            "tipo",
            "data_evento",
            "descrizione",
            "costo",
            "dipendente_coinvolto",
            "file_allegato",
            "risolto",
        ]
        widgets = {
            "data_evento": forms.DateInput(attrs={"type": "date"}),
            "descrizione": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Importo qui per evitare circular imports
        from .models import Gruppo

        # Imposta queryset per gruppi
        self.fields['gruppo'].queryset = Gruppo.objects.filter(attivo=True)

        # Rendi automezzo opzionale
        self.fields["automezzo"].required = False

    def clean(self):
        cleaned_data = super().clean()
        automezzo = cleaned_data.get('automezzo')
        gruppo = cleaned_data.get('gruppo')

        # Validazione XOR: deve essere selezionato SOLO uno tra automezzo e gruppo
        if not automezzo and not gruppo:
            raise forms.ValidationError(
                "Devi selezionare un Automezzo OPPURE un Gruppo Elettrogeno."
            )

        if automezzo and gruppo:
            raise forms.ValidationError(
                "Puoi selezionare solo un Automezzo O un Gruppo Elettrogeno, non entrambi."
            )

        return cleaned_data


class AffidamentoMezzoForm(forms.ModelForm):
    class Meta:
        model = AffidamentoMezzo
        fields = [
            "user",
            "automezzo",
            "data_inizio",
            "data_fine",
            "video_stato_vettura",
            "km_iniziali",
            "scopo_viaggio",
            "carburante",
            "danni_consegna",
            "note",
        ]
        widgets = {
            "data_inizio": forms.DateInput(attrs={"type": "date"}),
            "data_fine": forms.DateInput(attrs={"type": "date"}),
            "scopo_viaggio": forms.TextInput(
                attrs={"placeholder": "Es. Trasferta cliente Milano, consegna materiale..."}
            ),
            "note": forms.Textarea(attrs={"rows": 3}),
            "km_iniziali": forms.NumberInput(attrs={"min": "0"}),
            "danni_consegna": forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["video_stato_vettura"].required = False
        self.fields["note"].required = False
        self.fields["danni_consegna"].required = False


class AffidamentoRientroForm(forms.ModelForm):
    class Meta:
        model = AffidamentoMezzo
        fields = [
            "km_finali",
            "video_rientro",
            "danni_rientro",
            "note_rientro",
        ]
        widgets = {
            "km_finali": forms.NumberInput(attrs={"min": "0"}),
            "note_rientro": forms.Textarea(
                attrs={"rows": 3, "placeholder": "Note sul rientro, eventuali danni, problemi riscontrati..."}
            ),
            "danni_rientro": forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["km_finali"].required = True
        self.fields["video_rientro"].required = False
        self.fields["danni_rientro"].required = False
        self.fields["note_rientro"].required = False

# ==============================
# FORMS PER GRUPPI ELETTROGENI
# ==============================

class GruppoForm(forms.ModelForm):
    class Meta:
        model = Gruppo
        fields = [
            "numero_gruppo",
            "matricola",
            "marca",
            "modello",
            "anno_produzione",
            "potenza_kva",
            "potenza_kw",
            "tipo_motore",
            "cilindrata",
            "numero_cilindri",
            "capacita_serbatoio",
            "consumo_orario",
            "tipo_raffreddamento",
            "tensione_uscita",
            "frequenza",
            "ore_lavoro_attuali",
            "intervallo_manutenzione_ore",
            "attivo",
            "disponibile",
            "bloccato",
            "motivo_blocco",
            "ubicazione",
            "manuale_uso",
            "certificato_conformita",
            "scheda_tecnica",
            "assegnato_a",
            "note",
        ]
        widgets = {
            "motivo_blocco": forms.Textarea(attrs={"rows": 2}),
            "note": forms.Textarea(attrs={"rows": 3}),
            "ubicazione": forms.TextInput(attrs={"placeholder": "Es. Magazzino A, Cantiere Roma, ecc."}),
        }


class ManutenzioneGruppoCreateForm(forms.ModelForm):
    """Form per creare una nuova manutenzione gruppo"""

    class Meta:
        model = ManutenzioneGruppo
        fields = [
            "gruppo",
            "data_prevista",
            "descrizione",
            "fornitore",
            "luogo",
            "responsabile",
            "ore_lavoro",
        ]
        widgets = {
            "data_prevista": forms.DateInput(attrs={"type": "date"}),
            "descrizione": forms.Textarea(
                attrs={
                    "rows": 3,
                    "placeholder": "Descrivi il tipo di manutenzione da eseguire...",
                }
            ),
            "luogo": forms.TextInput(attrs={"placeholder": "Es. Sede, Cantiere, ecc."}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance.stato = "aperta"
        self.fields["fornitore"].required = False
        self.fields["luogo"].required = False
        self.fields["ore_lavoro"].required = False


class ManutenzioneGruppoUpdateForm(forms.ModelForm):
    """Form per aggiornare una manutenzione gruppo"""

    class Meta:
        model = ManutenzioneGruppo
        fields = [
            "data_prevista",
            "descrizione",
            "stato",
            "fornitore",
            "luogo",
            "costo",
            "ore_lavoro",
            "responsabile",
            "cambio_olio",
            "cambio_filtro_aria",
            "cambio_filtro_carburante",
            "cambio_filtro_olio",
            "revisione_batteria",
            "prova_funzionamento",
            "note_finali",
        ]
        widgets = {
            "data_prevista": forms.DateInput(attrs={"type": "date"}),
            "descrizione": forms.Textarea(attrs={"rows": 3}),
            "note_finali": forms.Textarea(attrs={"rows": 4}),
        }


class EventoGruppoForm(forms.ModelForm):
    class Meta:
        model = EventoGruppo
        fields = [
            "gruppo",
            "tipo",
            "data_evento",
            "ore_lavoro",
            "descrizione",
            "costo",
            "dipendente_coinvolto",
            "file_allegato",
            "risolto",
        ]
        widgets = {
            "data_evento": forms.DateInput(attrs={"type": "date"}),
            "descrizione": forms.Textarea(attrs={"rows": 4}),
        }


class AffidamentoGruppoForm(forms.ModelForm):
    class Meta:
        model = AffidamentoGruppo
        fields = [
            "user",
            "gruppo",
            "data_inizio",
            "data_fine",
            "ore_iniziali",
            "scopo_utilizzo",
            "destinazione",
            "carburante",
            "video_stato_gruppo",
            "note",
        ]
        widgets = {
            "data_inizio": forms.DateInput(attrs={"type": "date"}),
            "data_fine": forms.DateInput(attrs={"type": "date"}),
            "scopo_utilizzo": forms.TextInput(
                attrs={"placeholder": "Es. Cantiere Via Roma, Evento XYZ, ecc."}
            ),
            "destinazione": forms.TextInput(
                attrs={"placeholder": "Es. Via Roma 10, Milano"}
            ),
            "note": forms.Textarea(attrs={"rows": 3}),
        }


class AffidamentoGruppoRientroForm(forms.ModelForm):
    """Form per registrare il rientro di un gruppo"""

    class Meta:
        model = AffidamentoGruppo
        fields = [
            "ore_finali",
            "carburante_rientro",
            "video_stato_gruppo_rientro",
            "note_rientro",
            "danni_riscontrati",
        ]
        widgets = {
            "note_rientro": forms.Textarea(
                attrs={"rows": 3, "placeholder": "Note sul rientro, eventuali problemi riscontrati..."}
            ),
            "danni_riscontrati": forms.Textarea(
                attrs={"rows": 3, "placeholder": "Descrivi eventuali danni riscontrati..."}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["ore_finali"].required = True
        self.fields["video_stato_gruppo_rientro"].required = False
        self.fields["danni_riscontrati"].required = False
        self.fields["note_rientro"].required = False
