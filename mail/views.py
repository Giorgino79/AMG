"""
Views for Mail App - ModularBEF

Implementazione completa views per email, promemoria e chat.
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.urls import reverse
from django.db.models import Q, Count
from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()
from .models import (
    EmailConfiguration,
    EmailTemplate,
    EmailFolder,
    EmailLabel,
    EmailMessage,
    Promemoria,
    ChatConversation,
    ChatMessage,
)
from .forms import (
    EmailConfigurationForm,
    EmailTemplateForm,
    ComposeEmailForm,
    PromemoriaForm,
)
from .services.email_service import EmailService


# ============================================================================
# DASHBOARD & CONFIG
# ============================================================================

@login_required
def dashboard(request):
    """Dashboard email - solo gestione email"""
    # Get or create user email configuration
    email_config, created = EmailConfiguration.objects.get_or_create(
        user=request.user,
        defaults={
            'display_name': request.user.get_full_name() or request.user.username,
            'email_address': request.user.email,
        }
    )

    # Count email statistics
    total_messages = EmailMessage.objects.filter(
        sender_config__user=request.user
    ).count()

    total_templates = EmailTemplate.objects.filter(
        is_active=True
    ).count()

    # Recent activity
    recent_messages = EmailMessage.objects.filter(
        sender_config__user=request.user
    ).order_by('-created_at')[:5]

    context = {
        'title': 'Dashboard Email',
        'email_config': email_config,
        'total_messages': total_messages,
        'total_templates': total_templates,
        'recent_messages': recent_messages,
    }

    return render(request, 'mail/dashboard.html', context)


@login_required
def email_config(request):
    """Configurazione email utente (SMTP/IMAP)"""
    # Get or create configuration
    config, created = EmailConfiguration.objects.get_or_create(
        user=request.user,
        defaults={
            'display_name': request.user.get_full_name() or request.user.username,
            'email_address': request.user.email,
        }
    )

    if request.method == 'POST':
        form = EmailConfigurationForm(request.POST, instance=config)
        if form.is_valid():
            form.save()
            messages.success(request, 'Configurazione email salvata con successo')
            return redirect('mail:config')
        else:
            # Show form errors if validation fails
            messages.error(request, 'Errore nel salvataggio. Controlla i campi del form.')
    else:
        form = EmailConfigurationForm(instance=config)

    breadcrumb = [
        {'label': 'Home', 'url': reverse('home')},
        {'label': 'Mail', 'url': reverse('mail:dashboard')},
        {'label': 'Configurazione', 'url': None},
    ]

    context = {
        'title': 'Configurazione Email',
        'breadcrumb': breadcrumb,
        'form': form,
        'config': config,
    }

    return render(request, 'mail/config.html', context)


@login_required
def test_config(request):
    """Test configurazione email SMTP"""
    try:
        config = EmailConfiguration.objects.get(user=request.user)
        service = EmailService(user=request.user, config=config)

        if service.test_configuration():
            messages.success(request, 'Test configurazione riuscito! SMTP funzionante.')
        else:
            messages.error(request, f'Test fallito: {config.last_smtp_error}')
    except EmailConfiguration.DoesNotExist:
        messages.warning(request, 'Nessuna configurazione trovata. Configurala prima.')

    return redirect('mail:config')


# ============================================================================
# TEMPLATES
# ============================================================================

@login_required
def template_list(request):
    """Lista template email con ricerca"""
    search = request.GET.get('search', '')
    categoria = request.GET.get('categoria', '')

    templates = EmailTemplate.objects.filter(is_active=True)

    if search:
        templates = templates.filter(
            Q(nome__icontains=search) |
            Q(descrizione__icontains=search) |
            Q(subject__icontains=search)
        )

    if categoria:
        templates = templates.filter(categoria=categoria)

    templates = templates.order_by('-created_at')

    breadcrumb = [
        {'label': 'Home', 'url': reverse('home')},
        {'label': 'Mail', 'url': reverse('mail:dashboard')},
        {'label': 'Template', 'url': None},
    ]

    context = {
        'title': 'Template Email',
        'breadcrumb': breadcrumb,
        'templates': templates,
        'search': search,
        'categoria': categoria,
        'categorias': EmailTemplate.CATEGORY_CHOICES,
    }

    return render(request, 'mail/template_list.html', context)


@login_required
def template_create(request):
    """Crea nuovo template email"""
    if request.method == 'POST':
        form = EmailTemplateForm(request.POST)
        if form.is_valid():
            template = form.save(commit=False)
            template.created_by = request.user
            template.save()
            messages.success(request, f'Template "{template.nome}" creato con successo')
            return redirect('mail:template_list')
    else:
        form = EmailTemplateForm()

    breadcrumb = [
        {'label': 'Home', 'url': reverse('home')},
        {'label': 'Mail', 'url': reverse('mail:dashboard')},
        {'label': 'Template', 'url': reverse('mail:template_list')},
        {'label': 'Nuovo', 'url': None},
    ]

    context = {
        'title': 'Nuovo Template',
        'breadcrumb': breadcrumb,
        'form': form,
    }

    return render(request, 'mail/template_form.html', context)


@login_required
def template_edit(request, pk):
    """Modifica template email"""
    template = get_object_or_404(EmailTemplate, id=pk, is_active=True)

    # Non permettere modifica template di sistema
    if template.is_system:
        messages.warning(request, 'I template di sistema non possono essere modificati')
        return redirect('mail:template_list')

    if request.method == 'POST':
        form = EmailTemplateForm(request.POST, instance=template)
        if form.is_valid():
            form.save()
            messages.success(request, f'Template "{template.nome}" aggiornato con successo')
            return redirect('mail:template_list')
    else:
        form = EmailTemplateForm(instance=template)

    breadcrumb = [
        {'label': 'Home', 'url': reverse('home')},
        {'label': 'Mail', 'url': reverse('mail:dashboard')},
        {'label': 'Template', 'url': reverse('mail:template_list')},
        {'label': template.nome, 'url': None},
    ]

    context = {
        'title': f'Modifica Template: {template.nome}',
        'breadcrumb': breadcrumb,
        'form': form,
        'template': template,
    }

    return render(request, 'mail/template_form.html', context)


@login_required
def template_delete(request, pk):
    """Elimina template email (soft delete)"""
    template = get_object_or_404(EmailTemplate, id=pk, is_active=True)

    if template.is_system:
        messages.error(request, 'I template di sistema non possono essere eliminati')
        return redirect('mail:template_list')

    template.is_active = False
    template.deleted_at = timezone.now()
    template.save()

    messages.success(request, f'Template "{template.nome}" eliminato')
    return redirect('mail:template_list')


# ============================================================================
# MESSAGES
# ============================================================================

@login_required
def message_list(request):
    """Lista messaggi email con filtri per cartella e label"""
    # PULISCI TUTTI I MESSAGGI DJANGO PER EVITARE ALERT INDESIDERATI
    from django.contrib.messages import get_messages
    storage = get_messages(request)
    storage.used = True  # Marca tutti i messaggi come usati per non mostrarli

    folder_name = request.GET.get('folder', 'inbox')
    label_id = request.GET.get('label')
    search = request.GET.get('search', '')

    # Get user email config
    try:
        config = EmailConfiguration.objects.get(user=request.user)
    except EmailConfiguration.DoesNotExist:
        messages.warning(request, 'Configura prima il tuo account email')
        return redirect('mail:config')

    # Base queryset
    messages_qs = EmailMessage.objects.filter(
        sender_config=config,
        is_active=True
    ).select_related('sender_config').prefetch_related('labels')

    # Filter by folder type
    if folder_name.startswith('custom_'):
        # Custom folder
        folder_id = folder_name.replace('custom_', '')
        try:
            folder_obj = EmailFolder.objects.get(id=folder_id, config=config)
            messages_qs = messages_qs.filter(folder=folder_obj)
        except EmailFolder.DoesNotExist:
            pass
    elif folder_name == 'inbox':
        # Inbox: incoming messages not in trash/spam
        messages_qs = messages_qs.filter(
            direction='incoming',
            is_spam=False
        ).exclude(status='draft')
    elif folder_name == 'sent':
        # Sent: outgoing messages that are sent
        messages_qs = messages_qs.filter(
            direction='outgoing',
            status__in=['sent', 'delivered']
        )
    elif folder_name == 'drafts':
        # Drafts
        messages_qs = messages_qs.filter(status='draft')
    elif folder_name == 'trash':
        # Trash: messages marked for deletion (soft delete)
        messages_qs = messages_qs.filter(is_active=False)
    elif folder_name == 'spam':
        # Spam
        messages_qs = messages_qs.filter(is_spam=True)
    elif folder_name == 'archive':
        # Archive: messages not in other folders
        messages_qs = messages_qs.filter(
            folder__folder_type='archive'
        )

    # Filter by label
    if label_id:
        messages_qs = messages_qs.filter(labels__id=label_id)

    # Search
    if search:
        messages_qs = messages_qs.filter(
            Q(subject__icontains=search) |
            Q(content_text__icontains=search) |
            Q(to_addresses__icontains=search) |
            Q(from_address__icontains=search) |
            Q(from_name__icontains=search)
        )

    messages_qs = messages_qs.order_by('-created_at')

    # Get all folders and labels for sidebar
    folders = EmailFolder.objects.filter(config=config)
    labels = EmailLabel.objects.filter(configuration=config, is_active=True)

    # Calculate folder statistics
    all_messages = EmailMessage.objects.filter(sender_config=config, is_active=True)
    folders_stats = {
        'inbox': all_messages.filter(direction='incoming', is_spam=False).exclude(status='draft').count(),
        'sent': all_messages.filter(direction='outgoing', status__in=['sent', 'delivered']).count(),
        'drafts': all_messages.filter(status='draft').count(),
        'trash': EmailMessage.objects.filter(sender_config=config, is_active=False).count(),
        'spam': all_messages.filter(is_spam=True).count(),
        'archive': all_messages.filter(folder__folder_type='archive').count(),
    }

    breadcrumb = [
        {'label': 'Home', 'url': reverse('home')},
        {'label': 'Mail', 'url': reverse('mail:dashboard')},
        {'label': 'Messaggi', 'url': None},
    ]

    context = {
        'title': 'Messaggi Email',
        'breadcrumb': breadcrumb,
        'messages': messages_qs,
        'folders': folders,
        'labels': labels,
        'current_folder': folder_name,
        'search': search,
        'folders_stats': folders_stats,
    }

    return render(request, 'mail/message_list.html', context)


@login_required
def message_detail(request, pk):
    """Dettaglio messaggio email"""
    message = get_object_or_404(
        EmailMessage,
        id=pk,
        sender_config__user=request.user,
        is_active=True
    )

    # Mark as read
    if not message.is_read:
        message.is_read = True
        message.read_at = timezone.now()
        message.save()

    breadcrumb = [
        {'label': 'Home', 'url': reverse('home')},
        {'label': 'Mail', 'url': reverse('mail:dashboard')},
        {'label': 'Messaggi', 'url': reverse('mail:message_list')},
        {'label': message.subject[:50], 'url': None},
    ]

    context = {
        'title': f'Messaggio: {message.subject}',
        'breadcrumb': breadcrumb,
        'message': message,
    }

    return render(request, 'mail/message_detail.html', context)


@login_required
def compose_email(request):
    """Componi e invia nuova email"""
    try:
        config = EmailConfiguration.objects.get(user=request.user)
    except EmailConfiguration.DoesNotExist:
        messages.warning(request, 'Configura prima il tuo account email')
        return redirect('mail:config')

    if request.method == 'POST':
        form = ComposeEmailForm(request.POST, request.FILES)
        if form.is_valid():
            # Send or save as draft
            action = request.POST.get('action', 'save')

            if action == 'send':
                # Send email using service (creates message automatically)
                service = EmailService(user=request.user, config=config)
                try:
                    service.send_email(
                        to_addresses=form.cleaned_data['to_addresses'],
                        subject=form.cleaned_data['subject'],
                        content_html='',
                        content_text=form.cleaned_data['content_text'],
                        cc_addresses=form.cleaned_data['cc_addresses'],
                        bcc_addresses=form.cleaned_data['bcc_addresses'],
                    )
                    messages.success(request, 'Email inviata con successo')
                    return redirect('mail:message_list')
                except Exception as e:
                    messages.error(request, f'Errore invio: {str(e)}')
            else:
                # Save as draft
                email_message = form.save(commit=False)
                email_message.sender_config = config
                email_message.direction = 'outgoing'
                email_message.status = 'draft'
                email_message.created_by = request.user
                email_message.from_address = config.email_address
                email_message.from_name = config.display_name
                email_message.content_html = ''
                email_message.save()

                messages.success(request, 'Bozza salvata')
                return redirect('mail:message_list')
        else:
            # Show form errors if validation fails
            messages.error(request, 'Errore nel form. Controlla i campi inseriti.')
    else:
        form = ComposeEmailForm()

    breadcrumb = [
        {'label': 'Home', 'url': reverse('home')},
        {'label': 'Mail', 'url': reverse('mail:dashboard')},
        {'label': 'Nuova Email', 'url': None},
    ]

    context = {
        'title': 'Nuova Email',
        'breadcrumb': breadcrumb,
        'form': form,
    }

    return render(request, 'mail/compose.html', context)


@login_required
def message_toggle_flag(request, pk):
    """Toggle flag importante su messaggio"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)

    try:
        message = get_object_or_404(
            EmailMessage,
            id=pk,
            sender_config__user=request.user
        )
        message.toggle_flag()
        return JsonResponse({
            'success': True,
            'is_flagged': message.is_flagged
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


# ============================================================================
# PROMEMORIA
# ============================================================================

@login_required
def promemoria_list(request):
    """Lista promemoria con filtri"""
    stato = request.GET.get('stato', '')
    priorita = request.GET.get('priorita', '')
    search = request.GET.get('search', '')
    filtro_tipo = request.GET.get('tipo', 'assegnati')  # 'assegnati', 'creati', 'tutti'

    # Mostra promemoria creati dall'utente O assegnati all'utente
    if filtro_tipo == 'creati':
        promemoria = Promemoria.objects.filter(
            created_by=request.user,
            is_active=True
        )
    elif filtro_tipo == 'assegnati':
        promemoria = Promemoria.objects.filter(
            assegnato_a=request.user,
            is_active=True
        )
    else:  # tutti
        promemoria = Promemoria.objects.filter(
            Q(created_by=request.user) | Q(assegnato_a=request.user),
            is_active=True
        ).distinct()

    if stato:
        promemoria = promemoria.filter(stato=stato)

    if priorita:
        promemoria = promemoria.filter(priorita=priorita)

    if search:
        promemoria = promemoria.filter(
            Q(titolo__icontains=search) |
            Q(descrizione__icontains=search)
        )

    promemoria = promemoria.order_by('-priorita', 'data_scadenza')

    breadcrumb = [
        {'label': 'Home', 'url': reverse('home')},
        {'label': 'Mail', 'url': reverse('mail:dashboard')},
        {'label': 'Promemoria', 'url': None},
    ]

    context = {
        'title': 'Promemoria',
        'breadcrumb': breadcrumb,
        'promemoria': promemoria,
        'stato': stato,
        'priorita': priorita,
        'search': search,
        'filtro_tipo': filtro_tipo,
        'stati': Promemoria.STATUS_CHOICES,
        'prioritas': Promemoria.PRIORITY_CHOICES,
    }

    return render(request, 'mail/promemoria_list.html', context)


@login_required
def promemoria_create(request):
    """Crea nuovo promemoria"""
    if request.method == 'POST':
        form = PromemoriaForm(request.POST)
        if form.is_valid():
            promemoria = form.save(commit=False)
            promemoria.user = request.user
            promemoria.created_by = request.user
            # Se non è stato specificato assegnato_a, assegna al creatore
            if not promemoria.assegnato_a:
                promemoria.assegnato_a = request.user
            promemoria.save()
            messages.success(request, f'Promemoria "{promemoria.titolo}" creato')
            return redirect('mail:promemoria_list')
    else:
        # Pre-seleziona l'utente corrente come assegnatario
        form = PromemoriaForm(initial={'assegnato_a': request.user})

    breadcrumb = [
        {'label': 'Home', 'url': reverse('home')},
        {'label': 'Mail', 'url': reverse('mail:dashboard')},
        {'label': 'Promemoria', 'url': reverse('mail:promemoria_list')},
        {'label': 'Nuovo', 'url': None},
    ]

    context = {
        'title': 'Nuovo Promemoria',
        'breadcrumb': breadcrumb,
        'form': form,
    }

    return render(request, 'mail/promemoria_form.html', context)


@login_required
def promemoria_detail(request, pk):
    """Dettaglio promemoria"""
    from django.contrib.contenttypes.models import ContentType

    # Permette di vedere promemoria creati dall'utente O assegnati all'utente
    promemoria = get_object_or_404(
        Promemoria.objects.filter(
            Q(created_by=request.user) | Q(assegnato_a=request.user)
        ),
        id=pk,
        is_active=True
    )

    # Verifica se l'utente può modificare (solo il creatore)
    can_edit = promemoria.created_by == request.user

    breadcrumb = [
        {'label': 'Home', 'url': reverse('home')},
        {'label': 'Mail', 'url': reverse('mail:dashboard')},
        {'label': 'Promemoria', 'url': reverse('mail:promemoria_list')},
        {'label': promemoria.titolo[:50], 'url': None},
    ]

    context = {
        'title': f'Promemoria: {promemoria.titolo}',
        'breadcrumb': breadcrumb,
        'promemoria': promemoria,
        'object': promemoria,  # Per base_detail.html e sidebar
        'content_type_id': ContentType.objects.get_for_model(Promemoria).pk,
        'can_edit': can_edit,
        'edit_url': reverse('mail:promemoria_edit', args=[promemoria.pk]) if can_edit else None,
        'delete_url': reverse('mail:promemoria_delete', args=[promemoria.pk]) if can_edit else None,
        'back_url': reverse('mail:promemoria_list'),
    }

    return render(request, 'mail/promemoria_detail.html', context)


@login_required
def promemoria_edit(request, pk):
    """Modifica promemoria"""
    promemoria = get_object_or_404(
        Promemoria,
        id=pk,
        created_by=request.user,
        is_active=True
    )

    if request.method == 'POST':
        form = PromemoriaForm(request.POST, instance=promemoria)
        if form.is_valid():
            form.save()
            messages.success(request, f'Promemoria "{promemoria.titolo}" aggiornato')
            return redirect('mail:promemoria_detail', pk=promemoria.id)
    else:
        form = PromemoriaForm(instance=promemoria)

    breadcrumb = [
        {'label': 'Home', 'url': reverse('home')},
        {'label': 'Mail', 'url': reverse('mail:dashboard')},
        {'label': 'Promemoria', 'url': reverse('mail:promemoria_list')},
        {'label': promemoria.titolo[:50], 'url': reverse('mail:promemoria_detail', args=[pk])},
        {'label': 'Modifica', 'url': None},
    ]

    context = {
        'title': f'Modifica: {promemoria.titolo}',
        'breadcrumb': breadcrumb,
        'form': form,
        'promemoria': promemoria,
    }

    return render(request, 'mail/promemoria_form.html', context)


@login_required
def promemoria_complete(request, pk):
    """Segna promemoria come completato"""
    promemoria = get_object_or_404(
        Promemoria,
        id=pk,
        created_by=request.user,
        is_active=True
    )

    promemoria.stato = 'completed'
    promemoria.data_completamento = timezone.now()
    promemoria.save()

    messages.success(request, f'Promemoria "{promemoria.titolo}" completato')
    return redirect('mail:promemoria_list')


@login_required
def promemoria_delete(request, pk):
    """Elimina promemoria"""
    promemoria = get_object_or_404(
        Promemoria,
        id=pk,
        user=request.user,
        is_active=True
    )

    if request.method == 'POST':
        titolo = promemoria.titolo
        promemoria.is_active = False
        promemoria.deleted_at = timezone.now()
        promemoria.save()
        messages.success(request, f'Promemoria "{titolo}" eliminato')
        return redirect('mail:promemoria_list')

    return redirect('mail:promemoria_detail', pk=pk)


# ============================================================================
# CHAT - Pagina Unificata
# ============================================================================

@login_required
def chat(request):
    """
    Chat unificata: lista utenti e conversazioni di gruppo a sinistra, conversazione a destra.

    Gestisce sia la visualizzazione che l'invio messaggi in un'unica pagina.
    Crea automaticamente conversazioni dirette quando necessario.
    """
    # Lista tutti gli utenti attivi escluso l'utente corrente
    utenti = User.objects.filter(
        is_active=True
    ).exclude(
        id=request.user.id
    ).order_by('first_name', 'last_name', 'username')

    # Lista conversazioni di gruppo dell'utente
    conversazioni_gruppo = ChatConversation.objects.filter(
        tipo='group',
        partecipanti=request.user,
        is_active=True
    ).order_by('-last_message_at', '-created_at')

    # Contatto selezionato (via query param) oppure conversazione
    contatto_id = request.GET.get('contatto')
    conversazione_id = request.GET.get('conversazione')
    contatto = None
    conversazione = None
    messaggi = []

    # Se è selezionata una conversazione di gruppo specifica
    if conversazione_id:
        try:
            conversazione = ChatConversation.objects.get(
                pk=conversazione_id,
                partecipanti=request.user,
                is_active=True
            )

            # Gestione invio messaggio
            if request.method == 'POST':
                testo = request.POST.get('testo', '').strip()
                allegato = request.FILES.get('allegato')

                if testo or allegato:
                    nuovo_messaggio = ChatMessage.objects.create(
                        conversation=conversazione,
                        sender=request.user,
                        contenuto=testo,
                        created_by=request.user
                    )

                    # Gestione allegato tramite AllegatiMixin se presente
                    if allegato:
                        from core.models_legacy import Allegato
                        from django.contrib.contenttypes.models import ContentType
                        content_type = ContentType.objects.get_for_model(ChatMessage)
                        Allegato.objects.create(
                            content_type=content_type,
                            object_id=str(nuovo_messaggio.id),
                            file=allegato,
                            nome_originale=allegato.name,
                            uploaded_by=request.user
                        )

                    # Aggiorna timestamp conversazione
                    conversazione.last_message_at = timezone.now()
                    conversazione.messages_count = conversazione.messages.count()
                    conversazione.save()

                    return redirect(f"{reverse('mail:chat')}?conversazione={conversazione.id}")

            # Carica messaggi della conversazione
            messaggi = conversazione.messages.filter(
                is_active=True
            ).select_related('sender').order_by('created_at')

            # Segna messaggi come letti
            messaggi_non_letti = messaggi.exclude(
                sender=request.user
            ).exclude(
                read_by=request.user
            )
            for msg in messaggi_non_letti:
                msg.read_by.add(request.user)

        except ChatConversation.DoesNotExist:
            conversazione_id = None

    elif contatto_id:
        try:
            contatto = User.objects.get(id=contatto_id, is_active=True)

            # Cerca o crea conversazione diretta tra i due utenti
            conversazione = ChatConversation.objects.filter(
                tipo='direct',
                is_active=True,
                partecipanti=request.user
            ).filter(
                partecipanti=contatto
            ).first()

            if not conversazione:
                # Crea nuova conversazione diretta
                conversazione = ChatConversation.objects.create(
                    tipo='direct',
                    created_by=request.user
                )
                conversazione.partecipanti.add(request.user, contatto)

            # Gestione invio messaggio
            if request.method == 'POST':
                testo = request.POST.get('testo', '').strip()
                allegato = request.FILES.get('allegato')

                if testo or allegato:
                    nuovo_messaggio = ChatMessage.objects.create(
                        conversation=conversazione,
                        sender=request.user,
                        contenuto=testo,
                        created_by=request.user
                    )

                    # Gestione allegato tramite AllegatiMixin se presente
                    if allegato:
                        from core.models_legacy import Allegato
                        from django.contrib.contenttypes.models import ContentType
                        content_type = ContentType.objects.get_for_model(ChatMessage)
                        Allegato.objects.create(
                            content_type=content_type,
                            object_id=str(nuovo_messaggio.id),
                            file=allegato,
                            nome_originale=allegato.name,
                            uploaded_by=request.user
                        )

                    # Aggiorna timestamp conversazione
                    conversazione.last_message_at = timezone.now()
                    conversazione.messages_count = conversazione.messages.count()
                    conversazione.save()

                    return redirect(f"{reverse('mail:chat')}?contatto={contatto.id}")

            # Carica messaggi della conversazione
            messaggi = conversazione.messages.filter(
                is_active=True
            ).select_related('sender').order_by('created_at')

            # Segna messaggi come letti
            messaggi_non_letti = messaggi.exclude(
                sender=request.user
            ).exclude(
                read_by=request.user
            )
            for msg in messaggi_non_letti:
                msg.read_by.add(request.user)

        except User.DoesNotExist:
            contatto = None

    context = {
        'title': 'Chat e Messaggi',
        'utenti': utenti,
        'conversazioni_gruppo': conversazioni_gruppo,
        'contatto': contatto,
        'messaggi': messaggi,
        'conversazione': conversazione,
    }

    return render(request, 'mail/chat.html', context)


@login_required
def chat_conversation_detail(request, pk):
    """
    Vista dettaglio conversazione chat (sia diretta che di gruppo).

    Permette di visualizzare e inviare messaggi in una conversazione specifica.
    Usato principalmente per chat di gruppo associate a progetti.
    """
    conversazione = get_object_or_404(
        ChatConversation,
        pk=pk,
        is_active=True,
        partecipanti=request.user  # L'utente deve essere partecipante
    )

    # Gestione invio messaggio
    if request.method == 'POST':
        testo = request.POST.get('testo', '').strip()
        allegato = request.FILES.get('allegato')

        if testo or allegato:
            nuovo_messaggio = ChatMessage.objects.create(
                conversation=conversazione,
                sender=request.user,
                contenuto=testo,
                created_by=request.user
            )

            # Gestione allegato tramite AllegatiMixin se presente
            if allegato:
                from core.models_legacy import Allegato
                from django.contrib.contenttypes.models import ContentType
                content_type = ContentType.objects.get_for_model(ChatMessage)
                Allegato.objects.create(
                    content_type=content_type,
                    object_id=str(nuovo_messaggio.id),
                    file=allegato,
                    nome_originale=allegato.name,
                    uploaded_by=request.user
                )

            # Aggiorna timestamp conversazione
            conversazione.last_message_at = timezone.now()
            conversazione.messages_count = conversazione.messages.count()
            conversazione.save()

            return redirect('mail:chat_detail', pk=pk)

    # Carica messaggi della conversazione
    messaggi = conversazione.messages.filter(
        is_active=True
    ).select_related('sender').order_by('created_at')

    # Segna messaggi come letti
    messaggi_non_letti = messaggi.exclude(
        sender=request.user
    ).exclude(
        read_by=request.user
    )
    for msg in messaggi_non_letti:
        msg.read_by.add(request.user)

    # Lista utenti attivi per eventuali nuove chat (sidebar)
    utenti = User.objects.filter(
        is_active=True
    ).exclude(
        id=request.user.id
    ).order_by('first_name', 'last_name', 'username')

    context = {
        'title': conversazione.titolo or f'Chat #{conversazione.pk}',
        'conversazione': conversazione,
        'messaggi': messaggi,
        'utenti': utenti,
        'is_group_chat': conversazione.tipo == 'group',
    }

    return render(request, 'mail/chat.html', context)


# ============================================================================
# EMAIL SYNC VIEWS
# ============================================================================

@login_required
def sync_emails_manual(request):
    """Sincronizza email manualmente tramite AJAX"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)

    try:
        # Ottieni configurazione utente
        config = EmailConfiguration.objects.get(user=request.user)

        if not config.imap_enabled:
            return JsonResponse({
                'success': False,
                'error': 'IMAP non abilitato. Configura IMAP nelle impostazioni.'
            })

        # Sincronizzazione diretta senza Celery
        from .management.commands.sync_emails import Command
        command = Command()

        try:
            # Sincronizza INBOX
            synced = command.sync_config(config, limit=100, imap_folder='INBOX')

            return JsonResponse({
                'success': True,
                'message': f'Sincronizzazione completata: {synced} email scaricate',
                'synced': synced
            })
        except Exception as sync_error:
            # Salva errore nella configurazione
            config.last_imap_error = str(sync_error)
            config.save(update_fields=['last_imap_error'])

            return JsonResponse({
                'success': False,
                'error': f'Errore durante la sincronizzazione: {str(sync_error)}'
            })

    except EmailConfiguration.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Configura prima il tuo account email'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })
