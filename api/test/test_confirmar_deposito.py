"""
Tests unitarios para CU-04: Confirmar Depósito Físico.
Metodología TDD — cobertura 100% de api/views.py::confirmar_deposito
PEP8 compliant.
"""
import json
import uuid
from datetime import timedelta

from django.contrib.contenttypes.models import ContentType
from django.test import TestCase, Client
from django.utils import timezone

from web.models import BuzonDemanda, Etiqueta


def _crear_etiqueta(estado=Etiqueta.ESTADO_ETIQUETA_GENERADA, vigente=True):
    """Helper: crea un BuzonDemanda + Etiqueta para pruebas."""
    buzon = BuzonDemanda.objects.create(
        tipo_promocion='DEMANDA',
        correo_electronico='test@test.com',
        numero_sobres=1,
    )
    ct = ContentType.objects.get_for_model(buzon)
    delta = timedelta(hours=1) if vigente else timedelta(hours=-1)
    etiqueta = Etiqueta.objects.create(
        content_type=ct,
        object_id=buzon.pk,
        estado=estado,
        fecha_caducidad=timezone.now() + delta,
        numero_sobre=1,
    )
    return etiqueta


def _post(client, uid, body):
    """Helper: realiza un POST al endpoint de confirmar depósito."""
    return client.post(
        f'/api/confirmar-deposito/{uid}/',
        data=json.dumps(body),
        content_type='application/json',
    )


class ConfirmarDepositoFormatoTest(TestCase):
    """Validaciones de formato de entrada."""

    def setUp(self):
        self.client = Client()

    def test_uuid_mal_formado_retorna_404(self):
        response = _post(self.client, 'no-es-uuid', {'sensor_confirmado': True})
        self.assertEqual(response.status_code, 404)

    def test_json_invalido_retorna_400(self):
        etiqueta = _crear_etiqueta()
        response = self.client.post(
            f'/api/confirmar-deposito/{etiqueta.uuid}/',
            data='esto no es json',
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)

    def test_sin_campo_sensor_retorna_400(self):
        etiqueta = _crear_etiqueta()
        response = _post(self.client, etiqueta.uuid, {})
        self.assertEqual(response.status_code, 400)
        self.assertIn('sensor_confirmado', response.json()['error'])

    def test_sensor_en_false_retorna_400(self):
        etiqueta = _crear_etiqueta()
        response = _post(self.client, etiqueta.uuid, {'sensor_confirmado': False})
        self.assertEqual(response.status_code, 400)

    def test_metodo_get_retorna_405(self):
        etiqueta = _crear_etiqueta()
        response = self.client.get(f'/api/confirmar-deposito/{etiqueta.uuid}/')
        self.assertEqual(response.status_code, 405)


class ConfirmarDepositoNoEncontradoTest(TestCase):
    """UUID inexistente debe retornar 404."""

    def setUp(self):
        self.client = Client()

    def test_uuid_inexistente_retorna_404(self):
        response = _post(self.client, uuid.uuid4(), {'sensor_confirmado': True})
        self.assertEqual(response.status_code, 404)


class ConfirmarDepositoDuplicadoTest(TestCase):
    """RF-07: Depósito duplicado debe retornar 409."""

    def setUp(self):
        self.client = Client()

    def test_deposito_duplicado_retorna_409(self):
        etiqueta = _crear_etiqueta(estado=Etiqueta.ESTADO_DEPOSITADO)
        response = _post(self.client, etiqueta.uuid, {'sensor_confirmado': True})
        self.assertEqual(response.status_code, 409)
        self.assertIn('error', response.json())


class ConfirmarDepositoEstadoInvalidoTest(TestCase):
    """Estados distintos a ETIQUETA_GENERADA deben retornar 400."""

    def setUp(self):
        self.client = Client()

    def test_estado_cancelado_retorna_400(self):
        etiqueta = _crear_etiqueta(estado=Etiqueta.ESTADO_CANCELADO)
        response = _post(self.client, etiqueta.uuid, {'sensor_confirmado': True})
        self.assertEqual(response.status_code, 400)

    def test_estado_no_presentado_retorna_400(self):
        etiqueta = _crear_etiqueta(estado=Etiqueta.ESTADO_NO_PRESENTADO)
        response = _post(self.client, etiqueta.uuid, {'sensor_confirmado': True})
        self.assertEqual(response.status_code, 400)

    def test_respuesta_incluye_estado_actual(self):
        etiqueta = _crear_etiqueta(estado=Etiqueta.ESTADO_CANCELADO)
        response = _post(self.client, etiqueta.uuid, {'sensor_confirmado': True})
        self.assertIn('estado_actual', response.json())


class ConfirmarDepositoCaducadoTest(TestCase):
    """RN-01: Etiqueta caducada debe cambiar a NO_PRESENTADO y retornar 400."""

    def setUp(self):
        self.client = Client()

    def test_etiqueta_caducada_retorna_400(self):
        etiqueta = _crear_etiqueta(vigente=False)
        response = _post(self.client, etiqueta.uuid, {'sensor_confirmado': True})
        self.assertEqual(response.status_code, 400)

    def test_etiqueta_caducada_cambia_estado_en_bd(self):
        etiqueta = _crear_etiqueta(vigente=False)
        _post(self.client, etiqueta.uuid, {'sensor_confirmado': True})
        etiqueta.refresh_from_db()
        self.assertEqual(etiqueta.estado, Etiqueta.ESTADO_NO_PRESENTADO)


class ConfirmarDepositoExitosoTest(TestCase):
    """RF-06, RF-08: Depósito exitoso debe cambiar estado y registrar timestamp."""

    def setUp(self):
        self.client = Client()
        self.etiqueta = _crear_etiqueta()

    def test_deposito_exitoso_retorna_200(self):
        response = _post(self.client, self.etiqueta.uuid, {'sensor_confirmado': True})
        self.assertEqual(response.status_code, 200)

    def test_respuesta_contiene_depositado_true(self):
        response = _post(self.client, self.etiqueta.uuid, {'sensor_confirmado': True})
        self.assertTrue(response.json()['depositado'])

    def test_estado_cambia_a_depositado_en_bd(self):
        _post(self.client, self.etiqueta.uuid, {'sensor_confirmado': True})
        self.etiqueta.refresh_from_db()
        self.assertEqual(self.etiqueta.estado, Etiqueta.ESTADO_DEPOSITADO)

    def test_fecha_deposito_se_registra_en_bd(self):
        _post(self.client, self.etiqueta.uuid, {'sensor_confirmado': True})
        self.etiqueta.refresh_from_db()
        self.assertIsNotNone(self.etiqueta.fecha_deposito)

    def test_respuesta_contiene_uuid(self):
        response = _post(self.client, self.etiqueta.uuid, {'sensor_confirmado': True})
        self.assertEqual(response.json()['uuid'], str(self.etiqueta.uuid))

    def test_respuesta_contiene_fecha_deposito(self):
        response = _post(self.client, self.etiqueta.uuid, {'sensor_confirmado': True})
        self.assertIn('fecha_deposito', response.json())

    def test_respuesta_contiene_digito_verificador(self):
        response = _post(self.client, self.etiqueta.uuid, {'sensor_confirmado': True})
        self.assertIn('digito_verificador', response.json())