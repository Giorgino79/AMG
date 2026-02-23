"""
Management command per popolare il database con dati dimostrativi per il payroll
"""

from django.core.management.base import BaseCommand
from decimal import Decimal
from datetime import date
from payroll.models import CCNL, LivelloInquadramento, ElementoRetributivo
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = "Popola il database con dati dimostrativi per il sistema payroll"

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Inizializzazione dati payroll..."))

        # 1. Crea CCNL Commercio
        ccnl_commercio, created = CCNL.objects.get_or_create(
            nome="CCNL Commercio e Terziario",
            defaults={
                "tipo": "COMMERCIO",
                "data_inizio_validita": date(2024, 1, 1),
                "giorni_ferie_annui": 26,
                "ore_rol_annue": Decimal("88.00"),
                "ore_permessi_retribuiti_annui": Decimal("32.00"),
                "percentuale_straordinario_feriale": Decimal("15.00"),
                "percentuale_straordinario_festivo": Decimal("30.00"),
                "percentuale_straordinario_notturno": Decimal("50.00"),
                "ha_tredicesima": True,
                "ha_quattordicesima": False,
                "ha_scatti_anzianita": True,
                "anni_per_scatto": 2,
                "importo_scatto": Decimal("25.00"),
                "numero_massimo_scatti": 10,
            },
        )
        if created:
            self.stdout.write(
                self.style.SUCCESS(f"✓ Creato {ccnl_commercio.nome}")
            )

        # 2. Crea Livelli per CCNL Commercio
        livelli_commercio = [
            {
                "codice": "1",
                "descrizione": "Addetto vendite / Commesso",
                "paga_base_mensile": Decimal("1500.00"),
            },
            {
                "codice": "2",
                "descrizione": "Operatore specializzato",
                "paga_base_mensile": Decimal("1650.00"),
            },
            {
                "codice": "3",
                "descrizione": "Impiegato amministrativo",
                "paga_base_mensile": Decimal("1800.00"),
            },
            {
                "codice": "4",
                "descrizione": "Capo reparto",
                "paga_base_mensile": Decimal("2000.00"),
            },
            {
                "codice": "5",
                "descrizione": "Responsabile di settore",
                "paga_base_mensile": Decimal("2300.00"),
            },
        ]

        for liv_data in livelli_commercio:
            liv, created = LivelloInquadramento.objects.get_or_create(
                ccnl=ccnl_commercio,
                codice=liv_data["codice"],
                defaults={
                    "descrizione": liv_data["descrizione"],
                    "paga_base_mensile": liv_data["paga_base_mensile"],
                    "ore_settimanali_standard": Decimal("40.00"),
                },
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"  ✓ Livello {liv.codice}: {liv.descrizione}"
                    )
                )

        # 3. Crea Elementi Retributivi per CCNL Commercio
        elementi_commercio = [
            {
                "codice": "CONT",
                "nome": "Contingenza",
                "tipo_calcolo": "FISSO",
                "valore": Decimal("150.00"),
                "natura": "IMPONIBILE",
            },
            {
                "codice": "EDR",
                "nome": "Elemento Distinto della Retribuzione",
                "tipo_calcolo": "FISSO",
                "valore": Decimal("10.33"),
                "natura": "IMPONIBILE",
            },
            {
                "codice": "IND_TURNO",
                "nome": "Indennità di turno",
                "tipo_calcolo": "PERCENTUALE_PAGA_BASE",
                "valore": Decimal("5.00"),
                "natura": "IMPONIBILE",
            },
        ]

        for elem_data in elementi_commercio:
            elem, created = ElementoRetributivo.objects.get_or_create(
                ccnl=ccnl_commercio,
                codice=elem_data["codice"],
                defaults={
                    "nome": elem_data["nome"],
                    "tipo_calcolo": elem_data["tipo_calcolo"],
                    "valore": elem_data["valore"],
                    "natura": elem_data["natura"],
                    "incluso_tfr": True,
                    "incluso_tredicesima": True,
                    "attivo": True,
                },
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f"  ✓ Elemento: {elem.nome}")
                )

        # 4. Crea CCNL Metalmeccanici
        ccnl_metal, created = CCNL.objects.get_or_create(
            nome="CCNL Metalmeccanici Industria",
            defaults={
                "tipo": "METALMECCANICI",
                "data_inizio_validita": date(2024, 1, 1),
                "giorni_ferie_annui": 26,
                "ore_rol_annue": Decimal("104.00"),
                "ore_permessi_retribuiti_annui": Decimal("32.00"),
                "percentuale_straordinario_feriale": Decimal("25.00"),
                "percentuale_straordinario_festivo": Decimal("40.00"),
                "percentuale_straordinario_notturno": Decimal("60.00"),
                "ha_tredicesima": True,
                "ha_quattordicesima": False,
                "ha_scatti_anzianita": True,
                "anni_per_scatto": 3,
                "importo_scatto": Decimal("30.00"),
                "numero_massimo_scatti": 8,
            },
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f"✓ Creato {ccnl_metal.nome}"))

        # 5. Crea Livelli per CCNL Metalmeccanici
        livelli_metal = [
            {
                "codice": "B1",
                "descrizione": "Operaio generico",
                "paga_base_mensile": Decimal("1600.00"),
            },
            {
                "codice": "B2",
                "descrizione": "Operaio qualificato",
                "paga_base_mensile": Decimal("1800.00"),
            },
            {
                "codice": "C1",
                "descrizione": "Operaio specializzato",
                "paga_base_mensile": Decimal("2000.00"),
            },
            {
                "codice": "D1",
                "descrizione": "Tecnico",
                "paga_base_mensile": Decimal("2200.00"),
            },
            {
                "codice": "D2",
                "descrizione": "Quadro",
                "paga_base_mensile": Decimal("2500.00"),
            },
        ]

        for liv_data in livelli_metal:
            liv, created = LivelloInquadramento.objects.get_or_create(
                ccnl=ccnl_metal,
                codice=liv_data["codice"],
                defaults={
                    "descrizione": liv_data["descrizione"],
                    "paga_base_mensile": liv_data["paga_base_mensile"],
                    "ore_settimanali_standard": Decimal("40.00"),
                },
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"  ✓ Livello {liv.codice}: {liv.descrizione}"
                    )
                )

        # 6. Crea Elementi Retributivi per CCNL Metalmeccanici
        elementi_metal = [
            {
                "codice": "CONT",
                "nome": "Contingenza",
                "tipo_calcolo": "FISSO",
                "valore": Decimal("180.00"),
                "natura": "IMPONIBILE",
            },
            {
                "codice": "EDR",
                "nome": "Elemento Distinto della Retribuzione",
                "tipo_calcolo": "FISSO",
                "valore": Decimal("10.33"),
                "natura": "IMPONIBILE",
            },
            {
                "codice": "IND_REPERIBILITA",
                "nome": "Indennità reperibilità",
                "tipo_calcolo": "FISSO",
                "valore": Decimal("100.00"),
                "natura": "IMPONIBILE",
            },
        ]

        for elem_data in elementi_metal:
            elem, created = ElementoRetributivo.objects.get_or_create(
                ccnl=ccnl_metal,
                codice=elem_data["codice"],
                defaults={
                    "nome": elem_data["nome"],
                    "tipo_calcolo": elem_data["tipo_calcolo"],
                    "valore": elem_data["valore"],
                    "natura": elem_data["natura"],
                    "incluso_tfr": True,
                    "incluso_tredicesima": True,
                    "attivo": True,
                },
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f"  ✓ Elemento: {elem.nome}")
                )

        self.stdout.write(
            self.style.SUCCESS(
                "\n✅ Setup payroll completato con successo!"
            )
        )
        self.stdout.write(
            self.style.WARNING(
                "\n⚠️  Prossimi passi:"
            )
        )
        self.stdout.write(
            "   1. Accedi all'admin Django"
        )
        self.stdout.write(
            "   2. Vai su 'Dati Contrattuali Payroll' per assegnare CCNL e livello ai dipendenti"
        )
        self.stdout.write(
            "   3. Usa il PayrollCalculator per elaborare le buste paga"
        )
