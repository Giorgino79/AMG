"""
Celery tasks for Mail App - ModularBEF

Tasks asincroni per sincronizzazione email e altre operazioni.
"""

from celery import shared_task
from django.utils import timezone
import imaplib
import email
from email.header import decode_header
from email.utils import parsedate_to_datetime

from .models import EmailConfiguration, EmailMessage, EmailFolder


@shared_task
def sync_all_emails():
    """
    Task Celery per sincronizzare email da tutti gli account IMAP configurati.

    Viene eseguito periodicamente (default: ogni 3 minuti).
    Sincronizza sia INBOX che cartella Sent per vedere email inviate a se stessi.
    """
    from mail.management.commands.sync_emails import Command

    # Usa il comando esistente
    command = Command()

    # Ottieni configurazioni da sincronizzare
    configs = EmailConfiguration.objects.filter(imap_enabled=True)

    total_synced = 0
    total_errors = 0

    for config in configs:
        try:
            # Sincronizza INBOX
            synced_inbox = command.sync_config(config, limit=100, imap_folder='INBOX')
            total_synced += synced_inbox

            # Sincronizza anche Sent per vedere email inviate a se stessi
            try:
                synced_sent = command.sync_config(config, limit=50, imap_folder='[Gmail]/Sent Mail')
                total_synced += synced_sent
            except:
                # Se [Gmail]/Sent Mail non esiste, prova con Sent
                try:
                    synced_sent = command.sync_config(config, limit=50, imap_folder='Sent')
                    total_synced += synced_sent
                except:
                    pass  # Ignora errori sulla cartella Sent

        except Exception as e:
            total_errors += 1
            config.last_imap_error = str(e)
            config.save(update_fields=['last_imap_error'])

    return {
        'synced': total_synced,
        'errors': total_errors,
        'configs': configs.count()
    }


@shared_task
def sync_user_emails(user_id):
    """
    Task Celery per sincronizzare email di un singolo utente.

    Args:
        user_id: ID dell'utente
    """
    from django.contrib.auth import get_user_model
    from mail.management.commands.sync_emails import Command

    User = get_user_model()
    command = Command()

    try:
        user = User.objects.get(id=user_id)
        config = EmailConfiguration.objects.get(user=user, imap_enabled=True)

        synced = command.sync_config(config, limit=100, imap_folder='INBOX')

        return {
            'success': True,
            'synced': synced,
            'user': user.username
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }
