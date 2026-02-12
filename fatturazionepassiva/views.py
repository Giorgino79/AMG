# fatturazionepassiva/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.db.models import Q
from django.utils import timezone
from django.core.paginator import Paginator
from django.conf import settings
from datetime import datetime, timedelta
import json

from .models import RiconoscimentoFornitore, RigaRiconoscimento, ExportRiconoscimento
from anagrafica.models import Fornitore


@login_required
def dashboard(request):
    """Dashboard principale fatturazione passiva"""
    
    # Statistiche recenti
    riconoscimenti_recenti = RiconoscimentoFornitore.objects.select_related('fornitore').order_by('-data_creazione')[:5]
    
    # Contatori per stato
    stats = {
        'totale': RiconoscimentoFornitore.objects.count(),
        'bozze': RiconoscimentoFornitore.objects.filter(stato='bozza').count(),
        'definitivi': RiconoscimentoFornitore.objects.filter(stato='definitivo').count(),
        'inviati': RiconoscimentoFornitore.objects.filter(stato='inviato').count(),
    }
    
    context = {
        'riconoscimenti_recenti': riconoscimenti_recenti,
        'stats': stats,
    }
    
    return render(request, 'fatturazionepassiva/dashboard.html', context)


@login_required
def lista_riconoscimenti(request):
    """Lista dei riconoscimenti con filtri"""
    
    # Queryset base
    riconoscimenti = RiconoscimentoFornitore.objects.select_related('fornitore', 'creato_da').order_by('-data_creazione')
    
    # Filtri
    fornitore_id = request.GET.get('fornitore')
    stato = request.GET.get('stato')
    periodo_da = request.GET.get('periodo_da')
    periodo_a = request.GET.get('periodo_a')
    
    if fornitore_id:
        riconoscimenti = riconoscimenti.filter(fornitore_id=fornitore_id)
    
    if stato:
        riconoscimenti = riconoscimenti.filter(stato=stato)
    
    if periodo_da:
        try:
            data_da = datetime.strptime(periodo_da, '%Y-%m-%d').date()
            riconoscimenti = riconoscimenti.filter(periodo_da__gte=data_da)
        except ValueError:
            pass
    
    if periodo_a:
        try:
            data_a = datetime.strptime(periodo_a, '%Y-%m-%d').date()
            riconoscimenti = riconoscimenti.filter(periodo_a__lte=data_a)
        except ValueError:
            pass
    
    # Paginazione
    paginator = Paginator(riconoscimenti, 20)
    page = request.GET.get('page')
    riconoscimenti_page = paginator.get_page(page)
    
    # Fornitori per filtro
    fornitori = Fornitore.objects.filter(attivo=True).order_by('nome')
    
    context = {
        'riconoscimenti': riconoscimenti_page,
        'fornitori': fornitori,
        'filtri': {
            'fornitore_id': fornitore_id,
            'stato': stato,
            'periodo_da': periodo_da,
            'periodo_a': periodo_a,
        },
        'stati_choices': RiconoscimentoFornitore.STATI_RICONOSCIMENTO,
    }
    
    return render(request, 'fatturazionepassiva/lista_riconoscimenti.html', context)


@login_required
def crea_riconoscimento(request):
    """Form per creare nuovo riconoscimento"""
    
    if request.method == 'POST':
        try:
            fornitore_id = request.POST.get('fornitore')
            periodo_da = request.POST.get('periodo_da')
            periodo_a = request.POST.get('periodo_a')
            
            # Validazioni
            if not all([fornitore_id, periodo_da, periodo_a]):
                messages.error(request, 'Tutti i campi sono obbligatori')
                return redirect('fatturazionepassiva:crea_riconoscimento')
            
            fornitore = get_object_or_404(Fornitore, id=fornitore_id)
            periodo_da_date = datetime.strptime(periodo_da, '%Y-%m-%d').date()
            periodo_a_date = datetime.strptime(periodo_a, '%Y-%m-%d').date()
            
            # Controlla se esiste già un riconoscimento per questo periodo
            esistente = RiconoscimentoFornitore.objects.filter(
                fornitore=fornitore,
                periodo_da=periodo_da_date,
                periodo_a=periodo_a_date
            ).exists()
            
            if esistente:
                messages.error(request, 'Esiste già un riconoscimento per questo fornitore e periodo')
                return redirect('fatturazionepassiva:crea_riconoscimento')
            
            # Crea riconoscimento
            riconoscimento = RiconoscimentoFornitore.objects.create(
                fornitore=fornitore,
                periodo_da=periodo_da_date,
                periodo_a=periodo_a_date,
                include_ordini_ricevuti=request.POST.get('include_ordini_ricevuti') == 'on',
                include_ordini_da_ricevere=request.POST.get('include_ordini_da_ricevere') == 'on',
                include_ricezioni_manuali=request.POST.get('include_ricezioni_manuali') == 'on',
                creato_da=request.user,
                note=request.POST.get('note', '')
            )
            
            # Genera righe automaticamente
            righe_create = riconoscimento.genera_righe_da_acquisti()
            
            messages.success(request, f'Riconoscimento creato con {righe_create} righe')
            return redirect('fatturazionepassiva:dettaglio_riconoscimento', pk=riconoscimento.pk)
            
        except Exception as e:
            messages.error(request, f'Errore nella creazione: {str(e)}')
    
    # GET - Mostra form
    fornitori = Fornitore.objects.filter(attivo=True).order_by('nome')
    
    # Date predefinite (ultimo mese)
    oggi = timezone.now().date()
    primo_mese = oggi.replace(day=1)
    ultimo_mese_fine = primo_mese - timedelta(days=1)
    ultimo_mese_inizio = ultimo_mese_fine.replace(day=1)
    
    context = {
        'fornitori': fornitori,
        'periodo_da_default': ultimo_mese_inizio.strftime('%Y-%m-%d'),
        'periodo_a_default': ultimo_mese_fine.strftime('%Y-%m-%d'),
    }
    
    return render(request, 'fatturazionepassiva/crea_riconoscimento.html', context)


@login_required
def dettaglio_riconoscimento(request, pk):
    """Dettaglio riconoscimento con righe"""
    
    riconoscimento = get_object_or_404(
        RiconoscimentoFornitore.objects.select_related('fornitore', 'creato_da'),
        pk=pk
    )
    
    # Righe con prodotti
    righe = riconoscimento.righe.select_related(
        'prodotto', 'ordine_riferimento', 'ricezione_riferimento'
    ).order_by('prodotto__nome_prodotto')
    
    # Export effettuati
    export_history = riconoscimento.export.order_by('-data_export')[:10]
    
    context = {
        'riconoscimento': riconoscimento,
        'righe': righe,
        'export_history': export_history,
        'can_modify': riconoscimento.can_modify(),
        'can_send': riconoscimento.can_send(),
        'can_confirm': riconoscimento.can_confirm(),
    }
    
    return render(request, 'fatturazionepassiva/dettaglio_riconoscimento.html', context)


@login_required
def cambia_stato_riconoscimento(request, pk):
    """Cambia stato riconoscimento"""
    
    if request.method != 'POST':
        messages.error(request, 'Metodo non consentito')
        return redirect('fatturazionepassiva:dettaglio_riconoscimento', pk=pk)
    
    riconoscimento = get_object_or_404(RiconoscimentoFornitore, pk=pk)
    nuovo_stato = request.POST.get('nuovo_stato')
    
    try:
        if nuovo_stato == 'definitivo' and riconoscimento.stato == 'bozza':
            riconoscimento.stato = 'definitivo'
            riconoscimento.save()
            messages.success(request, 'Riconoscimento reso definitivo')
            
        elif nuovo_stato == 'inviato' and riconoscimento.can_send():
            riconoscimento.stato = 'inviato'
            riconoscimento.inviato_via_email = True
            riconoscimento.data_invio_email = timezone.now()
            riconoscimento.save()
            messages.success(request, 'Riconoscimento marcato come inviato')
            
        elif nuovo_stato == 'confermato' and riconoscimento.can_confirm():
            riconoscimento.stato = 'confermato'
            riconoscimento.confermato_da = request.user
            riconoscimento.data_conferma = timezone.now()
            riconoscimento.save()
            messages.success(request, 'Riconoscimento confermato')
            
        elif nuovo_stato == 'annullato':
            riconoscimento.stato = 'annullato'
            riconoscimento.save()
            messages.success(request, 'Riconoscimento annullato')
            
        else:
            messages.error(request, 'Cambio stato non consentito')
            
    except Exception as e:
        messages.error(request, f'Errore nel cambio stato: {str(e)}')
    
    return redirect('fatturazionepassiva:dettaglio_riconoscimento', pk=pk)


@login_required
def export_pdf(request, pk):
    """Export riconoscimento in PDF"""
    from .utils import ExportRiconoscimento
    
    riconoscimento = get_object_or_404(RiconoscimentoFornitore, pk=pk)
    
    try:
        exporter = ExportRiconoscimento(riconoscimento)
        return exporter.export_pdf()
    except ImportError:
        messages.error(request, 'Libreria PDF non disponibile')
        return redirect('fatturazionepassiva:dettaglio_riconoscimento', pk=pk)
    except Exception as e:
        messages.error(request, f'Errore nell\'export PDF: {str(e)}')
        return redirect('fatturazionepassiva:dettaglio_riconoscimento', pk=pk)


@login_required
def export_excel(request, pk):
    """Export riconoscimento in Excel"""
    from .utils import ExportRiconoscimento
    
    riconoscimento = get_object_or_404(RiconoscimentoFornitore, pk=pk)
    
    try:
        exporter = ExportRiconoscimento(riconoscimento)
        return exporter.export_excel()
    except ImportError:
        messages.error(request, 'Libreria Excel non disponibile')
        return redirect('fatturazionepassiva:dettaglio_riconoscimento', pk=pk)
    except Exception as e:
        messages.error(request, f'Errore nell\'export Excel: {str(e)}')
        return redirect('fatturazionepassiva:dettaglio_riconoscimento', pk=pk)


@login_required
def export_csv(request, pk):
    """Export riconoscimento in CSV"""
    from .utils import ExportRiconoscimento
    
    riconoscimento = get_object_or_404(RiconoscimentoFornitore, pk=pk)
    
    try:
        exporter = ExportRiconoscimento(riconoscimento)
        return exporter.export_csv()
    except Exception as e:
        messages.error(request, f'Errore nell\'export CSV: {str(e)}')
        return redirect('fatturazionepassiva:dettaglio_riconoscimento', pk=pk)


@login_required
def invia_email(request, pk):
    """Invia riconoscimento via email"""
    from .utils import invia_email_riconoscimento
    
    riconoscimento = get_object_or_404(RiconoscimentoFornitore, pk=pk)
    
    if request.method == 'POST':
        email_destinatario = request.POST.get('email_destinatario')
        includi_allegato = request.POST.get('includi_allegato') == 'on'
        tipo_allegato = request.POST.get('tipo_allegato', 'pdf')
        
        if not email_destinatario:
            messages.error(request, 'Email destinatario obbligatoria')
        else:
            try:
                success = invia_email_riconoscimento(
                    riconoscimento=riconoscimento,
                    email_destinatario=email_destinatario,
                    user=request.user,
                    includi_allegato=includi_allegato,
                    tipo_allegato=tipo_allegato
                )
                
                if success:
                    messages.success(request, f'Email inviata a {email_destinatario}')
                    # Cambia stato se necessario
                    if riconoscimento.stato == 'definitivo':
                        riconoscimento.stato = 'inviato'
                        riconoscimento.save()
                else:
                    messages.error(request, 'Errore nell\'invio email')
                    
            except Exception as e:
                messages.error(request, f'Errore nell\'invio: {str(e)}')
        
        return redirect('fatturazionepassiva:dettaglio_riconoscimento', pk=pk)
    
    # GET - Mostra form
    # Email predefinita del fornitore
    email_default = ''
    if hasattr(riconoscimento.fornitore, 'email') and riconoscimento.fornitore.email:
        email_default = riconoscimento.fornitore.email
    
    context = {
        'riconoscimento': riconoscimento,
        'email_default': email_default,
    }
    
    return render(request, 'fatturazionepassiva/invia_email.html', context)
