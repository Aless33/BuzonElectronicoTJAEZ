"""
Steps de Behave para CU-04: Confirmar Depósito Físico.
PEP8 compliant.
"""
import json
from datetime import timedelta

from behave import given, when, then
from django.contrib.contenttypes.models import ContentType
from django.test import Client
from django.utils import timezone

from web.models import BuzonDemanda, Etiqueta


def _crear_etiqueta(estado=Etiqueta.ESTADO_ETIQUETA_GENERADA, vigente=True):
    buzon = BuzonDemanda.objects.create(
        tipo_promocion='DEMANDA',
        correo_electronico='test@test.com',
        numero_sobres=1,
    )
    ct = ContentType.objects.get_for_model(buzon)
    delta = timedelta(hours=1) if vigente else timedelta(hours=-1)
    return Etiqueta.objects.create(
        content_type=ct,
        object_id=buzon.pk,
        estado=estado,
        fecha_caducidad=timezone.now() + delta,
        numero_sobre=1,
    )


def _post_deposito(client, uuid_str, body):
    return client.post(
        f'/api/confirmar-deposito/{uuid_str}/',
        data=json.dumps(body),
        content_type='application/json',
    )


# ─── GIVEN ────────────────────────────────────────────────────────────────────

@given('que el sensor detecta el depósito del sobre con UUID "{uuid_str}"')
def step_sensor_uuid(context, uuid_str):
    context.client = Client()
    context.uuid_str = uuid_str
    context.etiqueta = None


@given('que existe una etiqueta válida y vigente para depósito')
def step_etiqueta_valida_deposito(context):
    context.client = Client()
    context.etiqueta = _crear_etiqueta()
    context.uuid_str = str(context.etiqueta.uuid)


@given('que existe una etiqueta con estado "{estado}" para depósito')
def step_etiqueta_estado_deposito(context, estado):
    context.client = Client()
    context.etiqueta = _crear_etiqueta(estado=estado)
    context.uuid_str = str(context.etiqueta.uuid)


@given('que existe una etiqueta caducada para depósito')
def step_etiqueta_caducada_deposito(context):
    context.client = Client()
    context.etiqueta = _crear_etiqueta(vigente=False)
    context.uuid_str = str(context.etiqueta.uuid)


# ─── WHEN ─────────────────────────────────────────────────────────────────────

@when('el hardware confirma el depósito con sensor en true')
def step_confirma_sensor_true(context):
    context.response = _post_deposito(
        context.client,
        context.uuid_str,
        {'sensor_confirmado': True},
    )
    context.response_json = json.loads(context.response.content)


@when('el hardware confirma el depósito con sensor en true para esa etiqueta')
def step_confirma_sensor_true_etiqueta(context):
    context.response = _post_deposito(
        context.client,
        context.uuid_str,
        {'sensor_confirmado': True},
    )
    context.response_json = json.loads(context.response.content)


@when('el hardware envía un cuerpo JSON inválido')
def step_json_invalido(context):
    context.response = context.client.post(
        f'/api/confirmar-deposito/{context.uuid_str}/',
        data='esto no es json',
        content_type='application/json',
    )
    context.response_json = json.loads(context.response.content)


@when('el hardware confirma el depósito sin el campo sensor')
def step_sin_campo_sensor(context):
    context.response = _post_deposito(context.client, context.uuid_str, {})
    context.response_json = json.loads(context.response.content)


@when('el hardware confirma el depósito con sensor en false')
def step_sensor_false(context):
    context.response = _post_deposito(
        context.client,
        context.uuid_str,
        {'sensor_confirmado': False},
    )
    context.response_json = json.loads(context.response.content)


@when('el hardware envía un GET a confirmar depósito')
def step_get_confirmar(context):
    context.response = context.client.get(
        f'/api/confirmar-deposito/{context.uuid_str}/'
    )
    context.response_json = {}


# ─── THEN ─────────────────────────────────────────────────────────────────────

@then('la respuesta contiene "{texto}" en el mensaje de error')
def step_texto_en_error(context, texto):
    error = context.response_json.get('error', '')
    assert texto in error, (
        f"Se esperaba '{texto}' en el error, se obtuvo: '{error}'"
    )


@then('la fecha de depósito queda registrada en base de datos')
def step_fecha_deposito_registrada(context):
    context.etiqueta.refresh_from_db()
    assert context.etiqueta.fecha_deposito is not None, (
        "La fecha de depósito no fue registrada en la base de datos."
    )