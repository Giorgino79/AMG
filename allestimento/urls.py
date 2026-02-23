from django.urls import path
from . import views

app_name = 'allestimento'

urlpatterns = [
    path('', views.lista_sessioni, name='lista_sessioni'),
    path('upload/', views.upload_excel, name='upload_excel'),
    path('sessione/<int:pk>/', views.dettaglio_sessione, name='dettaglio_sessione'),
    path('sessione/<int:pk>/elimina/', views.elimina_sessione, name='elimina_sessione'),
    path('sessione/<int:pk>/pdf/', views.genera_pdf, name='genera_pdf'),
    path('riga/<int:pk>/conferma/', views.conferma_riga, name='conferma_riga'),
]
