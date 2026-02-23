"""
Management command per testare il calcolo delle buste paga
"""

from django.core.management.base import BaseCommand
from decimal import Decimal
from payroll.services import PayrollCalculator
from payroll.models import DatiContrattualiPayroll, CCNL, LivelloInquadramento
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = "Testa il calcolo delle buste paga con dati di esempio"

    def add_arguments(self, parser):
        parser.add_argument(
            "--user",
            type=str,
            help="Username del dipendente (default: admin)",
            default="admin",
        )
        parser.add_argument(
            "--mese", type=int, help="Mese (1-12, default: 1)", default=1
        )
        parser.add_argument("--anno", type=int, help="Anno (default: 2025)", default=2025)

    def handle(self, *args, **options):
        username = options["user"]
        mese = options["mese"]
        anno = options["anno"]

        self.stdout.write(
            self.style.SUCCESS(f"\n🧮 Test calcolo busta paga per {username}")
        )
        self.stdout.write(self.style.SUCCESS(f"   Periodo: {mese:02d}/{anno}\n"))

        # 1. Recupera l'utente
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f"❌ Utente '{username}' non trovato!")
            )
            self.stdout.write(
                "   Utenti disponibili: "
                + ", ".join(User.objects.values_list("username", flat=True))
            )
            return

        # 2. Verifica/Crea dati payroll
        try:
            dati_payroll = user.dati_payroll
            self.stdout.write(
                self.style.SUCCESS(
                    f"✓ Dati payroll esistenti per {user.get_full_name()}"
                )
            )
        except DatiContrattualiPayroll.DoesNotExist:
            self.stdout.write(
                self.style.WARNING(
                    f"⚠️  Dati payroll non configurati per {user.get_full_name()}"
                )
            )
            self.stdout.write("   Creo dati di esempio...")

            # Prendi il primo CCNL e livello disponibili
            ccnl = CCNL.objects.filter(tipo="COMMERCIO").first()
            if not ccnl:
                ccnl = CCNL.objects.first()

            if not ccnl:
                self.stdout.write(
                    self.style.ERROR(
                        "❌ Nessun CCNL trovato! Esegui prima: python manage.py setup_payroll_demo"
                    )
                )
                return

            livello = LivelloInquadramento.objects.filter(ccnl=ccnl, codice="3").first()
            if not livello:
                livello = LivelloInquadramento.objects.filter(ccnl=ccnl).first()

            dati_payroll = DatiContrattualiPayroll.objects.create(
                user=user,
                ccnl=ccnl,
                livello=livello,
                tipo_contratto="TEMPO_INDETERMINATO",
                ore_settimanali=Decimal("40.00"),
                percentuale_part_time=Decimal("100.00"),
                superminimo=Decimal("100.00"),
                aliquota_addizionale_regionale=Decimal("1.23"),
                aliquota_addizionale_comunale=Decimal("0.80"),
                detrazione_lavoro_dipendente=True,
                numero_figli_a_carico=0,
                coniuge_a_carico=False,
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f"✓ Dati payroll creati: {ccnl.nome} - Livello {livello.codice}"
                )
            )

        # 3. Mostra informazioni dipendente
        self.stdout.write("\n📋 DATI DIPENDENTE:")
        self.stdout.write(f"   Nome: {user.get_full_name()}")
        self.stdout.write(f"   CCNL: {dati_payroll.ccnl.nome}")
        self.stdout.write(
            f"   Livello: {dati_payroll.livello.codice} - {dati_payroll.livello.descrizione}"
        )
        self.stdout.write(
            f"   Paga base: € {dati_payroll.livello.paga_base_mensile:,.2f}"
        )
        self.stdout.write(f"   Superminimo: € {dati_payroll.superminimo:,.2f}")
        paga_oraria = dati_payroll.calcola_paga_oraria()
        self.stdout.write(f"   Paga oraria: € {paga_oraria:,.2f}/h")

        # 4. Prepara dati per il calcolo
        ore_ordinarie = Decimal("176.00")  # ~22 giorni * 8h
        ore_straordinari = {
            "feriale": Decimal("8.00"),
            "festivo": Decimal("0.00"),
            "notturno": Decimal("4.00"),
        }
        assenze = {
            "ferie": Decimal("8.00"),
            "rol": Decimal("0.00"),
            "permessi": Decimal("0.00"),
            "malattia": Decimal("0.00"),
        }

        self.stdout.write("\n⏱️  ORE LAVORATE:")
        self.stdout.write(f"   Ordinarie: {ore_ordinarie}h")
        self.stdout.write(f"   Straordinari feriali: {ore_straordinari['feriale']}h")
        self.stdout.write(f"   Straordinari festivi: {ore_straordinari['festivo']}h")
        self.stdout.write(f"   Straordinari notturni: {ore_straordinari['notturno']}h")
        self.stdout.write(f"   Ferie godute: {assenze['ferie']}h")

        # 5. Calcola la busta paga
        self.stdout.write("\n💰 CALCOLO BUSTA PAGA...")
        try:
            calculator = PayrollCalculator(user, mese, anno)

            # Calcola busta
            busta = calculator.calcola_busta_paga(
                ore_ordinarie=ore_ordinarie,
                ore_straordinari=ore_straordinari,
                assenze=assenze,
            )

            # Matura ferie e permessi
            calculator.matura_ferie_permessi_mensili()

            self.stdout.write(self.style.SUCCESS("\n✅ BUSTA PAGA ELABORATA!\n"))

            # 6. Mostra risultati
            self.stdout.write("📊 RIEPILOGO BUSTA PAGA:")
            self.stdout.write(f"   Periodo: {busta.mese:02d}/{busta.anno}")
            self.stdout.write(
                f"   Ore totali: {busta.ore_ordinarie + busta.ore_straordinario_feriale + busta.ore_straordinario_festivo + busta.ore_straordinario_notturno:.2f}h"
            )
            self.stdout.write("")

            self.stdout.write("💵 COMPETENZE (Retribuzione Lorda):")
            for voce in busta.voci.filter(tipo="COMPETENZA"):
                if voce.quantita:
                    self.stdout.write(
                        f"   • {voce.descrizione}: {voce.quantita:.2f}h × € {voce.importo_unitario:,.2f} = € {voce.importo_totale:,.2f}"
                    )
                else:
                    self.stdout.write(
                        f"   • {voce.descrizione}: € {voce.importo_totale:,.2f}"
                    )

            self.stdout.write("")
            self.stdout.write(
                f"   Imponibile Fiscale: € {busta.imponibile_fiscale:,.2f}"
            )
            self.stdout.write(
                f"   Imponibile Contributivo: € {busta.imponibile_contributivo:,.2f}"
            )

            self.stdout.write("\n➖ TRATTENUTE:")
            for voce in busta.voci.filter(tipo="TRATTENUTA"):
                self.stdout.write(
                    f"   • {voce.descrizione}: € {voce.importo_totale:,.2f}"
                )

            self.stdout.write("\n➕ DETRAZIONI:")
            for voce in busta.voci.filter(tipo="DEDUZIONE"):
                self.stdout.write(
                    f"   • {voce.descrizione}: € {voce.importo_totale:,.2f}"
                )

            self.stdout.write("\n" + "=" * 50)
            self.stdout.write(
                self.style.SUCCESS(
                    f"   💰 NETTO IN BUSTA: € {busta.netto_busta:,.2f}"
                )
            )
            self.stdout.write("=" * 50)

            self.stdout.write(f"\n   📈 TFR Maturato: € {busta.tfr_maturato:,.2f}")

            # 7. Mostra ferie/permessi
            self.stdout.write("\n🏖️  FERIE E PERMESSI:")
            from payroll.models import FeriePermessiPayroll

            for fp in FeriePermessiPayroll.objects.filter(user=user, anno=anno):
                self.stdout.write(
                    f"   • {fp.get_tipo_display()}: {fp.ore_maturate:.2f}h maturate, "
                    f"{fp.ore_godute:.2f}h godute, {fp.ore_residue:.2f}h residue"
                )

            self.stdout.write(
                self.style.SUCCESS(
                    f"\n✅ Test completato! Busta paga ID: {busta.id}"
                )
            )
            self.stdout.write(
                f"   Visualizza in admin: /admin/payroll/bustapaga/{busta.id}/change/"
            )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\n❌ Errore nel calcolo: {e}"))
            import traceback

            traceback.print_exc()
