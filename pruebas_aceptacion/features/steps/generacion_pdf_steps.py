"""
Implementación de los steps de Behave para la característica:
'Generación de PDF de etiquetas para el Buzón Electrónico'.

Ejecutar con:
    python manage.py behave --no-input
    -- o --
    behave features/generacion_pdf.feature
"""
import os
import sys
import uuid as uuid_mod
from datetime import time

# Sube desde steps/ -> features/ -> pruebas_aceptacion/ -> raíz del repo
RAIZ = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

# Ahora sí funcionan los imports de Django y del proyecto
from behave import given, when, then
from django.utils import timezone
from web.services.pdf_service import generar_pdf_etiquetas

# ---------------------------------------------------------------------------
# Steps: GIVEN (contexto)
# ---------------------------------------------------------------------------

@given("que el ciudadano ingresó los siguientes datos de trámite de seguimiento:")
def step_datos_seguimiento(context):
    """Carga datos de un trámite de seguimiento desde la tabla Gherkin."""
    tabla = {fila["campo"]: fila["valor"] for fila in context.table}
    context.datos = {
        "tipo_promocion": tabla.get("tipo_promocion", ""),
        "numero_expediente": tabla.get("numero_expediente") or None,
        "anio": int(tabla["anio"]) if tabla.get("anio") else None,
        "ponencia": tabla.get("ponencia") or None,
        "correo_ciudadano": tabla.get("correo_ciudadano", ""),
        "numero_sobres": int(tabla.get("numero_sobres", 1)),
    }
    context.error = None
    context.pdf_bytes = None
    context.etiquetas_meta = None


@given("que el ciudadano ingresó los siguientes datos de trámite inicial:")
def step_datos_inicial(context):
    """Carga datos de un trámite inicial (sin expediente) desde la tabla Gherkin."""
    tabla = {fila["campo"]: fila["valor"] for fila in context.table}
    context.datos = {
        "tipo_promocion": tabla.get("tipo_promocion", ""),
        "numero_expediente": None,
        "anio": None,
        "ponencia": None,
        "correo_ciudadano": tabla.get("correo_ciudadano", ""),
        "numero_sobres": int(tabla.get("numero_sobres", 1)),
    }
    context.error = None
    context.pdf_bytes = None
    context.etiquetas_meta = None


@given("que el ciudadano ingresó los siguientes datos incorrectos:")
def step_datos_incorrectos(context):
    """Carga datos intencionalmente inválidos para escenarios alternativos."""
    tabla = {fila["campo"]: fila["valor"] for fila in context.table}
    context.datos = {
        "tipo_promocion": tabla.get("tipo_promocion", ""),
        "numero_expediente": tabla.get("numero_expediente") or None,
        "anio": int(tabla["anio"]) if tabla.get("anio") else None,
        "ponencia": tabla.get("ponencia") or None,
        "correo_ciudadano": tabla.get("correo_ciudadano", ""),
        "numero_sobres": int(tabla.get("numero_sobres", 1)),
    }
    context.error = None
    context.pdf_bytes = None
    context.etiquetas_meta = None


# ---------------------------------------------------------------------------
# Steps: WHEN (acción)
# ---------------------------------------------------------------------------

@when("el sistema procesa la solicitud de generación de etiquetas")
def step_procesar_solicitud(context):
    """Llama al servicio de generación de PDF y captura resultado o error."""
    try:
        context.pdf_bytes, context.etiquetas_meta = generar_pdf_etiquetas(
            context.datos
        )
        context.error = None
    except ValueError as exc:
        context.error = str(exc)
        context.pdf_bytes = None
        context.etiquetas_meta = None


# ---------------------------------------------------------------------------
# Steps: THEN (verificación – happy paths)
# ---------------------------------------------------------------------------

@then("el sistema retorna un archivo PDF válido")
def step_pdf_valido(context):
    """Verifica que los bytes devueltos sean un PDF real."""
    assert context.pdf_bytes is not None, (
        f"No se generó PDF. Error capturado: {context.error}"
    )
    assert context.pdf_bytes.startswith(b"%PDF"), (
        "Los bytes generados no corresponden a un PDF válido."
    )


@then("el PDF contiene exactamente {n:d} etiqueta generada")
def step_una_etiqueta(context, n):
    """Verifica que se hayan generado exactamente N etiquetas."""
    assert context.etiquetas_meta is not None, "No hay metadatos de etiquetas."
    cantidad = len(context.etiquetas_meta)
    assert cantidad == n, (
        f"Se esperaban {n} etiquetas pero se generaron {cantidad}."
    )


@then("el PDF contiene exactamente {n:d} etiquetas generadas")
def step_n_etiquetas(context, n):
    """Verifica que se hayan generado exactamente N etiquetas (plural)."""
    step_una_etiqueta(context, n)


@then("cada etiqueta tiene un UUID único")
def step_uuid_unico(context):
    """Verifica que ningún UUID se repita entre etiquetas (RN-03)."""
    uuids = [e["uuid"] for e in context.etiquetas_meta]
    assert len(uuids) == len(set(uuids)), (
        "Se encontraron UUIDs duplicados entre las etiquetas generadas."
    )


@then("cada etiqueta tiene un dígito verificador de 6 caracteres")
def step_digito_verificador(context):
    """Verifica que cada dígito verificador tenga exactamente 6 caracteres."""
    for etiqueta in context.etiquetas_meta:
        dv = etiqueta["digito_verificador"]
        assert len(dv) == 6, (
            f"Dígito verificador '{dv}' tiene {len(dv)} caracteres, se esperaban 6."
        )


@then("la fecha de caducidad de cada etiqueta es a las 23:59 del día actual")
def step_fecha_caducidad(context):
    """Verifica que la caducidad de cada etiqueta sea a las 23:59:59 de hoy (RF-04)."""
    hoy = timezone.localdate()
    for etiqueta in context.etiquetas_meta:
        caducidad = etiqueta["fecha_caducidad"]
        assert caducidad.date() == hoy, (
            f"La caducidad ({caducidad.date()}) no corresponde a hoy ({hoy})."
        )
        assert caducidad.time().hour == 23, (
            f"La hora de caducidad debe ser 23, pero es {caducidad.time().hour}."
        )
        assert caducidad.time().minute == 59, (
            f"Los minutos de caducidad deben ser 59, pero son {caducidad.time().minute}."
        )


@then("los números de sobre son consecutivos del 1 al {n:d}")
def step_numeracion_consecutiva(context, n):
    """Verifica que los sobres estén numerados de 1 a N de forma consecutiva."""
    numeros = [e["numero_sobre"] for e in context.etiquetas_meta]
    esperados = list(range(1, n + 1))
    assert numeros == esperados, (
        f"Se esperaba numeración {esperados} pero se obtuvo {numeros}."
    )


# ---------------------------------------------------------------------------
# Steps: THEN (verificación – escenarios alternativos / errores)
# ---------------------------------------------------------------------------

@then("el sistema lanza un error de validación")
def step_error_validacion(context):
    """Verifica que el servicio haya lanzado un error de validación."""
    assert context.error is not None, (
        "Se esperaba un error de validación pero el sistema generó el PDF sin error."
    )
    assert context.pdf_bytes is None, (
        "No debería haberse generado un PDF cuando los datos son inválidos."
    )


@then('el mensaje de error menciona "{fragmento}"')
def step_mensaje_error_contiene(context, fragmento):
    """Verifica que el mensaje de error contenga el fragmento esperado."""
    assert fragmento in context.error, (
        f"El mensaje de error '{context.error}' no contiene '{fragmento}'."
    )
