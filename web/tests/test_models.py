from datetime import timedelta
from uuid import uuid4

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone

from web.models import (
    BuzonDemanda,
    BuzonContestacion,
    BuzonOtros,
    Etiqueta,
    EstatusPromocion,
    Ponencia,
    TipoPromocion,
)


class BuzonModelTestCase(TestCase):
    """
    Pruebas unitarias de modelos
    """

    def test_crear_buzon_demanda(self):
        """
        Se espera poder crear un registro de BuzonDemanda con campos base.
        """
        buzon = BuzonDemanda.objects.create(
            tipo_promocion=TipoPromocion.DEMANDA,
            correo_electronico="ciudadano@test.com",
            numero_sobres=2,
        )

        self.assertIsNotNone(buzon.pk)
        self.assertEqual(buzon.tipo_promocion, TipoPromocion.DEMANDA)
        self.assertEqual(buzon.correo_electronico, "ciudadano@test.com")
        self.assertEqual(buzon.numero_sobres, 2)

    def test_crear_buzon_contestacion(self):
        """
        Se espera poder crear una promoción de Contestación con datos
        de expediente.
        """

        buzon = BuzonContestacion.objects.create(
            tipo_promocion=TipoPromocion.CONTESTACION,
            correo_electronico="ciudadano@test.com",
            numero_sobres=1,
            numero_expediente="TJAEZ-123/2026",
            anio=2026,
            ponencia=Ponencia.PONENCIA_1,
        )

        self.assertIsNotNone(buzon.pk)
        self.assertEqual(buzon.numero_expediente, "TJAEZ-123/2026")
        self.assertEqual(buzon.anio, 2026)
        self.assertEqual(buzon.ponencia, Ponencia.PONENCIA_1)

    def test_crear_buzon_otros(self):
        """

        Se espera poder crear una promoción de tipo Otros con el campo
        especifique.
        """

        buzon = BuzonOtros.objects.create(
            tipo_promocion=TipoPromocion.OTROS,
            correo_electronico="ciudadano@test.com",
            numero_sobres=1,
            numero_expediente="EXP-999/2026",
            anio=2026,
            ponencia=Ponencia.PONENCIA_2,
            especifique="Promoción especial",
        )

        self.assertIsNotNone(buzon.pk)
        self.assertEqual(buzon.especifique, "Promoción especial")

    def test_str_buzon_demanda(self):
        """
        Se espera que el método __str__ del buzón muestre el id, tipo
        de promoción y correo.
        """

        buzon = BuzonDemanda.objects.create(
            tipo_promocion=TipoPromocion.DEMANDA,
            correo_electronico="ciudadano@test.com",
            numero_sobres=1,
        )

        esperado = (
            f"#{buzon.pk} - {buzon.get_tipo_promocion_display()} "
            f"({buzon.correo_electronico})"
        )

        self.assertEqual(str(buzon), esperado)

    def test_estatus_por_defecto_es_activo(self):
        """
        Se espera que todo buzón nuevo tenga estatus ACTIVO por defecto.
        """

        buzon = BuzonDemanda.objects.create(
            tipo_promocion=TipoPromocion.DEMANDA,
            correo_electronico="ciudadano@test.com",
            numero_sobres=1,
        )

        self.assertEqual(buzon.estatus, EstatusPromocion.ACTIVO)

    def test_fecha_recibir_se_asigna_por_defecto(self):
        """
        Se espera que fecha_recibir se genere automáticamente.
        """

        buzon = BuzonDemanda.objects.create(
            tipo_promocion=TipoPromocion.DEMANDA,
            correo_electronico="ciudadano@test.com",
            numero_sobres=1,
        )

        self.assertIsNotNone(buzon.fecha_recibir)
        self.assertTrue(timezone.is_aware(buzon.fecha_recibir))

    def test_tipo_promocion_invalido_no_pasa_validacion(self):
        """
        Se espera que un tipo de promoción fuera de las opciones válidas
        no pase la validación del modelo.
        """

        buzon = BuzonDemanda(
            tipo_promocion="TIPO_INVALIDO",
            correo_electronico="ciudadano@test.com",
            numero_sobres=1,
        )

        with self.assertRaises(ValidationError):
            buzon.full_clean()


class EtiquetaModelTestCase(TestCase):
    """
    Pruebas unitarias del modelo Etiqueta.
    """

    def setUp(self):
        self.buzon = BuzonDemanda.objects.create(
            tipo_promocion=TipoPromocion.DEMANDA,
            correo_electronico="ciudadano@test.com",
            numero_sobres=2,
        )
        self.content_type = ContentType.objects.get_for_model(self.buzon)

    def test_crear_etiqueta(self):
        """
        Se espera poder crear una etiqueta relacionada a un buzón.
        """

        etiqueta = Etiqueta.objects.create(
            content_type=self.content_type,
            object_id=self.buzon.pk,
            fecha_caducidad=timezone.now() + timedelta(hours=1),
            numero_sobre=1,
        )

        self.assertIsNotNone(etiqueta.pk)
        self.assertEqual(etiqueta.buzon, self.buzon)
        self.assertEqual(etiqueta.numero_sobre, 1)

    def test_str_etiqueta(self):
        """
        Se espera que __str__ de Etiqueta incluya el dígito verificador,
        número de sobre y estado.
        """

        etiqueta = Etiqueta.objects.create(
            content_type=self.content_type,
            object_id=self.buzon.pk,
            fecha_caducidad=timezone.now() + timedelta(hours=1),
            numero_sobre=1,
        )

        esperado = (
            f"Etiqueta {etiqueta.digito_verificador} - "
            f"Sobre {etiqueta.numero_sobre} [{etiqueta.estado}]"
        )

        self.assertEqual(str(etiqueta), esperado)

    def test_etiqueta_estado_por_defecto_es_generada(self):
        """
        Se espera que una etiqueta nueva tenga estado ETIQUETA_GENERADA.
        """

        etiqueta = Etiqueta.objects.create(
            content_type=self.content_type,
            object_id=self.buzon.pk,
            fecha_caducidad=timezone.now() + timedelta(hours=1),
            numero_sobre=1,
        )

        self.assertEqual(
            etiqueta.estado,
            Etiqueta.ESTADO_ETIQUETA_GENERADA
        )

    def test_etiqueta_uuid_se_genera_automaticamente(self):
        """
        Se espera que la etiqueta genere automáticamente un UUID.
        """
        etiqueta = Etiqueta.objects.create(
            content_type=self.content_type,
            object_id=self.buzon.pk,
            fecha_caducidad=timezone.now() + timedelta(hours=1),
            numero_sobre=1,
        )

        self.assertIsNotNone(etiqueta.uuid)

    def test_digito_verificador_tiene_6_caracteres(self):
        """
        Se espera que el dígito verificador tenga exactamente 6 caracteres.
        """
        etiqueta = Etiqueta.objects.create(
            content_type=self.content_type,
            object_id=self.buzon.pk,
            fecha_caducidad=timezone.now() + timedelta(hours=1),
            numero_sobre=1,
        )

        self.assertEqual(len(etiqueta.digito_verificador), 6)

    def test_etiqueta_se_relaciona_con_buzon_por_generic_foreign_key(self):
        """
        Se espera que la etiqueta pueda recuperar el buzón mediante
        GenericForeignKey.
        """

        etiqueta = Etiqueta.objects.create(
            content_type=self.content_type,
            object_id=self.buzon.pk,
            fecha_caducidad=timezone.now() + timedelta(hours=1),
            numero_sobre=1,
        )

        self.assertEqual(etiqueta.buzon, self.buzon)

    def test_uuid_de_etiqueta_es_unico(self):
        """
        Se espera que no puedan existir dos etiquetas con el mismo UUID.
        """

        uuid_repetido = uuid4()

        Etiqueta.objects.create(
            content_type=self.content_type,
            object_id=self.buzon.pk,
            uuid=uuid_repetido,
            fecha_caducidad=timezone.now() + timedelta(hours=1),
            numero_sobre=1,
        )

        with self.assertRaises(IntegrityError):
            Etiqueta.objects.create(
                content_type=self.content_type,
                object_id=self.buzon.pk,
                uuid=uuid_repetido,
                fecha_caducidad=timezone.now() + timedelta(hours=1),
                numero_sobre=2,
            )

    def test_etiqueta_esta_vigente_true(self):
        """
        Se espera que una etiqueta con fecha de caducidad futura esté vigente.
        """
        etiqueta = Etiqueta.objects.create(
            content_type=self.content_type,
            object_id=self.buzon.pk,
            fecha_caducidad=timezone.now() + timedelta(hours=1),
            numero_sobre=1,
        )

        self.assertTrue(etiqueta.esta_vigente)

    def test_etiqueta_esta_vigente_false(self):
        """
        Se espera que una etiqueta con fecha de caducidad pasada no esté
        vigente.
        """

        etiqueta = Etiqueta.objects.create(
            content_type=self.content_type,
            object_id=self.buzon.pk,
            fecha_caducidad=timezone.now() - timedelta(hours=1),
            numero_sobre=1,
        )

        self.assertFalse(etiqueta.esta_vigente)

    def test_estado_etiqueta_invalido_no_pasa_validacion(self):
        """

        Se espera que una etiqueta con estado inválido no pase full_clean.
        """

        etiqueta = Etiqueta(
            content_type=self.content_type,
            object_id=self.buzon.pk,
            estado="ESTADO_INVALIDO",
            fecha_caducidad=timezone.now() + timedelta(hours=1),
            numero_sobre=1,
        )

        with self.assertRaises(ValidationError):
            etiqueta.full_clean()
