"""
tests.py — Pruebas unitarias para la app Buzon
Cubre: Modelos, Formularios, Vistas y URLs
"""

from datetime import datetime, time, timedelta

from django.test import TestCase, Client
from django.urls import reverse, resolve
from django.utils import timezone
from django.contrib.messages import get_messages

from web.models import (
    BuzonDemanda, BuzonContestacion, BuzonAlegatos,
    BuzonInformeAutoridad, BuzonRecurso, BuzonIncidente,
    BuzonAmparo, BuzonExpedienteRAG, BuzonOtros,
    TipoPromocion, EstatusPromocion, Ponencia,
    default_fecha_recibir,
)
from web.forms import (
    BuzonDemandaForm, BuzonContestacionForm, BuzonAlegatosForm,
    BuzonInformeAutoridadForm, BuzonRecursoForm, BuzonIncidenteForm,
    BuzonAmparoForm, BuzonExpedienteRAGForm, BuzonOtrosForm,
    FORM_MAP,
)
from web import views


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

BASE_DATA = {
    'tipo_promocion': TipoPromocion.DEMANDA,
    'correo_electronico': 'usuario@example.com',
    'numero_sobres': 1,
}

EXPEDIENTE_DATA = {
    'numero_expediente': '001/2024',
    'anio': 2024,
    'ponencia': Ponencia.PONENCIA_1,
}


def make_demanda(**kwargs):
    """Crea y devuelve una instancia de BuzonDemanda."""
    data = {**BASE_DATA, **kwargs}
    return BuzonDemanda.objects.create(**data)


def make_contestacion(**kwargs):
    data = {**BASE_DATA, **EXPEDIENTE_DATA, 'tipo_promocion': TipoPromocion.CONTESTACION, **kwargs}
    return BuzonContestacion.objects.create(**data)


def make_otros(**kwargs):
    data = {
        **BASE_DATA,
        **EXPEDIENTE_DATA,
        'tipo_promocion': TipoPromocion.OTROS,
        'especifique': 'Prueba',
        **kwargs,
    }
    return BuzonOtros.objects.create(**data)


# ===========================================================================
# 1. PRUEBAS DE MODELOS
# ===========================================================================

class TestDefaultFechaRecibir(TestCase):
    """default_fecha_recibir debe devolver medianoche del día siguiente."""

    def test_es_medianoche(self):
        resultado = default_fecha_recibir()
        self.assertEqual(resultado.hour, 0)
        self.assertEqual(resultado.minute, 0)
        self.assertEqual(resultado.second, 0)

    def test_es_dia_siguiente(self):
        hoy = timezone.localdate()
        resultado = default_fecha_recibir()
        self.assertEqual(resultado.date(), hoy + timedelta(days=1))

    def test_es_aware(self):
        resultado = default_fecha_recibir()
        self.assertIsNotNone(resultado.tzinfo)

class TestBuzonConExpediente(TestCase):
    """Pruebas para modelos que heredan de BuzonConExpedinteBase."""

    MODELOS_CON_EXPEDIENTE = [
        (BuzonContestacion,      TipoPromocion.CONTESTACION),
        (BuzonAlegatos,          TipoPromocion.ALEGATOS),
        (BuzonInformeAutoridad,  TipoPromocion.INFORME_AUTORIDAD),
        (BuzonRecurso,           TipoPromocion.RECURSO),
        (BuzonIncidente,         TipoPromocion.INCIDENTE),
        (BuzonAmparo,            TipoPromocion.AMPARO),
        (BuzonExpedienteRAG,     TipoPromocion.EXPEDIENTE_RAG),
    ]

    def _crear(self, modelo, tipo):
        return modelo.objects.create(
            **{**BASE_DATA, **EXPEDIENTE_DATA, 'tipo_promocion': tipo}
        )

    def test_todos_se_crean(self):
        for modelo, tipo in self.MODELOS_CON_EXPEDIENTE:
            with self.subTest(modelo=modelo.__name__):
                obj = self._crear(modelo, tipo)
                self.assertIsNotNone(obj.pk)

    def test_numero_expediente_guardado(self):
        for modelo, tipo in self.MODELOS_CON_EXPEDIENTE:
            with self.subTest(modelo=modelo.__name__):
                obj = self._crear(modelo, tipo)
                self.assertEqual(obj.numero_expediente, EXPEDIENTE_DATA['numero_expediente'])

    def test_anio_guardado(self):
        for modelo, tipo in self.MODELOS_CON_EXPEDIENTE:
            with self.subTest(modelo=modelo.__name__):
                obj = self._crear(modelo, tipo)
                self.assertEqual(obj.anio, EXPEDIENTE_DATA['anio'])

    def test_ponencia_guardada(self):
        for modelo, tipo in self.MODELOS_CON_EXPEDIENTE:
            with self.subTest(modelo=modelo.__name__):
                obj = self._crear(modelo, tipo)
                self.assertEqual(obj.ponencia, Ponencia.PONENCIA_1)

    def test_str_incluye_tipo_legible(self):
        obj = make_contestacion()
        self.assertIn('Contestación', str(obj))

class TestBuzonOtros(TestCase):
    """Pruebas específicas para BuzonOtros (campo extra 'especifique')."""

    def setUp(self):
        self.obj = make_otros()

    def test_se_crea_correctamente(self):
        self.assertIsNotNone(self.obj.pk)

    def test_especifique_guardado(self):
        self.assertEqual(self.obj.especifique, 'Prueba')

    def test_str_contiene_tipo(self):
        self.assertIn('Otros', str(self.obj))

# ===========================================================================
# 2. PRUEBAS DE FORMULARIOS
# ===========================================================================

class TestBuzonOtrosForm(TestCase):
    """Formulario con campo adicional 'especifique'."""

    def _data(self, **kwargs):
        base = {
            'tipo_promocion': TipoPromocion.OTROS,
            'correo_electronico': 'test@example.com',
            'correo_electronico_confirmacion': 'test@example.com',
            'numero_sobres': 1,
            'numero_expediente': '456/2024',
            'anio': 2024,
            'ponencia': Ponencia.PONENCIA_3,
            'especifique': 'Algo más',
        }
        base.update(kwargs)
        return base

    def test_form_valido(self):
        form = BuzonOtrosForm(data=self._data())
        self.assertTrue(form.is_valid(), form.errors)

    def test_especifique_requerido(self):
        form = BuzonOtrosForm(data=self._data(especifique=''))
        self.assertFalse(form.is_valid())
        self.assertIn('especifique', form.errors)

class TestFormulariosTodosLosModelos(TestCase):
    """todos los formularios aceptan datos válidos."""

    CASOS = [
        (BuzonAlegatosForm,         TipoPromocion.ALEGATOS),
        (BuzonInformeAutoridadForm,  TipoPromocion.INFORME_AUTORIDAD),
        (BuzonRecursoForm,           TipoPromocion.RECURSO),
        (BuzonIncidenteForm,         TipoPromocion.INCIDENTE),
        (BuzonAmparoForm,            TipoPromocion.AMPARO),
        (BuzonExpedienteRAGForm,     TipoPromocion.EXPEDIENTE_RAG),
    ]

    def _base(self, tipo):
        return {
            'tipo_promocion': tipo,
            'correo_electronico': 'x@x.com',
            'correo_electronico_confirmacion': 'x@x.com',
            'numero_sobres': 1,
            'numero_expediente': '1/2025',
            'anio': 2025,
            'ponencia': Ponencia.PONENCIA_1,
        }

    def test_formularios_validos(self):
        for FormClass, tipo in self.CASOS:
            with self.subTest(form=FormClass.__name__):
                form = FormClass(data=self._base(tipo))
                self.assertTrue(form.is_valid(), form.errors)


# ===========================================================================
# 3. PRUEBAS DE VISTAS
# ===========================================================================

class TestBuzonCrearViewGET(TestCase):
    """GET a la vista principal."""

    def setUp(self):
        self.client = Client()
        self.url = reverse('buzon_crear')

    def test_codigo_http_200(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_template_correcto(self):
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'Realizar_registro/buzon_form.html')

    def test_contexto_contiene_form(self):
        response = self.client.get(self.url)
        self.assertIn('form', response.context)

    def test_contexto_contiene_tipos(self):
        response = self.client.get(self.url)
        self.assertIn('tipos', response.context)
        self.assertEqual(response.context['tipos'], TipoPromocion.choices)

    def test_contexto_tipo_actual_default(self):
        response = self.client.get(self.url)
        self.assertEqual(response.context['tipo_actual'], TipoPromocion.DEMANDA)

    def test_contexto_tipo_actual_por_querystring(self):
        response = self.client.get(self.url, {'tipo_promocion': TipoPromocion.ALEGATOS})
        self.assertEqual(response.context['tipo_actual'], TipoPromocion.ALEGATOS)

    def test_form_inicial_con_tipo(self):
        response = self.client.get(self.url, {'tipo_promocion': TipoPromocion.CONTESTACION})
        form = response.context['form']
        self.assertIsInstance(form, BuzonContestacionForm)

class TestBuzonCrearViewPOST(TestCase):
    """POST a la vista principal."""

    def setUp(self):
        self.client = Client()
        self.url = reverse('buzon_crear')

    def _post(self, data):
        return self.client.post(self.url, data, follow=True)

    def _data_demanda(self, **kwargs):
        base = {
            'tipo_promocion': TipoPromocion.DEMANDA,
            'correo_electronico': 'test@example.com',
            'correo_electronico_confirmacion': 'test@example.com',
            'numero_sobres': 1,
        }
        base.update(kwargs)
        return base

    # Formulario válido
    def test_redirige_tras_guardar(self):
        response = self.client.post(self.url, self._data_demanda())
        self.assertRedirects(response, self.url)

    def test_crea_registro_en_db(self):
        self.assertEqual(BuzonDemanda.objects.count(), 0)
        self.client.post(self.url, self._data_demanda())
        self.assertEqual(BuzonDemanda.objects.count(), 1)

    def test_mensaje_exito(self):
        response = self._post(self._data_demanda())
        msgs = list(get_messages(response.wsgi_request))
        self.assertTrue(any('correctamente' in str(m) for m in msgs))

    # Formulario inválido
    def test_codigo_200_si_invalido(self):
        response = self.client.post(self.url, {})
        self.assertEqual(response.status_code, 200)

    def test_no_redirige_si_invalido(self):
        response = self.client.post(self.url, {})
        self.assertTemplateUsed(response, 'Realizar_registro/buzon_form.html')

    def test_no_crea_registro_si_invalido(self):
        self.client.post(self.url, {})
        self.assertEqual(BuzonDemanda.objects.count(), 0)

    def test_form_con_errores_en_contexto(self):
        response = self.client.post(self.url, self._data_demanda(correo_electronico=''))
        form = response.context['form']
        self.assertTrue(form.errors)

    # POST con tipo distinto selecciona el formulario correcto
    def test_post_contestacion_usa_form_correcto(self):
        data = {
            'tipo_promocion': TipoPromocion.CONTESTACION,
            'correo_electronico': 'test@example.com',
            'correo_electronico_confirmacion': 'test@example.com',
            'numero_sobres': 1,
            'numero_expediente': '001/2024',
            'anio': 2024,
            'ponencia': Ponencia.PONENCIA_1,
        }
        self.client.post(self.url, data)
        self.assertEqual(BuzonContestacion.objects.count(), 1)

class TestBuzonFormParcialView(TestCase):
    """Vista parcial que devuelve campos extra según el tipo."""

    def setUp(self):
        self.client = Client()
        self.url = reverse('buzon_form_parcial')

    def test_codigo_http_200(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_template_correcto(self):
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'Realizar_registro/campos_extra.html')

    def test_contexto_contiene_campos_extra(self):
        response = self.client.get(self.url)
        self.assertIn('campos_extra', response.context)

    def test_demanda_no_tiene_campos_extra(self):
        response = self.client.get(self.url, {'tipo': TipoPromocion.DEMANDA})
        self.assertEqual(response.context['campos_extra'], [])

    def test_contestacion_tiene_campos_extra(self):
        response = self.client.get(self.url, {'tipo': TipoPromocion.CONTESTACION})
        nombres = [name for name, _ in response.context['campos_extra']]
        self.assertIn('numero_expediente', nombres)
        self.assertIn('anio', nombres)
        self.assertIn('ponencia', nombres)

    def test_otros_incluye_especifique(self):
        response = self.client.get(self.url, {'tipo': TipoPromocion.OTROS})
        nombres = [name for name, _ in response.context['campos_extra']]
        self.assertIn('especifique', nombres)

    def test_campos_base_excluidos(self):
        """Los campos base nunca deben aparecer como campos extra."""
        CAMPOS_BASE = {
            'tipo_promocion', 'correo_electronico',
            'correo_electronico_confirmacion', 'numero_sobres', 'fecha_recibir',
        }
        for tipo, _ in TipoPromocion.choices:
            with self.subTest(tipo=tipo):
                response = self.client.get(self.url, {'tipo': tipo})
                nombres = {name for name, _ in response.context['campos_extra']}
                self.assertEqual(nombres & CAMPOS_BASE, set())

    def test_metodo_post_no_permitido(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 405)


# ===========================================================================
# 4. PRUEBAS DE URLS
# ===========================================================================

class TestURLs(TestCase):
    """Verifica reverse(), resolve(), nombres y vistas correctas."""

    # buzon_crear
    def test_reverse_buzon_crear(self):
        url = reverse('buzon_crear')
        self.assertEqual(url, '/buzon/')

    def test_resolve_buzon_crear(self):
        match = resolve('/buzon/')
        self.assertEqual(match.url_name, 'buzon_crear')

    def test_vista_buzon_crear(self):
        match = resolve('/buzon/')
        self.assertEqual(match.func, views.buzon_crear)

    # buzon_form_parcial
    def test_reverse_buzon_form_parcial(self):
        url = reverse('buzon_form_parcial')
        self.assertEqual(url, '/buzon/form-parcial/')

    def test_resolve_buzon_form_parcial(self):
        match = resolve('/buzon/form-parcial/')
        self.assertEqual(match.url_name, 'buzon_form_parcial')

    def test_vista_buzon_form_parcial(self):
        match = resolve('/buzon/form-parcial/')
        self.assertEqual(match.func, views.buzon_form_parcial)

    # Nombres distintos
    def test_nombres_son_distintos(self):
        self.assertNotEqual(reverse('buzon_crear'), reverse('buzon_form_parcial'))