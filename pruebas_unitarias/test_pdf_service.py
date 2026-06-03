"""
test_pdf_service.py — Pruebas unitarias para web/services/pdf_service.py
"""

from django.test import TestCase
from django.utils import timezone
from unittest.mock import patch

from web.services.pdf_service import (
    generar_pdf_etiquetas,
    _validar_datos,
    _generar_digito_verificador,
    _calcular_caducidad,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

DATOS_DEMANDA = {
    "tipo_promocion":    "DEMANDA",
    "numero_expediente": None,
    "anio":              None,
    "ponencia":          None,
    "correo_ciudadano":  "ciudadano@example.com",
    "numero_sobres":     1,
}

DATOS_CONTESTACION = {
    "tipo_promocion":    "CONTESTACION",
    "numero_expediente": "123/2024",
    "anio":              2024,
    "ponencia":          "PONENCIA_1",
    "correo_ciudadano":  "abogado@example.com",
    "numero_sobres":     2,
}


# ===========================================================================
# 1. UTILIDADES INTERNAS
# ===========================================================================

class TestGenerarDigitoVerificador(TestCase):

    def test_longitud_6(self):
        digito = _generar_digito_verificador()
        self.assertEqual(len(digito), 6)

    def test_solo_mayusculas_y_digitos(self):
        import string
        validos = set(string.ascii_uppercase + string.digits)
        for _ in range(20):
            digito = _generar_digito_verificador()
            self.assertTrue(set(digito).issubset(validos))

    def test_genera_valores_distintos(self):
        digitos = {_generar_digito_verificador() for _ in range(50)}
        self.assertGreater(len(digitos), 1)


class TestCalcularCaducidad(TestCase):

    def test_hora_es_235959(self):
        caducidad = _calcular_caducidad()
        self.assertEqual(caducidad.hour, 23)
        self.assertEqual(caducidad.minute, 59)
        self.assertEqual(caducidad.second, 59)

    def test_es_dia_actual(self):
        caducidad = _calcular_caducidad()
        self.assertEqual(caducidad.date(), timezone.localdate())

    def test_es_timezone_aware(self):
        caducidad = _calcular_caducidad()
        self.assertIsNotNone(caducidad.tzinfo)


# ===========================================================================
# 2. VALIDACIONES
# ===========================================================================

class TestValidarDatos(TestCase):

    def _datos(self, **kwargs):
        base = {**DATOS_DEMANDA}
        base.update(kwargs)
        return base

    # --- Tipo de promoción ---

    def test_tipo_vacio_lanza_error(self):
        with self.assertRaises(ValueError) as ctx:
            _validar_datos(self._datos(tipo_promocion=''))
        self.assertIn('obligatorio', str(ctx.exception))

    def test_tipo_none_lanza_error(self):
        with self.assertRaises(ValueError):
            _validar_datos(self._datos(tipo_promocion=None))

    def test_tipo_invalido_lanza_error(self):
        with self.assertRaises(ValueError) as ctx:
            _validar_datos(self._datos(tipo_promocion='TIPO_INEXISTENTE'))
        self.assertIn('inválido', str(ctx.exception))

    # --- Trámites iniciales (DEMANDA, EXPEDIENTE_RAG_INICIAL) ---

    def test_demanda_con_expediente_lanza_error(self):
        with self.assertRaises(ValueError) as ctx:
            _validar_datos(self._datos(numero_expediente='999'))
        self.assertIn('iniciales', str(ctx.exception))

    def test_demanda_con_anio_lanza_error(self):
        with self.assertRaises(ValueError) as ctx:
            _validar_datos(self._datos(anio=2024))
        self.assertIn('iniciales', str(ctx.exception))

    def test_demanda_sin_expediente_valida(self):
        try:
            _validar_datos(self._datos())
        except ValueError:
            self.fail("_validar_datos lanzó ValueError para una DEMANDA válida")

    # --- Trámites de seguimiento ---

    def test_contestacion_sin_expediente_lanza_error(self):
        datos = {**DATOS_CONTESTACION, 'numero_expediente': ''}
        with self.assertRaises(ValueError) as ctx:
            _validar_datos(datos)
        self.assertIn('expediente', str(ctx.exception))

    def test_contestacion_sin_anio_lanza_error(self):
        datos = {**DATOS_CONTESTACION, 'anio': None}
        with self.assertRaises(ValueError) as ctx:
            _validar_datos(datos)
        self.assertIn('año', str(ctx.exception))

    def test_contestacion_valida(self):
        try:
            _validar_datos(DATOS_CONTESTACION)
        except ValueError:
            self.fail("_validar_datos lanzó ValueError para una CONTESTACION válida")

    # --- Correo ---

    def test_correo_vacio_lanza_error(self):
        with self.assertRaises(ValueError) as ctx:
            _validar_datos(self._datos(correo_ciudadano=''))
        self.assertIn('correo', str(ctx.exception))

    def test_correo_sin_arroba_lanza_error(self):
        with self.assertRaises(ValueError) as ctx:
            _validar_datos(self._datos(correo_ciudadano='correoSinArroba'))
        self.assertIn('correo', str(ctx.exception))

    # --- Número de sobres ---

    def test_cero_sobres_lanza_error(self):
        with self.assertRaises(ValueError) as ctx:
            _validar_datos(self._datos(numero_sobres=0))
        self.assertIn('menos 1', str(ctx.exception))

    def test_sobres_string_lanza_error(self):
        with self.assertRaises(ValueError) as ctx:
            _validar_datos(self._datos(numero_sobres='dos'))
        self.assertIn('menos 1', str(ctx.exception))

    def test_21_sobres_lanza_error(self):
        with self.assertRaises(ValueError) as ctx:
            _validar_datos(self._datos(numero_sobres=21))
        self.assertIn('20', str(ctx.exception))

    def test_20_sobres_valido(self):
        try:
            _validar_datos(self._datos(numero_sobres=20))
        except ValueError:
            self.fail("20 sobres debería ser válido")


# ===========================================================================
# 3. GENERACIÓN DEL PDF
# ===========================================================================

class TestGenerarPdfEtiquetas(TestCase):

    def test_retorna_bytes_pdf(self):
        pdf_bytes, _ = generar_pdf_etiquetas(DATOS_DEMANDA)
        self.assertIsInstance(pdf_bytes, bytes)
        self.assertTrue(pdf_bytes.startswith(b'%PDF'))

    def test_retorna_etiquetas_meta(self):
        _, etiquetas = generar_pdf_etiquetas(DATOS_DEMANDA)
        self.assertEqual(len(etiquetas), 1)

    def test_etiqueta_tiene_uuid(self):
        _, etiquetas = generar_pdf_etiquetas(DATOS_DEMANDA)
        import uuid
        uuid.UUID(str(etiquetas[0]['uuid']))  # lanza si no es UUID válido

    def test_etiqueta_tiene_digito_verificador(self):
        _, etiquetas = generar_pdf_etiquetas(DATOS_DEMANDA)
        self.assertEqual(len(etiquetas[0]['digito_verificador']), 6)

    def test_etiqueta_tiene_fecha_caducidad(self):
        _, etiquetas = generar_pdf_etiquetas(DATOS_DEMANDA)
        caducidad = etiquetas[0]['fecha_caducidad']
        self.assertEqual(caducidad.hour, 23)
        self.assertEqual(caducidad.minute, 59)

    def test_numero_sobres_correcto(self):
        datos = {**DATOS_DEMANDA, 'numero_sobres': 3}
        _, etiquetas = generar_pdf_etiquetas(datos)
        self.assertEqual(len(etiquetas), 3)

    def test_sobres_numerados_consecutivamente(self):
        datos = {**DATOS_DEMANDA, 'numero_sobres': 3}
        _, etiquetas = generar_pdf_etiquetas(datos)
        numeros = [e['numero_sobre'] for e in etiquetas]
        self.assertEqual(numeros, [1, 2, 3])

    def test_uuids_unicos(self):
        datos = {**DATOS_DEMANDA, 'numero_sobres': 5}
        _, etiquetas = generar_pdf_etiquetas(datos)
        uuids = [e['uuid'] for e in etiquetas]
        self.assertEqual(len(uuids), len(set(uuids)))

    def test_20_sobres_genera_pdf(self):
        datos = {**DATOS_DEMANDA, 'numero_sobres': 20}
        pdf_bytes, etiquetas = generar_pdf_etiquetas(datos)
        self.assertTrue(pdf_bytes.startswith(b'%PDF'))
        self.assertEqual(len(etiquetas), 20)

    def test_contestacion_genera_pdf(self):
        pdf_bytes, etiquetas = generar_pdf_etiquetas(DATOS_CONTESTACION)
        self.assertTrue(pdf_bytes.startswith(b'%PDF'))
        self.assertEqual(len(etiquetas), 2)

    def test_datos_invalidos_lanza_error(self):
        with self.assertRaises(ValueError):
            generar_pdf_etiquetas({**DATOS_DEMANDA, 'numero_sobres': 0})