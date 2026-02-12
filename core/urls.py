"""
URL Configuration per l'app Core

Include le API AJAX per la gestione allegati e gestione Template Permessi.
"""

from django.urls import path
from .views_allegati import (
    allegato_upload,
    allegati_list,
    allegato_delete,
    allegato_download,
    allegato_preview,
    global_search,
)
from .views import serve_qr_code
from .views_qrcode import (
    qrcode_generate,
    qrcode_download,
    qrcode_delete,
    qrcode_check,
)
from .views_permissions import (
    permission_template_list_view,
    permission_template_create_view,
    permission_template_detail_view,
    permission_template_update_view,
    permission_template_delete_view,
)

app_name = "core"

urlpatterns = [
    # ========== API ALLEGATI (AJAX) ==========
    path("allegati/upload/", allegato_upload, name="allegato_upload"),
    path("allegati/list/", allegati_list, name="allegati_list"),
    path("allegati/<int:allegato_id>/delete/", allegato_delete, name="allegato_delete"),
    path(
        "allegati/<int:allegato_id>/download/",
        allegato_download,
        name="allegato_download",
    ),
    path(
        "allegati/<int:allegato_id>/preview/", allegato_preview, name="allegato_preview"
    ),
    # ========== RICERCA GLOBALE (AJAX) ==========
    path("search/", global_search, name="global_search"),
    # ========== API QR CODE (AJAX) ==========
    path("qrcode/generate/", qrcode_generate, name="qrcode_generate"),
    path("qrcode/check/", qrcode_check, name="qrcode_check"),
    path("qrcode/<int:qrcode_id>/download/", qrcode_download, name="qrcode_download"),
    path("qrcode/<int:qrcode_id>/delete/", qrcode_delete, name="qrcode_delete"),
    # ========== UTILITY QR CODE (Legacy) ==========
    path("qrcode/", serve_qr_code, name="serve_qr_code"),
    # ========== TEMPLATE PERMESSI ==========
    path("permission-templates/", permission_template_list_view, name="permission_template_list"),
    path("permission-templates/create/", permission_template_create_view, name="permission_template_create"),
    path("permission-templates/<int:pk>/", permission_template_detail_view, name="permission_template_detail"),
    path("permission-templates/<int:pk>/update/", permission_template_update_view, name="permission_template_update"),
    path("permission-templates/<int:pk>/delete/", permission_template_delete_view, name="permission_template_delete"),
]
