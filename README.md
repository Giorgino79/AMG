# ModularBEF - Guida Sviluppo App

## Indice
1. [Introduzione](#introduzione)
2. [Architettura Core Obbligatoria](#architettura-core-obbligatoria)
3. [Creazione Nuova App - Guida Passo Passo](#creazione-nuova-app---guida-passo-passo)
4. [Models - Standard Obbligatori](#models---standard-obbligatori)
5. [Views - Standard Obbligatori](#views---standard-obbligatori)
6. [Templates - Standard Obbligatori](#templates---standard-obbligatori)
7. [Funzionalità Core Disponibili](#funzionalità-core-disponibili)
8. [Checklist Nuova App](#checklist-nuova-app)

---

## Introduzione

ModularBEF utilizza un'architettura modulare con un **core centralizzato** che fornisce funzionalità riutilizzabili. L'utilizzo delle funzioni e templates del core è **OBBLIGATORIO** per garantire:

- Consistenza dell'interfaccia utente
- Riutilizzo del codice
- Manutenibilità del progetto
- Funzionalità automatiche (allegati, QR code, audit, ricerca globale)

---

## Architettura Core Obbligatoria

### Struttura Progetto

```
mod2(26GEN26)/
├── core/                          # APP CORE - NON MODIFICARE
│   ├── models/
│   │   └── base.py               # BaseModel, BaseModelWithCode, BaseModelSimple
│   ├── mixins/
│   │   ├── model_mixins.py       # AllegatiMixin, QRCodeMixin, PDFMixin, etc.
│   │   └── view_mixins.py        # PermissionMixin, SearchMixin, etc.
│   ├── views.py                  # Generazione PDF, Excel, CSV, XML
│   ├── views_allegati.py         # API AJAX allegati
│   ├── views_qrcode.py           # API AJAX QR Code
│   ├── search.py                 # SearchRegistry
│   └── permissions_registry.py   # ModelPermissionRegistry
│
├── templates/
│   ├── commons_templates/         # Templates comuni OBBLIGATORI
│   │   ├── base_detail.html      # Base per pagine dettaglio
│   │   ├── dashboard.html        # Dashboard
│   │   └── components/           # Componenti allegati
│   │
│   └── components/                # Componenti UI riutilizzabili
│       ├── alerts.html
│       ├── breadcrumb.html
│       ├── confirm_action.html
│       ├── delete_modal.html
│       ├── empty_state.html
│       ├── form_layout.html
│       ├── loading_spinner.html
│       ├── pagination.html
│       └── detail_layout.html
│
├── static/
│   ├── css/
│   │   ├── base.css
│   │   └── detail_page.css
│   └── js/
│       ├── base.js
│       ├── allegati.js
│       ├── qrcode.js
│       └── search.js
│
└── [tue_app]/                     # Le tue app personalizzate
```

---

## Creazione Nuova App - Guida Passo Passo

### Step 1: Creare la struttura app

```bash
python manage.py startapp nome_app
```

### Step 2: Struttura cartelle consigliata

```
nome_app/
├── __init__.py
├── admin.py
├── apps.py
├── models.py
├── views.py
├── urls.py
├── forms.py
├── management/
│   └── commands/
│       └── setup_nome_app.py
├── templates/
│   └── nome_app/
│       ├── list.html
│       ├── detail.html
│       ├── form.html
│       └── pdf/
│           └── model_pdf.html
└── migrations/
```

### Step 3: Configurare `apps.py`

```python
from django.apps import AppConfig


class NomeAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'nome_app'
    verbose_name = 'Nome App Leggibile'

    def ready(self):
        """
        Registra i model nel SearchRegistry per la ricerca globale.
        OBBLIGATORIO per ogni model user-facing.
        """
        from core.search import SearchRegistry
        from .models import MioModello

        SearchRegistry.register(
            model=MioModello,
            category='Nome Categoria',
            icon='bi-icon-name',  # Bootstrap Icons
            priority=5  # 0-10, default 5
        )
```

### Step 4: Aggiungere a `INSTALLED_APPS` in settings.py

```python
INSTALLED_APPS = [
    # ...
    'nome_app.apps.NomeAppConfig',
]
```

### Step 5: Aggiungere URL in urls.py principale

```python
urlpatterns = [
    # ...
    path('nome-app/', include('nome_app.urls')),
]
```

---

## Models - Standard Obbligatori

### REGOLA 1: Ereditare SEMPRE da BaseModel

```python
# nome_app/models.py

from django.db import models
from django.urls import reverse
from core.models import BaseModel  # OBBLIGATORIO
from core.mixins.model_mixins import AllegatiMixin  # OBBLIGATORIO se servono allegati


class MioModello(BaseModel, AllegatiMixin):
    """
    Esempio di modello corretto.

    Eredita automaticamente:
    - id (UUID)
    - created_at, updated_at
    - created_by, updated_by
    - is_active, deleted_at (soft delete)
    - Gestione allegati completa
    """

    # I tuoi campi custom
    nome = models.CharField("Nome", max_length=200)
    descrizione = models.TextField("Descrizione", blank=True)
    stato = models.CharField(
        "Stato",
        max_length=20,
        choices=[
            ('bozza', 'Bozza'),
            ('attivo', 'Attivo'),
            ('completato', 'Completato'),
        ],
        default='bozza'
    )

    class Meta:
        verbose_name = "Mio Modello"
        verbose_name_plural = "Miei Modelli"
        ordering = ['-created_at']

    def __str__(self):
        return self.nome

    # OBBLIGATORIO: per navigazione e QR Code
    def get_absolute_url(self):
        return reverse('nome_app:miomodello_detail', kwargs={'pk': self.pk})

    # OBBLIGATORIO: per ricerca globale
    @classmethod
    def get_search_fields(cls):
        """Campi in cui cercare"""
        return ['nome', 'descrizione']

    def get_search_result_display(self):
        """Testo mostrato nei risultati di ricerca"""
        return f"{self.nome} - {self.get_stato_display()}"
```

### REGOLA 2: Usare BaseModelWithCode per oggetti con codice progressivo

```python
from core.models import BaseModelWithCode
from core.mixins.model_mixins import AllegatiMixin, PDFMixin


class Ordine(BaseModelWithCode, AllegatiMixin, PDFMixin):
    """
    Modello con codice auto-generato (es: ORD-20260115-0001)
    """

    CODE_PREFIX = "ORD"  # Prefisso codice
    CODE_LENGTH = 4      # Lunghezza parte numerica

    cliente = models.ForeignKey('anagrafica.Cliente', on_delete=models.PROTECT)
    data = models.DateField("Data Ordine")
    totale = models.DecimalField("Totale", max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = "Ordine"
        verbose_name_plural = "Ordini"

    def __str__(self):
        return f"{self.codice} - {self.cliente}"

    def get_absolute_url(self):
        return reverse('vendite:ordine_detail', kwargs={'pk': self.pk})

    # Per PDFMixin
    def get_pdf_template_name(self):
        return 'vendite/pdf/ordine_pdf.html'

    def get_pdf_context(self):
        return {
            'object': self,
            'righe': self.righe.all(),
            'azienda': settings.AZIENDA_INFO,
        }

    def get_pdf_filename(self):
        return f"ordine_{self.codice}.pdf"
```

### Mixins Disponibili (da usare quando servono)

| Mixin | Quando Usarlo |
|-------|---------------|
| `AllegatiMixin` | **SEMPRE** - Quasi tutti i model necessitano allegati |
| `PDFMixin` | Quando serve generare PDF del record |
| `QRCodeMixin` | Quando serve QR Code per accesso rapido |
| `AuditMixin` | Quando serve tracciare tutte le modifiche |

---

## Views - Standard Obbligatori

### REGOLA 1: Usare i View Mixins del core

```python
# nome_app/views.py

from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.contenttypes.models import ContentType

from core.mixins.view_mixins import (
    PermissionRequiredMixin,      # OBBLIGATORIO per controllo accessi
    SetCreatedByMixin,            # OBBLIGATORIO per tracking utente
    FormValidMessageMixin,        # Messaggi successo
    FormInvalidMessageMixin,      # Messaggi errore
    SearchMixin,                  # Ricerca nella lista
    CustomPaginationMixin,        # Paginazione
    BreadcrumbMixin,              # Breadcrumb
)

from .models import MioModello
from .forms import MioModelloForm


class MioModelloListView(PermissionRequiredMixin, SearchMixin, CustomPaginationMixin, ListView):
    """
    Vista lista con ricerca e paginazione.
    """
    model = MioModello
    template_name = 'nome_app/list.html'
    context_object_name = 'objects'
    permission_required = 'nome_app.view_miomodello'

    # SearchMixin config
    search_fields = ['nome', 'descrizione']

    # CustomPaginationMixin config
    default_page_size = 20
    max_page_size = 100

    def get_queryset(self):
        """Filtra solo record attivi"""
        return super().get_queryset().filter(is_active=True)


class MioModelloDetailView(PermissionRequiredMixin, DetailView):
    """
    Vista dettaglio con supporto allegati e QR Code.
    DEVE passare content_type_id per allegati/QR.
    """
    model = MioModello
    template_name = 'nome_app/detail.html'
    context_object_name = 'object'
    permission_required = 'nome_app.view_miomodello'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # OBBLIGATORIO: per gestione allegati e QR Code
        content_type = ContentType.objects.get_for_model(self.model)
        context['content_type_id'] = content_type.id

        # URL per azioni
        context['edit_url'] = reverse_lazy('nome_app:miomodello_update', kwargs={'pk': self.object.pk})
        context['delete_url'] = reverse_lazy('nome_app:miomodello_delete', kwargs={'pk': self.object.pk})
        context['back_url'] = reverse_lazy('nome_app:miomodello_list')

        return context


class MioModelloCreateView(
    PermissionRequiredMixin,
    SetCreatedByMixin,           # Imposta created_by automaticamente
    FormValidMessageMixin,
    FormInvalidMessageMixin,
    CreateView
):
    """
    Vista creazione con tracking utente e messaggi.
    """
    model = MioModello
    form_class = MioModelloForm
    template_name = 'nome_app/form.html'
    permission_required = 'nome_app.add_miomodello'
    success_message = "Elemento creato con successo!"

    def get_success_url(self):
        return reverse_lazy('nome_app:miomodello_detail', kwargs={'pk': self.object.pk})


class MioModelloUpdateView(
    PermissionRequiredMixin,
    FormValidMessageMixin,
    FormInvalidMessageMixin,
    UpdateView
):
    """
    Vista modifica.
    """
    model = MioModello
    form_class = MioModelloForm
    template_name = 'nome_app/form.html'
    permission_required = 'nome_app.change_miomodello'
    success_message = "Elemento modificato con successo!"

    def form_valid(self, form):
        """Imposta updated_by"""
        form.instance.updated_by = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('nome_app:miomodello_detail', kwargs={'pk': self.object.pk})


class MioModelloDeleteView(PermissionRequiredMixin, DeleteView):
    """
    Vista eliminazione (soft delete consigliato).
    """
    model = MioModello
    template_name = 'nome_app/confirm_delete.html'
    permission_required = 'nome_app.delete_miomodello'
    success_url = reverse_lazy('nome_app:miomodello_list')

    def form_valid(self, form):
        """Usa soft delete invece di delete reale"""
        self.object.soft_delete(user=self.request.user)
        return redirect(self.get_success_url())
```

### Vista per generazione PDF

```python
from django.http import HttpResponse
from core.views import genera_pdf_da_template


class MioModelloPDFView(PermissionRequiredMixin, DetailView):
    """
    Genera PDF del record.
    """
    model = MioModello
    permission_required = 'nome_app.view_miomodello'

    def get(self, request, *args, **kwargs):
        obj = self.get_object()

        context = {
            'object': obj,
            'request': request,
        }

        return genera_pdf_da_template(
            template_name='nome_app/pdf/miomodello_pdf.html',
            context=context,
            filename=f"documento_{obj.pk}.pdf"
        )
```

### Vista per export Excel

```python
from core.views import genera_excel_da_queryset


class MioModelloExcelView(PermissionRequiredMixin, View):
    """
    Esporta lista in Excel.
    """
    permission_required = 'nome_app.view_miomodello'

    def get(self, request):
        queryset = MioModello.objects.filter(is_active=True)

        columns = [
            ('nome', 'Nome'),
            ('descrizione', 'Descrizione'),
            ('stato', 'Stato'),
            ('created_at', 'Data Creazione'),
        ]

        return genera_excel_da_queryset(
            queryset=queryset,
            columns=columns,
            filename='export_miomodello.xlsx',
            sheet_name='Dati'
        )
```

---

## Templates - Standard Obbligatori

### Stile Dashboard e Liste - Classi CSS Standard

Per tutte le pagine dashboard e liste, usare **esclusivamente** le classi CSS definite in `static/css/style.css`.
**NON creare CSS custom** nei template. Riferimento: `acquisti/templates/acquisti/dashboard.html`

#### Struttura Header
```html
<div class="d-flex justify-content-between align-items-center mb-4">
    <h1 class="h3 mb-0">
        <i class="bi bi-icon-name me-2 text-primary"></i>Titolo Pagina
    </h1>
    <div class="btn-group">
        <a href="..." class="btn btn-outline-secondary">Azione Secondaria</a>
        <a href="..." class="btn btn-primary"><i class="bi bi-plus-lg"></i> Azione Primaria</a>
    </div>
</div>
```

#### Card Statistiche (4 colonne)
```html
<div class="row mb-4">
    <div class="col-md-3">
        <div class="card">
            <div class="card-header">
                <i class="bi bi-icon me-2"></i>Label
            </div>
            <div class="card-body text-center">
                <span class="widget-stat text-success">Valore</span>
            </div>
        </div>
    </div>
    <!-- Ripetere per altre 3 card con classi: second-color, third-color, fourth-color -->
</div>
```

#### Widget Dashboard
```html
<div class="dashboard-widget">
    <div class="widget-header">
        <h5 class="widget-title">
            <i class="bi bi-icon text-primary me-2"></i>Titolo Widget
        </h5>
    </div>
    <!-- Contenuto: table-responsive con table table-hover -->
</div>
```

#### Classi CSS Disponibili (da style.css)
| Classe | Uso |
|--------|-----|
| `.widget-stat` | Numeri grandi nelle card statistiche |
| `.dashboard-widget` | Container widget con sfondo bianco e shadow |
| `.widget-header` | Header del widget |
| `.widget-title` | Titolo h5 nel widget header |
| `.second-color` | Card header verde |
| `.third-color` | Card header giallo |
| `.fourth-color` | Card header arancione |

#### Icone
Usare **Bootstrap Icons** (`bi bi-*`), NON Font Awesome (`fas fa-*`).

---

### REGOLA 1: Pagine Dettaglio - Estendere `base_detail.html`

```html
{# nome_app/templates/nome_app/detail.html #}

{% extends "commons_templates/base_detail.html" %}
{% load static %}

{% block breadcrumb %}
<li class="breadcrumb-item"><a href="{% url 'nome_app:miomodello_list' %}">Miei Modelli</a></li>
<li class="breadcrumb-item active">{{ object.nome }}</li>
{% endblock %}

{% block page_title %}{{ object.nome }}{% endblock %}

{% block page_subtitle %}
<p class="text-muted mb-0">
    <i class="bi bi-calendar3"></i> Creato il {{ object.created_at|date:"d/m/Y" }}
</p>
{% endblock %}

{% block status_badge %}
<span class="badge bg-{% if object.stato == 'attivo' %}success{% elif object.stato == 'bozza' %}warning{% else %}secondary{% endif %}">
    {{ object.get_stato_display }}
</span>
{% endblock %}

{% block detail_content %}
{# Contenuto principale - 100% personalizzabile #}
<div class="row">
    <div class="col-md-6">
        <h5>Informazioni Generali</h5>
        <dl class="row">
            <dt class="col-sm-4">Nome</dt>
            <dd class="col-sm-8">{{ object.nome }}</dd>

            <dt class="col-sm-4">Descrizione</dt>
            <dd class="col-sm-8">{{ object.descrizione|default:"-" }}</dd>

            <dt class="col-sm-4">Stato</dt>
            <dd class="col-sm-8">{{ object.get_stato_display }}</dd>
        </dl>
    </div>

    <div class="col-md-6">
        <h5>Metadati</h5>
        <dl class="row">
            <dt class="col-sm-4">Creato da</dt>
            <dd class="col-sm-8">{{ object.created_by.get_full_name|default:object.created_by.username|default:"-" }}</dd>

            <dt class="col-sm-4">Data creazione</dt>
            <dd class="col-sm-8">{{ object.created_at|date:"d/m/Y H:i" }}</dd>

            <dt class="col-sm-4">Ultima modifica</dt>
            <dd class="col-sm-8">{{ object.updated_at|date:"d/m/Y H:i" }}</dd>
        </dl>
    </div>
</div>
{% endblock %}

{% block custom_actions %}
{# Azioni aggiuntive nella sidebar #}
<a href="{% url 'nome_app:miomodello_pdf' object.pk %}" class="list-group-item list-group-item-action" target="_blank">
    <i class="bi bi-file-pdf text-danger"></i> Scarica PDF
</a>
{% endblock %}

{% block extra_content %}
{# Contenuto extra sotto il card principale #}
{% if object.relazioni.exists %}
<div class="card shadow-sm mt-4">
    <div class="card-header">
        <h5 class="mb-0"><i class="bi bi-link-45deg"></i> Elementi Correlati</h5>
    </div>
    <div class="card-body">
        {# Tabella elementi correlati #}
    </div>
</div>
{% endif %}
{% endblock %}

{% block sidebar_extra %}
{# Card extra nella sidebar #}
<div class="card shadow-sm mt-3">
    <div class="card-header bg-warning text-dark">
        <h6 class="mb-0"><i class="bi bi-star-fill"></i> Statistiche</h6>
    </div>
    <div class="list-group list-group-flush">
        <div class="list-group-item">
            <small class="text-muted">Totale allegati</small>
            <span class="float-end badge bg-primary">{{ object.conta_allegati }}</span>
        </div>
    </div>
</div>
{% endblock %}
```

### REGOLA 2: Pagine Lista - Usare componenti standard

```html
{# nome_app/templates/nome_app/list.html #}

{% extends "base.html" %}
{% load static %}

{% block title %}Elenco Miei Modelli{% endblock %}

{% block content %}
<div class="container-fluid mt-4">
    {# Breadcrumb #}
    {% include 'components/breadcrumb.html' with breadcrumbs=breadcrumbs %}

    {# Header con ricerca #}
    <div class="d-flex justify-content-between align-items-center mb-4">
        <h1>Miei Modelli</h1>
        <a href="{% url 'nome_app:miomodello_create' %}" class="btn btn-primary">
            <i class="bi bi-plus-circle"></i> Nuovo
        </a>
    </div>

    {# Alerts #}
    {% include 'components/alerts.html' %}

    {# Filtri e ricerca #}
    <div class="card shadow-sm mb-4">
        <div class="card-body">
            <form method="get" class="row g-3">
                <div class="col-md-4">
                    <input type="text" name="q" class="form-control"
                           placeholder="Cerca..." value="{{ search_query }}">
                </div>
                <div class="col-md-3">
                    <select name="stato" class="form-select">
                        <option value="">Tutti gli stati</option>
                        <option value="bozza">Bozza</option>
                        <option value="attivo">Attivo</option>
                        <option value="completato">Completato</option>
                    </select>
                </div>
                <div class="col-md-2">
                    <button type="submit" class="btn btn-outline-primary w-100">
                        <i class="bi bi-search"></i> Cerca
                    </button>
                </div>
            </form>
        </div>
    </div>

    {# Tabella risultati o empty state #}
    {% if objects %}
    <div class="card shadow-sm">
        <div class="table-responsive">
            <table class="table table-hover mb-0">
                <thead class="table-light">
                    <tr>
                        <th>Nome</th>
                        <th>Stato</th>
                        <th>Allegati</th>
                        <th>Data Creazione</th>
                        <th class="text-end">Azioni</th>
                    </tr>
                </thead>
                <tbody>
                    {% for obj in objects %}
                    <tr>
                        <td>
                            <a href="{{ obj.get_absolute_url }}">{{ obj.nome }}</a>
                        </td>
                        <td>
                            <span class="badge bg-{% if obj.stato == 'attivo' %}success{% else %}secondary{% endif %}">
                                {{ obj.get_stato_display }}
                            </span>
                        </td>
                        <td>
                            {% if obj.ha_allegati %}
                            <span class="badge bg-primary">{{ obj.conta_allegati }}</span>
                            {% else %}
                            <span class="text-muted">-</span>
                            {% endif %}
                        </td>
                        <td>{{ obj.created_at|date:"d/m/Y" }}</td>
                        <td class="text-end">
                            <div class="btn-group btn-group-sm">
                                <a href="{{ obj.get_absolute_url }}" class="btn btn-outline-primary" title="Visualizza">
                                    <i class="bi bi-eye"></i>
                                </a>
                                <a href="{% url 'nome_app:miomodello_update' obj.pk %}" class="btn btn-outline-warning" title="Modifica">
                                    <i class="bi bi-pencil"></i>
                                </a>
                            </div>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>

    {# Paginazione #}
    <div class="mt-4">
        {% include 'components/pagination.html' with page_obj=page_obj %}
    </div>

    {% else %}
    {# Empty state #}
    {% include 'components/empty_state.html' with config=empty_config %}
    {% endif %}
</div>
{% endblock %}
```

### REGOLA 3: Form - Usare il componente form_layout

```html
{# nome_app/templates/nome_app/form.html #}

{% extends "base.html" %}
{% load crispy_forms_tags %}

{% block title %}{% if object %}Modifica{% else %}Nuovo{% endif %} Elemento{% endblock %}

{% block content %}
{% include 'components/form_layout.html' with form=form config=form_config %}
{% endblock %}
```

E nella view passare la configurazione:

```python
def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    context['form_config'] = {
        'title': 'Nuovo Elemento' if not self.object else f'Modifica {self.object}',
        'subtitle': 'Compila tutti i campi obbligatori',
        'submit_text': 'Salva',
        'cancel_url': 'nome_app:miomodello_list',
    }
    return context
```

### REGOLA 4: Template PDF

```html
{# nome_app/templates/nome_app/pdf/miomodello_pdf.html #}

<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{{ object.nome }}</title>
    <style>
        @page {
            size: A4;
            margin: 2cm;
        }
        body {
            font-family: Arial, sans-serif;
            font-size: 12px;
            line-height: 1.4;
        }
        .header {
            text-align: center;
            margin-bottom: 20px;
            border-bottom: 2px solid #5585b5;
            padding-bottom: 10px;
        }
        .header h1 {
            color: #5585b5;
            margin: 0;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
        }
        th, td {
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }
        th {
            background-color: #5585b5;
            color: white;
        }
        .footer {
            position: fixed;
            bottom: 0;
            width: 100%;
            text-align: center;
            font-size: 10px;
            color: #666;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>{{ object.nome }}</h1>
        <p>Generato il {{ today|date:"d/m/Y H:i" }}</p>
    </div>

    <h2>Dettagli</h2>
    <table>
        <tr>
            <th width="30%">Campo</th>
            <th>Valore</th>
        </tr>
        <tr>
            <td>Nome</td>
            <td>{{ object.nome }}</td>
        </tr>
        <tr>
            <td>Descrizione</td>
            <td>{{ object.descrizione|default:"-" }}</td>
        </tr>
        <tr>
            <td>Stato</td>
            <td>{{ object.get_stato_display }}</td>
        </tr>
        <tr>
            <td>Data Creazione</td>
            <td>{{ object.created_at|date:"d/m/Y H:i" }}</td>
        </tr>
    </table>

    <div class="footer">
        <p>ModularBEF - Documento generato automaticamente</p>
    </div>
</body>
</html>
```

---

## Funzionalità Core Disponibili

### Generazione Documenti

```python
from core.views import (
    genera_pdf_da_template,      # PDF da template HTML
    genera_pdf_da_html,          # PDF da stringa HTML
    genera_excel_da_queryset,    # Excel da queryset
    genera_excel_personalizzato, # Excel multi-foglio
    genera_csv_da_queryset,      # CSV da queryset
    genera_xml_fattura_elettronica,  # XML Fattura SDI
    get_export_response,         # Utility generica
)
```

### Gestione Allegati (automatica con AllegatiMixin)

```python
# Nel model che eredita da AllegatiMixin:
obj.allegati                          # QuerySet allegati
obj.aggiungi_allegato(file, desc, user)  # Aggiunge allegato
obj.get_allegati_pdf()                # Solo PDF
obj.get_allegati_immagini()           # Solo immagini
obj.get_allegati_documenti()          # PDF, DOC, XLS
obj.conta_allegati()                  # Conteggio
obj.ha_allegati()                     # Boolean
```

### Gestione QR Code

```python
# Nel model che eredita da QRCodeMixin:
obj.get_qr_code_data()    # URL completo per QR
obj.get_qr_code_url()     # URL endpoint QR
obj.generate_qr_code()    # Genera QR SVG/PNG
```

### Registrazione per Ricerca Globale

```python
# In apps.py ready():
from core.search import SearchRegistry

SearchRegistry.register(
    model=MioModello,
    category='Categoria',
    icon='bi-icon-name',
    priority=5
)
```

### Registrazione per Permessi

```python
# In core/permissions_registry.py, aggiungere:
registry.register(
    app_label="nome_app",
    model_name="miomodello",
    display_name="Miei Modelli",
    category="📦 Nome Categoria",
    icon="bi-box",
)
```

---

## Checklist Nuova App

### Prima di iniziare
- [ ] Hai creato l'app con `startapp`
- [ ] Hai aggiunto l'app a `INSTALLED_APPS`
- [ ] Hai configurato `apps.py` con `ready()` per SearchRegistry

### Models
- [ ] Tutti i model ereditano da `BaseModel` o `BaseModelWithCode`
- [ ] Model user-facing hanno `AllegatiMixin`
- [ ] Ogni model ha `get_absolute_url()`
- [ ] Ogni model ha `get_search_fields()` e `get_search_result_display()`
- [ ] Model registrati in `SearchRegistry` (apps.py)
- [ ] Model registrati in `permissions_registry.py`

### Views
- [ ] Tutte le view usano `PermissionRequiredMixin`
- [ ] CreateView usa `SetCreatedByMixin`
- [ ] UpdateView imposta `updated_by`
- [ ] DetailView passa `content_type_id` nel context
- [ ] DeleteView usa soft delete

### Templates
- [ ] Pagine dettaglio estendono `commons_templates/base_detail.html`
- [ ] Pagine lista usano `components/pagination.html`
- [ ] Form usano `components/form_layout.html`
- [ ] Alerts usano `components/alerts.html`
- [ ] Empty state usa `components/empty_state.html`

### URLs
- [ ] URLs configurati con `app_name`
- [ ] Pattern naming coerente: `model_list`, `model_detail`, `model_create`, `model_update`, `model_delete`

### Admin (opzionale)
- [ ] Model registrati in admin con filtri utili

### Test
- [ ] Test per views principali
- [ ] Test per permessi

---

## Stato Conformità App Esistenti

Di seguito lo stato di conformità delle app esistenti rispetto agli standard del core.

### App Conformi

| App | BaseModel | AllegatiMixin | SearchMixin | SearchRegistry | Note |
|-----|-----------|---------------|-------------|----------------|------|
| **users** | TimestampMixin | AllegatiMixin | - | - | Usa mixin core per User esteso |
| **mail** | BaseModel/BaseModelSimple | AllegatiMixin | - | - | Pienamente conforme |

### App Integrate con Core (Febbraio 2026)

| App | AllegatiMixin | SearchMixin | SearchRegistry | Note |
|-----|---------------|-------------|----------------|------|
| **anagrafica** | Cliente, Fornitore | Cliente, Fornitore | Registrati | Integrato con sistema allegati e ricerca globale |
| **automezzi** | Automezzo, Manutenzione, Rifornimento, EventoAutomezzo | Automezzo | Registrato | Usa mixin dal core |
| **stabilimenti** | Stabilimento, CostiStabilimento | Stabilimento, CostiStabilimento, DocStabilimento | Registrati | Integrato con sistema allegati e ricerca |
| **payroll** | - | BustaPaga | Registrato | Solo ricerca globale, no allegati |
| **trasporti** | Via GenericRelation | RichiestaTrasporto | Registrato | Usa ProcurementTargetMixin |
| **acquisti** | Via GenericRelation | OrdineAcquisto | Registrato | Integrato con ricerca globale |

### Stato Conformità Template Dettaglio

I template di dettaglio dovrebbero estendere `commons_templates/base_detail.html` per garantire:
- Sidebar con azioni standard (Modifica, Elimina, Torna alla lista)
- Gestione allegati integrata
- Generazione QR Code
- Layout consistente

#### Template Conformi (estendono `base_detail.html`)

| Template | App | Note |
|----------|-----|------|
| `dettaglio_stabilimento.html` | stabilimenti | ✅ Conforme |
| `affidamento_detail.html` | automezzi | ✅ Conforme |
| `automezzo_detail.html` | automezzi | ✅ Conforme |
| `richiesta_detail.html` | preventivi_beni | ✅ Conforme |
| `offerta_detail.html` | trasporti | ✅ Conforme |
| `richiesta_detail.html` | trasporti | ✅ Conforme |
| `dettaglio_ordine.html` | acquisti | ✅ Conforme |
| `promemoria_detail.html` | mail | ✅ Conforme |
| `user_detail.html` | users (templates/) | ✅ Conforme |

#### Template Specializzati (layout custom giustificato)

| Template | App | Motivo Layout Custom |
|----------|-----|---------------------|
| `manutenzione_detail.html` | automezzi | Layout 3 card orizzontali per workflow |
| `dettaglio_costo.html` | stabilimenti | Timeline e riepilogo economico |
| `dettaglio_sessione.html` | allestimento | Workflow interattivo con progress bar |
| `busta_paga_detail.html` | payroll | Cedolino paga con sezioni competenze/trattenute |
| `clienti/dettaglio.html` | anagrafica | Dashboard credito cliente con progress bar |
| `fornitori/dettaglio.html` | anagrafica | Layout anagrafico specializzato |

**Nota**: I template specializzati hanno layout custom giustificato dalla complessità funzionale. Non è necessario migrarli a `base_detail.html` se la funzionalità richiede un layout diverso.

### Note sulla Migrazione Models

Le app `anagrafica`, `payroll`, e `stabilimenti` **non** ereditano da `BaseModel` per motivi di compatibilità con le strutture dati esistenti. Utilizzano nomi di campo leggermente diversi:

- `attivo` invece di `is_active`
- `data_creazione` invece di `created_at` (stabilimenti)
- `creato_da` invece di `created_by` (stabilimenti)

**Per nuove app**: seguire sempre gli standard `BaseModel` documentati sopra.

**Per migrare app esistenti a BaseModel completo**: richiederebbe migrazioni database per rinominare campi e aggiornare tutte le views/templates che li utilizzano.

---

## Note Finali

### Cosa NON fare

1. **MAI** creare model senza ereditare da `BaseModel`
2. **MAI** creare pagine dettaglio senza supporto allegati/QR
3. **MAI** duplicare codice già presente nel core
4. **MAI** creare form di upload allegati custom (usare il sistema centralizzato)
5. **MAI** implementare ricerca custom (usare `SearchRegistry`)
6. **MAI** creare PDF senza usare `genera_pdf_da_template`

### Best Practices

1. Usare sempre soft delete invece di delete reale
2. Passare sempre `content_type_id` nelle pagine dettaglio
3. Registrare sempre i model nel `SearchRegistry`
4. Usare i View Mixins per codice DRY
5. Testare sempre i permessi

---

*Ultimo aggiornamento: Febbraio 2026*
