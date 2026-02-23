"""
Views per il modulo Payroll
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.db import transaction
from django.contrib.auth import get_user_model
from datetime import date
from decimal import Decimal

from .models import (
    DatiContrattualiPayroll,
    BustaPaga,
    CCNL,
    LivelloInquadramento,
    FeriePermessiPayroll,
    ManualePayroll,
)
from .services import PayrollCalculator

User = get_user_model()


@login_required
@permission_required("payroll.view_daticontrattualiPayroll", raise_exception=True)
def dati_payroll_detail(request, user_pk):
    """Visualizza i dati payroll di un dipendente"""
    user_obj = get_object_or_404(User, pk=user_pk)

    try:
        dati_payroll = user_obj.dati_payroll
    except DatiContrattualiPayroll.DoesNotExist:
        dati_payroll = None

    context = {
        "user_obj": user_obj,
        "dati_payroll": dati_payroll,
    }

    return render(request, "payroll/dati_payroll_detail.html", context)


@login_required
@permission_required("payroll.change_daticontrattualiPayroll", raise_exception=True)
def dati_payroll_form(request, user_pk):
    """Form per configurare i dati payroll di un dipendente"""
    user_obj = get_object_or_404(User, pk=user_pk)

    try:
        dati_payroll = user_obj.dati_payroll
    except DatiContrattualiPayroll.DoesNotExist:
        dati_payroll = None

    ccnl_list = CCNL.objects.all()
    livelli_list = LivelloInquadramento.objects.all()

    if request.method == "POST":
        # Recupera dati dal form
        ccnl_id = request.POST.get("ccnl")
        livello_id = request.POST.get("livello")
        tipo_contratto = request.POST.get("tipo_contratto")
        ore_settimanali = request.POST.get("ore_settimanali")
        percentuale_part_time = request.POST.get("percentuale_part_time")
        superminimo = request.POST.get("superminimo")
        aliquota_addizionale_regionale = request.POST.get(
            "aliquota_addizionale_regionale"
        )
        aliquota_addizionale_comunale = request.POST.get("aliquota_addizionale_comunale")
        detrazione_lavoro_dipendente = request.POST.get("detrazione_lavoro_dipendente")
        numero_figli_a_carico = request.POST.get("numero_figli_a_carico")
        coniuge_a_carico = request.POST.get("coniuge_a_carico")
        altri_familiari_a_carico = request.POST.get("altri_familiari_a_carico")
        iban = request.POST.get("iban")
        data_fine_contratto = request.POST.get("data_fine_contratto")
        data_cessazione = request.POST.get("data_cessazione")

        try:
            with transaction.atomic():
                if dati_payroll:
                    # Aggiorna esistente
                    if ccnl_id:
                        dati_payroll.ccnl = CCNL.objects.get(pk=ccnl_id)
                    if livello_id:
                        dati_payroll.livello = LivelloInquadramento.objects.get(
                            pk=livello_id
                        )
                    dati_payroll.tipo_contratto = tipo_contratto
                    dati_payroll.ore_settimanali = (
                        Decimal(ore_settimanali) if ore_settimanali else Decimal("40.00")
                    )
                    dati_payroll.percentuale_part_time = (
                        Decimal(percentuale_part_time)
                        if percentuale_part_time
                        else Decimal("100.00")
                    )
                    dati_payroll.superminimo = (
                        Decimal(superminimo) if superminimo else Decimal("0.00")
                    )
                    dati_payroll.aliquota_addizionale_regionale = (
                        Decimal(aliquota_addizionale_regionale)
                        if aliquota_addizionale_regionale
                        else Decimal("0.00")
                    )
                    dati_payroll.aliquota_addizionale_comunale = (
                        Decimal(aliquota_addizionale_comunale)
                        if aliquota_addizionale_comunale
                        else Decimal("0.00")
                    )
                    dati_payroll.detrazione_lavoro_dipendente = (
                        detrazione_lavoro_dipendente == "on"
                    )
                    dati_payroll.numero_figli_a_carico = (
                        int(numero_figli_a_carico) if numero_figli_a_carico else 0
                    )
                    dati_payroll.coniuge_a_carico = coniuge_a_carico == "on"
                    dati_payroll.altri_familiari_a_carico = (
                        int(altri_familiari_a_carico) if altri_familiari_a_carico else 0
                    )
                    dati_payroll.iban = iban or ""
                    dati_payroll.data_fine_contratto = data_fine_contratto or None
                    dati_payroll.data_cessazione = data_cessazione or None
                    dati_payroll.save()
                    messages.success(
                        request,
                        f"Dati payroll aggiornati per {user_obj.get_full_name()}",
                    )
                else:
                    # Crea nuovo
                    DatiContrattualiPayroll.objects.create(
                        user=user_obj,
                        ccnl=CCNL.objects.get(pk=ccnl_id) if ccnl_id else None,
                        livello=(
                            LivelloInquadramento.objects.get(pk=livello_id)
                            if livello_id
                            else None
                        ),
                        tipo_contratto=tipo_contratto,
                        ore_settimanali=(
                            Decimal(ore_settimanali)
                            if ore_settimanali
                            else Decimal("40.00")
                        ),
                        percentuale_part_time=(
                            Decimal(percentuale_part_time)
                            if percentuale_part_time
                            else Decimal("100.00")
                        ),
                        superminimo=(
                            Decimal(superminimo) if superminimo else Decimal("0.00")
                        ),
                        aliquota_addizionale_regionale=(
                            Decimal(aliquota_addizionale_regionale)
                            if aliquota_addizionale_regionale
                            else Decimal("0.00")
                        ),
                        aliquota_addizionale_comunale=(
                            Decimal(aliquota_addizionale_comunale)
                            if aliquota_addizionale_comunale
                            else Decimal("0.00")
                        ),
                        detrazione_lavoro_dipendente=(
                            detrazione_lavoro_dipendente == "on"
                        ),
                        numero_figli_a_carico=(
                            int(numero_figli_a_carico) if numero_figli_a_carico else 0
                        ),
                        coniuge_a_carico=coniuge_a_carico == "on",
                        altri_familiari_a_carico=(
                            int(altri_familiari_a_carico)
                            if altri_familiari_a_carico
                            else 0
                        ),
                        iban=iban or "",
                        data_fine_contratto=data_fine_contratto or None,
                        data_cessazione=data_cessazione or None,
                    )
                    messages.success(
                        request, f"Dati payroll creati per {user_obj.get_full_name()}"
                    )

            return redirect("users:user_detail", pk=user_obj.pk)

        except Exception as e:
            messages.error(request, f"Errore nel salvataggio: {e}")

    context = {
        "user_obj": user_obj,
        "dati_payroll": dati_payroll,
        "ccnl_list": ccnl_list,
        "livelli_list": livelli_list,
    }

    return render(request, "payroll/dati_payroll_form.html", context)


@login_required
@permission_required("payroll.view_bustapaga", raise_exception=True)
def busta_paga_list(request, user_pk):
    """Lista buste paga di un dipendente"""
    user_obj = get_object_or_404(User, pk=user_pk)
    buste = BustaPaga.objects.filter(user=user_obj).order_by("-anno", "-mese")

    # Statistiche
    buste_confermate_count = buste.filter(confermata=True).count()

    context = {
        "user_obj": user_obj,
        "buste": buste,
        "buste_confermate_count": buste_confermate_count,
    }

    return render(request, "payroll/busta_paga_list.html", context)


@login_required
@permission_required("payroll.view_bustapaga", raise_exception=True)
def busta_paga_detail(request, pk):
    """Dettaglio busta paga"""
    busta = get_object_or_404(BustaPaga, pk=pk)

    # Raggruppa voci per tipo
    competenze = busta.voci.filter(tipo="COMPETENZA")
    trattenute = busta.voci.filter(tipo="TRATTENUTA")
    detrazioni = busta.voci.filter(tipo="DEDUZIONE")

    context = {
        "busta": busta,
        "competenze": competenze,
        "trattenute": trattenute,
        "detrazioni": detrazioni,
    }

    return render(request, "payroll/busta_paga_detail.html", context)


@login_required
@permission_required("payroll.add_bustapaga", raise_exception=True)
def busta_paga_elabora(request, user_pk):
    """Form per elaborare una nuova busta paga"""
    user_obj = get_object_or_404(User, pk=user_pk)

    # Verifica dati payroll
    try:
        dati_payroll = user_obj.dati_payroll
    except DatiContrattualiPayroll.DoesNotExist:
        messages.error(
            request,
            f"Impossibile elaborare busta paga: dati payroll non configurati per {user_obj.get_full_name()}",
        )
        return redirect("users:user_detail", pk=user_obj.pk)

    # Default mese/anno corrente
    oggi = date.today()
    mese_default = oggi.month
    anno_default = oggi.year

    if request.method == "POST":
        mese = int(request.POST.get("mese", mese_default))
        anno = int(request.POST.get("anno", anno_default))
        ore_ordinarie = request.POST.get("ore_ordinarie")
        ore_straordinario_feriale = request.POST.get("ore_straordinario_feriale")
        ore_straordinario_festivo = request.POST.get("ore_straordinario_festivo")
        ore_straordinario_notturno = request.POST.get("ore_straordinario_notturno")
        ore_ferie = request.POST.get("ore_ferie")
        ore_rol = request.POST.get("ore_rol")
        ore_permessi = request.POST.get("ore_permessi")
        ore_malattia = request.POST.get("ore_malattia")

        try:
            # Inizializza calcolatore
            calculator = PayrollCalculator(user_obj, mese, anno)

            # Elabora busta
            busta = calculator.calcola_busta_paga(
                ore_ordinarie=Decimal(ore_ordinarie) if ore_ordinarie else Decimal("0"),
                ore_straordinari={
                    "feriale": (
                        Decimal(ore_straordinario_feriale)
                        if ore_straordinario_feriale
                        else Decimal("0")
                    ),
                    "festivo": (
                        Decimal(ore_straordinario_festivo)
                        if ore_straordinario_festivo
                        else Decimal("0")
                    ),
                    "notturno": (
                        Decimal(ore_straordinario_notturno)
                        if ore_straordinario_notturno
                        else Decimal("0")
                    ),
                },
                assenze={
                    "ferie": Decimal(ore_ferie) if ore_ferie else Decimal("0"),
                    "rol": Decimal(ore_rol) if ore_rol else Decimal("0"),
                    "permessi": Decimal(ore_permessi) if ore_permessi else Decimal("0"),
                    "malattia": Decimal(ore_malattia) if ore_malattia else Decimal("0"),
                },
            )

            # Matura ferie e permessi
            calculator.matura_ferie_permessi_mensili()

            messages.success(
                request,
                f"Busta paga elaborata con successo! Netto: € {busta.netto_busta:,.2f}",
            )
            return redirect("payroll:busta_paga_detail", pk=busta.pk)

        except Exception as e:
            messages.error(request, f"Errore nell'elaborazione: {e}")

    context = {
        "user_obj": user_obj,
        "mese_default": mese_default,
        "anno_default": anno_default,
    }

    return render(request, "payroll/busta_paga_elabora.html", context)


@login_required
@permission_required("payroll.view_feriepermessipayroll", raise_exception=True)
def ferie_permessi_list(request, user_pk):
    """Lista ferie e permessi payroll di un dipendente"""
    user_obj = get_object_or_404(User, pk=user_pk)
    anno_corrente = date.today().year

    ferie_permessi = FeriePermessiPayroll.objects.filter(
        user=user_obj, anno=anno_corrente
    ).order_by("tipo")

    context = {
        "user_obj": user_obj,
        "ferie_permessi": ferie_permessi,
        "anno": anno_corrente,
    }

    return render(request, "payroll/ferie_permessi_list.html", context)


@login_required
def manuale_payroll(request):
    """Visualizza il manuale di compilazione form Payroll"""
    manuale = ManualePayroll.get_manuale_attivo()

    context = {
        "manuale": manuale,
        "puo_modificare": request.user.is_staff or request.user.is_superuser,
    }

    return render(request, "payroll/manuale_payroll.html", context)


@login_required
def manuale_payroll_edit(request):
    """Modifica il manuale di compilazione (solo admin)"""
    # Verifica permessi admin
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, "Non hai i permessi per modificare il manuale.")
        return redirect("payroll:manuale_payroll")

    manuale = ManualePayroll.get_manuale_attivo()

    if request.method == "POST":
        titolo = request.POST.get("titolo")
        contenuto = request.POST.get("contenuto")
        versione = request.POST.get("versione")

        try:
            manuale.titolo = titolo
            manuale.contenuto = contenuto
            manuale.versione = versione
            manuale.modificato_da = request.user
            manuale.save()

            messages.success(request, "Manuale aggiornato con successo!")
            return redirect("payroll:manuale_payroll")

        except Exception as e:
            messages.error(request, f"Errore nel salvataggio: {e}")

    context = {
        "manuale": manuale,
    }

    return render(request, "payroll/manuale_payroll_edit.html", context)
