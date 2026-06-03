import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'buzon_electronico_tjaez.settings')
django.setup()

from django.test.utils import setup_test_environment
from django.test.runner import DiscoverRunner
from unittest.mock import patch
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


SELENIUM_HUB  = "http://selenium:4444/wd/hub"
APP_BASE_URL  = "http://web:8000"

# PDF falso para no depender del servicio real
FAKE_PDF      = b"%PDF-1.4 fake"
FAKE_ETIQUETAS = [{"uuid": __import__('uuid').uuid4(), "digito_verificador": "ABC123", "numero_sobre": 1}]


def before_all(context):
    setup_test_environment()
    context.base_url = APP_BASE_URL

    # Arrancar Selenium
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    context.driver = webdriver.Remote(
        command_executor=SELENIUM_HUB,
        options=options,
    )
    context.driver.implicitly_wait(5)


def after_all(context):
    if hasattr(context, 'driver'):
        context.driver.quit()


def before_scenario(context, scenario):
    context.runner     = DiscoverRunner(verbosity=0)
    context.old_config = context.runner.setup_databases()

    # Mock del servicio PDF para todos los escenarios
    context.pdf_patcher = patch(
        'web.views.generar_pdf_etiquetas',
        return_value=(FAKE_PDF, FAKE_ETIQUETAS),
    )
    context.pdf_patcher.start()


def after_scenario(context, scenario):
    context.pdf_patcher.stop()
    context.runner.teardown_databases(context.old_config)
    context.driver.delete_all_cookies()