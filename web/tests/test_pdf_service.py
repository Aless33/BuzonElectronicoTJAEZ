"""
Pruebas unitarias TDD para el servicio de generación de PDF.

Cubre validaciones, reglas de negocio y comportamientos descritos
en el SRS: RF-02, RF-03, RF-04, CU-02, RN-1, RN-2 y RN-3.

Ejecutar con:
    python manage.py test web.tests.test_pdf_service -v 2
"""

from django.test import TestCase
from django.utils import timezone

from web.services.pdf_service import (
    _calcular_caducidad,
    _generar_digito_verificador,
    _validar_datos,
    generar_pdf_etiquetas,
)


def datos_validos_seguimiento(**overrides):
    """
    Retorna datos válidos para un trámite de seguimiento.
    """
    base = {
        "tipo_promocion": "CONTESTACION",
        "numero_expediente": "12",
        "anio": 2019,
        "ponencia": "PRIMERA PONENCIA",
        "correo_ciudadano": "ciudadano@example.com",
        "numero_sobres": 1,
    }
    base.update(overrides)
    return base


def datos_validos_inicial(**overrides):
    """
    Retorna datos válidos para un trámite inicial.
    """
    base = {
        "tipo_promocion": "DEMANDA",
        "numero_expediente": None,
        "anio": None,
        "ponencia": None,
        "correo_ciudadano": "ciudadano@example.com",
        "numero_sobres": 1,
    }
    base.update(overrides)
    return base


class TestGenerarDigitoVerificador(TestCase):
    """
    Pruebas para la generación del dígito verificador.
    """

    def test_longitud_es_seis_caracteres(self):
        """
        El dígito verificador debe tener exactamente 6 caracteres.
        """
        digito = _generar_digito_verificador()

        self.assertEqual(len(digito), 6)

    def test_solo_contiene_alfanumericos_mayusculas(self):
        """
        Debe contener únicamente letras mayúsculas y dígitos.
        """
        import string

        permitidos = set(string.ascii_uppercase + string.digits)

        for _ in range(20):
            digito = _generar_digito_verificador()

            self.assertTrue(
                set(digito).issubset(permitidos),
                (
                    f"Dígito '{digito}' contiene caracteres "
                    "no permitidos."
                ),
            )

    def test_genera_valores_diferentes_en_cada_llamada(self):
        """
        Dos llamadas consecutivas deben producir valores distintos.
        """
        digitos = {_generar_digito_verificador() for _ in range(50)}

        self.assertGreater(len(digitos), 1)


class TestCalcularCaducidad(TestCase):
    """
    Verifica que la caducidad se establezca al final del día actual.
    """

    def test_caducidad_es_a_las_23_59_del_dia_actual(self):
        """
        La caducidad debe ser a las 23:59:59 de hoy.
        """
        caducidad = _calcular_caducidad()
        hoy = timezone.localdate()

        self.assertEqual(caducidad.date(), hoy)
        self.assertEqual(caducidad.time().hour, 23)
        self.assertEqual(caducidad.time().minute, 59)
        self.assertEqual(caducidad.time().second, 59)

    def test_caducidad_es_timezone_aware(self):
        """
        El datetime de caducidad debe ser timezone-aware.
        """
        caducidad = _calcular_caducidad()

        self.assertIsNotNone(caducidad.tzinfo)


class TestValidarDatos(TestCase):
    """
    Pruebas para las reglas de validación previas a generar el PDF.
    """

    def test_tipo_promocion_requerido(self):
        """
        Debe lanzar ValueError si falta el tipo de promoción.
        """
        datos = datos_validos_seguimiento(tipo_promocion="")

        with self.assertRaises(ValueError) as ctx:
            _validar_datos(datos)

        self.assertIn("tipo de promoción es obligatorio", str(ctx.exception))

    def test_tipo_promocion_invalido(self):
        """
        Debe rechazar tipos que no estén en el catálogo.
        """
        datos = datos_validos_seguimiento(tipo_promocion="INVENTADO")

        with self.assertRaises(ValueError) as ctx:
            _validar_datos(datos)

        self.assertIn("inválido", str(ctx.exception))

    def test_tipo_promocion_valido_no_lanza_error(self):
        """
        Un tipo válido de seguimiento no debe levantar excepción.
        """
        tipos_validos = (
            "CONTESTACION",
            "ALEGATOS",
            "AMPARO",
            "OTROS",
        )

        for tipo in tipos_validos:
            datos = datos_validos_seguimiento(tipo_promocion=tipo)

            try:
                _validar_datos(datos)
            except ValueError as error:
                self.fail(
                    "_validar_datos lanzó ValueError para "
                    f"tipo '{tipo}': {error}"
                )

    def test_tramite_inicial_no_debe_tener_expediente(self):
        """
        Demanda con número de expediente debe ser rechazada.
        """
        datos = datos_validos_inicial(numero_expediente="999")

        with self.assertRaises(ValueError) as ctx:
            _validar_datos(datos)

        self.assertIn("iniciales", str(ctx.exception))

    def test_tramite_inicial_no_debe_tener_anio(self):
        """
        Demanda con año debe ser rechazada.
        """
        datos = datos_validos_inicial(anio=2024)

        with self.assertRaises(ValueError) as ctx:
            _validar_datos(datos)

        self.assertIn("iniciales", str(ctx.exception))

    def test_tramite_inicial_no_debe_tener_ponencia(self):
        """
        Demanda con ponencia debe ser rechazada.
        """
        datos = datos_validos_inicial(ponencia="PRIMERA PONENCIA")

        with self.assertRaises(ValueError) as ctx:
            _validar_datos(datos)

        self.assertIn("iniciales", str(ctx.exception))

    def test_tramite_inicial_sin_datos_de_expediente_es_valido(self):
        """
        Una demanda sin expediente, año ni ponencia debe ser válida.
        """
        datos = datos_validos_inicial()

        try:
            _validar_datos(datos)
        except ValueError as error:
            self.fail(f"Demanda válida lanzó error: {error}")

    def test_rag_inicial_es_tratado_como_inicial(self):
        """
        EXPEDIENTE_RAG_INICIAL debe rechazar campos de expediente.
        """
        datos = datos_validos_inicial(
            tipo_promocion="EXPEDIENTE_RAG_INICIAL",
            numero_expediente="100",
        )

        with self.assertRaises(ValueError):
            _validar_datos(datos)

    def test_seguimiento_sin_expediente_es_invalido(self):
        """
        Contestación sin número de expediente debe ser rechazada.
        """
        datos = datos_validos_seguimiento(numero_expediente=None)

        with self.assertRaises(ValueError) as ctx:
            _validar_datos(datos)

        self.assertIn("expediente", str(ctx.exception))

    def test_seguimiento_sin_anio_es_invalido(self):
        """
        Contestación sin año debe ser rechazada.
        """
        datos = datos_validos_seguimiento(anio=None)

        with self.assertRaises(ValueError) as ctx:
            _validar_datos(datos)

        self.assertIn("año", str(ctx.exception))

    def test_correo_vacio_es_invalido(self):
        """
        Un correo vacío debe ser rechazado.
        """
        datos = datos_validos_seguimiento(correo_ciudadano="")

        with self.assertRaises(ValueError) as ctx:
            _validar_datos(datos)

        self.assertIn("correo", str(ctx.exception))

    def test_correo_sin_arroba_es_invalido(self):
        """
        Un correo sin arroba debe ser rechazado.
        """
        datos = datos_validos_seguimiento(
            correo_ciudadano="correosinArroba.com",
        )

        with self.assertRaises(ValueError) as ctx:
            _validar_datos(datos)

        self.assertIn("correo", str(ctx.exception))

    def test_correo_valido_no_lanza_error(self):
        """
        Un correo con arroba debe pasar la validación.
        """
        datos = datos_validos_seguimiento(
            correo_ciudadano="ok@tribunal.gob.mx",
        )

        try:
            _validar_datos(datos)
        except ValueError as error:
            self.fail(f"Correo válido lanzó error: {error}")

    def test_numero_sobres_cero_es_invalido(self):
        """
        Cero sobres debe ser rechazado.
        """
        datos = datos_validos_seguimiento(numero_sobres=0)

        with self.assertRaises(ValueError) as ctx:
            _validar_datos(datos)

        self.assertIn("sobres", str(ctx.exception))

    def test_numero_sobres_negativo_es_invalido(self):
        """
        Un número negativo de sobres debe ser rechazado.
        """
        datos = datos_validos_seguimiento(numero_sobres=-1)

        with self.assertRaises(ValueError) as ctx:
            _validar_datos(datos)

        self.assertIn("sobres", str(ctx.exception))

    def test_numero_sobres_mayor_a_20_es_invalido(self):
        """
        Más de 20 sobres debe ser rechazado.
        """
        datos = datos_validos_seguimiento(numero_sobres=21)

        with self.assertRaises(ValueError) as ctx:
            _validar_datos(datos)

        self.assertIn("20", str(ctx.exception))

    def test_numero_sobres_veinte_es_valido(self):
        """
        Exactamente 20 sobres debe ser válido.
        """
        datos = datos_validos_seguimiento(numero_sobres=20)

        try:
            _validar_datos(datos)
        except ValueError as error:
            self.fail(f"20 sobres lanzó error: {error}")


class TestGenerarPdfEtiquetas(TestCase):
    """
    Pruebas del generador completo de PDF.
    """

    def test_retorna_bytes_no_vacios_para_datos_validos(self):
        """
        El PDF generado debe ser bytes no vacíos.
        """
        pdf_bytes, _ = generar_pdf_etiquetas(datos_validos_seguimiento())

        self.assertIsInstance(pdf_bytes, bytes)
        self.assertGreater(len(pdf_bytes), 0)

    def test_pdf_comienza_con_firma_pdf(self):
        """
        Los bytes generados deben iniciar con la firma de un PDF.
        """
        pdf_bytes, _ = generar_pdf_etiquetas(datos_validos_seguimiento())

        self.assertTrue(
            pdf_bytes.startswith(b"%PDF"),
            "El archivo generado no es un PDF válido.",
        )

    def test_retorna_metadatos_por_cada_sobre(self):
        """
        Se deben retornar tantos metadatos como sobres solicitados.
        """
        numero_sobres = 3

        _, etiquetas_meta = generar_pdf_etiquetas(
            datos_validos_seguimiento(numero_sobres=numero_sobres)
        )

        self.assertEqual(len(etiquetas_meta), numero_sobres)

    def test_cada_etiqueta_tiene_uuid_unico(self):
        """
        Cada etiqueta debe tener un UUID diferente.
        """
        _, etiquetas_meta = generar_pdf_etiquetas(
            datos_validos_seguimiento(numero_sobres=5)
        )

        uuids = [etiqueta["uuid"] for etiqueta in etiquetas_meta]

        self.assertEqual(
            len(uuids),
            len(set(uuids)),
            "Se encontraron UUIDs duplicados.",
        )

    def test_cada_etiqueta_tiene_digito_verificador(self):
        """
        Cada metadato debe incluir su dígito verificador.
        """
        _, etiquetas_meta = generar_pdf_etiquetas(datos_validos_seguimiento())

        for etiqueta in etiquetas_meta:
            self.assertIn("digito_verificador", etiqueta)
            self.assertEqual(len(etiqueta["digito_verificador"]), 6)

    def test_numero_de_sobre_es_consecutivo(self):
        """
        Los sobres deben numerarse de 1 a N consecutivamente.
        """
        _, etiquetas_meta = generar_pdf_etiquetas(
            datos_validos_seguimiento(numero_sobres=4)
        )

        numeros = [etiqueta["numero_sobre"] for etiqueta in etiquetas_meta]

        self.assertEqual(numeros, [1, 2, 3, 4])

    def test_fecha_caducidad_es_a_las_23_59_del_dia_actual(self):
        """
        La caducidad de cada etiqueta debe ser 23:59:59 de hoy.
        """
        _, etiquetas_meta = generar_pdf_etiquetas(datos_validos_seguimiento())
        hoy = timezone.localdate()

        for etiqueta in etiquetas_meta:
            caducidad = etiqueta["fecha_caducidad"]
            self.assertEqual(caducidad.date(), hoy)
            self.assertEqual(caducidad.time().hour, 23)
            self.assertEqual(caducidad.time().minute, 59)

    def test_tramite_inicial_genera_pdf_sin_expediente(self):
        """
        Una demanda inicial debe generar PDF exitosamente sin expediente.
        """
        pdf_bytes, etiquetas_meta = generar_pdf_etiquetas(
            datos_validos_inicial()
        )

        self.assertTrue(pdf_bytes.startswith(b"%PDF"))
        self.assertEqual(len(etiquetas_meta), 1)

    def test_lanza_value_error_con_datos_invalidos(self):
        """
        Datos inválidos deben lanzar ValueError antes de generar el PDF.
        """
        datos = datos_validos_seguimiento(correo_ciudadano="invalido")

        with self.assertRaises(ValueError):
            generar_pdf_etiquetas(datos)

    def test_genera_pdf_con_un_solo_sobre(self):
        """
        El caso base de un sobre debe funcionar correctamente.
        """
        pdf_bytes, etiquetas_meta = generar_pdf_etiquetas(
            datos_validos_seguimiento(numero_sobres=1)
        )

        self.assertTrue(pdf_bytes.startswith(b"%PDF"))
        self.assertEqual(len(etiquetas_meta), 1)

    def test_genera_pdf_con_veinte_sobres(self):
        """
        El límite máximo de 20 sobres debe procesarse sin errores.
        """
        pdf_bytes, etiquetas_meta = generar_pdf_etiquetas(
            datos_validos_seguimiento(numero_sobres=20)
        )

        self.assertTrue(pdf_bytes.startswith(b"%PDF"))
        self.assertEqual(len(etiquetas_meta), 20)

    def test_tipo_de_dato_uuid_es_string(self):
        """
        El UUID en los metadatos debe ser una cadena de texto.
        """
        _, etiquetas_meta = generar_pdf_etiquetas(datos_validos_seguimiento())

        for etiqueta in etiquetas_meta:
            self.assertIsInstance(etiqueta["uuid"], str)

    def test_uuid_tiene_formato_valido(self):
        """
        El UUID generado debe tener formato UUID v4.
        """
        import uuid as uuid_mod

        _, etiquetas_meta = generar_pdf_etiquetas(datos_validos_seguimiento())

        for etiqueta in etiquetas_meta:
            try:
                parsed = uuid_mod.UUID(etiqueta["uuid"])
                self.assertEqual(parsed.version, 4)
            except ValueError:
                self.fail(f"UUID inválido: {etiqueta['uuid']}")
