"""
Views per app progetti_eventi.

STRUTTURA:
- View Commerciale: creazione/gestione progetti
- View Progetto: vista master con dettaglio completo
- View Engineering: gestione task ingegneri (da implementare)
"""

from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Q, Count, Prefetch
from django.utils import timezone
from datetime import timedelta

from core.mixins.view_mixins import (
    PermissionRequiredMixin,
    SetCreatedByMixin,
    FormValidMessageMixin,
    FormInvalidMessageMixin,
    SearchMixin,
    CustomPaginationMixin,
)

from .models import Progetto, ProgettoReparto, ListaProdotti, ProdottoLista, EngineeringTask
from .forms import ProgettoForm, ProgettoRepartoForm, ListaProdottiForm, ProdottoListaFormSet
from mail.models import ChatConversation


# ============================================================================
# DASHBOARD COMMERCIALE
# ============================================================================

class DashboardCommercialeView(PermissionRequiredMixin, ListView):
    """
    Dashboard per commerciali con overview progetti.
    """
    model = Progetto
    template_name = 'progetti_eventi/dashboard_commerciale.html'
    context_object_name = 'progetti_recenti'
    permission_required = 'progetti_eventi.view_progetto'

    def get_queryset(self):
        """Ultimi 10 progetti"""
        return Progetto.objects.select_related(
            'cliente',
            'commerciale'
        ).prefetch_related(
            'reparti'
        ).order_by('-created_at')[:10]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # ========== STATISTICHE ==========

        # Totali per stato
        context['totale_bozze'] = Progetto.objects.filter(stato='bozza').count()
        context['totale_in_engineering'] = Progetto.objects.filter(stato='in_engineering').count()
        context['totale_in_preparazione'] = Progetto.objects.filter(
            stato__in=['engineering_completato', 'in_preparazione']
        ).count()
        context['totale_in_corso'] = Progetto.objects.filter(stato='in_corso').count()

        # Progetti prossimi (entro 30 giorni)
        data_limite = timezone.now().date() + timedelta(days=30)
        context['progetti_prossimi'] = Progetto.objects.filter(
            data_evento__gte=timezone.now().date(),
            data_evento__lte=data_limite,
            stato__in=['pronto', 'in_preparazione', 'engineering_completato']
        ).select_related('cliente').order_by('data_evento')[:5]

        # Progetti urgenti (meno di 7 giorni)
        data_urgente = timezone.now().date() + timedelta(days=7)
        context['progetti_urgenti'] = Progetto.objects.filter(
            data_evento__gte=timezone.now().date(),
            data_evento__lte=data_urgente,
            stato__in=['bozza', 'in_engineering', 'in_preparazione']
        ).select_related('cliente').count()

        # Progetti per commerciale (se user è commerciale)
        if self.request.user.has_perm('progetti_eventi.view_all_progetti'):
            # Admin vede tutti
            context['miei_progetti'] = None
        else:
            # Commerciale vede solo i suoi
            context['miei_progetti'] = Progetto.objects.filter(
                commerciale=self.request.user
            ).count()

        # Reparti in engineering
        context['reparti_in_engineering'] = ProgettoReparto.objects.filter(
            engineering_stato__in=['assegnato', 'in_studio']
        ).select_related('progetto', 'engineering_assegnato_a').count()

        # Engineering completati questa settimana
        inizio_settimana = timezone.now() - timedelta(days=7)
        context['engineering_completati_settimana'] = ProgettoReparto.objects.filter(
            engineering_completato=True,
            data_completamento_engineering__gte=inizio_settimana
        ).count()

        return context


# ============================================================================
# LISTA PROGETTI
# ============================================================================

class ProgettoListView(PermissionRequiredMixin, SearchMixin, CustomPaginationMixin, ListView):
    """
    Lista progetti con filtri e ricerca.
    """
    model = Progetto
    template_name = 'progetti_eventi/progetto_list.html'
    context_object_name = 'progetti'
    permission_required = 'progetti_eventi.view_progetto'

    # SearchMixin
    search_fields = ['codice', 'nome_evento', 'cliente__ragione_sociale', 'location', 'citta_location']

    # Paginazione
    default_page_size = 20
    max_page_size = 100

    def get_queryset(self):
        qs = super().get_queryset().select_related(
            'cliente',
            'commerciale'
        ).prefetch_related(
            'reparti'
        )

        # Filtro per stato
        stato = self.request.GET.get('stato')
        if stato:
            qs = qs.filter(stato=stato)

        # Filtro per commerciale
        commerciale_id = self.request.GET.get('commerciale')
        if commerciale_id:
            qs = qs.filter(commerciale_id=commerciale_id)

        # Filtro per reparto coinvolto
        reparto = self.request.GET.get('reparto')
        if reparto:
            qs = qs.filter(reparti__tipo_reparto=reparto).distinct()

        # Filtro per data evento
        data_da = self.request.GET.get('data_da')
        data_a = self.request.GET.get('data_a')
        if data_da:
            qs = qs.filter(data_evento__gte=data_da)
        if data_a:
            qs = qs.filter(data_evento__lte=data_a)

        # Filtro urgenti
        if self.request.GET.get('solo_urgenti') == '1':
            data_urgente = timezone.now().date() + timedelta(days=7)
            qs = qs.filter(
                data_evento__gte=timezone.now().date(),
                data_evento__lte=data_urgente
            )

        return qs.order_by('-data_evento')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Lista commerciali per filtro
        from users.models import User
        context['commerciali'] = User.objects.filter(
            progetti_eventi_commerciale__isnull=False
        ).distinct().order_by('first_name', 'last_name')

        # Parametri filtri attuali (per mantenere selezione)
        context['filtro_stato'] = self.request.GET.get('stato', '')
        context['filtro_commerciale'] = self.request.GET.get('commerciale', '')
        context['filtro_reparto'] = self.request.GET.get('reparto', '')
        context['filtro_data_da'] = self.request.GET.get('data_da', '')
        context['filtro_data_a'] = self.request.GET.get('data_a', '')
        context['filtro_urgenti'] = self.request.GET.get('solo_urgenti', '')

        return context


# ============================================================================
# CREAZIONE PROGETTO
# ============================================================================

class ProgettoCreateView(
    PermissionRequiredMixin,
    SetCreatedByMixin,
    FormValidMessageMixin,
    FormInvalidMessageMixin,
    CreateView
):
    """
    Creazione nuovo progetto da parte del commerciale.

    WORKFLOW:
    1. Commerciale compila form progetto
    2. Seleziona reparti coinvolti (Audio/Video/Luci)
    3. Sistema crea automaticamente ProgettoReparto per ogni reparto
    4. Commerciale viene reindirizzato alla vista dettaglio
    """
    model = Progetto
    form_class = ProgettoForm
    template_name = 'progetti_eventi/progetto_form.html'
    permission_required = 'progetti_eventi.add_progetto'
    success_message = "Progetto creato con successo! I reparti sono stati notificati."

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_config'] = {
            'title': 'Nuovo Progetto Evento',
            'subtitle': 'Inserisci i dati del progetto e seleziona i reparti coinvolti',
            'submit_text': 'Crea Progetto',
            'cancel_url': 'progetti_eventi:progetto_list',
        }
        return context

    def form_valid(self, form):
        # Imposta commerciale automaticamente
        form.instance.commerciale = self.request.user

        # Salva progetto
        response = super().form_valid(form)

        # CREA ProgettoReparto per ogni reparto selezionato
        reparti_selezionati = form.cleaned_data.get('reparti_coinvolti', [])

        for reparto in reparti_selezionati:
            ProgettoReparto.objects.create(
                progetto=self.object,
                tipo_reparto=reparto,
                created_by=self.request.user
            )

        # Aggiorna campo denormalizzato sul progetto
        self.object.reparti_coinvolti = reparti_selezionati
        self.object.save(update_fields=['reparti_coinvolti'])

        # CREA CHAT DI PROGETTO
        partecipanti_selezionati = form.cleaned_data.get('partecipanti', [])

        # Crea chat di gruppo
        chat = ChatConversation.objects.create(
            titolo=f"Chat: {self.object.codice} - {self.object.nome_evento}",
            tipo='group',
            created_by=self.request.user
        )

        # Aggiungi commerciale (creatore) come partecipante
        chat.partecipanti.add(self.request.user)

        # Aggiungi partecipanti selezionati
        if partecipanti_selezionati:
            chat.partecipanti.add(*partecipanti_selezionati)

        # Collega chat al progetto
        self.object.chat_progetto = chat
        self.object.save(update_fields=['chat_progetto'])

        # Salva partecipanti nel progetto
        self.object.partecipanti.set(partecipanti_selezionati)

        # Aggiunge anche il commerciale ai partecipanti
        self.object.partecipanti.add(self.request.user)

        # SALVA MEZZI ASSEGNATI
        mezzi_selezionati = form.cleaned_data.get('mezzi_assegnati', [])
        if mezzi_selezionati:
            self.object.mezzi_assegnati.set(mezzi_selezionati)

        messages.success(
            self.request,
            f"Progetto {self.object.codice} creato! "
            f"Reparti coinvolti: {', '.join([r.upper() for r in reparti_selezionati])}. "
            f"Chat di progetto creata con {chat.partecipanti.count()} partecipanti."
            + (f" Mezzi assegnati: {len(mezzi_selezionati)}." if mezzi_selezionati else "")
        )

        # TODO: Invia notifiche agli ingegneri (quando saranno assegnati)

        return response

    def get_success_url(self):
        return self.object.get_absolute_url()


# ============================================================================
# MODIFICA PROGETTO
# ============================================================================

class ProgettoUpdateView(
    PermissionRequiredMixin,
    FormValidMessageMixin,
    FormInvalidMessageMixin,
    UpdateView
):
    """
    Modifica progetto esistente.

    ATTENZIONE: La modifica dei reparti coinvolti non elimina ProgettoReparto esistenti,
    ma può aggiungerne di nuovi.
    """
    model = Progetto
    form_class = ProgettoForm
    template_name = 'progetti_eventi/progetto_form.html'
    permission_required = 'progetti_eventi.change_progetto'
    success_message = "Progetto aggiornato con successo!"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_config'] = {
            'title': f'Modifica Progetto {self.object.codice}',
            'subtitle': self.object.nome_evento,
            'submit_text': 'Salva Modifiche',
            'cancel_url': 'progetti_eventi:progetto_detail',
            'cancel_url_kwargs': {'pk': self.object.pk},
        }
        return context

    def form_valid(self, form):
        # Aggiorna updated_by
        form.instance.updated_by = self.request.user

        response = super().form_valid(form)

        # Gestione reparti: aggiungi nuovi se selezionati
        reparti_selezionati = form.cleaned_data.get('reparti_coinvolti', [])
        reparti_esistenti = set(self.object.reparti.values_list('tipo_reparto', flat=True))

        for reparto in reparti_selezionati:
            if reparto not in reparti_esistenti:
                ProgettoReparto.objects.create(
                    progetto=self.object,
                    tipo_reparto=reparto,
                    created_by=self.request.user
                )
                messages.info(self.request, f"Aggiunto reparto {reparto.upper()}")

        # Aggiorna campo denormalizzato
        self.object.reparti_coinvolti = reparti_selezionati
        self.object.save(update_fields=['reparti_coinvolti'])

        # AGGIORNA PARTECIPANTI CHAT
        partecipanti_selezionati = form.cleaned_data.get('partecipanti', [])

        # Se esiste già una chat, aggiorna i partecipanti
        if self.object.chat_progetto:
            # Aggiorna partecipanti nella chat
            self.object.chat_progetto.partecipanti.clear()
            self.object.chat_progetto.partecipanti.add(self.request.user)  # Commerciale sempre presente
            if partecipanti_selezionati:
                self.object.chat_progetto.partecipanti.add(*partecipanti_selezionati)
        else:
            # Se non esiste ancora una chat, creala
            chat = ChatConversation.objects.create(
                titolo=f"Chat: {self.object.codice} - {self.object.nome_evento}",
                tipo='group',
                created_by=self.request.user
            )
            chat.partecipanti.add(self.request.user)
            if partecipanti_selezionati:
                chat.partecipanti.add(*partecipanti_selezionati)

            self.object.chat_progetto = chat
            self.object.save(update_fields=['chat_progetto'])

        # Aggiorna partecipanti nel progetto
        self.object.partecipanti.set(partecipanti_selezionati)
        self.object.partecipanti.add(self.request.user)

        # AGGIORNA MEZZI ASSEGNATI
        mezzi_selezionati = form.cleaned_data.get('mezzi_assegnati', [])
        self.object.mezzi_assegnati.set(mezzi_selezionati)

        return response

    def get_success_url(self):
        return self.object.get_absolute_url()


# ============================================================================
# VISTA MASTER PROGETTO (PUNTO 3)
# ============================================================================

class ProgettoDetailView(PermissionRequiredMixin, DetailView):
    """
    Vista MASTER del progetto con TAB per ogni reparto.

    Mostra:
    - Informazioni generali progetto
    - Timeline stati
    - Tab per ogni reparto (Audio/Video/Luci) con:
      * Stato Engineering
      * Stato Magazzino (collegamento app)
      * Stato Logistica (collegamento app)
      * Stato Travel (collegamento app)
      * Stato Scouting (collegamento app)
    """
    model = Progetto
    template_name = 'progetti_eventi/progetto_detail.html'
    context_object_name = 'progetto'
    permission_required = 'progetti_eventi.view_progetto'

    def get_queryset(self):
        return super().get_queryset().select_related(
            'cliente',
            'commerciale',
            'created_by',
            'updated_by'
        ).prefetch_related(
            Prefetch(
                'reparti',
                queryset=ProgettoReparto.objects.select_related(
                    'engineering_assegnato_a'
                ).prefetch_related(
                    'liste_prodotti__prodotti',
                    'engineering_tasks'
                )
            )
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Content type per allegati e QR Code
        content_type = ContentType.objects.get_for_model(self.model)
        context['content_type_id'] = content_type.id

        # URL azioni
        context['edit_url'] = reverse_lazy('progetti_eventi:progetto_update', kwargs={'pk': self.object.pk})
        context['delete_url'] = reverse_lazy('progetti_eventi:progetto_delete', kwargs={'pk': self.object.pk})
        context['back_url'] = reverse_lazy('progetti_eventi:progetto_list')

        # Reparti con dati aggregati
        reparti = []
        for reparto in self.object.reparti.all():
            reparto_data = {
                'object': reparto,
                'icon': reparto.icon,
                'liste_prodotti_count': reparto.liste_prodotti.count(),
                'liste_prodotti_approvate': reparto.liste_prodotti.filter(approvata=True).count(),
                'engineering_tasks_count': reparto.engineering_tasks.count(),
                'engineering_tasks_completati': reparto.engineering_tasks.filter(stato='completato').count(),

                # PLACEHOLDER: Dati dalle altre app (quando saranno pronte)
                # 'richieste_magazzino': reparto.richieste_approntamento.all(),
                # 'consegne_logistica': reparto.consegne.all(),
                # 'missioni_travel': reparto.missioni.all(),
                # 'richieste_scouting': reparto.richieste_personale.all(),
            }
            reparti.append(reparto_data)

        context['reparti_data'] = reparti

        # Timeline progetto
        timeline = self._build_timeline()
        context['timeline'] = timeline

        # Statistiche rapide
        context['stats'] = self._build_stats()

        # Azioni disponibili in base allo stato
        context['azioni_disponibili'] = self._get_azioni_disponibili()

        return context

    def _build_timeline(self):
        """Costruisce timeline eventi del progetto"""
        timeline = []

        if self.object.created_at:
            timeline.append({
                'data': self.object.created_at,
                'tipo': 'creazione',
                'icona': 'plus-circle',
                'colore': 'primary',
                'titolo': 'Progetto Creato',
                'descrizione': f'da {self.object.created_by.get_full_name() if self.object.created_by else "N/A"}',
            })

        if self.object.data_invio_engineering:
            timeline.append({
                'data': self.object.data_invio_engineering,
                'tipo': 'engineering',
                'icona': 'diagram-3',
                'colore': 'info',
                'titolo': 'Inviato a Engineering',
                'descrizione': f'{self.object.reparti.count()} reparti coinvolti',
            })

        if self.object.data_completamento_engineering:
            timeline.append({
                'data': self.object.data_completamento_engineering,
                'tipo': 'engineering_completato',
                'icona': 'check-circle',
                'colore': 'success',
                'titolo': 'Engineering Completato',
                'descrizione': 'Tutti i reparti hanno completato lo studio',
            })

        # Evento
        data_evento_dt = timezone.datetime.combine(
            self.object.data_evento,
            self.object.ora_inizio_evento or timezone.datetime.min.time()
        )
        # Rendi il datetime timezone-aware
        if timezone.is_naive(data_evento_dt):
            data_evento_dt = timezone.make_aware(data_evento_dt)

        timeline.append({
            'data': data_evento_dt,
            'tipo': 'evento',
            'icona': 'calendar-event',
            'colore': 'warning' if self.object.is_urgente else 'secondary',
            'titolo': 'Data Evento',
            'descrizione': f'{self.object.nome_evento} - {self.object.location}',
        })

        # Ordina per data
        timeline.sort(key=lambda x: x['data'])

        return timeline

    def _build_stats(self):
        """Statistiche rapide"""
        reparti = self.object.reparti.all()

        return {
            'reparti_totali': reparti.count(),
            'reparti_engineering_completato': reparti.filter(engineering_completato=True).count(),
            'reparti_pronti': reparti.filter(
                magazzino_ready=True,
                logistica_ready=True,
                travel_ready=True,
                scouting_ready=True
            ).count(),
            'liste_prodotti_totali': sum(r.liste_prodotti.count() for r in reparti),
            'liste_prodotti_approvate': sum(r.liste_prodotti.filter(approvata=True).count() for r in reparti),
            'giorni_mancanti': self.object.giorni_mancanti,
            'percentuale_completamento': self.object.percentuale_completamento,
        }

    def _get_azioni_disponibili(self):
        """Determina azioni disponibili in base allo stato"""
        azioni = []

        if self.object.stato == 'bozza':
            azioni.append({
                'url': reverse_lazy('progetti_eventi:progetto_invia_engineering', kwargs={'pk': self.object.pk}),
                'label': 'Invia a Engineering',
                'icona': 'send',
                'colore': 'primary',
                'confirm': 'Confermi l\'invio a Engineering? I reparti verranno notificati.',
            })

        if self.object.stato == 'in_engineering':
            azioni.append({
                'url': '#',
                'label': 'In attesa Engineering',
                'icona': 'hourglass-split',
                'colore': 'secondary',
                'disabled': True,
            })

        # Aggiungi altre azioni in base agli stati...

        return azioni


# ============================================================================
# AZIONI PROGETTO
# ============================================================================

class ProgettoInviaEngineeringView(PermissionRequiredMixin, DetailView):
    """
    Invia il progetto a engineering (cambia stato).
    """
    model = Progetto
    permission_required = 'progetti_eventi.change_progetto'

    def post(self, request, *args, **kwargs):
        progetto = self.get_object()

        try:
            progetto.invia_a_engineering(user=request.user)
            messages.success(
                request,
                f"Progetto {progetto.codice} inviato a Engineering. "
                f"Gli ingegneri sono stati notificati."
            )
        except ValidationError as e:
            messages.error(request, str(e))

        return redirect(progetto.get_absolute_url())


class ProgettoDeleteView(PermissionRequiredMixin, DeleteView):
    """
    Soft delete del progetto.
    """
    model = Progetto
    template_name = 'progetti_eventi/progetto_confirm_delete.html'
    permission_required = 'progetti_eventi.delete_progetto'
    success_url = reverse_lazy('progetti_eventi:progetto_list')

    def form_valid(self, form):
        """Usa soft delete invece di eliminazione fisica"""
        self.object.soft_delete(user=self.request.user)
        messages.success(self.request, f"Progetto {self.object.codice} eliminato.")
        return redirect(self.get_success_url())


# ============================================================================
# DETTAGLIO REPARTO
# ============================================================================

class ProgettoRepartoDetailView(PermissionRequiredMixin, DetailView):
    """
    Vista dettagliata di un singolo reparto (Audio/Video/Luci).

    Mostra tutte le informazioni specifiche del reparto:
    - Engineering
    - Liste prodotti
    - Collegamenti a magazzino/logistica/travel/scouting
    """
    model = ProgettoReparto
    template_name = 'progetti_eventi/reparto_detail.html'
    context_object_name = 'reparto'
    permission_required = 'progetti_eventi.view_progettoreparto'

    def get_queryset(self):
        return super().get_queryset().select_related(
            'progetto',
            'progetto__cliente',
            'engineering_assegnato_a'
        ).prefetch_related(
            'liste_prodotti__prodotti',
            'engineering_tasks'
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Content type per allegati
        content_type = ContentType.objects.get_for_model(self.model)
        context['content_type_id'] = content_type.id

        # URL back al progetto
        context['back_url'] = self.object.progetto.get_absolute_url()

        # TODO: Quando le app saranno pronte, caricare:
        # context['richieste_magazzino'] = self.object.richieste_approntamento.all()
        # context['consegne_logistica'] = self.object.consegne.all()
        # context['missioni_travel'] = self.object.missioni.all()
        # context['richieste_scouting'] = self.object.richieste_personale.all()

        return context


# ============================================================================
# LISTE PRODOTTI (ENGINEERING)
# ============================================================================

class ListaProdottiCreateView(
    PermissionRequiredMixin,
    SetCreatedByMixin,
    FormValidMessageMixin,
    CreateView
):
    """
    Creazione lista prodotti da parte dell'ingegnere.
    """
    model = ListaProdotti
    form_class = ListaProdottiForm
    template_name = 'progetti_eventi/lista_prodotti_form.html'
    permission_required = 'progetti_eventi.add_listaprodotti'
    success_message = "Lista prodotti creata con successo!"

    def dispatch(self, request, *args, **kwargs):
        # Ottieni ProgettoReparto dal parametro URL
        self.progetto_reparto = get_object_or_404(ProgettoReparto, pk=kwargs.get('reparto_pk'))
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['progetto_reparto'] = self.progetto_reparto

        # Formset prodotti
        if self.request.POST:
            context['formset'] = ProdottoListaFormSet(self.request.POST)
        else:
            context['formset'] = ProdottoListaFormSet()

        return context

    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']

        # Associa al reparto
        form.instance.progetto_reparto = self.progetto_reparto

        if formset.is_valid():
            self.object = form.save()

            # Salva prodotti
            formset.instance = self.object
            formset.save()

            messages.success(
                self.request,
                f"Lista '{self.object.nome_lista}' creata con {self.object.numero_prodotti} prodotti."
            )
            return redirect(self.object.get_absolute_url())
        else:
            return self.form_invalid(form)

    def get_success_url(self):
        return self.progetto_reparto.get_absolute_url()


class ListaProdottiDetailView(PermissionRequiredMixin, DetailView):
    """
    Dettaglio lista prodotti con possibilità di approvazione.
    """
    model = ListaProdotti
    template_name = 'progetti_eventi/lista_prodotti_detail.html'
    context_object_name = 'lista'
    permission_required = 'progetti_eventi.view_listaprodotti'

    def get_queryset(self):
        return super().get_queryset().select_related(
            'progetto_reparto__progetto',
            'approvata_da'
        ).prefetch_related('prodotti')


class ListaProdottiApprovaView(PermissionRequiredMixin, DetailView):
    """
    Approva una lista prodotti.
    """
    model = ListaProdotti
    permission_required = 'progetti_eventi.change_listaprodotti'

    def post(self, request, *args, **kwargs):
        lista = self.get_object()
        note = request.POST.get('note_approvazione', '')

        try:
            lista.approva(user=request.user, note=note)
            messages.success(
                request,
                f"Lista '{lista.nome_lista}' approvata con successo!"
            )
        except Exception as e:
            messages.error(request, f"Errore: {str(e)}")

        return redirect(lista.get_absolute_url())
