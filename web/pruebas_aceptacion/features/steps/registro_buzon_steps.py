from behave import given, when, then
from django.test import Client
from django.urls import reverse


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _post_buzon(context):
    """Envía el formulario acumulado en context.payload vía POST."""
    context.response = context.client.post(
        reverse('buzon_crear'),
        data=context.payload,
        follow=True,
    )


# ─── GIVEN ────────────────────────────────────────────────────────────────────

@given('que el usuario abre el formulario de registro')
def step_abre_formulario(context):
    context.client  = Client()
    context.payload = {}
    response = context.client.get(reverse('buzon_crear'))
    assert response.status_code == 200, (
        f"Se esperaba 200 al abrir el formulario, se obtuvo {response.status_code}"
    )


@given('selecciona el tipo de promoción "{tipo}"')
def step_selecciona_tipo(context, tipo):
    context.payload['tipo_promocion'] = tipo

    tipos_con_expediente = {
        'CONTESTACION', 'ALEGATOS', 'INFORME_AUTORIDAD',
        'RECURSO', 'INCIDENTE', 'AMPARO', 'EXPEDIENTE_RAG', 'OTROS',
    }
    if tipo in tipos_con_expediente:
        ajax_url = reverse('buzon_form_parcial') + f'?tipo={tipo}'
        ajax_resp = context.client.get(ajax_url)
        assert ajax_resp.status_code == 200, (
            f"La vista parcial devolvió {ajax_resp.status_code} para tipo={tipo}"
        )


# ─── WHEN ─────────────────────────────────────────────────────────────────────

@when('llena el correo "{correo}" y lo confirma con "{confirmacion}"')
def step_llena_correo(context, correo, confirmacion):
    context.payload['correo_electronico']              = correo
    context.payload['correo_electronico_confirmacion'] = confirmacion


@when('llena el número de sobres con {numero:d}')
def step_llena_sobres(context, numero):
    context.payload['numero_sobres'] = numero


@when('llena el número de expediente "{expediente}" con año {anio:d} y ponencia "{ponencia}"')
def step_llena_expediente(context, expediente, anio, ponencia):
    context.payload['numero_expediente'] = expediente
    context.payload['anio']              = anio
    context.payload['ponencia']          = ponencia


@when('especifica "{texto}"')
def step_especifica(context, texto):
    context.payload['especifique'] = texto


@when('envía el formulario')
def step_envia_formulario(context):
    _post_buzon(context)


# ─── THEN ─────────────────────────────────────────────────────────────────────

@then('el sistema guarda el registro exitosamente')
def step_registro_exitoso(context):
    assert context.response.status_code == 200, (
        f"Se esperaba redirección exitosa (200), se obtuvo {context.response.status_code}"
    )
    assert 'form' in context.response.context, (
        "El contexto no contiene 'form' tras guardar; revisa la redirección."
    )


@then('muestra el mensaje "{mensaje}"')
def step_muestra_mensaje(context, mensaje):
    messages = [str(m) for m in context.response.context['messages']]
    assert mensaje in messages, (
        f"Mensaje esperado: '{mensaje}'\nMensajes presentes: {messages}"
    )


@then('el formulario muestra los campos de expediente')
def step_muestra_campos_expediente(context):
    tipo    = context.payload.get('tipo_promocion', '')
    url     = reverse('buzon_form_parcial') + f'?tipo={tipo}'
    resp    = context.client.get(url)
    content = resp.content.decode('utf-8')
    assert resp.status_code == 200
    for campo in ['numero_expediente', 'anio', 'ponencia']:
        assert campo in content, (
            f"El campo '{campo}' no aparece en la respuesta parcial para tipo={tipo}"
        )


@then('el formulario no muestra campos de expediente')
def step_no_muestra_campos_expediente(context):
    tipo    = context.payload.get('tipo_promocion', 'DEMANDA')
    url     = reverse('buzon_form_parcial') + f'?tipo={tipo}'
    resp    = context.client.get(url)
    content = resp.content.decode('utf-8')
    assert resp.status_code == 200
    for campo in ['numero_expediente', 'anio', 'ponencia']:
        assert campo not in content, (
            f"El campo '{campo}' no debería aparecer para tipo={tipo}"
        )