# App Trasporti - Documentazione Completa

## Indice
1. [Panoramica](#panoramica)
2. [Modelli Dati](#modelli-dati)
3. [Workflow Completo](#workflow-completo)
4. [Funzionalità Principali](#funzionalità-principali)
5. [Sistema Email](#sistema-email)
6. [Template e UI](#template-e-ui)
7. [Configurazione](#configurazione)

---

## Panoramica

L'app **Trasporti** è un sistema completo per la gestione delle richieste di trasporto merci, dalla creazione della richiesta fino alla consegna finale. Permette di:

- Creare richieste di trasporto dettagliate
- Inviare richieste a fornitori accreditati e non
- Raccogliere offerte tramite form pubblico (senza autenticazione)
- Valutare e confrontare le offerte ricevute
- Approvare e confermare il trasporto
- Riaprire richieste per cambiare fornitore
- Tracciare lo stato del trasporto

### Caratteristiche Principali

- **Workflow a 3 Step** simile all'app preventivi
- **Form pubblico** per fornitori esterni (accesso tramite token)
- **Email automatiche** con design BEF Management
- **Gestione colli dettagliata** (dimensioni, peso, volume)
- **Calcolo automatico distanze** tra ritiro e consegna
- **Sistema di conferma** con notifiche email
- **Possibilità di riapertura** per cambio fornitore

---

## Modelli Dati

### RichiestaTrasporto

Modello principale che rappresenta una richiesta di trasporto.

#### Campi Principali

**Identificazione:**
- `numero` - Numero univoco autogenerato (formato: TRAS-YYYY-NNNN)
- `titolo` - Titolo descrittivo della richiesta
- `tipo_trasporto` - Tipo (NAZIONALE, INTERNAZIONALE, ESPRESSO, GROUPAGE)
- `priorita` - Priorità (BASSA, NORMALE, ALTA, URGENTE)

**Ritiro:**
- `indirizzo_ritiro`, `cap_ritiro`, `citta_ritiro`, `provincia_ritiro`, `nazione_ritiro`
- `data_ritiro_richiesta` - Data richiesta per il ritiro
- `ora_ritiro_dalle`, `ora_ritiro_alle` - Fascia oraria ritiro
- `note_ritiro` - Note specifiche per il ritiro

**Consegna:**
- `indirizzo_consegna`, `cap_consegna`, `citta_consegna`, `provincia_consegna`, `nazione_consegna`
- `data_consegna_richiesta` - Data richiesta per la consegna
- `ora_consegna_dalle`, `ora_consegna_alle` - Fascia oraria consegna
- `note_consegna` - Note specifiche per la consegna

**Merce:**
- `tipo_merce` - Descrizione tipo di merce
- `numero_colli_totali` - Calcolato automaticamente dai colli
- `peso_totale_kg` - Calcolato automaticamente dai colli
- `volume_totale_m3` - Calcolato automaticamente dai colli
- `valore_merce` - Valore dichiarato della merce
- `merce_fragile` - Flag merce fragile
- `merce_deperibile` - Flag merce deperibile
- `merce_pericolosa` - Flag merce pericolosa (ADR)
- `codice_adr` - Codice ADR se merce pericolosa
- `temperatura_controllata` - Flag temperatura controllata
- `temperatura_min`, `temperatura_max` - Range temperatura

**Servizi Richiesti:**
- `assicurazione_richiesta` - Flag assicurazione
- `massimale_assicurazione` - Massimale assicurazione
- `scarico_a_piano` - Flag scarico a piano
- `numero_piano` - Numero piano per scarico
- `presenza_montacarichi` - Flag montacarichi
- `tracking_richiesto` - Flag tracking GPS
- `packing_list_richiesto` - Flag packing list

**Workflow:**
- `stato` - Stato della richiesta (vedi Stati Workflow)
- `data_creazione` - Data creazione richiesta
- `data_invio_richiesta` - Data invio ai trasportatori
- `data_valutazione` - Data inizio valutazione offerte
- `data_approvazione` - Data approvazione offerta
- `data_conferma` - Data conferma trasporto
- `data_ritiro_effettivo` - Data ritiro effettivo
- `data_consegna_effettiva` - Data consegna effettiva

**Relazioni:**
- `richiedente` - User che ha creato la richiesta
- `operatore` - User che gestisce la richiesta
- `approvatore` - User che ha approvato l'offerta
- `offerta_approvata` - ForeignKey all'offerta approvata

#### Stati Workflow

1. **BOZZA** - Richiesta in creazione
2. **RICHIESTA_INVIATA** - Richiesta inviata ai trasportatori
3. **OFFERTE_RICEVUTE** - Almeno un'offerta ricevuta
4. **IN_VALUTAZIONE** - Offerte in fase di valutazione
5. **APPROVATA** - Offerta approvata, in attesa di conferma
6. **CONFERMATA** - Trasporto confermato al fornitore
7. **IN_CORSO** - Trasporto in corso
8. **CONSEGNATO** - Merce consegnata
9. **ANNULLATA** - Richiesta annullata

### ColloTrasporto

Rappresenta un collo da trasportare (pallet, scatola, ecc.).

#### Campi

- `richiesta` - ForeignKey a RichiestaTrasporto
- `quantita` - Numero di colli identici
- `tipo` - Tipo (PALLET_EUR, PALLET_120x100, SCATOLA, CASSA, FUSTO, ROTOLO, ALTRO)
- `lunghezza_cm`, `larghezza_cm`, `altezza_cm` - Dimensioni in cm
- `peso_kg` - Peso totale
- `volume_m3` - Calcolato automaticamente (L x W x H / 1.000.000 * quantità)
- `fragile` - Flag fragile
- `stackable` - Flag impilabile
- `descrizione` - Descrizione aggiuntiva

### TrasportatoreOfferta

Rappresenta un trasportatore (fornitore) che può ricevere richieste.

#### Campi

- `richiesta` - ForeignKey a RichiestaTrasporto
- `fornitore` - ForeignKey a Fornitore (se accreditato)
- `nome` - Nome trasportatore
- `email` - Email per invio richiesta
- `attivo` - Se è un fornitore accreditato
- `token` - UUID per accesso pubblico al form
- `data_invio_email` - Data invio email richiesta
- `email_inviata` - Flag email inviata

### OffertaTrasporto

Rappresenta un'offerta ricevuta da un trasportatore.

#### Campi Principali

**Identificazione:**
- `richiesta` - ForeignKey a RichiestaTrasporto
- `trasportatore` - ForeignKey a TrasportatoreOfferta
- `numero_offerta` - Numero offerta del fornitore

**Prezzi:**
- `importo_trasporto` - Importo base trasporto
- `importo_assicurazione` - Importo assicurazione
- `importo_pedaggi` - Importo pedaggi
- `importo_extra` - Importo extra
- `descrizione_extra` - Descrizione costi extra
- `importo_totale` - Totale (calcolato automaticamente)
- `valuta` - Valuta (default: EUR)

**Tempi:**
- `data_ritiro_proposta` - Data ritiro proposta
- `ora_ritiro_dalle`, `ora_ritiro_alle` - Fascia oraria ritiro
- `data_consegna_prevista` - Data consegna prevista
- `ora_consegna_dalle`, `ora_consegna_alle` - Fascia oraria consegna
- `tempo_transito_giorni` - Giorni di transito

**Mezzo:**
- `tipo_mezzo` - Tipo (FURGONE, MOTRICE, BILICO, AUTOARTICOLATO, ALTRO)
- `targa_mezzo` - Targa del mezzo
- `nome_conducente` - Nome conducente
- `telefono_conducente` - Telefono conducente

**Servizi:**
- `tracking_incluso` - Flag tracking incluso
- `assicurazione_inclusa` - Flag assicurazione inclusa
- `scarico_a_piano_incluso` - Flag scarico a piano incluso

**Workflow:**
- `data_ricevimento` - Data ricezione offerta
- `data_scadenza_offerta` - Data scadenza validità
- `confermata` - Flag offerta confermata
- `data_conferma` - Data conferma trasporto
- `file_offerta` - Allegato PDF/documento

**Note:**
- `note_tecniche` - Note tecniche
- `note_commerciali` - Note commerciali

### ParametroValutazione

Parametri custom per valutare le offerte.

#### Campi

- `offerta` - ForeignKey a OffertaTrasporto
- `descrizione` - Descrizione parametro
- `valore` - Valore del parametro

---

## Workflow Completo

Il workflow dell'app trasporti segue 3 step principali + fasi aggiuntive.

### Step 0: Creazione Richiesta

**URL:** `/trasporti/richieste/nuova/`
**View:** `richiesta_create`
**Stato:** BOZZA

1. L'utente compila il form di creazione richiesta
2. Inserisce dati ritiro e consegna
3. Aggiunge i colli (formset)
4. Specifica servizi richiesti
5. Salva la richiesta in stato BOZZA

**Campi Obbligatori:**
- Titolo
- Indirizzi ritiro/consegna completi
- Date ritiro/consegna
- Almeno un collo

### Step 1: Selezione Trasportatori e Invio

**URL:** `/trasporti/richieste/<uuid>/step1-invia/`
**View:** `step1_invia_trasportatori`
**Stato:** BOZZA → RICHIESTA_INVIATA

1. L'utente seleziona i trasportatori dalla pagina di selezione
2. Può scegliere tra:
   - **Fornitori accreditati** (già registrati nel sistema)
   - **Nuovi fornitori** (fino a 3, solo nome ed email)
3. Conferma la selezione
4. Il sistema:
   - Crea record TrasportatoreOfferta per ogni trasportatore
   - Genera token univoci per accesso pubblico
   - Invia email a tutti i trasportatori con link al form
   - Cambia stato a RICHIESTA_INVIATA

**Email Inviata:**
- Oggetto: "Richiesta Preventivo Trasporto - [NUMERO]"
- Corpo: HTML con dettagli richiesta e link con token
- Link: `/trasporti/risposta/<token>/`

### Step 2: Raccolta Offerte

**URL:** `/trasporti/richieste/<uuid>/step2-raccolta/`
**View:** `step2_raccolta_offerte`
**Stato:** RICHIESTA_INVIATA → OFFERTE_RICEVUTE (quando arriva prima offerta)

**Pagina Interna (operatore):**
- Visualizza elenco trasportatori contattati
- Mostra stato email (inviata/non inviata)
- Lista offerte ricevute
- Possibilità di aggiungere offerte manualmente
- Pulsante "Procedi a Valutazione" (quando ci sono offerte)

**Pagina Pubblica (fornitore):**

**URL:** `/trasporti/risposta/<token>/`
**View:** `risposta_fornitore_pubblica`
**Autenticazione:** NO (accesso tramite token)

Il fornitore:
1. Clicca sul link ricevuto via email
2. Visualizza tutti i dettagli della richiesta:
   - Percorso (ritiro → consegna)
   - Date richieste
   - Dettaglio colli (quantità, dimensioni, peso)
   - Servizi richiesti
   - Note
3. Compila il form offerta:
   - Importo imponibile (+ IVA)
   - Data ritiro garantita
   - Data consegna garantita
   - Note eventuali
   - Allegato preventivo (opzionale)
4. Invia l'offerta

**Cosa succede:**
- Viene creata un'offerta OffertaTrasporto
- Importo totale = importo_imponibile * 1.22 (IVA 22%)
- Tempo transito = giorni tra ritiro e consegna
- Lo stato della richiesta passa a OFFERTE_RICEVUTE
- Il fornitore può aggiornare l'offerta se clicca di nuovo sul link

### Step 3: Valutazione e Approvazione

**URL:** `/trasporti/richieste/<uuid>/step3-valutazione/`
**View:** `step3_valutazione`
**Stato:** OFFERTE_RICEVUTE/IN_VALUTAZIONE → APPROVATA

1. L'operatore visualizza tabella comparativa offerte:
   - Trasportatore
   - Importo totale
   - Data ritiro/consegna
   - Tempo transito
   - Servizi inclusi
2. Può visualizzare dettaglio di ogni offerta
3. Seleziona l'offerta migliore tramite radio button
4. Conferma l'approvazione
5. Il sistema:
   - Imposta `offerta_approvata` sulla richiesta
   - Cambia stato a APPROVATA
   - Salva `data_approvazione`
   - Salva `approvatore` (user corrente)

### Step 4: Conferma Trasporto

**URL:** `/trasporti/richieste/<uuid>/conferma-trasporto/`
**View:** `conferma_trasporto`
**Stato:** APPROVATA → CONFERMATA

**Quando usare:**
- Dopo aver approvato un'offerta
- Quando si è pronti a confermare il trasporto al fornitore

**Cosa fa:**
1. Verifica che ci sia un'offerta approvata
2. Controlla se c'era già una conferma precedente
3. Se c'è un fornitore precedente:
   - Marca l'offerta precedente come `confermata=False`
   - Invia email di annullamento al fornitore precedente
4. Marca l'offerta corrente come `confermata=True`
5. Invia email di conferma al nuovo fornitore
6. Cambia stato a CONFERMATA
7. Salva `data_conferma`

**Email di Conferma (header verde):**
- Oggetto: "✅ CONFERMATO - Trasporto [NUMERO]"
- Importo evidenziato in verde
- Dettagli completi ritiro/consegna
- Checklist prossimi passi

**Email di Annullamento (header rosso):**
- Oggetto: "Annullamento Trasporto - [NUMERO]"
- Notifica della cancellazione
- Motivo: selezione fornitore alternativo

### Step 5: Riapertura Richiesta

**URL:** `/trasporti/richieste/<uuid>/riapri/`
**View:** `riapri_richiesta`
**Stato:** CONFERMATA/IN_CORSO/CONSEGNATO → APPROVATA

**Quando usare:**
- Il fornitore confermato ha problemi
- Si vuole cambiare fornitore per qualsiasi motivo

**Cosa fa:**
1. Verifica che la richiesta sia in stato CONFERMATA/IN_CORSO/CONSEGNATO
2. Riporta lo stato a APPROVATA
3. Mantiene l'offerta approvata corrente
4. Reindirizza alla pagina di valutazione
5. L'operatore può ora selezionare un'altra offerta

**Processo completo cambio fornitore:**
1. Click su "Riapri Richiesta" → stato torna ad APPROVATA
2. Vai a valutazione → scegli nuova offerta → approva
3. Click su "Conferma Trasporto" → invia email annullamento + conferma

### Stati Successivi (Gestiti manualmente)

**IN_CORSO:**
- Trasporto iniziato
- Possibile tracking tramite `/trasporti/offerte/<uuid>/tracking/`

**CONSEGNATO:**
- Trasporto completato
- Inserire `data_consegna_effettiva`

**ANNULLATA:**
- Richiesta annullata per qualsiasi motivo

---

## Funzionalità Principali

### Dashboard

**URL:** `/trasporti/`
**View:** `dashboard`

Visualizza:
- Statistiche richieste per stato
- Ultime richieste create
- Richieste in attesa di azione
- Grafici e metriche

### Lista Richieste

**URL:** `/trasporti/richieste/`
**View:** `richieste_list`

- Tabella filtrabili e ordinabili
- Filtri per stato, priorità, date
- Ricerca per numero, titolo, città
- Link alle azioni rapide

### Dettaglio Richiesta

**URL:** `/trasporti/richieste/<uuid>/`
**View:** `richiesta_detail`

**Visualizza:**
- Header con numero, titolo, stato, priorità
- Percorso (ritiro → consegna) con mappe visuali
- Tabella colli dettagliata
- Caratteristiche merce
- Servizi richiesti
- Timeline workflow
- Offerte ricevute (tabella comparativa)

**Azioni contestuali per stato:**
- BOZZA: "Seleziona Trasportatori"
- RICHIESTA_INVIATA: "Gestisci Offerte" + "Aggiungi Offerta"
- OFFERTE_RICEVUTE: "Valuta Offerte"
- APPROVATA: "Conferma Trasporto"
- CONFERMATA/IN_CORSO/CONSEGNATO: "Tracking Spedizione" + "Riapri Richiesta"

### Dettaglio Offerta

**URL:** `/trasporti/offerte/<uuid>/`
**View:** `offerta_detail`

**Design BEF Management:**
- Header gradiente verde (#74b49b → #5c8d89)
- Card trasportatore
- Dettaglio prezzi con totale evidenziato
- Box ritiro/consegna colorati (verde chiaro/medio)
- Tabella confronto con altre offerte
- Badge "la più economica" se applicabile
- Calcolo automatico differenza con offerta migliore

**Visualizza:**
- Info trasportatore completo
- Breakdown prezzi dettagliato
- Tempi di ritiro/consegna proposti
- Mezzo e conducente
- Servizi inclusi
- Note tecniche/commerciali
- File allegato scaricabile
- Info richiesta collegata
- Confronto con altre offerte

### Selezione Trasportatori

**URL:** `/trasporti/richieste/<uuid>/trasportatori/`
**View:** `richiesta_select_trasportatori`

**Form con due sezioni:**

1. **Fornitori Accreditati:**
   - Select2 multiplo
   - Lista fornitori attivi ordinati per nome
   - Mostra email e info contatto

2. **Nuovi Fornitori (fino a 3):**
   - Campi nome + email per 3 nuovi fornitori
   - Validazione: se compili nome, email è obbligatoria
   - Creati automaticamente come fornitori non accreditati

**Sidebar:**
- Trasportatori già selezionati
- Info workflow step

**Validazione:**
- Almeno 1 trasportatore (esistente o nuovo)
- Email valide
- Coppie nome/email complete

### Creazione Offerta Manuale

**URL:** `/trasporti/richieste/<uuid>/offerta/nuova/`
**View:** `offerta_create`

Per inserire offerte ricevute offline (telefono, fax, ecc.)

**Campi principali:**
- Selezione trasportatore (tra quelli della richiesta)
- Numero offerta fornitore
- Importi (trasporto, assicurazione, pedaggi, extra)
- Date e orari ritiro/consegna
- Tipo mezzo e conducente
- Servizi inclusi
- Note tecniche/commerciali
- File offerta (upload)

### Tracking Spedizione

**URL:** `/trasporti/offerte/<uuid>/tracking/`
**View:** `offerta_tracking`

**Funzionalità:**
- Visualizzazione stato trasporto
- Timeline eventi
- Posizione GPS (se disponibile)
- Info conducente
- ETA (tempo stimato arrivo)

### Calcolo Distanza

**URL AJAX:** `/trasporti/api/calcola-distanza/`
**View:** `api_calcola_distanza`

Endpoint AJAX per calcolare distanza tra ritiro e consegna.

**Parametri POST:**
- `ritiro_citta`, `ritiro_provincia`
- `consegna_citta`, `consegna_provincia`

**Response JSON:**
```json
{
  "distanza_km": 245,
  "tempo_stimato": "3h 15min"
}
```

### Parametri Valutazione

**URL GET:** `/trasporti/offerte/<uuid>/parametri/`
**URL SAVE:** `/trasporti/offerte/<uuid>/parametri/save/`
**Views:** `offerta_parametri_get`, `offerta_parametri_save`

Endpoint AJAX per gestire parametri custom di valutazione.

**Esempi parametri:**
- Esperienza fornitore
- Recensioni precedenti
- Assicurazione inclusa
- Tempi di consegna
- Servizi extra

---

## Sistema Email

Tutte le email utilizzano il **ManagementEmailService** con design HTML responsive.

### Palette Colori BEF Management

```css
--color-first: #d3f6d1;   /* Verde chiaro */
--color-second: #a7d7c5;  /* Verde medio */
--color-third: #74b49b;   /* Verde principale */
--color-fourth: #5c8d89;  /* Verde scuro */
--color-text: #393e46;    /* Testo */
```

### Email Richiesta Preventivo

**Destinatario:** Trasportatori selezionati
**Quando:** Step 1 - Invio richieste
**Template:** Inline nella view `step1_invia_trasportatori`

**Contenuto:**
- Header gradiente verde
- Numero e titolo richiesta
- Percorso (ritiro → consegna)
- Riepilogo merce e colli
- Servizi richiesti
- Call-to-action: Link al form pubblico
- Footer con lock icon (pagina sicura)

**Link formato:**
```
https://dominio.com/trasporti/risposta/<TOKEN>/
```

### Email Conferma Trasporto

**Destinatario:** Fornitore selezionato
**Quando:** Conferma trasporto
**Template:** Inline nella view `conferma_trasporto`

**Caratteristiche:**
- Header gradiente verde (#74b49b → #5c8d89)
- Importo evidenziato in box verde
- Tabella dettagli ritiro/consegna
- Box colli con dimensioni
- Checklist prossimi passi:
  - ☐ Confermare ricezione email
  - ☐ Organizzare ritiro
  - ☐ Comunicare targa/conducente
  - ☐ Fornire tracking

### Email Annullamento Trasporto

**Destinatario:** Fornitore precedentemente confermato
**Quando:** Conferma a nuovo fornitore
**Template:** Inline nella view `conferma_trasporto`

**Caratteristiche:**
- Header gradiente rosso (#dc3545 → #c82333)
- Messaggio chiaro di annullamento
- Motivo: selezione fornitore alternativo
- Scuse per l'inconveniente
- Invito a future collaborazioni

---

## Template e UI

### Palette Colori Consistente

Tutti i template utilizzano la palette BEF Management:

**Template Interni** (extends base.html):
- Verde per header e azioni positive
- Blu per info
- Giallo/arancione per warning
- Rosso per danger/annullamenti

**Template Pubblico** (risposta_fornitore_pubblica.html):
- Standalone (non extends base.html)
- Usa stessa palette verde
- Background gradiente verde
- Card arrotondata con shadow
- Responsive per mobile

### Componenti UI Riutilizzabili

**Badge Stati:**
```html
{% if richiesta.stato == 'BOZZA' %}bg-secondary
{% elif richiesta.stato == 'RICHIESTA_INVIATA' %}bg-primary
{% elif richiesta.stato == 'OFFERTE_RICEVUTE' %}bg-info
{% elif richiesta.stato == 'APPROVATA' %}bg-success
{% elif richiesta.stato == 'CONFERMATA' %}bg-success
{% elif richiesta.stato == 'IN_CORSO' %}bg-warning
{% elif richiesta.stato == 'CONSEGNATO' %}bg-success
{% else %}bg-danger
```

**Box Ritiro/Consegna:**
```html
<!-- Ritiro: verde chiaro con bordo verde principale -->
<div class="bg-primary bg-opacity-10 border-start border-4 border-success">

<!-- Consegna: verde medio con bordo verde scuro -->
<div class="bg-success bg-opacity-10 border-start border-4 border-success">
```

**Timeline Eventi:**
```html
<ul class="list-unstyled timeline">
  <li class="mb-2">
    <small class="text-muted">{{ data|date:"d/m/Y H:i" }}</small><br>
    <strong>Evento</strong>
  </li>
</ul>
```

### Icone FontAwesome

- **Trasporto:** `fa-truck`, `fa-truck-moving`
- **Ritiro:** `fa-arrow-up`
- **Consegna:** `fa-arrow-down`
- **Collo:** `fa-box`
- **Tracking:** `fa-map-marker-alt`
- **Conferma:** `fa-check-circle`
- **Riapertura:** `fa-undo`
- **Email:** `fa-envelope`
- **File:** `fa-file-pdf`
- **Sicurezza:** `fa-lock`

### Conferme JavaScript

**Riapertura richiesta:**
```javascript
onclick="return confirm('Sei sicuro di voler riaprire questa richiesta? Potrai selezionare un altro fornitore.');"
```

---

## Configurazione

### Settings Required

```python
# settings.py

INSTALLED_APPS = [
    ...
    'trasporti',
    'django_select2',  # Per select multipli
]

# Upload files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Email (già configurato in Management2)
# Usa ManagementEmailService
```

### URL Configuration

```python
# project/urls.py
from django.urls import path, include

urlpatterns = [
    ...
    path('trasporti/', include('trasporti.urls')),
]
```

### Permissions

**Required permissions:**
- `trasporti.view_richiestatrasporto`
- `trasporti.add_richiestatrasporto`
- `trasporti.change_richiestatrasporto`
- `trasporti.delete_richiestatrasporto`
- `trasporti.view_offertatrasporto`
- `trasporti.add_offertatrasporto`

**Public access:**
- `/trasporti/risposta/<token>/` - Nessuna autenticazione richiesta

### Migrations

```bash
python manage.py makemigrations trasporti
python manage.py migrate trasporti
```

**Migrations create:**
- RichiestaTrasporto model
- ColloTrasporto model
- TrasportatoreOfferta model
- OffertaTrasporto model
- ParametroValutazione model

### Static Files

**CSS richiesti:**
- Bootstrap 5.3.0
- FontAwesome 6.4.0
- Django Select2 CSS

**JavaScript richiesti:**
- Bootstrap 5.3.0 bundle
- jQuery (per Select2)
- Django Select2 JS

---

## Utilizzo Tipico

### Scenario Completo

**1. Creazione Richiesta**
```
Giorgio (Operatore) crea richiesta:
- Titolo: "Trasporto macchinari Milano → Roma"
- Ritiro: Via Test 1, 20100 Milano (MI) - 15/02/2026
- Consegna: Via Test 2, 00100 Roma (RM) - 18/02/2026
- Colli: 2 pallet EUR (120x80x120 cm, 300 kg cad.)
- Servizi: Assicurazione + Tracking
- Salva → Stato: BOZZA
```

**2. Selezione Trasportatori**
```
Giorgio seleziona:
- Fornitori accreditati: "Trasporti Veloci SRL", "Express Cargo"
- Nuovo fornitore: "Logistica Nuova" (info@logisticanuova.it)
- Conferma → Sistema invia 3 email con link token
- Stato: RICHIESTA_INVIATA
```

**3. Ricezione Offerte**
```
Fornitore 1 (Trasporti Veloci):
- Clicca link da email
- Vede dettagli richiesta
- Compila: €850 + IVA, ritiro 15/02, consegna 17/02
- Allega PDF preventivo
- Invia → Offerta creata

Fornitore 2 (Express Cargo):
- Offre: €920 + IVA, ritiro 15/02, consegna 18/02

Fornitore 3 (Logistica Nuova):
- Offre: €780 + IVA, ritiro 16/02, consegna 19/02

Stato: OFFERTE_RICEVUTE (3 offerte)
```

**4. Valutazione**
```
Giorgio va in valutazione:
- Vede tabella comparativa:
  - Logistica Nuova: €951.60 (3 giorni)
  - Trasporti Veloci: €1037.00 (2 giorni) ← più veloce
  - Express Cargo: €1122.40 (3 giorni)

- Sceglie "Trasporti Veloci" (miglior rapporto qualità/prezzo/tempo)
- Approva → Stato: APPROVATA
```

**5. Conferma**
```
Giorgio conferma trasporto:
- Click "Conferma Trasporto"
- Sistema invia email a Trasporti Veloci:
  ✅ "CONFERMATO - Trasporto TRAS-2026-0042"
  - Importo: €1037.00
  - Ritiro: 15/02/2026 in Via Test 1, Milano
  - Checklist prossimi passi

- Stato: CONFERMATA
```

**6. Problema e Cambio Fornitore**
```
Trasporti Veloci ha un imprevisto:
- Giorgio clicca "Riapri Richiesta"
- Conferma → Stato torna: APPROVATA
- Torna a valutazione
- Seleziona "Logistica Nuova" (€951.60)
- Approva
- Click "Conferma Trasporto"

Sistema invia 2 email:
- ❌ A Trasporti Veloci: "Annullamento Trasporto"
- ✅ A Logistica Nuova: "CONFERMATO - Trasporto"

- Stato: CONFERMATA (nuovo fornitore)
```

**7. Completamento**
```
- 16/02: Ritiro effettuato → Stato: IN_CORSO
- Tracking GPS attivo
- 19/02: Consegna completata → Stato: CONSEGNATO
```

---

## Best Practices

### Per gli Operatori

1. **Compilare tutti i dettagli della richiesta** - Più info = offerte accurate
2. **Selezionare almeno 3 trasportatori** - Migliore confronto prezzi
3. **Verificare le offerte ricevute** - Controllare allegati e note
4. **Documentare parametri di valutazione** - Per future referenze
5. **Confermare solo quando sicuri** - La conferma invia email ufficiale

### Per i Fornitori

1. **Rispondere tempestivamente** - Le richieste possono avere scadenza
2. **Allegare preventivo dettagliato** - PDF con condizioni chiare
3. **Essere precisi su date** - Evitare ritardi non comunicati
4. **Includere tutti i costi** - Evitare sorprese successive
5. **Aggiornare l'offerta se necessario** - Il link rimane valido

### Sicurezza

1. **Token univoci** - Un token per ogni trasportatore per ogni richiesta
2. **Validazione input** - Tutti i form validano dimensioni file e formati
3. **Protezione email** - Nessun dato sensibile in plain text
4. **Audit trail** - Tutte le date di workflow registrate
5. **Conferme JavaScript** - Per azioni critiche (riapri, elimina)

---

## Troubleshooting

### Problema: Email non inviate

**Causa:** Configurazione SMTP errata
**Soluzione:** Verificare settings email e ManagementEmailService

### Problema: Form pubblico non accessibile

**Causa:** Token errato o scaduto
**Soluzione:** Rigenerare token o reinviare email

### Problema: Calcolo totali errato

**Causa:** Colli non salvati correttamente
**Soluzione:** Verificare formset e signals save()

### Problema: Offerta non appare in valutazione

**Causa:** Offerta scaduta o non confermata
**Soluzione:** Verificare data_scadenza_offerta

### Problema: Non posso confermare trasporto

**Causa:** Offerta non approvata
**Soluzione:** Prima approvare un'offerta in step 3

---

## Sviluppi Futuri

### Funzionalità Pianificate

- [ ] Integrazione tracking GPS real-time
- [ ] Notifiche push per cambio stato
- [ ] Export Excel delle richieste
- [ ] Statistiche e analytics avanzate
- [ ] Integrazione con corrieri (API)
- [ ] Firma digitale documenti
- [ ] App mobile per conducenti
- [ ] Rating e recensioni fornitori
- [ ] Sistema di fatturazione integrato
- [ ] Multi-valuta avanzato

### Miglioramenti UI

- [ ] Grafici comparativi offerte
- [ ] Mappa percorso ritiro-consegna
- [ ] Timeline visuale workflow
- [ ] Drag & drop upload files
- [ ] Preview PDF in-page
- [ ] Chat con fornitori

---

## Contatti e Supporto

**Developer:** Claude Code
**Progetto:** BEF Management
**Versione:** 1.0
**Data:** Gennaio 2026

Per domande o segnalazioni aprire issue nel repository del progetto.

---

*Documento generato automaticamente - Aggiornato: 12/01/2026*
