from django.apps import AppConfig


class AutomezziConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "automezzi"
    verbose_name = "Gestione Automezzi"

    def ready(self):
        """
        Registra i modelli nel SearchRegistry quando l'app è pronta.
        """
        try:
            from core.search import SearchRegistry
            from .models import Automezzo

            # Registra Automezzo per ricerca globale
            SearchRegistry.register(
                model=Automezzo,
                category='Automezzi',
                icon='bi-car-front',
                priority=10
            )

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Errore registrazione SearchRegistry per automezzi: {e}")
