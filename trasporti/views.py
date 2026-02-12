"""
Views for Trasporti app
=======================

Views complete con workflow 3 step simile a preventivi.
"""

import logging
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.utils import timezone
from django.db import transaction
from django.db.models import Q, Count

logger = logging.getLogger(__name__)

from .models import (
    RichiestaTrasporto, OffertaTrasporto, Collo,
    TrasportatoreOfferta, ParametroValutazione
)
from .forms import (
    RichiestaTrasportoForm, ColloFormSet,
    SceltaTrasportatoriForm, OffertaTrasportoForm, SceltaOffertaForm
)


# ============================================
# DASHBOARD E LISTE
# ============================================

@login_required
def dashboard(request):
    """Dashboard trasporti"""

    # Statistiche rapide
    richieste_attive = RichiestaTrasporto.objects.exclude(
        stato__in=['CONSEGNATO', 'ANNULLATA']
    ).count()

    richieste_in_corso = RichiestaTrasporto.objects.filter(stato='IN_CORSO').count()

    richieste_bozza = RichiestaTrasporto.objects.filter(
        stato='BOZZA',
        richiedente=request.user
    ).count()

    # Richieste recenti
    richieste_recenti = RichiestaTrasporto.objects.all().order_by('-data_creazione')[:5]

    context = {
        'richieste_attive': richieste_attive,
        'richieste_in_corso': richieste_in_corso,
        'richieste_bozza': richieste_bozza,
        'richieste_recenti': richieste_recenti,
    }
    return render(request, 'trasporti/dashboard.html', context)


@login_required
def richieste_list(request):
    """Lista richieste trasporto con filtri"""

    richieste = RichiestaTrasporto.objects.all()

    # Filtri
    stato = request.GET.get('stato')
    tipo = request.GET.get('tipo')
    search = request.GET.get('search')

    if stato:
        richieste = richieste.filter(stato=stato)
    if tipo:
        richieste = richieste.filter(tipo_trasporto=tipo)
    if search:
        richieste = richieste.filter(
            Q(numero__icontains=search) |
            Q(titolo__icontains=search) |
            Q(citta_ritiro__icontains=search) |
            Q(citta_consegna__icontains=search)
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
        'search': search,
    }
    return render(request, 'trasporti/richieste_list.html', context)


@login_required
def richiesta_detail(request, pk):
    """Dettaglio richiesta"""
    richiesta = get_object_or_404(RichiestaTrasporto, pk=pk)

    # Content type per allegati e QR code
    from django.contrib.contenttypes.models import ContentType
    content_type = ContentType.objects.get_for_model(richiesta)

    context = {
        'richiesta': richiesta,
        'object': richiesta,  # Per template comune
        'content_type_id': content_type.id,
        'back_url': '/trasporti/richieste/',
    }
    return render(request, 'trasporti/richiesta_detail.html', context)


# ============================================
# CREAZIONE RICHIESTA
# ============================================

@login_required
@transaction.atomic
def richiesta_create(request):
    """Crea nuova richiesta trasporto con colli"""

    if request.method == 'POST':
        form = RichiestaTrasportoForm(request.POST, user=request.user)
        formset = ColloFormSet(request.POST)

        if form.is_valid() and formset.is_valid():
            richiesta = form.save(commit=False)
            richiesta.richiedente = request.user
            richiesta.save()

            # Salva colli
            formset.instance = richiesta
            formset.save()

            messages.success(request, f'Richiesta trasporto {richiesta.numero} creata con successo!')
            return redirect('trasporti:richiesta_detail', pk=richiesta.pk)
    else:
        form = RichiestaTrasportoForm(user=request.user)
        formset = ColloFormSet()

    context = {
        'form': form,
        'formset': formset,
    }
    return render(request, 'trasporti/richiesta_create.html', context)


# ============================================
# SELEZIONE TRASPORTATORI
# ============================================

@login_required
@transaction.atomic
def richiesta_select_trasportatori(request, pk):
    """Seleziona trasportatori per richiesta (esistenti + nuovi)"""

    richiesta = get_object_or_404(RichiestaTrasporto, pk=pk)

    if richiesta.stato != 'BOZZA':
        messages.warning(request, 'Puoi selezionare i trasportatori solo in stato BOZZA')
        return redirect('trasporti:richiesta_detail', pk=pk)

    if request.method == 'POST':
        form = SceltaTrasportatoriForm(request.POST)
        if form.is_valid():
            trasportatori_esistenti = form.cleaned_data.get('trasportatori_esistenti', [])
            nuovi_fornitori = form.cleaned_data.get('nuovi_fornitori', [])

            count_esistenti = 0
            count_nuovi = 0

            # Crea record TrasportatoreOfferta per fornitori esistenti
            for trasportatore in trasportatori_esistenti:
                TrasportatoreOfferta.objects.get_or_create(
                    richiesta=richiesta,
                    trasportatore=trasportatore
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
                trasportatore_offerta, _ = TrasportatoreOfferta.objects.get_or_create(
                    richiesta=richiesta,
                    trasportatore=fornitore
                )

                if created:
                    trasportatore_offerta.note_trasportatore = f"Fornitore non accreditato. Email: {nuovo['email']}"
                    trasportatore_offerta.save()
                    count_nuovi += 1

            # Messaggio di successo
            msg_parts = []
            if count_esistenti:
                msg_parts.append(f'{count_esistenti} fornitore/i esistente/i')
            if count_nuovi:
                msg_parts.append(f'{count_nuovi} nuovo/i fornitore/i')

            messages.success(request, f'Selezionati: {", ".join(msg_parts)}')
            return redirect('trasporti:step1_invia', pk=pk)
    else:
        form = SceltaTrasportatoriForm()

    context = {
        'richiesta': richiesta,
        'form': form,
        'trasportatori_selezionati': richiesta.trasportatori.all(),
    }
    return render(request, 'trasporti/richiesta_select_trasportatori.html', context)


# ============================================
# WORKFLOW 3 STEP
# ============================================

@login_required
def step1_invia_trasportatori(request, pk):
    """Step 1: Invio richieste ai trasportatori con email integrate"""

    richiesta = get_object_or_404(RichiestaTrasporto, pk=pk)

    if richiesta.stato not in ['BOZZA', 'RICHIESTA_INVIATA']:
        messages.warning(request, 'Richiesta già inviata')
        return redirect('trasporti:richiesta_detail', pk=pk)

    trasportatori_offerte = TrasportatoreOfferta.objects.filter(richiesta=richiesta)

    if not trasportatori_offerte.exists():
        messages.error(request, 'Seleziona almeno un trasportatore prima di inviare')
        return redirect('trasporti:richiesta_select_trasportatori', pk=pk)

    if request.method == 'POST':
        # Invia email con servizio integrato
        from mail.services import ManagementEmailService
        email_service = ManagementEmailService(user=request.user)

        count_success = 0
        count_failed = 0
        errors = []

        for trasportatore_offerta in trasportatori_offerte:
            if trasportatore_offerta.email_inviata:
                continue  # Già inviata

            trasportatore = trasportatore_offerta.trasportatore

            # Verifica email
            email_dest = trasportatore.email
            if not email_dest:
                errors.append(f'{trasportatore.nome}: email mancante')
                count_failed += 1
                continue

            try:
                # Prepara contesto email
                context = {
                    'richiesta': richiesta,
                    'trasportatore': trasportatore,
                    'trasportatore_offerta': trasportatore_offerta,
                    'link_risposta': request.build_absolute_uri(
                        f'/trasporti/risposta/{trasportatore_offerta.token_accesso}/'
                    ),
                }

                # Crea contenuto HTML
                html_content = f"""
                <html>
                <head>
                    <style>
                        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                        .header {{ background-color: #007bff; color: white; padding: 20px; text-align: center; }}
                        .content {{ background-color: #f8f9fa; padding: 20px; margin: 20px 0; }}
                        .info-box {{ background-color: white; padding: 15px; margin: 10px 0; border-left: 4px solid #007bff; }}
                        .button {{ display: inline-block; padding: 12px 24px; background-color: #28a745; color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                        .footer {{ text-align: center; color: #6c757d; font-size: 12px; margin-top: 30px; }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="header">
                            <h1>Richiesta Preventivo Trasporto</h1>
                        </div>
                        <div class="content">
                            <h2>Gentile {trasportatore.nome},</h2>
                            <p>Vi sottoponiamo una richiesta di preventivo per il seguente trasporto:</p>

                            <div class="info-box">
                                <strong>Richiesta N°:</strong> {richiesta.numero}<br>
                                <strong>Titolo:</strong> {richiesta.titolo}<br>
                                <strong>Tipo Trasporto:</strong> {richiesta.get_tipo_trasporto_display()}
                            </div>

                            <div class="info-box">
                                <strong>RITIRO</strong><br>
                                Indirizzo: {richiesta.indirizzo_ritiro}<br>
                                Città: {richiesta.cap_ritiro} {richiesta.citta_ritiro} ({richiesta.provincia_ritiro})<br>
                                Data: {richiesta.data_ritiro_richiesta.strftime('%d/%m/%Y')}<br>
                                {f"Orario: {richiesta.ora_ritiro_dalle.strftime('%H:%M')} - {richiesta.ora_ritiro_alle.strftime('%H:%M')}" if richiesta.ora_ritiro_dalle else ""}
                            </div>

                            <div class="info-box">
                                <strong>CONSEGNA</strong><br>
                                Indirizzo: {richiesta.indirizzo_consegna}<br>
                                Città: {richiesta.cap_consegna} {richiesta.citta_consegna} ({richiesta.provincia_consegna})<br>
                                Data: {richiesta.data_consegna_richiesta.strftime('%d/%m/%Y')}<br>
                                {f"Orario: {richiesta.ora_consegna_dalle.strftime('%H:%M')} - {richiesta.ora_consegna_alle.strftime('%H:%M')}" if richiesta.ora_consegna_dalle else ""}
                            </div>

                            <div class="info-box">
                                <strong>DETTAGLI MERCE</strong><br>
                                Tipo Merce: {richiesta.tipo_merce}<br>
                                N° Colli: {richiesta.numero_colli_totali}<br>
                                Peso Totale: {richiesta.peso_totale_kg} kg<br>
                                Volume Totale: {richiesta.volume_totale_m3} m³
                            </div>

                            <div class="info-box">
                                <strong>DETTAGLIO COLLI</strong><br>
                                <table style="width: 100%; border-collapse: collapse; margin-top: 10px;">
                                    <thead>
                                        <tr style="background-color: #f1f3f5;">
                                            <th style="padding: 8px; border: 1px solid #dee2e6; text-align: left;">Q.tà</th>
                                            <th style="padding: 8px; border: 1px solid #dee2e6; text-align: left;">Tipo</th>
                                            <th style="padding: 8px; border: 1px solid #dee2e6; text-align: left;">Dimensioni (cm)</th>
                                            <th style="padding: 8px; border: 1px solid #dee2e6; text-align: left;">Peso</th>
                                            <th style="padding: 8px; border: 1px solid #dee2e6; text-align: left;">Volume</th>
                                            <th style="padding: 8px; border: 1px solid #dee2e6; text-align: left;">Note</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {''.join([
                                            f'''<tr>
                                                <td style="padding: 8px; border: 1px solid #dee2e6;">{collo.quantita}</td>
                                                <td style="padding: 8px; border: 1px solid #dee2e6;">{collo.get_tipo_display()}</td>
                                                <td style="padding: 8px; border: 1px solid #dee2e6;">{collo.lunghezza_cm} × {collo.larghezza_cm} × {collo.altezza_cm}</td>
                                                <td style="padding: 8px; border: 1px solid #dee2e6;">{collo.peso_kg} kg</td>
                                                <td style="padding: 8px; border: 1px solid #dee2e6;">{collo.volume_m3} m³</td>
                                                <td style="padding: 8px; border: 1px solid #dee2e6;">
                                                    {collo.descrizione if collo.descrizione else ''}
                                                    {'<br><span style="color: #dc3545;">⚠ FRAGILE</span>' if collo.fragile else ''}
                                                    {'<br><span style="color: #6c757d;">✗ NON Impilabile</span>' if not collo.stackable else ''}
                                                </td>
                                            </tr>'''
                                            for collo in richiesta.colli.all().order_by('ordine')
                                        ])}
                                    </tbody>
                                </table>
                            </div>

                            {'<div class="info-box"><strong>Note:</strong><br>' + richiesta.note_interne + '</div>' if richiesta.note_interne else ''}

                            <p style="text-align: center;">
                                <a href="{context['link_risposta']}" class="button">INVIA LA TUA OFFERTA</a>
                            </p>

                            <p><small>Oppure rispondi direttamente a questa email con la tua offerta.</small></p>
                        </div>
                        <div class="footer">
                            <p>Questa è una richiesta automatica del sistema di gestione trasporti.<br>
                            Per informazioni contattare: {request.user.email}</p>
                        </div>
                    </div>
                </body>
                </html>
                """

                # Invia email
                result = email_service.send_email(
                    to=email_dest,
                    subject=f'Richiesta Preventivo Trasporto - {richiesta.numero}',
                    html_content=html_content,
                    source_object=richiesta,
                    category='trasporti'
                )

                if result.get('success'):
                    trasportatore_offerta.email_inviata = True
                    trasportatore_offerta.data_invio = timezone.now()
                    trasportatore_offerta.save()
                    count_success += 1
                else:
                    error_msg = result.get('error', 'Errore sconosciuto')
                    errors.append(f'{trasportatore.nome}: {error_msg}')
                    count_failed += 1

            except Exception as e:
                logger.error(f'Errore invio email a {trasportatore.nome}: {str(e)}')
                errors.append(f'{trasportatore.nome}: {str(e)}')
                count_failed += 1

        # Aggiorna stato richiesta se almeno una email inviata
        if count_success > 0:
            richiesta.stato = 'RICHIESTA_INVIATA'
            richiesta.data_invio_richiesta = timezone.now()
            richiesta.operatore = request.user
            richiesta.save()

        # Messaggi di feedback
        if count_success > 0:
            messages.success(request, f'✓ Richiesta inviata con successo a {count_success} trasportatori')

        if count_failed > 0:
            messages.warning(request, f'⚠ Invio fallito per {count_failed} trasportatori')
            for error in errors[:5]:  # Mostra massimo 5 errori
                messages.error(request, error)

        return redirect('trasporti:richiesta_detail', pk=pk)

    context = {
        'richiesta': richiesta,
        'trasportatori_offerte': trasportatori_offerte,
    }
    return render(request, 'trasporti/step1_invia.html', context)


@login_required
def step2_raccolta_offerte(request, pk):
    """Step 2: Raccolta offerte dai trasportatori"""

    richiesta = get_object_or_404(RichiestaTrasporto, pk=pk)

    if richiesta.stato not in ['RICHIESTA_INVIATA', 'OFFERTE_RICEVUTE']:
        messages.warning(request, 'La richiesta deve essere in stato RICHIESTA_INVIATA')
        return redirect('trasporti:richiesta_detail', pk=pk)

    offerte = richiesta.offerte.all().order_by('importo_totale')
    trasportatori_offerte = TrasportatoreOfferta.objects.filter(richiesta=richiesta)

    # Statistiche
    totale_trasportatori = trasportatori_offerte.count()
    trasportatori_risposto = trasportatori_offerte.filter(ha_risposto=True).count()

    if request.method == 'POST':
        if offerte.count() >= 2:
            richiesta.stato = 'OFFERTE_RICEVUTE'
            richiesta.save()
            messages.success(request, 'Raccolta offerte completata')
            return redirect('trasporti:step3_valutazione', pk=pk)
        else:
            messages.error(request, 'Servono almeno 2 offerte per procedere')

    context = {
        'richiesta': richiesta,
        'offerte': offerte,
        'totale_trasportatori': totale_trasportatori,
        'trasportatori_risposto': trasportatori_risposto,
    }
    return render(request, 'trasporti/step2_raccolta.html', context)


@login_required
@transaction.atomic
def step3_valutazione(request, pk):
    """Step 3: Valutazione, approvazione offerta e creazione ODA"""

    richiesta = get_object_or_404(RichiestaTrasporto, pk=pk)

    if richiesta.stato not in ['OFFERTE_RICEVUTE', 'IN_VALUTAZIONE', 'APPROVATA']:
        messages.warning(request, 'Devi prima raccogliere le offerte')
        return redirect('trasporti:richiesta_detail', pk=pk)

    offerte = richiesta.offerte.all().order_by('importo_totale')

    if request.method == 'POST':
        form = SceltaOffertaForm(request.POST, richiesta=richiesta)
        if form.is_valid():
            offerta_scelta = form.cleaned_data['offerta_scelta']
            note = form.cleaned_data.get('note_approvazione', '')

            trasportatore = offerta_scelta.trasportatore

            try:
                # 1. Crea Ordine di Acquisto (ODA)
                from acquisti.services import crea_ordine_da_trasporto, genera_pdf_ordine
                ordine_acquisto = crea_ordine_da_trasporto(richiesta, offerta_scelta, request.user)

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

                html_content = f"""
                <html>
                <head>
                    <style>
                        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                        .header {{ background: linear-gradient(135deg, #74b49b 0%, #5c8d89 100%); color: white; padding: 20px; text-align: center; border-radius: 10px 10px 0 0; }}
                        .content {{ background-color: #f8f9fa; padding: 20px; border-radius: 0 0 10px 10px; }}
                        .info-box {{ background-color: white; padding: 15px; margin: 10px 0; border-left: 4px solid #74b49b; border-radius: 5px; }}
                        .highlight {{ background-color: #d3f6d1; padding: 15px; border-radius: 5px; text-align: center; margin: 20px 0; }}
                        .footer {{ text-align: center; color: #6c757d; font-size: 12px; margin-top: 30px; }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="header">
                            <h1>Conferma Ordine - {ordine_acquisto.numero_ordine}</h1>
                        </div>
                        <div class="content">
                            <h2>Gentile {trasportatore.nome},</h2>
                            <p>Siamo lieti di comunicarvi che la vostra offerta per il trasporto
                            <strong>{richiesta.numero}</strong> è stata <strong>approvata</strong> e confermata.</p>

                            <div class="info-box">
                                <strong>Richiesta N°:</strong> {richiesta.numero}<br>
                                <strong>Ordine di Acquisto N°:</strong> {ordine_acquisto.numero_ordine}<br>
                                <strong>Titolo:</strong> {richiesta.titolo}<br>
                                <strong>Percorso:</strong> {richiesta.citta_ritiro} → {richiesta.citta_consegna}
                            </div>

                            <div class="highlight">
                                <h3 style="color: #5c8d89; margin: 0;">Importo Confermato</h3>
                                <p style="font-size: 24px; font-weight: bold; color: #74b49b; margin: 10px 0;">
                                    € {offerta_scelta.importo_totale:,.2f}
                                </p>
                            </div>

                            <div class="info-box">
                                <strong>Dettagli Trasporto:</strong><br>
                                Tipo: {richiesta.get_tipo_trasporto_display()}<br>
                                Colli: {richiesta.numero_colli_totali}<br>
                                Peso: {richiesta.peso_totale_kg} kg<br>
                                Data Ritiro: {offerta_scelta.data_ritiro_proposta.strftime('%d/%m/%Y') if offerta_scelta.data_ritiro_proposta else 'Da definire'}<br>
                                Data Consegna: {offerta_scelta.data_consegna_prevista.strftime('%d/%m/%Y') if offerta_scelta.data_consegna_prevista else 'Da definire'}
                            </div>

                            <div class="info-box" style="border-left-color: #17a2b8;">
                                <strong>In allegato:</strong> Ordine di Acquisto ufficiale (PDF)<br>
                                <em>Si prega di procedere con il trasporto secondo i termini indicati nell'ordine.</em>
                            </div>

                            <p>Per qualsiasi chiarimento, non esitate a contattarci.</p>

                            <p>Cordiali saluti,<br>
                            <strong>Team Trasporti</strong></p>
                        </div>
                        <div class="footer">
                            <p>Questa è una notifica automatica del sistema di gestione trasporti.<br>
                            Per informazioni contattare: {request.user.email}</p>
                        </div>
                    </div>
                </body>
                </html>
                """

                # Prepara allegato PDF
                pdf_attachment = (pdf_filename, pdf_buffer.read(), 'application/pdf')

                result = email_service.send_email(
                    to=trasportatore.email,
                    subject=f'Ordine di Acquisto {ordine_acquisto.numero_ordine} - Trasporto {richiesta.numero}',
                    html_content=html_content,
                    source_object=richiesta,
                    category='trasporti',
                    attachments=[pdf_attachment]
                )

                if result.get('success'):
                    messages.success(
                        request,
                        f'Ordine {ordine_acquisto.numero_ordine} creato e inviato a {trasportatore.nome}!'
                    )
                else:
                    messages.warning(
                        request,
                        f'Ordine {ordine_acquisto.numero_ordine} creato, ma email non inviata: {result.get("error")}'
                    )

            except Exception as e:
                logger.error(f'Errore approvazione offerta trasporto e creazione ODA: {str(e)}')
                messages.error(
                    request,
                    f'Errore durante l\'approvazione: {str(e)}'
                )
                return redirect('trasporti:step3_valutazione', pk=pk)

            return redirect('trasporti:richiesta_detail', pk=pk)
    else:
        form = SceltaOffertaForm(richiesta=richiesta)

    context = {
        'richiesta': richiesta,
        'offerte': offerte,
        'form': form,
    }
    return render(request, 'trasporti/step3_valutazione.html', context)


@login_required
@transaction.atomic
def conferma_trasporto(request, pk):
    """
    Conferma trasporto e invia email al fornitore selezionato.
    Se c'era un fornitore precedente, invia email di annullamento.
    """
    richiesta = get_object_or_404(RichiestaTrasporto, pk=pk)

    if not richiesta.offerta_approvata:
        messages.error(request, 'Devi prima approvare un\'offerta')
        return redirect('trasporti:richiesta_detail', pk=pk)

    offerta_approvata = richiesta.offerta_approvata
    fornitore_precedente = None

    # Verifica se c'era già una conferma precedente
    if richiesta.stato in ['CONFERMATA', 'IN_CORSO', 'CONSEGNATO']:
        # Salva il fornitore precedente per inviargli l'annullamento
        # Cerca l'offerta che era stata confermata prima
        offerte_confermate = OffertaTrasporto.objects.filter(
            richiesta=richiesta,
            confermata=True
        ).exclude(pk=offerta_approvata.pk)

        if offerte_confermate.exists():
            fornitore_precedente = offerte_confermate.first().trasportatore
            # Segna come non confermata
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
                    body {{ font-family: 'Ubuntu', Arial, sans-serif; line-height: 1.6; color: #393e46; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: linear-gradient(135deg, #dc3545 0%, #c82333 100%); color: white; padding: 20px; text-align: center; border-radius: 10px 10px 0 0; }}
                    .content {{ background-color: #f8f9fa; padding: 20px; margin: 20px 0; border-radius: 0 0 10px 10px; }}
                    .info-box {{ background-color: white; padding: 15px; margin: 10px 0; border-left: 4px solid #dc3545; border-radius: 5px; }}
                    .footer {{ text-align: center; color: #6c757d; font-size: 12px; margin-top: 30px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>⚠ Annullamento Conferma Trasporto</h1>
                    </div>
                    <div class="content">
                        <h2>Gentile {fornitore_precedente.ragione_sociale},</h2>
                        <p>Vi informiamo che la conferma del trasporto per la richiesta <strong>{richiesta.numero}</strong>
                        è stata annullata per motivi organizzativi.</p>

                        <div class="info-box">
                            <strong>Richiesta N°:</strong> {richiesta.numero}<br>
                            <strong>Titolo:</strong> {richiesta.titolo}<br>
                            <strong>Percorso:</strong> {richiesta.citta_ritiro} → {richiesta.citta_consegna}
                        </div>

                        <p>Ci scusiamo per l'inconveniente e restiamo a disposizione per future collaborazioni.</p>

                        <p>Cordiali saluti,<br>
                        <strong>Team Trasporti</strong></p>
                    </div>
                    <div class="footer">
                        <p>Questa è una notifica automatica del sistema di gestione trasporti.<br>
                        Per informazioni contattare: {request.user.email}</p>
                    </div>
                </div>
            </body>
            </html>
            """

            email_service.send_email(
                to=fornitore_precedente.email,
                subject=f'Annullamento Conferma Trasporto - {richiesta.numero}',
                html_content=html_annullamento,
                source_object=richiesta,
                category='trasporti'
            )

            logger.info(f'Email annullamento inviata a {fornitore_precedente.ragione_sociale}')
        except Exception as e:
            logger.error(f'Errore invio email annullamento: {str(e)}')

    # 2. Invia email di conferma al nuovo fornitore
    try:
        html_conferma = f"""
        <html>
        <head>
            <style>
                body {{ font-family: 'Ubuntu', Arial, sans-serif; line-height: 1.6; color: #393e46; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #74b49b 0%, #5c8d89 100%); color: white; padding: 20px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background-color: #f8f9fa; padding: 20px; margin: 20px 0; }}
                .info-box {{ background-color: white; padding: 15px; margin: 10px 0; border-left: 4px solid #74b49b; border-radius: 5px; }}
                .highlight {{ background-color: #d3f6d1; padding: 15px; border-radius: 5px; text-align: center; margin: 20px 0; }}
                .footer {{ text-align: center; color: #6c757d; font-size: 12px; margin-top: 30px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>✓ Conferma Trasporto</h1>
                </div>
                <div class="content">
                    <h2>Gentile {offerta_approvata.trasportatore.nome},</h2>
                    <p>Siamo lieti di confermarvi l'affidamento del trasporto di seguito descritto:</p>

                    <div class="info-box">
                        <strong>Richiesta N°:</strong> {richiesta.numero}<br>
                        <strong>Titolo:</strong> {richiesta.titolo}<br>
                        <strong>Tipo Trasporto:</strong> {richiesta.get_tipo_trasporto_display()}
                    </div>

                    <div class="highlight">
                        <h3 style="color: #5c8d89; margin: 0;">Importo Confermato</h3>
                        <p style="font-size: 24px; font-weight: bold; color: #74b49b; margin: 10px 0;">
                            €{offerta_approvata.importo_totale:,.2f}
                        </p>
                    </div>

                    <div class="info-box">
                        <strong>📍 RITIRO</strong><br>
                        Indirizzo: {richiesta.indirizzo_ritiro}<br>
                        Città: {richiesta.cap_ritiro} {richiesta.citta_ritiro} ({richiesta.provincia_ritiro})<br>
                        Data: {offerta_approvata.data_ritiro_proposta.strftime('%d/%m/%Y')}<br>
                        {f"Orario: {offerta_approvata.ora_ritiro_dalle.strftime('%H:%M')} - {offerta_approvata.ora_ritiro_alle.strftime('%H:%M')}" if offerta_approvata.ora_ritiro_dalle else ""}
                    </div>

                    <div class="info-box">
                        <strong>📦 CONSEGNA</strong><br>
                        Indirizzo: {richiesta.indirizzo_consegna}<br>
                        Città: {richiesta.cap_consegna} {richiesta.citta_consegna} ({richiesta.provincia_consegna})<br>
                        Data: {offerta_approvata.data_consegna_prevista.strftime('%d/%m/%Y')}<br>
                        {f"Orario: {offerta_approvata.ora_consegna_dalle.strftime('%H:%M')} - {offerta_approvata.ora_consegna_alle.strftime('%H:%M')}" if offerta_approvata.ora_consegna_dalle else ""}
                    </div>

                    <div class="info-box">
                        <strong>📋 DETTAGLI MERCE</strong><br>
                        Tipo Merce: {richiesta.tipo_merce}<br>
                        N° Colli: {richiesta.numero_colli_totali}<br>
                        Peso Totale: {richiesta.peso_totale_kg} kg<br>
                        Volume Totale: {richiesta.volume_totale_m3} m³
                    </div>

                    <p><strong>Prossimi passi:</strong></p>
                    <ol>
                        <li>Confermare disponibilità mezzo e conducente</li>
                        <li>Comunicare eventuali variazioni con almeno 24h di preavviso</li>
                        <li>Fornire aggiornamenti tracking durante il trasporto</li>
                    </ol>

                    <p>Per qualsiasi chiarimento, non esitate a contattarci.</p>

                    <p>Cordiali saluti,<br>
                    <strong>Team Trasporti</strong></p>
                </div>
                <div class="footer">
                    <p>Questa è una conferma automatica del sistema di gestione trasporti.<br>
                    Per informazioni contattare: {request.user.email}</p>
                </div>
            </div>
        </body>
        </html>
        """

        # Crea Ordine di Acquisto (ODA)
        from acquisti.services import crea_ordine_da_trasporto, genera_pdf_ordine
        ordine_acquisto = crea_ordine_da_trasporto(richiesta, offerta_approvata, request.user)

        # Genera PDF dell'ordine
        pdf_buffer = genera_pdf_ordine(ordine_acquisto)
        pdf_filename = f"ODA_{ordine_acquisto.numero_ordine.replace('-', '_')}.pdf"

        # Aggiorna HTML con numero ODA
        html_conferma = html_conferma.replace(
            '<h1>✓ Conferma Trasporto</h1>',
            f'<h1>✓ Conferma Trasporto - {ordine_acquisto.numero_ordine}</h1>'
        )
        html_conferma = html_conferma.replace(
            '</div>\n                <div class="footer">',
            f'''<div class="info-box" style="margin-top: 20px; border-left-color: #5585b5;">
                        <strong>Numero Ordine di Acquisto:</strong> {ordine_acquisto.numero_ordine}<br>
                        <em>In allegato il documento ufficiale dell'ordine.</em>
                    </div>
                </div>
                <div class="footer">'''
        )

        # Prepara allegato PDF
        pdf_attachment = (pdf_filename, pdf_buffer.read(), 'application/pdf')

        result = email_service.send_email(
            to=offerta_approvata.trasportatore.email,
            subject=f'Ordine di Acquisto {ordine_acquisto.numero_ordine} - Trasporto {richiesta.numero}',
            html_content=html_conferma,
            source_object=richiesta,
            category='trasporti',
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

            msg = f'Ordine {ordine_acquisto.numero_ordine} creato! Email inviata a {offerta_approvata.trasportatore.nome}'
            if fornitore_precedente:
                msg += f'. Email di annullamento inviata a {fornitore_precedente.nome}'

            messages.success(request, msg)
        else:
            # Se email fallisce, elimina l'ordine creato
            ordine_acquisto.delete()
            messages.error(request, f'Errore invio email: {result.get("error")}')

    except Exception as e:
        logger.error(f'Errore conferma trasporto: {str(e)}')
        messages.error(request, f'Errore durante la conferma: {str(e)}')

    return redirect('trasporti:richiesta_detail', pk=pk)


@login_required
@transaction.atomic
def riapri_richiesta(request, pk):
    """
    Riapre una richiesta confermata/conclusa per selezionare un altro fornitore.
    """
    richiesta = get_object_or_404(RichiestaTrasporto, pk=pk)

    # Verifica che la richiesta sia in uno stato che può essere riaperto
    if richiesta.stato not in ['CONFERMATA', 'IN_CORSO', 'CONSEGNATO']:
        messages.warning(request, 'Questa richiesta non può essere riaperta')
        return redirect('trasporti:richiesta_detail', pk=pk)

    # Riporta lo stato a APPROVATA (mantenendo l'offerta approvata)
    richiesta.stato = 'APPROVATA'
    richiesta.save()

    messages.info(request, f'Richiesta {richiesta.numero} riaperta. Puoi ora selezionare un altro fornitore.')

    return redirect('trasporti:step3_valutazione', pk=pk)


@login_required
def marca_trasporto_in_corso(request, pk):
    """
    Marca il trasporto come IN_CORSO e registra la data di ritiro effettivo.
    """
    richiesta = get_object_or_404(RichiestaTrasporto, pk=pk)

    # Verifica che la richiesta sia in stato CONFERMATA
    if richiesta.stato != 'CONFERMATA':
        messages.warning(request, 'Il trasporto deve essere confermato prima di poter essere marcato come in corso')
        return redirect('trasporti:richiesta_detail', pk=pk)

    # Aggiorna stato e data ritiro effettivo
    richiesta.stato = 'IN_CORSO'
    richiesta.data_ritiro_effettivo = timezone.now()
    richiesta.save()

    messages.success(request, f'Trasporto {richiesta.numero} marcato come IN CORSO. Data ritiro registrata: {richiesta.data_ritiro_effettivo.strftime("%d/%m/%Y %H:%M")}')

    return redirect('trasporti:richiesta_detail', pk=pk)


@login_required
def marca_consegna_effettuata(request, pk):
    """
    Marca il trasporto come CONSEGNATO e registra la data di consegna effettiva.
    """
    richiesta = get_object_or_404(RichiestaTrasporto, pk=pk)

    # Verifica che la richiesta sia in stato IN_CORSO
    if richiesta.stato != 'IN_CORSO':
        messages.warning(request, 'Il trasporto deve essere in corso prima di poter essere marcato come consegnato')
        return redirect('trasporti:richiesta_detail', pk=pk)

    # Aggiorna stato e data consegna effettiva
    richiesta.stato = 'CONSEGNATO'
    richiesta.data_consegna_effettiva = timezone.now()
    richiesta.save()

    messages.success(request, f'Trasporto {richiesta.numero} marcato come CONSEGNATO. Data consegna registrata: {richiesta.data_consegna_effettiva.strftime("%d/%m/%Y %H:%M")}')

    return redirect('trasporti:richiesta_detail', pk=pk)


# ============================================
# GESTIONE OFFERTE
# ============================================

@login_required
@transaction.atomic
def offerta_create(request, richiesta_pk):
    """Crea nuova offerta"""

    richiesta = get_object_or_404(RichiestaTrasporto, pk=richiesta_pk)

    if request.method == 'POST':
        form = OffertaTrasportoForm(request.POST, request.FILES, richiesta=richiesta, user=request.user)
        if form.is_valid():
            offerta = form.save(commit=False)
            offerta.richiesta = richiesta
            offerta.operatore_inserimento = request.user
            offerta.save()

            # Aggiorna stato TrasportatoreOfferta
            TrasportatoreOfferta.objects.filter(
                richiesta=richiesta,
                trasportatore=offerta.trasportatore
            ).update(ha_risposto=True, data_risposta=timezone.now())

            messages.success(request, 'Offerta inserita con successo')
            return redirect('trasporti:step2_raccolta', pk=richiesta.pk)
    else:
        form = OffertaTrasportoForm(richiesta=richiesta, user=request.user)

    context = {
        'richiesta': richiesta,
        'form': form,
    }
    return render(request, 'trasporti/offerta_create.html', context)


@login_required
def offerta_detail(request, pk):
    """Dettaglio offerta"""
    offerta = get_object_or_404(OffertaTrasporto, pk=pk)

    # Content type per allegati e QR code
    from django.contrib.contenttypes.models import ContentType
    content_type = ContentType.objects.get_for_model(offerta)

    context = {
        'offerta': offerta,
        'object': offerta,  # Per template comune
        'content_type_id': content_type.id,
        'back_url': f'/trasporti/richieste/{offerta.richiesta.pk}/',
    }
    return render(request, 'trasporti/offerta_detail.html', context)


@login_required
def offerta_tracking(request, pk):
    """Tracking offerta/spedizione"""
    offerta = get_object_or_404(OffertaTrasporto, pk=pk)

    eventi = offerta.eventi_tracking.all().order_by('-data_evento')

    context = {
        'offerta': offerta,
        'eventi': eventi,
    }
    return render(request, 'trasporti/offerta_tracking.html', context)


# ============================================
# API ENDPOINTS (AJAX)
# ============================================

@login_required
def offerta_parametri_get(request, pk):
    """AJAX: Get parametri valutazione offerta"""

    try:
        offerta = OffertaTrasporto.objects.get(pk=pk)
        parametri = list(offerta.parametri.values('id', 'descrizione', 'valore', 'ordine'))

        return JsonResponse({'parametri': parametri})
    except OffertaTrasporto.DoesNotExist:
        return JsonResponse({'error': 'Offerta non trovata'}, status=404)


@login_required
def offerta_parametri_save(request, pk):
    """AJAX: Save parametri valutazione offerta"""

    if request.method != 'POST':
        return JsonResponse({'error': 'Metodo non supportato'}, status=405)

    try:
        import json
        offerta = OffertaTrasporto.objects.get(pk=pk)
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


@login_required
def api_calcola_distanza(request):
    """API: Calcola distanza tra due punti (placeholder)"""

    # TODO: Implementare con Google Maps API
    return JsonResponse({
        'distanza_km': 0,
        'durata_minuti': 0,
        'message': 'API non ancora implementata'
    })


def risposta_fornitore_pubblica(request, token):
    """
    View pubblica per la risposta dei fornitori tramite token.
    Non richiede autenticazione.
    """
    from .forms import RispostaFornitoreForm

    # Recupera il TrasportatoreOfferta tramite token
    trasportatore_offerta = get_object_or_404(
        TrasportatoreOfferta,
        token_accesso=token
    )

    richiesta = trasportatore_offerta.richiesta
    trasportatore = trasportatore_offerta.trasportatore

    # Verifica se è già stata inviata un'offerta
    offerta_esistente = OffertaTrasporto.objects.filter(
        richiesta=richiesta,
        trasportatore=trasportatore
    ).first()

    if request.method == 'POST':
        form = RispostaFornitoreForm(request.POST, request.FILES)

        if form.is_valid():
            # Estrai dati dal form
            importo_imponibile = form.cleaned_data['importo_imponibile']
            data_ritiro = form.cleaned_data['data_ritiro_garantita']
            data_consegna = form.cleaned_data['data_consegna_garantita']
            allegato = form.cleaned_data.get('allegato')
            note = form.cleaned_data.get('note', '')

            # Calcola giorni di transito
            tempo_transito = (data_consegna - data_ritiro).days

            # Crea o aggiorna l'offerta
            if offerta_esistente:
                offerta = offerta_esistente
                offerta.importo_trasporto = importo_imponibile
                offerta.importo_totale = importo_imponibile
                offerta.data_ritiro_proposta = data_ritiro
                offerta.data_consegna_prevista = data_consegna
                offerta.tempo_transito_giorni = tempo_transito
                offerta.note_tecniche = note
                if allegato:
                    offerta.file_offerta = allegato
                offerta.save()

                messages.success(request, 'Offerta aggiornata con successo!')
            else:
                offerta = OffertaTrasporto.objects.create(
                    richiesta=richiesta,
                    trasportatore=trasportatore,
                    importo_trasporto=importo_imponibile,
                    importo_totale=importo_imponibile,
                    data_ritiro_proposta=data_ritiro,
                    data_consegna_prevista=data_consegna,
                    tempo_transito_giorni=tempo_transito,
                    note_tecniche=note,
                    file_offerta=allegato if allegato else None
                )

                # Marca come offerta ricevuta
                trasportatore_offerta.offerta_ricevuta = True
                trasportatore_offerta.data_offerta = timezone.now()
                trasportatore_offerta.save()

                # Aggiorna stato richiesta se necessario
                if richiesta.stato == 'RICHIESTA_INVIATA':
                    richiesta.stato = 'OFFERTE_RICEVUTE'
                    richiesta.save()

                messages.success(request, 'Offerta inviata con successo!')

            # Redirect alla stessa pagina per mostrare il messaggio di successo
            return redirect('trasporti:risposta_fornitore_pubblica', token=token)
    else:
        # Pre-compila il form se esiste già un'offerta
        initial_data = {}
        if offerta_esistente:
            initial_data = {
                'importo_imponibile': offerta_esistente.importo_trasporto,
                'data_ritiro_garantita': offerta_esistente.data_ritiro_proposta,
                'data_consegna_garantita': offerta_esistente.data_consegna_prevista,
                'note': offerta_esistente.note_tecniche,
            }

        form = RispostaFornitoreForm(initial=initial_data)

    context = {
        'form': form,
        'richiesta': richiesta,
        'trasportatore': trasportatore,
        'trasportatore_offerta': trasportatore_offerta,
        'offerta_esistente': offerta_esistente,
    }

    return render(request, 'trasporti/risposta_fornitore_pubblica.html', context)
