"""
URL Configuration per l'app Users
"""

from django.urls import path
from . import views

app_name = "users"

urlpatterns = [
    # ========== AUTENTICAZIONE ==========
    path("", views.login_view, name="login"),  # Root = login (landing page)
    path("login/", views.login_view, name="login_alias"),  # Alias
    path("logout/", views.logout_view, name="logout"),
    # ========== CRUD USERS ==========
    path("users/", views.user_list_view, name="user_list"),
    path("users/create/", views.user_create_view, name="user_create"),
    path("users/<int:pk>/", views.user_detail_view, name="user_detail"),
    path("users/<int:pk>/update/", views.user_update_view, name="user_update"),
    path(
        "users/<int:pk>/permissions/",
        views.user_permissions_manage_view,
        name="user_permissions_manage",
    ),
    path(
        "users/<int:pk>/permissions/apply-template/",
        views.user_permissions_apply_template_view,
        name="user_permissions_apply_template",
    ),
    # ========== TIMBRATURE ==========
    path("timbratura/quick/", views.timbratura_quick_view, name="timbratura_quick"),
    path("timbrature/", views.timbratura_list_view, name="timbratura_list"),
    path("giornate/", views.giornata_lavorativa_list_view, name="giornata_list"),
    path("giornata/chiudi/", views.chiudi_giornata_view, name="chiudi_giornata"),
    # ========== FERIE E PERMESSI ==========
    path(
        "ferie/richiedi/",
        views.richiesta_ferie_create_view,
        name="richiesta_ferie_create",
    ),
    path("ferie/", views.richieste_ferie_list_view, name="richieste_ferie_list"),
    path(
        "ferie/<int:pk>/gestisci/",
        views.richiesta_ferie_gestisci_view,
        name="richiesta_ferie_gestisci",
    ),
    path(
        "ferie/admin/",
        views.richieste_ferie_admin_list_view,
        name="richieste_ferie_admin_list",
    ),
    path(
        "permessi/richiedi/",
        views.richiesta_permesso_create_view,
        name="richiesta_permesso_create",
    ),
    path(
        "permessi/", views.richieste_permessi_list_view, name="richieste_permessi_list"
    ),
    path(
        "permessi/<int:pk>/gestisci/",
        views.richiesta_permesso_gestisci_view,
        name="richiesta_permesso_gestisci",
    ),
    path(
        "permessi/admin/",
        views.richieste_permessi_admin_list_view,
        name="richieste_permessi_admin_list",
    ),
    # ========== LETTERE RICHIAMO ==========
    path(
        "lettere-richiamo/crea/",
        views.lettera_richiamo_create_view,
        name="lettera_richiamo_create",
    ),
    path(
        "lettere-richiamo/",
        views.lettera_richiamo_list_view,
        name="lettera_richiamo_list",
    ),
    # ========== PROFILO E IMPOSTAZIONI ==========
    path("profilo/", views.profilo_view, name="profilo"),
    path("impostazioni/", views.impostazioni_view, name="impostazioni"),
    # ========== EXPORT ==========
    path(
        "giornate/export/excel/",
        views.giornate_export_excel,
        name="giornate_export_excel",
    ),
    path("giornate/export/pdf/", views.giornate_export_pdf, name="giornate_export_pdf"),
]
