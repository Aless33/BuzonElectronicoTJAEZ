from django.test import TestCase

from web.forms import (
    BuzonDemandaForm,
    BuzonContestacionForm,
    BuzonOtrosForm,
    FORM_MAP,
)
from web.models import TipoPromocion, Ponencia


class BuzonFormTestCase(TestCase):
    """
    Pruebas unitarias de formularios creadas bajo enfoque TDD.
    """

    def test_buzon_demanda_form_valido(self):
        """
        Se espera que el formulario de Demanda sea válido cuando recibe
        todos sus campos obligatorios correctamente.
        """

        form = BuzonDemandaForm(data={
            "tipo_promocion": TipoPromocion.DEMANDA,
            "correo_electronico": "ciudadano@test.com",
            "correo_electronico_confirmacion": "ciudadano@test.com",
            "numero_sobres": 2,
        })

        self.assertTrue(form.is_valid())

    def test_buzon_contestacion_form_valido(self):
        """
        Se espera que el formulario de Contestación sea válido cuando
        recibe campos base y campos de expediente.
        """

        form = BuzonContestacionForm(data={
            "tipo_promocion": TipoPromocion.CONTESTACION,
            "correo_electronico": "ciudadano@test.com",
            "correo_electronico_confirmacion": "ciudadano@test.com",
            "numero_sobres": 1,
            "numero_expediente": "TJAEZ-123/2026",
            "anio": 2026,
            "ponencia": Ponencia.PONENCIA_1,
        })

        self.assertTrue(form.is_valid())

    def test_buzon_otros_form_valido(self):
        """
        Se espera que el formulario de Otros sea válido cuando incluye
        el campo especifique.
        """

        form = BuzonOtrosForm(data={
            "tipo_promocion": TipoPromocion.OTROS,
            "correo_electronico": "ciudadano@test.com",
            "correo_electronico_confirmacion": "ciudadano@test.com",
            "numero_sobres": 1,
            "numero_expediente": "EXP-999/2026",
            "anio": 2026,
            "ponencia": Ponencia.PONENCIA_2,
            "especifique": "Promoción especial",
        })

        self.assertTrue(form.is_valid())

    def test_buzon_demanda_form_invalido_si_correos_no_coinciden(self):
        """
        Se espera que el formulario sea inválido si el correo y su
        confirmación son diferentes.
        """

        form = BuzonDemandaForm(data={
            "tipo_promocion": TipoPromocion.DEMANDA,
            "correo_electronico": "ciudadano@test.com",
            "correo_electronico_confirmacion": "otro@test.com",
            "numero_sobres": 1,
        })

        self.assertFalse(form.is_valid())
        self.assertIn("correo_electronico_confirmacion", form.errors)

    def test_mensaje_error_correos_no_coinciden(self):
        """
        Se espera mostrar el mensaje personalizado cuando los correos
        no coinciden.
        """

        form = BuzonDemandaForm(data={
            "tipo_promocion": TipoPromocion.DEMANDA,
            "correo_electronico": "ciudadano@test.com",
            "correo_electronico_confirmacion": "otro@test.com",
            "numero_sobres": 1,
        })

        self.assertFalse(form.is_valid())
        self.assertIn(
            "Los correos electrónicos no coinciden.",
            form.errors["correo_electronico_confirmacion"]
        )

    def test_buzon_demanda_form_requiere_tipo_promocion(self):
        """
        Se espera que tipo_promocion sea obligatorio.
        """

        form = BuzonDemandaForm(data={
            "correo_electronico": "ciudadano@test.com",
            "correo_electronico_confirmacion": "ciudadano@test.com",
            "numero_sobres": 1,
        })

        self.assertFalse(form.is_valid())
        self.assertIn("tipo_promocion", form.errors)

    def test_buzon_demanda_form_requiere_correo_electronico(self):
        """
        Se espera que correo_electronico sea obligatorio.
        """

        form = BuzonDemandaForm(data={
            "tipo_promocion": TipoPromocion.DEMANDA,
            "correo_electronico_confirmacion": "ciudadano@test.com",
            "numero_sobres": 1,
        })

        self.assertFalse(form.is_valid())
        self.assertIn("correo_electronico", form.errors)

    def test_buzon_demanda_form_requiere_confirmacion_correo(self):
        """
        Se espera que correo_electronico_confirmacion sea obligatorio.
        """

        form = BuzonDemandaForm(data={
            "tipo_promocion": TipoPromocion.DEMANDA,
            "correo_electronico": "ciudadano@test.com",
            "numero_sobres": 1,
        })

        self.assertFalse(form.is_valid())
        self.assertIn("correo_electronico_confirmacion", form.errors)

    def test_buzon_demanda_form_requiere_numero_sobres(self):
        """
        Se espera que numero_sobres sea obligatorio.
        """

        form = BuzonDemandaForm(data={
            "tipo_promocion": TipoPromocion.DEMANDA,
            "correo_electronico": "ciudadano@test.com",
            "correo_electronico_confirmacion": "ciudadano@test.com",
        })

        self.assertFalse(form.is_valid())
        self.assertIn("numero_sobres", form.errors)

    def test_buzon_demanda_form_invalido_con_numero_sobres_cero(self):
        """
        Se espera que numero_sobres no permita cero porque el modelo usa
        PositiveIntegerField.
        """

        form = BuzonDemandaForm(data={
            "tipo_promocion": TipoPromocion.DEMANDA,
            "correo_electronico": "ciudadano@test.com",
            "correo_electronico_confirmacion": "ciudadano@test.com",
            "numero_sobres": 0,
        })

        self.assertFalse(form.is_valid())
        self.assertIn("numero_sobres", form.errors)

    def test_buzon_contestacion_form_requiere_numero_expediente(self):
        """
        Se espera que Contestación requiera número de expediente.
        """

        form = BuzonContestacionForm(data={
            "tipo_promocion": TipoPromocion.CONTESTACION,
            "correo_electronico": "ciudadano@test.com",
            "correo_electronico_confirmacion": "ciudadano@test.com",
            "numero_sobres": 1,
            "anio": 2026,
            "ponencia": Ponencia.PONENCIA_1,
        })

        self.assertFalse(form.is_valid())
        self.assertIn("numero_expediente", form.errors)

    def test_buzon_contestacion_form_requiere_anio(self):
        """
        Se espera que Contestación requiera año.
        """

        form = BuzonContestacionForm(data={
            "tipo_promocion": TipoPromocion.CONTESTACION,
            "correo_electronico": "ciudadano@test.com",
            "correo_electronico_confirmacion": "ciudadano@test.com",
            "numero_sobres": 1,
            "numero_expediente": "TJAEZ-123/2026",
            "ponencia": Ponencia.PONENCIA_1,
        })

        self.assertFalse(form.is_valid())
        self.assertIn("anio", form.errors)

    def test_buzon_contestacion_form_requiere_ponencia(self):
        """
        Se espera que Contestación requiera ponencia.
        """
        form = BuzonContestacionForm(data={
            "tipo_promocion": TipoPromocion.CONTESTACION,
            "correo_electronico": "ciudadano@test.com",
            "correo_electronico_confirmacion": "ciudadano@test.com",
            "numero_sobres": 1,
            "numero_expediente": "TJAEZ-123/2026",
            "anio": 2026,
        })

        self.assertFalse(form.is_valid())
        self.assertIn("ponencia", form.errors)

    def test_buzon_otros_form_requiere_especifique(self):
        """
        Se espera que el formulario Otros requiera el campo especifique.
        """

        form = BuzonOtrosForm(data={
            "tipo_promocion": TipoPromocion.OTROS,
            "correo_electronico": "ciudadano@test.com",
            "correo_electronico_confirmacion": "ciudadano@test.com",
            "numero_sobres": 1,
            "numero_expediente": "EXP-999/2026",
            "anio": 2026,
            "ponencia": Ponencia.PONENCIA_2,
        })

        self.assertFalse(form.is_valid())
        self.assertIn("especifique", form.errors)

    def test_form_map_demanda_usa_buzon_demanda_form(self):
        """
        Se espera que DEMANDA use BuzonDemandaForm.
        """

        self.assertEqual(FORM_MAP[TipoPromocion.DEMANDA], BuzonDemandaForm)

    def test_form_map_contestacion_usa_buzon_contestacion_form(self):
        """
        Se espera que CONTESTACION use BuzonContestacionForm.
        """

        self.assertEqual(
            FORM_MAP[TipoPromocion.CONTESTACION],
            BuzonContestacionForm
        )

    def test_form_map_otros_usa_buzon_otros_form(self):
        """
        Se espera que OTROS use BuzonOtrosForm.
        """

        self.assertEqual(FORM_MAP[TipoPromocion.OTROS], BuzonOtrosForm)
