"""
Vistas de la API REST para el Buzón Electrónico TJAEZ.
Implementa CU-03 y CU-04 usando Django REST Framework.
PEP8 compliant.
"""
#import buzon_electronico_tjaez.celery
from web.tasks import enviar_acuse_correo
#import json
import uuid as uuid_lib

from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from web.models import Etiqueta


class ValidarQRView(APIView):
    """
    CU-03: Consultar Validez del QR.
    GET /api/validar-qr/<uuid>/

    Valida que el QR exista, esté vigente y en estado ETIQUETA_GENERADA.
    Retorna autorización para que el hardware abra la compuerta.
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, uuid_str):
        """Valida el QR escaneado por el hardware."""
        try:
            uuid_limpio = uuid_lib.UUID(uuid_str)
        except ValueError:
            return Response(
                {"error": "Formato de QR inválido."},
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            etiqueta = Etiqueta.objects.get(uuid=uuid_limpio)
        except Etiqueta.DoesNotExist:
            return Response(
                {"error": "QR no encontrado."},
                status=status.HTTP_404_NOT_FOUND
            )

        estados_rechazados = {
            Etiqueta.ESTADO_DEPOSITADO,
            Etiqueta.ESTADO_CANCELADO,
            Etiqueta.ESTADO_NO_PRESENTADO,
        }
        if etiqueta.estado in estados_rechazados:
            return Response(
                {
                    "error": "Etiqueta no disponible.",
                    "estado_actual": etiqueta.estado,
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        if not etiqueta.esta_vigente:
            etiqueta.estado = Etiqueta.ESTADO_NO_PRESENTADO
            etiqueta.save(update_fields=["estado"])
            return Response(
                {"error": "La etiqueta ha caducado."},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            {
                "autorizado": True,
                "uuid": str(etiqueta.uuid),
                "digito_verificador": etiqueta.digito_verificador,
                "numero_sobre": etiqueta.numero_sobre,
                "estado": etiqueta.estado,
            },
            status=status.HTTP_200_OK
        )


class ConfirmarDepositoView(APIView):
    """
    CU-04: Confirmar Depósito Físico.
    POST /api/confirmar-deposito/<uuid>/

    Recibe la señal del sensor físico y cambia el estado a DEPOSITADO.
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, uuid_str):
        """Confirma el depósito físico del sobre."""
        try:
            uuid_limpio = uuid_lib.UUID(uuid_str)
        except ValueError:
            return Response(
                {"error": "Formato de UUID inválido."},
                status=status.HTTP_404_NOT_FOUND
            )

        sensor = request.data.get("sensor_confirmado", None)

        if sensor is None:
            return Response(
                {"error": "Falta el campo 'sensor_confirmado' en el payload."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not sensor:
            return Response(
                {"error": "El sensor no confirmó el depósito."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            etiqueta = Etiqueta.objects.get(uuid=uuid_limpio)
        except Etiqueta.DoesNotExist:
            return Response(
                {"error": "UUID no encontrado."},
                status=status.HTTP_404_NOT_FOUND
            )

        if etiqueta.estado == Etiqueta.ESTADO_DEPOSITADO:
            return Response(
                {"error": "Esta etiqueta ya fue depositada anteriormente."},
                status=status.HTTP_409_CONFLICT
            )

        if etiqueta.estado != Etiqueta.ESTADO_ETIQUETA_GENERADA:
            return Response(
                {
                    "error": "La etiqueta no está en un estado válido.",
                    "estado_actual": etiqueta.estado,
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        if not etiqueta.esta_vigente:
            etiqueta.estado = Etiqueta.ESTADO_NO_PRESENTADO
            etiqueta.save(update_fields=["estado"])
            return Response(
                {"error": "La etiqueta ha caducado."},
                status=status.HTTP_400_BAD_REQUEST
            )

        with transaction.atomic():
            etiqueta.estado = Etiqueta.ESTADO_DEPOSITADO
            etiqueta.fecha_deposito = timezone.now()
            etiqueta.save(update_fields=["estado", "fecha_deposito"])

        # CU-05: encolar tarea asíncrona (RNF-07)
        # El fallo del correo NO invalida el depósito
        try:
            enviar_acuse_correo.delay(etiqueta.pk)
        except Exception:
            pass

        return Response(
            {
                "depositado": True,
                "uuid": str(etiqueta.uuid),
                "digito_verificador": etiqueta.digito_verificador,
                "fecha_deposito": etiqueta.fecha_deposito.isoformat(),
                "numero_sobre": etiqueta.numero_sobre,
            },
            status=status.HTTP_200_OK
        )