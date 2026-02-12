from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core"
    verbose_name = "Core - Sistema Base"

    def ready(self):
        """
        Inizializzazione app al caricamento Django.

        Registra i modelli user-facing nel ModelPermissionRegistry.
        """
        # Import qui per evitare problemi di import circolari
        from .permissions_registry import register_default_models

        # Registra modelli di default
        register_default_models()
