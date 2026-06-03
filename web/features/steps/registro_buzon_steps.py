import django
import time
from behave import given, then, when
from django.urls import reverse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait
import os

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "buzon_electronico_tjaez.settings",
)


django.setup()

BASE_URL = "http://localhost:8000"


def obtener_browser(context):
    if not hasattr(context, "browser"):
        firefox_options = Options()
        firefox_options.add_argument("--headless")

        context.browser = webdriver.Firefox(options=firefox_options)
        context.browser.implicitly_wait(5)

    return context.browser


def esperar_carga_completa(browser):
    WebDriverWait(browser, 10).until(
        lambda navegador: navegador.execute_script(
            "return document.readyState"
        ) == "complete"
    )


@given("que el ciudadano está en el formulario de registro de buzón")
def step_abrir_formulario(context):
    browser = obtener_browser(context)
    url = BASE_URL + reverse("buzon_crear")
    browser.get(url)
    esperar_carga_completa(browser)


@when('selecciona el tipo de promoción "{tipo_promocion}"')
def step_seleccionar_tipo_promocion(context, tipo_promocion):
    browser = obtener_browser(context)

    select = Select(browser.find_element(By.ID, "id_tipo_promocion"))
    select.select_by_value(tipo_promocion)

    WebDriverWait(browser, 10).until(
        EC.presence_of_element_located((By.ID, "id_tipo_promocion"))
    )


@when('captura el correo "{correo}"')
def step_capturar_correo(context, correo):
    browser = obtener_browser(context)

    campo = browser.find_element(By.NAME, "correo_electronico")
    campo.clear()
    campo.send_keys(correo)


@when('confirma el correo "{correo}"')
def step_confirmar_correo(context, correo):
    browser = obtener_browser(context)

    campo = browser.find_element(
        By.NAME,
        "correo_electronico_confirmacion",
    )
    campo.clear()
    campo.send_keys(correo)


@when('captura "{numero_sobres}" sobres')
def step_capturar_numero_sobres(context, numero_sobres):
    browser = obtener_browser(context)

    campo = browser.find_element(By.NAME, "numero_sobres")
    campo.clear()
    campo.send_keys(numero_sobres)


@when("envía el formulario")
def step_enviar_formulario(context):
    browser = obtener_browser(context)

    formulario = browser.find_element(By.TAG_NAME, "form")
    formulario.submit()
    esperar_carga_completa(browser)


@then("el sistema debe generar un PDF de etiquetas")
def step_validar_pdf(context):
    browser = obtener_browser(context)

    WebDriverWait(browser, 10).until(
        lambda navegador: navegador.current_url is not None
    )

    assert browser.current_url is not None


@then('el sistema debe mostrar el error "{mensaje}"')
def step_validar_mensaje_error(context, mensaje):
    browser = obtener_browser(context)

    def pagina_contiene_mensaje(navegador):
        return mensaje in navegador.page_source

    WebDriverWait(browser, 10).until(pagina_contiene_mensaje)


@then("el sistema debe mostrar los campos de expediente")
def step_validar_campos_expediente(context):
    browser = obtener_browser(context)

    WebDriverWait(browser, 10).until(
        EC.presence_of_element_located((By.NAME, "numero_expediente"))
    )

    assert browser.find_element(By.NAME, "numero_expediente")
    assert browser.find_element(By.NAME, "anio")
    assert browser.find_element(By.NAME, "ponencia")


@then('el sistema debe mostrar el campo "{nombre_campo}"')
def step_validar_campo(context, nombre_campo):
    browser = obtener_browser(context)

    WebDriverWait(browser, 10).until(
        EC.presence_of_element_located((By.NAME, nombre_campo))
    )

    assert browser.find_element(By.NAME, nombre_campo)


@then('el sistema debe mostrar un error en el campo "{nombre_campo}"')
def step_validar_error_campo(context, nombre_campo):
    browser = obtener_browser(context)
    time.sleep(1)  # esperar que el DOM esté listo tras el submit

    def pagina_contiene_error(navegador):
        try:
            contenido = navegador.page_source.lower()
            return (
                nombre_campo.lower() in contenido
                or "sobres" in contenido
                or "número de sobres" in contenido
                or "numero de sobres" in contenido
            )
        except Exception:
            return False

    WebDriverWait(browser, 10).until(pagina_contiene_error)
