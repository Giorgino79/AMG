"""
URLs per app progetti_eventi.
"""

from django.urls import path
from . import views

app_name = 'progetti_eventi'

urlpatterns = [
    # Dashboard
    path('', views.DashboardCommercialeView.as_view(), name='dashboard'),

    # Progetti
    path('progetti/', views.ProgettoListView.as_view(), name='progetto_list'),
    path('progetti/nuovo/', views.ProgettoCreateView.as_view(), name='progetto_create'),
    path('progetti/<uuid:pk>/', views.ProgettoDetailView.as_view(), name='progetto_detail'),
    path('progetti/<uuid:pk>/modifica/', views.ProgettoUpdateView.as_view(), name='progetto_update'),
    path('progetti/<uuid:pk>/elimina/', views.ProgettoDeleteView.as_view(), name='progetto_delete'),

    # Azioni Progetto
    path('progetti/<uuid:pk>/invia-engineering/', views.ProgettoInviaEngineeringView.as_view(), name='progetto_invia_engineering'),

    # Reparti
    path('reparti/<uuid:pk>/', views.ProgettoRepartoDetailView.as_view(), name='reparto_detail'),

    # Liste Prodotti
    path('reparti/<uuid:reparto_pk>/liste-prodotti/nuova/', views.ListaProdottiCreateView.as_view(), name='lista_prodotti_create'),
    path('liste-prodotti/<uuid:pk>/', views.ListaProdottiDetailView.as_view(), name='lista_prodotti_detail'),
    path('liste-prodotti/<uuid:pk>/approva/', views.ListaProdottiApprovaView.as_view(), name='lista_prodotti_approva'),
]
