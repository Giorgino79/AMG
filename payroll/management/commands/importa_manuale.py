"""
Command per importare il manuale Payroll dal file MD al database
"""

from django.core.management.base import BaseCommand
from payroll.models import ManualePayroll
import os


class Command(BaseCommand):
    help = "Importa il manuale Payroll dal file MANUALE_COMPILAZIONE_PAYROLL.md"

    def handle(self, *args, **options):
        # Path del file manuale
        base_dir = os.path.dirname(
            os.path.dirname(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            )
        )
        manuale_path = os.path.join(
            base_dir, "MANUALE_COMPILAZIONE_PAYROLL.md"
        )

        # Leggi il file
        if not os.path.exists(manuale_path):
            self.stdout.write(
                self.style.ERROR(
                    f"File non trovato: {manuale_path}"
                )
            )
            return

        with open(manuale_path, "r", encoding="utf-8") as f:
            contenuto = f.read()

        # Elimina vecchie versioni
        ManualePayroll.objects.all().delete()

        # Crea nuovo manuale
        manuale = ManualePayroll.objects.create(
            titolo="Manuale di Compilazione Form Payroll - ModularBEF",
            contenuto=contenuto,
            versione="1.0",
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"✅ Manuale importato con successo! ID: {manuale.id}"
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"📄 Caratteri: {len(contenuto):,}"
            )
        )
