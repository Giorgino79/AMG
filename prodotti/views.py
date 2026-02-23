# prodotti/views.py
"""
PRODOTTI VIEWS - Anagrafica Prodotti
=====================================
Solo CRUD prodotti e categorie. No scorte, no prezzi.
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_http_methods
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
)
from django.contrib.auth.mixins import LoginRequiredMixin

from .models import Categoria, Prodotto
from .forms import CategoriaForm, ProdottoForm, ProdottoSearchForm
from ricezioni.models import Lotto


# ============================================================================
# DASHBOARD
# ============================================================================


@login_required
def dashboard_prodotti(request):
    """Dashboard principale prodotti"""

    stats = {
        "totale_categorie": Categoria.objects.count(),
        "categorie_attive": Categoria.objects.filter(attiva=True).count(),
        "totale_prodotti": Prodotto.objects.count(),
        "prodotti_attivi": Prodotto.objects.filter(attivo=True).count(),
        "novita": Prodotto.objects.filter(novita=True, attivo=True).count(),
        "in_evidenza": Prodotto.objects.filter(in_evidenza=True, attivo=True).count(),
    }

    # Ultimi prodotti inseriti
    ultimi_prodotti = Prodotto.objects.select_related(
        "categoria", "fornitore_principale"
    ).order_by("-created_at")[:10]

    # Categorie con conteggio prodotti
    categorie_con_conteggio = (
        Categoria.objects.filter(attiva=True)
        .annotate(num_prodotti=Count("prodotti", filter=Q(prodotti__attivo=True)))
        .order_by("-num_prodotti")[:10]
    )

    context = {
        "stats": stats,
        "ultimi_prodotti": ultimi_prodotti,
        "categorie_con_conteggio": categorie_con_conteggio,
    }

    return render(request, "prodotti/dashboard.html", context)


# ============================================================================
# VIEWS CATEGORIE
# ============================================================================


class CategoriaListView(LoginRequiredMixin, ListView):
    model = Categoria
    template_name = "prodotti/categoria_list.html"
    context_object_name = "categorie"
    paginate_by = 20
    ordering = ["nome_categoria"]

    def get_queryset(self):
        queryset = super().get_queryset().annotate(
            num_prodotti=Count("prodotti", filter=Q(prodotti__attivo=True))
        )
        search = self.request.GET.get("search")
        if search:
            queryset = queryset.filter(
                Q(nome_categoria__icontains=search) | Q(descrizione__icontains=search)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search"] = self.request.GET.get("search", "")
        context["total_categorie"] = self.get_queryset().count()
        context["categorie_attive"] = self.get_queryset().filter(attiva=True).count()
        return context


class CategoriaDetailView(LoginRequiredMixin, DetailView):
    model = Categoria
    template_name = "prodotti/categoria_detail.html"
    context_object_name = "categoria"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        categoria = self.object

        prodotti = categoria.prodotti.select_related(
            "fornitore_principale"
        ).order_by("nome_prodotto")
        paginator = Paginator(prodotti, 12)
        page_number = self.request.GET.get("page")
        context["prodotti_page"] = paginator.get_page(page_number)

        context["stats"] = {
            "totale_prodotti": categoria.prodotti.count(),
            "prodotti_attivi": categoria.prodotti.filter(attivo=True).count(),
        }

        from django.contrib.contenttypes.models import ContentType
        content_type = ContentType.objects.get_for_model(categoria)

        context["content_type_id"] = content_type.id
        context["edit_url"] = reverse_lazy("prodotti:categoria_update", kwargs={"pk": categoria.pk})
        context["delete_url"] = reverse_lazy("prodotti:categoria_delete", kwargs={"pk": categoria.pk})
        context["back_url"] = reverse_lazy("prodotti:categoria_list")

        return context


class CategoriaCreateView(LoginRequiredMixin, CreateView):
    model = Categoria
    form_class = CategoriaForm
    template_name = "prodotti/categoria_form.html"
    success_url = reverse_lazy("prodotti:categoria_list")

    def form_valid(self, form):
        messages.success(self.request, _("Categoria creata con successo."))
        return super().form_valid(form)


class CategoriaUpdateView(LoginRequiredMixin, UpdateView):
    model = Categoria
    form_class = CategoriaForm
    template_name = "prodotti/categoria_form.html"
    success_url = reverse_lazy("prodotti:categoria_list")

    def form_valid(self, form):
        messages.success(self.request, _("Categoria aggiornata con successo."))
        return super().form_valid(form)


class CategoriaDeleteView(LoginRequiredMixin, DeleteView):
    model = Categoria
    template_name = "prodotti/categoria_confirm_delete.html"
    success_url = reverse_lazy("prodotti:categoria_list")

    def delete(self, request, *args, **kwargs):
        categoria = self.get_object()
        if categoria.prodotti.exists():
            messages.error(
                request, _("Impossibile eliminare la categoria: contiene prodotti.")
            )
            return redirect("prodotti:categoria_detail", pk=categoria.pk)
        messages.success(request, _("Categoria eliminata con successo."))
        return super().delete(request, *args, **kwargs)


# ============================================================================
# VIEWS PRODOTTI
# ============================================================================


class ProdottoListView(LoginRequiredMixin, ListView):
    model = Prodotto
    template_name = "prodotti/prodotto_list.html"
    context_object_name = "prodotti"
    paginate_by = 24

    def get_queryset(self):
        queryset = Prodotto.objects.select_related("categoria", "fornitore_principale")

        form = ProdottoSearchForm(self.request.GET)
        if form.is_valid():
            search = form.cleaned_data.get("search")
            categoria = form.cleaned_data.get("categoria")
            fornitore = form.cleaned_data.get("fornitore")
            attivo = form.cleaned_data.get("attivo")
            tipo_prodotto = form.cleaned_data.get("tipo_prodotto")

            if search:
                queryset = queryset.filter(
                    Q(nome_prodotto__icontains=search)
                    | Q(ean__icontains=search)
                    | Q(codice_interno__icontains=search)
                    | Q(codice_fornitore__icontains=search)
                    | Q(descrizione_breve__icontains=search)
                )

            if categoria:
                queryset = queryset.filter(categoria=categoria)

            if fornitore:
                queryset = queryset.filter(fornitore_principale=fornitore)

            if attivo == "true":
                queryset = queryset.filter(attivo=True)
            elif attivo == "false":
                queryset = queryset.filter(attivo=False)

            if tipo_prodotto:
                queryset = queryset.filter(tipo_prodotto=tipo_prodotto)

        return queryset.order_by("nome_prodotto")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search_form"] = ProdottoSearchForm(self.request.GET)
        context["total_prodotti"] = self.get_queryset().count()

        all_prodotti = Prodotto.objects.all()
        context["stats"] = {
            "totale": all_prodotti.count(),
            "attivi": all_prodotti.filter(attivo=True).count(),
        }

        return context


class ProdottoDetailView(LoginRequiredMixin, DetailView):
    model = Prodotto
    template_name = "prodotti/prodotto_detail.html"
    context_object_name = "prodotto"

    def get_queryset(self):
        return Prodotto.objects.select_related("categoria", "fornitore_principale")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        prodotto = self.object

        from django.contrib.contenttypes.models import ContentType
        content_type = ContentType.objects.get_for_model(prodotto)

        context["content_type_id"] = content_type.id
        context["edit_url"] = reverse_lazy("prodotti:prodotto_update", kwargs={"pk": prodotto.pk})
        context["delete_url"] = reverse_lazy("prodotti:prodotto_delete", kwargs={"pk": prodotto.pk})
        context["back_url"] = reverse_lazy("prodotti:prodotto_list")

        # === SEZIONE LOTTI ===

        # Query base: lotti confermati di questo prodotto
        lotti_base = Lotto.objects.filter(
            prodotto=prodotto,
            ricezione__confermata=True,
        ).select_related(
            'stabilimento',
            'ricezione',
            'ricezione__ordine_acquisto',
        ).order_by('-ricezione__data_ricezione', '-data_creazione')

        # Form filtri (applicato solo ai lotti disponibili)
        from .forms import LottiProdottoFilterForm
        lotti_filter_form = LottiProdottoFilterForm(self.request.GET or None)

        # Lotti DISPONIBILI (non trattati HACCP, quantità residua > 0)
        lotti_disponibili_base = lotti_base.filter(trattato_haccp=False, quantita_residua__gt=0)
        lotti_filtrati = lotti_filter_form.filter_queryset(lotti_disponibili_base)

        # Lotti TRATTATI HACCP (ritirati dalla circolazione)
        lotti_trattati = lotti_base.filter(trattato_haccp=True).prefetch_related(
            'azioni_scadenza__utente'
        )

        # Calcola totali per stabilimento (solo disponibili)
        totali_per_stabilimento = lotti_filtrati.values(
            'stabilimento__nome',
            'stabilimento__codice_stabilimento'
        ).annotate(
            totale=Sum('quantita_residua')
        ).order_by('stabilimento__nome')

        context['lotti'] = lotti_filtrati
        context['lotti_trattati'] = lotti_trattati
        context['lotti_filter_form'] = lotti_filter_form
        context['totali_per_stabilimento'] = totali_per_stabilimento
        context['ha_lotti'] = lotti_filtrati.exists()
        context['ha_lotti_trattati'] = lotti_trattati.exists()

        return context


class ProdottoCreateView(LoginRequiredMixin, CreateView):
    model = Prodotto
    form_class = ProdottoForm
    template_name = "prodotti/prodotto_form.html"

    def get_success_url(self):
        return reverse_lazy("prodotti:prodotto_detail", kwargs={"pk": self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, _("Prodotto creato con successo."))
        return super().form_valid(form)


class ProdottoUpdateView(LoginRequiredMixin, UpdateView):
    model = Prodotto
    form_class = ProdottoForm
    template_name = "prodotti/prodotto_form.html"

    def get_success_url(self):
        return reverse_lazy("prodotti:prodotto_detail", kwargs={"pk": self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, _("Prodotto aggiornato con successo."))
        return super().form_valid(form)


class ProdottoDeleteView(LoginRequiredMixin, DeleteView):
    model = Prodotto
    template_name = "prodotti/prodotto_confirm_delete.html"
    success_url = reverse_lazy("prodotti:prodotto_list")

    def delete(self, request, *args, **kwargs):
        messages.success(request, _("Prodotto eliminato con successo."))
        return super().delete(request, *args, **kwargs)


# ============================================================================
# API VIEWS (per AJAX)
# ============================================================================


@login_required
@require_http_methods(["GET"])
def api_prodotto_info(request, prodotto_id):
    """API per informazioni prodotto (autocomplete, etc.)"""
    try:
        prodotto = get_object_or_404(
            Prodotto.objects.select_related("categoria", "fornitore_principale"),
            pk=prodotto_id,
        )
        data = {
            "id": prodotto.id,
            "nome": prodotto.nome_prodotto,
            "nome_completo": prodotto.nome_completo,
            "ean": prodotto.ean,
            "codice_interno": prodotto.codice_interno or "",
            "categoria": prodotto.categoria.nome_categoria,
            "fornitore": (
                prodotto.fornitore_principale.ragione_sociale
                if prodotto.fornitore_principale
                else ""
            ),
            "tipo_prodotto": prodotto.get_tipo_prodotto_display(),
            "misura": prodotto.get_misura_display(),
            "has_qrcode": prodotto.has_qrcode,
            "has_barcode": prodotto.has_barcode,
        }
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


@login_required
@require_http_methods(["GET"])
def api_prodotto_search(request):
    """API ricerca prodotti per autocomplete"""
    q = request.GET.get("q", "").strip()
    if len(q) < 2:
        return JsonResponse({"results": []})

    prodotti = Prodotto.objects.filter(
        attivo=True
    ).filter(
        Q(nome_prodotto__icontains=q)
        | Q(ean__icontains=q)
        | Q(codice_interno__icontains=q)
        | Q(codice_fornitore__icontains=q)
    ).select_related("categoria", "fornitore_principale")[:20]

    results = []
    for p in prodotti:
        results.append({
            "id": p.id,
            "nome": p.nome_prodotto,
            "codice_interno": p.codice_interno or "",
            "ean": p.ean or "",
            "fornitore": p.fornitore_principale.ragione_sociale if p.fornitore_principale else "",
            "fornitore_id": p.fornitore_principale_id if p.fornitore_principale else None,
            "categoria": p.categoria.nome_categoria if p.categoria else "",
            "misura": p.get_misura_display(),
            "misura_codice": p.misura,
            "codice_fornitore": p.codice_fornitore or "",
            "aliquota_iva": p.aliquota_iva or "22",
        })
    return JsonResponse({"results": results})
