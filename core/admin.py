from django.contrib import admin
from .models_legacy import Allegato, ModuloRegistry, QRCode


@admin.register(Allegato)
class AllegatoAdmin(admin.ModelAdmin):
    """Admin per gestire gli allegati"""

    list_display = [
        "nome_originale",
        "content_type",
        "object_id",
        "dimensione_display",
        "uploaded_by",
        "created_at",
    ]
    list_filter = ["content_type", "created_at", "tipo_file"]
    search_fields = ["nome_originale", "descrizione"]
    readonly_fields = [
        "nome_originale",
        "dimensione",
        "tipo_file",
        "created_at",
        "updated_at",
    ]
    date_hierarchy = "created_at"

    fieldsets = (
        (
            "File",
            {
                "fields": ("file", "nome_originale", "dimensione", "tipo_file"),
            },
        ),
        (
            "Collegamento",
            {
                "fields": ("content_type", "object_id"),
            },
        ),
        (
            "Dettagli",
            {
                "fields": ("descrizione", "uploaded_by"),
            },
        ),
        (
            "Timestamp",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def dimensione_display(self, obj):
        """Mostra dimensione formattata"""
        return obj.get_size_display()

    dimensione_display.short_description = "Dimensione"


@admin.register(ModuloRegistry)
class ModuloRegistryAdmin(admin.ModelAdmin):
    """Admin per gestire i moduli del sistema"""

    list_display = [
        "nome",
        "codice",
        "categoria",
        "versione",
        "attivo",
        "obbligatorio",
        "ordine",
    ]
    list_filter = ["categoria", "attivo", "obbligatorio"]
    search_fields = ["nome", "codice", "descrizione"]
    readonly_fields = ["created_at", "updated_at"]

    fieldsets = (
        (
            "Informazioni Base",
            {
                "fields": ("nome", "codice", "app_name", "descrizione"),
            },
        ),
        (
            "Classificazione",
            {
                "fields": ("categoria", "icona", "ordine"),
            },
        ),
        (
            "Stato e Dipendenze",
            {
                "fields": ("attivo", "obbligatorio", "versione", "dipendenze"),
            },
        ),
        (
            "Timestamp",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    actions = ["attiva_moduli", "disattiva_moduli"]

    def attiva_moduli(self, request, queryset):
        """Azione per attivare moduli selezionati"""
        count = 0
        errors = []
        for modulo in queryset:
            try:
                modulo.attiva()
                count += 1
            except Exception as e:
                errors.append(f"{modulo.nome}: {str(e)}")

        if count:
            self.message_user(request, f"{count} moduli attivati con successo")
        if errors:
            self.message_user(request, "Errori: " + ", ".join(errors), level="error")

    attiva_moduli.short_description = "Attiva moduli selezionati"

    def disattiva_moduli(self, request, queryset):
        """Azione per disattivare moduli selezionati"""
        count = 0
        errors = []
        for modulo in queryset.exclude(obbligatorio=True):
            try:
                modulo.disattiva()
                count += 1
            except Exception as e:
                errors.append(f"{modulo.nome}: {str(e)}")

        if count:
            self.message_user(request, f"{count} moduli disattivati con successo")
        if errors:
            self.message_user(request, "Errori: " + ", ".join(errors), level="error")

    disattiva_moduli.short_description = "Disattiva moduli selezionati"


@admin.register(QRCode)
class QRCodeAdmin(admin.ModelAdmin):
    """Admin per gestire i QR Code"""

    list_display = [
        "id",
        "content_type",
        "object_id",
        "url_display",
        "created_by",
        "created_at",
    ]
    list_filter = ["content_type", "created_at"]
    search_fields = ["url", "object_id"]
    readonly_fields = [
        "qr_image_preview",
        "created_at",
        "updated_at",
    ]
    date_hierarchy = "created_at"

    fieldsets = (
        (
            "Collegamento",
            {
                "fields": ("content_type", "object_id"),
            },
        ),
        (
            "QR Code",
            {
                "fields": ("url", "size", "qr_image", "qr_image_preview"),
            },
        ),
        (
            "Tracciamento",
            {
                "fields": ("created_by", "created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def url_display(self, obj):
        """Mostra URL troncato"""
        if len(obj.url) > 50:
            return obj.url[:47] + "..."
        return obj.url

    url_display.short_description = "URL"

    def qr_image_preview(self, obj):
        """Mostra anteprima immagine QR Code"""
        if obj.qr_image:
            from django.utils.html import format_html
            return format_html(
                '<img src="{}" style="max-width: 200px; max-height: 200px;">',
                obj.qr_image.url
            )
        return "Nessuna immagine"

    qr_image_preview.short_description = "Anteprima QR Code"
