"""
Views per il calendario aziendale integrato.

Il calendario utilizza CalendarioRegistry per aggregare eventi
da diverse fonti con controllo permessi automatico.
"""

from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.views import View
from datetime import datetime
from .calendario_registry import CalendarioRegistry


class CalendarioView(LoginRequiredMixin, TemplateView):
    """View principale per il calendario aziendale"""
    template_name = 'core/calendario.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Calendario Aziendale'

        # Passa informazioni sui provider disponibili per l'utente
        context['providers_info'] = CalendarioRegistry.get_providers_info(self.request.user)
        context['categories'] = CalendarioRegistry.get_categories()

        return context


class CalendarioEventiAPIView(LoginRequiredMixin, View):
    """
    API per fornire eventi al calendario in formato JSON.
    Usa CalendarioRegistry per aggregare eventi da tutte le app
    registrate con controllo permessi automatico.
    """

    def get(self, request):
        # Parametri data da FullCalendar
        start_date = request.GET.get('start')
        end_date = request.GET.get('end')

        # Filtra per categoria se richiesto
        categories = request.GET.getlist('categories[]')

        # Parse date se fornite
        try:
            start = datetime.fromisoformat(start_date.replace('Z', '+00:00')) if start_date else None
            end = datetime.fromisoformat(end_date.replace('Z', '+00:00')) if end_date else None
        except (ValueError, AttributeError):
            start = None
            end = None

        # Recupera eventi dal registry con controllo permessi automatico
        eventi = CalendarioRegistry.get_events_for_user(
            user=request.user,
            start_date=start,
            end_date=end,
            categories=categories if categories else None
        )

        return JsonResponse(eventi, safe=False)
