"""
Registry per gestione permissions sui modelli user-facing.

Questo modulo definisce quali modelli sono gestibili dagli admin
tramite il form di assegnazione permessi agli utenti.

IMPORTANTE:
- Solo i modelli registrati qui appariranno nel form permissions
- I modelli "di servizio" (Allegato, ModuloRegistry, etc.) NON vanno registrati
- Ogni nuovo modello user-facing VA REGISTRATO manualmente
"""

from django.apps import apps
from django.contrib.contenttypes.models import ContentType


class ModelPermissionRegistry:
    """
    Registry centralizzato per modelli gestibili con permissions.

    Pattern Singleton per garantire un unico registro globale.
    """

    _instance = None
    _registry = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._registry = {}
        return cls._instance

    def register(self, app_label, model_name, display_name=None, category=None, icon=None):
        """
        Registra un modello come gestibile con permissions.

        Args:
            app_label (str): Nome app Django (es. "users", "payroll")
            model_name (str): Nome modello lowercase (es. "user", "bustapaga")
            display_name (str): Nome visualizzato (es. "Utenti", "Buste Paga")
            category (str): Categoria per raggruppamento (es. "Gestione Personale")
            icon (str): Icona Bootstrap (es. "bi-people", "bi-cash-coin")

        Example:
            registry = ModelPermissionRegistry()
            registry.register(
                app_label="users",
                model_name="user",
                display_name="Utenti",
                category="Gestione Personale",
                icon="bi-people"
            )
        """
        key = f"{app_label}.{model_name}"

        # Verifica che il modello esista
        try:
            model_class = apps.get_model(app_label, model_name)
        except LookupError:
            raise ValueError(
                f"Modello {key} non trovato. Verifica app_label e model_name."
            )

        self._registry[key] = {
            "app_label": app_label,
            "model_name": model_name,
            "model_class": model_class,
            "display_name": display_name or model_class._meta.verbose_name_plural.title(),
            "category": category or app_label.title(),
            "icon": icon or "bi-file-earmark",
            "permissions": self._get_model_permissions(model_class),
        }

    def _get_model_permissions(self, model_class):
        """
        Ottiene i permessi Django standard per un modello.

        Returns:
            list: Lista di dict con codename, name, label
        """
        # Usa _meta invece di ContentType per evitare query al database
        app_label = model_class._meta.app_label
        model_name = model_class._meta.model_name
        permissions = []

        # Permessi CRUD standard Django
        for action, label in [
            ("add", "Creare"),
            ("view", "Visualizzare"),
            ("change", "Modificare"),
            ("delete", "Eliminare"),
        ]:
            codename = f"{action}_{model_name}"
            perm_name = f"{app_label}.{codename}"

            permissions.append(
                {
                    "codename": codename,
                    "full_name": perm_name,
                    "action": action,
                    "label": label,
                }
            )

        return permissions

    def get_registered_models(self):
        """
        Restituisce tutti i modelli registrati.

        Returns:
            dict: Dizionario {key: model_info}
        """
        return self._registry.copy()

    def get_models_by_category(self):
        """
        Restituisce modelli raggruppati per categoria.

        Returns:
            dict: {category: [model_info, ...]}
        """
        categorized = {}

        for model_info in self._registry.values():
            category = model_info["category"]
            if category not in categorized:
                categorized[category] = []
            categorized[category].append(model_info)

        return categorized

    def is_registered(self, app_label, model_name):
        """Verifica se un modello è registrato"""
        key = f"{app_label}.{model_name}"
        return key in self._registry

    def get_model_info(self, app_label, model_name):
        """Ottiene informazioni su un modello registrato"""
        key = f"{app_label}.{model_name}"
        return self._registry.get(key)

    def unregister(self, app_label, model_name):
        """Rimuove un modello dal registro (usare con cautela!)"""
        key = f"{app_label}.{model_name}"
        if key in self._registry:
            del self._registry[key]


# ============================================================================
# REGISTRAZIONE MODELLI USER-FACING
# ============================================================================

def register_default_models():
    """
    Registra i modelli user-facing di default.

    IMPORTANTE: Quando aggiungi un nuovo modello all'applicazione,
    se vuoi che sia gestibile tramite permissions, DEVI registrarlo qui!

    MODELLI DA NON REGISTRARE (esempi):
    - Allegato (modello di servizio generico)
    - ModuloRegistry (configurazione sistema)
    - VoceBustaPaga (dettaglio interno, gestito da BustaPaga)
    - ContentType, Permission (Django internals)
    """
    registry = ModelPermissionRegistry()

    # ========== APP: USERS ==========
    registry.register(
        app_label="users",
        model_name="user",
        display_name="Utenti / Dipendenti",
        category="👥 Gestione Personale",
        icon="bi-people-fill",
    )

    registry.register(
        app_label="users",
        model_name="richiestaferie",
        display_name="Richieste Ferie",
        category="👥 Gestione Personale",
        icon="bi-calendar-check",
    )

    registry.register(
        app_label="users",
        model_name="richiestapermesso",
        display_name="Richieste Permessi",
        category="👥 Gestione Personale",
        icon="bi-clock-history",
    )

    registry.register(
        app_label="users",
        model_name="letterarichiamo",
        display_name="Lettere di Richiamo",
        category="👥 Gestione Personale",
        icon="bi-exclamation-triangle-fill",
    )

    registry.register(
        app_label="users",
        model_name="giornatalavorativa",
        display_name="Giornate Lavorative",
        category="⏰ Presenze",
        icon="bi-calendar3",
    )

    registry.register(
        app_label="users",
        model_name="timbratura",
        display_name="Timbrature",
        category="⏰ Presenze",
        icon="bi-stopwatch",
    )

    # ========== APP: PAYROLL ==========
    registry.register(
        app_label="payroll",
        model_name="ccnl",
        display_name="CCNL",
        category="💰 Amministrazione Payroll",
        icon="bi-file-earmark-text",
    )

    registry.register(
        app_label="payroll",
        model_name="livelloinquadramento",
        display_name="Livelli Inquadramento",
        category="💰 Amministrazione Payroll",
        icon="bi-bar-chart-steps",
    )

    registry.register(
        app_label="payroll",
        model_name="elementoretributivo",
        display_name="Elementi Retributivi",
        category="💰 Amministrazione Payroll",
        icon="bi-currency-euro",
    )

    registry.register(
        app_label="payroll",
        model_name="daticontrattualiPayroll",
        display_name="Contratti Payroll",
        category="💰 Amministrazione Payroll",
        icon="bi-file-earmark-person",
    )

    registry.register(
        app_label="payroll",
        model_name="bustapaga",
        display_name="Buste Paga",
        category="💼 Elaborazione Paghe",
        icon="bi-receipt",
    )

    registry.register(
        app_label="payroll",
        model_name="feriepermessiPayroll",
        display_name="Ferie/Permessi Payroll",
        category="💼 Elaborazione Paghe",
        icon="bi-calendar-range",
    )

    registry.register(
        app_label="payroll",
        model_name="manualepayroll",
        display_name="Manuale Payroll",
        category="📚 Documentazione",
        icon="bi-book",
    )

    # ========== APP: MAIL (PREMIUM) ==========
    registry.register(
        app_label="mail",
        model_name="emailconfiguration",
        display_name="Configurazioni Email",
        category="📧 Sistema Email & Comunicazioni",
        icon="bi-gear-fill",
    )

    registry.register(
        app_label="mail",
        model_name="emailtemplate",
        display_name="Template Email",
        category="📧 Sistema Email & Comunicazioni",
        icon="bi-file-text",
    )

    registry.register(
        app_label="mail",
        model_name="emailfolder",
        display_name="Cartelle Email",
        category="📧 Sistema Email & Comunicazioni",
        icon="bi-folder",
    )

    registry.register(
        app_label="mail",
        model_name="emaillabel",
        display_name="Etichette Email",
        category="📧 Sistema Email & Comunicazioni",
        icon="bi-tag",
    )

    registry.register(
        app_label="mail",
        model_name="emailmessage",
        display_name="Messaggi Email",
        category="📧 Sistema Email & Comunicazioni",
        icon="bi-envelope",
    )

    registry.register(
        app_label="mail",
        model_name="promemoria",
        display_name="Promemoria",
        category="🔔 Promemoria & Notifiche",
        icon="bi-bell-fill",
    )

    registry.register(
        app_label="mail",
        model_name="chatconversation",
        display_name="Conversazioni Chat",
        category="💬 Chat Interna",
        icon="bi-chat-dots-fill",
    )

    registry.register(
        app_label="mail",
        model_name="chatmessage",
        display_name="Messaggi Chat",
        category="💬 Chat Interna",
        icon="bi-chat-left-text",
    )

    # ========== ISTRUZIONI PER NUOVI MODELLI ==========
    """
    COME AGGIUNGERE UN NUOVO MODELLO:

    1. Aggiungi la registrazione qui sopra seguendo questo pattern:

       registry.register(
           app_label="nome_app",           # es. "vendite"
           model_name="nomemodello",       # es. "fattura" (lowercase!)
           display_name="Nome Visualizzato", # es. "Fatture"
           category="🏷️ Categoria",        # es. "💼 Vendite"
           icon="bi-icon-name",            # es. "bi-receipt-cutoff"
       )

    2. VERIFICA che il modello abbia i permessi Django standard:
       - add_<model>
       - view_<model>
       - change_<model>
       - delete_<model>

    3. Se il modello ha permessi custom (definiti in Meta.permissions),
       DEVONO essere gestiti separatamente (non in questo form).

    4. MODELLI DA NON REGISTRARE:
       - Modelli di servizio/utility (Allegato, Log, etc.)
       - Modelli di dettaglio gestiti dal parent (VoceBustaPaga, etc.)
       - Modelli Django interni (ContentType, Permission, Session, etc.)
       - Modelli di configurazione sistema (ModuloRegistry, etc.)

    5. Dopo aver registrato, riavviare il server Django per applicare.
    """


# NOTA: register_default_models() viene chiamato in core/apps.py
# nel metodo ready() per evitare query al database durante l'import


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================


def get_user_model_permissions(user):
    """
    Ottiene i permessi dell'utente sui modelli registrati.

    Args:
        user: Istanza User

    Returns:
        dict: {
            'app_label.model_name': {
                'can_add': bool,
                'can_view': bool,
                'can_change': bool,
                'can_delete': bool,
            }
        }
    """
    registry = ModelPermissionRegistry()
    user_perms = {}

    for key, model_info in registry.get_registered_models().items():
        model_class = model_info["model_class"]

        user_perms[key] = {
            "can_add": user.has_perm(f"{model_info['app_label']}.add_{model_info['model_name']}"),
            "can_view": user.has_perm(f"{model_info['app_label']}.view_{model_info['model_name']}"),
            "can_change": user.has_perm(f"{model_info['app_label']}.change_{model_info['model_name']}"),
            "can_delete": user.has_perm(f"{model_info['app_label']}.delete_{model_info['model_name']}"),
        }

    return user_perms


def get_registry():
    """Helper per ottenere l'istanza del registry"""
    return ModelPermissionRegistry()
