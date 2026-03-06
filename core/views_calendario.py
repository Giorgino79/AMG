"""
Views per il calendario aziendale integrato.

Il calendario mostra eventi da diverse fonti:
- Eventi automezzi (incidenti, guasti)
- Manutenzioni programmate
- Affidamenti mezzi
- Scadenze e revisioni
"""

from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.views import View
from django.db.models import Q
from datetime import datetime, timedelta


class CalendarioView(LoginRequiredMixin, TemplateView):
    """View principale per il calendario aziendale"""
    template_name = 'core/calendario.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Calendario Aziendale'
        return context


class CalendarioEventiAPIView(LoginRequiredMixin, View):
    """
    API per fornire eventi al calendario in formato JSON.
    Supporta il formato richiesto da FullCalendar.
    """

    def get(self, request):
        # Parametri data da FullCalendar
        start_date = request.GET.get('start')
        end_date = request.GET.get('end')

        eventi = []

        # Parse date se fornite
        try:
            start = datetime.fromisoformat(start_date.replace('Z', '+00:00')) if start_date else None
            end = datetime.fromisoformat(end_date.replace('Z', '+00:00')) if end_date else None
        except (ValueError, AttributeError):
            start = None
            end = None

        # ===== EVENTI AUTOMEZZI =====
        try:
            from automezzi.models import EventoAutomezzo

            eventi_auto = EventoAutomezzo.objects.select_related('automezzo', 'responsabile')

            if start and end:
                eventi_auto = eventi_auto.filter(
                    data_evento__gte=start.date(),
                    data_evento__lte=end.date()
                )

            for evento in eventi_auto[:100]:  # Limit per performance
                color = '#dc3545' if evento.tipo == 'incidente' else '#ffc107' if evento.tipo == 'guasto' else '#6c757d'

                eventi.append({
                    'id': f'evento-auto-{evento.id}',
                    'title': f'{evento.get_tipo_display()}: {evento.automezzo}',
                    'start': evento.data_evento.isoformat(),
                    'color': color,
                    'url': f'/automezzi/eventi/{evento.id}/',
                    'extendedProps': {
                        'tipo': 'evento_automezzo',
                        'descrizione': evento.descrizione[:100] if evento.descrizione else '',
                    }
                })
        except ImportError:
            pass

        # ===== MANUTENZIONI =====
        try:
            from automezzi.models import Manutenzione

            manutenzioni = Manutenzione.objects.select_related('automezzo', 'responsabile')

            if start and end:
                manutenzioni = manutenzioni.filter(
                    Q(data_inizio__gte=start.date(), data_inizio__lte=end.date()) |
                    Q(data_fine_prevista__gte=start.date(), data_fine_prevista__lte=end.date()) |
                    Q(data_fine_effettiva__gte=start.date(), data_fine_effettiva__lte=end.date())
                )

            for manutenzione in manutenzioni[:100]:
                color = '#28a745' if manutenzione.stato == 'completato' else '#007bff' if manutenzione.stato == 'in_corso' else '#6c757d'

                # Usa data fine effettiva se disponibile, altrimenti prevista
                data_fine = manutenzione.data_fine_effettiva or manutenzione.data_fine_prevista

                eventi.append({
                    'id': f'manutenzione-{manutenzione.id}',
                    'title': f'Manutenzione: {manutenzione.automezzo}',
                    'start': manutenzione.data_inizio.isoformat(),
                    'end': data_fine.isoformat() if data_fine else None,
                    'color': color,
                    'url': f'/automezzi/manutenzioni/{manutenzione.id}/',
                    'extendedProps': {
                        'tipo': 'manutenzione',
                        'stato': manutenzione.get_stato_display(),
                        'descrizione': manutenzione.descrizione[:100] if manutenzione.descrizione else '',
                    }
                })
        except ImportError:
            pass

        # ===== AFFIDAMENTI MEZZI =====
        try:
            from automezzi.models import AffidamentoMezzo

            affidamenti = AffidamentoMezzo.objects.select_related('automezzo', 'utente')

            if start and end:
                affidamenti = affidamenti.filter(
                    Q(data_inizio__gte=start.date(), data_inizio__lte=end.date()) |
                    Q(data_fine_prevista__gte=start.date(), data_fine_prevista__lte=end.date()) |
                    Q(data_rientro_effettivo__gte=start.date(), data_rientro_effettivo__lte=end.date())
                )

            for affidamento in affidamenti[:100]:
                color = '#17a2b8' if affidamento.stato == 'attivo' else '#28a745' if affidamento.stato == 'completato' else '#ffc107'

                # Usa data rientro effettivo se disponibile, altrimenti prevista
                data_fine = affidamento.data_rientro_effettivo or affidamento.data_fine_prevista

                eventi.append({
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
                    }
                })
        except ImportError:
            pass

        # ===== SCADENZE REVISIONI =====
        try:
            from automezzi.models import Automezzo

            # Solo automezzi con revisione nei prossimi 90 giorni
            if start and end:
                automezzi = Automezzo.objects.filter(
                    data_prossima_revisione__gte=start.date(),
                    data_prossima_revisione__lte=end.date()
                )
            else:
                automezzi = Automezzo.objects.filter(
                    data_prossima_revisione__isnull=False
                )

            for automezzo in automezzi[:50]:
                # Colore rosso se mancano meno di 30 giorni
                giorni_mancanti = (automezzo.data_prossima_revisione - datetime.now().date()).days
                color = '#dc3545' if giorni_mancanti < 30 else '#ffc107'

                eventi.append({
                    'id': f'revisione-{automezzo.id}',
                    'title': f'Revisione: {automezzo}',
                    'start': automezzo.data_prossima_revisione.isoformat(),
                    'color': color,
                    'url': f'/automezzi/{automezzo.id}/',
                    'extendedProps': {
                        'tipo': 'revisione',
                        'giorni_mancanti': giorni_mancanti,
                    }
                })
        except ImportError:
            pass

        return JsonResponse(eventi, safe=False)
