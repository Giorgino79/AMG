"""
ACQUISTI SERVICES - Servizi per gestione ordini di acquisto
===========================================================

Servizi per:
- Creazione automatica ODA da preventivi/trasporti
- Generazione PDF ordine
- Integrazione con email
"""

from io import BytesIO
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from django.core.files.base import ContentFile

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
    Image,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT

import logging

logger = logging.getLogger(__name__)


def crea_ordine_da_preventivo(richiesta, offerta, user):
    """
    Crea un Ordine di Acquisto da un preventivo beni/servizi confermato.

    Args:
        richiesta: RichiestaPreventivo instance
        offerta: Offerta instance (offerta approvata)
        user: User che crea l'ordine

    Returns:
        OrdineAcquisto instance
    """
    from .models import OrdineAcquisto

    # Prepara descrizione dettagliata dalle voci
    descrizione_voci = []
    for voce in richiesta.voci.all().order_by('ordine'):
        descrizione_voci.append(
            f"- {voce.quantita} {voce.get_unita_misura_display()} - {voce.descrizione}"
        )

    ordine = OrdineAcquisto.objects.create(
        tipo_origine='PREVENTIVO',
        content_type=ContentType.objects.get_for_model(richiesta),
        object_id=str(richiesta.pk),
        richiesta_preventivo=richiesta,
        fornitore=offerta.fornitore,
        importo_totale=offerta.importo_totale,
        valuta=offerta.valuta,
        termini_pagamento=offerta.get_termini_pagamento_display() if offerta.termini_pagamento else '',
        tempi_consegna=f"{offerta.tempo_consegna_giorni} giorni" if offerta.tempo_consegna_giorni else '',
        data_consegna_richiesta=offerta.data_consegna_proposta or richiesta.data_consegna_richiesta or timezone.now().date(),
        oggetto_ordine=richiesta.titolo,
        descrizione_dettagliata="\n".join(descrizione_voci),
        riferimento_fornitore=offerta.numero_offerta or '',
        creato_da=user,
    )

    # Aggiorna l'offerta con il numero ordine
    offerta.numero_ordine = ordine.numero_ordine
    offerta.save(update_fields=['numero_ordine'])

    logger.info(f"Creato ODA {ordine.numero_ordine} da preventivo {richiesta.numero}")

    return ordine


def crea_ordine_da_trasporto(richiesta, offerta, user):
    """
    Crea un Ordine di Acquisto da un trasporto confermato.

    Args:
        richiesta: RichiestaTrasporto instance
        offerta: OffertaTrasporto instance (offerta approvata)
        user: User che crea l'ordine

    Returns:
        OrdineAcquisto instance
    """
    from .models import OrdineAcquisto

    # Prepara descrizione
    descrizione = f"""Trasporto: {richiesta.percorso_completo}
Tipo: {richiesta.get_tipo_trasporto_display()}
Colli: {richiesta.numero_colli_totali}
Peso totale: {richiesta.peso_totale_kg} kg
Data ritiro: {offerta.data_ritiro_proposta.strftime('%d/%m/%Y')}
Data consegna: {offerta.data_consegna_prevista.strftime('%d/%m/%Y')}"""

    ordine = OrdineAcquisto.objects.create(
        tipo_origine='TRASPORTO',
        content_type=ContentType.objects.get_for_model(richiesta),
        object_id=str(richiesta.pk),
        richiesta_trasporto=richiesta,
        fornitore=offerta.trasportatore,
        importo_totale=offerta.importo_totale,
        valuta=offerta.valuta,
        termini_pagamento=offerta.termini_pagamento or '',
        tempi_consegna=f"{offerta.tempo_transito_giorni} giorni transito",
        data_consegna_richiesta=offerta.data_consegna_prevista,
        oggetto_ordine=f"Trasporto {richiesta.titolo}",
        descrizione_dettagliata=descrizione,
        riferimento_fornitore=offerta.numero_offerta or '',
        creato_da=user,
    )

    # Aggiorna l'offerta con il numero ordine
    offerta.numero_ordine = ordine.numero_ordine
    offerta.save(update_fields=['numero_ordine'])

    logger.info(f"Creato ODA {ordine.numero_ordine} da trasporto {richiesta.numero}")

    return ordine


def genera_pdf_ordine(ordine):
    """
    Genera il PDF dell'ordine di acquisto.

    Args:
        ordine: OrdineAcquisto instance

    Returns:
        BytesIO buffer con il PDF
    """
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm,
    )

    elements = []
    styles = getSampleStyleSheet()

    # Stili personalizzati
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=colors.HexColor('#5585b5'),
        spaceAfter=20,
        alignment=TA_CENTER,
    )

    header_style = ParagraphStyle(
        'Header',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#333333'),
        spaceBefore=15,
        spaceAfter=10,
    )

    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
    )

    bold_style = ParagraphStyle(
        'Bold',
        parent=styles['Normal'],
        fontSize=10,
        fontName='Helvetica-Bold',
    )

    # INTESTAZIONE
    elements.append(Paragraph("ORDINE DI ACQUISTO", title_style))
    elements.append(Spacer(1, 10))

    # Info ordine box
    info_data = [
        ['Numero Ordine:', ordine.numero_ordine, 'Data:', ordine.data_ordine.strftime('%d/%m/%Y')],
        ['Origine:', ordine.origine_display, 'Stato:', ordine.get_stato_display()],
    ]

    info_table = Table(info_data, colWidths=[3*cm, 5*cm, 2*cm, 5*cm])
    info_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8f9fa')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#5585b5')),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 20))

    # FORNITORE
    elements.append(Paragraph("FORNITORE", header_style))

    fornitore = ordine.fornitore
    fornitore_info = f"""
    <b>{fornitore.ragione_sociale}</b><br/>
    {fornitore.indirizzo or ''}<br/>
    {fornitore.cap or ''} {fornitore.citta or ''}<br/>
    P.IVA: {fornitore.partita_iva or 'N/D'}<br/>
    Email: {fornitore.email or 'N/D'}<br/>
    Tel: {fornitore.telefono or 'N/D'}
    """
    elements.append(Paragraph(fornitore_info, normal_style))
    elements.append(Spacer(1, 15))

    # OGGETTO ORDINE
    elements.append(Paragraph("OGGETTO ORDINE", header_style))
    elements.append(Paragraph(ordine.oggetto_ordine or 'N/D', normal_style))
    elements.append(Spacer(1, 10))

    # DESCRIZIONE DETTAGLIATA
    if ordine.descrizione_dettagliata:
        elements.append(Paragraph("DETTAGLIO", header_style))
        # Sostituisci newline con <br/>
        desc_html = ordine.descrizione_dettagliata.replace('\n', '<br/>')
        elements.append(Paragraph(desc_html, normal_style))
        elements.append(Spacer(1, 15))

    # CONDIZIONI COMMERCIALI
    elements.append(Paragraph("CONDIZIONI COMMERCIALI", header_style))

    condizioni_data = [
        ['Importo Totale:', f"€ {ordine.importo_totale:,.2f}"],
        ['Termini Pagamento:', ordine.termini_pagamento or 'Da concordare'],
        ['Tempi Consegna:', ordine.tempi_consegna or 'Da concordare'],
        ['Data Consegna Richiesta:', ordine.data_consegna_richiesta.strftime('%d/%m/%Y') if ordine.data_consegna_richiesta else 'N/D'],
    ]

    if ordine.riferimento_fornitore:
        condizioni_data.append(['Rif. Fornitore:', ordine.riferimento_fornitore])

    cond_table = Table(condizioni_data, colWidths=[5*cm, 10*cm])
    cond_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('LINEBELOW', (0, 0), (-1, -2), 0.5, colors.lightgrey),
        ('LINEBELOW', (0, -1), (-1, -1), 1, colors.HexColor('#5585b5')),
    ]))
    elements.append(cond_table)
    elements.append(Spacer(1, 20))

    # NOTE
    if ordine.note_ordine:
        elements.append(Paragraph("NOTE", header_style))
        elements.append(Paragraph(ordine.note_ordine.replace('\n', '<br/>'), normal_style))
        elements.append(Spacer(1, 15))

    # FOOTER
    elements.append(Spacer(1, 30))
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.grey,
        alignment=TA_CENTER,
    )
    elements.append(Paragraph(
        f"Documento generato automaticamente il {timezone.now().strftime('%d/%m/%Y alle %H:%M')}",
        footer_style
    ))
    elements.append(Paragraph(
        f"Creato da: {ordine.creato_da.get_full_name() or ordine.creato_da.username}",
        footer_style
    ))

    # Build PDF
    doc.build(elements)
    buffer.seek(0)

    return buffer


def genera_pdf_ordine_come_file(ordine):
    """
    Genera il PDF e lo restituisce come ContentFile Django.

    Args:
        ordine: OrdineAcquisto instance

    Returns:
        tuple: (ContentFile, filename)
    """
    buffer = genera_pdf_ordine(ordine)
    filename = f"ODA_{ordine.numero_ordine.replace('-', '_')}.pdf"

    return ContentFile(buffer.read(), name=filename), filename
