from django.apps import AppConfig


class AcquistiConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "acquisti"
    verbose_name = "Acquisti"

    def ready(self):
        """
        Registra i modelli nel SearchRegistry quando l'app è pronta.
        """
        try:
            from core.search import SearchRegistry
            from .models import OrdineAcquisto

            # Registra OrdineAcquisto per ricerca globale
            SearchRegistry.register(
                model=OrdineAcquisto,
                category='Acquisti',
                icon='bi-cart-check',
                priority=8
            )

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Errore registrazione SearchRegistry per acquisti: {e}")
