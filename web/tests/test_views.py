from unittest.mock import patch

from django.contrib.messages import get_messages
from django.test import TestCase
from django.urls import reverse

from web.forms import BuzonContestacionForm, BuzonDemandaForm
from web.models import (
    BuzonDemanda,
    Etiqueta,
    Ponencia,
    TipoPromocion,
)


class BuzonCrearViewTestCase(TestCase):
    """
    Pruebas unitarias de la vista buzon_crear bajo enfoque TDD.
    """

    def test_buzon_crear_get_status_200(self):
        """

        Se espera que la vista principal responda 200 por GET.
        """

        response = self.client.get(reverse("buzon_crear"))

        self.assertEqual(response.status_code, 200)

    def test_buzon_crear_get_template_correcto(self):
        """

        Se espera que la vista principal renderice el template del formulario.
        """

        response = self.client.get(reverse("buzon_crear"))

        self.assertTemplateUsed(
            response,
            "Realizar_registro/buzon_form.html"
        )

    def test_buzon_crear_get_contexto_correcto(self):
        """

        Se espera que el contexto incluya form, tipo_actual y tipos.
        """

        response = self.client.get(reverse("buzon_crear"))

        self.assertIn("form", response.context)
        self.assertIn("tipo_actual", response.context)
        self.assertIn("tipos", response.context)

    def test_buzon_crear_get_tipo_default_es_demanda(self):
        """

        Se espera que si no se indica tipo_promocion, se use DEMANDA.
        """

        response = self.client.get(reverse("buzon_crear"))

        self.assertEqual(
            response.context["tipo_actual"],
            TipoPromocion.DEMANDA
        )
        self.assertIsInstance(response.context["form"], BuzonDemandaForm)

    def test_buzon_crear_get_con_tipo_contestacion_usa_form_correcto(self):
        """

        Se espera que al recibir tipo_promocion=CONTESTACION se use
        BuzonContestacionForm.
        """

        response = self.client.get(
            reverse("buzon_crear"),
            {"tipo_promocion": TipoPromocion.CONTESTACION}
        )

        self.assertEqual(
            response.context["tipo_actual"],
            TipoPromocion.CONTESTACION
        )
        self.assertIsInstance(response.context["form"], BuzonContestacionForm)

    @patch("web.views.generar_pdf_etiquetas")
    def test_buzon_crear_post_valido_devuelve_pdf(self, mock_generar_pdf):
        """

        Se espera que un POST válido devuelva un PDF.
        """

        mock_generar_pdf.return_value = (
            b"%PDF-1.4 contenido simulado",
            [
                {
                    "uuid": "11111111-1111-1111-1111-111111111111",
                    "digito_verificador": "ABC123",
                    "numero_sobre": 1,
                }
            ]
        )

        response = self.client.post(reverse("buzon_crear"), data={
            "tipo_promocion": TipoPromocion.DEMANDA,
            "correo_electronico": "ciudadano@test.com",
            "correo_electronico_confirmacion": "ciudadano@test.com",
            "numero_sobres": 1,
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")

    @patch("web.views.generar_pdf_etiquetas")
    def test_buzon_crear_post_valido_content_disposition_inline(
        self,
        mock_generar_pdf
    ):
        """

        Se espera que el PDF se devuelva inline para visualizarse
        en el navegador.
        """

        mock_generar_pdf.return_value = (
            b"%PDF-1.4 contenido simulado",
            [
                {
                    "uuid": "22222222-2222-2222-2222-222222222222",
                    "digito_verificador": "DEF456",
                    "numero_sobre": 1,
                }
            ]
        )

        response = self.client.post(reverse("buzon_crear"), data={
            "tipo_promocion": TipoPromocion.DEMANDA,
            "correo_electronico": "ciudadano@test.com",
            "correo_electronico_confirmacion": "ciudadano@test.com",
            "numero_sobres": 1,
        })

        self.assertIn("inline", response["Content-Disposition"])
        self.assertIn("etiquetas_", response["Content-Disposition"])
        self.assertIn(".pdf", response["Content-Disposition"])

    @patch("web.views.generar_pdf_etiquetas")
    def test_buzon_crear_post_valido_crea_buzon(self, mock_generar_pdf):
        """

        Se espera que un POST válido cree un BuzonDemanda.
        """

        mock_generar_pdf.return_value = (
            b"%PDF-1.4 contenido simulado",
            [
                {
                    "uuid": "33333333-3333-3333-3333-333333333333",
                    "digito_verificador": "GHI789",
                    "numero_sobre": 1,
                }
            ]
        )

        self.client.post(reverse("buzon_crear"), data={
            "tipo_promocion": TipoPromocion.DEMANDA,
            "correo_electronico": "ciudadano@test.com",
            "correo_electronico_confirmacion": "ciudadano@test.com",
            "numero_sobres": 1,
        })

        self.assertEqual(BuzonDemanda.objects.count(), 1)

    @patch("web.views.generar_pdf_etiquetas")
    def test_buzon_crear_post_valido_crea_etiquetas(self, mock_generar_pdf):
        """

        Se espera que al crear un buzón también se creen sus etiquetas.
        """

        mock_generar_pdf.return_value = (
            b"%PDF-1.4 contenido simulado",
            [
                {
                    "uuid": "44444444-4444-4444-4444-444444444444",
                    "digito_verificador": "JKL111",
                    "numero_sobre": 1,
                },
                {
                    "uuid": "55555555-5555-5555-5555-555555555555",
                    "digito_verificador": "MNO222",
                    "numero_sobre": 2,
                },
            ]
        )

        self.client.post(reverse("buzon_crear"), data={
            "tipo_promocion": TipoPromocion.DEMANDA,
            "correo_electronico": "ciudadano@test.com",
            "correo_electronico_confirmacion": "ciudadano@test.com",
            "numero_sobres": 2,
        })

        self.assertEqual(Etiqueta.objects.count(), 2)

    @patch("web.views.generar_pdf_etiquetas")
    def test_numero_etiquetas_igual_numero_sobres(self, mock_generar_pdf):
        """

        Se espera que la cantidad de etiquetas generadas coincida con
        el número de sobres.
        """

        mock_generar_pdf.return_value = (
            b"%PDF-1.4 contenido simulado",
            [
                {
                    "uuid": "66666666-6666-6666-6666-666666666666",
                    "digito_verificador": "PQR333",
                    "numero_sobre": 1,
                },
                {
                    "uuid": "77777777-7777-7777-7777-777777777777",
                    "digito_verificador": "STU444",
                    "numero_sobre": 2,
                },
                {
                    "uuid": "88888888-8888-8888-8888-888888888888",
                    "digito_verificador": "VWX555",
                    "numero_sobre": 3,
                },
            ]
        )

        self.client.post(reverse("buzon_crear"), data={
            "tipo_promocion": TipoPromocion.DEMANDA,
            "correo_electronico": "ciudadano@test.com",
            "correo_electronico_confirmacion": "ciudadano@test.com",
            "numero_sobres": 3,
        })

        buzon = BuzonDemanda.objects.first()

        self.assertEqual(buzon.numero_sobres, 3)
        self.assertEqual(Etiqueta.objects.count(), 3)

    @patch("web.views.generar_pdf_etiquetas")
    def test_buzon_crear_si_pdf_falla_elimina_buzon(self, mock_generar_pdf):
        """

        Se espera que si falla la generación del PDF, el buzón recién
        creado sea eliminado.
        """

        mock_generar_pdf.side_effect = ValueError(
            "No se pudo generar el PDF."
        )

        response = self.client.post(reverse("buzon_crear"), data={
            "tipo_promocion": TipoPromocion.DEMANDA,
            "correo_electronico": "ciudadano@test.com",
            "correo_electronico_confirmacion": "ciudadano@test.com",
            "numero_sobres": 1,
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(BuzonDemanda.objects.count(), 0)

    @patch("web.views.generar_pdf_etiquetas")
    def test_buzon_crear_si_pdf_falla_muestra_mensaje_error(
        self,
        mock_generar_pdf
    ):
        """

        Se espera que si falla el servicio de PDF, se muestre un mensaje
        de error al usuario.
        """

        mock_generar_pdf.side_effect = ValueError(
            "No se pudo generar el PDF."
        )

        response = self.client.post(reverse("buzon_crear"), data={
            "tipo_promocion": TipoPromocion.DEMANDA,
            "correo_electronico": "ciudadano@test.com",
            "correo_electronico_confirmacion": "ciudadano@test.com",
            "numero_sobres": 1,
        })

        mensajes = list(get_messages(response.wsgi_request))

        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            any("No se pudo generar el PDF." in str(m) for m in mensajes)
        )

    def test_buzon_crear_post_invalido_no_crea_buzon(self):
        """

        Se espera que un POST inválido no cree registros.
        """

        response = self.client.post(reverse("buzon_crear"), data={
            "tipo_promocion": TipoPromocion.DEMANDA,
            "correo_electronico": "ciudadano@test.com",
            "correo_electronico_confirmacion": "otro@test.com",
            "numero_sobres": 1,
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(BuzonDemanda.objects.count(), 0)

    @patch("web.views.generar_pdf_etiquetas")
    def test_buzon_crear_post_contestacion_valida_crea_registro(
        self,
        mock_generar_pdf
    ):
        """

        Se espera que una promoción de tipo Contestación válida se procese
        correctamente.
        """

        mock_generar_pdf.return_value = (
            b"%PDF-1.4 contenido simulado",
            [
                {
                    "uuid": "99999999-9999-9999-9999-999999999999",
                    "digito_verificador": "XYZ999",
                    "numero_sobre": 1,
                }
            ]
        )

        response = self.client.post(reverse("buzon_crear"), data={
            "tipo_promocion": TipoPromocion.CONTESTACION,
            "correo_electronico": "ciudadano@test.com",
            "correo_electronico_confirmacion": "ciudadano@test.com",
            "numero_sobres": 1,
            "numero_expediente": "TJAEZ-123/2026",
            "anio": 2026,
            "ponencia": Ponencia.PONENCIA_1,
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")


class BuzonFormParcialViewTestCase(TestCase):
    """
    Pruebas unitarias de la vista buzon_form_parcial bajo enfoque TDD.
    """

    def test_buzon_form_parcial_get_status_200(self):
        """

        Se espera que la vista parcial responda 200 por GET.
        """

        response = self.client.get(reverse("buzon_form_parcial"))

        self.assertEqual(response.status_code, 200)

    def test_buzon_form_parcial_template_correcto(self):
        """

        Se espera que la vista parcial use el template campos_extra.html.
        """

        response = self.client.get(reverse("buzon_form_parcial"))

        self.assertTemplateUsed(
            response,
            "Realizar_registro/campos_extra.html"
        )

    def test_buzon_form_parcial_contexto_contiene_campos_extra(self):
        """

        Se espera que el contexto incluya campos_extra.
        """

        response = self.client.get(reverse("buzon_form_parcial"))

        self.assertIn("campos_extra", response.context)

    def test_buzon_form_parcial_demanda_no_muestra_campos_extra(self):
        """

        Se espera que Demanda no tenga campos extra.
        """

        response = self.client.get(
            reverse("buzon_form_parcial"),
            {"tipo": TipoPromocion.DEMANDA}
        )

        campos_extra = response.context["campos_extra"]

        self.assertEqual(len(campos_extra), 0)

    def test_buzon_form_parcial_contestacion_muestra_campos_extra(self):
        """

        Se espera que Contestación muestre los campos de expediente.
        """

        response = self.client.get(
            reverse("buzon_form_parcial"),
            {"tipo": TipoPromocion.CONTESTACION}
        )

        nombres_campos = [
            nombre for nombre, campo in response.context["campos_extra"]
        ]

        self.assertIn("numero_expediente", nombres_campos)
        self.assertIn("anio", nombres_campos)
        self.assertIn("ponencia", nombres_campos)

    def test_buzon_form_parcial_otros_muestra_especifique(self):
        """

        Se espera que Otros muestre el campo especifique.
        """

        response = self.client.get(
            reverse("buzon_form_parcial"),
            {"tipo": TipoPromocion.OTROS}
        )

        nombres_campos = [
            nombre for nombre, campo in response.context["campos_extra"]
        ]

        self.assertIn("especifique", nombres_campos)

    def test_buzon_form_parcial_no_permite_post(self):
        """

        Se espera que la vista parcial solo permita GET.
        """

        response = self.client.post(reverse("buzon_form_parcial"))

        self.assertEqual(response.status_code, 405)
