"""
test_formulario.py — Pruebas unitarias + Selenium para la app Buzon
"""

from datetime import timedelta
from unittest.mock import patch, MagicMock
import uuid

from django.test import TestCase, Client
from django.urls import reverse, resolve
from django.utils import timezone
from django.contrib.messages import get_messages

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

from web.models import (
    BuzonDemanda, BuzonContestacion, BuzonOtros,
    TipoPromocion, Ponencia,
)
from web.forms import (
    BuzonDemandaForm, BuzonContestacionForm, BuzonOtrosForm,
    BuzonAlegatosForm, BuzonInformeAutoridadForm, BuzonRecursoForm,
    BuzonIncidenteForm, BuzonAmparoForm, BuzonExpedienteRAGForm,
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

# Solo para formularios
BASE_FORM_DATA = {
    **BASE_DATA,
    'correo_electronico_confirmacion': 'usuario@example.com',
}

EXPEDIENTE_DATA = {
    'numero_expediente': '001/2024',
    'anio': 2024,
    'ponencia': Ponencia.PONENCIA_1,
}

# PDF + etiquetas simulados para evitar dependencia del servicio real
FAKE_UUID = uuid.uuid4()
FAKE_ETIQUETAS = [{"uuid": FAKE_UUID, "digito_verificador": "ABC123", "numero_sobre": 1}]
FAKE_PDF = b"%PDF-1.4 fake"


def mock_generar_pdf(datos):
    """Mock del servicio PDF para no depender de lógica externa."""
    return FAKE_PDF, FAKE_ETIQUETAS


# ===========================================================================
# 1. PRUEBAS DE MODELOS
# ===========================================================================

class TestDefaultFechaRecibir(TestCase):

    def test_es_medianoche(self):
        from web.models import default_fecha_recibir
        resultado = default_fecha_recibir()
        self.assertEqual(resultado.hour, 0)
        self.assertEqual(resultado.minute, 0)
        self.assertEqual(resultado.second, 0)

    def test_es_dia_siguiente(self):
        from web.models import default_fecha_recibir
        hoy = timezone.localdate()
        resultado = default_fecha_recibir()
        self.assertEqual(resultado.date(), hoy + timedelta(days=1))

    def test_es_aware(self):
        from web.models import default_fecha_recibir
        resultado = default_fecha_recibir()
        self.assertIsNotNone(resultado.tzinfo)


class TestBuzonConExpediente(TestCase):

    MODELOS_CON_EXPEDIENTE = [
        (BuzonContestacion,     TipoPromocion.CONTESTACION),
        (BuzonOtros,            TipoPromocion.OTROS),
    ]

    def _crear(self, modelo, tipo):
        data = {**BASE_DATA, **EXPEDIENTE_DATA, 'tipo_promocion': tipo}
        if modelo == BuzonOtros:
            data['especifique'] = 'Prueba'
        return modelo.objects.create(**data)

    def test_todos_se_crean(self):
        for modelo, tipo in self.MODELOS_CON_EXPEDIENTE:
            with self.subTest(modelo=modelo.__name__):
                obj = self._crear(modelo, tipo)
                self.assertIsNotNone(obj.pk)

    def test_str_incluye_tipo_legible(self):
        obj = self._crear(BuzonContestacion, TipoPromocion.CONTESTACION)
        self.assertIn('Contestación', str(obj))


# ===========================================================================
# 2. PRUEBAS DE FORMULARIOS
# ===========================================================================

class TestBuzonDemandaForm(TestCase):

    def _data(self, **kwargs):
        base = {**BASE_FORM_DATA}
        base.update(kwargs)
        return base

    def test_form_valido(self):
        form = BuzonDemandaForm(data=self._data())
        self.assertTrue(form.is_valid(), form.errors)

    def test_correos_distintos_invalido(self):
        form = BuzonDemandaForm(data=self._data(
            correo_electronico_confirmacion='otro@example.com'
        ))
        self.assertFalse(form.is_valid())
        self.assertIn('correo_electronico_confirmacion', form.errors)

    def test_correo_requerido(self):
        form = BuzonDemandaForm(data=self._data(correo_electronico=''))
        self.assertFalse(form.is_valid())


class TestBuzonOtrosForm(TestCase):

    def _data(self, **kwargs):
        base = {
            **BASE_FORM_DATA,
            **EXPEDIENTE_DATA,
            'tipo_promocion': TipoPromocion.OTROS,
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
            **BASE_FORM_DATA,
            **EXPEDIENTE_DATA,
            'tipo_promocion': tipo,
        }

    def test_formularios_validos(self):
        for FormClass, tipo in self.CASOS:
            with self.subTest(form=FormClass.__name__):
                form = FormClass(data=self._base(tipo))
                self.assertTrue(form.is_valid(), form.errors)


# ===========================================================================
# 3. PRUEBAS DE VISTAS (sin Selenium — mock del PDF)
# ===========================================================================

PDF_PATH = 'web.views.generar_pdf_etiquetas'


class TestBuzonCrearViewGET(TestCase):

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
    """
    La vista devuelve un PDF al guardar correctamente.
    Usamos mock para no depender del servicio PDF real.
    """

    def setUp(self):
        self.client = Client()
        self.url = reverse('buzon_crear')

    def _data_demanda(self, **kwargs):
        base = {**BASE_FORM_DATA}
        base.update(kwargs)
        return base

    @patch(PDF_PATH, side_effect=mock_generar_pdf)
    def test_devuelve_pdf_tras_guardar(self, _mock):
        response = self.client.post(self.url, self._data_demanda())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')

    @patch(PDF_PATH, side_effect=mock_generar_pdf)
    def test_crea_registro_en_db(self, _mock):
        self.assertEqual(BuzonDemanda.objects.count(), 0)
        self.client.post(self.url, self._data_demanda())
        self.assertEqual(BuzonDemanda.objects.count(), 1)

    @patch(PDF_PATH, side_effect=mock_generar_pdf)
    def test_crea_etiquetas_en_db(self, _mock):
        from web.models import Etiqueta
        self.client.post(self.url, self._data_demanda())
        self.assertEqual(Etiqueta.objects.count(), 1)

    @patch(PDF_PATH, side_effect=ValueError("Error de prueba"))
    def test_error_pdf_muestra_mensaje(self, _mock):
        response = self.client.post(self.url, self._data_demanda())
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'Realizar_registro/buzon_form.html')

    @patch(PDF_PATH, side_effect=ValueError("Error de prueba"))
    def test_error_pdf_no_crea_registro(self, _mock):
        self.client.post(self.url, self._data_demanda())
        self.assertEqual(BuzonDemanda.objects.count(), 0)

    def test_codigo_200_si_invalido(self):
        response = self.client.post(self.url, {})
        self.assertEqual(response.status_code, 200)

    def test_no_crea_registro_si_invalido(self):
        self.client.post(self.url, {})
        self.assertEqual(BuzonDemanda.objects.count(), 0)

    def test_form_con_errores_en_contexto(self):
        response = self.client.post(self.url, self._data_demanda(correo_electronico=''))
        form = response.context['form']
        self.assertTrue(form.errors)

    @patch(PDF_PATH, side_effect=mock_generar_pdf)
    def test_post_contestacion_crea_registro(self, _mock):
        data = {
            **BASE_FORM_DATA,          # ← incluye correo_electronico_confirmacion
            **EXPEDIENTE_DATA,
            'tipo_promocion': TipoPromocion.CONTESTACION,
            }
        self.client.post(self.url, data)
        self.assertEqual(BuzonContestacion.objects.count(), 1)


class TestBuzonFormParcialView(TestCase):

    def setUp(self):
        self.client = Client()
        self.url = reverse('buzon_form_parcial')

    def test_codigo_http_200(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_template_correcto(self):
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'Realizar_registro/campos_extra.html')

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

    def test_reverse_buzon_crear(self):
        self.assertEqual(reverse('buzon_crear'), '/buzon/')

    def test_resolve_buzon_crear(self):
        match = resolve('/buzon/')
        self.assertEqual(match.url_name, 'buzon_crear')

    def test_vista_buzon_crear(self):
        match = resolve('/buzon/')
        self.assertEqual(match.func, views.buzon_crear)

    def test_reverse_buzon_form_parcial(self):
        self.assertEqual(reverse('buzon_form_parcial'), '/buzon/form-parcial/')

    def test_resolve_buzon_form_parcial(self):
        match = resolve('/buzon/form-parcial/')
        self.assertEqual(match.url_name, 'buzon_form_parcial')

    def test_vista_buzon_form_parcial(self):
        match = resolve('/buzon/form-parcial/')
        self.assertEqual(match.func, views.buzon_form_parcial)

    def test_nombres_son_distintos(self):
        self.assertNotEqual(reverse('buzon_crear'), reverse('buzon_form_parcial'))


# ===========================================================================
# 5. PRUEBAS SELENIUM (navegador real)
# ===========================================================================

SELENIUM_URL = "http://selenium:4444/wd/hub"
APP_URL = "http://web:8000/buzon/"


def crear_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Remote(
        command_executor=SELENIUM_URL,
        options=options,
    )
    driver.implicitly_wait(5)
    return driver


class TestSeleniumBuzonForm(TestCase):
    """
    Pruebas de interfaz con Selenium.
    Requiere docker-compose con el servicio 'selenium' activo.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        try:
            cls.driver = crear_driver()
            cls.disponible = True
        except Exception:
            cls.disponible = False

    @classmethod
    def tearDownClass(cls):
        if getattr(cls, 'disponible', False):
            cls.driver.quit()
        super().tearDownClass()

    def setUp(self):
        if not self.disponible:
            self.skipTest("Selenium no disponible")

    # --- Helpers ---

    def _abrir(self):
        self.driver.get(APP_URL)
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, "buzon-form"))
        )

    def _llenar_base(self, correo="test@example.com", sobres="1"):
        self.driver.find_element(By.NAME, "correo_electronico").clear()
        self.driver.find_element(By.NAME, "correo_electronico").send_keys(correo)
        self.driver.find_element(By.NAME, "correo_electronico_confirmacion").clear()
        self.driver.find_element(By.NAME, "correo_electronico_confirmacion").send_keys(correo)
        self.driver.find_element(By.NAME, "numero_sobres").clear()
        self.driver.find_element(By.NAME, "numero_sobres").send_keys(sobres)

    def _seleccionar_tipo(self, tipo):
        select = Select(self.driver.find_element(By.ID, "id_tipo_promocion"))
        select.select_by_value(tipo)
        # Esperar a que carguen los campos extra
        WebDriverWait(self.driver, 5).until(
            EC.invisibility_of_element_located((By.CSS_SELECTOR, "#campos-loading.visible"))
        )

    # --- Tests ---

    def test_pagina_carga_correctamente(self):
        self._abrir()
        self.assertIn("Buzón Electrónico", self.driver.title)

    def test_campos_base_visibles(self):
        self._abrir()
        self.assertTrue(self.driver.find_element(By.NAME, "correo_electronico").is_displayed())
        self.assertTrue(self.driver.find_element(By.NAME, "numero_sobres").is_displayed())

    def test_cambio_tipo_carga_campos_extra(self):
        self._abrir()
        self._seleccionar_tipo(TipoPromocion.CONTESTACION)
        WebDriverWait(self.driver, 5).until(
            EC.presence_of_element_located((By.NAME, "numero_expediente"))
        )
        self.assertTrue(self.driver.find_element(By.NAME, "numero_expediente").is_displayed())

    def test_demanda_no_muestra_campos_extra(self):
        self._abrir()
        self._seleccionar_tipo(TipoPromocion.DEMANDA)
        campos = self.driver.find_elements(By.NAME, "numero_expediente")
        self.assertEqual(len(campos), 0)

    def test_otros_muestra_campo_especifique(self):
        self._abrir()
        self._seleccionar_tipo(TipoPromocion.OTROS)
        WebDriverWait(self.driver, 5).until(
            EC.presence_of_element_located((By.NAME, "especifique"))
        )
        self.assertTrue(self.driver.find_element(By.NAME, "especifique").is_displayed())

    def test_correos_distintos_muestra_error_html5(self):
        self._abrir()
        self.driver.find_element(By.NAME, "correo_electronico").send_keys("a@a.com")
        confirmacion = self.driver.find_element(By.NAME, "correo_electronico_confirmacion")
        confirmacion.send_keys("b@b.com")
        confirmacion.send_keys("\t")  # Trigger blur
        # El campo debe marcar validación nativa
        valido = self.driver.execute_script(
            "return arguments[0].validity.valid", confirmacion
        )
        self.assertFalse(valido)

    @patch(PDF_PATH, side_effect=mock_generar_pdf)
    def test_submit_demanda_valida_retorna_pdf(self, _mock):
        self._abrir()
        self._llenar_base()
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        WebDriverWait(self.driver, 10).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        content_type = self.driver.execute_script("return document.contentType")
        self.assertEqual(content_type, "application/pdf")

# ===========================================================================
# 1b. PRUEBAS DEL MODELO ETIQUETA
# ===========================================================================

from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from web.models import Etiqueta

class TestEtiqueta(TestCase):

    def _crear_etiqueta(self, delta_segundos=3600):
        """Crea una etiqueta ligada a un BuzonDemanda."""
        buzon = BuzonDemanda.objects.create(**BASE_DATA)
        ct = ContentType.objects.get_for_model(buzon)
        return Etiqueta.objects.create(
            content_type=ct,
            object_id=buzon.pk,
            fecha_caducidad=timezone.now() + timezone.timedelta(seconds=delta_segundos),
            numero_sobre=1,
        )

    def test_str_contiene_digito_y_sobre(self):
        etiqueta = self._crear_etiqueta()
        resultado = str(etiqueta)
        self.assertIn(etiqueta.digito_verificador, resultado)
        self.assertIn('1', resultado)

    def test_digito_verificador_6_caracteres(self):
        etiqueta = self._crear_etiqueta()
        self.assertEqual(len(etiqueta.digito_verificador), 6)

    def test_esta_vigente_true(self):
        etiqueta = self._crear_etiqueta(delta_segundos=3600)
        self.assertTrue(etiqueta.esta_vigente)

    def test_esta_vigente_false(self):
        etiqueta = self._crear_etiqueta(delta_segundos=-3600)
        self.assertFalse(etiqueta.esta_vigente)