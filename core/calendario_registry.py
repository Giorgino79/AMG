"""
Sistema di registrazione per eventi del calendario aziendale.

Permette alle app di registrare event providers che generano eventi
per il calendario con controllo permessi integrato.

Esempio d'uso in automezzi/apps.py:

    from core.calendario_registry import CalendarioRegistry

    def get_eventi_automezzi(user, start_date, end_date):
        if not user.has_perm('automezzi.view_eventoautomezzo'):
            return []

        eventi = EventoAutomezzo.objects.filter(
            data_evento__gte=start_date,
            data_evento__lte=end_date
        )

        return [{
            'id': f'evento-{e.id}',
            'title': f'{e.get_tipo_display()}: {e.automezzo}',
            'start': e.data_evento.isoformat(),
            'color': '#dc3545',
            'url': f'/automezzi/eventi/{e.id}/',
        } for e in eventi]

    CalendarioRegistry.register(
        name='eventi_automezzi',
        provider_func=get_eventi_automezzi,
        permission='automezzi.view_eventoautomezzo',
        category='Automezzi',
        description='Eventi veicoli (incidenti, guasti, ecc.)'
    )
"""

from typing import Callable, Optional, Dict, List, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class CalendarioRegistry:
    """
    Registry per event providers del calendario aziendale.

    Ogni provider è una funzione che genera eventi per il calendario
    e può specificare permessi richiesti per la visualizzazione.
    """

    _providers: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def register(
        cls,
        name: str,
        provider_func: Callable,
        permission: Optional[str] = None,
        category: str = 'Altri',
        description: str = '',
        color: Optional[str] = None,
        priority: int = 50
    ):
        """
        Registra un event provider per il calendario.

        Args:
            name: Nome univoco del provider (es. 'eventi_automezzi')
            provider_func: Funzione che genera eventi. Deve accettare (user, start_date, end_date)
                          e restituire lista di dict compatibili con FullCalendar
            permission: Permesso Django richiesto (es. 'automezzi.view_eventoautomezzo')
                       Se None, visibile a tutti gli utenti autenticati
            category: Categoria per organizzare i provider (es. 'Automezzi', 'Progetti')
            description: Descrizione del tipo di eventi forniti
            color: Colore di default per gli eventi (se non specificato dal provider)
            priority: Priorità di rendering (più basso = prima). Default 50

        Example:
            def get_manutenzioni(user, start, end):
                if not user.has_perm('automezzi.view_manutenzione'):
                    return []
                return [...]

            CalendarioRegistry.register(
                name='manutenzioni',
                provider_func=get_manutenzioni,
                permission='automezzi.view_manutenzione',
                category='Automezzi'
            )
        """
        if name in cls._providers:
            logger.warning(f"Provider '{name}' già registrato. Verrà sovrascritto.")

        cls._providers[name] = {
            'name': name,
            'func': provider_func,
            'permission': permission,
            'category': category,
            'description': description,
            'color': color,
            'priority': priority
        }

        logger.info(f"Provider calendario '{name}' registrato (categoria: {category})")

    @classmethod
    def unregister(cls, name: str):
        """Rimuove un provider dal registry"""
        if name in cls._providers:
            del cls._providers[name]
            logger.info(f"Provider calendario '{name}' rimosso")

    @classmethod
    def get_events_for_user(
        cls,
        user,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        categories: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Recupera tutti gli eventi per un utente, controllando i permessi.

        Args:
            user: Utente Django
            start_date: Data inizio filtro (opzionale)
            end_date: Data fine filtro (opzionale)
            categories: Lista di categorie da includere (se None, include tutte)

        Returns:
            Lista di eventi in formato FullCalendar
        """
        if not user or not user.is_authenticated:
            return []

        all_events = []

        # Ordina provider per priorità
        sorted_providers = sorted(
            cls._providers.values(),
            key=lambda p: p['priority']
        )

        for provider in sorted_providers:
            # Filtra per categoria se specificato
            if categories and provider['category'] not in categories:
                continue

            # Controlla permesso
            permission = provider['permission']
            if permission and not user.has_perm(permission):
                logger.debug(
                    f"User {user.username} non ha permesso {permission} "
                    f"per provider '{provider['name']}'"
                )
                continue

            # Chiama provider function
            try:
                events = provider['func'](user, start_date, end_date)

                # Aggiungi colore di default se non specificato
                if provider['color']:
                    for event in events:
                        if 'color' not in event:
                            event['color'] = provider['color']

                # Aggiungi metadati provider
                for event in events:
                    event.setdefault('extendedProps', {})
                    event['extendedProps']['provider'] = provider['name']
                    event['extendedProps']['category'] = provider['category']

                all_events.extend(events)

                logger.debug(
                    f"Provider '{provider['name']}' ha generato {len(events)} eventi"
                )

            except Exception as e:
                logger.error(
                    f"Errore nel provider '{provider['name']}': {e}",
                    exc_info=True
                )
                # Non interrompere per errori di singoli provider
                continue

        return all_events

    @classmethod
    def get_categories(cls) -> List[str]:
        """Restituisce lista di tutte le categorie registrate"""
        return sorted(set(p['category'] for p in cls._providers.values()))

    @classmethod
    def get_providers_info(cls, user=None) -> List[Dict[str, Any]]:
        """
        Restituisce informazioni su tutti i provider.
        Se user è specificato, include solo provider accessibili.
        """
        providers_info = []

        for provider in cls._providers.values():
            # Se user specificato, controlla permesso
            if user:
                permission = provider['permission']
                if permission and not user.has_perm(permission):
                    continue

            providers_info.append({
                'name': provider['name'],
                'category': provider['category'],
                'description': provider['description'],
                'permission': provider['permission'],
                'color': provider['color']
            })

        return providers_info

    @classmethod
    def clear(cls):
        """Pulisce tutti i provider (utile per testing)"""
        cls._providers.clear()
