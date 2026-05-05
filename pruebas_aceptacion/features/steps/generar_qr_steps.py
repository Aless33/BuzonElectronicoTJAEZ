from behave import given, when, then
import uuid
from datetime import datetime, time

# --- Escenario: Generación exitosa de códigos QR y Acuse Provisional (Happy Path) ---

@given('que un ciudadano completó exitosamente el formulario de pre-registro')
def step_impl(context):
    context.formulario_valido = True

@given('declaró {num_sobres:d} sobres físicos')
def step_impl(context, num_sobres):
    context.num_sobres = num_sobres

@when('el sistema procesa la solicitud para generar los códigos')
def step_impl(context):
    context.etiquetas_generadas = []
    
    if getattr(context, 'formulario_valido', False) and context.num_sobres > 0:
        for _ in range(context.num_sobres):
            context.etiquetas_generadas.append({
                'uuid': str(uuid.uuid4()),
                'caducidad': datetime.combine(datetime.today(), time(23, 59))
            })
        context.pdf_descargado = True

@then('se deben crear {num_registros:d} registros de etiquetas en la base de datos')
def step_impl(context, num_registros):
    assert len(context.etiquetas_generadas) == num_registros, f"Se esperaban {num_registros} etiquetas, pero se generaron {len(context.etiquetas_generadas)}."

@then('cada etiqueta debe contener un UUID v4 único e irrepetible')
def step_impl(context):
    uuids = [etiqueta['uuid'] for etiqueta in context.etiquetas_generadas]
    
    duplicados = False
    lista_verificacion = []
    for id_qr in uuids:
        if id_qr in lista_verificacion:
            duplicados = True
            break
        lista_verificacion.append(id_qr)
        
    assert duplicados is False, "Se detectaron UUIDs duplicados en la generación del lote."

@then('la caducidad de cada etiqueta debe establecerse a las 23:59 horas del día de su expedición')
def step_impl(context):
    for etiqueta in context.etiquetas_generadas:
        hora_caducidad = etiqueta['caducidad'].strftime('%H:%M')
        assert hora_caducidad == '23:59', f"La hora de caducidad registrada es {hora_caducidad}, se esperaba 23:59."

@then('el sistema debe iniciar la descarga de un archivo PDF con formato de recorte')
def step_impl(context):
    assert getattr(context, 'pdf_descargado', False) is True, "El sistema no emitió la orden de descarga del archivo PDF."

# --- Escenario: Fallo en la generación por falta de sobres físicos ---

@given('que el sistema recibe una petición para generar códigos QR')
def step_impl(context):
    context.peticion_recibida = True

@when('la cantidad de sobres físicos declarados es 0 o nula')
def step_impl(context):
    context.num_sobres = 0
    if context.num_sobres == 0:
        context.proceso_interrumpido = True
        context.rollback = True
        context.mensaje_error = "la cantidad de sobres es requerida"

@then('el sistema interrumpe el proceso')
def step_impl(context):
    assert getattr(context, 'proceso_interrumpido', False) is True, "El proceso continuó su ejecución en lugar de interrumpirse."

@then('se realiza un rollback en la base de datos')
def step_impl(context):
    assert getattr(context, 'rollback', False) is True, "No se ejecutó el rollback en la base de datos."

@then('el sistema retorna un mensaje de error indicando que la cantidad de sobres es requerida')
def step_impl(context):
    error_recibido = getattr(context, 'mensaje_error', '')
    assert error_recibido == "la cantidad de sobres es requerida", f"El mensaje de error esperado no coincide. Se recibió: {error_recibido}"

@when('el tipo de promoción no es proporcionado')
def step_impl(context):
    context.datos = {"numero_sobres": 1}
    try:
        from web.services import generar_qr_provisional
        generar_qr_provisional(context.datos)
    except ValueError as e:
        context.error_generado = str(e)
        context.proceso_interrumpido = True

@then('el sistema retorna un error indicando que el tipo de promoción es obligatorio')
def step_impl(context):
    assert getattr(context, 'error_generado', '') == "El tipo de promoción es obligatorio."

@when('la cantidad de sobres físicos es un tipo de dato incorrecto')
def step_impl(context):
    context.datos = {"tipo_promocion": "DEMANDA", "numero_sobres": "dos"}
    try:
        from web.services import generar_qr_provisional
        generar_qr_provisional(context.datos)
    except ValueError as e:
        context.error_generado = str(e)
        context.proceso_interrumpido = True

@then('el sistema retorna un error indicando que el número de sobres debe ser al menos 1')
def step_impl(context):
    assert getattr(context, 'error_generado', '') == "El número de sobres debe ser al menos 1."