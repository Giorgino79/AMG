from django.apps import AppConfig


class PayrollConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "payroll"
    verbose_name = "Payroll"

    def ready(self):
        """
        Registra i modelli nel SearchRegistry quando l'app è pronta.
        """
        try:
            from core.search import SearchRegistry
            from .models import BustaPaga

            # Registra BustaPaga per ricerca globale
            SearchRegistry.register(
                model=BustaPaga,
                category='Payroll',
                icon='bi-receipt',
                priority=8
            )

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Errore registrazione SearchRegistry per payroll: {e}")
