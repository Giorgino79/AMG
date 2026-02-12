from django.apps import AppConfig


class StabilimentiConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "stabilimenti"
    verbose_name = "Gestione Stabilimenti"

    def ready(self):
        """
        Registra i modelli nel SearchRegistry quando l'app è pronta.
        """
        try:
            from core.search import SearchRegistry
            from .models import Stabilimento, CostiStabilimento, DocStabilimento

            # Registra Stabilimento per ricerca globale
            SearchRegistry.register(
                model=Stabilimento,
                category='Stabilimenti',
                icon='bi-building',
                priority=10
            )

            # Registra CostiStabilimento per ricerca globale
            SearchRegistry.register(
                model=CostiStabilimento,
                category='Stabilimenti',
                icon='bi-cash-stack',
                priority=8
            )

            # Registra DocStabilimento per ricerca globale
            SearchRegistry.register(
                model=DocStabilimento,
                category='Stabilimenti',
                icon='bi-file-earmark-text',
                priority=6
            )

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Errore registrazione SearchRegistry per stabilimenti: {e}")
