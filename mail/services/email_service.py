"""
Email Service - ModularBEF

Service per invio email con supporto SMTP custom e template.

TODO: Implementare completamente le funzionalità di invio email.
"""

import logging
import re
from django.core.mail import EmailMessage as DjangoEmailMessage, EmailMultiAlternatives
from django.conf import settings
from django.utils import timezone
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

logger = logging.getLogger(__name__)


class ManagementEmailService:
    """
    Servizio semplificato per l'invio email usando le impostazioni Django.

    Utilizzato principalmente dalle app acquisti e trasporti per
    inviare email ai fornitori/trasportatori.
    """

    def __init__(self, user=None):
        """
        Inizializza il servizio email.

        Args:
            user: Utente Django che sta inviando l'email (per tracking)
        """
        self.user = user
        self.from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@example.com')

    def send_email(self, to, subject, body_html=None, body_text=None,
                   attachments=None, cc=None, bcc=None, reply_to=None,
                   html_content=None, source_object=None, category=None, **kwargs):
        """
        Invia un'email con supporto HTML.

        Args:
            to: Destinatario (stringa o lista)
            subject: Oggetto dell'email
            body_html: Contenuto HTML dell'email
            html_content: Alias per body_html (per compatibilità)
            body_text: Contenuto testuale (opzionale, generato da HTML se mancante)
            attachments: Lista di allegati [(filename, content, mimetype), ...]
            cc: Destinatari in copia
            bcc: Destinatari in copia nascosta
            reply_to: Indirizzo per le risposte
            source_object: Oggetto sorgente (ignorato, per compatibilità)
            category: Categoria email (ignorato, per compatibilità)

        Returns:
            dict: {'success': True/False, 'error': messaggio errore se fallito}
        """
        # Supporta sia body_html che html_content
        if body_html is None and html_content is not None:
            body_html = html_content

        if not body_html:
            return {'success': False, 'error': 'Contenuto HTML mancante'}

        try:
            # Normalizza destinatari
            if isinstance(to, str):
                to_list = [to]
            else:
                to_list = list(to)

            # Genera testo plain da HTML se non fornito
            if not body_text:
                body_text = re.sub(r'<[^>]+>', '', body_html)
                body_text = re.sub(r'\s+', ' ', body_text).strip()

            # Crea email
            email = EmailMultiAlternatives(
                subject=subject,
                body=body_text,
                from_email=self.from_email,
                to=to_list,
                cc=cc or [],
                bcc=bcc or [],
                reply_to=[reply_to] if reply_to else []
            )

            # Aggiungi versione HTML
            email.attach_alternative(body_html, "text/html")

            # Aggiungi allegati
            if attachments:
                for attachment in attachments:
                    if len(attachment) == 3:
                        filename, content, mimetype = attachment
                        email.attach(filename, content, mimetype)
                    elif len(attachment) == 2:
                        filename, content = attachment
                        email.attach(filename, content)

            # Invia
            email.send(fail_silently=False)

            logger.info(f"Email inviata con successo a {', '.join(to_list)} - Oggetto: {subject}")

            return {'success': True}

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Errore invio email a {to}: {error_msg}")
            return {'success': False, 'error': error_msg}


class EmailService:
    """
    Service per gestione invio email.

    Supporta:
    - Invio tramite configurazione utente (SMTP custom)
    - Invio tramite Django settings (fallback)
    - Template con variabili
    - Allegati
    - Stats tracking
    """

    def __init__(self, user=None, config=None):
        """
        Inizializza service.

        Args:
            user: User object (opzionale)
            config: EmailConfiguration object (opzionale)
        """
        self.user = user
        self.config = config

        if not self.config and self.user:
            try:
                from ..models import EmailConfiguration
                self.config = EmailConfiguration.objects.get(user=self.user)
            except EmailConfiguration.DoesNotExist:
                self.config = None

    def send_email(
        self,
        to_addresses,
        subject,
        content_html='',
        content_text='',
        cc_addresses=None,
        bcc_addresses=None,
        attachments=None,
        template=None,
        context=None
    ):
        """
        Invia email.

        Args:
            to_addresses: Lista destinatari
            subject: Oggetto
            content_html: Contenuto HTML
            content_text: Contenuto testo
            cc_addresses: Lista CC (opzionale)
            bcc_addresses: Lista BCC (opzionale)
            attachments: Lista file allegati (opzionale)
            template: EmailTemplate object (opzionale)
            context: Dict variabili per template (opzionale)

        Returns:
            EmailMessage: Oggetto messaggio creato

        TODO: Implementare logica completa di invio
        """
        from ..models import EmailMessage

        # Se template fornito, renderizza
        if template and context:
            subject, content_html, content_text = template.render(context)
            template.increment_usage()

        # Crea messaggio nel database
        message = EmailMessage.objects.create(
            sender_config=self.config,
            from_address=self.config.email_address if self.config else settings.DEFAULT_FROM_EMAIL,
            from_name=self.config.display_name if self.config else '',
            to_addresses=to_addresses if isinstance(to_addresses, list) else [to_addresses],
            cc_addresses=cc_addresses or [],
            bcc_addresses=bcc_addresses or [],
            subject=subject,
            content_html=content_html,
            content_text=content_text,
            template_used=template,
            direction='outgoing',
            status='pending',
            created_by=self.user,
        )

        try:
            # Invio reale via SMTP
            self._send_smtp(
                to_addresses=message.to_addresses,
                cc_addresses=message.cc_addresses,
                bcc_addresses=message.bcc_addresses,
                subject=message.subject,
                content_html=content_html,
                content_text=content_text,
                attachments=attachments
            )

            message.mark_as_sent()

        except Exception as e:
            message.mark_as_failed(str(e))
            raise

        return message

    def _send_smtp(self, to_addresses, subject, content_text='', content_html='',
                   cc_addresses=None, bcc_addresses=None, attachments=None):
        """
        Invia email tramite SMTP usando la configurazione dell'utente.

        Args:
            to_addresses: Lista indirizzi destinatari
            subject: Oggetto email
            content_text: Contenuto testo semplice
            content_html: Contenuto HTML (opzionale)
            cc_addresses: Lista CC (opzionale)
            bcc_addresses: Lista BCC (opzionale)
            attachments: Lista allegati (opzionale)
        """
        if not self.config:
            raise ValueError("Configurazione email non disponibile")

        # Crea messaggio
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"{self.config.display_name} <{self.config.email_address}>"
        msg['To'] = ', '.join(to_addresses) if isinstance(to_addresses, list) else to_addresses

        # Aggiungi header Reply-To per evitare problemi
        msg['Reply-To'] = self.config.email_address

        # Aggiungi Date header
        from email.utils import formatdate
        msg['Date'] = formatdate(localtime=True)

        # Aggiungi Message-ID per tracking
        from email.utils import make_msgid
        msg['Message-ID'] = make_msgid(domain=self.config.email_address.split('@')[1])

        if cc_addresses:
            msg['Cc'] = ', '.join(cc_addresses) if isinstance(cc_addresses, list) else cc_addresses

        # Aggiungi contenuto testo
        if content_text:
            part_text = MIMEText(content_text, 'plain', 'utf-8')
            msg.attach(part_text)

        # Aggiungi contenuto HTML
        if content_html:
            part_html = MIMEText(content_html, 'html', 'utf-8')
            msg.attach(part_html)

        # TODO: Gestire allegati se necessario
        # if attachments:
        #     for attachment in attachments:
        #         # Implementare logica allegati
        #         pass

        # Prepara lista completa destinatari (to + cc + bcc)
        all_recipients = []
        if isinstance(to_addresses, list):
            all_recipients.extend(to_addresses)
        else:
            all_recipients.append(to_addresses)

        if cc_addresses:
            if isinstance(cc_addresses, list):
                all_recipients.extend(cc_addresses)
            else:
                all_recipients.append(cc_addresses)

        if bcc_addresses:
            if isinstance(bcc_addresses, list):
                all_recipients.extend(bcc_addresses)
            else:
                all_recipients.append(bcc_addresses)

        # Connetti e invia
        try:
            if self.config.use_ssl:
                # SSL connection
                server = smtplib.SMTP_SSL(
                    self.config.smtp_server,
                    self.config.smtp_port,
                    timeout=30
                )
            else:
                # Normal connection with optional TLS
                server = smtplib.SMTP(
                    self.config.smtp_server,
                    self.config.smtp_port,
                    timeout=30
                )
                if self.config.use_tls:
                    server.starttls()

            # Login
            server.login(self.config.smtp_username, self.config.smtp_password)

            # Invia
            server.send_message(msg)

            # Chiudi connessione
            server.quit()

        except smtplib.SMTPException as e:
            raise Exception(f"Errore SMTP: {str(e)}")
        except Exception as e:
            raise Exception(f"Errore invio email: {str(e)}")

    def send_template_email(self, to_addresses, template_slug, context):
        """
        Invia email usando template.

        Args:
            to_addresses: Lista destinatari
            template_slug: Slug del template
            context: Dict variabili

        Returns:
            EmailMessage: Messaggio inviato
        """
        from ..models import EmailTemplate

        template = EmailTemplate.objects.get(slug=template_slug, is_active=True)
        return self.send_email(
            to_addresses=to_addresses,
            subject='',  # Verrà sovrascritto dal template
            template=template,
            context=context
        )

    def test_configuration(self):
        """
        Testa configurazione SMTP con connessione reale.

        Returns:
            bool: True se test riuscito, False altrimenti
        """
        if not self.config:
            self.config.last_error = "Nessuna configurazione disponibile"
            self.config.save()
            return False

        if not self.config.is_configured:
            self.config.last_error = "Configurazione incompleta"
            self.config.save()
            return False

        try:
            # Test connessione SMTP reale
            if self.config.use_ssl:
                server = smtplib.SMTP_SSL(
                    self.config.smtp_server,
                    self.config.smtp_port,
                    timeout=10
                )
            else:
                server = smtplib.SMTP(
                    self.config.smtp_server,
                    self.config.smtp_port,
                    timeout=10
                )
                if self.config.use_tls:
                    server.starttls()

            # Tenta il login
            server.login(self.config.smtp_username, self.config.smtp_password)

            # Se arriviamo qui, il test è riuscito
            server.quit()

            # Aggiorna configurazione
            self.config.is_verified = True
            self.config.last_test_at = timezone.now()
            self.config.last_error = ''
            self.config.save()

            return True

        except smtplib.SMTPAuthenticationError as e:
            error_msg = f"Autenticazione fallita: {str(e)}"
            self.config.is_verified = False
            self.config.last_error = error_msg
            self.config.save()
            return False

        except smtplib.SMTPException as e:
            error_msg = f"Errore SMTP: {str(e)}"
            self.config.is_verified = False
            self.config.last_error = error_msg
            self.config.save()
            return False

        except Exception as e:
            error_msg = f"Errore: {str(e)}"
            self.config.is_verified = False
            self.config.last_error = error_msg
            self.config.save()
            return False

    def get_user_stats(self, days=30):
        """
        Ottieni statistiche invio email utente.

        Args:
            days: Giorni di storico (default 30)

        Returns:
            dict: Statistiche aggregate

        TODO: Implementare query statistiche
        """
        from ..models import EmailStats
        from datetime import timedelta

        if not self.config:
            return {}

        start_date = timezone.now().date() - timedelta(days=days)

        stats = EmailStats.objects.filter(
            config=self.config,
            date__gte=start_date
        ).aggregate(
            total_sent=models.Sum('emails_sent'),
            total_failed=models.Sum('emails_failed'),
            total_bounced=models.Sum('emails_bounced'),
        )

        return stats
