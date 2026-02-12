"""
ACQUISTI URLs - URL patterns per app acquisti
============================================
"""

from django.urls import path
from . import views

app_name = 'acquisti'

urlpatterns = [
    # Dashboard principale
    path('', views.dashboard, name='dashboard'),

    # Gestione ordini
    path('crea/', views.crea_ordine, name='crea_ordine'),
    path('dettaglio/<int:pk>/', views.dettaglio_ordine, name='dettaglio_ordine'),
    path('pdf/<int:pk>/', views.scarica_pdf, name='scarica_pdf'),

    # Report ordini
    path('report/', views.report_ordini, name='report_ordini'),

    # AJAX endpoints
    path('ajax/segna-ricevuto/<int:pk>/', views.segna_ricevuto_ajax, name='segna_ricevuto_ajax'),
]
