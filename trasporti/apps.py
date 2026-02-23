from django.apps import AppConfig


class TrasportiConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "trasporti"
    verbose_name = "Trasporti"

    def ready(self):
        """
        Registra i modelli nel SearchRegistry quando l'app è pronta.
        """
        try:
            from core.search import SearchRegistry
            from .models import RichiestaTrasporto

            # Registra RichiestaTrasporto per ricerca globale
            SearchRegistry.register(
                model=RichiestaTrasporto,
                category='Trasporti',
                icon='bi-truck',
                priority=8
            )

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Errore registrazione SearchRegistry per trasporti: {e}")
