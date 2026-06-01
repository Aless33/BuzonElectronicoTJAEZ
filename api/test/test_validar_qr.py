"""
Tests unitarios para CU-03: Consultar Validez del QR.
Metodología TDD — cobertura 100% de api/views.py::ValidarQRView
PEP8 compliant.
"""
import uuid
from datetime import timedelta

from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

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
    return Etiqueta.objects.create(
        content_type=ct,
        object_id=buzon.pk,
        estado=estado,
        fecha_caducidad=timezone.now() + delta,
        numero_sobre=1,
    )


def _cliente_autenticado():
    """Helper: crea un APIClient con JWT."""
    user = User.objects.create_user(
        username='hardware',
        password='testpass123'
    )
    client = APIClient()
    client.force_authenticate(user=user)
    return client


class ValidarQRSinAutenticacionTest(TestCase):
    """Acceso sin token debe retornar 401."""

    def setUp(self):
        self.client = APIClient()
        self.etiqueta = _crear_etiqueta()

    def test_sin_token_retorna_401(self):
        response = self.client.get(
            f'/api/validar-qr/{self.etiqueta.uuid}/'
        )
        self.assertEqual(response.status_code, 401)


class ValidarQRFormatoInvalidoTest(TestCase):
    """RF-05: UUID mal formado debe retornar 404."""

    def setUp(self):
        self.client = _cliente_autenticado()

    def test_uuid_mal_formado_retorna_404(self):
        response = self.client.get('/api/validar-qr/esto-no-es-un-uuid/')
        self.assertEqual(response.status_code, 404)
        self.assertIn('error', response.json())

    def test_uuid_vacio_retorna_404(self):
        response = self.client.get('/api/validar-qr/----/')
        self.assertEqual(response.status_code, 404)


class ValidarQRNoEncontradoTest(TestCase):
    """RF-05: UUID válido pero inexistente debe retornar 404."""

    def setUp(self):
        self.client = _cliente_autenticado()

    def test_uuid_inexistente_retorna_404(self):
        uid = str(uuid.uuid4())
        response = self.client.get(f'/api/validar-qr/{uid}/')
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()['error'], 'QR no encontrado.')


class ValidarQREstadoRechazadoTest(TestCase):
    """RF-07: Estados inválidos deben retornar 400."""

    def setUp(self):
        self.client = _cliente_autenticado()

    def test_estado_depositado_retorna_400(self):
        etiqueta = _crear_etiqueta(estado=Etiqueta.ESTADO_DEPOSITADO)
        response = self.client.get(f'/api/validar-qr/{etiqueta.uuid}/')
        self.assertEqual(response.status_code, 400)

    def test_estado_cancelado_retorna_400(self):
        etiqueta = _crear_etiqueta(estado=Etiqueta.ESTADO_CANCELADO)
        response = self.client.get(f'/api/validar-qr/{etiqueta.uuid}/')
        self.assertEqual(response.status_code, 400)

    def test_estado_no_presentado_retorna_400(self):
        etiqueta = _crear_etiqueta(estado=Etiqueta.ESTADO_NO_PRESENTADO)
        response = self.client.get(f'/api/validar-qr/{etiqueta.uuid}/')
        self.assertEqual(response.status_code, 400)

    def test_respuesta_incluye_estado_actual(self):
        etiqueta = _crear_etiqueta(estado=Etiqueta.ESTADO_DEPOSITADO)
        response = self.client.get(f'/api/validar-qr/{etiqueta.uuid}/')
        self.assertIn('estado_actual', response.json())


class ValidarQRCaducadoTest(TestCase):
    """RN-01: Etiqueta caducada debe cambiar a NO_PRESENTADO y retornar 400."""

    def setUp(self):
        self.client = _cliente_autenticado()

    def test_etiqueta_caducada_retorna_400(self):
        etiqueta = _crear_etiqueta(vigente=False)
        response = self.client.get(f'/api/validar-qr/{etiqueta.uuid}/')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['error'], 'La etiqueta ha caducado.')

    def test_etiqueta_caducada_cambia_estado_en_bd(self):
        etiqueta = _crear_etiqueta(vigente=False)
        self.client.get(f'/api/validar-qr/{etiqueta.uuid}/')
        etiqueta.refresh_from_db()
        self.assertEqual(etiqueta.estado, Etiqueta.ESTADO_NO_PRESENTADO)


class ValidarQRExitosoTest(TestCase):
    """RF-05: Etiqueta válida y vigente debe retornar 200 con autorización."""

    def setUp(self):
        self.client = _cliente_autenticado()
        self.etiqueta = _crear_etiqueta()

    def test_qr_valido_retorna_200(self):
        response = self.client.get(f'/api/validar-qr/{self.etiqueta.uuid}/')
        self.assertEqual(response.status_code, 200)

    def test_respuesta_contiene_autorizado_true(self):
        response = self.client.get(f'/api/validar-qr/{self.etiqueta.uuid}/')
        self.assertTrue(response.json()['autorizado'])

    def test_respuesta_contiene_uuid(self):
        response = self.client.get(f'/api/validar-qr/{self.etiqueta.uuid}/')
        self.assertEqual(response.json()['uuid'], str(self.etiqueta.uuid))

    def test_respuesta_contiene_digito_verificador(self):
        response = self.client.get(f'/api/validar-qr/{self.etiqueta.uuid}/')
        self.assertIn('digito_verificador', response.json())

    def test_respuesta_contiene_numero_sobre(self):
        response = self.client.get(f'/api/validar-qr/{self.etiqueta.uuid}/')
        self.assertEqual(response.json()['numero_sobre'], 1)

    def test_estado_no_cambia_tras_validacion(self):
        self.client.get(f'/api/validar-qr/{self.etiqueta.uuid}/')
        self.etiqueta.refresh_from_db()
        self.assertEqual(self.etiqueta.estado, Etiqueta.ESTADO_ETIQUETA_GENERADA)

    def test_metodo_post_retorna_405(self):
        response = self.client.post(f'/api/validar-qr/{self.etiqueta.uuid}/')
        self.assertEqual(response.status_code, 405)