"""
Steps de Behave para CU-03: Validar QR.
PEP8 compliant.
"""
import json
from datetime import timedelta

from behave import given, when, then
from django.contrib.contenttypes.models import ContentType
from django.test import Client
from django.utils import timezone

from web.models import BuzonDemanda, Etiqueta


def _crear_buzon():
    return BuzonDemanda.objects.create(
        tipo_promocion='DEMANDA',
        correo_electronico='test@test.com',
        numero_sobres=1,
    )


def _crear_etiqueta(estado=Etiqueta.ESTADO_ETIQUETA_GENERADA, vigente=True):
    buzon = _crear_buzon()
    ct = ContentType.objects.get_for_model(buzon)
    delta = timedelta(hours=1) if vigente else timedelta(hours=-1)
    return Etiqueta.objects.create(
        content_type=ct,
        object_id=buzon.pk,
        estado=estado,
        fecha_caducidad=timezone.now() + delta,
        numero_sobre=1,
    )


# ─── GIVEN ────────────────────────────────────────────────────────────────────

@given('que el hardware escanea el código "{codigo}"')
def step_escanea_codigo(context, codigo):
    context.client = Client()
    context.uuid_str = codigo
    context.etiqueta = None


@given('que existe una etiqueta con estado "{estado}"')
def step_etiqueta_con_estado(context, estado):
    context.client = Client()
    context.etiqueta = _crear_etiqueta(estado=estado)
    context.uuid_str = str(context.etiqueta.uuid)


@given('que existe una etiqueta vigente que ha caducado')
def step_etiqueta_caducada(context):
    context.client = Client()
    context.etiqueta = _crear_etiqueta(vigente=False)
    context.uuid_str = str(context.etiqueta.uuid)


@given('que existe una etiqueta válida y vigente')
def step_etiqueta_valida(context):
    context.client = Client()
    context.etiqueta = _crear_etiqueta()
    context.uuid_str = str(context.etiqueta.uuid)


# ─── WHEN ─────────────────────────────────────────────────────────────────────

@when('consulta la validez del QR')
def step_consulta_validez(context):
    context.response = context.client.get(
        f'/api/validar-qr/{context.uuid_str}/'
    )
    context.response_json = json.loads(context.response.content)


@when('el hardware consulta la validez de esa etiqueta')
def step_consulta_etiqueta(context):
    context.response = context.client.get(
        f'/api/validar-qr/{context.uuid_str}/'
    )
    context.response_json = json.loads(context.response.content)


@when('el hardware envía un POST a validar QR')
def step_post_validar_qr(context):
    context.response = context.client.post(
        f'/api/validar-qr/{context.uuid_str}/'
    )
    context.response_json = {}


# ─── THEN ─────────────────────────────────────────────────────────────────────

@then('la API retorna el código de estado {codigo:d}')
def step_codigo_estado(context, codigo):
    assert context.response.status_code == codigo, (
        f"Se esperaba {codigo}, se obtuvo {context.response.status_code}. "
        f"Respuesta: {context.response.content}"
    )


@then('la respuesta contiene el campo "{campo}"')
def step_contiene_campo(context, campo):
    assert campo in context.response_json, (
        f"El campo '{campo}' no está en la respuesta: {context.response_json}"
    )


@then('la respuesta contiene el mensaje de error "{mensaje}"')
def step_contiene_mensaje_error(context, mensaje):
    assert context.response_json.get('error') == mensaje, (
        f"Se esperaba error '{mensaje}', "
        f"se obtuvo '{context.response_json.get('error')}'"
    )


@then('el estado de la etiqueta en base de datos es "{estado}"')
def step_estado_en_bd(context, estado):
    context.etiqueta.refresh_from_db()
    assert context.etiqueta.estado == estado, (
        f"Se esperaba estado '{estado}', "
        f"se obtuvo '{context.etiqueta.estado}'"
    )