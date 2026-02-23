from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from datetime import datetime, date, timedelta
from calendar import monthrange, monthcalendar
from collections import defaultdict
import calendar

from progetti_eventi.models import Progetto
from automezzi.models import Automezzo


@method_decorator(login_required, name='dispatch')
class DashboardLogisticaView(TemplateView):
    """Dashboard principale logistica"""
    template_name = 'logistica/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        oggi = date.today()

        # Prossime consegne (7 giorni)
        prossime_consegne = Progetto.objects.filter(
            data_consegna_richiesta__gte=oggi,
            data_consegna_richiesta__lte=oggi + timedelta(days=7),
            deleted_at__isnull=True
        ).order_by('data_consegna_richiesta')[:10]

        # Prossimi ritiri (7 giorni)
        prossimi_ritiri = Progetto.objects.filter(
            data_ritiro_richiesta__gte=oggi,
            data_ritiro_richiesta__lte=oggi + timedelta(days=7),
            deleted_at__isnull=True
        ).order_by('data_ritiro_richiesta')[:10]

        # Statistiche
        consegne_oggi = Progetto.objects.filter(
            data_consegna_richiesta=oggi,
            deleted_at__isnull=True
        ).count()

        ritiri_oggi = Progetto.objects.filter(
            data_ritiro_richiesta=oggi,
            deleted_at__isnull=True
        ).count()

        context.update({
            'prossime_consegne': prossime_consegne,
            'prossimi_ritiri': prossimi_ritiri,
            'consegne_oggi': consegne_oggi,
            'ritiri_oggi': ritiri_oggi,
        })

        return context


@method_decorator(login_required, name='dispatch')
class CalendarioMeseView(TemplateView):
    """Vista calendario mensile con consegne e ritiri"""
    template_name = 'logistica/calendario_mese.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Ottieni anno e mese da URL o usa oggi
        anno = int(self.kwargs.get('anno', datetime.now().year))
        mese = int(self.kwargs.get('mese', datetime.now().month))

        # Calcola mese precedente e successivo
        if mese == 1:
            mese_prec, anno_prec = 12, anno - 1
        else:
            mese_prec, anno_prec = mese - 1, anno

        if mese == 12:
            mese_succ, anno_succ = 1, anno + 1
        else:
            mese_succ, anno_succ = mese + 1, anno

        # Ottieni tutte le consegne e ritiri del mese
        primo_giorno = date(anno, mese, 1)
        ultimo_giorno = date(anno, mese, monthrange(anno, mese)[1])

        consegne = Progetto.objects.filter(
            data_consegna_richiesta__gte=primo_giorno,
            data_consegna_richiesta__lte=ultimo_giorno,
            deleted_at__isnull=True
        ).select_related('cliente', 'commerciale')

        ritiri = Progetto.objects.filter(
            data_ritiro_richiesta__gte=primo_giorno,
            data_ritiro_richiesta__lte=ultimo_giorno,
            deleted_at__isnull=True
        ).select_related('cliente', 'commerciale')

        # Organizza per giorno
        consegne_per_giorno = {}
        for consegna in consegne:
            giorno = consegna.data_consegna_richiesta.day
            if giorno not in consegne_per_giorno:
                consegne_per_giorno[giorno] = []
            consegne_per_giorno[giorno].append(consegna)

        ritiri_per_giorno = {}
        for ritiro in ritiri:
            giorno = ritiro.data_ritiro_richiesta.day
            if giorno not in ritiri_per_giorno:
                ritiri_per_giorno[giorno] = []
            ritiri_per_giorno[giorno].append(ritiro)

        # Crea struttura calendario
        cal = monthcalendar(anno, mese)
        nome_mese = calendar.month_name[mese]

        # Costruisci settimane con dati
        settimane = []
        for settimana in cal:
            giorni_settimana = []
            for giorno in settimana:
                if giorno == 0:
                    giorni_settimana.append({
                        'numero': None,
                        'consegne': [],
                        'ritiri': [],
                        'is_oggi': False
                    })
                else:
                    data_corrente = date(anno, mese, giorno)
                    giorni_settimana.append({
                        'numero': giorno,
                        'data': data_corrente,
                        'consegne': consegne_per_giorno.get(giorno, []),
                        'ritiri': ritiri_per_giorno.get(giorno, []),
                        'is_oggi': data_corrente == date.today(),
                        'is_passato': data_corrente < date.today()
                    })
            settimane.append(giorni_settimana)

        context.update({
            'anno': anno,
            'mese': mese,
            'nome_mese': nome_mese,
            'settimane': settimane,
            'mese_prec': mese_prec,
            'anno_prec': anno_prec,
            'mese_succ': mese_succ,
            'anno_succ': anno_succ,
        })

        return context


@method_decorator(login_required, name='dispatch')
class CalendarioGiornoView(TemplateView):
    """Vista dettaglio giorno con tutte le consegne/ritiri"""
    template_name = 'logistica/calendario_giorno.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Ottieni data da URL o usa oggi
        anno = int(self.kwargs.get('anno', datetime.now().year))
        mese = int(self.kwargs.get('mese', datetime.now().month))
        giorno = int(self.kwargs.get('giorno', datetime.now().day))

        data_selezionata = date(anno, mese, giorno)

        # Calcola giorno precedente e successivo
        giorno_prec = data_selezionata - timedelta(days=1)
        giorno_succ = data_selezionata + timedelta(days=1)

        # Ottieni consegne del giorno
        consegne = Progetto.objects.filter(
            data_consegna_richiesta=data_selezionata,
            deleted_at__isnull=True
        ).select_related('cliente', 'commerciale').prefetch_related('reparti')

        # Ottieni ritiri del giorno
        ritiri = Progetto.objects.filter(
            data_ritiro_richiesta=data_selezionata,
            deleted_at__isnull=True
        ).select_related('cliente', 'commerciale').prefetch_related('reparti')

        context.update({
            'data_selezionata': data_selezionata,
            'consegne': consegne,
            'ritiri': ritiri,
            'giorno_prec': giorno_prec,
            'giorno_succ': giorno_succ,
            'is_oggi': data_selezionata == date.today(),
        })

        return context


@method_decorator(login_required, name='dispatch')
class CalendarioMezziView(TemplateView):
    """
    Calendario mensile che mostra i mezzi impegnati per ogni giorno.

    Per ogni giorno mostra quali mezzi sono assegnati a progetti
    in base alle date di consegna e ritiro.
    """
    template_name = 'logistica/calendario_mezzi.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Ottieni anno e mese da URL o usa corrente
        anno = int(self.kwargs.get('anno', datetime.now().year))
        mese = int(self.kwargs.get('mese', datetime.now().month))

        # Dati calendario
        mese_corrente = date(anno, mese, 1)
        nome_mese = calendar.month_name[mese]

        # Mese precedente e successivo
        if mese == 1:
            mese_prec = date(anno - 1, 12, 1)
        else:
            mese_prec = date(anno, mese - 1, 1)

        if mese == 12:
            mese_succ = date(anno + 1, 1, 1)
        else:
            mese_succ = date(anno, mese + 1, 1)

        # Genera struttura calendario
        cal = monthcalendar(anno, mese)
        settimane = []

        # Ottieni tutti i progetti del mese con mezzi assegnati
        primo_giorno = date(anno, mese, 1)
        ultimo_giorno = date(anno, mese, monthrange(anno, mese)[1])

        progetti_con_mezzi = Progetto.objects.filter(
            deleted_at__isnull=True,
            mezzi_assegnati__isnull=False,
            # Progetto attivo nel mese (consegna <= ultimo giorno AND ritiro >= primo giorno)
            data_consegna_richiesta__date__lte=ultimo_giorno,
            data_ritiro_richiesta__date__gte=primo_giorno
        ).select_related('cliente').prefetch_related('mezzi_assegnati').distinct()

        # Organizza mezzi per giorno
        mezzi_per_giorno = defaultdict(list)

        for progetto in progetti_con_mezzi:
            # Range date progetto
            data_inizio = progetto.data_consegna_richiesta.date()
            data_fine = progetto.data_ritiro_richiesta.date()

            # Per ogni giorno del progetto nel mese
            current_date = max(data_inizio, primo_giorno)
            end_date = min(data_fine, ultimo_giorno)

            while current_date <= end_date:
                for mezzo in progetto.mezzi_assegnati.all():
                    mezzi_per_giorno[current_date].append({
                        'mezzo': mezzo,
                        'progetto': progetto,
                        'numero': mezzo.numero_mezzo or '?',
                        'targa': mezzo.targa,
                    })
                current_date += timedelta(days=1)

        # Costruisci settimane con dati
        for settimana in cal:
            giorni_settimana = []
            for giorno in settimana:
                if giorno == 0:
                    giorni_settimana.append({
                        'numero': None,
                        'is_oggi': False,
                        'mezzi': []
                    })
                else:
                    data_giorno = date(anno, mese, giorno)
                    mezzi_giorno = mezzi_per_giorno.get(data_giorno, [])

                    # Raggruppa per mezzo (se stesso mezzo usato da più progetti)
                    mezzi_unici = {}
                    for item in mezzi_giorno:
                        targa = item['targa']
                        if targa not in mezzi_unici:
                            mezzi_unici[targa] = {
                                'mezzo': item['mezzo'],
                                'numero': item['numero'],
                                'targa': targa,
                                'progetti': []
                            }
                        mezzi_unici[targa]['progetti'].append(item['progetto'])

                    giorni_settimana.append({
                        'numero': giorno,
                        'data': data_giorno,
                        'is_oggi': data_giorno == date.today(),
                        'mezzi': list(mezzi_unici.values()),
                        'count_mezzi': len(mezzi_unici)
                    })
            settimane.append(giorni_settimana)

        # Lista tutti i mezzi attivi
        tutti_mezzi = Automezzo.objects.filter(
            attivo=True,
            bloccata=False
        ).order_by('numero_mezzo', 'targa')

        context.update({
            'anno': anno,
            'mese': mese,
            'nome_mese': nome_mese,
            'mese_corrente': mese_corrente,
            'mese_prec': mese_prec,
            'mese_succ': mese_succ,
            'settimane': settimane,
            'oggi': date.today(),
            'tutti_mezzi': tutti_mezzi,
            'giorni_settimana': ['Lun', 'Mar', 'Mer', 'Gio', 'Ven', 'Sab', 'Dom'],
        })

        return context
