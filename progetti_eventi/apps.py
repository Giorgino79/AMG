"""
Config app progetti_eventi.
"""

from django.apps import AppConfig


class ProgettiEventiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'progetti_eventi'
    verbose_name = 'Progetti Eventi'

    def ready(self):
        """
        Registra i model nel SearchRegistry per la ricerca globale.
        """
        from core.search import SearchRegistry
        from .models import Progetto, ProgettoReparto, ListaProdotti

        # Registra Progetto
        SearchRegistry.register(
            model=Progetto,
            category='Progetti Eventi',
            icon='bi-calendar-event',
            priority=7
        )

        # Registra ProgettoReparto
        SearchRegistry.register(
            model=ProgettoReparto,
            category='Progetti Eventi',
            icon='bi-diagram-3',
            priority=6
        )

        # Registra ListaProdotti
        SearchRegistry.register(
            model=ListaProdotti,
            category='Engineering',
            icon='bi-list-check',
            priority=5
        )
