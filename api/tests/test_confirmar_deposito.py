from datetime import timedelta
from uuid import uuid4

from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient
from unittest.mock import patch
from web.models import BuzonDemanda, Etiqueta, TipoPromocion


class ConfirmarDepositoAPITestCase(TestCase):
    """
    Pruebas unitarias del endpoint CU-04 Confirmar Depósito bajo enfoque TDD.
    """

    def setUp(self):
        self.client = APIClient()
        self.usuario = User.objects.create_user(
            username="usuario_api",
            password="password123",
        )
        self.client.force_authenticate(user=self.usuario)

        self.buzon = BuzonDemanda.objects.create(
            tipo_promocion=TipoPromocion.DEMANDA,
            correo_electronico="ciudadano@example.com",
            numero_sobres=1,
        )
        self.content_type = ContentType.objects.get_for_model(self.buzon)

    def crear_etiqueta(self, **overrides):
        datos = {
            "content_type": self.content_type,
            "object_id": self.buzon.pk,
            "fecha_caducidad": timezone.now() + timedelta(hours=1),
            "numero_sobre": 1,
        }
        datos.update(overrides)

        return Etiqueta.objects.create(**datos)

    def test_confirmar_deposito_requiere_autenticacion(self):
        """

        Se espera que un usuario anónimo no pueda confirmar depósito.
        """
        self.client.force_authenticate(user=None)
        etiqueta = self.crear_etiqueta()

        response = self.client.post(
            reverse(
                "confirmar_deposito",
                kwargs={"uuid_str": str(etiqueta.uuid)},
            ),
            data={"sensor_confirmado": True},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_confirmar_deposito_valido_actualiza_estado(self):
        """

        Se espera que un depósito confirmado cambie el estado a DEPOSITADO.
        """
        etiqueta = self.crear_etiqueta()

        response = self.client.post(
            reverse(
                "confirmar_deposito",
                kwargs={"uuid_str": str(etiqueta.uuid)},
            ),
            data={"sensor_confirmado": True},
            format="json",
        )

        etiqueta.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["depositado"])
        self.assertEqual(etiqueta.estado, Etiqueta.ESTADO_DEPOSITADO)
        self.assertIsNotNone(etiqueta.fecha_deposito)
        self.assertEqual(response.data["uuid"], str(etiqueta.uuid))
        self.assertEqual(
            response.data["digito_verificador"],
            etiqueta.digito_verificador,
        )
        self.assertEqual(response.data["numero_sobre"], etiqueta.numero_sobre)

    def test_confirmar_deposito_formato_uuid_invalido_retorna_404(self):
        """

        Se espera que un UUID inválido sea rechazado.
        """
        response = self.client.post(
            reverse(
                "confirmar_deposito",
                kwargs={"uuid_str": "uuid-invalido"},
            ),
            data={"sensor_confirmado": True},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["error"], "Formato de UUID inválido.")

    def test_confirmar_deposito_uuid_inexistente_retorna_404(self):
        """

        Se espera que un UUID inexistente sea rechazado.
        """
        response = self.client.post(
            reverse(
                "confirmar_deposito",
                kwargs={"uuid_str": str(uuid4())},
            ),
            data={"sensor_confirmado": True},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["error"], "UUID no encontrado.")

    def test_confirmar_deposito_sin_sensor_retorna_400(self):
        """

        Se espera rechazar el depósito si falta sensor_confirmado.
        """
        etiqueta = self.crear_etiqueta()

        response = self.client.post(
            reverse(
                "confirmar_deposito",
                kwargs={"uuid_str": str(etiqueta.uuid)},
            ),
            data={},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["error"],
            "Falta el campo 'sensor_confirmado' en el payload.",
        )

    def test_confirmar_deposito_sensor_false_retorna_400(self):
        """

        Se espera rechazar el depósito si el sensor no confirma.
        """
        etiqueta = self.crear_etiqueta()

        response = self.client.post(
            reverse(
                "confirmar_deposito",
                kwargs={"uuid_str": str(etiqueta.uuid)},
            ),
            data={"sensor_confirmado": False},
            format="json",
        )

        etiqueta.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["error"],
            "El sensor no confirmó el depósito.",
        )
        self.assertEqual(
            etiqueta.estado,
            Etiqueta.ESTADO_ETIQUETA_GENERADA,
        )

    def test_confirmar_deposito_duplicado_retorna_409(self):
        """

        Se espera rechazar una etiqueta ya depositada.
        """
        etiqueta = self.crear_etiqueta(
            estado=Etiqueta.ESTADO_DEPOSITADO,
            fecha_deposito=timezone.now(),
        )

        response = self.client.post(
            reverse(
                "confirmar_deposito",
                kwargs={"uuid_str": str(etiqueta.uuid)},
            ),
            data={"sensor_confirmado": True},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(
            response.data["error"],
            "Esta etiqueta ya fue depositada anteriormente.",
        )

    def test_confirmar_deposito_cancelado_retorna_400(self):
        """

        Se espera rechazar una etiqueta cancelada.
        """
        etiqueta = self.crear_etiqueta(
            estado=Etiqueta.ESTADO_CANCELADO,
        )

        response = self.client.post(
            reverse(
                "confirmar_deposito",
                kwargs={"uuid_str": str(etiqueta.uuid)},
            ),
            data={"sensor_confirmado": True},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["error"],
            "La etiqueta no está en un estado válido.",
        )
        self.assertEqual(
            response.data["estado_actual"],
            Etiqueta.ESTADO_CANCELADO,
        )

    def test_confirmar_deposito_no_presentado_retorna_400(self):
        """

        Se espera rechazar una etiqueta no presentada.
        """
        etiqueta = self.crear_etiqueta(
            estado=Etiqueta.ESTADO_NO_PRESENTADO,
        )

        response = self.client.post(
            reverse(
                "confirmar_deposito",
                kwargs={"uuid_str": str(etiqueta.uuid)},
            ),
            data={"sensor_confirmado": True},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["estado_actual"],
            Etiqueta.ESTADO_NO_PRESENTADO,
        )

    def test_confirmar_deposito_caducado_actualiza_no_presentado(self):
        """

        Se espera que una etiqueta caducada sea marcada como NO_PRESENTADO.
        """
        etiqueta = self.crear_etiqueta(
            fecha_caducidad=timezone.now() - timedelta(hours=1),
        )

        response = self.client.post(
            reverse(
                "confirmar_deposito",
                kwargs={"uuid_str": str(etiqueta.uuid)},
            ),
            data={"sensor_confirmado": True},
            format="json",
        )

        etiqueta.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "La etiqueta ha caducado.")
        self.assertEqual(etiqueta.estado, Etiqueta.ESTADO_NO_PRESENTADO)

    def test_confirmar_deposito_no_permite_get(self):
        """

        Se espera que confirmar depósito no acepte GET.
        """
        etiqueta = self.crear_etiqueta()

        response = self.client.get(
            reverse(
                "confirmar_deposito",
                kwargs={"uuid_str": str(etiqueta.uuid)},
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    def test_confirmar_deposito_fallo_correo_no_invalida_deposito(self):
        """
        CU-05 (RNF-07): Si enviar_acuse_correo.delay() lanza una excepción,
        el depósito igual debe quedar confirmado — el fallo del correo
        no invalida la operación.
        """
        etiqueta = self.crear_etiqueta()
        with patch(
            'api.views.enviar_acuse_correo.delay',
            side_effect=Exception('Redis no disponible'),
        ):
            response = self.client.post(
                reverse(
                    'confirmar_deposito',
                    kwargs={'uuid_str': str(etiqueta.uuid)},
                ),
                data={'sensor_confirmado': True},
                format='json',
            )

        etiqueta.refresh_from_db()

        # El depósito debe haberse confirmado a pesar del fallo del correo
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['depositado'])
        self.assertEqual(etiqueta.estado, Etiqueta.ESTADO_DEPOSITADO)
        self.assertIsNotNone(etiqueta.fecha_deposito)
