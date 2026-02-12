from django.apps import AppConfig


class MailConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "mail"
    verbose_name = "Sistema Email & Comunicazioni"

    # Premium Module Configuration
    premium = True
    requires_license = True
    category = "comunicazione"
    description = "Sistema completo per gestione email, promemoria e chat interna"
    version = "1.0.0"

    def ready(self):
        """Initialize app signals and services"""
        # Import signals if needed
        pass
