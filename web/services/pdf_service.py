"""
Servicio de generación de PDF para el Buzón Electrónico TJAEZ.

Implementa RF-02, RF-03 y RF-04 del SRS:
  - RF-02: Genera UUID v4 + dígito verificador por sobre.
  - RF-03: PDF con dos secciones por sobre.
  - RF-04: Caducidad a las 23:59 hrs del día de emisión.

El PDF resultante imita el formato físico observado:
  dos tarjetas recortables lado a lado con líneas punteadas,
  logo del tribunal, QR en la etiqueta izquierda y datos en ambas.
"""

import io
import random
import string
import uuid
from datetime import time

import qrcode
from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas


ANCHO_PAGINA, ALTO_PAGINA = letter

ANCHO_TARJETA = 8.0 * cm
ALTO_TARJETA = 11.0 * cm
MARGEN_HORIZONTAL = 1.5 * cm
SEPARACION_TARJETAS = 0.8 * cm
MARGEN_SUPERIOR = ALTO_PAGINA - 2.0 * cm

COLOR_LINEA_PUNTEADA = colors.HexColor("#888888")
COLOR_TITULO = colors.HexColor("#1a1a1a")
COLOR_ACENTO = colors.HexColor("#000000")

FUENTE_NORMAL = "Helvetica"
FUENTE_BOLD = "Helvetica-Bold"


def _generar_digito_verificador() -> str:
    """Genera un código alfanumérico corto de 6 caracteres."""
    caracteres = string.ascii_uppercase + string.digits
    return "".join(random.choices(caracteres, k=6))


def _calcular_caducidad() -> object:
    """
    Retorna el datetime de caducidad a las 23:59:59 del día actual.

    Usa timezone-aware para respetar la zona horaria configurada en Django.
    """
    hoy = timezone.localdate()
    fin_dia = time(23, 59, 59)
    caducidad_naive = timezone.datetime.combine(hoy, fin_dia)
    return timezone.make_aware(caducidad_naive)


def _generar_imagen_qr(uuid_str: str) -> ImageReader:
    """
    Genera un código QR en memoria a partir del UUID.

    Devuelve un ImageReader compatible con ReportLab.
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=6,
        border=2,
    )
    qr.add_data(uuid_str)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return ImageReader(buffer)


def _dibujar_lineas_punteadas(
    c: canvas.Canvas,
    x: float,
    y: float,
    ancho: float,
    alto: float,
) -> None:
    """
    Dibuja el rectángulo de líneas punteadas que delimita cada tarjeta.
    """
    c.saveState()
    c.setStrokeColor(COLOR_LINEA_PUNTEADA)
    c.setLineWidth(0.5)
    c.setDash(3, 3)
    c.rect(x, y, ancho, alto)
    c.restoreState()


def _dibujar_icono_tijeras(c: canvas.Canvas, x: float, y: float) -> None:
    """Dibuja un símbolo de tijeras en la esquina superior."""
    c.saveState()
    c.setFont(FUENTE_NORMAL, 10)
    c.setFillColor(COLOR_LINEA_PUNTEADA)
    c.drawString(x, y, "✂")
    c.restoreState()


def _dibujar_encabezado_tribunal(
    c: canvas.Canvas,
    x: float,
    y: float,
    ancho: float,
) -> float:
    """
    Dibuja el encabezado del Tribunal de Justicia Administrativa.

    Retorna la nueva coordenada Y tras el encabezado.
    """
    c.saveState()

    c.setFont(FUENTE_BOLD, 6.5)
    c.setFillColor(COLOR_TITULO)
    linea1 = "TRIBUNAL DE JUSTICIA"
    linea2 = "ADMINISTRATIVA"
    linea3 = "ZACATECAS"

    centro = x + ancho / 2
    c.drawCentredString(centro, y, linea1)
    c.drawCentredString(centro, y - 8, linea2)
    c.setFont(FUENTE_NORMAL, 5.5)
    c.drawCentredString(centro, y - 15, linea3)

    c.restoreState()
    return y - 22


def _dibujar_datos_tramite(
    c: canvas.Canvas,
    x: float,
    y: float,
    ancho: float,
    datos: dict,
) -> None:
    """
    Dibuja los datos del trámite centrados dentro de la tarjeta.
    """
    c.saveState()
    centro = x + ancho / 2

    lineas = [
        (
            FUENTE_NORMAL,
            8,
            f"Expediente: {datos.get('numero_expediente', 'N/A')}",
        ),
        (
            FUENTE_NORMAL,
            8,
            f"Año: {datos.get('anio', 'N/A')}",
        ),
        (
            FUENTE_BOLD,
            8,
            datos.get("ponencia", "SIN PONENCIA").upper(),
        ),
        (
            FUENTE_NORMAL,
            8,
            f"Fecha: {datos.get('fecha', '')}",
        ),
        (
            FUENTE_NORMAL,
            8,
            f"Sobre {datos.get('numero_sobre', 1)} "
            f"de {datos.get('total_sobres', 1)}",
        ),
    ]

    cursor_y = y
    for fuente, tamaño, texto in lineas:
        c.setFont(fuente, tamaño)
        c.setFillColor(COLOR_ACENTO)
        c.drawCentredString(centro, cursor_y, texto)
        cursor_y -= 13

    c.restoreState()


def _dibujar_etiqueta_sobre(
    c: canvas.Canvas,
    x: float,
    y_inferior: float,
    datos: dict,
) -> None:
    """
    Dibuja la sección izquierda: ETIQUETA SOBRE con QR y datos.
    """
    ancho = ANCHO_TARJETA
    alto = ALTO_TARJETA

    _dibujar_lineas_punteadas(c, x, y_inferior, ancho, alto)
    _dibujar_icono_tijeras(c, x + 2, y_inferior + alto - 10)

    cursor_y = _dibujar_encabezado_tribunal(
        c,
        x + 5,
        y_inferior + alto - 15,
        ancho - 10,
    )
    cursor_y -= 5

    qr_img = _generar_imagen_qr(datos["uuid"])
    qr_size = 3.5 * cm
    qr_x = x + (ancho - qr_size) / 2

    c.drawImage(
        qr_img,
        qr_x,
        cursor_y - qr_size,
        width=qr_size,
        height=qr_size,
        preserveAspectRatio=True,
    )
    cursor_y -= qr_size + 8

    _dibujar_datos_tramite(c, x + 5, cursor_y, ancho - 10, datos)

    c.saveState()
    c.setFont(FUENTE_BOLD, 9)
    c.setFillColor(COLOR_ACENTO)
    c.drawCentredString(x + ancho / 2, y_inferior + 12, "ETIQUETA SOBRE")
    c.restoreState()


def _dibujar_acuse_provisional(
    c: canvas.Canvas,
    x: float,
    y_inferior: float,
    datos: dict,
) -> None:
    """
    Dibuja la sección derecha: ACUSE PROVISIONAL sin QR.
    """
    ancho = ANCHO_TARJETA
    alto = ALTO_TARJETA

    _dibujar_lineas_punteadas(c, x, y_inferior, ancho, alto)
    _dibujar_icono_tijeras(c, x + 2, y_inferior + alto - 10)

    cursor_y = _dibujar_encabezado_tribunal(
        c,
        x + 5,
        y_inferior + alto - 15,
        ancho - 10,
    )
    cursor_y -= 3.5 * cm + 20

    _dibujar_datos_tramite(c, x + 5, cursor_y, ancho - 10, datos)

    c.saveState()
    c.setFont(FUENTE_BOLD, 9)
    c.setFillColor(COLOR_ACENTO)
    c.drawCentredString(x + ancho / 2, y_inferior + 12, "ACUSE PROVISIONAL")
    c.restoreState()


def generar_pdf_etiquetas(datos_promocion: dict) -> tuple[bytes, list[dict]]:
    """
    Genera el PDF de etiquetas y retorna los metadatos generados.

    Args:
        datos_promocion: Diccionario con los datos validados del formulario.

    Returns:
        Tupla con los bytes del PDF y la lista de metadatos de etiquetas.

    Raises:
        ValueError: Si los datos de entrada no son válidos.
    """
    _validar_datos(datos_promocion)

    numero_sobres = datos_promocion["numero_sobres"]
    fecha_hoy = timezone.localdate().strftime("%Y-%m-%d")
    caducidad = _calcular_caducidad()

    etiquetas_meta = []
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)

    for numero_sobre in range(1, numero_sobres + 1):
        uid = str(uuid.uuid4())
        digito = _generar_digito_verificador()

        etiquetas_meta.append({
            "uuid": uid,
            "digito_verificador": digito,
            "fecha_caducidad": caducidad,
            "numero_sobre": numero_sobre,
        })

        numero_expediente = (
            datos_promocion.get("numero_expediente") or "N/A"
        )
        ponencia = datos_promocion.get("ponencia") or "SIN PONENCIA"

        datos_tarjeta = {
            "uuid": uid,
            "digito_verificador": digito,
            "numero_expediente": numero_expediente,
            "anio": datos_promocion.get("anio") or "N/A",
            "ponencia": ponencia,
            "fecha": fecha_hoy,
            "numero_sobre": numero_sobre,
            "total_sobres": numero_sobres,
        }

        y_inferior = MARGEN_SUPERIOR - ALTO_TARJETA
        x_etiqueta = MARGEN_HORIZONTAL
        x_acuse = (
            MARGEN_HORIZONTAL
            + ANCHO_TARJETA
            + SEPARACION_TARJETAS
        )

        _dibujar_etiqueta_sobre(c, x_etiqueta, y_inferior, datos_tarjeta)
        _dibujar_acuse_provisional(c, x_acuse, y_inferior, datos_tarjeta)

        if numero_sobre < numero_sobres:
            c.showPage()

    c.save()
    pdf_bytes = buffer.getvalue()
    buffer.close()

    return pdf_bytes, etiquetas_meta


TIPOS_INICIALES = {
    "DEMANDA",
    "EXPEDIENTE_RAG_INICIAL",
}

TIPOS_VALIDOS = {
    "DEMANDA",
    "EXPEDIENTE_RAG_INICIAL",
    "CONTESTACION",
    "ALEGATOS",
    "INFORME_AUTORIDAD",
    "RECURSO",
    "INCIDENTE",
    "AMPARO",
    "EXPEDIENTE_RAG",
    "OTROS",
}


def _validar_datos(datos: dict) -> None:
    """
    Valida las reglas de negocio antes de generar el PDF.

    Raises:
        ValueError: Con un mensaje descriptivo si alguna regla falla.
    """
    tipo = datos.get("tipo_promocion", "")

    if not tipo:
        raise ValueError("El tipo de promoción es obligatorio.")

    if tipo not in TIPOS_VALIDOS:
        raise ValueError(f"Tipo de promoción inválido: '{tipo}'.")

    if tipo in TIPOS_INICIALES:
        tiene_expediente = datos.get("numero_expediente")
        tiene_anio = datos.get("anio")
        tiene_ponencia = datos.get("ponencia")

        if tiene_expediente or tiene_anio or tiene_ponencia:
            raise ValueError(
                "Los trámites iniciales no deben incluir número de "
                "expediente, año ni ponencia."
            )
    else:
        if not datos.get("numero_expediente"):
            raise ValueError(
                "El número de expediente es obligatorio para este "
                "tipo de trámite."
            )

        if not datos.get("anio"):
            raise ValueError("El año del expediente es obligatorio.")

    correo = datos.get("correo_ciudadano", "")

    if not correo or "@" not in correo:
        raise ValueError("Se requiere un correo electrónico válido.")

    numero_sobres = datos.get("numero_sobres", 0)

    if not isinstance(numero_sobres, int) or numero_sobres < 1:
        raise ValueError("El número de sobres debe ser al menos 1.")

    if numero_sobres > 20:
        raise ValueError(
            "El número de sobres no puede exceder 20 por solicitud."
        )
