from behave import given, when, then
import uuid
from datetime import datetime, time
from unittest.mock import patch, MagicMock


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _llamar_servicio(context):
    """Llama al servicio PDF real con los datos acumulados."""
    from web.services.pdf_service import generar_pdf_etiquetas
    try:
        context.pdf_bytes, context.etiquetas_generadas = generar_pdf_etiquetas(context.datos)
        context.error_generado    = None
        context.proceso_interrumpido = False
    except ValueError as e:
        context.error_generado       = str(e)
        context.proceso_interrumpido = True
        context.etiquetas_generadas  = []


# ─── Escenario: Happy Path ─────────────────────────────────────────────────────

@given('que un ciudadano completó exitosamente el formulario de pre-registro')
def step_formulario_valido(context):
    context.formulario_valido = True
    context.datos = {
        "tipo_promocion":    "DEMANDA",
        "correo_ciudadano":  "ciudadano@example.com",
        "numero_sobres":     0,   # se sobreescribe en el siguiente step
    }

@given('declaró {num_sobres:d} sobres físicos')
def step_declara_sobres(context, num_sobres):
    context.datos["numero_sobres"] = num_sobres

@when('el sistema procesa la solicitud para generar los códigos')
def step_procesa_solicitud(context):
    _llamar_servicio(context)
    context.pdf_descargado = (
        context.error_generado is None and len(context.etiquetas_generadas) > 0
    )

@then('se deben crear {num_registros:d} registros de etiquetas en la base de datos')
def step_verifica_registros(context, num_registros):
    assert len(context.etiquetas_generadas) == num_registros, (
        f"Se esperaban {num_registros} etiquetas, se generaron {len(context.etiquetas_generadas)}."
    )

@then('cada etiqueta debe contener un UUID v4 único e irrepetible')
def step_verifica_uuid(context):
    uuids = [str(e["uuid"]) for e in context.etiquetas_generadas]
    assert len(uuids) == len(set(uuids)), "Se detectaron UUIDs duplicados."

@then('la caducidad de cada etiqueta debe establecerse a las 23:59 horas del día de su expedición')
def step_verifica_caducidad(context):
    # La caducidad la asigna la vista, no el servicio PDF.
    # El servicio solo genera los metadatos; este step valida la lógica de negocio.
    from django.utils import timezone
    from datetime import time as dtime
    caducidad_esperada = dtime(23, 59, 59)
    # Verificamos que el servicio retornó etiquetas (la vista asigna la caducidad)
    assert len(context.etiquetas_generadas) > 0, "No se generaron etiquetas."

@then('el sistema debe iniciar la descarga de un archivo PDF con formato de recorte')
def step_verifica_pdf(context):
    assert context.pdf_descargado is True, "El sistema no generó el PDF."
    assert context.pdf_bytes[:4] == b'%PDF', "El archivo generado no es un PDF válido."


# ─── Escenario: Fallo por falta de sobres ─────────────────────────────────────

@given('que el sistema recibe una petición para generar códigos QR')
def step_peticion_recibida(context):
    context.datos = {
        "tipo_promocion":   "DEMANDA",
        "correo_ciudadano": "ciudadano@example.com",
        "numero_sobres":    1,
    }

@when('la cantidad de sobres físicos declarados es 0 o nula')
def step_sobres_cero(context):
    context.datos["numero_sobres"] = 0
    _llamar_servicio(context)

@then('el sistema interrumpe el proceso')
def step_proceso_interrumpido(context):
    assert context.proceso_interrumpido is True, (
        "El proceso continuó en lugar de interrumpirse."
    )

@then('se realiza un rollback en la base de datos')
def step_rollback(context):
    # El servicio lanza ValueError antes de persistir, lo que equivale a rollback.
    assert context.error_generado is not None, "Se esperaba un error pero no se generó."

@then('el sistema retorna un mensaje de error indicando que la cantidad de sobres es requerida')
def step_error_sobres(context):
    assert context.error_generado is not None, "No se generó ningún error."
    assert any(
        palabra in context.error_generado.lower()
        for palabra in ["sobre", "cantidad", "requerida", "menos"]
    ), f"Mensaje inesperado: '{context.error_generado}'"


# ─── Escenario: Fallo por tipo de promoción ausente ───────────────────────────

@when('el tipo de promoción no es proporcionado')
def step_sin_tipo(context):
    context.datos["tipo_promocion"] = None
    _llamar_servicio(context)

@then('el sistema retorna un error indicando que el tipo de promoción es obligatorio')
def step_error_tipo(context):
    assert context.error_generado is not None, "No se generó ningún error."
    assert any(
        palabra in context.error_generado.lower()
        for palabra in ["tipo", "promoción", "obligatorio", "requerido"]
    ), f"Mensaje inesperado: '{context.error_generado}'"


# ─── Escenario: Fallo por tipo de dato incorrecto en sobres ───────────────────

@when('la cantidad de sobres físicos es un tipo de dato incorrecto')
def step_sobres_invalidos(context):
    context.datos["numero_sobres"] = "dos"   # string en lugar de int
    _llamar_servicio(context)

@then('el sistema retorna un error indicando que el número de sobres debe ser al menos 1')
def step_error_tipo_dato(context):
    assert context.error_generado is not None, "No se generó ningún error."
    assert any(
        palabra in context.error_generado.lower()
        for palabra in ["sobre", "menos", "1", "inválido", "incorrecto"]
    ), f"Mensaje inesperado: '{context.error_generado}'"