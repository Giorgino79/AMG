# fatturazionepassiva/urls.py

from django.urls import path
from . import views

app_name = 'fatturazionepassiva'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Riconoscimenti CRUD
    path('riconoscimenti/', views.lista_riconoscimenti, name='lista_riconoscimenti'),
    path('riconoscimenti/nuovo/', views.crea_riconoscimento, name='crea_riconoscimento'),
    path('riconoscimenti/<int:pk>/', views.dettaglio_riconoscimento, name='dettaglio_riconoscimento'),
    path('riconoscimenti/<int:pk>/stato/', views.cambia_stato_riconoscimento, name='cambia_stato_riconoscimento'),
    
    # Export
    path('riconoscimenti/<int:pk>/export/pdf/', views.export_pdf, name='export_pdf'),
    path('riconoscimenti/<int:pk>/export/excel/', views.export_excel, name='export_excel'),
    path('riconoscimenti/<int:pk>/export/csv/', views.export_csv, name='export_csv'),
    
    # Email
    path('riconoscimenti/<int:pk>/email/', views.invia_email, name='invia_email'),
]