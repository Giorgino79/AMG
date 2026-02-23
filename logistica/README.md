# App Logistica

Sistema di gestione logistica con calendario automatico per consegne e ritiri progetti eventi.

## Panoramica

L'app **logistica** riceve automaticamente i dati dai progetti creati dai commerciali e li visualizza in un calendario interattivo per facilitare la pianificazione delle consegne e ritiri.

### Workflow

```
COMMERCIALE                    LOGISTICA
    │                              │
    ├─> Crea Progetto             │
    │   - Nome evento             │
    │   - Cliente                 │
    │   - Location                │
    │   - Data consegna ──────────┼──> Calendario Consegne
    │   - Data ritiro ────────────┼──> Calendario Ritiri
    │   - Note logistica          │
    │                              │
    │                              ├─> Dashboard (prossimi 7 giorni)
    │                              ├─> Calendario Mensile
    │                              └─> Vista Giornaliera Dettagliata
```

## Caratteristiche Principali

### 1. Acquisizione Automatica Dati

L'app **non ha modelli propri** (per ora), ma legge direttamente dal modello `Progetto`:

```python
from progetti_eventi.models import Progetto

# Consegne del giorno
consegne = Progetto.objects.filter(
    data_consegna_richiesta=data_selezionata,
    deleted_at__isnull=True
)

# Ritiri del giorno
ritiri = Progetto.objects.filter(
    data_ritiro_richiesta=data_selezionata,
    deleted_at__isnull=True
)
```

### 2. Dashboard Logistica

**URL:** `/logistica/`

Mostra:
- **Statistiche oggi**: Conteggio consegne e ritiri
- **Prossime consegne** (7 giorni): Top 10 consegne imminenti
- **Prossimi ritiri** (7 giorni): Top 10 ritiri imminenti

Ogni card include:
- Codice progetto
- Nome evento
- Cliente
- Location
- Orario
- Reparti coinvolti

### 3. Calendario Mensile

**URL:** `/logistica/calendario/` o `/logistica/calendario/<anno>/<mese>/`

Caratteristiche:
- **Vista griglia** 7 giorni × N settimane
- **Navigazione**: Mese precedente/successivo
- **Evidenziazione oggi**: Sfondo giallo
- **Badge consegne**: Blu con icona ⬇️
- **Badge ritiri**: Verde con icona ⬆️
- **Contatori**: Se >2 eventi, mostra "+N"
- **Click su giorno**: Vai a vista giornaliera

Esempio giorno:
```
┌─────────────────┐
│       15        │  ← Numero giorno
├─────────────────┤
│ ⬇️ PRJ-2026-001 │  ← Consegna
│ ⬇️ PRJ-2026-003 │  ← Consegna
│ +2              │  ← Altre 2 consegne
│ ⬆️ PRJ-2026-002 │  ← Ritiro
└─────────────────┘
```

### 4. Vista Giorno

**URL:** `/logistica/giorno/<anno>/<mese>/<giorno>/`

Vista dettagliata con:
- **Navigazione**: Giorno precedente/successivo
- **Due colonne**:
  - Consegne programmate (sinistra, blu)
  - Ritiri programmati (destra, verde)

Per ogni progetto mostra:
- Codice e nome evento
- Orario esatto
- Cliente e commerciale
- Indirizzo completo destinazione
- Reparti coinvolti
- Note logistica (se presenti)
- Link al dettaglio progetto

## Struttura File

```
logistica/
├── __init__.py
├── apps.py                 # Configurazione app
├── views.py                # 3 views: Dashboard, CalendarioMese, CalendarioGiorno
├── urls.py                 # URL routing
├── README.md               # Questa documentazione
└── templates/
    └── logistica/
        ├── dashboard.html              # Dashboard principale
        ├── calendario_mese.html        # Calendario mensile
        └── calendario_giorno.html      # Dettaglio giornata
```

## Views

### DashboardLogisticaView

```python
class DashboardLogisticaView(TemplateView):
    """Dashboard con statistiche e prossimi eventi"""
    template_name = 'logistica/dashboard.html'
```

**Context data:**
- `consegne_oggi`: Count consegne di oggi
- `ritiri_oggi`: Count ritiri di oggi
- `prossime_consegne`: Queryset consegne prossimi 7 giorni
- `prossimi_ritiri`: Queryset ritiri prossimi 7 giorni

### CalendarioMeseView

```python
class CalendarioMeseView(TemplateView):
    """Calendario mensile con grid layout"""
    template_name = 'logistica/calendario_mese.html'
```

**Context data:**
- `anno`, `mese`, `nome_mese`: Info mese corrente
- `settimane`: Lista settimane, ogni settimana è lista 7 giorni
- `mese_prec`, `anno_prec`: Per navigazione
- `mese_succ`, `anno_succ`: Per navigazione

**Struttura giorno:**
```python
{
    'numero': 15,
    'data': date(2026, 2, 15),
    'consegne': [<Progetto>, <Progetto>],
    'ritiri': [<Progetto>],
    'is_oggi': True,
    'is_passato': False
}
```

### CalendarioGiornoView

```python
class CalendarioGiornoView(TemplateView):
    """Vista dettaglio singola giornata"""
    template_name = 'logistica/calendario_giorno.html'
```

**Context data:**
- `data_selezionata`: Data del giorno
- `consegne`: Queryset consegne del giorno
- `ritiri`: Queryset ritiri del giorno
- `giorno_prec`, `giorno_succ`: Per navigazione
- `is_oggi`: Boolean se è oggi

## URL Disponibili

| URL | Vista | Descrizione |
|-----|-------|-------------|
| `/logistica/` | Dashboard | Panoramica prossimi eventi |
| `/logistica/calendario/` | Calendario Mese | Mese corrente |
| `/logistica/calendario/2026/3/` | Calendario Mese | Marzo 2026 |
| `/logistica/giorno/` | Calendario Giorno | Oggi |
| `/logistica/giorno/2026/3/15/` | Calendario Giorno | 15 Marzo 2026 |

## Integrazione con Progetti Eventi

### Dati Utilizzati da Progetto

L'app legge questi campi dal modello `Progetto`:

```python
progetto.codice                      # PRJ-2026-0001
progetto.nome_evento                 # "Matrimonio Demo"
progetto.cliente.ragione_sociale     # "Demo SRL"
progetto.commerciale.get_full_name   # "Mario Rossi"
progetto.data_evento                 # Data evento
progetto.data_consegna_richiesta     # Data/ora consegna
progetto.data_ritiro_richiesta       # Data/ora ritiro
progetto.location                    # "Villa Demo"
progetto.indirizzo_location          # "Via Demo 1"
progetto.citta_location              # "Milano"
progetto.reparti_coinvolti           # ['audio', 'video', 'luci']
progetto.note_logistica              # Note specifiche
```

### Sincronizzazione Automatica

✅ **Automatica al 100%**

Quando un commerciale:
1. Crea un progetto → Appare immediatamente nel calendario
2. Modifica data consegna → Aggiornamento automatico calendario
3. Modifica data ritiro → Aggiornamento automatico calendario
4. Elimina progetto (soft delete) → Scompare dal calendario

Non serve **nessuna azione manuale** da parte della logistica!

## Sidebar

Il link è stato aggiunto nella sidebar sotto la sezione **PROGETTI**:

```html
<a href="{% url 'logistica:dashboard' %}" class="nav-link">
    <i class="bi bi-truck"></i>
    <span>Logistica</span>
</a>
```

## Design Calendario

### Colori

- **Consegne**: Blu (`#1976d2`)
  - Background card: `#e3f2fd`
  - Icona: `bi-box-arrow-down`

- **Ritiri**: Verde (`#388e3c`)
  - Background card: `#e8f5e9`
  - Icona: `bi-box-arrow-up`

- **Oggi**: Giallo (`#ffc107`)
  - Background cella: `#fff3cd`
  - Border: `2px solid #ffc107`

- **Giorni passati**: Opacità 60%

### Responsive

- Desktop: Griglia 7 colonne
- Tablet: Griglia fluida
- Mobile: Scroll orizzontale

### Interattività

- **Hover su giorno**: Zoom leggero + shadow
- **Click su giorno**: Navigazione a vista dettagliata
- **Scroll automatico**: Al caricamento, scroll su giorno corrente

## Sviluppi Futuri

Questa è la **versione base** senza modelli propri. Prossimi step:

### Fase 2: Modelli Logistica (prossima implementazione)

```python
class ConsegnaProgetto(BaseModel):
    """Dettaglio consegna con automezzo e tecnici"""
    progetto_reparto = FK('progetti_eventi.ProgettoReparto')
    automezzo = FK('automezzi.Automezzo')
    autista = FK('users.User')
    stato = CharField()  # pianificata, in_corso, completata
    ora_partenza_effettiva = DateTimeField()
    ora_arrivo_effettiva = DateTimeField()
    km_percorsi = DecimalField()

class RitiroProgetto(BaseModel):
    """Dettaglio ritiro"""
    progetto_reparto = FK('progetti_eventi.ProgettoReparto')
    automezzo = FK('automezzi.Automezzo')
    # ...
```

### Fase 3: Funzionalità Avanzate

- [ ] Assegnazione automezzi
- [ ] Assegnazione autisti
- [ ] Tracking GPS in tempo reale
- [ ] Calcolo percorsi ottimizzati
- [ ] Gestione colli e materiali
- [ ] Firma digitale consegna/ritiro
- [ ] Report giornalieri/mensili
- [ ] Export PDF packing list
- [ ] Integrazione app mobile autisti
- [ ] Notifiche push ritardi

### Fase 4: Ottimizzazione Percorsi

- [ ] Algoritmo ottimizzazione multi-consegna
- [ ] Calcolo costi carburante
- [ ] Gestione ZTL e permessi
- [ ] Integrazione Google Maps API
- [ ] Calcolo emissioni CO2

## Note Tecniche

### Performance

Le query sono ottimizzate con:
- `select_related()` per cliente e commerciale
- `prefetch_related()` per reparti
- Filtro `deleted_at__isnull=True` per soft delete
- Index su date per query veloci

### Sicurezza

- `@login_required` su tutte le views
- Filtro automatico deleted
- Nessuna modifica dati (solo lettura per ora)

### Scalabilità

L'architettura supporta migliaia di progetti:
- Query filtrate per range date (non carica tutto)
- Paginazione pronta per implementazione
- Cache-ready (da abilitare in produzione)

## Testing

```bash
# Verifica calendario mese corrente
curl http://127.0.0.1:8000/logistica/calendario/

# Verifica giorno specifico
curl http://127.0.0.1:8000/logistica/giorno/2026/2/21/
```

## Supporto

Per domande o segnalazioni: aprire issue nel repository.

---

**Versione:** 1.0 (Base - Solo lettura)
**Data:** Febbraio 2026
**Autore:** Claude Code + Giorgio
