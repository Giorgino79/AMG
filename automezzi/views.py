from django.urls import reverse, reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
    TemplateView,
)
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from .models import (
    Automezzo,
    Manutenzione,
    AllegatoManutenzione,
    Rifornimento,
    EventoAutomezzo,
    AffidamentoMezzo,
)
from .forms import (
    AutomezzoForm,
    ManutenzioneForm,
    ManutenzioneCreateForm,
    ManutenzioneUpdateForm,
    ManutenzioneResponsabileForm,
    ManutenzioneFinaleForm,
    AllegatoManutenzioneForm,
    RifornimentoForm,
    EventoAutomezzoForm,
    AffidamentoMezzoForm,
    AffidamentoRientroForm,
)
from django.utils import timezone
from core.pdf_generator import generate_pdf_from_html
import itertools


# AUTOMEZZI CRUD
class AutomezzoListView(LoginRequiredMixin, ListView):
    model = Automezzo
    template_name = "automezzi/automezzo_list.html"
    context_object_name = "automezzi"
    paginate_by = 20

    def get_queryset(self):
        qs = super().get_queryset().order_by("targa")

        # Ricerca per targa
        targa_search = self.request.GET.get("targa", "")
        if targa_search:
            qs = qs.filter(targa__icontains=targa_search)

        # Filtro per marca
        marca_search = self.request.GET.get("marca", "")
        if marca_search:
            qs = qs.filter(marca__icontains=marca_search)

        # Filtro per stato attivo
        attivo_filter = self.request.GET.get("attivo", "")
        if attivo_filter == "si":
            qs = qs.filter(attivo=True)
        elif attivo_filter == "no":
            qs = qs.filter(attivo=False)

        # Filtro per disponibilità
        disponibile_filter = self.request.GET.get("disponibile", "")
        if disponibile_filter == "si":
            qs = qs.filter(disponibile=True)
        elif disponibile_filter == "no":
            qs = qs.filter(disponibile=False)

        # Filtro per anno immatricolazione
        anno_da = self.request.GET.get("anno_da", "")
        if anno_da:
            try:
                qs = qs.filter(anno_immatricolazione__gte=int(anno_da))
            except ValueError:
                pass

        anno_a = self.request.GET.get("anno_a", "")
        if anno_a:
            try:
                qs = qs.filter(anno_immatricolazione__lte=int(anno_a))
            except ValueError:
                pass

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["targa_search"] = self.request.GET.get("targa", "")
        context["marca_search"] = self.request.GET.get("marca", "")
        context["attivo_filter"] = self.request.GET.get("attivo", "")
        context["disponibile_filter"] = self.request.GET.get("disponibile", "")
        context["anno_da"] = self.request.GET.get("anno_da", "")
        context["anno_a"] = self.request.GET.get("anno_a", "")
        return context


class AutomezzoDetailView(LoginRequiredMixin, DetailView):
    model = Automezzo
    template_name = "automezzi/automezzo_detail.html"
    context_object_name = "automezzo"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from django.contrib.contenttypes.models import ContentType

        automezzo = self.object
        context['object'] = automezzo  # Per base_detail.html
        context['edit_url'] = reverse_lazy('automezzi:automezzo_update', kwargs={'pk': automezzo.pk})
        context['delete_url'] = reverse_lazy('automezzi:automezzo_delete', kwargs={'pk': automezzo.pk})
        context['back_url'] = reverse_lazy('automezzi:automezzo_list')
        context['content_type_id'] = ContentType.objects.get_for_model(Automezzo).id

        # Statistiche per sidebar
        context['manutenzioni_count'] = automezzo.manutenzioni.count()
        context['rifornimenti_count'] = automezzo.rifornimenti.count()
        context['eventi_count'] = automezzo.eventi.count()
        context['manutenzioni_aperte'] = automezzo.manutenzioni.exclude(stato='terminata').count()

        return context


class AutomezzoCreateView(LoginRequiredMixin, CreateView):
    model = Automezzo
    form_class = AutomezzoForm
    template_name = "automezzi/automezzo_form.html"
    success_url = reverse_lazy("automezzi:automezzo_list")


class AutomezzoUpdateView(LoginRequiredMixin, UpdateView):
    model = Automezzo
    form_class = AutomezzoForm
    template_name = "automezzi/automezzo_form.html"
    success_url = reverse_lazy("automezzi:automezzo_list")


class AutomezzoDeleteView(LoginRequiredMixin, DeleteView):
    model = Automezzo
    template_name = "automezzi/automezzo_confirm_delete.html"
    success_url = reverse_lazy("automezzi:automezzo_list")


# MANUTENZIONI CRUD
class ManutenzioneListView(LoginRequiredMixin, ListView):
    model = Manutenzione
    template_name = "automezzi/manutenzione_list.html"
    context_object_name = "manutenzioni"
    paginate_by = 20

    def get_queryset(self):
        # Se presente pk automezzo in url, filtra per automezzo
        pk = self.kwargs.get("automezzo_pk")
        qs = (
            super()
            .get_queryset()
            .select_related("automezzo", "responsabile")
            .order_by("-data_prevista")
        )
        if pk:
            qs = qs.filter(automezzo_id=pk)

        # Ricerca per targa
        targa_search = self.request.GET.get("targa", "")
        if targa_search:
            qs = qs.filter(automezzo__targa__icontains=targa_search)

        # Ricerca per numero mezzo
        numero_mezzo_search = self.request.GET.get("numero_mezzo", "")
        if numero_mezzo_search:
            try:
                numero_mezzo = int(numero_mezzo_search)
                qs = qs.filter(automezzo__numero_mezzo=numero_mezzo)
            except ValueError:
                pass

        # Filtro per stato completamento
        completata_filter = self.request.GET.get("completata", "")
        if completata_filter == "si":
            qs = qs.filter(completata=True)
        elif completata_filter == "no":
            qs = qs.filter(completata=False)

        # Filtro per descrizione
        descrizione_search = self.request.GET.get("descrizione", "")
        if descrizione_search:
            qs = qs.filter(descrizione__icontains=descrizione_search)

        # Filtro per range di date
        data_da = self.request.GET.get("data_da", "")
        if data_da:
            try:
                from django.utils import timezone

                data_da_parsed = timezone.datetime.strptime(data_da, "%Y-%m-%d").date()
                qs = qs.filter(data__gte=data_da_parsed)
            except ValueError:
                pass

        data_a = self.request.GET.get("data_a", "")
        if data_a:
            try:
                from django.utils import timezone

                data_a_parsed = timezone.datetime.strptime(data_a, "%Y-%m-%d").date()
                qs = qs.filter(data__lte=data_a_parsed)
            except ValueError:
                pass

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["targa_search"] = self.request.GET.get("targa", "")
        context["numero_mezzo_search"] = self.request.GET.get("numero_mezzo", "")
        context["completata_filter"] = self.request.GET.get("completata", "")
        context["descrizione_search"] = self.request.GET.get("descrizione", "")
        context["data_da"] = self.request.GET.get("data_da", "")
        context["data_a"] = self.request.GET.get("data_a", "")
        return context


class ManutenzioneDetailView(LoginRequiredMixin, DetailView):
    model = Manutenzione
    template_name = "automezzi/manutenzione_detail.html"
    context_object_name = "manutenzione"


class ManutenzioneCreateView(LoginRequiredMixin, CreateView):
    model = Manutenzione
    form_class = ManutenzioneCreateForm
    template_name = "automezzi/manutenzione_form.html"

    def get_initial(self):
        initial = super().get_initial()
        # Se la manutenzione è creata da dettaglio automezzo
        pk = self.kwargs.get("automezzo_pk")
        if pk:
            initial["automezzo"] = pk
        return initial

    def form_valid(self, form):
        # Imposta automaticamente seguito_da con l'utente corrente
        form.instance.seguito_da = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("automezzi:manutenzione_list")


class ManutenzioneUpdateView(LoginRequiredMixin, UpdateView):
    model = Manutenzione
    form_class = ManutenzioneUpdateForm
    template_name = "automezzi/manutenzione_form.html"

    def get_success_url(self):
        return reverse_lazy("automezzi:manutenzione_list")


class ManutenzioneDeleteView(LoginRequiredMixin, DeleteView):
    model = Manutenzione
    template_name = "automezzi/manutenzione_confirm_delete.html"

    def get_success_url(self):
        return reverse_lazy("automezzi:manutenzione_list")


class ManutenzioneResponsabileView(LoginRequiredMixin, UpdateView):
    """View per il form del responsabile che porta il mezzo in manutenzione"""

    model = Manutenzione
    form_class = ManutenzioneResponsabileForm
    template_name = "automezzi/manutenzione_responsabile_form.html"

    def get_queryset(self):
        # Solo manutenzioni con stato 'aperta' possono essere prese in carico
        return super().get_queryset().filter(stato="aperta")

    def form_valid(self, form):
        # Imposta automaticamente data_inizio_manutenzione e cambia stato
        form.instance.data_inizio_manutenzione = timezone.now()
        form.instance.stato = "in_corso"
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            "automezzi:manutenzione_detail", kwargs={"pk": self.object.pk}
        )


class ManutenzioneFinaleView(LoginRequiredMixin, UpdateView):
    """View per il completamento finale della manutenzione"""

    model = Manutenzione
    form_class = ManutenzioneFinaleForm
    template_name = "automezzi/manutenzione_finale_form.html"

    def get_queryset(self):
        # Solo manutenzioni con stato 'in_corso' possono essere completate
        return super().get_queryset().filter(stato="in_corso")

    def form_valid(self, form):
        # Imposta automaticamente data_completamento e cambia stato
        form.instance.data_completamento = timezone.now()
        form.instance.stato = "terminata"
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            "automezzi:manutenzione_detail", kwargs={"pk": self.object.pk}
        )


class AllegatoManutenzioneCreateView(LoginRequiredMixin, CreateView):
    """View per aggiungere allegati aggiuntivi"""

    model = AllegatoManutenzione
    form_class = AllegatoManutenzioneForm
    template_name = "automezzi/allegato_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["manutenzione"] = get_object_or_404(
            Manutenzione, pk=self.kwargs["manutenzione_pk"]
        )
        return context

    def form_valid(self, form):
        # Collega l'allegato alla manutenzione e all'utente
        form.instance.manutenzione = get_object_or_404(
            Manutenzione, pk=self.kwargs["manutenzione_pk"]
        )
        form.instance.caricato_da = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            "automezzi:manutenzione_detail",
            kwargs={"pk": self.kwargs["manutenzione_pk"]},
        )


# RIFORNIMENTI CRUD
class RifornimentoListView(LoginRequiredMixin, ListView):
    model = Rifornimento
    template_name = "automezzi/rifornimento_list.html"
    context_object_name = "rifornimenti"
    paginate_by = 20

    def get_queryset(self):
        pk = self.kwargs.get("automezzo_pk")
        qs = super().get_queryset().select_related("automezzo").order_by("-data")
        if pk:
            qs = qs.filter(automezzo_id=pk)

        # Ricerca per targa
        targa_search = self.request.GET.get("targa", "")
        if targa_search:
            qs = qs.filter(automezzo__targa__icontains=targa_search)

        # Filtro per range di date
        data_da = self.request.GET.get("data_da", "")
        if data_da:
            try:
                from django.utils import timezone

                data_da_parsed = timezone.datetime.strptime(data_da, "%Y-%m-%d").date()
                qs = qs.filter(data__gte=data_da_parsed)
            except ValueError:
                pass

        data_a = self.request.GET.get("data_a", "")
        if data_a:
            try:
                from django.utils import timezone

                data_a_parsed = timezone.datetime.strptime(data_a, "%Y-%m-%d").date()
                qs = qs.filter(data__lte=data_a_parsed)
            except ValueError:
                pass

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["targa_search"] = self.request.GET.get("targa", "")
        context["data_da"] = self.request.GET.get("data_da", "")
        context["data_a"] = self.request.GET.get("data_a", "")
        return context


class RifornimentoDetailView(LoginRequiredMixin, DetailView):
    model = Rifornimento
    template_name = "automezzi/rifornimento_detail.html"
    context_object_name = "rifornimento"


class RifornimentoCreateView(LoginRequiredMixin, CreateView):
    model = Rifornimento
    form_class = RifornimentoForm
    template_name = "automezzi/rifornimento_form.html"

    def get_initial(self):
        initial = super().get_initial()
        pk = self.kwargs.get("automezzo_pk")
        if pk:
            initial["automezzo"] = pk
        return initial

    def get_success_url(self):
        return reverse_lazy("automezzi:rifornimento_list")


class RifornimentoUpdateView(LoginRequiredMixin, UpdateView):
    model = Rifornimento
    form_class = RifornimentoForm
    template_name = "automezzi/rifornimento_form.html"

    def get_success_url(self):
        return reverse_lazy("automezzi:rifornimento_list")


class RifornimentoDeleteView(LoginRequiredMixin, DeleteView):
    model = Rifornimento
    template_name = "automezzi/rifornimento_confirm_delete.html"

    def get_success_url(self):
        return reverse_lazy("automezzi:rifornimento_list")


# EVENTI AUTOMEZZO CRUD
class EventoAutomezzoListView(LoginRequiredMixin, ListView):
    model = EventoAutomezzo
    template_name = "automezzi/evento_list.html"
    context_object_name = "eventi"
    paginate_by = 20

    def get_queryset(self):
        pk = self.kwargs.get("automezzo_pk")
        qs = (
            super()
            .get_queryset()
            .select_related("automezzo", "dipendente_coinvolto")
            .order_by("-data_evento")
        )
        if pk:
            qs = qs.filter(automezzo_id=pk)

        # Ricerca per targa
        targa_search = self.request.GET.get("targa", "")
        if targa_search:
            qs = qs.filter(automezzo__targa__icontains=targa_search)

        # Filtro per tipo evento
        tipo_filter = self.request.GET.get("tipo", "")
        if tipo_filter:
            qs = qs.filter(tipo=tipo_filter)

        # Filtro per stato risoluzione
        risolto_filter = self.request.GET.get("risolto", "")
        if risolto_filter == "si":
            qs = qs.filter(risolto=True)
        elif risolto_filter == "no":
            qs = qs.filter(risolto=False)

        # Filtro per range di date
        data_da = self.request.GET.get("data_da", "")
        if data_da:
            try:
                from django.utils import timezone

                data_da_parsed = timezone.datetime.strptime(data_da, "%Y-%m-%d").date()
                qs = qs.filter(data_evento__gte=data_da_parsed)
            except ValueError:
                pass

        data_a = self.request.GET.get("data_a", "")
        if data_a:
            try:
                from django.utils import timezone

                data_a_parsed = timezone.datetime.strptime(data_a, "%Y-%m-%d").date()
                qs = qs.filter(data_evento__lte=data_a_parsed)
            except ValueError:
                pass

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["targa_search"] = self.request.GET.get("targa", "")
        context["tipo_filter"] = self.request.GET.get("tipo", "")
        context["risolto_filter"] = self.request.GET.get("risolto", "")
        context["data_da"] = self.request.GET.get("data_da", "")
        context["data_a"] = self.request.GET.get("data_a", "")
        context["tipo_choices"] = EventoAutomezzo.TIPO_EVENTO_CHOICES
        return context


class EventoAutomezzoDetailView(LoginRequiredMixin, DetailView):
    model = EventoAutomezzo
    template_name = "automezzi/evento_detail.html"
    context_object_name = "evento"


class EventoAutomezzoCreateView(LoginRequiredMixin, CreateView):
    model = EventoAutomezzo
    form_class = EventoAutomezzoForm
    template_name = "automezzi/evento_form.html"

    def get_initial(self):
        initial = super().get_initial()
        pk = self.kwargs.get("automezzo_pk")
        if pk:
            initial["automezzo"] = pk
        return initial

    def get_success_url(self):
        return reverse_lazy("automezzi:evento_list")


class EventoAutomezzoUpdateView(LoginRequiredMixin, UpdateView):
    model = EventoAutomezzo
    form_class = EventoAutomezzoForm
    template_name = "automezzi/evento_form.html"

    def get_success_url(self):
        return reverse_lazy("automezzi:evento_list")


class EventoAutomezzoDeleteView(LoginRequiredMixin, DeleteView):
    model = EventoAutomezzo
    template_name = "automezzi/evento_confirm_delete.html"

    def get_success_url(self):
        return reverse_lazy("automezzi:evento_list")


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "automezzi/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now().date()
        context["automezzi_count"] = Automezzo.objects.count()
        context["attivi_count"] = Automezzo.objects.filter(attivo=True).count()
        context["disponibili_count"] = Automezzo.objects.filter(
            disponibile=True, attivo=True, bloccata=False
        ).count()
        context["automezzi_bloccati"] = Automezzo.objects.filter(bloccata=True)
        context["manutenzioni_in_corso"] = Manutenzione.objects.filter(completata=False)
        context["prossime_revisioni"] = Automezzo.objects.filter(
            data_revisione__gte=today
        ).order_by("data_revisione")[:5]
        context["eventi_recenti"] = EventoAutomezzo.objects.order_by("-data_evento")[:5]
        context["rifornimenti_recenti"] = Rifornimento.objects.order_by("-data")[:5]
        context["affidamenti_attivi"] = AffidamentoMezzo.objects.exclude(stato="completato").count()

        # Affidamento attivo per l'utente corrente
        context["mio_affidamento"] = AffidamentoMezzo.objects.filter(
            user=self.request.user,
            stato__in=["in_attesa", "accettato", "in_corso"],
        ).select_related("automezzo").first()

        return context


class CronologiaAutomezzoView(LoginRequiredMixin, TemplateView):
    """Vista per mostrare la cronologia completa di un automezzo"""

    template_name = "automezzi/cronologia_automezzo.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Parametri dalla request
        targa = self.request.GET.get("targa", "").strip().upper()
        data_da = self.request.GET.get("data_da", "")
        data_a = self.request.GET.get("data_a", "")

        context["targa_search"] = targa
        context["data_da"] = data_da
        context["data_a"] = data_a

        if not targa:
            context["error"] = "Inserire una targa per la ricerca"
            return context

        # Cerca l'automezzo
        try:
            automezzo = Automezzo.objects.get(targa__iexact=targa)
            context["automezzo"] = automezzo
        except Automezzo.DoesNotExist:
            context["error"] = f'Automezzo con targa "{targa}" non trovato'
            return context

        # Prepara filtri data
        date_filter_kwargs = {}
        if data_da:
            try:
                data_da_parsed = timezone.datetime.strptime(data_da, "%Y-%m-%d").date()
                date_filter_kwargs["gte"] = data_da_parsed
            except ValueError:
                pass

        if data_a:
            try:
                data_a_parsed = timezone.datetime.strptime(data_a, "%Y-%m-%d").date()
                date_filter_kwargs["lte"] = data_a_parsed
            except ValueError:
                pass

        # Query per ogni tipo di record
        rifornimenti = Rifornimento.objects.filter(automezzo=automezzo)
        if date_filter_kwargs:
            for k, v in date_filter_kwargs.items():
                rifornimenti = rifornimenti.filter(**{f"data__{k}": v})

        eventi = EventoAutomezzo.objects.filter(automezzo=automezzo)
        if date_filter_kwargs:
            for k, v in date_filter_kwargs.items():
                eventi = eventi.filter(**{f"data_evento__{k}": v})

        manutenzioni = Manutenzione.objects.filter(automezzo=automezzo)
        if date_filter_kwargs:
            for k, v in date_filter_kwargs.items():
                manutenzioni = manutenzioni.filter(**{f"data__{k}": v})

        # Crea lista unificata con tipo e colore
        cronologia = []

        # Rifornimenti (colore info - blu)
        for rif in rifornimenti.select_related("automezzo"):
            cronologia.append(
                {
                    "data": rif.data,
                    "tipo": "rifornimento",
                    "colore": "table-info",  # Blu
                    "icona": "fas fa-gas-pump",
                    "oggetto": rif,
                    "descrizione": f"{rif.litri}L - €{rif.costo_totale}",
                    "dettagli": f"{rif.chilometri} km",
                    "url": f"/automezzi/rifornimenti/{rif.pk}/",
                }
            )

        # Eventi (colore warning - giallo)
        for evento in eventi.select_related("automezzo"):
            cronologia.append(
                {
                    "data": evento.data_evento,
                    "tipo": "evento",
                    "colore": "table-warning",  # Giallo
                    "icona": "fas fa-exclamation-triangle",
                    "oggetto": evento,
                    "descrizione": f"{evento.get_tipo_display()}",
                    "dettagli": (
                        evento.descrizione[:50] + "..."
                        if evento.descrizione and len(evento.descrizione) > 50
                        else evento.descrizione or ""
                    ),
                    "url": f"/automezzi/eventi/{evento.pk}/",
                    "stato": "Risolto" if evento.risolto else "Non risolto",
                }
            )

        # Manutenzioni (colore success - verde)
        for man in manutenzioni.select_related("automezzo"):
            cronologia.append(
                {
                    "data": man.data_prevista,
                    "tipo": "manutenzione",
                    "colore": "table-success",  # Verde
                    "icona": "fas fa-tools",
                    "oggetto": man,
                    "descrizione": (
                        man.descrizione[:50] + "..."
                        if len(man.descrizione) > 50
                        else man.descrizione
                    ),
                    "dettagli": f"€{man.costo}",
                    "url": f"/automezzi/manutenzioni/{man.pk}/",
                    "stato": "Completata" if man.completata else "Da completare",
                }
            )

        # Ordina per data (più recenti prima)
        cronologia.sort(key=lambda x: x["data"], reverse=True)

        context["cronologia"] = cronologia
        context["totale_records"] = len(cronologia)

        return context


# PDF VIEWS
class RifornimentoPDFView(LoginRequiredMixin, DetailView):
    """Vista per generare PDF rifornimento"""

    model = Rifornimento

    def get(self, request, *args, **kwargs):
        rifornimento = self.get_object()

        context = {
            "rifornimento": rifornimento,
            "today": timezone.now(),
        }

        # Genera PDF usando il sistema Management
        from django.template.loader import render_to_string
        from core.pdf_generator import PDFConfig

        html_content = render_to_string("automezzi/pdf/rifornimento_pdf.html", context)
        config = PDFConfig(
            filename=f'rifornimento_{rifornimento.automezzo.targa}_{rifornimento.data.strftime("%Y%m%d")}.pdf'
        )
        pdf_buffer = generate_pdf_from_html(html_content, config, output_type="buffer")

        if pdf_buffer:
            response = HttpResponse(
                pdf_buffer.getvalue(), content_type="application/pdf"
            )
            response["Content-Disposition"] = (
                f'inline; filename="rifornimento_{rifornimento.automezzo.targa}_{rifornimento.data.strftime("%Y%m%d")}.pdf"'
            )
            return response

        return HttpResponse("Errore nella generazione del PDF", status=500)


class EventoPDFView(LoginRequiredMixin, DetailView):
    """Vista per generare PDF evento"""

    model = EventoAutomezzo

    def get(self, request, *args, **kwargs):
        evento = self.get_object()

        context = {
            "evento": evento,
            "today": timezone.now(),
        }

        # Genera PDF usando il sistema Management
        html_content = render_to_string("automezzi/pdf/evento_pdf.html", context)
        config = PDFConfig(
            filename=f'evento_{evento.automezzo.targa}_{evento.data_evento.strftime("%Y%m%d")}.pdf'
        )
        pdf_buffer = generate_pdf_from_html(html_content, config, output_type="buffer")

        if pdf_buffer:
            response = HttpResponse(
                pdf_buffer.getvalue(), content_type="application/pdf"
            )
            response["Content-Disposition"] = (
                f'inline; filename="evento_{evento.automezzo.targa}_{evento.data_evento.strftime("%Y%m%d")}.pdf"'
            )
            return response

        return HttpResponse("Errore nella generazione del PDF", status=500)


class ManutenzionePDFView(LoginRequiredMixin, DetailView):
    """Vista per generare PDF manutenzione"""

    model = Manutenzione

    def get(self, request, *args, **kwargs):
        manutenzione = self.get_object()

        context = {
            "manutenzione": manutenzione,
            "today": timezone.now(),
        }

        # Genera PDF usando il sistema Management
        html_content = render_to_string("automezzi/pdf/manutenzione_pdf.html", context)
        config = PDFConfig(
            filename=f'manutenzione_{manutenzione.automezzo.targa}_{manutenzione.data_prevista.strftime("%Y%m%d")}.pdf'
        )
        pdf_buffer = generate_pdf_from_html(html_content, config, output_type="buffer")

        if pdf_buffer:
            response = HttpResponse(
                pdf_buffer.getvalue(), content_type="application/pdf"
            )
            response["Content-Disposition"] = (
                f'inline; filename="manutenzione_{manutenzione.automezzo.targa}_{manutenzione.data_prevista.strftime("%Y%m%d")}.pdf"'
            )
            return response

        return HttpResponse("Errore nella generazione del PDF", status=500)


# AFFIDAMENTO MEZZO
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings as django_settings


@method_decorator(staff_member_required, name="dispatch")
class AffidamentoMezzoListView(LoginRequiredMixin, TemplateView):
    template_name = "automezzi/affidamento_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from django.db.models import Q

        base_qs = AffidamentoMezzo.objects.select_related("user", "automezzo", "creato_da")

        # Affidamenti in essere (non completati)
        context["affidamenti_attivi"] = base_qs.exclude(stato="completato").order_by("-data_creazione")

        # Ultimi 5 completati
        context["affidamenti_completati"] = base_qs.filter(stato="completato").order_by("-data_rientro")[:5]

        # Ricerca
        q = self.request.GET.get("q", "").strip()
        targa = self.request.GET.get("targa", "").strip()
        data_da = self.request.GET.get("data_da", "")
        data_a = self.request.GET.get("data_a", "")

        context["q"] = q
        context["targa_search"] = targa
        context["data_da"] = data_da
        context["data_a"] = data_a

        has_search = q or targa or data_da or data_a

        if has_search:
            risultati = base_qs.all()

            if q:
                risultati = risultati.filter(
                    Q(user__username__icontains=q)
                    | Q(user__first_name__icontains=q)
                    | Q(user__last_name__icontains=q)
                )

            if targa:
                risultati = risultati.filter(automezzo__targa__icontains=targa)

            if data_da:
                risultati = risultati.filter(data_inizio__gte=data_da)

            if data_a:
                risultati = risultati.filter(data_fine__lte=data_a)

            context["risultati_ricerca"] = risultati.order_by("-data_creazione")
            context["has_search"] = True
        else:
            context["has_search"] = False

        return context


@method_decorator(staff_member_required, name="dispatch")
class AffidamentoMezzoCreateView(LoginRequiredMixin, CreateView):
    model = AffidamentoMezzo
    form_class = AffidamentoMezzoForm
    template_name = "automezzi/affidamento_form.html"

    def form_valid(self, form):
        form.instance.creato_da = self.request.user
        response = super().form_valid(form)
        self._invia_mail_affidamento(self.object)
        return response

    def _invia_mail_affidamento(self, affidamento):
        subject = f"Affidamento mezzo {affidamento.automezzo.targa} - Presa in carico"
        accept_url = self.request.build_absolute_uri(
            reverse_lazy(
                "automezzi:affidamento_accetta",
                kwargs={"token": str(affidamento.token_accettazione)},
            )
        )
        context = {
            "affidamento": affidamento,
            "accept_url": accept_url,
        }
        html_message = render_to_string(
            "automezzi/email/affidamento_notifica.html", context
        )
        send_mail(
            subject=subject,
            message="",
            from_email=django_settings.DEFAULT_FROM_EMAIL,
            recipient_list=[affidamento.user.email],
            html_message=html_message,
            fail_silently=True,
        )

    def get_success_url(self):
        return reverse_lazy("automezzi:affidamento_list")


@method_decorator(staff_member_required, name="dispatch")
class AffidamentoMezzoDetailView(LoginRequiredMixin, DetailView):
    model = AffidamentoMezzo
    template_name = "automezzi/affidamento_detail.html"
    context_object_name = "affidamento"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from django.contrib.contenttypes.models import ContentType

        # Context per base_detail.html
        context['object'] = self.object  # Alias per template comune
        context['content_type_id'] = ContentType.objects.get_for_model(AffidamentoMezzo).id
        context['back_url'] = reverse('automezzi:affidamento_list')
        return context


class AffidamentoAccettaView(LoginRequiredMixin, TemplateView):
    template_name = "automezzi/affidamento_accetta.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        token = self.kwargs["token"]
        affidamento = get_object_or_404(AffidamentoMezzo, token_accettazione=token)
        context["affidamento"] = affidamento
        context["already_accepted"] = affidamento.firma_accettazione
        return context

    def post(self, request, *args, **kwargs):
        token = self.kwargs["token"]
        affidamento = get_object_or_404(AffidamentoMezzo, token_accettazione=token)

        if affidamento.firma_accettazione:
            from django.contrib import messages
            messages.warning(request, "Questo affidamento è già stato accettato.")
            return self.get(request, *args, **kwargs)

        if request.user != affidamento.user:
            from django.contrib import messages
            messages.error(request, "Non sei autorizzato ad accettare questo affidamento.")
            return self.get(request, *args, **kwargs)

        affidamento.firma_accettazione = True
        affidamento.data_accettazione = timezone.now()
        affidamento.stato = "accettato"
        affidamento.save()

        self._invia_mail_conferma(affidamento)

        from django.contrib import messages
        messages.success(request, "Affidamento accettato con successo!")
        return self.get(request, *args, **kwargs)

    def _invia_mail_conferma(self, affidamento):
        subject = f"Conferma presa in carico mezzo {affidamento.automezzo.targa}"
        context = {"affidamento": affidamento}
        html_message = render_to_string(
            "automezzi/email/affidamento_conferma.html", context
        )
        send_mail(
            subject=subject,
            message="",
            from_email=django_settings.DEFAULT_FROM_EMAIL,
            recipient_list=[affidamento.user.email],
            html_message=html_message,
            fail_silently=True,
        )


@method_decorator(staff_member_required, name="dispatch")
class AffidamentoRientroView(LoginRequiredMixin, UpdateView):
    model = AffidamentoMezzo
    form_class = AffidamentoRientroForm
    template_name = "automezzi/affidamento_rientro_form.html"

    def get_queryset(self):
        return super().get_queryset().filter(stato__in=["in_attesa", "accettato", "in_corso"])

    def form_valid(self, form):
        form.instance.data_rientro = timezone.now()
        form.instance.stato = "completato"
        if form.instance.km_finali:
            form.instance.automezzo.chilometri_attuali = form.instance.km_finali
            form.instance.automezzo.save()
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            "automezzi:affidamento_detail", kwargs={"pk": self.object.pk}
        )


# === VISTA "IL MIO MEZZO" PER UTENTI CON AFFIDAMENTO ATTIVO ===

class MioAffidamentoView(LoginRequiredMixin, TemplateView):
    """Vista per l'utente che ha un mezzo affidato: riepilogo, rifornimenti ed eventi"""
    template_name = "automezzi/mio_affidamento.html"

    def get_affidamento_attivo(self):
        return AffidamentoMezzo.objects.filter(
            user=self.request.user,
            stato__in=["in_attesa", "accettato", "in_corso"],
        ).select_related("automezzo").first()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        affidamento = self.get_affidamento_attivo()
        context["affidamento"] = affidamento

        if affidamento:
            automezzo = affidamento.automezzo
            # Rifornimenti e eventi durante il periodo di affidamento
            context["rifornimenti"] = Rifornimento.objects.filter(
                automezzo=automezzo,
                data__gte=affidamento.data_inizio,
            ).order_by("-data")
            context["eventi"] = EventoAutomezzo.objects.filter(
                automezzo=automezzo,
                data_evento__gte=affidamento.data_inizio,
            ).order_by("-data_evento")

        return context


class AffidamentoRifornimentoCreateView(LoginRequiredMixin, CreateView):
    """Crea un rifornimento nel contesto dell'affidamento attivo dell'utente"""
    model = Rifornimento
    form_class = RifornimentoForm
    template_name = "automezzi/affidamento_rifornimento_form.html"

    def get_affidamento(self):
        if not hasattr(self, "_affidamento"):
            self._affidamento = AffidamentoMezzo.objects.filter(
                user=self.request.user,
                stato__in=["in_attesa", "accettato", "in_corso"],
            ).select_related("automezzo").order_by("-data_creazione").first()
            if not self._affidamento:
                from django.http import Http404
                raise Http404("Nessun affidamento attivo")
        return self._affidamento

    def get_initial(self):
        initial = super().get_initial()
        affidamento = self.get_affidamento()
        initial["automezzo"] = affidamento.automezzo.pk
        return initial

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        affidamento = self.get_affidamento()
        form.fields["automezzo"].queryset = Automezzo.objects.filter(pk=affidamento.automezzo.pk)
        form.fields["automezzo"].initial = affidamento.automezzo.pk
        form.fields["automezzo"].widget.attrs["readonly"] = True
        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["affidamento"] = self.get_affidamento()
        return context

    def get_success_url(self):
        return reverse_lazy("automezzi:mio_affidamento")


class AffidamentoEventoCreateView(LoginRequiredMixin, CreateView):
    """Crea un evento nel contesto dell'affidamento attivo dell'utente"""
    model = EventoAutomezzo
    form_class = EventoAutomezzoForm
    template_name = "automezzi/affidamento_evento_form.html"

    def get_affidamento(self):
        if not hasattr(self, "_affidamento"):
            self._affidamento = AffidamentoMezzo.objects.filter(
                user=self.request.user,
                stato__in=["in_attesa", "accettato", "in_corso"],
            ).select_related("automezzo").order_by("-data_creazione").first()
            if not self._affidamento:
                from django.http import Http404
                raise Http404("Nessun affidamento attivo")
        return self._affidamento

    def get_initial(self):
        initial = super().get_initial()
        affidamento = self.get_affidamento()
        initial["automezzo"] = affidamento.automezzo.pk
        initial["dipendente_coinvolto"] = self.request.user.pk
        return initial

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        affidamento = self.get_affidamento()
        form.fields["automezzo"].queryset = Automezzo.objects.filter(pk=affidamento.automezzo.pk)
        form.fields["automezzo"].initial = affidamento.automezzo.pk
        form.fields["automezzo"].widget.attrs["readonly"] = True
        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["affidamento"] = self.get_affidamento()
        return context

    def get_success_url(self):
        return reverse_lazy("automezzi:mio_affidamento")
