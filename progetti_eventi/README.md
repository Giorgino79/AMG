# App Progetti Eventi

Sistema di gestione progetti eventi con coordinamento cross-reparto (Audio/Video/Luci).

## Panoramica

Questa app è l'**orchestratore centrale** che permette al commerciale di creare progetti eventi e coordinare automaticamente tutti i reparti aziendali coinvolti.

### Workflow Generale

```
COMMERCIALE                ENGINEERING           ALTRE APP (future)
    │                          │                        │
    ├─> Crea Progetto         │                        │
    ├─> Seleziona Reparti     │                        │
    │   (Audio/Video/Luci)    │                        │
    │                          │                        │
    ├────────────────────────> │                        │
    │   Invia a Engineering    │                        │
    │                          │                        │
    │                          ├─> Studia Progetto     │
    │                          ├─> Crea Liste Prodotti │
    │                          ├─> Approva Liste       │
    │                          │                        │
    │                          ├──────────────────────> │
    │                          │   Genera Task          │
    │                          │   - Magazzino          │
    │                          │   - Logistica          │
    │                          │   - Travel             │
    │                          │   - Scouting           │
    │                          │                        │
    │ <───────────────────────────────────────────────── │
    │   Notifiche Completamento                         │
```

## Modelli Principali

### 1. Progetto
Entità principale creata dal commerciale.

**Campi chiave:**
- `codice` - Autogenerato (PRJ-2026-0001)
- `cliente` - FK a anagrafica.Cliente
- `nome_evento`, `tipo_evento`, `data_evento`
- `location` - Dove si svolge l'evento
- `commerciale` - FK a users.User
- `reparti_coinvolti` - Lista reparti selezionati
- `stato` - Workflow (bozza → in_engineering → completato)

### 2. ProgettoReparto
**CHIAVE ARCHITETTURALE**: Istanza separata per ogni reparto (Audio/Video/Luci).

**Perché separato?**
- Ogni reparto ha il proprio ingegnere
- Ogni reparto ha le proprie liste prodotti
- Ogni reparto genera task separati per magazzino/logistica/travel/scouting

**Campi di integrazione (flag booleani):**
```python
engineering_completato = False  # True quando ingegnere completa studio
magazzino_ready = False         # True quando app magazzino finisce approntamento
logistica_ready = False         # True quando app logistica pianifica consegne
travel_ready = False            # True quando app travel organizza viaggi
scouting_ready = False          # True quando app scouting trova personale
```

### 3. ListaProdotti
Output dell'engineering. Una volta approvata, viene usata dalle app downstream.

**Workflow approvazione:**
```python
lista.stato = 'bozza'           # Creata da ingegnere
lista.stato = 'in_revisione'    # Inviata per revisione
lista.approva(user)             # Approvata → magazzino può usarla
```

### 4. ProdottoLista
Singolo prodotto nella lista con:
- Codice, nome, categoria
- Quantità
- Dimensioni (L x W x H) e peso
- Calcolo automatico volume (m³)

## Integrazione con Altre App

### Schema Collegamento

```python
# App MAGAZZINO (quando sarà creata)
class RichiestaApprontamento(BaseModel):
    progetto_reparto = models.ForeignKey(
        'progetti_eventi.ProgettoReparto',
        on_delete=models.CASCADE,
        related_name='richieste_approntamento'
    )
    lista_prodotti = models.ForeignKey('progetti_eventi.ListaProdotti', ...)
    stato = models.CharField(...)

    def completa(self):
        # Quando completato, aggiorna flag
        self.progetto_reparto.magazzino_ready = True
        self.progetto_reparto.save()

# App LOGISTICA
class ConsegnaEvento(BaseModel):
    progetto_reparto = models.ForeignKey('progetti_eventi.ProgettoReparto', ...)
    data_consegna = models.DateTimeField(...)
    automezzo = models.ForeignKey('automezzi.Automezzo', ...)

    def completa_consegna(self):
        self.progetto_reparto.logistica_ready = True
        self.progetto_reparto.save()

# App TRAVEL
class MissioneTecnico(BaseModel):
    progetto_reparto = models.ForeignKey('progetti_eventi.ProgettoReparto', ...)
    tecnico = models.ForeignKey('users.User', ...)
    # ... dettagli viaggio

# App SCOUTING
class RichiestaPersonale(BaseModel):
    progetto_reparto = models.ForeignKey('progetti_eventi.ProgettoReparto', ...)
    numero_tecnici = models.PositiveIntegerField(...)
    numero_facchini = models.PositiveIntegerField(...)
```

## View Principali

### Dashboard Commerciale
**URL:** `/progetti/`

Mostra:
- Statistiche progetti per stato
- Progetti urgenti (< 7 giorni)
- Prossimi eventi (30 giorni)
- Engineering in corso

### Lista Progetti
**URL:** `/progetti/progetti/`

Filtri:
- Stato progetto
- Reparto coinvolto
- Range date
- Commerciale
- Solo urgenti

### Vista Master Progetto
**URL:** `/progetti/progetti/<uuid>/`

**CUORE DELL'APP**: Vista unificata con TAB per ogni reparto.

Struttura:
```
┌─────────────────────────────────────────┐
│ Header: Info Evento + Stato + Timeline  │
├─────────────────────────────────────────┤
│ TAB: Audio | Video | Luci               │
├─────────────────────────────────────────┤
│ Per ogni TAB:                           │
│ ┌────────────────────────────────────┐  │
│ │ 5 CARD:                            │  │
│ │ [Engineering][Magazzino]           │  │
│ │ [Logistica][Travel][Scouting]      │  │
│ └────────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

Ogni card mostra:
- Stato attuale (badge colorato)
- Info principali
- Link all'app specifica (quando pronta)
- Placeholder dati

## Template Creati

```
templates/progetti_eventi/
├── dashboard_commerciale.html       # Dashboard
├── progetto_list.html              # Lista con filtri
├── progetto_form.html              # Create/Update (multi-tab)
├── progetto_detail.html            # VISTA MASTER (con TAB reparti)
├── progetto_confirm_delete.html    # Conferma eliminazione
├── reparto_detail.html             # Dettaglio singolo reparto
├── lista_prodotti_form.html        # Form liste prodotti (con formset dinamico)
├── lista_prodotti_detail.html      # Dettaglio lista + approvazione
└── components/
    └── reparto_tab_content.html    # Contenuto TAB (5 card)
```

## Installazione

### 1. Aggiungi app a settings.py

```python
INSTALLED_APPS = [
    # ... app esistenti ...
    'anagrafica',
    'users',
    'core',
    'progetti_eventi',  # ← AGGIUNGI QUESTA
]
```

### 2. Aggiungi URL

```python
# mod2/urls.py
urlpatterns = [
    # ...
    path('progetti/', include('progetti_eventi.urls')),
]
```

### 3. Crea migrations

```bash
python manage.py makemigrations progetti_eventi
python manage.py migrate progetti_eventi
```

### 4. (Opzionale) Crea dati demo

```bash
python manage.py shell
```

```python
from progetti_eventi.models import Progetto, ProgettoReparto
from anagrafica.models import Cliente
from users.models import User
from datetime import date, timedelta

# Crea cliente demo
cliente = Cliente.objects.create(
    ragione_sociale="Demo SRL",
    telefono="1234567890",
    email="demo@example.com",
    partita_iva="IT12345678901"
)

# Crea commerciale
commerciale = User.objects.first()

# Crea progetto
progetto = Progetto.objects.create(
    cliente=cliente,
    nome_evento="Matrimonio Demo",
    tipo_evento="matrimonio",
    data_evento=date.today() + timedelta(days=30),
    location="Villa Demo",
    indirizzo_location="Via Demo 1",
    citta_location="Milano",
    data_consegna_richiesta=date.today() + timedelta(days=29),
    data_ritiro_richiesta=date.today() + timedelta(days=31),
    commerciale=commerciale,
    reparti_coinvolti=['audio', 'video', 'luci'],
)

# Crea reparti
for reparto in ['audio', 'video', 'luci']:
    ProgettoReparto.objects.create(
        progetto=progetto,
        tipo_reparto=reparto,
    )

print(f"Progetto {progetto.codice} creato!")
```

## URL Principali

| URL | Descrizione |
|-----|-------------|
| `/progetti/` | Dashboard commerciale |
| `/progetti/progetti/` | Lista progetti |
| `/progetti/progetti/nuovo/` | Crea progetto |
| `/progetti/progetti/<uuid>/` | Vista master progetto |
| `/progetti/progetti/<uuid>/modifica/` | Modifica progetto |
| `/progetti/progetti/<uuid>/invia-engineering/` | Invia a engineering |
| `/progetti/reparti/<uuid>/` | Dettaglio reparto |
| `/progetti/reparti/<uuid>/liste-prodotti/nuova/` | Crea lista prodotti |
| `/progetti/liste-prodotti/<uuid>/` | Dettaglio lista |
| `/progetti/liste-prodotti/<uuid>/approva/` | Approva lista |

## Permissions

Permessi Django standard:
- `progetti_eventi.view_progetto`
- `progetti_eventi.add_progetto`
- `progetti_eventi.change_progetto`
- `progetti_eventi.delete_progetto`
- `progetti_eventi.view_progettoreparto`
- `progetti_eventi.add_listaprodotti`
- `progetti_eventi.change_listaprodotti`

## Testing

```bash
# Run test
python manage.py test progetti_eventi

# Coverage
pytest --cov=progetti_eventi
```

## Roadmap Futuri Sviluppi

- [ ] Notifiche email automatiche agli ingegneri
- [ ] Dashboard engineering dedicata
- [ ] Export PDF progetto completo
- [ ] Timeline visuale interattiva
- [ ] Drag & drop assegnazione ingegneri
- [ ] Clonazione progetti
- [ ] Template progetti predefiniti
- [ ] Integrazione calendario aziendale

## Note Tecniche

### Perché ProgettoReparto è separato?

Inizialmente si potrebbe pensare a un campo JSONField per tutti i reparti, ma la separazione offre:

1. **Relazioni DB corrette**: Ogni reparto ha ForeignKey verso altre app
2. **Query efficienti**: Filtri facili (`ProgettoReparto.objects.filter(tipo_reparto='audio')`)
3. **Scalabilità**: Facile aggiungere nuovi reparti
4. **Audit trail**: Tracking modifiche per reparto
5. **Permissions**: Possibili permessi per reparto in futuro

### Gestione Stati

Gli stati sono gestiti a 2 livelli:

1. **Stato Progetto** (globale):
   - `bozza` → `in_engineering` → `engineering_completato` → `in_preparazione` → `pronto` → `in_corso` → `completato`

2. **Stato Reparto** (calcolato da flag):
   ```python
   @property
   def stato_globale(self):
       if not self.engineering_completato:
           return 'engineering_pending'
       if all([magazzino_ready, logistica_ready, travel_ready, scouting_ready]):
           return 'pronto'
       return 'in_preparazione'
   ```

## Supporto

Per domande o segnalazioni: aprire issue nel repository.

---

**Versione:** 1.0
**Data:** Febbraio 2026
**Autore:** Claude Code + Giorgio
