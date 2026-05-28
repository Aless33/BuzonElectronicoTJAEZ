import io
import uuid
import qrcode
from datetime import time
from django.utils import timezone

def _calcular_caducidad() -> object:
    hoy = timezone.localdate()
    fin_dia = time(23, 59, 59)
    caducidad_naive = timezone.datetime.combine(hoy, fin_dia)
    return timezone.make_aware(caducidad_naive)

def generar_qr_provisional(datos_promocion: dict) -> tuple[bytes, dict]:
    """
    Genera un código QR en formato PNG y devuelve sus bytes junto con los metadatos.
    """
    if not datos_promocion.get("tipo_promocion"):
        raise ValueError("El tipo de promoción es obligatorio.")
    
    numero_sobres = datos_promocion.get("numero_sobres", 0)
    if not isinstance(numero_sobres, int) or numero_sobres < 1:
        raise ValueError("El número de sobres debe ser al menos 1.")

    uid = str(uuid.uuid4())
    caducidad = _calcular_caducidad()

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=6,
        border=2,
    )
    qr.add_data(uid)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    qr_bytes = buffer.getvalue()
    buffer.close()

    metadatos = {
        "uuid": uid,
        "fecha_caducidad": caducidad,
    }

    return qr_bytes, metadatos