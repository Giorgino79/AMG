"""
Management command per creare chat per progetti esistenti.

Uso:
    python manage.py create_project_chats
    python manage.py create_project_chats --update  (aggiorna anche esistenti)
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from progetti_eventi.models import Progetto
from mail.models import ChatConversation


class Command(BaseCommand):
    help = 'Crea chat di gruppo per tutti i progetti che non ne hanno una'

    def add_arguments(self, parser):
        parser.add_argument(
            '--update',
            action='store_true',
            help='Aggiorna anche le chat già esistenti con i partecipanti del progetto',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Mostra cosa farebbe senza effettivamente creare le chat',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        update_existing = options['update']

        # Conta progetti totali
        progetti_totali = Progetto.objects.filter(deleted_at__isnull=True).count()
        self.stdout.write(f"\n📊 Progetti totali: {progetti_totali}")

        # Trova progetti senza chat
        progetti_senza_chat = Progetto.objects.filter(
            chat_progetto__isnull=True,
            deleted_at__isnull=True
        ).select_related('commerciale', 'cliente')

        count_senza_chat = progetti_senza_chat.count()
        self.stdout.write(f"🔍 Progetti senza chat: {count_senza_chat}")

        if dry_run:
            self.stdout.write("\n🔎 DRY RUN - Nessuna modifica effettuata\n")
            for progetto in progetti_senza_chat[:10]:  # Mostra primi 10
                self.stdout.write(
                    f"  • {progetto.codice} - {progetto.nome_evento} "
                    f"(Commerciale: {progetto.commerciale.username})"
                )
            if count_senza_chat > 10:
                self.stdout.write(f"  ... e altri {count_senza_chat - 10}")
            return

        # Crea chat per progetti senza
        created_count = 0
        error_count = 0

        self.stdout.write("\n🚀 Creazione chat in corso...\n")

        for progetto in progetti_senza_chat:
            try:
                with transaction.atomic():
                    # Crea chat di gruppo
                    chat = ChatConversation.objects.create(
                        titolo=f"Chat: {progetto.codice} - {progetto.nome_evento}",
                        tipo='group',
                        created_by=progetto.commerciale
                    )

                    # Aggiungi commerciale come partecipante
                    chat.partecipanti.add(progetto.commerciale)

                    # Aggiungi altri partecipanti se già configurati
                    if progetto.partecipanti.exists():
                        chat.partecipanti.add(*progetto.partecipanti.all())

                    # Collega chat al progetto
                    progetto.chat_progetto = chat
                    progetto.save(update_fields=['chat_progetto'])

                    # Assicurati che il commerciale sia nei partecipanti del progetto
                    if not progetto.partecipanti.filter(id=progetto.commerciale.id).exists():
                        progetto.partecipanti.add(progetto.commerciale)

                    created_count += 1
                    partecipanti_count = chat.partecipanti.count()

                    self.stdout.write(
                        self.style.SUCCESS(
                            f"  ✓ {progetto.codice} - Chat creata "
                            f"({partecipanti_count} partecipanti)"
                        )
                    )

            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(
                        f"  ✗ {progetto.codice} - Errore: {str(e)}"
                    )
                )

        # Aggiorna chat esistenti se richiesto
        updated_count = 0
        if update_existing:
            self.stdout.write("\n🔄 Aggiornamento chat esistenti...\n")

            progetti_con_chat = Progetto.objects.filter(
                chat_progetto__isnull=False,
                deleted_at__isnull=True
            ).select_related('chat_progetto', 'commerciale')

            for progetto in progetti_con_chat:
                try:
                    chat = progetto.chat_progetto

                    # Assicurati che il commerciale sia presente
                    if not chat.partecipanti.filter(id=progetto.commerciale.id).exists():
                        chat.partecipanti.add(progetto.commerciale)

                    # Sincronizza partecipanti
                    if progetto.partecipanti.exists():
                        for partecipante in progetto.partecipanti.all():
                            if not chat.partecipanti.filter(id=partecipante.id).exists():
                                chat.partecipanti.add(partecipante)

                    updated_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"  ✓ {progetto.codice} - Chat aggiornata "
                            f"({chat.partecipanti.count()} partecipanti)"
                        )
                    )

                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(
                            f"  ✗ {progetto.codice} - Errore: {str(e)}"
                        )
                    )

        # Riepilogo finale
        self.stdout.write("\n" + "="*60)
        self.stdout.write(self.style.SUCCESS(f"\n✅ COMPLETATO!\n"))
        self.stdout.write(f"  • Chat create: {created_count}")
        if update_existing:
            self.stdout.write(f"  • Chat aggiornate: {updated_count}")
        if error_count > 0:
            self.stdout.write(self.style.WARNING(f"  • Errori: {error_count}"))

        # Verifica finale
        progetti_senza_chat_finale = Progetto.objects.filter(
            chat_progetto__isnull=True,
            deleted_at__isnull=True
        ).count()

        self.stdout.write(f"\n📈 Progetti ancora senza chat: {progetti_senza_chat_finale}")
        self.stdout.write("="*60 + "\n")
