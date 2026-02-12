"""
CORE PDF GENERATOR - ModularBEF
================================

Sistema universale per generazione PDF.
Supporta ReportLab per PDF professionali con tabelle e stili.
Supporta xhtml2pdf per generazione PDF da HTML.
"""

from io import BytesIO
from typing import List, Dict, Any, Optional
from datetime import datetime, date
from decimal import Decimal
from dataclasses import dataclass, field

from django.http import HttpResponse
from django.utils import timezone

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, letter
    from reportlab.platypus import (
        SimpleDocTemplate,
        Table,
        TableStyle,
        Paragraph,
        Spacer,
    )
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.pdfgen import canvas

    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

try:
    from xhtml2pdf import pisa

    XHTML2PDF_AVAILABLE = True
except ImportError:
    XHTML2PDF_AVAILABLE = False


@dataclass
class PDFConfig:
    """Configurazione per la generazione PDF da HTML."""

    filename: str = "document.pdf"
    page_size: str = "A4"
    orientation: str = "portrait"
    margin_top: str = "1cm"
    margin_bottom: str = "1cm"
    margin_left: str = "1cm"
    margin_right: str = "1cm"


def generate_pdf_from_html(
    html_content: str,
    config: PDFConfig = None,
    output_type: str = "response",
) -> Optional[BytesIO | HttpResponse]:
    """
    Genera un PDF da contenuto HTML usando xhtml2pdf.

    Args:
        html_content: Stringa HTML da convertire in PDF
        config: Configurazione PDFConfig (opzionale)
        output_type: "response" per HttpResponse, "buffer" per BytesIO

    Returns:
        HttpResponse o BytesIO con il PDF, None se errore
    """
    if not XHTML2PDF_AVAILABLE:
        raise ImportError("xhtml2pdf non installato. Run: pip install xhtml2pdf")

    if config is None:
        config = PDFConfig()

    # Crea buffer
    buffer = BytesIO()

    # Genera PDF
    pisa_status = pisa.CreatePDF(html_content, dest=buffer)

    if pisa_status.err:
        return None

    buffer.seek(0)

    if output_type == "buffer":
        return buffer

    # Response
    response = HttpResponse(buffer.getvalue(), content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{config.filename}"'
    return response


def generate_pdf_response(
    data: List[Dict[str, Any]],
    filename: str,
    title: str = "Report",
    headers: List[str] = None,
) -> HttpResponse:
    """
    Genera un file PDF con tabella e lo ritorna come HttpResponse.

    Args:
        data: Lista di dizionari con i dati
        filename: Nome del file (senza estensione)
        title: Titolo del documento
        headers: Lista headers personalizzati (opzionale)

    Returns:
        HttpResponse con il file PDF
    """
    if not REPORTLAB_AVAILABLE:
        raise ImportError("reportlab non installato. Run: pip install reportlab")

    # Crea buffer
    buffer = BytesIO()

    # Crea documento
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    # Elementi del documento
    elements = []

    # Stili
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Heading1"],
        fontSize=18,
        textColor=colors.HexColor("#5585b5"),
        spaceAfter=30,
        alignment=1,  # Center
    )

    # Titolo
    elements.append(Paragraph(title, title_style))
    elements.append(Spacer(1, 12))

    # Info generazione
    info_text = f"Generato il {timezone.now().strftime('%d/%m/%Y alle %H:%M')}"
    info_style = ParagraphStyle(
        "Info",
        parent=styles["Normal"],
        fontSize=9,
        textColor=colors.grey,
        alignment=2,  # Right
    )
    elements.append(Paragraph(info_text, info_style))
    elements.append(Spacer(1, 20))

    if not data:
        elements.append(Paragraph("Nessun dato disponibile", styles["Normal"]))
    else:
        # Headers
        if headers is None:
            headers = list(data[0].keys())

        # Prepara dati tabella
        table_data = [headers]

        for row_data in data:
            row = []
            for header in headers:
                value = row_data.get(header, "")

                # Formatta valore
                if isinstance(value, (datetime, date)):
                    formatted = (
                        value.strftime("%d/%m/%Y %H:%M")
                        if isinstance(value, datetime)
                        else value.strftime("%d/%m/%Y")
                    )
                elif isinstance(value, Decimal):
                    formatted = f"{float(value):.2f}"
                elif value is None:
                    formatted = "-"
                else:
                    formatted = str(value)

                row.append(formatted)

            table_data.append(row)

        # Crea tabella
        table = Table(table_data)

        # Stile tabella
        table_style = TableStyle(
            [
                # Header
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#5585b5")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 12),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                # Dati
                ("BACKGROUND", (0, 1), (-1, -1), colors.white),
                ("TEXTCOLOR", (0, 1), (-1, -1), colors.black),
                ("ALIGN", (0, 1), (-1, -1), "LEFT"),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 1), (-1, -1), 10),
                ("TOPPADDING", (0, 1), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 1), (-1, -1), 6),
                # Bordi
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("BOX", (0, 0), (-1, -1), 2, colors.HexColor("#5585b5")),
                # Alternating row colors
                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [colors.white, colors.HexColor("#f8f9fa")],
                ),
            ]
        )

        table.setStyle(table_style)
        elements.append(table)

    # Build PDF
    doc.build(elements)

    # Ottieni PDF
    pdf = buffer.getvalue()
    buffer.close()

    # Response
    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{filename}.pdf"'

    return response
