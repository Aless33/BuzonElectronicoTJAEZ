from datetime import timedelta
from behave import given, when
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from rest_framework.test import APIClient
from web.models import BuzonDemanda
from web.models import Etiqueta
from web.models import TipoPromocion
import os
import django
django.setup()

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "buzon_electronico_tjaez.settings",
)


def crear_cliente_autenticado():
    usuario = User.objects.create_user(
        username="hardware_test",
        password="testpass123",
    )
    cliente = APIClient()
    cliente.force_authenticate(user=usuario)
    return cliente


def crear_etiqueta(
    estado=Etiqueta.ESTADO_ETIQUETA_GENERADA,
    vigente=True,
):
    buzon = BuzonDemanda.objects.create(
        tipo_promocion=TipoPromocion.DEMANDA,
        correo_electronico="test@test.com",
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


@given('que el hardware escanea el código "{codigo}"')
def step_escanea_codigo(context, codigo):
    context.client = crear_cliente_autenticado()
    context.uuid_str = codigo
    context.etiqueta = None


@given('que existe una etiqueta con estado "{estado}"')
def step_etiqueta_con_estado(context, estado):
    context.client = crear_cliente_autenticado()
    context.etiqueta = crear_etiqueta(estado=estado)
    context.uuid_str = str(context.etiqueta.uuid)


@given("que existe una etiqueta caducada")
def step_etiqueta_caducada(context):
    context.client = crear_cliente_autenticado()
    context.etiqueta = crear_etiqueta(vigente=False)
    context.uuid_str = str(context.etiqueta.uuid)


@given("que existe una etiqueta válida y vigente")
def step_etiqueta_valida(context):
    context.client = crear_cliente_autenticado()
    context.etiqueta = crear_etiqueta()
    context.uuid_str = str(context.etiqueta.uuid)


@given("el hardware no está autenticado")
def step_hardware_no_autenticado(context):
    context.client.force_authenticate(user=None)


@when("consulta la validez del QR")
def step_consulta_validez(context):
    context.response = context.client.get(
        f"/api/validar-qr/{context.uuid_str}/"
    )
    context.response_json = obtener_json(context.response)


@when("el hardware consulta la validez de esa etiqueta")
def step_consulta_etiqueta(context):
    context.response = context.client.get(
        f"/api/validar-qr/{context.uuid_str}/"
    )
    context.response_json = obtener_json(context.response)


@when("el hardware envía un POST a validar QR")
def step_post_validar_qr(context):
    context.response = context.client.post(
        f"/api/validar-qr/{context.uuid_str}/",
        data={},
        format="json",
    )
    context.response_json = obtener_json(context.response)
