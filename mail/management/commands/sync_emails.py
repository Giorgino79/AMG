"""
Management command per sincronizzare email tramite IMAP.

Uso:
    python manage.py sync_emails                    # Sincronizza tutte le configurazioni attive
    python manage.py sync_emails --user=username    # Sincronizza solo un utente specifico
    python manage.py sync_emails --limit=50         # Limita numero email da scaricare
"""

import imaplib
import email
from email.header import decode_header
from email.utils import parsedate_to_datetime
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.utils import timezone
from mail.models import EmailConfiguration, EmailMessage, EmailFolder

User = get_user_model()


class Command(BaseCommand):
    help = 'Sincronizza email tramite IMAP dalle configurazioni attive'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user',
            type=str,
            help='Username specifico da sincronizzare'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=100,
            help='Numero massimo email da scaricare per configurazione (default: 100)'
        )
        parser.add_argument(
            '--folder',
            type=str,
            default='INBOX',
            help='Cartella IMAP da sincronizzare (default: INBOX)'
        )

    def handle(self, *args, **options):
        username = options.get('user')
        limit = options.get('limit')
        imap_folder = options.get('folder')

        # Ottieni configurazioni da sincronizzare
        configs = EmailConfiguration.objects.filter(imap_enabled=True)

        if username:
            try:
                user = User.objects.get(username=username)
                configs = configs.filter(user=user)
            except User.DoesNotExist:
                raise CommandError(f'Utente "{username}" non trovato')

        if not configs.exists():
            self.stdout.write(self.style.WARNING('Nessuna configurazione IMAP attiva trovata'))
            return

        self.stdout.write(f'Trovate {configs.count()} configurazioni da sincronizzare\n')

        total_synced = 0
        total_errors = 0

        for config in configs:
            self.stdout.write(f'\n{"="*60}')
            self.stdout.write(f'Sincronizzazione: {config.user.username} ({config.email_address})')
            self.stdout.write(f'{"="*60}')

            try:
                synced = self.sync_config(config, limit, imap_folder)
                total_synced += synced
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Sincronizzate {synced} email per {config.email_address}')
                )
            except Exception as e:
                total_errors += 1
                config.last_imap_error = str(e)
                config.save(update_fields=['last_imap_error'])
                self.stdout.write(
                    self.style.ERROR(f'✗ Errore per {config.email_address}: {str(e)}')
                )

        # Riepilogo finale
        self.stdout.write(f'\n{"="*60}')
        self.stdout.write(self.style.SUCCESS(f'TOTALE: {total_synced} email sincronizzate'))
        if total_errors > 0:
            self.stdout.write(self.style.ERROR(f'Errori: {total_errors} configurazioni fallite'))
        self.stdout.write(f'{"="*60}\n')

    def sync_config(self, config, limit, imap_folder):
        """Sincronizza email per una configurazione specifica"""

        if not config.is_imap_configured:
            raise Exception("Configurazione IMAP incompleta")

        # Connetti a IMAP
        mail = self.connect_imap(config)

        try:
            # Seleziona cartella
            status, messages = mail.select(imap_folder)
            if status != 'OK':
                raise Exception(f"Impossibile selezionare cartella {imap_folder}")

            # Ottieni lista email
            status, message_nums = mail.search(None, 'ALL')
            if status != 'OK':
                raise Exception("Impossibile cercare email")

            message_ids = message_nums[0].split()

            # Limita numero email da scaricare (prendi le più recenti)
            if limit and len(message_ids) > limit:
                message_ids = message_ids[-limit:]

            synced_count = 0

            self.stdout.write(f'Trovate {len(message_ids)} email da processare...')

            # Ottieni o crea cartella Inbox
            inbox_folder, _ = EmailFolder.objects.get_or_create(
                config=config,
                name='Inbox',
                defaults={
                    'folder_type': 'inbox',
                }
            )

            for num in message_ids:
                try:
                    # Scarica email
                    status, msg_data = mail.fetch(num, '(RFC822)')
                    if status != 'OK':
                        continue

                    # Parsa email
                    raw_email = msg_data[0][1]
                    email_message = email.message_from_bytes(raw_email)

                    # Estrai Message-ID
                    message_id = email_message.get('Message-ID', '')

                    # Salta se già presente
                    if message_id and EmailMessage.objects.filter(
                        sender_config=config,
                        message_id=message_id
                    ).exists():
                        continue

                    # Estrai dati email
                    subject = self.decode_header_value(email_message.get('Subject', 'Nessun oggetto'))
                    from_header = self.decode_header_value(email_message.get('From', ''))
                    to_header = self.decode_header_value(email_message.get('To', ''))
                    cc_header = self.decode_header_value(email_message.get('Cc', ''))
                    date_header = email_message.get('Date')

                    # Parsa mittente
                    from_address, from_name = self.parse_email_address(from_header)

                    # Parsa destinatari
                    to_addresses = self.parse_email_list(to_header)
                    cc_addresses = self.parse_email_list(cc_header)

                    # Estrai contenuto
                    content_text, content_html = self.extract_content(email_message)

                    # Parsa data
                    try:
                        date_received = parsedate_to_datetime(date_header) if date_header else timezone.now()
                    except:
                        date_received = timezone.now()

                    # Crea EmailMessage
                    email_obj = EmailMessage.objects.create(
                        sender_config=config,
                        folder=inbox_folder,
                        message_id=message_id,
                        server_uid=num.decode() if isinstance(num, bytes) else str(num),
                        from_address=from_address,
                        from_name=from_name,
                        to_addresses=to_addresses,
                        cc_addresses=cc_addresses,
                        subject=subject,
                        content_text=content_text,
                        content_html=content_html,
                        direction='incoming',
                        status='received',
                        is_read=False,
                    )

                    synced_count += 1

                    if synced_count % 10 == 0:
                        self.stdout.write(f'  Processate {synced_count}/{len(message_ids)} email...')

                except Exception as e:
                    self.stdout.write(
                        self.style.WARNING(f'  Errore nel processare email #{num}: {str(e)}')
                    )
                    continue

            # Aggiorna timestamp sync
            config.last_imap_sync = timezone.now()
            config.last_imap_error = ''
            config.save(update_fields=['last_imap_sync', 'last_imap_error'])

            # Aggiorna contatori cartella
            inbox_folder.update_message_count()

            return synced_count

        finally:
            # Chiudi connessione
            try:
                mail.close()
                mail.logout()
            except:
                pass

    def connect_imap(self, config):
        """Connette al server IMAP"""
        try:
            if config.imap_use_ssl:
                mail = imaplib.IMAP4_SSL(
                    config.imap_server,
                    config.imap_port,
                    timeout=30
                )
            else:
                mail = imaplib.IMAP4(
                    config.imap_server,
                    config.imap_port,
                    timeout=30
                )
                if config.imap_use_tls:
                    mail.starttls()

            # Login
            mail.login(config.imap_username, config.imap_password)

            return mail

        except imaplib.IMAP4.error as e:
            raise Exception(f"Errore IMAP: {str(e)}")
        except Exception as e:
            raise Exception(f"Errore connessione IMAP: {str(e)}")

    def decode_header_value(self, header_value):
        """Decodifica header email"""
        if not header_value:
            return ''

        decoded_parts = decode_header(header_value)
        decoded_str = ''

        for part, encoding in decoded_parts:
            if isinstance(part, bytes):
                try:
                    decoded_str += part.decode(encoding or 'utf-8', errors='replace')
                except:
                    decoded_str += part.decode('utf-8', errors='replace')
            else:
                decoded_str += str(part)

        return decoded_str.strip()

    def parse_email_address(self, email_header):
        """Estrae email e nome da header tipo 'Nome <email@example.com>'"""
        if not email_header:
            return ('', '')

        # Prova a estrarre email tra <>
        if '<' in email_header and '>' in email_header:
            start = email_header.index('<')
            end = email_header.index('>')
            email_addr = email_header[start+1:end].strip()
            name = email_header[:start].strip().strip('"\'')
            return (email_addr, name)
        else:
            # Solo email senza nome
            return (email_header.strip(), '')

    def parse_email_list(self, email_header):
        """Parsa lista email separata da virgole"""
        if not email_header:
            return []

        emails = []
        for part in email_header.split(','):
            addr, _ = self.parse_email_address(part.strip())
            if addr:
                emails.append(addr)

        return emails

    def extract_content(self, email_message):
        """Estrae contenuto testo e HTML da email"""
        content_text = ''
        content_html = ''

        if email_message.is_multipart():
            for part in email_message.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get('Content-Disposition', ''))

                # Salta allegati
                if 'attachment' in content_disposition:
                    continue

                try:
                    payload = part.get_payload(decode=True)
                    if payload:
                        charset = part.get_content_charset() or 'utf-8'
                        decoded_payload = payload.decode(charset, errors='replace')

                        if content_type == 'text/plain' and not content_text:
                            content_text = decoded_payload
                        elif content_type == 'text/html' and not content_html:
                            content_html = decoded_payload
                except:
                    continue
        else:
            # Email non multipart
            try:
                payload = email_message.get_payload(decode=True)
                if payload:
                    charset = email_message.get_content_charset() or 'utf-8'
                    content_text = payload.decode(charset, errors='replace')
            except:
                pass

        return (content_text, content_html)
