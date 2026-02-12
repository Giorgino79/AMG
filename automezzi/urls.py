from django.urls import path

from .views import (
    AutomezzoListView,
    AutomezzoDetailView,
    AutomezzoCreateView,
    AutomezzoUpdateView,
    AutomezzoDeleteView,
    ManutenzioneListView,
    ManutenzioneDetailView,
    ManutenzioneCreateView,
    ManutenzioneUpdateView,
    ManutenzioneDeleteView,
    ManutenzioneResponsabileView,
    ManutenzioneFinaleView,
    AllegatoManutenzioneCreateView,
    RifornimentoListView,
    RifornimentoDetailView,
    RifornimentoCreateView,
    RifornimentoUpdateView,
    RifornimentoDeleteView,
    EventoAutomezzoListView,
    EventoAutomezzoDetailView,
    EventoAutomezzoCreateView,
    EventoAutomezzoUpdateView,
    EventoAutomezzoDeleteView,
    DashboardView,
    CronologiaAutomezzoView,
    RifornimentoPDFView,
    EventoPDFView,
    ManutenzionePDFView,
    AffidamentoMezzoListView,
    AffidamentoMezzoCreateView,
    AffidamentoMezzoDetailView,
    AffidamentoAccettaView,
    AffidamentoRientroView,
    MioAffidamentoView,
    AffidamentoRifornimentoCreateView,
    AffidamentoEventoCreateView,
)

app_name = "automezzi"

urlpatterns = [
    path("", DashboardView.as_view(), name="dashboard"),
    path("cronologia/", CronologiaAutomezzoView.as_view(), name="cronologia"),
    # AUTOMEZZI
    path("lista/", AutomezzoListView.as_view(), name="automezzo_list"),
    path("nuovo/", AutomezzoCreateView.as_view(), name="automezzo_create"),
    path("<int:pk>/", AutomezzoDetailView.as_view(), name="automezzo_detail"),
    path(
        "<int:pk>/modifica/",
        AutomezzoUpdateView.as_view(),
        name="automezzo_update",
    ),
    path(
        "<int:pk>/elimina/",
        AutomezzoDeleteView.as_view(),
        name="automezzo_delete",
    ),
    # MANUTENZIONI
    path("manutenzioni/", ManutenzioneListView.as_view(), name="manutenzione_list"),
    path(
        "manutenzioni/nuova/",
        ManutenzioneCreateView.as_view(),
        name="manutenzione_create",
    ),
    path(
        "manutenzioni/<int:pk>/",
        ManutenzioneDetailView.as_view(),
        name="manutenzione_detail",
    ),
    path(
        "manutenzioni/<int:pk>/modifica/",
        ManutenzioneUpdateView.as_view(),
        name="manutenzione_update",
    ),
    path(
        "manutenzioni/<int:pk>/prendi-carico/",
        ManutenzioneResponsabileView.as_view(),
        name="manutenzione_prendi_carico",
    ),
    path(
        "manutenzioni/<int:pk>/completa/",
        ManutenzioneFinaleView.as_view(),
        name="manutenzione_completa",
    ),
    path(
        "manutenzioni/<int:manutenzione_pk>/allegati/nuovo/",
        AllegatoManutenzioneCreateView.as_view(),
        name="allegato_manutenzione_create",
    ),
    path(
        "manutenzioni/<int:pk>/elimina/",
        ManutenzioneDeleteView.as_view(),
        name="manutenzione_delete",
    ),
    # annidate per automezzo
    path(
        "<int:automezzo_pk>/manutenzioni/",
        ManutenzioneListView.as_view(),
        name="manutenzione_list_automezzo",
    ),
    path(
        "<int:automezzo_pk>/manutenzioni/nuova/",
        ManutenzioneCreateView.as_view(),
        name="manutenzione_create_automezzo",
    ),
    # RIFORNIMENTI
    path("rifornimenti/", RifornimentoListView.as_view(), name="rifornimento_list"),
    path(
        "rifornimenti/nuovo/",
        RifornimentoCreateView.as_view(),
        name="rifornimento_create",
    ),
    path(
        "rifornimenti/<int:pk>/",
        RifornimentoDetailView.as_view(),
        name="rifornimento_detail",
    ),
    path(
        "rifornimenti/<int:pk>/modifica/",
        RifornimentoUpdateView.as_view(),
        name="rifornimento_update",
    ),
    path(
        "rifornimenti/<int:pk>/elimina/",
        RifornimentoDeleteView.as_view(),
        name="rifornimento_delete",
    ),
    # annidate per automezzo
    path(
        "<int:automezzo_pk>/rifornimenti/",
        RifornimentoListView.as_view(),
        name="rifornimento_list_automezzo",
    ),
    path(
        "<int:automezzo_pk>/rifornimenti/nuovo/",
        RifornimentoCreateView.as_view(),
        name="rifornimento_create_automezzo",
    ),
    # EVENTI
    path("eventi/", EventoAutomezzoListView.as_view(), name="evento_list"),
    path("eventi/nuovo/", EventoAutomezzoCreateView.as_view(), name="evento_create"),
    path("eventi/<int:pk>/", EventoAutomezzoDetailView.as_view(), name="evento_detail"),
    path(
        "eventi/<int:pk>/modifica/",
        EventoAutomezzoUpdateView.as_view(),
        name="evento_update",
    ),
    path(
        "eventi/<int:pk>/elimina/",
        EventoAutomezzoDeleteView.as_view(),
        name="evento_delete",
    ),
    # annidate per automezzo
    path(
        "<int:automezzo_pk>/eventi/",
        EventoAutomezzoListView.as_view(),
        name="evento_list_automezzo",
    ),
    path(
        "<int:automezzo_pk>/eventi/nuovo/",
        EventoAutomezzoCreateView.as_view(),
        name="evento_create_automezzo",
    ),
    # PDF EXPORTS
    path(
        "rifornimenti/<int:pk>/pdf/",
        RifornimentoPDFView.as_view(),
        name="rifornimento_pdf",
    ),
    path("eventi/<int:pk>/pdf/", EventoPDFView.as_view(), name="evento_pdf"),
    path(
        "manutenzioni/<int:pk>/pdf/",
        ManutenzionePDFView.as_view(),
        name="manutenzione_pdf",
    ),
    # AFFIDAMENTI
    path("affidamenti/", AffidamentoMezzoListView.as_view(), name="affidamento_list"),
    path("affidamenti/nuovo/", AffidamentoMezzoCreateView.as_view(), name="affidamento_create"),
    path("affidamenti/<int:pk>/", AffidamentoMezzoDetailView.as_view(), name="affidamento_detail"),
    path("affidamenti/<int:pk>/rientro/", AffidamentoRientroView.as_view(), name="affidamento_rientro"),
    path("affidamenti/accetta/<uuid:token>/", AffidamentoAccettaView.as_view(), name="affidamento_accetta"),
    # IL MIO MEZZO (utente con affidamento attivo)
    path("il-mio-mezzo/", MioAffidamentoView.as_view(), name="mio_affidamento"),
    path("il-mio-mezzo/rifornimento/", AffidamentoRifornimentoCreateView.as_view(), name="affidamento_rifornimento_create"),
    path("il-mio-mezzo/evento/", AffidamentoEventoCreateView.as_view(), name="affidamento_evento_create"),
]
