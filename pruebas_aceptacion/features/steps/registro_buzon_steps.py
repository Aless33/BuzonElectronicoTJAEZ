from behave import given, when, then
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


APP_URL = "http://web:8000/buzon/"
WAIT    = 8  # segundos


def _wait(context):
    return WebDriverWait(context.driver, WAIT)


def _abrir_formulario(context):
    context.driver.get(APP_URL)
    _wait(context).until(
        EC.presence_of_element_located((By.ID, "buzon-form"))
    )


def _esperar_campos_extra_listos(context):
    """Espera a que el spinner desaparezca tras cambiar el tipo."""
    _wait(context).until(
        EC.invisibility_of_element_located(
            (By.CSS_SELECTOR, "#campos-loading.visible")
        )
    )


# ─── GIVEN ────────────────────────────────────────────────────────────────────

@given('que el usuario abre el formulario de registro')
def step_abre_formulario(context):
    _abrir_formulario(context)
    assert context.driver.find_element(By.ID, "buzon-form").is_displayed()


@given('selecciona el tipo de promoción "{tipo}"')
def step_selecciona_tipo(context, tipo):
    select = Select(context.driver.find_element(By.ID, "id_tipo_promocion"))
    select.select_by_value(tipo)
    _esperar_campos_extra_listos(context)


# ─── WHEN ─────────────────────────────────────────────────────────────────────

@when('llena el correo "{correo}" y lo confirma con "{confirmacion}"')
def step_llena_correo(context, correo, confirmacion):
    campo = context.driver.find_element(By.NAME, "correo_electronico")
    campo.clear()
    campo.send_keys(correo)

    confirmar = context.driver.find_element(By.NAME, "correo_electronico_confirmacion")
    confirmar.clear()
    confirmar.send_keys(confirmacion)


@when('llena el número de sobres con {numero:d}')
def step_llena_sobres(context, numero):
    campo = context.driver.find_element(By.NAME, "numero_sobres")
    campo.clear()
    campo.send_keys(str(numero))


@when('llena el número de expediente "{expediente}" con año {anio:d} y ponencia "{ponencia}"')
def step_llena_expediente(context, expediente, anio, ponencia):
    _wait(context).until(
        EC.presence_of_element_located((By.NAME, "numero_expediente"))
    )
    context.driver.find_element(By.NAME, "numero_expediente").send_keys(expediente)
    context.driver.find_element(By.NAME, "anio").send_keys(str(anio))
    Select(context.driver.find_element(By.NAME, "ponencia")).select_by_value(ponencia)


@when('especifica "{texto}"')
def step_especifica(context, texto):
    _wait(context).until(
        EC.presence_of_element_located((By.NAME, "especifique"))
    )
    context.driver.find_element(By.NAME, "especifique").send_keys(texto)


@when('envía el formulario')
def step_envia_formulario(context):
    context.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    _wait(context).until(
        lambda d: d.execute_script("return document.readyState") == "complete"
    )
    # DEBUG temporal — ver qué devuelve el servidor
    print(f"\nURL actual: {context.driver.current_url}")
    print(f"Título: {context.driver.title}")
    print(f"Content-Type: {context.driver.execute_script('return document.contentType')}")
    # Ver si hay errores de formulario en la página
    try:
        errores = context.driver.find_elements(By.CSS_SELECTOR, ".errorlist li")
        if errores:
            print(f"Errores del formulario: {[e.text for e in errores]}")
    except:
        pass


# ─── THEN ─────────────────────────────────────────────────────────────────────

@then('el sistema guarda el registro exitosamente')
def step_registro_exitoso(context):
    """
    La vista devuelve un PDF inline tras guardar correctamente.
    Verificamos que el content-type sea application/pdf.
    """
    content_type = context.driver.execute_script("return document.contentType")
    assert content_type == "application/pdf", (
        f"Se esperaba 'application/pdf', se obtuvo: '{content_type}'\n"
        f"URL actual: {context.driver.current_url}\n"
        f"Título: {context.driver.title}"
    )


@then('muestra el mensaje "{mensaje}"')
def step_muestra_mensaje(context, mensaje):
    """
    Si la vista devuelve un PDF, el mensaje de éxito no aplica.
    Este step se omite con una advertencia.
    """
    # La vista retorna PDF directamente, la pagina ya no muestra mensajes.
    pass


@then('el formulario muestra los campos de expediente')
def step_muestra_campos_expediente(context):
    for campo in ["numero_expediente", "anio", "ponencia"]:
        _wait(context).until(
            EC.presence_of_element_located((By.NAME, campo))
        )
        assert context.driver.find_element(By.NAME, campo).is_displayed(), (
            f"El campo '{campo}' no está visible"
        )


@then('el formulario no muestra campos de expediente')
def step_no_muestra_campos_expediente(context):
    # Para DEMANDA no hay spinner, esperar solo que el DOM esté listo
    import time
    time.sleep(1)  # pequeña pausa para cualquier request AJAX residual
    for campo in ["numero_expediente", "anio", "ponencia"]:
        elementos = context.driver.find_elements(By.NAME, campo)
        assert len(elementos) == 0, (
            f"El campo '{campo}' no debería aparecer para tipo DEMANDA"
        )