"""
Tareas asíncronas de Celery para el Buzón Electrónico TJAEZ.
Implementa CU-05: Enviar notificación por correo.
PEP8 compliant.
"""
from celery import shared_task
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=300,
    queue='celery',
)
def enviar_acuse_correo(self, etiqueta_id):
    """
    CU-05: Envía el acuse provisional por correo al ciudadano.
    """
    from .models import Etiqueta

    try:
        etiqueta = Etiqueta.objects.select_related().get(pk=etiqueta_id)
    except Etiqueta.DoesNotExist:
        return {'status': 'error', 'mensaje': 'Etiqueta no encontrada.'}

    buzon = etiqueta.buzon
    correo_destino = buzon.correo_electronico

    contexto = {
        'tipo_promocion': buzon.get_tipo_promocion_display(),
        'numero_expediente': getattr(buzon, 'numero_expediente', None),
        'anio': getattr(buzon, 'anio', None),
        'ponencia': getattr(buzon, 'ponencia', None),
        'digito_verificador': etiqueta.digito_verificador,
        'fecha_deposito': etiqueta.fecha_deposito,
        'numero_sobre': etiqueta.numero_sobre,
        'uuid': str(etiqueta.uuid),
    }

    asunto = 'Confirmación de Recepción - Buzón Electrónico TJAEZ'
    html_mensaje = render_to_string('correos/acuse_deposito.html', contexto)
    texto_plano = strip_tags(html_mensaje)

    try:
        send_mail(
            subject=asunto,
            message=texto_plano,
            from_email=None,
            recipient_list=[correo_destino],
            html_message=html_mensaje,
            fail_silently=False,
        )
        return {'status': 'ok', 'correo': correo_destino}

    except Exception as exc:
        raise self.retry(exc=exc)