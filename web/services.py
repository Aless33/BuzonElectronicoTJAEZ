import uuid
from datetime import datetime, time
from django.utils import timezone

def generar_etiquetas_lote(num_sobres):
    """
    Genera un lote de etiquetas con UUID v4 y caducidad a las 23:59.
    """
    if not num_sobres or num_sobres <= 0:
        raise ValueError("La cantidad de sobres es requerida y debe ser mayor a 0")
    
    etiquetas = []
    
    # Obtiene la fecha actual considerando la zona horaria del sistema
    hoy = timezone.localdate()
    hora_limite = time(23, 59)
    caducidad = timezone.make_aware(datetime.combine(hoy, hora_limite))

    for _ in range(num_sobres):
        etiquetas.append({
            'uuid': str(uuid.uuid4()),
            'caducidad': caducidad
        })
        
    return etiquetas