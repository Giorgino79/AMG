"""
ACQUISTI VIEWS - Sistema gestione ordini di acquisto
===================================================

Views per:
- Dashboard con ordini da ricevere e ricevuti
- Creazione manuale ordini
- Gestione stati ordini
- Ricerca e filtri
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count, Sum
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
import logging

from .models import OrdineAcquisto
from .forms import RicercaOrdiniForm, CreaOrdineForm, CambiaStatoOrdineForm, OrdineDettaglioForm, ReportOrdiniForm
from .services import genera_pdf_ordine
from decimal import Decimal

logger = logging.getLogger(__name__)


@login_required
def dashboard(request):
    """
    Dashboard principale ordini di acquisto
    """

    # Form di ricerca
    form_ricerca = RicercaOrdiniForm(request.GET or None)

    # Ordini da ricevere (stato CREATO)
    ordini_da_ricevere = OrdineAcquisto.objects.filter(
        stato='CREATO'
    ).select_related('fornitore', 'creato_da').order_by('-data_ordine')

    # Ordini ricevuti/pagati
    ordini_completati_base = OrdineAcquisto.objects.filter(
        stato__in=['RICEVUTO', 'PAGATO']
    ).select_related('fornitore', 'ricevuto_da')

    # Applica filtri di ricerca
    if form_ricerca.is_valid():
        ordini_completati_base = form_ricerca.filter_queryset(ordini_completati_base)

    # Paginazione
    paginator = Paginator(ordini_completati_base.order_by('-data_ricevimento', '-data_ordine'), 10)
    page_number = request.GET.get('page', 1)
    ordini_completati = paginator.get_page(page_number)

    # Statistiche
    stats = {
        'totale_da_ricevere': ordini_da_ricevere.count(),
        'totale_ricevuti_oggi': OrdineAcquisto.objects.filter(
            stato__in=['RICEVUTO', 'PAGATO'],
            data_ricevimento__date=timezone.now().date()
        ).count(),
        'totale_ordini_mese': OrdineAcquisto.objects.filter(
            data_ordine__gte=timezone.now().replace(day=1)
        ).count(),
        'importo_mese': OrdineAcquisto.objects.filter(
            data_ordine__gte=timezone.now().replace(day=1)
        ).aggregate(Sum('importo_totale'))['importo_totale__sum'] or 0,
    }

    context = {
        'ordini_da_ricevere': ordini_da_ricevere,
        'ordini_completati': ordini_completati,
        'form_ricerca': form_ricerca,
        'stats': stats,
    }

    return render(request, 'acquisti/dashboard.html', context)


@login_required
def crea_ordine(request):
    """
    Creazione manuale ordine di acquisto
    """
    if request.method == 'POST':
        form = CreaOrdineForm(request.POST, user=request.user)
        if form.is_valid():
            ordine = form.save()
            messages.success(
                request,
                f"Ordine {ordine.numero_ordine} creato con successo!"
            )
            return redirect('acquisti:dettaglio_ordine', pk=ordine.pk)
    else:
        form = CreaOrdineForm(user=request.user)

    context = {
        'form': form,
        'page_title': 'Crea Nuovo Ordine di Acquisto'
    }

    return render(request, 'acquisti/crea_ordine.html', context)


@login_required
def dettaglio_ordine(request, pk):
    """
    Dettaglio ordine con possibilità di modifica stato
    """
    ordine = get_object_or_404(
        OrdineAcquisto.objects.select_related(
            'fornitore', 'creato_da', 'ricevuto_da', 'pagato_da',
            'richiesta_preventivo', 'richiesta_trasporto'
        ),
        pk=pk
    )

    # Form per cambio stato
    form_stato = CambiaStatoOrdineForm(ordine, request.POST or None)
    form_dettaglio = OrdineDettaglioForm(request.POST or None, instance=ordine)

    if request.method == 'POST':
        # Gestione cambio stato
        if 'cambia_stato' in request.POST and form_stato.is_valid():
            azione = form_stato.cleaned_data['azione']
            note = form_stato.cleaned_data.get('note', '')

            if azione == 'segna_ricevuto' and ordine.puo_essere_ricevuto():
                ordine.segna_come_ricevuto(request.user)
                messages.success(request, f"Ordine {ordine.numero_ordine} segnato come RICEVUTO")

            elif azione == 'segna_pagato' and ordine.puo_essere_pagato():
                ordine.segna_come_pagato(request.user)
                messages.success(request, f"Ordine {ordine.numero_ordine} segnato come PAGATO")

            # Salva note se presenti
            if note:
                ordine.note_ordine = f"{ordine.note_ordine}\n\n[{timezone.now().strftime('%d/%m/%Y %H:%M')}] {note}".strip()
                ordine.save()

            return redirect('acquisti:dettaglio_ordine', pk=ordine.pk)

        # Gestione modifica dettagli
        elif 'aggiorna_dettagli' in request.POST and form_dettaglio.is_valid():
            form_dettaglio.save()
            messages.success(request, "Dettagli ordine aggiornati con successo")
            return redirect('acquisti:dettaglio_ordine', pk=ordine.pk)

    # Content type per allegati e QR code
    from django.contrib.contenttypes.models import ContentType
    content_type = ContentType.objects.get_for_model(ordine)

    context = {
        'ordine': ordine,
        'object': ordine,  # Per template comune
        'form_stato': form_stato,
        'form_dettaglio': form_dettaglio,
        'content_type_id': content_type.id,
        'back_url': '/acquisti/',
    }

    return render(request, 'acquisti/dettaglio_ordine.html', context)


@login_required
def segna_ricevuto_ajax(request, pk):
    """
    AJAX endpoint per segnare ordine come ricevuto
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Metodo non supportato'}, status=405)

    ordine = get_object_or_404(OrdineAcquisto, pk=pk)

    if not ordine.puo_essere_ricevuto():
        return JsonResponse({
            'error': 'Ordine non può essere segnato come ricevuto'
        }, status=400)

    try:
        ordine.segna_come_ricevuto(request.user)

        return JsonResponse({
            'success': True,
            'message': f'Ordine {ordine.numero_ordine} segnato come RICEVUTO',
            'nuovo_stato': ordine.stato,
            'nuovo_stato_display': ordine.get_stato_display(),
            'css_class': ordine.get_stato_css_class(),
        })

    except Exception as e:
        return JsonResponse({
            'error': f'Errore durante l\'operazione: {str(e)}'
        }, status=500)


@login_required
def scarica_pdf(request, pk):
    """
    Scarica PDF dell'ordine di acquisto
    """
    ordine = get_object_or_404(OrdineAcquisto, pk=pk)

    pdf_buffer = genera_pdf_ordine(ordine)
    filename = f"ODA_{ordine.numero_ordine.replace('-', '_')}.pdf"

    response = HttpResponse(pdf_buffer.read(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    return response


# ============================================
# REPORT ORDINI IN ATTESA FATTURA
# ============================================

@login_required
def report_ordini(request):
    """
    Report ordini in attesa fattura con filtri e export.
    Mostra ordini filtrabili per periodo, fornitore, stato e tipo origine.
    Permette export in PDF e Excel.
    """
    form = ReportOrdiniForm(request.GET or None)

    # Query base - ordini con select_related per performance
    ordini = OrdineAcquisto.objects.select_related(
        'fornitore', 'creato_da', 'ricevuto_da'
    ).order_by('-data_ordine')

    # Applica filtri
    if form.is_valid():
        ordini = form.filter_queryset(ordini)
    else:
        # Default: mostra solo ordini RICEVUTI (in attesa fattura)
        ordini = ordini.filter(stato='RICEVUTO')

    # Calcola totali
    totali = ordini.aggregate(
        totale_imponibile=Sum('imponibile'),
        totale_iva=Sum('importo_iva'),
        totale_importo=Sum('importo_totale'),
    )

    # Valori di default se None
    totali = {
        'totale_imponibile': totali['totale_imponibile'] or Decimal('0.00'),
        'totale_iva': totali['totale_iva'] or Decimal('0.00'),
        'totale_importo': totali['totale_importo'] or Decimal('0.00'),
    }

    # Gestione export
    export_format = request.GET.get('export')
    if export_format:
        return esporta_report_ordini(request, ordini, totali, export_format)

    # Paginazione
    paginator = Paginator(ordini, 25)
    page_number = request.GET.get('page', 1)
    ordini_page = paginator.get_page(page_number)

    context = {
        'form': form,
        'ordini': ordini_page,
        'totali': totali,
        'count': ordini.count(),
    }

    return render(request, 'acquisti/report_ordini.html', context)


def esporta_report_ordini(request, ordini, totali, formato):
    """
    Esporta il report ordini in PDF o Excel.
    """
    from core.views import genera_excel_da_queryset, genera_pdf_da_template

    timestamp = timezone.now().strftime('%Y%m%d_%H%M')

    if formato == 'excel':
        # Definisci colonne per Excel
        columns = [
            ('numero_ordine', 'N° Ordine'),
            ('fornitore__ragione_sociale', 'Fornitore'),
            ('data_ordine', 'Data Ordine'),
            ('data_ricevimento', 'Data Ricevimento'),
            ('get_tipo_origine_display', 'Tipo'),
            ('imponibile', 'Imponibile €'),
            ('importo_iva', 'IVA €'),
            ('importo_totale', 'Totale €'),
            ('get_stato_display', 'Stato'),
        ]
        return genera_excel_da_queryset(
            ordini,
            columns,
            f'report_ordini_{timestamp}.xlsx',
            sheet_name='Ordini Attesa Fattura'
        )

    elif formato == 'pdf':
        context = {
            'ordini': ordini,
            'totali': totali,
            'count': ordini.count(),
            'data_report': timezone.now(),
            'filtri_applicati': _get_filtri_applicati(request),
        }
        return genera_pdf_da_template(
            'acquisti/report_ordini_pdf.html',
            context,
            f'report_ordini_{timestamp}.pdf'
        )

    return HttpResponse("Formato non supportato", status=400)


def _get_filtri_applicati(request):
    """
    Estrae i filtri applicati dalla request per mostrarli nel PDF.
    """
    filtri = []

    if request.GET.get('data_da'):
        filtri.append(f"Da: {request.GET.get('data_da')}")
    if request.GET.get('data_a'):
        filtri.append(f"A: {request.GET.get('data_a')}")
    if request.GET.get('fornitore'):
        from anagrafica.models import Fornitore
        try:
            fornitore = Fornitore.objects.get(pk=request.GET.get('fornitore'))
            filtri.append(f"Fornitore: {fornitore.ragione_sociale}")
        except Fornitore.DoesNotExist:
            pass
    if request.GET.get('stato'):
        stati_display = dict(OrdineAcquisto.STATI_CHOICES)
        filtri.append(f"Stato: {stati_display.get(request.GET.get('stato'), request.GET.get('stato'))}")
    if request.GET.get('tipo_origine'):
        tipi_display = dict(OrdineAcquisto.TIPO_ORIGINE_CHOICES)
        filtri.append(f"Tipo: {tipi_display.get(request.GET.get('tipo_origine'), request.GET.get('tipo_origine'))}")

    return filtri if filtri else ['Nessun filtro applicato']
