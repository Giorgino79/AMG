"""
URL configuration for ModularBEF project.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from users.views import dashboard_view

urlpatterns = [
    # Root - Redirect to login
    path("", include("users.urls")),  # Landing page = login
    # Dashboard centrale
    path("dashboard/", dashboard_view, name="dashboard"),
    path("home/", dashboard_view, name="home"),  # Alias per compatibilità template
    # Admin
    path("admin/", admin.site.urls),
    # Core (API allegati e utilities)
    path("core/", include("core.urls")),
    # Payroll
    path("payroll/", include("payroll.urls")),
    # Mail (Email, Promemoria, Chat - Premium Module)
    path("mail/", include("mail.urls")),
    # Anagrafica (Clienti e Fornitori)
    path("anagrafica/", include("anagrafica.urls")),
    path("trasporti/", include(("trasporti.urls", "trasporti"), namespace='trasporti')),
    path("preventivi_beni/", include("preventivi_beni.urls")),
    path("preventivi-beni/", include("preventivi_beni.urls")),  # Alias con trattino per compatibilità link email
    path("allestimento/", include("allestimento.urls")),
    path("acquisti/", include("acquisti.urls")),
    path("automezzi/", include("automezzi.urls")),
    path("stabilimenti/", include("stabilimenti.urls")),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
