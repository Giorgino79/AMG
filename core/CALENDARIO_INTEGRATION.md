# Integrazione Calendario Aziendale

Guida per integrare eventi delle tue app nel calendario aziendale centralizzato.

## Panoramica

Il sistema di calendario utilizza un **Registry Pattern** che permette a ogni app di registrare "event providers" - funzioni che generano eventi per il calendario con controllo permessi automatico.

## Come Integrare la Tua App

### 1. Crea il file `calendario_providers.py` nella tua app

```python
# mia_app/calendario_providers.py

def get_miei_eventi(user, start_date, end_date):
    """
    Provider function per generare eventi.

    Args:
        user: Django User object
        start_date: datetime object (opzionale, può essere None)
        end_date: datetime object (opzionale, può essere None)

    Returns:
        Lista di dict in formato FullCalendar
    """
    # Controlla permesso (opzionale ma consigliato)
    if not user.has_perm('mia_app.view_mioelemento'):
        return []

    from .models import MioModello

    # Query del tuo modello
    queryset = MioModello.objects.all()

    # Filtra per date se fornite
    if start_date and end_date:
        queryset = queryset.filter(
            data_evento__gte=start_date.date(),
            data_evento__lte=end_date.date()
        )

    # Genera eventi in formato FullCalendar
    events = []
    for item in queryset[:100]:  # Limita per performance
        events.append({
            'id': f'mio-evento-{item.id}',
            'title': f'Mio Evento: {item.nome}',
            'start': item.data_inizio.isoformat(),
            'end': item.data_fine.isoformat() if item.data_fine else None,
            'color': '#007bff',  # Colore Bootstrap
            'url': f'/mia-app/eventi/{item.id}/',  # Link di dettaglio
            'extendedProps': {
                'tipo': 'mio_tipo',
                'descrizione': item.descrizione[:100] if item.descrizione else '',
                # Altri dati custom...
            }
        })

    return events
```

### 2. Registra i provider in `apps.py`

```python
# mia_app/apps.py

from django.apps import AppConfig

class MiaAppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "mia_app"
    verbose_name = "Mia Applicazione"

    def ready(self):
        """Registra event providers nel CalendarioRegistry"""
        try:
            from core.calendario_registry import CalendarioRegistry
            from .calendario_providers import get_miei_eventi

            CalendarioRegistry.register(
                name='miei_eventi',
                provider_func=get_miei_eventi,
                permission='mia_app.view_mioelemento',  # Opzionale
                category='Mia Categoria',
                description='Descrizione dei miei eventi',
                color='#007bff',  # Colore di default (opzionale)
                priority=60  # Priorità rendering (opzionale, default 50)
            )

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Errore registrazione CalendarioRegistry: {e}")
```

## Formato Eventi FullCalendar

Gli eventi devono seguire il formato FullCalendar:

```python
{
    'id': 'unique-id',              # ID univoco (string)
    'title': 'Titolo Evento',       # Titolo visualizzato (required)
    'start': '2024-01-15',          # Data/ora inizio ISO format (required)
    'end': '2024-01-16',            # Data/ora fine ISO format (opzionale)
    'color': '#007bff',             # Colore background (opzionale)
    'url': '/path/to/detail/',      # URL di dettaglio (opzionale)
    'extendedProps': {              # Proprietà custom (opzionale)
        'tipo': 'categoria',
        'descrizione': 'Descrizione',
        # Altri dati...
    }
}
```

## Controllo Permessi

Il sistema supporta due livelli di controllo permessi:

### 1. Permesso a livello di registrazione

```python
CalendarioRegistry.register(
    name='miei_eventi',
    provider_func=get_miei_eventi,
    permission='mia_app.view_mioelemento',  # Permesso Django
    ...
)
```

Se l'utente non ha questo permesso, il provider **non viene chiamato**.

### 2. Permesso a livello di provider function

```python
def get_miei_eventi(user, start_date, end_date):
    # Controllo permesso granulare
    if not user.has_perm('mia_app.view_mioelemento'):
        return []

    # Oppure filtra in base all'utente
    if user.groups.filter(name='Operatori').exists():
        queryset = queryset.filter(assegnato_a=user)

    ...
```

## Categorie

Le categorie permettono di raggruppare eventi simili. Esempi:

- `Automezzi` - Eventi veicoli
- `Progetti` - Eventi progetti
- `HR` - Eventi risorse umane
- `Scadenze` - Scadenze e deadline
- `Manutenzioni` - Manutenzioni varie

Gli utenti possono filtrare il calendario per categoria.

## Colori Consigliati (Bootstrap)

```python
'#007bff'  # Primary (blu)
'#28a745'  # Success (verde)
'#dc3545'  # Danger (rosso)
'#ffc107'  # Warning (giallo)
'#17a2b8'  # Info (ciano)
'#6c757d'  # Secondary (grigio)
```

## Best Practices

### Performance

- **Limita i risultati**: Usa `.queryset[:100]` per evitare query pesanti
- **Usa select_related**: Ottimizza query con relazioni FK
- **Filtra per date**: Usa sempre i parametri `start_date` e `end_date`

```python
queryset = queryset.select_related('utente', 'reparto')[:100]
```

### Sicurezza

- **Controlla sempre i permessi**: Non esporre dati sensibili
- **Valida input utente**: Le date vengono già validate dal sistema
- **Try/Except**: Il registry cattura eccezioni, ma usa try/except per gestirle meglio

### UX

- **Titoli chiari**: Es. "Manutenzione: Fiat Panda AA123BB"
- **Colori significativi**: Rosso = urgente, Verde = completato, ecc.
- **URL di dettaglio**: Sempre fornire un link cliccabile
- **ExtendedProps**: Aggiungi info utili per tooltip/filtri

## Esempio Completo: Eventi Progetti

```python
# progetti_eventi/calendario_providers.py

def get_progetti_eventi(user, start_date, end_date):
    """Provider per eventi progetto"""

    # Controllo permesso
    if not user.has_perm('progetti_eventi.view_evento'):
        return []

    from .models import Evento
    from django.db.models import Q

    # Query con filtri
    eventi_qs = Evento.objects.select_related('progetto', 'responsabile')

    if start_date and end_date:
        eventi_qs = eventi_qs.filter(
            Q(data_inizio__gte=start_date.date(), data_inizio__lte=end_date.date()) |
            Q(data_fine__gte=start_date.date(), data_fine__lte=end_date.date())
        )

    # Se utente è operatore, mostra solo i suoi
    if not user.is_staff:
        eventi_qs = eventi_qs.filter(responsabile=user)

    eventi_qs = eventi_qs[:100]

    # Genera eventi
    events = []
    for evento in eventi_qs:
        # Colore in base allo stato
        color_map = {
            'pianificato': '#6c757d',
            'in_corso': '#007bff',
            'completato': '#28a745',
            'cancellato': '#dc3545'
        }
        color = color_map.get(evento.stato, '#6c757d')

        events.append({
            'id': f'progetto-evento-{evento.id}',
            'title': f'{evento.progetto.nome}: {evento.titolo}',
            'start': evento.data_inizio.isoformat(),
            'end': evento.data_fine.isoformat() if evento.data_fine else None,
            'color': color,
            'url': f'/progetti/eventi/{evento.id}/',
            'extendedProps': {
                'tipo': 'progetto_evento',
                'stato': evento.get_stato_display(),
                'progetto': evento.progetto.nome,
                'responsabile': evento.responsabile.get_full_name(),
                'descrizione': evento.descrizione[:100] if evento.descrizione else '',
            }
        })

    return events


# progetti_eventi/apps.py

def ready(self):
    try:
        from core.calendario_registry import CalendarioRegistry
        from .calendario_providers import get_progetti_eventi

        CalendarioRegistry.register(
            name='eventi_progetti',
            provider_func=get_progetti_eventi,
            permission='progetti_eventi.view_evento',
            category='Progetti',
            description='Eventi e milestone progetti',
            color='#007bff',
            priority=25
        )

    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Errore registrazione CalendarioRegistry: {e}")
```

## Testing

Per testare i tuoi provider:

```python
# In Django shell
from core.calendario_registry import CalendarioRegistry
from django.contrib.auth import get_user_model
from datetime import datetime, timedelta

User = get_user_model()
user = User.objects.first()

start = datetime.now()
end = datetime.now() + timedelta(days=30)

# Ottieni eventi
events = CalendarioRegistry.get_events_for_user(user, start, end)

# Verifica
print(f"Trovati {len(events)} eventi")
for event in events[:5]:
    print(f"- {event['title']}")
```

## Troubleshooting

### Gli eventi non appaiono

1. Verifica che il provider sia registrato: `CalendarioRegistry._providers`
2. Controlla i permessi: `user.has_perm('app.view_model')`
3. Verifica che ci siano dati nel range di date
4. Controlla i log Django per errori

### Errori di import

- Assicurati che `core` sia in `INSTALLED_APPS`
- Usa import relativi nel provider: `from .models import`
- Registra nel metodo `ready()` dell'AppConfig

### Performance lente

- Limita il queryset: `[:100]`
- Usa `select_related()` per FK
- Aggiungi indici DB sulle date
- Valuta caching per dati statici

## Riferimenti

- **FullCalendar Docs**: https://fullcalendar.io/docs
- **Django Permissions**: https://docs.djangoproject.com/en/stable/topics/auth/
- **Registry Pattern**: Design pattern per estensibilità modulare
