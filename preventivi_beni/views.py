"""
Views for Preventivi Beni/Servizi app
=====================================

Views complete con workflow 3 step identico a trasporti.
"""

import logging
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.utils import timezone
from django.db import transaction
from django.db.models import Q

logger = logging.getLogger(__name__)

from .models import (
    RichiestaPreventivo, VocePreventivo, Offerta,
    FornitorePreventivo, ParametroValutazione
)
from .forms import (
    RichiestaForm, VoceFormSet,
    SceltaFornitoriForm, OffertaForm, SceltaOffertaForm
)


# ============================================
# DASHBOARD E LISTE
# ============================================

@login_required
def dashboard(request):
    """Dashboard preventivi beni/servizi"""

    # Statistiche rapide
    richieste_attive = RichiestaPreventivo.objects.exclude(
        stato__in=['ORDINATO', 'ANNULLATA']
    ).count()

    richieste_in_attesa = RichiestaPreventivo.objects.filter(
        stato__in=['RICHIESTA_INVIATA', 'OFFERTE_RICEVUTE']
    ).count()

    richieste_bozza = RichiestaPreventivo.objects.filter(
        stato='BOZZA',
        richiedente=request.user
    ).count()

    # Richieste recenti
    richieste_recenti = RichiestaPreventivo.objects.all().order_by('-data_creazione')[:5]

    context = {
        'richieste_attive': richieste_attive,
        'richieste_in_attesa': richieste_in_attesa,
        'richieste_bozza': richieste_bozza,
        'richieste_recenti': richieste_recenti,
    }
    return render(request, 'preventivi_beni/dashboard.html', context)


@login_required
def richieste_list(request):
    """Lista richieste preventivo con filtri"""

    richieste = RichiestaPreventivo.objects.all()

    # Filtri
    stato = request.GET.get('stato')
    tipo = request.GET.get('tipo')
    categoria = request.GET.get('categoria')
    search = request.GET.get('search')

    if stato:
        richieste = richieste.filter(stato=stato)
    if tipo:
        richieste = richieste.filter(tipo_richiesta=tipo)
    if categoria:
        richieste = richieste.filter(categoria=categoria)
    if search:
        richieste = richieste.filter(
            Q(numero__icontains=search) |
            Q(titolo__icontains=search) |
            Q(descrizione__icontains=search)
        )

    richieste = richieste.order_by('-data_creazione')

    # Paginazione
    paginator = Paginator(richieste, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'stato_filter': stato,
        'tipo_filter': tipo,
        'categoria_filter': categoria,
        'search': search,
    }
    return render(request, 'preventivi_beni/richieste_list.html', context)


@login_required
def richiesta_detail(request, pk):
    """Dettaglio richiesta"""
    richiesta = get_object_or_404(RichiestaPreventivo, pk=pk)

    # Content type per allegati e QR code
    from django.contrib.contenttypes.models import ContentType
    content_type = ContentType.objects.get_for_model(richiesta)

    context = {
        'richiesta': richiesta,
        'object': richiesta,  # Per template comune
        'content_type_id': content_type.id,
        'back_url': '/preventivi_beni/richieste/',
    }
    return render(request, 'preventivi_beni/richiesta_detail.html', context)


# ============================================
# CREAZIONE RICHIESTA
# ============================================

@login_required
@transaction.atomic
def richiesta_create(request):
    """Crea nuova richiesta preventivo con voci"""

    if request.method == 'POST':
        form = RichiestaForm(request.POST, user=request.user)
        formset = VoceFormSet(request.POST)

        if form.is_valid() and formset.is_valid():
            richiesta = form.save(commit=False)
            richiesta.richiedente = request.user
            richiesta.save()

            # Salva voci
            formset.instance = richiesta
            formset.save()

            messages.success(request, f'Richiesta preventivo {richiesta.numero} creata con successo!')
            return redirect('preventivi_beni:richiesta_detail', pk=richiesta.pk)
    else:
        form = RichiestaForm(user=request.user)
        formset = VoceFormSet()

    context = {
        'form': form,
        'formset': formset,
    }
    return render(request, 'preventivi_beni/richiesta_create.html', context)


# ============================================
# SELEZIONE FORNITORI
# ============================================

@login_required
@transaction.atomic
def richiesta_select_fornitori(request, pk):
    """Seleziona fornitori per richiesta (esistenti + nuovi)"""

    richiesta = get_object_or_404(RichiestaPreventivo, pk=pk)

    if richiesta.stato != 'BOZZA':
        messages.warning(request, 'Puoi selezionare i fornitori solo in stato BOZZA')
        return redirect('preventivi_beni:richiesta_detail', pk=pk)

    if request.method == 'POST':
        form = SceltaFornitoriForm(request.POST)
        if form.is_valid():
            fornitori_esistenti = form.cleaned_data.get('fornitori_esistenti', [])
            nuovi_fornitori = form.cleaned_data.get('nuovi_fornitori', [])

            count_esistenti = 0
            count_nuovi = 0

            # Crea record FornitorePreventivo per fornitori esistenti
            for fornitore in fornitori_esistenti:
                FornitorePreventivo.objects.get_or_create(
                    richiesta=richiesta,
                    fornitore=fornitore
                )
                count_esistenti += 1

            # Gestisci nuovi fornitori
            from anagrafica.models import Fornitore
            for nuovo in nuovi_fornitori:
                # Crea un nuovo fornitore temporaneo (non ancora accreditato)
                fornitore, created = Fornitore.objects.get_or_create(
                    email=nuovo['email'],
                    defaults={
                        'ragione_sociale': nuovo['ragione_sociale'],
                        'attivo': False,  # Non attivo fino ad accreditamento
                    }
                )

                # Crea relazione con note
                fornitore_preventivo, _ = FornitorePreventivo.objects.get_or_create(
                    richiesta=richiesta,
                    fornitore=fornitore
                )

                if created:
                    fornitore_preventivo.note_fornitore = f"Fornitore non accreditato. Email: {nuovo['email']}"
                    fornitore_preventivo.save()
                    count_nuovi += 1

            # Messaggio di successo
            msg_parts = []
            if count_esistenti:
                msg_parts.append(f'{count_esistenti} fornitore/i esistente/i')
            if count_nuovi:
                msg_parts.append(f'{count_nuovi} nuovo/i fornitore/i')

            messages.success(request, f'Selezionati: {", ".join(msg_parts)}')
            return redirect('preventivi_beni:step1_invia', pk=pk)
    else:
        form = SceltaFornitoriForm()

    context = {
        'richiesta': richiesta,
        'form': form,
        'fornitori_selezionati': richiesta.fornitori.all(),
    }
    return render(request, 'preventivi_beni/richiesta_select_fornitori.html', context)


# ============================================
# WORKFLOW 3 STEP
# ============================================

@login_required
def step1_invia_fornitori(request, pk):
    """Step 1: Invio richieste ai fornitori con email integrate"""

    richiesta = get_object_or_404(RichiestaPreventivo, pk=pk)

    if richiesta.stato not in ['BOZZA', 'RICHIESTA_INVIATA']:
        messages.warning(request, 'Richiesta già inviata')
        return redirect('preventivi_beni:richiesta_detail', pk=pk)

    fornitori_preventivi = FornitorePreventivo.objects.filter(richiesta=richiesta)

    if not fornitori_preventivi.exists():
        messages.error(request, 'Seleziona almeno un fornitore prima di inviare')
        return redirect('preventivi_beni:richiesta_select_fornitori', pk=pk)

    if request.method == 'POST':
        # Invia email con servizio integrato
        from mail.services import ManagementEmailService
        email_service = ManagementEmailService(user=request.user)

        count_success = 0
        count_failed = 0
        errors = []

        for fornitore_preventivo in fornitori_preventivi:
            if fornitore_preventivo.email_inviata:
                continue  # Già inviata

            fornitore = fornitore_preventivo.fornitore

            # Verifica email
            email_dest = fornitore.email
            if not email_dest:
                errors.append(f'{fornitore.ragione_sociale}: email mancante')
                count_failed += 1
                continue

            try:
                # Prepara tabella voci
                voci_html = ""
                for voce in richiesta.voci.all().order_by('ordine'):
                    voci_html += f"""
                    <tr>
                        <td style="padding: 8px; border: 1px solid #dee2e6;">{voce.codice or '-'}</td>
                        <td style="padding: 8px; border: 1px solid #dee2e6;">{voce.descrizione}</td>
                        <td style="padding: 8px; border: 1px solid #dee2e6;">{voce.quantita} {voce.get_unita_misura_display()}</td>
                        <td style="padding: 8px; border: 1px solid #dee2e6;">
                            {voce.marca_richiesta or '-'}<br>
                            {voce.modello_richiesto or ''}
                        </td>
                        <td style="padding: 8px; border: 1px solid #dee2e6;">{voce.note or '-'}</td>
                    </tr>
                    """

                # Prepara sezione automezzo se presente
                automezzo_html = ""
                if richiesta.automezzo:
                    automezzo = richiesta.automezzo
                    automezzo_html = f"""
                            <div class="info-box" style="border-left-color: #17a2b8;">
                                <strong>Automezzo di Riferimento:</strong><br>
                                <strong>Targa:</strong> {automezzo.targa}<br>
                                <strong>Marca/Modello:</strong> {automezzo.marca} {automezzo.modello}<br>
                                <strong>Anno:</strong> {automezzo.anno_immatricolazione}<br>
                                {f'<em>In allegato: libretto di circolazione (fronte)</em>' if automezzo.libretto_fronte else ''}
                            </div>
                    """

                # Crea contenuto HTML
                html_content = f"""
                <html>
                <head>
                    <style>
                        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                        .container {{ max-width: 700px; margin: 0 auto; padding: 20px; }}
                        .header {{ background-color: #007bff; color: white; padding: 20px; text-align: center; }}
                        .content {{ background-color: #f8f9fa; padding: 20px; margin: 20px 0; }}
                        .info-box {{ background-color: white; padding: 15px; margin: 10px 0; border-left: 4px solid #007bff; }}
                        .button {{ display: inline-block; padding: 12px 24px; background-color: #28a745; color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                        .footer {{ text-align: center; color: #6c757d; font-size: 12px; margin-top: 30px; }}
                        table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
                        th {{ background-color: #f1f3f5; padding: 10px; border: 1px solid #dee2e6; text-align: left; }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="header">
                            <h1>Richiesta di Preventivo</h1>
                        </div>
                        <div class="content">
                            <h2>Gentile {fornitore.ragione_sociale},</h2>
                            <p>Vi sottoponiamo una richiesta di preventivo per i seguenti beni/servizi:</p>

                            <div class="info-box">
                                <strong>Richiesta N°:</strong> {richiesta.numero}<br>
                                <strong>Oggetto:</strong> {richiesta.titolo}<br>
                                <strong>Tipo:</strong> {richiesta.get_tipo_richiesta_display()}<br>
                                {f'<strong>Categoria:</strong> {richiesta.get_categoria_display()}<br>' if richiesta.categoria else ''}
                            </div>

                            {automezzo_html}

                            {f'<div class="info-box"><strong>Descrizione:</strong><br>{richiesta.descrizione}</div>' if richiesta.descrizione else ''}

                            <h3>Articoli/Servizi Richiesti</h3>
                            <table>
                                <thead>
                                    <tr>
                                        <th>Codice</th>
                                        <th>Descrizione</th>
                                        <th>Quantità</th>
                                        <th>Marca/Modello</th>
                                        <th>Note</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {voci_html}
                                </tbody>
                            </table>

                            <div class="info-box">
                                {f'<strong>Luogo Consegna:</strong> {richiesta.luogo_consegna}<br>' if richiesta.luogo_consegna else ''}
                                {f'<strong>Data Consegna Richiesta:</strong> {richiesta.data_consegna_richiesta.strftime("%d/%m/%Y")}<br>' if richiesta.data_consegna_richiesta else ''}
                                {f'<strong>Scadenza Offerte:</strong> {richiesta.data_scadenza_offerte.strftime("%d/%m/%Y")}<br>' if richiesta.data_scadenza_offerte else ''}
                                {f'<strong>Condizioni Pagamento:</strong> {richiesta.get_condizioni_pagamento_richieste_display()}<br>' if richiesta.condizioni_pagamento_richieste else ''}
                            </div>

                            {f'<div class="info-box"><strong>Note:</strong><br>{richiesta.note_per_fornitori}</div>' if richiesta.note_per_fornitori else ''}

                            <p style="text-align: center;">
                                <a href="{request.build_absolute_uri(f'/preventivi_beni/risposta/{fornitore_preventivo.token_accesso}/')}" class="button">INVIA LA TUA OFFERTA</a>
                            </p>

                            <p><small>Oppure rispondi direttamente a questa email con la tua offerta.</small></p>
                        </div>
                        <div class="footer">
                            <p>Questa è una richiesta automatica del sistema di gestione preventivi.<br>
                            Per informazioni contattare: {request.user.email}</p>
                        </div>
                    </div>
                </body>
                </html>
                """

                # Prepara allegati
                allegati = []

                # Allega libretto fronte se presente automezzo con libretto
                if richiesta.automezzo and richiesta.automezzo.libretto_fronte:
                    try:
                        libretto = richiesta.automezzo.libretto_fronte
                        # Determina il mimetype dal nome file
                        import os
                        filename = os.path.basename(libretto.name)
                        ext = os.path.splitext(filename)[1].lower()

                        mimetype_map = {
                            '.pdf': 'application/pdf',
                            '.jpg': 'image/jpeg',
                            '.jpeg': 'image/jpeg',
                            '.png': 'image/png',
                            '.gif': 'image/gif',
                        }
                        mimetype = mimetype_map.get(ext, 'application/octet-stream')

                        # Leggi il contenuto del file
                        libretto.open('rb')
                        file_content = libretto.read()
                        libretto.close()

                        allegato_nome = f"Libretto_{richiesta.automezzo.targa}{ext}"
                        allegati.append((allegato_nome, file_content, mimetype))

                    except Exception as e:
                        logger.warning(f'Impossibile allegare libretto: {str(e)}')

                # Invia email
                result = email_service.send_email(
                    to=email_dest,
                    subject=f'Richiesta Preventivo - {richiesta.numero} - {richiesta.titolo}',
                    html_content=html_content,
                    source_object=richiesta,
                    category='preventivi_beni',
                    attachments=allegati if allegati else None
                )

                if result.get('success'):
                    fornitore_preventivo.email_inviata = True
                    fornitore_preventivo.data_invio = timezone.now()
                    fornitore_preventivo.save()
                    count_success += 1
                else:
                    error_msg = result.get('error', 'Errore sconosciuto')
                    errors.append(f'{fornitore.ragione_sociale}: {error_msg}')
                    count_failed += 1

            except Exception as e:
                logger.error(f'Errore invio email a {fornitore.ragione_sociale}: {str(e)}')
                errors.append(f'{fornitore.ragione_sociale}: {str(e)}')
                count_failed += 1

        # Aggiorna stato richiesta se almeno una email inviata
        if count_success > 0:
            richiesta.stato = 'RICHIESTA_INVIATA'
            richiesta.data_invio_richiesta = timezone.now()
            richiesta.operatore = request.user
            richiesta.save()

        # Messaggi di feedback
        if count_success > 0:
            messages.success(request, f'Richiesta inviata con successo a {count_success} fornitori')

        if count_failed > 0:
            messages.warning(request, f'Invio fallito per {count_failed} fornitori')
            for error in errors[:5]:  # Mostra massimo 5 errori
                messages.error(request, error)

        return redirect('preventivi_beni:richiesta_detail', pk=pk)

    context = {
        'richiesta': richiesta,
        'fornitori_preventivi': fornitori_preventivi,
    }
    return render(request, 'preventivi_beni/step1_invia.html', context)


@login_required
def step2_raccolta_offerte(request, pk):
    """Step 2: Raccolta offerte dai fornitori"""

    richiesta = get_object_or_404(RichiestaPreventivo, pk=pk)

    if richiesta.stato not in ['RICHIESTA_INVIATA', 'OFFERTE_RICEVUTE']:
        messages.warning(request, 'La richiesta deve essere in stato RICHIESTA_INVIATA')
        return redirect('preventivi_beni:richiesta_detail', pk=pk)

    offerte = richiesta.offerte.all().order_by('importo_totale')
    fornitori_preventivi = FornitorePreventivo.objects.filter(richiesta=richiesta)

    # Statistiche
    totale_fornitori = fornitori_preventivi.count()
    fornitori_risposto = fornitori_preventivi.filter(ha_risposto=True).count()

    if request.method == 'POST':
        if offerte.count() >= 2:
            richiesta.stato = 'OFFERTE_RICEVUTE'
            richiesta.save()
            messages.success(request, 'Raccolta offerte completata')
            return redirect('preventivi_beni:step3_valutazione', pk=pk)
        else:
            messages.error(request, 'Servono almeno 2 offerte per procedere')

    context = {
        'richiesta': richiesta,
        'offerte': offerte,
        'totale_fornitori': totale_fornitori,
        'fornitori_risposto': fornitori_risposto,
    }
    return render(request, 'preventivi_beni/step2_raccolta.html', context)


@login_required
@transaction.atomic
def step3_valutazione(request, pk):
    """Step 3: Valutazione, approvazione offerta e creazione ODA"""

    richiesta = get_object_or_404(RichiestaPreventivo, pk=pk)

    if richiesta.stato not in ['OFFERTE_RICEVUTE', 'IN_VALUTAZIONE', 'APPROVATA']:
        messages.warning(request, 'Devi prima raccogliere le offerte')
        return redirect('preventivi_beni:richiesta_detail', pk=pk)

    offerte = richiesta.offerte.all().order_by('importo_totale')

    if request.method == 'POST':
        form = SceltaOffertaForm(request.POST, richiesta=richiesta)
        if form.is_valid():
            offerta_scelta = form.cleaned_data['offerta_scelta']
            note = form.cleaned_data.get('note_approvazione', '')

            fornitore = offerta_scelta.fornitore

            try:
                # 1. Crea Ordine di Acquisto (ODA)
                from acquisti.services import crea_ordine_da_preventivo, genera_pdf_ordine
                ordine_acquisto = crea_ordine_da_preventivo(richiesta, offerta_scelta, request.user)

                # 2. Genera PDF dell'ordine
                pdf_buffer = genera_pdf_ordine(ordine_acquisto)
                pdf_filename = f"ODA_{ordine_acquisto.numero_ordine.replace('-', '_')}.pdf"

                # 3. Approva offerta e aggiorna stati
                richiesta.offerta_approvata = offerta_scelta
                richiesta.stato = 'CONFERMATA'
                richiesta.data_approvazione = timezone.now()
                richiesta.data_valutazione = timezone.now()
                richiesta.data_conferma = timezone.now()
                if note:
                    richiesta.note_interne += f"\n\nNote approvazione: {note}"
                richiesta.save()

                # Aggiorna offerta come confermata
                offerta_scelta.confermata = True
                offerta_scelta.data_conferma = timezone.now()
                offerta_scelta.numero_ordine = ordine_acquisto.numero_ordine
                offerta_scelta.save()

                # 4. Prepara email con ODA allegato
                from mail.services import ManagementEmailService
                email_service = ManagementEmailService(user=request.user)

                # Prepara tabella voci
                voci_html = ""
                for voce in richiesta.voci.all().order_by('ordine'):
                    voci_html += f"""
                    <tr>
                        <td style="padding: 8px; border: 1px solid #dee2e6;">{voce.descrizione}</td>
                        <td style="padding: 8px; border: 1px solid #dee2e6;">{voce.quantita} {voce.get_unita_misura_display()}</td>
                    </tr>
                    """

                html_content = f"""
                <html>
                <head>
                    <style>
                        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                        .header {{ background-color: #28a745; color: white; padding: 20px; text-align: center; border-radius: 10px 10px 0 0; }}
                        .content {{ background-color: #f8f9fa; padding: 20px; border-radius: 0 0 10px 10px; }}
                        .info-box {{ background-color: white; padding: 15px; margin: 10px 0; border-left: 4px solid #28a745; border-radius: 5px; }}
                        .highlight {{ background-color: #d4edda; padding: 15px; border-radius: 5px; text-align: center; margin: 20px 0; }}
                        .footer {{ text-align: center; color: #6c757d; font-size: 12px; margin-top: 30px; }}
                        table {{ width: 100%; border-collapse: collapse; }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="header">
                            <h1>Conferma Ordine - {ordine_acquisto.numero_ordine}</h1>
                        </div>
                        <div class="content">
                            <h2>Gentile {fornitore.ragione_sociale},</h2>
                            <p>Siamo lieti di comunicarvi che la vostra offerta per la richiesta di preventivo
                            <strong>{richiesta.numero}</strong> è stata <strong>approvata</strong> e confermata.</p>

                            <div class="info-box">
                                <strong>Richiesta N°:</strong> {richiesta.numero}<br>
                                <strong>Ordine di Acquisto N°:</strong> {ordine_acquisto.numero_ordine}<br>
                                <strong>Oggetto:</strong> {richiesta.titolo}<br>
                                <strong>Tipo:</strong> {richiesta.get_tipo_richiesta_display()}
                            </div>

                            <div class="highlight">
                                <h3 style="color: #155724; margin: 0;">Importo Confermato</h3>
                                <p style="font-size: 24px; font-weight: bold; color: #28a745; margin: 10px 0;">
                                    € {offerta_scelta.importo_totale:,.2f}
                                </p>
                            </div>

                            <h3>Articoli/Servizi Ordinati</h3>
                            <table>
                                <thead>
                                    <tr style="background-color: #f1f3f5;">
                                        <th style="padding: 10px; border: 1px solid #dee2e6;">Descrizione</th>
                                        <th style="padding: 10px; border: 1px solid #dee2e6;">Quantità</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {voci_html}
                                </tbody>
                            </table>

                            <div class="info-box">
                                {f'<strong>Luogo Consegna:</strong> {richiesta.luogo_consegna}<br>' if richiesta.luogo_consegna else ''}
                                {f'<strong>Data Consegna:</strong> {offerta_scelta.data_consegna_proposta.strftime("%d/%m/%Y")}<br>' if offerta_scelta.data_consegna_proposta else ''}
                                {f'<strong>Termini Pagamento:</strong> {offerta_scelta.get_termini_pagamento_display()}<br>' if offerta_scelta.termini_pagamento else ''}
                            </div>

                            <div class="info-box" style="border-left-color: #17a2b8;">
                                <strong>In allegato:</strong> Ordine di Acquisto ufficiale (PDF)<br>
                                <em>Si prega di procedere con la fornitura secondo i termini indicati nell'ordine.</em>
                            </div>

                            <p>Per qualsiasi chiarimento, non esitate a contattarci.</p>

                            <p>Cordiali saluti</p>
                        </div>
                        <div class="footer">
                            <p>Questa è una notifica automatica del sistema di gestione preventivi.<br>
                            Per informazioni contattare: {request.user.email}</p>
                        </div>
                    </div>
                </body>
                </html>
                """

                # Prepara allegato PDF
                pdf_attachment = (pdf_filename, pdf_buffer.read(), 'application/pdf')

                result = email_service.send_email(
                    to=fornitore.email,
                    subject=f'Ordine di Acquisto {ordine_acquisto.numero_ordine} - {richiesta.numero} - {richiesta.titolo}',
                    html_content=html_content,
                    source_object=richiesta,
                    category='preventivi_beni',
                    attachments=[pdf_attachment]
                )

                if result.get('success'):
                    messages.success(
                        request,
                        f'Ordine {ordine_acquisto.numero_ordine} creato e inviato a {fornitore}!'
                    )
                else:
                    messages.warning(
                        request,
                        f'Ordine {ordine_acquisto.numero_ordine} creato, ma email non inviata: {result.get("error")}'
                    )

                # 5. Se categoria MANUTENZIONE e automezzo selezionato, crea Manutenzione
                if richiesta.categoria == 'MANUTENZIONE' and richiesta.automezzo:
                    try:
                        from automezzi.models import Manutenzione
                        from datetime import timedelta

                        # Componi descrizione dalle voci del preventivo
                        voci_desc = ", ".join(
                            v.descrizione for v in richiesta.voci.all().order_by('ordine')
                        )
                        descrizione = f"Manutenzione da preventivo {richiesta.numero}"
                        if voci_desc:
                            descrizione = f"{descrizione}: {voci_desc}"
                        # Tronca a 255 caratteri (limite del campo)
                        descrizione = descrizione[:255]

                        # Data prevista: dalla consegna dell'offerta o +7 giorni da oggi
                        data_prevista = (
                            offerta_scelta.data_consegna_proposta
                            if offerta_scelta.data_consegna_proposta
                            else (timezone.now() + timedelta(days=7)).date()
                        )

                        manutenzione = Manutenzione.objects.create(
                            automezzo=richiesta.automezzo,
                            descrizione=descrizione,
                            data_prevista=data_prevista,
                            stato='aperta',
                            fornitore=fornitore,
                            luogo=richiesta.luogo_consegna or '',
                            costo=offerta_scelta.importo_totale,
                            seguito_da=request.user,
                        )

                        messages.info(
                            request,
                            f'Manutenzione #{manutenzione.pk} creata automaticamente '
                            f'per automezzo {richiesta.automezzo.targa}'
                        )
                    except Exception as e:
                        logger.warning(f'Errore creazione manutenzione da preventivo: {str(e)}')
                        messages.warning(
                            request,
                            f'Ordine creato, ma errore nella creazione della manutenzione: {str(e)}'
                        )

            except Exception as e:
                logger.error(f'Errore approvazione offerta e creazione ODA: {str(e)}')
                messages.error(
                    request,
                    f'Errore durante l\'approvazione: {str(e)}'
                )
                return redirect('preventivi_beni:step3_valutazione', pk=pk)

            return redirect('preventivi_beni:richiesta_detail', pk=pk)
    else:
        form = SceltaOffertaForm(richiesta=richiesta)

    context = {
        'richiesta': richiesta,
        'offerte': offerte,
        'form': form,
    }
    return render(request, 'preventivi_beni/step3_valutazione.html', context)


@login_required
@transaction.atomic
def conferma_ordine(request, pk):
    """
    Conferma ordine e invia email al fornitore selezionato.
    Se c'era un fornitore precedente, invia email di annullamento.
    """
    richiesta = get_object_or_404(RichiestaPreventivo, pk=pk)

    if not richiesta.offerta_approvata:
        messages.error(request, 'Devi prima approvare un\'offerta')
        return redirect('preventivi_beni:richiesta_detail', pk=pk)

    offerta_approvata = richiesta.offerta_approvata
    fornitore_precedente = None

    # Verifica se c'era già una conferma precedente
    if richiesta.stato in ['CONFERMATA', 'ORDINATO']:
        offerte_confermate = Offerta.objects.filter(
            richiesta=richiesta,
            confermata=True
        ).exclude(pk=offerta_approvata.pk)

        if offerte_confermate.exists():
            fornitore_precedente = offerte_confermate.first().fornitore
            offerte_confermate.update(confermata=False)

    from mail.services import ManagementEmailService
    email_service = ManagementEmailService(user=request.user)

    # 1. Invia email di annullamento al fornitore precedente (se presente)
    if fornitore_precedente:
        try:
            html_annullamento = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background-color: #dc3545; color: white; padding: 20px; text-align: center; border-radius: 10px 10px 0 0; }}
                    .content {{ background-color: #f8f9fa; padding: 20px; border-radius: 0 0 10px 10px; }}
                    .info-box {{ background-color: white; padding: 15px; margin: 10px 0; border-left: 4px solid #dc3545; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>Annullamento Conferma Ordine</h1>
                    </div>
                    <div class="content">
                        <h2>Gentile {fornitore_precedente.ragione_sociale},</h2>
                        <p>Vi informiamo che la conferma dell'ordine per la richiesta <strong>{richiesta.numero}</strong>
                        è stata annullata per motivi organizzativi.</p>

                        <div class="info-box">
                            <strong>Richiesta N°:</strong> {richiesta.numero}<br>
                            <strong>Oggetto:</strong> {richiesta.titolo}
                        </div>

                        <p>Ci scusiamo per l'inconveniente e restiamo a disposizione per future collaborazioni.</p>

                        <p>Cordiali saluti</p>
                    </div>
                </div>
            </body>
            </html>
            """

            email_service.send_email(
                to=fornitore_precedente.email,
                subject=f'Annullamento Conferma Ordine - {richiesta.numero}',
                html_content=html_annullamento,
                source_object=richiesta,
                category='preventivi_beni'
            )

        except Exception as e:
            logger.error(f'Errore invio email annullamento: {str(e)}')

    # 2. Invia email di conferma al nuovo fornitore
    try:
        # Prepara tabella voci
        voci_html = ""
        for voce in richiesta.voci.all().order_by('ordine'):
            voci_html += f"""
            <tr>
                <td style="padding: 8px; border: 1px solid #dee2e6;">{voce.descrizione}</td>
                <td style="padding: 8px; border: 1px solid #dee2e6;">{voce.quantita} {voce.get_unita_misura_display()}</td>
            </tr>
            """

        html_conferma = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #28a745; color: white; padding: 20px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background-color: #f8f9fa; padding: 20px; }}
                .info-box {{ background-color: white; padding: 15px; margin: 10px 0; border-left: 4px solid #28a745; }}
                .highlight {{ background-color: #d4edda; padding: 15px; border-radius: 5px; text-align: center; margin: 20px 0; }}
                table {{ width: 100%; border-collapse: collapse; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Conferma Ordine</h1>
                </div>
                <div class="content">
                    <h2>Gentile {offerta_approvata.fornitore.ragione_sociale},</h2>
                    <p>Siamo lieti di confermarvi l'ordine di seguito descritto:</p>

                    <div class="info-box">
                        <strong>Richiesta N°:</strong> {richiesta.numero}<br>
                        <strong>Oggetto:</strong> {richiesta.titolo}<br>
                        <strong>Tipo:</strong> {richiesta.get_tipo_richiesta_display()}
                    </div>

                    <div class="highlight">
                        <h3 style="color: #155724; margin: 0;">Importo Confermato</h3>
                        <p style="font-size: 24px; font-weight: bold; color: #28a745; margin: 10px 0;">
                            {offerta_approvata.importo_totale:,.2f} {offerta_approvata.valuta}
                        </p>
                    </div>

                    <h3>Articoli/Servizi Ordinati</h3>
                    <table>
                        <thead>
                            <tr style="background-color: #f1f3f5;">
                                <th style="padding: 10px; border: 1px solid #dee2e6;">Descrizione</th>
                                <th style="padding: 10px; border: 1px solid #dee2e6;">Quantità</th>
                            </tr>
                        </thead>
                        <tbody>
                            {voci_html}
                        </tbody>
                    </table>

                    <div class="info-box">
                        {f'<strong>Luogo Consegna:</strong> {richiesta.luogo_consegna}<br>' if richiesta.luogo_consegna else ''}
                        {f'<strong>Data Consegna:</strong> {offerta_approvata.data_consegna_proposta.strftime("%d/%m/%Y")}<br>' if offerta_approvata.data_consegna_proposta else ''}
                        {f'<strong>Termini Pagamento:</strong> {offerta_approvata.get_termini_pagamento_display()}<br>' if offerta_approvata.termini_pagamento else ''}
                    </div>

                    <p>Per qualsiasi chiarimento, non esitate a contattarci.</p>

                    <p>Cordiali saluti</p>
                </div>
            </div>
        </body>
        </html>
        """

        # Crea Ordine di Acquisto (ODA)
        from acquisti.services import crea_ordine_da_preventivo, genera_pdf_ordine
        ordine_acquisto = crea_ordine_da_preventivo(richiesta, offerta_approvata, request.user)

        # Genera PDF dell'ordine
        pdf_buffer = genera_pdf_ordine(ordine_acquisto)
        pdf_filename = f"ODA_{ordine_acquisto.numero_ordine.replace('-', '_')}.pdf"

        # Aggiorna HTML con numero ODA
        html_conferma = html_conferma.replace(
            '<h1>Conferma Ordine</h1>',
            f'<h1>Conferma Ordine - {ordine_acquisto.numero_ordine}</h1>'
        )
        html_conferma = html_conferma.replace(
            '</div>\n                </div>\n            </div>\n        </body>',
            f'''<div class="info-box" style="margin-top: 20px;">
                            <strong>Numero Ordine di Acquisto:</strong> {ordine_acquisto.numero_ordine}<br>
                            <em>In allegato il documento ufficiale dell'ordine.</em>
                        </div>
                    </div>
                </div>
            </div>
        </body>'''
        )

        # Prepara allegato PDF
        pdf_attachment = (pdf_filename, pdf_buffer.read(), 'application/pdf')

        result = email_service.send_email(
            to=offerta_approvata.fornitore.email,
            subject=f'Ordine di Acquisto {ordine_acquisto.numero_ordine} - {richiesta.numero}',
            html_content=html_conferma,
            source_object=richiesta,
            category='preventivi_beni',
            attachments=[pdf_attachment]
        )

        if result.get('success'):
            # Aggiorna stato
            offerta_approvata.confermata = True
            offerta_approvata.data_conferma = timezone.now()
            offerta_approvata.save()

            richiesta.stato = 'CONFERMATA'
            richiesta.data_conferma = timezone.now()
            richiesta.save()

            msg = f'Ordine {ordine_acquisto.numero_ordine} creato! Email inviata a {offerta_approvata.fornitore}'
            if fornitore_precedente:
                msg += f'. Email di annullamento inviata a {fornitore_precedente}'

            messages.success(request, msg)
        else:
            # Se email fallisce, elimina l'ordine creato
            ordine_acquisto.delete()
            messages.error(request, f'Errore invio email: {result.get("error")}')

    except Exception as e:
        logger.error(f'Errore conferma ordine: {str(e)}')
        messages.error(request, f'Errore durante la conferma: {str(e)}')

    return redirect('preventivi_beni:richiesta_detail', pk=pk)


@login_required
@transaction.atomic
def riapri_richiesta(request, pk):
    """
    Riapre una richiesta confermata per selezionare un altro fornitore.
    """
    richiesta = get_object_or_404(RichiestaPreventivo, pk=pk)

    if richiesta.stato not in ['CONFERMATA', 'ORDINATO']:
        messages.warning(request, 'Questa richiesta non può essere riaperta')
        return redirect('preventivi_beni:richiesta_detail', pk=pk)

    # Riporta lo stato a APPROVATA
    richiesta.stato = 'APPROVATA'
    richiesta.save()

    messages.info(request, f'Richiesta {richiesta.numero} riaperta. Puoi ora selezionare un altro fornitore.')

    return redirect('preventivi_beni:step3_valutazione', pk=pk)


# ============================================
# GESTIONE OFFERTE
# ============================================

@login_required
@transaction.atomic
def offerta_create(request, richiesta_pk):
    """Crea nuova offerta"""

    richiesta = get_object_or_404(RichiestaPreventivo, pk=richiesta_pk)

    if request.method == 'POST':
        form = OffertaForm(request.POST, request.FILES, richiesta=richiesta, user=request.user)
        if form.is_valid():
            offerta = form.save(commit=False)
            offerta.richiesta = richiesta
            offerta.operatore_inserimento = request.user
            offerta.save()

            # Aggiorna stato FornitorePreventivo
            FornitorePreventivo.objects.filter(
                richiesta=richiesta,
                fornitore=offerta.fornitore
            ).update(ha_risposto=True, data_risposta=timezone.now())

            messages.success(request, 'Offerta inserita con successo')
            return redirect('preventivi_beni:step2_raccolta', pk=richiesta.pk)
    else:
        form = OffertaForm(richiesta=richiesta, user=request.user)

    context = {
        'richiesta': richiesta,
        'form': form,
    }
    return render(request, 'preventivi_beni/offerta_create.html', context)


@login_required
def offerta_detail(request, pk):
    """Dettaglio offerta"""
    offerta = get_object_or_404(Offerta, pk=pk)

    context = {
        'offerta': offerta,
    }
    return render(request, 'preventivi_beni/offerta_detail.html', context)


# ============================================
# API ENDPOINTS (AJAX)
# ============================================

@login_required
def offerta_parametri_get(request, pk):
    """AJAX: Get parametri valutazione offerta"""

    try:
        offerta = Offerta.objects.get(pk=pk)
        parametri = list(offerta.parametri.values('id', 'descrizione', 'valore', 'ordine'))

        return JsonResponse({'parametri': parametri})
    except Offerta.DoesNotExist:
        return JsonResponse({'error': 'Offerta non trovata'}, status=404)


@login_required
def offerta_parametri_save(request, pk):
    """AJAX: Save parametri valutazione offerta"""

    if request.method != 'POST':
        return JsonResponse({'error': 'Metodo non supportato'}, status=405)

    try:
        import json
        offerta = Offerta.objects.get(pk=pk)
        data = json.loads(request.body)
        parametri_data = data.get('parametri', [])

        # Elimina parametri esistenti
        offerta.parametri.all().delete()

        # Crea nuovi parametri
        for i, param in enumerate(parametri_data):
            ParametroValutazione.objects.create(
                offerta=offerta,
                descrizione=param.get('descrizione', ''),
                valore=param.get('valore', ''),
                ordine=i,
                creato_da=request.user
            )

        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def risposta_fornitore_pubblica(request, token):
    """
    View pubblica per la risposta dei fornitori tramite token.
    Non richiede autenticazione.
    """
    from .forms import RispostaFornitoreForm

    # Recupera il FornitorePreventivo tramite token
    fornitore_preventivo = get_object_or_404(
        FornitorePreventivo,
        token_accesso=token
    )

    richiesta = fornitore_preventivo.richiesta
    fornitore = fornitore_preventivo.fornitore

    # Verifica se è già stata inviata un'offerta
    offerta_esistente = Offerta.objects.filter(
        richiesta=richiesta,
        fornitore=fornitore
    ).first()

    if request.method == 'POST':
        form = RispostaFornitoreForm(request.POST, request.FILES)

        if form.is_valid():
            # Estrai dati dal form
            importo_totale = form.cleaned_data['importo_totale']
            tempo_consegna_giorni = form.cleaned_data['tempo_consegna_giorni']
            data_consegna_proposta = form.cleaned_data.get('data_consegna_proposta')
            validita_offerta_giorni = form.cleaned_data['validita_offerta_giorni']
            allegato = form.cleaned_data.get('allegato')
            note = form.cleaned_data.get('note', '')

            # Crea o aggiorna l'offerta
            if offerta_esistente:
                offerta = offerta_esistente
                offerta.importo_merce = importo_totale
                offerta.importo_totale = importo_totale
                offerta.tempo_consegna_giorni = tempo_consegna_giorni
                offerta.data_consegna_proposta = data_consegna_proposta
                offerta.validita_offerta_giorni = validita_offerta_giorni
                offerta.note_commerciali = note
                if allegato:
                    offerta.file_offerta = allegato
                offerta.save()

                messages.success(request, 'Offerta aggiornata con successo!')
            else:
                offerta = Offerta.objects.create(
                    richiesta=richiesta,
                    fornitore=fornitore,
                    importo_merce=importo_totale,
                    importo_totale=importo_totale,
                    tempo_consegna_giorni=tempo_consegna_giorni,
                    data_consegna_proposta=data_consegna_proposta,
                    validita_offerta_giorni=validita_offerta_giorni,
                    note_commerciali=note,
                    file_offerta=allegato if allegato else None
                )

                # Marca come risposto
                fornitore_preventivo.ha_risposto = True
                fornitore_preventivo.data_risposta = timezone.now()
                fornitore_preventivo.save()

                # Aggiorna stato richiesta se necessario
                if richiesta.stato == 'RICHIESTA_INVIATA':
                    richiesta.stato = 'OFFERTE_RICEVUTE'
                    richiesta.save()

                messages.success(request, 'Offerta inviata con successo!')

            return redirect('preventivi_beni:risposta_fornitore_pubblica', token=token)
    else:
        # Pre-compila il form se esiste già un'offerta
        initial_data = {}
        if offerta_esistente:
            initial_data = {
                'importo_totale': offerta_esistente.importo_totale,
                'tempo_consegna_giorni': offerta_esistente.tempo_consegna_giorni,
                'data_consegna_proposta': offerta_esistente.data_consegna_proposta,
                'validita_offerta_giorni': offerta_esistente.validita_offerta_giorni,
                'note': offerta_esistente.note_commerciali,
            }

        form = RispostaFornitoreForm(initial=initial_data)

    context = {
        'form': form,
        'richiesta': richiesta,
        'fornitore': fornitore,
        'fornitore_preventivo': fornitore_preventivo,
        'offerta_esistente': offerta_esistente,
    }

    return render(request, 'preventivi_beni/risposta_fornitore_pubblica.html', context)
