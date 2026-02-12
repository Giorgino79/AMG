"""
Views per la gestione dei QR Code.
Sistema completo per generare, visualizzare e scaricare QR Code collegati a qualsiasi oggetto.
"""

from django.http import JsonResponse, FileResponse, Http404
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.files.base import ContentFile
from django.urls import reverse
from .models_legacy import QRCode
from qr_code.qrcode.maker import make_qr_code_image
from qr_code.qrcode.utils import QRCodeOptions
from io import BytesIO


# ============================================================================
# QR CODE VIEWS
# ============================================================================


@login_required
@require_http_methods(["POST"])
def qrcode_generate(request):
    """
    Genera o recupera un QR Code per un oggetto specifico.

    POST parameters:
        - content_type: ID del ContentType
        - object_id: ID dell'oggetto

    Returns:
        JSON con dati del QR Code creato/esistente
    """
    try:
        content_type_id = request.POST.get("content_type")
        object_id = request.POST.get("object_id")

        if not content_type_id or not object_id:
            return JsonResponse({"error": "Parametri mancanti"}, status=400)

        # Recupera ContentType
        try:
            content_type = ContentType.objects.get(pk=content_type_id)
        except ContentType.DoesNotExist:
            return JsonResponse({"error": "Tipo contenuto non valido"}, status=400)

        # Verifica se esiste già un QR Code per questo oggetto
        try:
            qr_obj = QRCode.objects.get(
                content_type=content_type,
                object_id=object_id
            )
            created = False
            # Verifica se l'immagine esiste
            has_image = bool(qr_obj.qr_image) and qr_obj.qr_image.name
        except QRCode.DoesNotExist:
            qr_obj = None
            created = True
            has_image = False

        # Se non esiste o manca l'immagine, genera l'immagine QR
        if not qr_obj or not has_image:
            # Recupera l'oggetto reale per costruire l'URL
            obj = content_type.get_object_for_this_type(pk=object_id)

            # Costruisce URL assoluto all'oggetto
            # Prova a usare get_absolute_url() se esiste, altrimenti usa admin URL
            if hasattr(obj, 'get_absolute_url'):
                obj_url = obj.get_absolute_url()
            else:
                # Fallback: URL admin
                obj_url = reverse(
                    f'admin:{content_type.app_label}_{content_type.model}_change',
                    args=[object_id]
                )

            # URL assoluto completo
            full_url = request.build_absolute_uri(obj_url)

            # Genera QR Code usando django-qr-code
            options = QRCodeOptions(
                size=10,
                border=4,
                image_format='png',
                dark_color='black',
                light_color='white',
            )
            image_bytes = make_qr_code_image(full_url, options)

            # Nome file
            filename = f"qr_{content_type.model}_{object_id}.png"

            if qr_obj:
                # Aggiorna QR esistente senza immagine
                qr_obj.url = full_url
                qr_obj.qr_image.save(filename, ContentFile(image_bytes), save=False)
                qr_obj.save()
            else:
                # Crea nuovo QR con tutti i campi obbligatori
                qr_obj = QRCode(
                    content_type=content_type,
                    object_id=object_id,
                    url=full_url,
                    created_by=request.user
                )
                qr_obj.qr_image.save(filename, ContentFile(image_bytes), save=False)
                qr_obj.save()

        # Restituisci dati QR Code
        return JsonResponse({
            "success": True,
            "qrcode": {
                "id": qr_obj.pk,
                "url": qr_obj.url,
                "image_url": qr_obj.qr_image.url,
                "created_at": qr_obj.created_at.strftime("%d/%m/%Y %H:%M"),
                "created": created,
            }
        })

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def qrcode_download(request, qrcode_id):
    """
    Download dell'immagine QR Code.

    URL: /core/qrcode/<id>/download/
    """
    try:
        qr_obj = QRCode.objects.get(pk=qrcode_id)

        # FileResponse gestisce automaticamente il download
        response = FileResponse(
            qr_obj.qr_image.open("rb"),
            as_attachment=True,
            filename=f"qrcode_{qr_obj.pk}.png",
        )

        return response

    except QRCode.DoesNotExist:
        raise Http404("QR Code non trovato")
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@login_required
@require_http_methods(["DELETE", "POST"])  # POST per compatibilità browser
def qrcode_delete(request, qrcode_id):
    """
    Elimina un QR Code.

    URL: /core/qrcode/<id>/delete/
    """
    try:
        qr_obj = QRCode.objects.get(pk=qrcode_id)

        # Elimina (il file immagine viene eliminato automaticamente tramite override delete())
        qr_obj.delete()

        return JsonResponse({
            "success": True,
            "message": "QR Code eliminato con successo"
        })

    except QRCode.DoesNotExist:
        return JsonResponse({"error": "QR Code non trovato"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def qrcode_check(request):
    """
    Verifica se esiste un QR Code per un oggetto specifico.

    GET parameters:
        - content_type: ID del ContentType
        - object_id: ID dell'oggetto

    Returns:
        JSON con informazioni sul QR Code se esiste
    """
    try:
        content_type_id = request.GET.get("content_type")
        object_id = request.GET.get("object_id")

        if not content_type_id or not object_id:
            return JsonResponse({"error": "Parametri mancanti"}, status=400)

        # Cerca QR Code esistente
        try:
            qr_obj = QRCode.objects.get(
                content_type_id=content_type_id,
                object_id=object_id
            )

            # Verifica se l'immagine esiste
            has_image = bool(qr_obj.qr_image) and qr_obj.qr_image.name
            if not has_image:
                # QR esiste ma immagine mancante, trattalo come non esistente
                return JsonResponse({
                    "success": True,
                    "exists": False
                })

            return JsonResponse({
                "success": True,
                "exists": True,
                "qrcode": {
                    "id": qr_obj.pk,
                    "url": qr_obj.url,
                    "image_url": qr_obj.qr_image.url,
                    "created_at": qr_obj.created_at.strftime("%d/%m/%Y %H:%M"),
                }
            })
        except QRCode.DoesNotExist:
            return JsonResponse({
                "success": True,
                "exists": False
            })

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
