from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "users"
    verbose_name = "Users - Gestione Utenti"

    def ready(self):
        """
        Codice eseguito quando l'app è pronta.

        Registra model User nel SearchRegistry per ricerca globale.
        """
        from core.search import SearchRegistry
        from .models import User

        # Registra User nel sistema ricerca globale
        SearchRegistry.register(
            model=User, category="Users", icon="bi-person-circle", priority=10
        )
