from io import BytesIO
from qr_code.qrcode.maker import make_qr_code_image
from qr_code.qrcode.utils import QRCodeOptions


def generate_qr_code(data, box_size=10, border=4, fill_color="black", back_color="white"):
    """
    Genera un QR Code dai dati forniti.

    Args:
        data: Stringa o URL da codificare
        box_size: Dimensione di ogni singolo quadrato del QR
        border: Spessore del bordo
        fill_color: Colore del QR
        back_color: Colore dello sfondo

    Returns:
        BytesIO: Buffer contenente l'immagine PNG
    """
    # Configura opzioni QR Code
    options = QRCodeOptions(
        size=box_size,
        border=border,
        image_format='png',
        dark_color=fill_color,
        light_color=back_color,
    )

    # Genera immagine QR Code
    image_bytes = make_qr_code_image(data, options)

    buffer = BytesIO(image_bytes)
    buffer.seek(0)
    return buffer
