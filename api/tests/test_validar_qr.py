from datetime import timedelta
from uuid import uuid4

from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from web.models import BuzonDemanda, Etiqueta, TipoPromocion


class ValidarQRAPITestCase(TestCase):
    """
    Pruebas unitarias del endpoint CU-03 Validar QR bajo enfoque TDD.
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

    def test_validar_qr_requiere_autenticacion(self):
        """
        TDD - Rojo:
        Se espera que un usuario anónimo no pueda validar un QR.
        """
        self.client.force_authenticate(user=None)
        etiqueta = self.crear_etiqueta()

        response = self.client.get(
            reverse("validar_qr", kwargs={"uuid_str": str(etiqueta.uuid)})
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_validar_qr_valido_retorna_autorizado(self):
        """
        TDD - Rojo:
        Se espera que un QR existente, vigente y generado sea autorizado.
        """
        etiqueta = self.crear_etiqueta()

        response = self.client.get(
            reverse("validar_qr", kwargs={"uuid_str": str(etiqueta.uuid)})
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["autorizado"])
        self.assertEqual(response.data["uuid"], str(etiqueta.uuid))
        self.assertEqual(
            response.data["digito_verificador"],
            etiqueta.digito_verificador,
        )
        self.assertEqual(response.data["numero_sobre"], etiqueta.numero_sobre)
        self.assertEqual(response.data["estado"], etiqueta.estado)

    def test_validar_qr_formato_invalido_retorna_404(self):
        """
        TDD - Rojo:
        Se espera que un UUID con formato inválido sea rechazado.
        """
        response = self.client.get(
            reverse("validar_qr", kwargs={"uuid_str": "uuid-invalido"})
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("error", response.data)
        self.assertEqual(response.data["error"], "Formato de QR inválido.")

    def test_validar_qr_inexistente_retorna_404(self):
        """
        TDD - Rojo:
        Se espera que un UUID válido pero inexistente sea rechazado.
        """
        response = self.client.get(
            reverse("validar_qr", kwargs={"uuid_str": str(uuid4())})
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["error"], "QR no encontrado.")

    def test_validar_qr_depositado_retorna_400(self):
        """
        TDD - Rojo:
        Se espera que una etiqueta ya depositada no pueda validarse.
        """
        etiqueta = self.crear_etiqueta(
            estado=Etiqueta.ESTADO_DEPOSITADO,
        )

        response = self.client.get(
            reverse("validar_qr", kwargs={"uuid_str": str(etiqueta.uuid)})
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "Etiqueta no disponible.")
        self.assertEqual(
            response.data["estado_actual"],
            Etiqueta.ESTADO_DEPOSITADO,
        )

    def test_validar_qr_cancelado_retorna_400(self):
        """
        TDD - Rojo:
        Se espera que una etiqueta cancelada no pueda validarse.
        """
        etiqueta = self.crear_etiqueta(
            estado=Etiqueta.ESTADO_CANCELADO,
        )

        response = self.client.get(
            reverse("validar_qr", kwargs={"uuid_str": str(etiqueta.uuid)})
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "Etiqueta no disponible.")
        self.assertEqual(
            response.data["estado_actual"],
            Etiqueta.ESTADO_CANCELADO,
        )

    def test_validar_qr_no_presentado_retorna_400(self):
        """
        TDD - Rojo:
        Se espera que una etiqueta no presentada no pueda validarse.
        """
        etiqueta = self.crear_etiqueta(
            estado=Etiqueta.ESTADO_NO_PRESENTADO,
        )

        response = self.client.get(
            reverse("validar_qr", kwargs={"uuid_str": str(etiqueta.uuid)})
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "Etiqueta no disponible.")
        self.assertEqual(
            response.data["estado_actual"],
            Etiqueta.ESTADO_NO_PRESENTADO,
        )

    def test_validar_qr_caducado_retorna_400_y_actualiza_estado(self):
        """
        TDD - Rojo:
        Se espera que una etiqueta caducada sea marcada como NO_PRESENTADO.
        """
        etiqueta = self.crear_etiqueta(
            fecha_caducidad=timezone.now() - timedelta(hours=1),
        )

        response = self.client.get(
            reverse("validar_qr", kwargs={"uuid_str": str(etiqueta.uuid)})
        )

        etiqueta.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "La etiqueta ha caducado.")
        self.assertEqual(etiqueta.estado, Etiqueta.ESTADO_NO_PRESENTADO)

    def test_validar_qr_no_permite_post(self):
        """
        TDD - Rojo:
        Se espera que validar QR no acepte POST.
        """
        etiqueta = self.crear_etiqueta()

        response = self.client.post(
            reverse("validar_qr", kwargs={"uuid_str": str(etiqueta.uuid)}),
            data={},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED,
        )
