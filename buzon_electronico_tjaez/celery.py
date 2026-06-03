"""
Configuración de Celery para el proyecto Buzón Electrónico TJAEZ.
PEP8 compliant.
"""
import os

from celery import Celery

os.environ.setdefault(
    'DJANGO_SETTINGS_MODULE',
    'buzon_electronico_tjaez.settings'
)

app = Celery('buzon_electronico_tjaez')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Forzar Redis como broker explícitamente
app.conf.broker_url = 'redis://redis:6379/0'
app.conf.result_backend = 'redis://redis:6379/0'
