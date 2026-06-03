import django
from django.test.runner import DiscoverRunner
from django.test.utils import setup_test_environment
from django.test.utils import teardown_test_environment
import os

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "buzon_electronico_tjaez.settings",
)


def before_all(context):
    django.setup()

    try:
        setup_test_environment()
    except RuntimeError:
        pass


def before_scenario(context, scenario):
    context.runner = DiscoverRunner(verbosity=0)
    context.old_config = context.runner.setup_databases()


def after_scenario(context, scenario):
    context.runner.teardown_databases(context.old_config)


def after_all(context):
    teardown_test_environment()
