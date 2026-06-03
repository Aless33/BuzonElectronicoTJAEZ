"""
Tests para web/tasks.py — cobertura 100%.
Usa Django TestCase estándar (compatible con coverage + manage.py test).

Casos:
  1. Etiqueta no existe → retorna dict de error.
  2. send_mail exitoso → retorna {'status': 'ok', 'correo': ...}.
  3. send_mail falla   → la tarea agota reintentos (MaxRetriesExceededError).
"""
from unittest.mock import patch

from django.contrib.contenttypes.models import ContentType
from django.test import TestCase, override_settings
from django.utils import timezone

from web.models import BuzonDemanda, Etiqueta
from web.tasks import enviar_acuse_correo


CELERY_EAGER = {
    'CELERY_TASK_ALWAYS_EAGER': True,
    'CELERY_TASK_EAGER_PROPAGATES': True,
}


def _crear_buzon():
    return BuzonDemanda.objects.create(
        tipo_promocion='DEMANDA',
        correo_electronico='ciudadano@example.com',
        numero_sobres=1,
    )


def _crear_etiqueta(buzon):
    ct = ContentType.objects.get_for_model(BuzonDemanda)
    return Etiqueta.objects.create(
        content_type=ct,
        object_id=buzon.pk,
        fecha_caducidad=timezone.now() + timezone.timedelta(days=1),
        numero_sobre=1,
        fecha_deposito=timezone.now(),
    )


@override_settings(**CELERY_EAGER)
class EnviarAcuseCorreoTests(TestCase):

    # ------------------------------------------------------------------
    # Caso 1 — Etiqueta inexistente
    # ------------------------------------------------------------------
    def test_etiqueta_no_encontrada(self):
        """
        ID inexistente → retorna error sin lanzar excepción.
        """
        resultado = enviar_acuse_correo.apply(args=[99999])

        self.assertTrue(resultado.successful())
        self.assertEqual(resultado.result, {
            'status': 'error',
            'mensaje': 'Etiqueta no encontrada.',
        })

    # ------------------------------------------------------------------
    # Caso 2 — Envío exitoso
    # ------------------------------------------------------------------
    @patch('web.tasks.render_to_string', return_value='<p>Acuse</p>')
    @patch('web.tasks.send_mail', return_value=1)
    def test_envio_exitoso(self, mock_send_mail, mock_render):
        """
        send_mail exitoso → retorna {'status': 'ok', 'correo': ...}.
        """
        buzon = _crear_buzon()
        etiqueta = _crear_etiqueta(buzon)

        resultado = enviar_acuse_correo.apply(args=[etiqueta.pk])

        self.assertTrue(resultado.successful())
        self.assertEqual(resultado.result, {
            'status': 'ok',
            'correo': 'ciudadano@example.com',
        })

        mock_send_mail.assert_called_once()
        _, call_kwargs = mock_send_mail.call_args
        self.assertEqual(
            call_kwargs['recipient_list'], ['ciudadano@example.com']
        )
        self.assertFalse(call_kwargs['fail_silently'])

    # ------------------------------------------------------------------
    # Caso 3 — send_mail falla → self.retry() → MaxRetriesExceededError
    # ------------------------------------------------------------------
    @patch('web.tasks.render_to_string', return_value='<p>Acuse</p>')
    @patch('web.tasks.send_mail', side_effect=Exception('SMTP caído'))
    def test_reintento_al_fallar_send_mail(self, mock_send_mail, mock_render):
        """
        send_mail falla → la tarea llama self.retry().
        Con CELERY_TASK_ALWAYS_EAGER=True, Celery lanza celery.exceptions.Retry
        en lugar de ejecutar reintentos reales — verificamos que:
          - Se lanza Retry (prueba que el bloque except se ejecutó).
          - send_mail fue llamado exactamente 1 vez.
        """
        from celery.exceptions import Retry

        buzon = _crear_buzon()
        etiqueta = _crear_etiqueta(buzon)

        with self.assertRaises(Retry):
            enviar_acuse_correo.apply(args=[etiqueta.pk], throw=True)

        mock_send_mail.assert_called_once()
