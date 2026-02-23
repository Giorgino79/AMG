"""
Servizio per il calcolo delle buste paga
Implementa tutta la logica retributiva conforme al diritto del lavoro italiano
"""

from decimal import Decimal
from datetime import date
from django.db import transaction
from ..models import (
    BustaPaga,
    VoceBustaPaga,
    FeriePermessiPayroll,
    DatiContrattualiPayroll,
)


class PayrollCalculator:
    """Calcola la busta paga secondo il CCNL applicabile"""

    # Aliquote IRPEF 2025 (aggiornare annualmente!)
    # Scaglioni: (limite_superiore, aliquota_percentuale)
    SCAGLIONI_IRPEF = [
        (15000, Decimal("23.00")),   # Fino a 15.000€: 23%
        (28000, Decimal("25.00")),   # Da 15.001€ a 28.000€: 25%  (era 27%)
        (50000, Decimal("35.00")),   # Da 28.001€ a 50.000€: 35%  (era 38%)
        (float("inf"), Decimal("43.00")),  # Oltre 50.000€: 43%
    ]

    # Contributi INPS a carico dipendente (esempio, variano per categoria)
    CONTRIBUTO_INPS_DIPENDENTE = Decimal("9.19")

    def __init__(self, user, mese, anno):
        """
        Inizializza il calcolatore

        Args:
            user: istanza del modello User (dipendente)
            mese: mese di riferimento (1-12)
            anno: anno di riferimento
        """
        self.user = user
        self.mese = mese
        self.anno = anno

        # Verifica esistenza dati payroll
        try:
            self.dati_payroll = user.dati_payroll
        except DatiContrattualiPayroll.DoesNotExist:
            raise ValueError(
                f"Dati payroll non configurati per {user.get_full_name()}"
            )

        self.ccnl = self.dati_payroll.ccnl
        self.livello = self.dati_payroll.livello

        if not self.ccnl or not self.livello:
            raise ValueError(
                f"CCNL e Livello non configurati per {user.get_full_name()}"
            )

    def _applica_scaglioni_irpef(self, reddito_annuo):
        """
        Applica gli scaglioni IRPEF progressivi a un reddito annuo.

        Args:
            reddito_annuo: Reddito annuo imponibile (Decimal)

        Returns:
            Decimal: IRPEF totale calcolata

        Example:
            Per reddito di €30.000:
            - Primi €15.000 tassati al 23% = €3.450
            - Da €15.001 a €28.000 (€13.000) al 25% = €3.250
            - Da €28.001 a €30.000 (€2.000) al 35% = €700
            - TOTALE IRPEF = €7.400
        """
        irpef_totale = Decimal("0")
        residuo = reddito_annuo
        scaglione_precedente = Decimal("0")

        for limite_superiore, aliquota in self.SCAGLIONI_IRPEF:
            if residuo <= 0:
                break

            # Calcola la porzione di reddito in questo scaglione
            if limite_superiore == float("inf"):
                limite_dec = residuo + scaglione_precedente
            else:
                limite_dec = Decimal(str(limite_superiore))

            scaglione_corrente = min(residuo, limite_dec - scaglione_precedente)

            # Applica aliquota a questo scaglione
            irpef_scaglione = scaglione_corrente * (aliquota / Decimal("100"))
            irpef_totale += irpef_scaglione

            # Aggiorna per prossimo scaglione
            residuo -= scaglione_corrente
            scaglione_precedente = limite_dec

        return irpef_totale.quantize(Decimal("0.01"))

    @transaction.atomic
    def calcola_busta_paga(self, ore_ordinarie, ore_straordinari=None, assenze=None):
        """
        Calcola la busta paga completa

        Args:
            ore_ordinarie: ore lavorate normali
            ore_straordinari: dict con chiavi 'feriale', 'festivo', 'notturno'
            assenze: dict con chiavi 'ferie', 'rol', 'permessi', 'malattia'

        Returns:
            BustaPaga: istanza della busta paga creata
        """
        ore_straordinari = ore_straordinari or {}
        assenze = assenze or {}

        # Verifica se esiste già una busta per questo mese/anno
        try:
            busta = BustaPaga.objects.get(
                user=self.user, mese=self.mese, anno=self.anno
            )
            # Elimina le voci esistenti per ricalcolare
            busta.voci.all().delete()
        except BustaPaga.DoesNotExist:
            # Crea nuova busta paga
            busta = BustaPaga.objects.create(
                user=self.user,
                mese=self.mese,
                anno=self.anno,
            )

        # Imposta le ore
        busta.ore_ordinarie = ore_ordinarie
        busta.ore_straordinario_feriale = ore_straordinari.get("feriale", 0)
        busta.ore_straordinario_festivo = ore_straordinari.get("festivo", 0)
        busta.ore_straordinario_notturno = ore_straordinari.get("notturno", 0)
        busta.ore_ferie = assenze.get("ferie", 0)
        busta.ore_rol = assenze.get("rol", 0)
        busta.ore_permessi = assenze.get("permessi", 0)
        busta.ore_malattia = assenze.get("malattia", 0)

        # 1. Calcola competenze (retribuzione lorda)
        self._calcola_competenze(busta, ore_ordinarie, ore_straordinari)

        # 2. Calcola imponibili (fiscale e contributivo)
        self._calcola_imponibili(busta)

        # 3. Calcola trattenute previdenziali
        self._calcola_contributi_inps(busta)

        # 4. Calcola IRPEF e addizionali
        self._calcola_irpef(busta)

        # 5. Calcola detrazioni fiscali
        self._calcola_detrazioni(busta)

        # 6. Calcola netto
        busta.netto_busta = (
            busta.imponibile_fiscale
            - busta.ritenute_previdenziali
            - busta.ritenute_irpef
            - busta.addizionale_regionale
            - busta.addizionale_comunale
            + busta.detrazioni_fiscali
            - busta.altre_trattenute
        )

        # 7. Calcola TFR
        self._calcola_tfr(busta)

        busta.save()

        # 8. Aggiorna ferie e permessi
        self._aggiorna_ferie_permessi(assenze)

        return busta

    def _calcola_competenze(self, busta, ore_ordinarie, ore_straordinari):
        """Calcola tutte le competenze (retribuzione lorda)"""
        paga_oraria = self.dati_payroll.calcola_paga_oraria()

        # 1. Paga base ordinaria
        importo_base = paga_oraria * Decimal(str(ore_ordinarie))
        VoceBustaPaga.objects.create(
            busta_paga=busta,
            tipo="COMPETENZA",
            descrizione="Retribuzione ordinaria",
            quantita=Decimal(str(ore_ordinarie)),
            importo_unitario=paga_oraria,
            importo_totale=importo_base,
        )

        # 2. Straordinari
        for tipo, ore in ore_straordinari.items():
            if ore > 0:
                if tipo == "feriale":
                    percentuale = self.ccnl.percentuale_straordinario_feriale
                    desc = "Straordinario feriale"
                elif tipo == "festivo":
                    percentuale = self.ccnl.percentuale_straordinario_festivo
                    desc = "Straordinario festivo"
                else:  # notturno
                    percentuale = self.ccnl.percentuale_straordinario_notturno
                    desc = "Straordinario notturno"

                maggiorazione = paga_oraria * (percentuale / Decimal("100"))
                paga_straord = paga_oraria + maggiorazione
                importo_straord = paga_straord * Decimal(str(ore))

                VoceBustaPaga.objects.create(
                    busta_paga=busta,
                    tipo="COMPETENZA",
                    descrizione=f"{desc} (+{percentuale}%)",
                    quantita=Decimal(str(ore)),
                    importo_unitario=paga_straord,
                    importo_totale=importo_straord,
                )

        # 3. Elementi retributivi del CCNL (contingenza, EDR, indennità, ecc.)
        for elemento in self.ccnl.elementi_retributivi.filter(attivo=True):
            importo = self._calcola_elemento_retributivo(elemento, importo_base)
            if importo > 0:
                VoceBustaPaga.objects.create(
                    busta_paga=busta,
                    tipo="COMPETENZA",
                    descrizione=elemento.nome,
                    importo_totale=importo,
                    imponibile_fiscale=(
                        elemento.natura in ["IMPONIBILE", "SOLO_FISCALE"]
                    ),
                    imponibile_contributivo=(
                        elemento.natura in ["IMPONIBILE", "SOLO_CONTRIBUTIVO"]
                    ),
                )

    def _calcola_elemento_retributivo(self, elemento, paga_base):
        """Calcola singolo elemento retributivo (contingenza, EDR, ecc.)"""
        if elemento.tipo_calcolo == "FISSO":
            return elemento.valore
        elif elemento.tipo_calcolo == "PERCENTUALE_PAGA_BASE":
            return paga_base * (elemento.valore / Decimal("100"))
        elif elemento.tipo_calcolo == "PERCENTUALE_RETRIBUZIONE":
            # Richiederebbe il totale retribuzione, per semplicità usiamo paga_base
            return paga_base * (elemento.valore / Decimal("100"))
        # ORARIO richiederebbe ore specifiche, non implementato qui
        return Decimal("0")

    def _calcola_imponibili(self, busta):
        """Calcola imponibile fiscale e contributivo"""
        imponibile_fiscale = Decimal("0")
        imponibile_contributivo = Decimal("0")

        for voce in busta.voci.filter(tipo="COMPETENZA"):
            if voce.imponibile_fiscale:
                imponibile_fiscale += voce.importo_totale
            if voce.imponibile_contributivo:
                imponibile_contributivo += voce.importo_totale

        busta.imponibile_fiscale = imponibile_fiscale.quantize(Decimal("0.01"))
        busta.imponibile_contributivo = imponibile_contributivo.quantize(
            Decimal("0.01")
        )

    def _calcola_contributi_inps(self, busta):
        """Calcola contributi previdenziali a carico dipendente"""
        contributi = busta.imponibile_contributivo * (
            self.CONTRIBUTO_INPS_DIPENDENTE / Decimal("100")
        )
        busta.ritenute_previdenziali = contributi.quantize(Decimal("0.01"))

        VoceBustaPaga.objects.create(
            busta_paga=busta,
            tipo="TRATTENUTA",
            descrizione=f"Contributi INPS ({self.CONTRIBUTO_INPS_DIPENDENTE}%)",
            importo_totale=busta.ritenute_previdenziali,
            imponibile_fiscale=False,
            imponibile_contributivo=False,
        )

    def _calcola_irpef(self, busta):
        """
        Calcola IRPEF con metodo del CUMULO ANNUALE (progressivo).

        NORMATIVA:
        L'IRPEF va calcolata sul reddito CUMULATO da inizio anno, non mese per mese.
        Questo garantisce che l'aliquota progressiva sia applicata correttamente.

        METODO:
        1. Somma reddito cumulato da gennaio al mese corrente
        2. Calcola IRPEF totale sul cumulo
        3. Sottrai IRPEF già trattenuta nei mesi precedenti
        4. Il risultato è l'IRPEF del mese corrente

        SCAGLIONI IRPEF 2025 (aggiornare annualmente!):
        - Fino a €15.000: 23%
        - Da €15.001 a €28.000: 25% (vecchio sistema: 27%)
        - Da €28.001 a €50.000: 35% (vecchio sistema: 38%)
        - Oltre €50.000: 43%

        Riferimenti:
        - Art. 11 TUIR (D.P.R. 917/1986)
        - Legge di Bilancio 2024 (modifica scaglioni)
        - Circolare Agenzia Entrate n. 2/E del 2024
        """
        # 1. Recupera buste paga precedenti dell'anno corrente
        buste_precedenti = BustaPaga.objects.filter(
            user=self.user,
            anno=self.anno,
            mese__lt=self.mese,
            confermata=True  # Solo buste confermate
        ).order_by('mese')

        # 2. Calcola reddito cumulato e IRPEF già pagata
        reddito_cumulato = Decimal("0")
        irpef_gia_pagata = Decimal("0")

        for busta_prec in buste_precedenti:
            # Imponibile IRPEF = imponibile fiscale - contributi previdenziali
            imponibile_prec = busta_prec.imponibile_fiscale - busta_prec.ritenute_previdenziali
            reddito_cumulato += imponibile_prec
            irpef_gia_pagata += busta_prec.ritenute_irpef

        # 3. Aggiungi il mese corrente al cumulo
        imponibile_corrente = busta.imponibile_fiscale - busta.ritenute_previdenziali
        reddito_cumulato += imponibile_corrente

        # 4. Calcola IRPEF sul cumulo annuale
        irpef_cumulata = self._applica_scaglioni_irpef(reddito_cumulato)

        # 5. IRPEF del mese corrente = IRPEF cumulata - IRPEF già pagata
        busta.ritenute_irpef = (irpef_cumulata - irpef_gia_pagata).quantize(Decimal("0.01"))

        # 6. Gestisci eventuale conguaglio negativo (raro, ma possibile)
        if busta.ritenute_irpef < 0:
            # In caso di conguaglio negativo (es. bonus Renzi, detrazioni elevate)
            # mantenere a 0 e gestire il conguaglio separatamente
            busta.ritenute_irpef = Decimal("0")

        VoceBustaPaga.objects.create(
            busta_paga=busta,
            tipo="TRATTENUTA",
            descrizione="IRPEF",
            importo_totale=busta.ritenute_irpef,
            imponibile_fiscale=False,
            imponibile_contributivo=False,
        )

        # Addizionale Regionale
        busta.addizionale_regionale = (
            imponibile
            * (self.dati_payroll.aliquota_addizionale_regionale / Decimal("100"))
        ).quantize(Decimal("0.01"))

        if busta.addizionale_regionale > 0:
            VoceBustaPaga.objects.create(
                busta_paga=busta,
                tipo="TRATTENUTA",
                descrizione=f"Addizionale Regionale ({self.dati_payroll.aliquota_addizionale_regionale}%)",
                importo_totale=busta.addizionale_regionale,
                imponibile_fiscale=False,
                imponibile_contributivo=False,
            )

        # Addizionale Comunale
        busta.addizionale_comunale = (
            imponibile
            * (self.dati_payroll.aliquota_addizionale_comunale / Decimal("100"))
        ).quantize(Decimal("0.01"))

        if busta.addizionale_comunale > 0:
            VoceBustaPaga.objects.create(
                busta_paga=busta,
                tipo="TRATTENUTA",
                descrizione=f"Addizionale Comunale ({self.dati_payroll.aliquota_addizionale_comunale}%)",
                importo_totale=busta.addizionale_comunale,
                imponibile_fiscale=False,
                imponibile_contributivo=False,
            )

    def _calcola_detrazioni(self, busta):
        """
        Calcola detrazioni fiscali per lavoro dipendente

        NOTA: Formula semplificata. In produzione andrebbero considerati:
        - Reddito annuo complessivo
        - Numero giorni lavorati nell'anno
        - Altre detrazioni specifiche
        """
        if not self.dati_payroll.detrazione_lavoro_dipendente:
            busta.detrazioni_fiscali = Decimal("0")
            return

        # Stima reddito annuo basato su imponibile mensile
        reddito_annuo = busta.imponibile_fiscale * Decimal("12")

        # Formula detrazioni lavoro dipendente (semplificata)
        if reddito_annuo <= 15000:
            detrazione_annua = Decimal("1955")
        elif reddito_annuo <= 28000:
            detrazione_annua = Decimal("1910") + Decimal("1190") * (
                (Decimal("28000") - reddito_annuo) / Decimal("13000")
            )
        elif reddito_annuo <= 50000:
            detrazione_annua = Decimal("1910") * (
                (Decimal("50000") - reddito_annuo) / Decimal("22000")
            )
        else:
            detrazione_annua = Decimal("0")

        # Detrazione mensile
        busta.detrazioni_fiscali = (detrazione_annua / Decimal("12")).quantize(
            Decimal("0.01")
        )

        if busta.detrazioni_fiscali > 0:
            VoceBustaPaga.objects.create(
                busta_paga=busta,
                tipo="DEDUZIONE",
                descrizione="Detrazioni lavoro dipendente",
                importo_totale=busta.detrazioni_fiscali,
                imponibile_fiscale=False,
                imponibile_contributivo=False,
            )

    def _calcola_tfr(self, busta):
        """
        Calcola TFR maturato nel mese secondo normativa italiana.

        FORMULA CORRETTA: TFR = Retribuzione Utile TFR / 13.5

        Retribuzione Utile TFR include:
        - Paga base, contingenza, scatti anzianità, superminimo
        - Indennità fisse e continuative utili TFR (secondo CCNL)

        ESCLUSI dal TFR:
        - Rimborsi spese
        - Premi/compensi occasionali non continuativi
        - Elementi retributivi con flag 'incluso_tfr=False'

        NOTA: La rivalutazione TFR (indice ISTAT + 1.5% fisso) viene
        applicata annualmente sul montante accumulato, non mensilmente.

        Riferimenti normativi:
        - Art. 2120 Codice Civile
        - Legge n. 297/1982
        - Circolare INPS n. 82/2007
        """
        # Calcola retribuzione utile per TFR
        retribuzione_utile_tfr = Decimal("0")

        for voce in busta.voci.filter(tipo="COMPETENZA"):
            # Include solo voci utili per TFR
            # Verifica se la voce appartiene a un ElementoRetributivo
            if hasattr(voce, 'elemento_retributivo_ref'):
                # Se c'è un riferimento, usa il flag incluso_tfr
                # (questo richiede modifica al model VoceBustaPaga - per ora includiamo tutto)
                pass

            # Per ora: includi tutte le competenze imponibili contributivamente
            if voce.imponibile_contributivo:
                retribuzione_utile_tfr += voce.importo_totale

        # Formula corretta: TFR = Retribuzione Utile / 13.5
        # (1/13.5 = 0.074074... ≈ 7.41% non 6.91%!)
        busta.tfr_maturato = (retribuzione_utile_tfr / Decimal("13.5")).quantize(
            Decimal("0.01")
        )

        # TODO: Implementare rivalutazione TFR annuale
        # - Calcolare montante TFR accumulato
        # - Applicare rivalutazione ISTAT (75% aumento ISTAT)
        # - Applicare quota fissa 1.5% annuo
        # - Sottrarre eventuale imposta sostitutiva 17% su rivalutazione

    def _aggiorna_ferie_permessi(self, assenze):
        """Aggiorna i contatori di ferie e permessi utilizzati"""
        tipo_mapping = {
            "ferie": "FERIE",
            "rol": "ROL",
            "permessi": "PERMESSO_RETRIBUITO",
            "malattia": "MALATTIA",
        }

        for tipo_assenza, ore in assenze.items():
            if ore > 0 and tipo_assenza in tipo_mapping:
                fp, created = FeriePermessiPayroll.objects.get_or_create(
                    user=self.user,
                    anno=self.anno,
                    tipo=tipo_mapping[tipo_assenza],
                )

                fp.ore_godute += Decimal(str(ore))
                fp.save()

    def matura_ferie_permessi_mensili(self):
        """
        Calcola la maturazione mensile di ferie e permessi

        Chiamare questo metodo ogni mese per aggiornare i contatori di maturazione
        """
        # Ore giornaliere standard
        ore_giornaliere = self.dati_payroll.ore_settimanali / Decimal("5")

        # 1. Maturazione FERIE
        # Giorni ferie annui dal CCNL * ore giornaliere / 12 mesi
        ore_ferie_mensili = (
            Decimal(str(self.ccnl.giorni_ferie_annui))
            * ore_giornaliere
            / Decimal("12")
        )

        fp_ferie, _ = FeriePermessiPayroll.objects.get_or_create(
            user=self.user, anno=self.anno, tipo="FERIE"
        )
        fp_ferie.ore_maturate += ore_ferie_mensili
        fp_ferie.save()

        # 2. Maturazione ROL
        ore_rol_mensili = self.ccnl.ore_rol_annue / Decimal("12")

        fp_rol, _ = FeriePermessiPayroll.objects.get_or_create(
            user=self.user, anno=self.anno, tipo="ROL"
        )
        fp_rol.ore_maturate += ore_rol_mensili
        fp_rol.save()

        # 3. Permessi Retribuiti (ex festività)
        ore_permessi_mensili = self.ccnl.ore_permessi_retribuiti_annui / Decimal("12")

        fp_permessi, _ = FeriePermessiPayroll.objects.get_or_create(
            user=self.user, anno=self.anno, tipo="PERMESSO_RETRIBUITO"
        )
        fp_permessi.ore_maturate += ore_permessi_mensili
        fp_permessi.save()

    def get_riepilogo_annuale(self):
        """
        Restituisce un riepilogo delle buste paga dell'anno corrente

        Returns:
            dict: statistiche annuali
        """
        buste = BustaPaga.objects.filter(user=self.user, anno=self.anno).order_by(
            "mese"
        )

        riepilogo = {
            "anno": self.anno,
            "dipendente": self.user.get_full_name(),
            "numero_buste": buste.count(),
            "totale_ore_ordinarie": sum(b.ore_ordinarie for b in buste),
            "totale_ore_straordinari": sum(
                b.ore_straordinario_feriale
                + b.ore_straordinario_festivo
                + b.ore_straordinario_notturno
                for b in buste
            ),
            "totale_imponibile_fiscale": sum(b.imponibile_fiscale for b in buste),
            "totale_imponibile_contributivo": sum(
                b.imponibile_contributivo for b in buste
            ),
            "totale_ritenute_previdenziali": sum(
                b.ritenute_previdenziali for b in buste
            ),
            "totale_ritenute_irpef": sum(b.ritenute_irpef for b in buste),
            "totale_netto": sum(b.netto_busta for b in buste),
            "totale_tfr": sum(b.tfr_maturato for b in buste),
        }

        return riepilogo
