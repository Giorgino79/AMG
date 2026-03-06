"""
Event providers per il calendario aziendale - App Automezzi.

Ogni funzione provider genera eventi per il calendario
con controllo permessi integrato.
"""

from django.db.models import Q
from datetime import datetime


def get_eventi_automezzi(user, start_date, end_date):
    """Provider per eventi automezzi (incidenti, guasti, ecc.)"""
    if not user.has_perm('automezzi.view_eventoautomezzo'):
        return []

    from .models import EventoAutomezzo

    eventi_qs = EventoAutomezzo.objects.select_related('automezzo', 'responsabile')

    # Filtra per date se fornite
    if start_date and end_date:
        eventi_qs = eventi_qs.filter(
            data_evento__gte=start_date.date(),
            data_evento__lte=end_date.date()
        )

    # Limita per performance
    eventi_qs = eventi_qs[:100]

    events = []
    for evento in eventi_qs:
        # Colore in base al tipo
        if evento.tipo == 'incidente':
            color = '#dc3545'  # Rosso
        elif evento.tipo == 'guasto':
            color = '#ffc107'  # Giallo
        else:
            color = '#6c757d'  # Grigio

        events.append({
            'id': f'evento-auto-{evento.id}',
            'title': f'{evento.get_tipo_display()}: {evento.automezzo}',
            'start': evento.data_evento.isoformat(),
            'color': color,
            'url': f'/automezzi/eventi/{evento.id}/',
            'extendedProps': {
                'tipo': 'evento_automezzo',
                'tipo_evento': evento.tipo,
                'descrizione': evento.descrizione[:100] if evento.descrizione else '',
                'responsabile': evento.responsabile.get_full_name() if evento.responsabile else '',
            }
        })

    return events


def get_manutenzioni(user, start_date, end_date):
    """Provider per manutenzioni programmate"""
    if not user.has_perm('automezzi.view_manutenzione'):
        return []

    from .models import Manutenzione

    manutenzioni_qs = Manutenzione.objects.select_related('automezzo', 'responsabile')

    # Filtra per date se fornite
    if start_date and end_date:
        manutenzioni_qs = manutenzioni_qs.filter(
            Q(data_inizio__gte=start_date.date(), data_inizio__lte=end_date.date()) |
            Q(data_fine_prevista__gte=start_date.date(), data_fine_prevista__lte=end_date.date()) |
            Q(data_fine_effettiva__gte=start_date.date(), data_fine_effettiva__lte=end_date.date())
        )

    manutenzioni_qs = manutenzioni_qs[:100]

    events = []
    for manutenzione in manutenzioni_qs:
        # Colore in base allo stato
        if manutenzione.stato == 'completato':
            color = '#28a745'  # Verde
        elif manutenzione.stato == 'in_corso':
            color = '#007bff'  # Blu
        else:
            color = '#6c757d'  # Grigio

        # Usa data fine effettiva se disponibile, altrimenti prevista
        data_fine = manutenzione.data_fine_effettiva or manutenzione.data_fine_prevista

        title = f'Manutenzione: {manutenzione.automezzo}'
        if manutenzione.tipo:
            title = f'{manutenzione.get_tipo_display()}: {manutenzione.automezzo}'

        events.append({
            'id': f'manutenzione-{manutenzione.id}',
            'title': title,
            'start': manutenzione.data_inizio.isoformat(),
            'end': data_fine.isoformat() if data_fine else None,
            'color': color,
            'url': f'/automezzi/manutenzioni/{manutenzione.id}/',
            'extendedProps': {
                'tipo': 'manutenzione',
                'stato': manutenzione.get_stato_display(),
                'descrizione': manutenzione.descrizione[:100] if manutenzione.descrizione else '',
                'responsabile': manutenzione.responsabile.get_full_name() if manutenzione.responsabile else '',
            }
        })

    return events


def get_affidamenti(user, start_date, end_date):
    """Provider per affidamenti mezzi"""
    if not user.has_perm('automezzi.view_affidamentomezzo'):
        return []

    from .models import AffidamentoMezzo

    affidamenti_qs = AffidamentoMezzo.objects.select_related('automezzo', 'utente')

    # Filtra per date se fornite
    if start_date and end_date:
        affidamenti_qs = affidamenti_qs.filter(
            Q(data_inizio__gte=start_date.date(), data_inizio__lte=end_date.date()) |
            Q(data_fine_prevista__gte=start_date.date(), data_fine_prevista__lte=end_date.date()) |
            Q(data_rientro_effettivo__gte=start_date.date(), data_rientro_effettivo__lte=end_date.date())
        )

    affidamenti_qs = affidamenti_qs[:100]

    events = []
    for affidamento in affidamenti_qs:
        # Colore in base allo stato
        if affidamento.stato == 'attivo':
            color = '#17a2b8'  # Ciano
        elif affidamento.stato == 'completato':
            color = '#28a745'  # Verde
        else:
            color = '#ffc107'  # Giallo

        # Usa data rientro effettivo se disponibile, altrimenti prevista
        data_fine = affidamento.data_rientro_effettivo or affidamento.data_fine_prevista

        events.append({
            'id': f'affidamento-{affidamento.id}',
            'title': f'Affidamento: {affidamento.automezzo} - {affidamento.utente.get_full_name()}',
            'start': affidamento.data_inizio.isoformat(),
            'end': data_fine.isoformat() if data_fine else None,
            'color': color,
            'url': f'/automezzi/affidamenti/{affidamento.id}/',
            'extendedProps': {
                'tipo': 'affidamento',
                'stato': affidamento.get_stato_display(),
                'utente': affidamento.utente.get_full_name(),
                'note': affidamento.note[:100] if affidamento.note else '',
            }
        })

    return events


def get_scadenze_revisioni(user, start_date, end_date):
    """Provider per scadenze revisioni automezzi"""
    if not user.has_perm('automezzi.view_automezzo'):
        return []

    from .models import Automezzo

    # Filtra automezzi con revisione programmata
    automezzi_qs = Automezzo.objects.filter(
        data_prossima_revisione__isnull=False
    )

    # Filtra per date se fornite
    if start_date and end_date:
        automezzi_qs = automezzi_qs.filter(
            data_prossima_revisione__gte=start_date.date(),
            data_prossima_revisione__lte=end_date.date()
        )

    automezzi_qs = automezzi_qs[:50]

    events = []
    for automezzo in automezzi_qs:
        # Calcola giorni mancanti
        giorni_mancanti = (automezzo.data_prossima_revisione - datetime.now().date()).days

        # Colore in base all'urgenza
        if giorni_mancanti < 0:
            color = '#dc3545'  # Rosso - scaduta
            title = f'⚠️ REVISIONE SCADUTA: {automezzo}'
        elif giorni_mancanti < 30:
            color = '#ffc107'  # Giallo - urgente
            title = f'⚠️ Revisione urgente: {automezzo} ({giorni_mancanti}gg)'
        else:
            color = '#17a2b8'  # Ciano
            title = f'Revisione: {automezzo}'

        events.append({
            'id': f'revisione-{automezzo.id}',
            'title': title,
            'start': automezzo.data_prossima_revisione.isoformat(),
            'color': color,
            'url': f'/automezzi/{automezzo.id}/',
            'extendedProps': {
                'tipo': 'revisione',
                'giorni_mancanti': giorni_mancanti,
                'targa': automezzo.targa,
            }
        })

    return events


def get_scadenze_assicurazioni(user, start_date, end_date):
    """Provider per scadenze assicurazioni automezzi"""
    if not user.has_perm('automezzi.view_automezzo'):
        return []

    from .models import Automezzo

    # Filtra automezzi con assicurazione in scadenza
    automezzi_qs = Automezzo.objects.filter(
        scadenza_assicurazione__isnull=False
    )

    # Filtra per date se fornite
    if start_date and end_date:
        automezzi_qs = automezzi_qs.filter(
            scadenza_assicurazione__gte=start_date.date(),
            scadenza_assicurazione__lte=end_date.date()
        )

    automezzi_qs = automezzi_qs[:50]

    events = []
    for automezzo in automezzi_qs:
        # Calcola giorni mancanti
        giorni_mancanti = (automezzo.scadenza_assicurazione - datetime.now().date()).days

        # Colore in base all'urgenza
        if giorni_mancanti < 0:
            color = '#dc3545'  # Rosso - scaduta
            title = f'⚠️ ASSICURAZIONE SCADUTA: {automezzo}'
        elif giorni_mancanti < 30:
            color = '#ffc107'  # Giallo - urgente
            title = f'⚠️ Assicurazione urgente: {automezzo} ({giorni_mancanti}gg)'
        else:
            color = '#28a745'  # Verde
            title = f'Assicurazione: {automezzo}'

        events.append({
            'id': f'assicurazione-{automezzo.id}',
            'title': title,
            'start': automezzo.scadenza_assicurazione.isoformat(),
            'color': color,
            'url': f'/automezzi/{automezzo.id}/',
            'extendedProps': {
                'tipo': 'assicurazione',
                'giorni_mancanti': giorni_mancanti,
                'targa': automezzo.targa,
            }
        })

    return events
