from django.apps import AppConfig


class AutomezziConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "automezzi"
    verbose_name = "Gestione Automezzi"

    def ready(self):
        """
        Registra i modelli nel SearchRegistry e CalendarioRegistry quando l'app è pronta.
        """
        # Import signals
        import automezzi.signals

        # ===== SEARCH REGISTRY =====
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

        # ===== CALENDARIO REGISTRY =====
        try:
            from core.calendario_registry import CalendarioRegistry
            from .calendario_providers import (
                get_eventi_automezzi,
                get_manutenzioni,
                get_affidamenti,
                get_scadenze_revisioni,
                get_scadenze_assicurazioni
            )

            # Registra provider eventi automezzi
            CalendarioRegistry.register(
                name='eventi_automezzi',
                provider_func=get_eventi_automezzi,
                permission='automezzi.view_eventoautomezzo',
                category='Automezzi',
                description='Eventi veicoli (incidenti, guasti, ecc.)',
                priority=10
            )

            # Registra provider manutenzioni
            CalendarioRegistry.register(
                name='manutenzioni',
                provider_func=get_manutenzioni,
                permission='automezzi.view_manutenzione',
                category='Automezzi',
                description='Manutenzioni programmate e in corso',
                priority=20
            )

            # Registra provider affidamenti
            CalendarioRegistry.register(
                name='affidamenti',
                provider_func=get_affidamenti,
                permission='automezzi.view_affidamentomezzo',
                category='Automezzi',
                description='Affidamenti mezzi a utenti',
                priority=30
            )

            # Registra provider scadenze revisioni
            CalendarioRegistry.register(
                name='scadenze_revisioni',
                provider_func=get_scadenze_revisioni,
                permission='automezzi.view_automezzo',
                category='Scadenze',
                description='Scadenze revisioni veicoli',
                priority=40
            )

            # Registra provider scadenze assicurazioni
            CalendarioRegistry.register(
                name='scadenze_assicurazioni',
                provider_func=get_scadenze_assicurazioni,
                permission='automezzi.view_automezzo',
                category='Scadenze',
                description='Scadenze assicurazioni veicoli',
                priority=50
            )

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Errore registrazione CalendarioRegistry per automezzi: {e}")
