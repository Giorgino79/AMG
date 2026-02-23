from django.urls import path
from . import views

app_name = 'logistica'

urlpatterns = [
    # Dashboard
    path('', views.DashboardLogisticaView.as_view(), name='dashboard'),

    # Calendario Mensile
    path('calendario/', views.CalendarioMeseView.as_view(), name='calendario_mese'),
    path('calendario/<int:anno>/<int:mese>/', views.CalendarioMeseView.as_view(), name='calendario_mese'),

    # Calendario Giornaliero
    path('giorno/', views.CalendarioGiornoView.as_view(), name='calendario_giorno'),
    path('giorno/<int:anno>/<int:mese>/<int:giorno>/', views.CalendarioGiornoView.as_view(), name='calendario_giorno'),

    # Calendario Mezzi
    path('mezzi/', views.CalendarioMezziView.as_view(), name='calendario_mezzi'),
    path('mezzi/<int:anno>/<int:mese>/', views.CalendarioMezziView.as_view(), name='calendario_mezzi'),
]
