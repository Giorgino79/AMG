"""
Anagrafica Views - ModularBEF
=============================

Views per gestione Clienti e Fornitori: CRUD, Dashboard, API e PDF.
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse_lazy
from django.http import JsonResponse, HttpResponse
from django.db.models import Q, Count
from django.utils import timezone

from core.pdf_generator import generate_pdf_response

from .models import Cliente, Fornitore
from .forms import ClienteForm, FornitoreForm


# ============================================================================
# MIXIN
# ============================================================================

class AnagraficaAccessMixin(LoginRequiredMixin):
    """Mixin per controllo accesso alle viste anagrafica."""
    login_url = "/admin/login/"


# ============================================================================
# DASHBOARD
# ============================================================================

@login_required
def dashboard(request):
    """Dashboard principale anagrafica con statistiche."""

    # Statistiche clienti
    clienti_totali = Cliente.objects.filter(attivo=True).count()
    clienti_nuovi = Cliente.objects.filter(
        attivo=True,
        created_at__gte=timezone.now() - timezone.timedelta(days=30)
    ).count()

    # Statistiche fornitori
    fornitori_totali = Fornitore.objects.filter(attivo=True).count()
    fornitori_per_categoria = Fornitore.objects.filter(attivo=True).values(
        "categoria"
    ).annotate(count=Count("id")).order_by("-count")[:5]

    # Ultimi clienti e fornitori
    ultimi_clienti = Cliente.objects.filter(attivo=True).order_by("-created_at")[:5]
    ultimi_fornitori = Fornitore.objects.filter(attivo=True).order_by("-created_at")[:5]

    context = {
        "clienti_totali": clienti_totali,
        "clienti_nuovi": clienti_nuovi,
        "fornitori_totali": fornitori_totali,
        "fornitori_per_categoria": fornitori_per_categoria,
        "ultimi_clienti": ultimi_clienti,
        "ultimi_fornitori": ultimi_fornitori,
    }
    return render(request, "anagrafica/dashboard.html", context)


# ============================================================================
# CLIENTI - CRUD
# ============================================================================

class ClienteListView(AnagraficaAccessMixin, ListView):
    """Elenco clienti con ricerca e filtri."""

    model = Cliente
    template_name = "anagrafica/clienti/elenco.html"
    context_object_name = "clienti"
    paginate_by = 20

    def get_queryset(self):
        queryset = Cliente.objects.all()

        # Filtro credito
        credito = self.request.GET.get("credito", "").strip()
        if credito == "con_limite":
            queryset = queryset.filter(limite_credito__gt=0)
        elif credito == "senza_limite":
            queryset = queryset.filter(limite_credito=0)

        # Ricerca
        search = self.request.GET.get("search", "").strip()
        if search:
            queryset = queryset.filter(
                Q(ragione_sociale__icontains=search) |
                Q(email__icontains=search) |
                Q(telefono__icontains=search) |
                Q(partita_iva__icontains=search) |
                Q(codice_fiscale__icontains=search)
            )

        # Ordinamento
        ordine = self.request.GET.get("ordine", "ragione_sociale")
        if ordine in ["ragione_sociale", "-ragione_sociale", "created_at", "-created_at", "citta", "-citta"]:
            queryset = queryset.order_by(ordine)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search_query"] = self.request.GET.get("search", "")
        context["credito_filter"] = self.request.GET.get("credito", "")
        context["ordine"] = self.request.GET.get("ordine", "ragione_sociale")
        context["totale_crediti"] = sum(
            c.limite_credito for c in Cliente.objects.filter(limite_credito__gt=0)
        )
        return context


class ClienteDetailView(AnagraficaAccessMixin, DetailView):
    """Dettaglio cliente."""

    model = Cliente
    template_name = "anagrafica/clienti/dettaglio.html"
    context_object_name = "cliente"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cliente = self.object

        # Configurazione per detail_layout
        context["detail_config"] = {
            "title": cliente.ragione_sociale,
            "subtitle": f"Cliente - {cliente.get_tipo_pagamento_display()}",
            "sections": [
                {
                    "title": "Dati Anagrafici",
                    "icon": "bi-person-vcard",
                    "fields": [
                        {"label": "Ragione Sociale", "value": cliente.ragione_sociale},
                        {"label": "Indirizzo", "value": cliente.get_indirizzo_completo()},
                    ]
                },
                {
                    "title": "Contatti",
                    "icon": "bi-telephone",
                    "fields": [
                        {"label": "Telefono", "value": cliente.telefono},
                        {"label": "Email", "value": cliente.email},
                    ]
                },
                {
                    "title": "Dati Fiscali",
                    "icon": "bi-receipt",
                    "fields": [
                        {"label": "Partita IVA", "value": cliente.partita_iva or "-"},
                        {"label": "Codice Fiscale", "value": cliente.codice_fiscale or "-"},
                        {"label": "Codice Univoco SDI", "value": cliente.codice_univoco or "-"},
                        {"label": "PEC", "value": cliente.pec or "-"},
                    ]
                },
                {
                    "title": "Condizioni Commerciali",
                    "icon": "bi-truck",
                    "fields": [
                        {"label": "Tipo Pagamento", "value": cliente.get_tipo_pagamento_display()},
                    ]
                },
            ],
            "show_allegati": False,
            "show_qrcode": False,
            "back_url": "anagrafica:cliente_list",
            "edit_url": "anagrafica:cliente_update",
            "delete_url": "anagrafica:cliente_delete",
            "pdf_url": "anagrafica:cliente_pdf",
        }

        # Note se presenti
        if cliente.note:
            context["detail_config"]["sections"].append({
                "title": "Note",
                "icon": "bi-sticky",
                "html": f"<p>{cliente.note}</p>"
            })

        return context


class ClienteCreateView(AnagraficaAccessMixin, CreateView):
    """Creazione nuovo cliente."""

    model = Cliente
    form_class = ClienteForm
    template_name = "anagrafica/clienti/nuovo.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["titolo"] = "Nuovo Cliente"
        context["submit_text"] = "Crea Cliente"
        return context

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, f"Cliente '{form.instance.ragione_sociale}' creato con successo!")
        return super().form_valid(form)


class ClienteUpdateView(AnagraficaAccessMixin, UpdateView):
    """Modifica cliente esistente."""

    model = Cliente
    form_class = ClienteForm
    template_name = "anagrafica/clienti/modifica.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["titolo"] = f"Modifica Cliente: {self.object.ragione_sociale}"
        context["submit_text"] = "Salva Modifiche"
        return context

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        messages.success(self.request, f"Cliente '{form.instance.ragione_sociale}' modificato con successo!")
        return super().form_valid(form)


class ClienteDeleteView(AnagraficaAccessMixin, DeleteView):
    """Eliminazione cliente (soft delete)."""

    model = Cliente
    template_name = "anagrafica/clienti/elimina.html"
    success_url = reverse_lazy("anagrafica:cliente_list")

    def form_valid(self, form):
        cliente = self.object
        cliente.soft_delete(user=self.request.user)
        messages.success(self.request, f"Cliente '{cliente.ragione_sociale}' eliminato con successo!")
        return redirect(self.success_url)


# ============================================================================
# FORNITORI - CRUD
# ============================================================================

class FornitoreListView(AnagraficaAccessMixin, ListView):
    """Elenco fornitori con ricerca e filtri."""

    model = Fornitore
    template_name = "anagrafica/fornitori/elenco.html"
    context_object_name = "fornitori"
    paginate_by = 20

    def get_queryset(self):
        queryset = Fornitore.objects.all()

        # Filtro stato
        stato = self.request.GET.get("stato", "").strip()
        if stato == "attivi":
            queryset = queryset.filter(attivo=True)
        elif stato == "inattivi":
            queryset = queryset.filter(attivo=False)
        else:
            # Default: mostra tutti
            pass

        # Ricerca
        search = self.request.GET.get("search", "").strip()
        if search:
            queryset = queryset.filter(
                Q(ragione_sociale__icontains=search) |
                Q(email__icontains=search) |
                Q(telefono__icontains=search) |
                Q(partita_iva__icontains=search)
            )

        # Filtro categoria
        categoria = self.request.GET.get("categoria", "").strip()
        if categoria:
            queryset = queryset.filter(categoria=categoria)

        # Ordinamento
        ordine = self.request.GET.get("ordine", "ragione_sociale")
        if ordine in ["ragione_sociale", "-ragione_sociale", "created_at", "-created_at", "categoria"]:
            queryset = queryset.order_by(ordine)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search_query"] = self.request.GET.get("search", "")
        context["stato_filter"] = self.request.GET.get("stato", "")
        context["categoria_filtro"] = self.request.GET.get("categoria", "")
        context["ordine"] = self.request.GET.get("ordine", "ragione_sociale")
        context["categorie"] = Fornitore.CATEGORIA_CHOICES

        # Statistiche
        context["stats"] = {
            "totali": Fornitore.objects.count(),
            "attivi": Fornitore.objects.filter(attivo=True).count(),
            "inattivi": Fornitore.objects.filter(attivo=False).count(),
        }
        return context


class FornitoreDetailView(AnagraficaAccessMixin, DetailView):
    """Dettaglio fornitore."""

    model = Fornitore
    template_name = "anagrafica/fornitori/dettaglio.html"
    context_object_name = "fornitore"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        fornitore = self.object

        # Configurazione per detail_layout
        sections = [
            {
                "title": "Dati Anagrafici",
                "icon": "bi-building",
                "fields": [
                    {"label": "Ragione Sociale", "value": fornitore.ragione_sociale},
                    {"label": "Indirizzo", "value": fornitore.get_indirizzo_completo()},
                    {"label": "Categoria", "value": fornitore.get_categoria_display(), "badge": True, "badge_color": "info"},
                ]
            },
            {
                "title": "Contatti",
                "icon": "bi-telephone",
                "fields": [
                    {"label": "Telefono", "value": fornitore.telefono},
                    {"label": "Email", "value": fornitore.email},
                ]
            },
            {
                "title": "Dati Fiscali",
                "icon": "bi-receipt",
                "fields": [
                    {"label": "Partita IVA", "value": fornitore.partita_iva},
                    {"label": "Codice Fiscale", "value": fornitore.codice_fiscale or "-"},
                    {"label": "PEC", "value": fornitore.pec or "-"},
                    {"label": "Codice Destinatario SDI", "value": fornitore.codice_destinatario or "-"},
                ]
            },
            {
                "title": "Dati Bancari",
                "icon": "bi-bank",
                "fields": [
                    {"label": "IBAN", "value": fornitore.iban or "-"},
                ]
            },
            {
                "title": "Condizioni di Pagamento",
                "icon": "bi-cash-stack",
                "fields": [
                    {"label": "Tipo Pagamento", "value": fornitore.get_tipo_pagamento_display()},
                    {"label": "Priorità Pagamento", "value": fornitore.get_priorita_pagamento_default_display()},
                ]
            },
        ]

        # Aggiungi sezione referente se presente
        if fornitore.has_referente():
            sections.append({
                "title": "Referente",
                "icon": "bi-person-badge",
                "fields": [
                    {"label": "Nome", "value": fornitore.referente_nome or "-"},
                    {"label": "Telefono", "value": fornitore.referente_telefono or "-"},
                    {"label": "Email", "value": fornitore.referente_email or "-"},
                ]
            })

        # Aggiungi note se presenti
        if fornitore.note:
            sections.append({
                "title": "Note",
                "icon": "bi-sticky",
                "html": f"<p>{fornitore.note}</p>"
            })

        context["detail_config"] = {
            "title": fornitore.ragione_sociale,
            "subtitle": f"Fornitore - {fornitore.get_categoria_display()}",
            "sections": sections,
            "show_allegati": False,
            "show_qrcode": False,
            "back_url": "anagrafica:fornitore_list",
            "edit_url": "anagrafica:fornitore_update",
            "delete_url": "anagrafica:fornitore_delete",
            "pdf_url": "anagrafica:fornitore_pdf",
        }

        return context


class FornitoreCreateView(AnagraficaAccessMixin, CreateView):
    """Creazione nuovo fornitore."""

    model = Fornitore
    form_class = FornitoreForm
    template_name = "anagrafica/fornitori/nuovo.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["titolo"] = "Nuovo Fornitore"
        context["submit_text"] = "Crea Fornitore"
        return context

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, f"Fornitore '{form.instance.ragione_sociale}' creato con successo!")
        return super().form_valid(form)


class FornitoreUpdateView(AnagraficaAccessMixin, UpdateView):
    """Modifica fornitore esistente."""

    model = Fornitore
    form_class = FornitoreForm
    template_name = "anagrafica/fornitori/modifica.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["titolo"] = f"Modifica Fornitore: {self.object.ragione_sociale}"
        context["submit_text"] = "Salva Modifiche"
        return context

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        messages.success(self.request, f"Fornitore '{form.instance.ragione_sociale}' modificato con successo!")
        return super().form_valid(form)


class FornitoreDeleteView(AnagraficaAccessMixin, DeleteView):
    """Eliminazione fornitore (soft delete)."""

    model = Fornitore
    template_name = "anagrafica/fornitori/elimina.html"
    success_url = reverse_lazy("anagrafica:fornitore_list")

    def form_valid(self, form):
        fornitore = self.object
        fornitore.soft_delete(user=self.request.user)
        messages.success(self.request, f"Fornitore '{fornitore.ragione_sociale}' eliminato con successo!")
        return redirect(self.success_url)


# ============================================================================
# PDF EXPORT
# ============================================================================

@login_required
def cliente_pdf(request, pk):
    """Genera PDF scheda cliente."""
    cliente = get_object_or_404(Cliente, pk=pk)

    data = [{
        "Campo": "Ragione Sociale",
        "Valore": cliente.ragione_sociale
    }, {
        "Campo": "Indirizzo",
        "Valore": cliente.get_indirizzo_completo(),
    }, {
    }, {
        "Campo": "Telefono",
        "Valore": cliente.telefono,
    }, {
        "Campo": "Email",
        "Valore": cliente.email,
    }, {
        "Campo": "Partita IVA",
        "Valore": cliente.partita_iva or "-",
    }, {
        "Campo": "Codice Fiscale",
        "Valore": cliente.codice_fiscale or "-",
    }, {
        "Campo": "Codice Univoco SDI",
        "Valore": cliente.codice_univoco or "-",
    }, {
        "Campo": "PEC",
        "Valore": cliente.pec or "-",
    }, {
        "Campo": "Tipo Pagamento",
        "Valore": cliente.get_tipo_pagamento_display(),
    }, 
    {
        "Campo": "Orario Consegna",
        "Valore": cliente.orario_consegna or "-",
    }]

    return generate_pdf_response(
        data=data,
        filename=f"cliente_{cliente.pk}",
        title=f"Scheda Cliente: {cliente.ragione_sociale}",
        headers=["Campo", "Valore"]
    )


@login_required
def fornitore_pdf(request, pk):
    """Genera PDF scheda fornitore."""
    fornitore = get_object_or_404(Fornitore, pk=pk)

    data = [{
        "Campo": "Ragione Sociale",
        "Valore": fornitore.ragione_sociale,
    }, {
        "Campo": "Indirizzo",
        "Valore": fornitore.get_indirizzo_completo(),
    }, {
        "Campo": "Categoria",
        "Valore": fornitore.get_categoria_display(),
    }, {
        "Campo": "Telefono",
        "Valore": fornitore.telefono,
    }, {
        "Campo": "Email",
        "Valore": fornitore.email,
    }, {
        "Campo": "Partita IVA",
        "Valore": fornitore.partita_iva,
    }, {
        "Campo": "Codice Fiscale",
        "Valore": fornitore.codice_fiscale or "-",
    }, {
        "Campo": "PEC",
        "Valore": fornitore.pec or "-",
    }, {
        "Campo": "Codice Destinatario SDI",
        "Valore": fornitore.codice_destinatario or "-",
    }, {
        "Campo": "IBAN",
        "Valore": fornitore.iban or "-",
    }, {
        "Campo": "Tipo Pagamento",
        "Valore": fornitore.get_tipo_pagamento_display(),
    }, {
        "Campo": "Priorità Pagamento",
        "Valore": fornitore.get_priorita_pagamento_default_display(),
    }, {
        "Campo": "Referente",
        "Valore": fornitore.referente_nome or "-",
    }, {
        "Campo": "Tel. Referente",
        "Valore": fornitore.referente_telefono or "-",
    }, {
        "Campo": "Email Referente",
        "Valore": fornitore.referente_email or "-",
    }]

    return generate_pdf_response(
        data=data,
        filename=f"fornitore_{fornitore.pk}",
        title=f"Scheda Fornitore: {fornitore.ragione_sociale}",
        headers=["Campo", "Valore"]
    )


@login_required
def clienti_lista_pdf(request):
    """Genera PDF elenco clienti."""
    clienti = Cliente.objects.filter(attivo=True).order_by("ragione_sociale")

    data = []
    for cliente in clienti:
        data.append({
            "Ragione Sociale": cliente.ragione_sociale,
            "Città": cliente.citta or "-",
            "Telefono": cliente.telefono,
            "Email": cliente.email,
            "P.IVA": cliente.partita_iva or "-",
            "Pagamento": cliente.get_tipo_pagamento_display(),
        })

    return generate_pdf_response(
        data=data,
        filename="cliente_list",
        title="Elenco Clienti",
        headers=["Ragione Sociale", "Città", "Telefono", "Email", "P.IVA", "Pagamento"]
    )


@login_required
def fornitori_lista_pdf(request):
    """Genera PDF elenco fornitori."""
    fornitori = Fornitore.objects.filter(attivo=True).order_by("ragione_sociale")

    data = []
    for fornitore in fornitori:
        data.append({
            "Ragione_sociale": fornitore.ragione_sociale,
            "Categoria": fornitore.get_categoria_display(),
            "Telefono": fornitore.telefono,
            "Email": fornitore.email,
            "P.IVA": fornitore.partita_iva,
            "Pagamento": fornitore.get_tipo_pagamento_display(),
        })

    return generate_pdf_response(
        data=data,
        filename="fornitore_list",
        title="Elenco Fornitori",
        headers=["Ragione Sociale", "Categoria", "Telefono", "Email", "P.IVA", "Pagamento"]
    )


# ============================================================================
# API
# ============================================================================

@login_required
def api_search(request):
    """API per ricerca globale anagrafica."""
    query = request.GET.get("q", "").strip()
    tipo = request.GET.get("tipo", "")

    if len(query) < 2:
        return JsonResponse({"results": []})

    results = []

    # Ricerca clienti
    if tipo in ["", "clienti"]:
        clienti = Cliente.objects.filter(
            attivo=True
        ).filter(
            Q(ragione_sociale__icontains=query) |
            Q(email__icontains=query) |
            Q(telefono__icontains=query)
        )[:10]

        for cliente in clienti:
            results.append({
                "tipo": "cliente",
                "id": str(cliente.pk),
                "ragione_sociale": cliente.ragione_sociale,
                "dettaglio": f"{cliente.email} - {cliente.telefono}",
                "url": cliente.get_absolute_url(),
            })

    # Ricerca fornitori
    if tipo in ["", "fornitori"]:
        fornitori = Fornitore.objects.filter(
            attivo=True
        ).filter(
            Q(ragione_sociale__icontains=query) |
            Q(email__icontains=query) |
            Q(telefono__icontains=query)
        )[:10]

        for fornitore in fornitori:
            results.append({
                "tipo": "fornitore",
                "id": str(fornitore.pk),
                "ragione_sociale": fornitore.ragione_sociale,
                "dettaglio": f"{fornitore.get_categoria_display()} - {fornitore.email}",
                "url": fornitore.get_absolute_url(),
            })

    return JsonResponse({"results": results})


@login_required
def api_stats(request):
    """API per statistiche dashboard."""
    stats = {
        "clienti_totali": Cliente.objects.filter(attivo=True).count(),
        "fornitori_totali": Fornitore.objects.filter(attivo=True).count(),
        "clienti_nuovi_mese": Cliente.objects.filter(
            attivo=True,
            created_at__gte=timezone.now() - timezone.timedelta(days=30)
        ).count(),
        "fornitori_nuovi_mese": Fornitore.objects.filter(
            attivo=True,
            created_at__gte=timezone.now() - timezone.timedelta(days=30)
        ).count(),
    }
    return JsonResponse(stats)


@login_required
def toggle_attivo(request, tipo, pk):
    """Toggle stato attivo/inattivo per cliente o fornitore."""
    if tipo == "cliente":
        obj = get_object_or_404(Cliente, pk=pk)
    elif tipo == "fornitore":
        obj = get_object_or_404(Fornitore, pk=pk)
    else:
        messages.error(request, "Tipo non valido")
        return redirect("anagrafica:dashboard")

    if obj.attivo:
        obj.attivo = False
        obj.save()
        stato = "disattivato"
    else:
        obj.attivo = True
        obj.save()
        stato = "attivato"

    messages.success(request, f"{tipo.capitalize()} {obj.ragione_sociale} {stato} con successo!")

    # Redirect alla lista appropriata
    if tipo == "cliente":
        return redirect("anagrafica:cliente_list")
    return redirect("anagrafica:fornitore_list")


# ============================================================================
# EXPORT CSV
# ============================================================================

@login_required
def export_clienti_csv(request):
    """Export clienti in formato CSV."""
    import csv

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="clienti.csv"'

    writer = csv.writer(response)
    writer.writerow([
        "Ragione Sociale", "Indirizzo", "CAP", "Città", 
        "Telefono", "Email", "P.IVA", "CF",
        "Codice Univoco", "PEC", "Tipo Pagamento",
        "Giorno Chiusura", "Orario Consegna", "Note"
    ])

    for cliente in Cliente.objects.filter(attivo=True).order_by("ragione_sociale"):
        writer.writerow([
            cliente.ragione_sociale,
            cliente.indirizzo,
            cliente.cap,
            cliente.citta,
            cliente.telefono,
            cliente.email,
            cliente.partita_iva,
            cliente.codice_fiscale,
            cliente.codice_univoco,
            cliente.pec,
            cliente.get_tipo_pagamento_display(),
            cliente.note,
        ])

    return response


@login_required
def export_fornitori_csv(request):
    """Export fornitori in formato CSV."""
    import csv

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="fornitori.csv"'

    writer = csv.writer(response)
    writer.writerow([
        "Ragione Sociale", "Indirizzo", "CAP", "Città",
        "Telefono", "Email", "P.IVA", "CF", "PEC",
        "Codice SDI", "IBAN", "Categoria",
        "Tipo Pagamento", "Priorità Pagamento",
        "Referente", "Tel. Referente", "Email Referente", "Note"
    ])

    for fornitore in Fornitore.objects.filter(attivo=True).order_by("ragione_sociale"):
        writer.writerow([
            fornitore.ragione_sociale,
            fornitore.indirizzo,
            fornitore.cap,
            fornitore.citta,
            fornitore.telefono,
            fornitore.email,
            fornitore.partita_iva,
            fornitore.codice_fiscale,
            fornitore.pec,
            fornitore.codice_destinatario,
            fornitore.iban,
            fornitore.get_categoria_display(),
            fornitore.get_tipo_pagamento_display(),
            fornitore.get_priorita_pagamento_default_display(),
            fornitore.referente_nome,
            fornitore.referente_telefono,
            fornitore.referente_email,
            fornitore.note,
        ])

    return response
