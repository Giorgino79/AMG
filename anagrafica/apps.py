from django.apps import AppConfig


class AnagraficaConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "anagrafica"
    verbose_name = "Anagrafica"

    def ready(self):
        """
        Registra i modelli nel SearchRegistry quando l'app è pronta.
        """
        try:
            from core.search import SearchRegistry
            from .models import Cliente, Fornitore

            # Registra Cliente per ricerca globale
            SearchRegistry.register(
                model=Cliente,
                category='Anagrafica',
                icon='bi-person-badge',
                priority=10
            )

            # Registra Fornitore per ricerca globale
            SearchRegistry.register(
                model=Fornitore,
                category='Anagrafica',
                icon='bi-building',
                priority=10
            )

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Errore registrazione SearchRegistry per anagrafica: {e}")
