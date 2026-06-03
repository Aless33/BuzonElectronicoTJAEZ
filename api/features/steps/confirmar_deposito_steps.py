from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from rest_framework.test import APIClient
from web.models import BuzonDemanda
from web.models import Etiqueta
from web.models import TipoPromocion
from datetime import timedelta
from behave import given, then, when
import os
import django
django.setup()


os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "buzon_electronico_tjaez.settings",
)


def crear_cliente_autenticado():
    usuario = User.objects.create_user(
        username="hardware_deposito",
        password="testpass123",
    )
    cliente = APIClient()
    cliente.force_authenticate(user=usuario)
    return cliente


def crear_etiqueta_deposito(
    estado=Etiqueta.ESTADO_ETIQUETA_GENERADA,
    vigente=True,
):
    buzon = BuzonDemanda.objects.create(
        tipo_promocion=TipoPromocion.DEMANDA,
        correo_electronico="deposito@test.com",
        numero_sobres=1,
    )
    content_type = ContentType.objects.get_for_model(buzon)
    delta = timedelta(hours=1) if vigente else timedelta(hours=-1)

    return Etiqueta.objects.create(
        content_type=content_type,
        object_id=buzon.pk,
        estado=estado,
        fecha_caducidad=timezone.now() + delta,
        numero_sobre=1,
    )


def obtener_json(response):
    try:
        return response.json()
    except ValueError:
        return {}


@given("que existe una etiqueta generada y vigente para depósito")
def step_etiqueta_generada_vigente(context):
    context.client = crear_cliente_autenticado()
    context.etiqueta = crear_etiqueta_deposito()
    context.uuid_str = str(context.etiqueta.uuid)


@given("que existe una etiqueta ya depositada")
def step_etiqueta_ya_depositada(context):
    context.client = crear_cliente_autenticado()
    context.etiqueta = crear_etiqueta_deposito(
        estado=Etiqueta.ESTADO_DEPOSITADO,
    )
    context.uuid_str = str(context.etiqueta.uuid)


@given("que existe una etiqueta cancelada para depósito")
def step_etiqueta_cancelada(context):
    context.client = crear_cliente_autenticado()
    context.etiqueta = crear_etiqueta_deposito(
        estado=Etiqueta.ESTADO_CANCELADO,
    )
    context.uuid_str = str(context.etiqueta.uuid)


@given("que existe una etiqueta caducada para depósito")
def step_etiqueta_caducada(context):
    context.client = crear_cliente_autenticado()
    context.etiqueta = crear_etiqueta_deposito(vigente=False)
    context.uuid_str = str(context.etiqueta.uuid)


@given('que el hardware tiene el UUID de depósito "{uuid_str}"')
def step_uuid_deposito(context, uuid_str):
    context.client = crear_cliente_autenticado()
    context.etiqueta = None
    context.uuid_str = uuid_str


@given("el hardware de depósito no está autenticado")
def step_hardware_deposito_no_autenticado(context):
    context.client.force_authenticate(user=None)


@when("el hardware confirma el depósito con sensor verdadero")
def step_confirma_sensor_true(context):
    context.response = context.client.post(
        f"/api/confirmar-deposito/{context.uuid_str}/",
        data={"sensor_confirmado": True},
        format="json",
    )
    context.response_json = obtener_json(context.response)


@when("el hardware confirma el depósito con sensor falso")
def step_confirma_sensor_false(context):
    context.response = context.client.post(
        f"/api/confirmar-deposito/{context.uuid_str}/",
        data={"sensor_confirmado": False},
        format="json",
    )
    context.response_json = obtener_json(context.response)


@when("el hardware confirma el depósito sin enviar sensor")
def step_confirma_sin_sensor(context):
    context.response = context.client.post(
        f"/api/confirmar-deposito/{context.uuid_str}/",
        data={},
        format="json",
    )
    context.response_json = obtener_json(context.response)


@when("el hardware envía un GET a confirmar depósito")
def step_get_confirmar_deposito(context):
    context.response = context.client.get(
        f"/api/confirmar-deposito/{context.uuid_str}/"
    )
    context.response_json = obtener_json(context.response)


@then("la etiqueta tiene fecha de depósito registrada")
def step_fecha_deposito_registrada(context):
    context.etiqueta.refresh_from_db()

    assert context.etiqueta.fecha_deposito is not None
