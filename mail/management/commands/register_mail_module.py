"""
Management command per registrare il modulo Mail nel ModuloRegistry.

Uso: python manage.py register_mail_module
"""

from django.core.management.base import BaseCommand
from core.models_legacy import ModuloRegistry


class Command(BaseCommand):
    help = "Registra il modulo Mail nel ModuloRegistry come modulo premium"

    def handle(self, *args, **options):
        """Crea o aggiorna il record ModuloRegistry per il modulo Mail"""

        mail_module, created = ModuloRegistry.objects.update_or_create(
            codice="mail",
            defaults={
                "nome": "Sistema Email & Comunicazioni",
                "app_name": "mail",
                "descrizione": (
                    "Sistema completo per gestione email (SMTP/IMAP), "
                    "promemoria con notifiche e chat interna tra utenti. "
                    "Include template riutilizzabili, cartelle e labels Gmail-style, "
                    "allegati, statistiche di invio e molto altro."
                ),
                "categoria": "comunicazione",
                "attivo": True,
                "obbligatorio": False,
                "versione": "1.0.0",
                "dipendenze": ["core", "users"],
                "icona": "bi-envelope-fill",
                "ordine": 30,
            },
        )

        if created:
            self.stdout.write(
                self.style.SUCCESS(
                    f"✓ Modulo Mail creato con successo (ID: {mail_module.id})"
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"✓ Modulo Mail aggiornato con successo (ID: {mail_module.id})"
                )
            )

        self.stdout.write(
            self.style.WARNING(
                "\nNota: Questo è un modulo PREMIUM che richiederà licenza attiva."
            )
        )
        self.stdout.write(
            "Funzionalità incluse:\n"
            "  • Configurazione SMTP/IMAP per invio e ricezione email\n"
            "  • Template riutilizzabili con variabili dinamiche\n"
            "  • Cartelle e labels Gmail-style\n"
            "  • Sistema promemoria con notifiche email\n"
            "  • Chat interna 1-to-1 e di gruppo\n"
            "  • Gestione allegati su tutti i modelli\n"
            "  • Statistiche di invio e logging completo\n"
        )
