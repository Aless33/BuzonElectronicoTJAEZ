"""
Configuración del entorno Behave para las pruebas de aceptación de la API.
PEP8 compliant.
"""
import os
import django
from django.test.utils import setup_test_environment
from django.test.runner import DiscoverRunner

os.environ.setdefault(
    'DJANGO_SETTINGS_MODULE',
    'buzon_electronico_tjaez.settings'
)


def before_all(context):
    django.setup()
    setup_test_environment()


def before_scenario(context, scenario):
    context.runner = DiscoverRunner(verbosity=0)
    context.old_config = context.runner.setup_databases()


def after_scenario(context, scenario):
    context.runner.teardown_databases(context.old_config)