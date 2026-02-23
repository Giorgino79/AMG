"""
URLs for Preventivi Beni/Servizi app
====================================
"""

from django.urls import path
from . import views

app_name = 'preventivi_beni'

urlpatterns = [
    # Dashboard
    path('prevenvitiv', views.dashboard, name='dashboard'),

    # Liste e dettagli
    path('richieste/', views.richieste_list, name='richieste_list'),
    path('richieste/<uuid:pk>/', views.richiesta_detail, name='richiesta_detail'),

    # Creazione
    path('richieste/nuova/', views.richiesta_create, name='richiesta_create'),

    # Selezione fornitori
    path('richieste/<uuid:pk>/fornitori/', views.richiesta_select_fornitori, name='richiesta_select_fornitori'),

    # Workflow 3 Step
    path('richieste/<uuid:pk>/step1-invia/', views.step1_invia_fornitori, name='step1_invia'),
    path('richieste/<uuid:pk>/step2-raccolta/', views.step2_raccolta_offerte, name='step2_raccolta'),
    path('richieste/<uuid:pk>/step3-valutazione/', views.step3_valutazione, name='step3_valutazione'),

    # Conferma ordine
    path('richieste/<uuid:pk>/conferma-ordine/', views.conferma_ordine, name='conferma_ordine'),
    path('richieste/<uuid:pk>/riapri/', views.riapri_richiesta, name='riapri_richiesta'),

    # Offerte
    path('richieste/<uuid:richiesta_pk>/offerta/nuova/', views.offerta_create, name='offerta_create'),
    path('offerte/<uuid:pk>/', views.offerta_detail, name='offerta_detail'),

    # API endpoints (AJAX)
    path('offerte/<uuid:pk>/parametri/', views.offerta_parametri_get, name='offerta_parametri_get'),
    path('offerte/<uuid:pk>/parametri/save/', views.offerta_parametri_save, name='offerta_parametri_save'),

    # View pubblica per risposta fornitori (senza autenticazione)
    path('risposta/<uuid:token>/', views.risposta_fornitore_pubblica, name='risposta_fornitore_pubblica'),
]
