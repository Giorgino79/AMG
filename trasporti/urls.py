"""
URLs for Trasporti app
======================

URL patterns per l'app trasporti.
Workflow a 3 step simile a preventivi.
"""

from django.urls import path
from . import views

app_name = 'trasporti'

urlpatterns = [
    # Dashboard
    path('trasporti', views.dashboard, name='dashboard'),

    # Lista richieste
    path('richieste/', views.richieste_list, name='richieste_list'),
    path('richieste/<uuid:pk>/', views.richiesta_detail, name='richiesta_detail'),

    # Creazione richiesta
    path('richieste/nuova/', views.richiesta_create, name='richiesta_create'),

    # Gestione trasportatori
    path('richieste/<uuid:pk>/trasportatori/', views.richiesta_select_trasportatori, name='richiesta_select_trasportatori'),

    # Workflow 3 Step
    path('richieste/<uuid:pk>/step1-invia/', views.step1_invia_trasportatori, name='step1_invia'),
    path('richieste/<uuid:pk>/step2-raccolta/', views.step2_raccolta_offerte, name='step2_raccolta'),
    path('richieste/<uuid:pk>/step3-valutazione/', views.step3_valutazione, name='step3_valutazione'),
    path('richieste/<uuid:pk>/conferma-trasporto/', views.conferma_trasporto, name='conferma_trasporto'),
    path('richieste/<uuid:pk>/marca-in-corso/', views.marca_trasporto_in_corso, name='marca_in_corso'),
    path('richieste/<uuid:pk>/marca-consegnato/', views.marca_consegna_effettuata, name='marca_consegnato'),
    path('richieste/<uuid:pk>/riapri/', views.riapri_richiesta, name='riapri_richiesta'),

    # Gestione offerte
    path('richieste/<uuid:richiesta_pk>/offerta/nuova/', views.offerta_create, name='offerta_create'),
    path('offerte/<uuid:pk>/', views.offerta_detail, name='offerta_detail'),

    # Tracking
    path('offerte/<uuid:pk>/tracking/', views.offerta_tracking, name='offerta_tracking'),

    # API Endpoints (AJAX)
    path('offerte/<uuid:pk>/parametri/', views.offerta_parametri_get, name='offerta_parametri_get'),
    path('offerte/<uuid:pk>/parametri/save/', views.offerta_parametri_save, name='offerta_parametri_save'),

    # Calcolo distanza (AJAX)
    path('api/calcola-distanza/', views.api_calcola_distanza, name='api_calcola_distanza'),

    # Risposta pubblica fornitori (senza autenticazione)
    path('risposta/<uuid:token>/', views.risposta_fornitore_pubblica, name='risposta_fornitore_pubblica'),
]
