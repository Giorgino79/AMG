"""
Views per l'app users.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required, permission_required
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from django.db.models import Q, Sum
from django.db import transaction
from django.core.paginator import Paginator
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from datetime import datetime, date, timedelta

from .models import (
    User,
    Timbratura,
    GiornataLavorativa,
    RichiestaFerie,
    RichiestaPermesso,
    LetteraRichiamo,
)
from .forms import (
    LoginForm,
    UserCreateForm,
    UserUpdateForm,
    UserProfiloForm,
    TimbraturaForm,
    TimbraturaQuickForm,
    RichiestaFerieForm,
    RichiestaPermessoForm,
    ApprovaRifiutaForm,
    LetteraRichiamoForm,
)
from .forms_permissions import UserPermissionsForm


# ============================================================================
# AUTENTICAZIONE
# ============================================================================


@require_http_methods(["GET", "POST"])
def login_view(request):
    """
    Vista login.

    - GET: mostra form login
    - POST: autentica user e redirect a dashboard

    Remember me: imposta sessione a 30 giorni
    """
    # Se già autenticato, redirect a dashboard
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        form = LoginForm(request, data=request.POST)

        if form.is_valid():
            user = form.get_user()

            # Login user
            login(request, user)

            # Remember me
            if form.cleaned_data.get("remember_me"):
                # Sessione valida 30 giorni
                request.session.set_expiry(60 * 60 * 24 * 30)  # 30 giorni
            else:
                # Sessione scade alla chiusura browser
                request.session.set_expiry(0)

            # Log ultimo accesso
            user.last_login = timezone.now()
            user.save(update_fields=["last_login"])

            # Success message
            messages.success(
                request, f"Benvenuto, {user.get_full_name() or user.username}!"
            )

            # Redirect a next o dashboard
            next_url = request.GET.get("next") or request.POST.get("next")
            if next_url:
                return redirect(next_url)
            return redirect("dashboard")

        else:
            # Form non valido
            messages.error(request, "Credenziali non valide. Riprova.")

    else:
        form = LoginForm()

    context = {
        "form": form,
    }

    return render(request, "login.html", context)


@require_http_methods(["GET", "POST"])
def logout_view(request):
    """
    Vista logout.

    Esegue logout e redirect a login page.
    """
    logout(request)
    messages.info(request, "Logout effettuato con successo.")
    return redirect("users:login")


# ============================================================================
# DASHBOARD
# ============================================================================


@login_required
def dashboard_view(request):
    """
    Dashboard centrale del sistema.

    Visualizza:
    - Stats generali
    - Notifiche
    - Azioni rapide
    - Promemoria
    - Chat
    """
    # Stats reali
    oggi = date.today()

    # Users attivi
    users_attivi = User.objects.filter(stato="attivo").count()

    # Ore oggi dell'utente corrente
    giornata_oggi = request.user.giornate.filter(data=oggi).first()
    ore_oggi = giornata_oggi.ore_totali if giornata_oggi else 0

    # Richieste pending dell'utente
    ferie_pending = request.user.richieste_ferie.filter(stato="in_attesa").count()
    permessi_pending = request.user.richieste_permessi.filter(stato="in_attesa").count()
    richieste_pending = ferie_pending + permessi_pending

    # Template Permessi (solo per admin)
    template_permessi_attivi = 0
    template_permessi_totali = 0
    if request.user.has_perm('users.gestione_completa_users'):
        from core.models_permissions import PermissionTemplate
        template_permessi_attivi = PermissionTemplate.objects.filter(attivo=True).count()
        template_permessi_totali = PermissionTemplate.objects.count()

    # Mail App Stats - Promemoria e Chat
    from mail.models import Promemoria, ChatConversation, ChatMessage

    # Promemoria assegnati all'utente (pending)
    promemoria_attivi = Promemoria.objects.filter(
        assegnato_a=request.user,
        is_active=True,
        stato='pending'
    ).count()

    # Promemoria recenti assegnati all'utente
    recent_promemoria = Promemoria.objects.filter(
        Q(assegnato_a=request.user) | Q(created_by=request.user),
        is_active=True
    ).distinct().order_by('-created_at')[:5]

    total_conversations = ChatConversation.objects.filter(
        partecipanti=request.user,
        is_active=True
    ).count()

    # Count unread chat messages
    unread_messages = ChatMessage.objects.filter(
        conversation__partecipanti=request.user,
        # is_read=False,
        # is_active=True
    ).exclude(sender=request.user).count()

    stats = {
        "users_attivi": users_attivi,
        "ore_oggi": ore_oggi,
        "richieste_pending": richieste_pending,
        "template_permessi_attivi": template_permessi_attivi,
        "template_permessi_totali": template_permessi_totali,
        "promemoria_attivi": promemoria_attivi,
        "total_conversations": total_conversations,
        "unread_messages": unread_messages,
    }

    # Affidamento mezzo attivo per l'utente corrente
    from automezzi.models import AffidamentoMezzo
    mio_affidamento = AffidamentoMezzo.objects.filter(
        user=request.user,
        stato__in=["in_attesa", "accettato", "in_corso"],
    ).select_related("automezzo").first()

    context = {
        "stats": stats,
        "today": oggi,
        "recent_promemoria": recent_promemoria,
        "mio_affidamento": mio_affidamento,
    }

    return render(request, "commons_templates/dashboard.html", context)


# ============================================================================
# CRUD USERS
# ============================================================================


@login_required
@permission_required("users.view_user", raise_exception=True)
def user_list_view(request):
    """
    Lista users con filtri e paginazione.

    Filtri:
    - Stato (attivo, sospeso, cessato, in_prova)
    - Qualifica
    - Reparto
    - Ricerca testuale (nome, username, codice)
    """
    users = User.objects.all().order_by("-date_joined")

    # Filtri
    stato = request.GET.get("stato")
    if stato:
        users = users.filter(stato=stato)

    qualifica = request.GET.get("qualifica")
    if qualifica:
        users = users.filter(qualifica__icontains=qualifica)

    reparto = request.GET.get("reparto")
    if reparto:
        users = users.filter(reparto__icontains=reparto)

    # Ricerca
    q = request.GET.get("q")
    if q:
        users = users.filter(
            Q(username__icontains=q)
            | Q(first_name__icontains=q)
            | Q(last_name__icontains=q)
            | Q(codice_dipendente__icontains=q)
            | Q(email__icontains=q)
        )

    # Paginazione
    paginator = Paginator(users, 25)
    page = request.GET.get("page")
    users_page = paginator.get_page(page)

    context = {
        "users": users_page,
        "total": users.count(),
    }

    return render(request, "users/user_list.html", context)


@login_required
@permission_required("users.add_user", raise_exception=True)
@require_http_methods(["GET", "POST"])
def user_create_view(request):
    """
    Crea nuovo user con template permessi.

    Features:
    - Auto-generazione codice_dipendente
    - Template permessi predefiniti
    - Permessi custom opzionali
    """
    if request.method == "POST":
        form = UserCreateForm(request.POST, request.FILES)

        if form.is_valid():
            user = form.save()
            messages.success(
                request,
                f"User {user.username} (codice: {user.codice_dipendente}) creato con successo!",
            )
            return redirect("users:user_detail", pk=user.pk)
        else:
            # Mostra errori specifici per ogni campo
            for field, errors in form.errors.items():
                for error in errors:
                    if field == '__all__':
                        messages.error(request, f"Errore: {error}")
                    else:
                        field_label = form.fields.get(field).label if field in form.fields else field
                        messages.error(request, f"{field_label}: {error}")
    else:
        form = UserCreateForm()

    context = {
        "form": form,
        "title": "Crea Nuovo User",
    }

    return render(request, "users/user_form.html", context)


@login_required
@permission_required("users.view_user", raise_exception=True)
def user_detail_view(request, pk):
    """
    Dettaglio user con:
    - Dati anagrafici
    - Stats timbrature
    - Richieste ferie/permessi
    - Lettere richiamo
    - Allegati (via core)

    Usa il sistema di componenti per layout consistente.
    """
    user = get_object_or_404(User, pk=pk)

    # Stats timbrature
    oggi = date.today()
    mese_corrente = oggi.replace(day=1)
    timbrature_mese = user.timbrature.filter(data__gte=mese_corrente).count()
    giornate_mese = user.giornate.filter(data__gte=mese_corrente)
    ore_mese = giornate_mese.aggregate(totale=Sum("ore_totali"))["totale"] or 0

    # Richieste pending
    ferie_pending = user.richieste_ferie.filter(stato="in_attesa").count()
    permessi_pending = user.richieste_permessi.filter(stato="in_attesa").count()

    # Lettere richiamo non lette
    lettere_non_lette = user.lettere_richiamo.filter(user_ha_letto=False).count()

    # ContentType per sistema allegati
    content_type = ContentType.objects.get_for_model(User)

    # Breadcrumb
    breadcrumbs = [
        {'label': 'Dashboard', 'url': '/'},
        {'label': 'Dipendenti', 'url': '/users/'},
        {'label': user.get_full_name() or user.username, 'url': None},
    ]

    # Detail Layout Config
    detail_config = {
        'title': user.get_full_name() or user.username,
        'subtitle': f'Codice Dipendente: {user.codice_dipendente} | Username: {user.username}',
        'sections': [
            {
                'title': 'Dati Anagrafici',
                'icon': 'bi-person-vcard',
                'fields': [
                    {'label': 'Email', 'value': user.email or '-'},
                    {
                        'label': 'Data Nascita',
                        'value': f'{user.data_nascita.strftime("%d/%m/%Y")} ({user.eta} anni)' if user.data_nascita and user.eta else (user.data_nascita.strftime("%d/%m/%Y") if user.data_nascita else '-')
                    },
                    {'label': 'Luogo Nascita', 'value': user.luogo_nascita or '-'},
                    {'label': 'Codice Fiscale', 'value': user.codice_fiscale or '-'},
                    {'label': 'Telefono', 'value': user.telefono or '-'},
                    {'label': 'Telefono Emergenza', 'value': user.telefono_emergenza or '-'},
                    {
                        'label': 'Indirizzo',
                        'value': f'{user.indirizzo}<br>{user.cap} {user.citta} ({user.provincia})' if user.indirizzo else '-'
                    },
                ]
            },
            {
                'title': 'Dati Lavorativi',
                'icon': 'bi-briefcase',
                'fields': [
                    {
                        'label': 'Stato',
                        'value': user.get_stato_display(),
                        'badge': True,
                        'badge_color': 'success' if user.stato == 'attivo' else ('warning' if user.stato == 'sospeso' else 'secondary')
                    },
                    {'label': 'Qualifica', 'value': user.qualifica or '-'},
                    {'label': 'Reparto', 'value': user.reparto or '-'},
                    {
                        'label': 'Data Assunzione',
                        'value': f'{user.data_assunzione.strftime("%d/%m/%Y")} ({user.anni_servizio} anni)' if user.data_assunzione and user.anni_servizio else (user.data_assunzione.strftime("%d/%m/%Y") if user.data_assunzione else '-')
                    },
                    {
                        'label': 'Data Cessazione',
                        'value': user.data_cessazione.strftime("%d/%m/%Y") if user.data_cessazione else '-'
                    },
                    {'label': 'Ferie Annuali', 'value': f'{user.giorni_ferie_anno} giorni'},
                    {'label': 'Ferie Utilizzate', 'value': f'{user.ferie_utilizzate} giorni'},
                    {'label': 'Ferie Residue', 'value': f'{user.giorni_ferie_residui} giorni'},
                    {'label': 'Permessi Residui', 'value': f'{user.ore_permesso_residue} ore'},
                ]
            },
            {
                'title': 'Statistiche Mese Corrente',
                'icon': 'bi-graph-up',
                'fields': [
                    {'label': 'Timbrature', 'value': timbrature_mese},
                    {'label': 'Ore Lavorate', 'value': f'{ore_mese:.2f} ore'},
                    {
                        'label': 'Richieste Pending',
                        'value': ferie_pending + permessi_pending,
                        'badge': True if (ferie_pending + permessi_pending) > 0 else False,
                        'badge_color': 'warning'
                    },
                    {
                        'label': 'Lettere Richiamo Non Lette',
                        'value': lettere_non_lette,
                        'badge': True if lettere_non_lette > 0 else False,
                        'badge_color': 'danger'
                    },
                ]
            },
        ],
        'back_url': 'users:user_list',
        'show_header': False,  # Header gestito direttamente nel template
        'show_allegati': True,
        'show_metadata': True,
        # Sidebar custom content
        'sidebar_template': 'users/includes/user_detail_sidebar.html',
    }

    # Verifica se l'utente corrente può gestire questo utente
    can_manage_user = (
        request.user.is_staff or
        request.user.is_superuser or
        request.user.has_perm('users.change_user')
    )

    context = {
        "user_obj": user,
        "object": user,
        "content_type_id": content_type.id,
        "timbrature_mese": timbrature_mese,
        "ore_mese": ore_mese,
        "ferie_pending": ferie_pending,
        "permessi_pending": permessi_pending,
        "lettere_non_lette": lettere_non_lette,
        "can_manage_user": can_manage_user,  # Per mostrare sezione gestione nella sidebar
        # Config per componenti
        "breadcrumbs": breadcrumbs,
        "detail_config": detail_config,
    }

    return render(request, "users/user_detail.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def user_update_view(request, pk):
    """
    Modifica user.

    Permessi:
    - Admin: tutti i campi
    - User stesso: solo foto profilo
    """
    user = get_object_or_404(User, pk=pk)

    # Check permessi
    if not request.user.has_perm("users.change_user"):
        # User può modificare solo sé stesso (foto profilo)
        if request.user.pk != user.pk:
            messages.error(request, "Non hai i permessi per modificare questo user.")
            return redirect("users:user_detail", pk=pk)

        # Form profilo limitato
        if request.method == "POST":
            form = UserProfiloForm(request.POST, request.FILES, instance=user)
            if form.is_valid():
                form.save()
                messages.success(request, "Foto profilo aggiornata!")
                return redirect("users:user_detail", pk=pk)
        else:
            form = UserProfiloForm(instance=user)

        context = {
            "form": form,
            "user_obj": user,
            "title": "Modifica Foto Profilo",
        }
        return render(request, "users/user_profilo_form.html", context)

    # Admin: form completo
    if request.method == "POST":
        form = UserUpdateForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, f"User {user.username} aggiornato con successo!")
            return redirect("users:user_detail", pk=pk)
        else:
            messages.error(request, "Errore nell'aggiornamento. Verifica i campi.")
    else:
        form = UserUpdateForm(instance=user)

    context = {
        "form": form,
        "user_obj": user,
        "title": f"Modifica User: {user.username}",
    }

    return render(request, "users/user_form.html", context)


# ============================================================================
# TIMBRATURE
# ============================================================================


@login_required
@require_http_methods(["POST"])
def timbratura_quick_view(request):
    """
    Timbratura veloce da modal.

    Features:
    - Solo tipo e turno
    - Data/ora automatiche
    - Risposta JSON
    - Crea/aggiorna automaticamente GiornataLavorativa
    """
    form = TimbraturaQuickForm(request.POST)

    if form.is_valid():
        timbratura = Timbratura.objects.create(
            user=request.user,
            tipo=form.cleaned_data["tipo"],
            turno=form.cleaned_data["turno"],
            data=date.today(),
            ora=datetime.now().time(),
        )

        # Crea o aggiorna la giornata lavorativa
        giornata, created = GiornataLavorativa.objects.get_or_create(
            user=request.user, data=timbratura.data
        )
        giornata.calcola_ore()
        giornata.save()

        return JsonResponse(
            {
                "success": True,
                "message": f"Timbratura {timbratura.get_tipo_display()} - {timbratura.get_turno_display()} registrata!",
                "data": timbratura.data.isoformat(),
                "ora": timbratura.ora.strftime("%H:%M"),
            }
        )
    else:
        return JsonResponse({"success": False, "errors": form.errors}, status=400)


@login_required
@require_http_methods(["POST"])
def chiudi_giornata_view(request):
    """
    Chiude la giornata lavorativa corrente.

    Features:
    - Calcola ore totali e straordinari
    - Marca giornata come conclusa
    - Risposta JSON
    """
    oggi = date.today()

    try:
        giornata, created = GiornataLavorativa.objects.get_or_create(
            user=request.user, data=oggi
        )

        # Calcola le ore
        giornata.calcola_ore()
        giornata.conclusa = True
        giornata.save()

        return JsonResponse(
            {
                "success": True,
                "message": f"Giornata chiusa! Ore totali: {giornata.ore_totali}h, Straordinari: {giornata.ore_straordinarie}h",
                "ore_totali": float(giornata.ore_totali),
                "ore_mattina": float(giornata.ore_mattina),
                "ore_pomeriggio": float(giornata.ore_pomeriggio),
                "ore_notte": float(giornata.ore_notte),
                "ore_straordinarie": float(giornata.ore_straordinarie),
            }
        )
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=400)


@login_required
def timbratura_list_view(request):
    """
    Lista timbrature user con filtri.

    Filtri:
    - Data range
    - Turno
    """
    timbrature = request.user.timbrature.all().order_by("-data", "-ora")

    # Filtri
    data_da = request.GET.get("data_da")
    if data_da:
        timbrature = timbrature.filter(data__gte=data_da)

    data_a = request.GET.get("data_a")
    if data_a:
        timbrature = timbrature.filter(data__lte=data_a)

    turno = request.GET.get("turno")
    if turno:
        timbrature = timbrature.filter(turno=turno)

    # Paginazione
    paginator = Paginator(timbrature, 50)
    page = request.GET.get("page")
    timbrature_page = paginator.get_page(page)

    context = {
        "timbrature": timbrature_page,
    }

    return render(request, "users/timbratura_list.html", context)


@login_required
def giornata_lavorativa_list_view(request):
    """
    Lista giornate lavorative con stats e filtri.

    Features:
    - Filtri per range di date (data_da, data_a)
    - Filtro per stato (conclusa/in_corso)
    - Totale ore periodo
    - Totale straordinari
    - Media ore/giorno
    - Export Excel/PDF
    """
    giornate = request.user.giornate.all().order_by("-data")

    # Filtri data
    data_da = request.GET.get("data_da")
    data_a = request.GET.get("data_a")

    # Default: mese corrente se non specificato
    if not data_da and not data_a:
        oggi = date.today()
        data_da = date(oggi.year, oggi.month, 1)
        data_a = date(oggi.year, oggi.month + 1, 1) - timedelta(days=1) if oggi.month < 12 else date(oggi.year, 12, 31)
    else:
        if data_da:
            try:
                data_da = datetime.strptime(data_da, "%Y-%m-%d").date()
                giornate = giornate.filter(data__gte=data_da)
            except ValueError:
                data_da = None

        if data_a:
            try:
                data_a = datetime.strptime(data_a, "%Y-%m-%d").date()
                giornate = giornate.filter(data__lte=data_a)
            except ValueError:
                data_a = None

    # Filtro stato
    stato = request.GET.get("stato")
    if stato == "conclusa":
        giornate = giornate.filter(conclusa=True)
    elif stato == "in_corso":
        giornate = giornate.filter(conclusa=False)

    # Stats
    ore_totali = giornate.aggregate(totale=Sum("ore_totali"))["totale"] or 0
    straordinari = giornate.aggregate(totale=Sum("ore_straordinarie"))["totale"] or 0

    # Media ore/giorno
    num_giornate = giornate.count()
    media_ore = ore_totali / num_giornate if num_giornate > 0 else 0

    context = {
        "giornate": giornate,
        "ore_totali": ore_totali,
        "straordinari": straordinari,
        "media_ore": media_ore,
        "data_da": data_da.strftime("%Y-%m-%d") if isinstance(data_da, date) else data_da,
        "data_a": data_a.strftime("%Y-%m-%d") if isinstance(data_a, date) else data_a,
    }

    return render(request, "users/giornata_list.html", context)


# ============================================================================
# FERIE E PERMESSI
# ============================================================================


@login_required
@require_http_methods(["GET", "POST"])
def richiesta_ferie_create_view(request):
    """
    Richiedi ferie.

    Features:
    - Calcolo automatico giorni lavorativi
    - Validazione giorni disponibili
    - Validazione sovrapposizioni ferie
    """
    if request.method == "POST":
        form = RichiestaFerieForm(request.POST)

        if form.is_valid():
            try:
                richiesta = form.save(commit=False)
                richiesta.user = request.user

                # Valida giorni disponibili
                if richiesta.giorni_richiesti > request.user.giorni_ferie_residui:
                    messages.error(
                        request,
                        f"Giorni richiesti ({richiesta.giorni_richiesti}) superiori a giorni disponibili ({request.user.giorni_ferie_residui})",
                    )
                    return render(
                        request, "users/richiesta_ferie_form.html", {"form": form}
                    )

                # Il save() nel form chiama full_clean() che valida le sovrapposizioni
                form_with_user = RichiestaFerieForm(request.POST, instance=richiesta)
                if form_with_user.is_valid():
                    form_with_user.save()
                    messages.success(
                        request, "Richiesta ferie inviata! In attesa di approvazione."
                    )
                    return redirect("users:richieste_ferie_list")
                else:
                    # Mostri errori della validazione model
                    for field, errors in form_with_user.errors.items():
                        for error in errors:
                            messages.error(request, str(error))
                    return render(
                        request, "users/richiesta_ferie_form.html", {"form": form_with_user}
                    )
            except ValidationError as e:
                messages.error(request, str(e))
                return render(
                    request, "users/richiesta_ferie_form.html", {"form": form}
                )
        else:
            messages.error(request, "Errore nella richiesta. Verifica i campi.")
    else:
        form = RichiestaFerieForm()

    context = {
        "form": form,
        "giorni_disponibili": request.user.giorni_ferie_residui,
    }

    return render(request, "users/richiesta_ferie_form.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def richiesta_permesso_create_view(request):
    """
    Richiedi permesso orario.

    Features:
    - Calcolo automatico ore
    - Validazione ore disponibili
    """
    if request.method == "POST":
        form = RichiestaPermessoForm(request.POST)

        if form.is_valid():
            richiesta = form.save(commit=False)
            richiesta.user = request.user

            # Valida ore disponibili
            if richiesta.ore_richieste > request.user.ore_permesso_residue:
                messages.error(
                    request,
                    f"Ore richieste ({richiesta.ore_richieste}) superiori a ore disponibili ({request.user.ore_permesso_residue})",
                )
                return render(
                    request, "users/richiesta_permesso_form.html", {"form": form}
                )

            richiesta.save()
            messages.success(
                request, "Richiesta permesso inviata! In attesa di approvazione."
            )
            return redirect("users:richieste_permessi_list")
        else:
            messages.error(request, "Errore nella richiesta. Verifica i campi.")
    else:
        form = RichiestaPermessoForm()

    context = {
        "form": form,
        "ore_disponibili": request.user.ore_permesso_residue,
    }

    return render(request, "users/richiesta_permesso_form.html", context)


@login_required
def richieste_ferie_list_view(request):
    """
    Lista richieste ferie user.

    Filtri:
    - Stato (in_attesa, approvata, rifiutata)
    """
    richieste = request.user.richieste_ferie.all().order_by("-created_at")

    # Filtro stato
    stato = request.GET.get("stato")
    if stato:
        richieste = richieste.filter(stato=stato)

    # Paginazione
    paginator = Paginator(richieste, 20)
    page = request.GET.get("page")
    richieste_page = paginator.get_page(page)

    context = {
        "richieste": richieste_page,
    }

    return render(request, "users/richieste_ferie_list.html", context)


@login_required
def richieste_permessi_list_view(request):
    """
    Lista richieste permessi user.

    Filtri:
    - Stato (in_attesa, approvata, rifiutata)
    """
    richieste = request.user.richieste_permessi.all().order_by("-created_at")

    # Filtro stato
    stato = request.GET.get("stato")
    if stato:
        richieste = richieste.filter(stato=stato)

    # Paginazione
    paginator = Paginator(richieste, 20)
    page = request.GET.get("page")
    richieste_page = paginator.get_page(page)

    context = {
        "richieste": richieste_page,
    }

    return render(request, "users/richieste_permessi_list.html", context)


@login_required
@permission_required("users.approva_ferie", raise_exception=True)
def richiesta_ferie_gestisci_view(request, pk):
    """
    Approva/Rifiuta richiesta ferie.

    Permessi: users.approva_ferie
    """
    richiesta = get_object_or_404(RichiestaFerie, pk=pk)

    if request.method == "POST":
        form = ApprovaRifiutaForm(request.POST)

        if form.is_valid():
            azione = form.cleaned_data["azione"]

            if azione == "approva":
                richiesta.approva(amministratore=request.user)
                messages.success(
                    request,
                    f"Richiesta ferie di {richiesta.user.get_full_name()} approvata!",
                )
            else:
                motivazione = form.cleaned_data["motivazione_rifiuto"]
                richiesta.rifiuta(amministratore=request.user, motivazione=motivazione)
                messages.warning(
                    request,
                    f"Richiesta ferie di {richiesta.user.get_full_name()} rifiutata.",
                )

            return redirect("users:richieste_ferie_admin_list")
        else:
            messages.error(request, "Errore nella gestione richiesta.")
            return redirect("users:richieste_ferie_admin_list")

    # GET - mostra dettaglio richiesta
    altre_richieste = (
        RichiestaFerie.objects.filter(user=richiesta.user)
        .exclude(pk=pk)
        .order_by("-created_at")[:5]
    )

    context = {
        "richiesta": richiesta,
        "altre_richieste": altre_richieste,
    }

    return render(request, "users/richiesta_ferie_gestisci.html", context)


@login_required
@permission_required("users.approva_permessi", raise_exception=True)
def richiesta_permesso_gestisci_view(request, pk):
    """
    Approva/Rifiuta richiesta permesso.

    Permessi: users.approva_permessi
    """
    richiesta = get_object_or_404(RichiestaPermesso, pk=pk)

    if request.method == "POST":
        form = ApprovaRifiutaForm(request.POST)

        if form.is_valid():
            azione = form.cleaned_data["azione"]

            if azione == "approva":
                richiesta.approva(amministratore=request.user)
                messages.success(
                    request,
                    f"Richiesta permesso di {richiesta.user.get_full_name()} approvata!",
                )
            else:
                motivazione = form.cleaned_data["motivazione_rifiuto"]
                richiesta.rifiuta(amministratore=request.user, motivazione=motivazione)
                messages.warning(
                    request,
                    f"Richiesta permesso di {richiesta.user.get_full_name()} rifiutata.",
                )

            return redirect("users:richieste_permessi_admin_list")
        else:
            messages.error(request, "Errore nella gestione richiesta.")
            return redirect("users:richieste_permessi_admin_list")

    # GET - mostra dettaglio richiesta
    altre_richieste = (
        RichiestaPermesso.objects.filter(user=richiesta.user)
        .exclude(pk=pk)
        .order_by("-created_at")[:5]
    )

    context = {
        "richiesta": richiesta,
        "altre_richieste": altre_richieste,
    }

    return render(request, "users/richiesta_permesso_gestisci.html", context)


@login_required
@permission_required("users.approva_ferie", raise_exception=True)
def richieste_ferie_admin_list_view(request):
    """
    Lista tutte richieste ferie (admin).

    Filtri:
    - Stato
    - User
    """
    filter_type = request.GET.get("filter", "in_attesa")

    if filter_type == "tutte":
        richieste = RichiestaFerie.objects.all()
    else:
        richieste = RichiestaFerie.objects.filter(stato=filter_type)

    richieste = richieste.select_related("user").order_by("-created_at")

    # Richieste pending per badge
    richieste_pending = RichiestaFerie.objects.filter(stato="in_attesa")

    # Paginazione
    paginator = Paginator(richieste, 20)
    page = request.GET.get("page")
    richieste_page = paginator.get_page(page)

    context = {
        "richieste": richieste_page,
        "richieste_pending": richieste_pending,
        "filter": filter_type,
    }

    return render(request, "users/richieste_ferie_admin_list.html", context)


@login_required
@permission_required("users.approva_permessi", raise_exception=True)
def richieste_permessi_admin_list_view(request):
    """
    Lista tutte richieste permessi (admin).

    Filtri:
    - Stato
    - User
    """
    filter_type = request.GET.get("filter", "in_attesa")

    if filter_type == "tutte":
        richieste = RichiestaPermesso.objects.all()
    else:
        richieste = RichiestaPermesso.objects.filter(stato=filter_type)

    richieste = richieste.select_related("user").order_by("-created_at")

    # Richieste pending per badge
    richieste_pending = RichiestaPermesso.objects.filter(stato="in_attesa")

    # Paginazione
    paginator = Paginator(richieste, 20)
    page = request.GET.get("page")
    richieste_page = paginator.get_page(page)

    context = {
        "richieste": richieste_page,
        "richieste_pending": richieste_pending,
        "filter": filter_type,
    }

    return render(request, "users/richieste_permessi_admin_list.html", context)


# ============================================================================
# LETTERA RICHIAMO
# ============================================================================


@login_required
@permission_required("users.emetti_lettera_richiamo", raise_exception=True)
@require_http_methods(["GET", "POST"])
def lettera_richiamo_create_view(request):
    """
    Emetti lettera di richiamo.

    Permessi: users.emetti_lettera_richiamo
    """
    if request.method == "POST":
        form = LetteraRichiamoForm(request.POST)

        if form.is_valid():
            lettera = form.save(commit=False)
            lettera.emessa_da = request.user
            lettera.save()

            messages.success(
                request,
                f"Lettera di richiamo {lettera.get_tipo_display()} emessa per {lettera.user.get_full_name()}.",
            )
            return redirect("users:user_detail", pk=lettera.user.pk)
        else:
            messages.error(request, "Errore nell'emissione lettera.")
    else:
        form = LetteraRichiamoForm()

    context = {
        "form": form,
    }

    return render(request, "users/lettera_richiamo_form.html", context)


@login_required
def lettera_richiamo_list_view(request):
    """
    Lista lettere richiamo.

    - Admin/Responsabili: vedono tutte le lettere con filtri
    - Dipendenti: vedono solo le proprie lettere
    """
    # Se admin o ha permessi, mostra tutte
    if request.user.is_superuser or request.user.has_perm(
        "users.emetti_lettera_richiamo"
    ):
        lettere = LetteraRichiamo.objects.all().select_related("user", "emessa_da")

        # Filtri
        search = request.GET.get("search")
        if search:
            lettere = lettere.filter(
                Q(user__first_name__icontains=search)
                | Q(user__last_name__icontains=search)
                | Q(user__codice_dipendente__icontains=search)
            )

        tipo = request.GET.get("tipo")
        if tipo:
            lettere = lettere.filter(tipo=tipo)

        data_da = request.GET.get("data_da")
        if data_da:
            lettere = lettere.filter(data_emissione__gte=data_da)

        data_a = request.GET.get("data_a")
        if data_a:
            lettere = lettere.filter(data_emissione__lte=data_a)
    else:
        # Dipendente: solo le proprie
        lettere = request.user.lettere_richiamo.all()

        # Segna come lette
        lettere.filter(user_ha_letto=False).update(
            user_ha_letto=True, data_lettura=timezone.now()
        )

    lettere = lettere.order_by("-data_emissione")

    context = {
        "lettere": lettere,
    }

    return render(request, "users/lettera_richiamo_list.html", context)


# ============================================================================
# PROFILO E IMPOSTAZIONI
# ============================================================================


@login_required
def profilo_view(request):
    """
    Visualizza e modifica il profilo dell'utente corrente.
    """
    if request.method == "POST":
        form = UserProfiloForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profilo aggiornato con successo!")
            return redirect("users:profilo")
    else:
        form = UserProfiloForm(instance=request.user)

    context = {
        "form": form,
        "user": request.user,
    }
    return render(request, "users/profilo.html", context)


@login_required
def impostazioni_view(request):
    """
    Pagina impostazioni utente (notifiche, privacy, ecc).
    """
    context = {
        "user": request.user,
    }
    return render(request, "users/impostazioni.html", context)


# ============================================================================
# GESTIONE PERMESSI UTENTE
# ============================================================================


@login_required
@permission_required("users.change_user", raise_exception=True)
@require_http_methods(["GET", "POST"])
def user_permissions_manage_view(request, pk):
    """
    Gestione permessi CRUD per un utente.

    Permessi richiesti: users.change_user

    Features:
    - Form dinamico con permessi per tutti i modelli registrati
    - Raggruppamento per categoria
    - Card Bootstrap per visualizzazione CRUD
    - Salvataggio batch dei permessi

    Args:
        pk: ID dell'utente da gestire
    """
    user_obj = get_object_or_404(User, pk=pk)

    if request.method == "POST":
        form = UserPermissionsForm(request.POST, user_obj=user_obj)

        if form.is_valid():
            try:
                # Salva permessi
                form.save()

                messages.success(
                    request,
                    f"Permessi per {user_obj.get_full_name() or user_obj.username} aggiornati con successo!",
                )
                return redirect("users:user_detail", pk=pk)

            except Exception as e:
                messages.error(request, f"Errore nel salvataggio permessi: {str(e)}")
        else:
            messages.error(request, "Errore nella validazione form. Verifica i campi.")
    else:
        # GET: inizializza form con permessi attuali
        form = UserPermissionsForm(user_obj=user_obj)

    # Raggruppa campi per categoria per il template
    fields_by_category = form.get_fields_by_category()

    # Template disponibili (solo per admin)
    available_templates = []
    if request.user.has_perm('users.gestione_completa_users'):
        from core.models_permissions import PermissionTemplate
        available_templates = PermissionTemplate.objects.filter(attivo=True).order_by('nome')

    context = {
        "form": form,
        "user_obj": user_obj,
        "fields_by_category": fields_by_category,
        "available_templates": available_templates,
        "title": f"Gestione Permessi - {user_obj.get_full_name() or user_obj.username}",
    }

    return render(request, "users/user_permissions_form.html", context)


@login_required
@permission_required("users.gestione_completa_users", raise_exception=True)
@require_http_methods(["POST"])
def user_permissions_apply_template_view(request, pk):
    """
    Applica un template di permessi a un utente.

    Permessi richiesti: users.gestione_completa_users

    Features:
    - Applica tutti i permessi (CRUD + base) del template
    - Opzione per sovrascrivere permessi esistenti
    - Incrementa contatore utilizzi template
    """
    user_obj = get_object_or_404(User, pk=pk)

    template_id = request.POST.get('template_id')
    sovrascrivi = request.POST.get('sovrascrivi') == '1'

    if not template_id:
        messages.error(request, "Nessun template selezionato.")
        return redirect('users:user_permissions_manage', pk=pk)

    try:
        from core.models_permissions import PermissionTemplate
        template = get_object_or_404(PermissionTemplate, pk=template_id, attivo=True)

        with transaction.atomic():
            # Se sovrascrivi, rimuovi tutti i permessi esistenti
            if sovrascrivi:
                user_obj.user_permissions.clear()

            # Applica il template
            stats = template.applica_a_utente(user_obj)

            # Messaggio di successo
            total_added = stats['permessi_crud_aggiunti'] + stats['permessi_base_aggiunti']
            messages.success(
                request,
                f"Template '{template.nome}' applicato con successo! "
                f"Aggiunti {total_added} permessi "
                f"({stats['permessi_crud_aggiunti']} CRUD + {stats['permessi_base_aggiunti']} base)."
            )

            # Eventuali errori
            if stats['errori']:
                for errore in stats['errori']:
                    messages.warning(request, f"Attenzione: {errore}")

        return redirect('users:user_permissions_manage', pk=pk)

    except Exception as e:
        messages.error(request, f"Errore nell'applicazione del template: {str(e)}")
        return redirect('users:user_permissions_manage', pk=pk)


# ============================================================================
# EXPORT GIORNATE (PDF/EXCEL)
# ============================================================================


@login_required
def giornate_export_excel(request):
    """
    Esporta giornate lavorative in Excel.
    """
    from core.excel_generator import generate_excel_response

    # Ottieni giornate (con eventuali filtri)
    giornate = request.user.giornate.all().order_by("-data")

    # Filtro mese se presente
    mese = request.GET.get("mese")
    if mese:
        try:
            anno, mese_num = mese.split("-")
            giornate = giornate.filter(data__year=anno, data__month=mese_num)
        except ValueError:
            pass

    # Prepara dati
    data = []
    for g in giornate:
        data.append(
            {
                "Data": g.data,
                "Ore Mattina": float(g.ore_mattina),
                "Ore Pomeriggio": float(g.ore_pomeriggio),
                "Ore Notte": float(g.ore_notte),
                "Ore Totali": float(g.ore_totali),
                "Straordinari": float(g.ore_straordinarie),
                "Conclusa": "Sì" if g.conclusa else "No",
                "Note": g.note or "-",
            }
        )

    # Headers personalizzati
    headers = [
        "Data",
        "Ore Mattina",
        "Ore Pomeriggio",
        "Ore Notte",
        "Ore Totali",
        "Straordinari",
        "Conclusa",
        "Note",
    ]

    # Nome file
    filename = f"giornate_lavorative_{request.user.username}_{timezone.now().strftime('%Y%m%d')}"

    return generate_excel_response(
        data, filename, sheet_name="Giornate Lavorative", headers=headers
    )


@login_required
def giornate_export_pdf(request):
    """
    Esporta giornate lavorative in PDF.
    """
    from core.pdf_generator import generate_pdf_response

    # Ottieni giornate (con eventuali filtri)
    giornate = request.user.giornate.all().order_by("-data")

    # Filtro mese se presente
    mese = request.GET.get("mese")
    if mese:
        try:
            anno, mese_num = mese.split("-")
            giornate = giornate.filter(data__year=anno, data__month=mese_num)
        except ValueError:
            pass

    # Prepara dati
    data = []
    for g in giornate:
        data.append(
            {
                "Data": g.data,
                "Mattina": f"{float(g.ore_mattina)}h",
                "Pomeriggio": f"{float(g.ore_pomeriggio)}h",
                "Notte": f"{float(g.ore_notte)}h",
                "Totale": f"{float(g.ore_totali)}h",
                "Straord.": f"{float(g.ore_straordinarie)}h",
            }
        )

    # Headers personalizzati
    headers = ["Data", "Mattina", "Pomeriggio", "Notte", "Totale", "Straord."]

    # Nome file e titolo
    filename = f"giornate_lavorative_{request.user.username}_{timezone.now().strftime('%Y%m%d')}"
    title = (
        f"Giornate Lavorative - {request.user.get_full_name() or request.user.username}"
    )

    return generate_pdf_response(data, filename, title=title, headers=headers)
