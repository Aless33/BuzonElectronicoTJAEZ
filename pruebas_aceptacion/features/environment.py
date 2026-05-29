import os
import sys

# Esto se ejecuta AL IMPORTAR el archivo, antes que todo lo demás
RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

# Ahora sí se puede importar Django
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'buzon_electronico_tjaez.settings')
django.setup()


def before_all(context):
    pass
