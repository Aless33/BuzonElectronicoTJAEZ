"""
Vistas de la API REST para el Buzón Electrónico TJAEZ.
Implementa CU-03 y CU-04 usando Django REST Framework.
PEP8 compliant.
"""

import logging
import uuid as uuid_lib

from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from web.models import Etiqueta
from web.tasks import enviar_acuse_correo

from .serializers import (
    ConfirmarDepositoInputSerializer,
    EtiquetaDepositoSerializer,
    EtiquetaValidacionSerializer,
)

logger = logging.getLogger(__name__)

# Estados en los que una etiqueta puede ser validada/depositada.
# Única fuente de verdad para CU-03 y CU-04 (lista blanca).
ESTADOS_OPERABLES = {Etiqueta.ESTADO_ETIQUETA_GENERADA}


def _parsear_uuid(uuid_str, mensaje_error):
    """
    Intenta convertir uuid_str a UUID.
    Retorna (uuid, None) si es válido, o (None, Response) si no lo es.
    """
    try:
        return uuid_lib.UUID(uuid_str), None
    except ValueError:
        return None, Response(
            {"error": mensaje_error},
            status=status.HTTP_404_NOT_FOUND,
        )


def _verificar_vigencia(etiqueta):
    """
    Verifica que la etiqueta siga vigente. Si ya no lo está, la marca
    como NO_PRESENTADO y persiste el cambio.
    Retorna None si sigue vigente, o Response con el error correspondiente.
    """
    if etiqueta.esta_vigente:
        return None

    etiqueta.estado = Etiqueta.ESTADO_NO_PRESENTADO
    etiqueta.save(update_fields=["estado"])
    return Response(
        {"error": "La etiqueta ha caducado."},
        status=status.HTTP_400_BAD_REQUEST,
    )


def _validar_estado_operable(etiqueta):
    """
    Valida que la etiqueta esté en un estado operable (lista blanca,
    compartida entre CU-03 y CU-04). Retorna None si es válida, o
    Response con el error correspondiente.
    """
    if etiqueta.estado == Etiqueta.ESTADO_DEPOSITADO:
        return Response(
            {"error": "Esta etiqueta ya fue depositada anteriormente."},
            status=status.HTTP_409_CONFLICT,
        )

    if etiqueta.estado not in ESTADOS_OPERABLES:
        return Response(
            {
                "error": "La etiqueta no está en un estado válido.",
                "estado_actual": etiqueta.estado,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    return None


class ValidarQRView(APIView):
    """
    CU-03: Consultar Validez del QR.
    GET /api/validar-qr/<uuid>/

    Valida que el QR exista, esté vigente y en estado operable.
    Retorna autorización para que el hardware abra la compuerta.
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, uuid_str):
        """Valida el QR escaneado por el hardware."""
        uuid_limpio, error = _parsear_uuid(uuid_str, "Formato de QR inválido.")
        if error:
            return error

        try:
            etiqueta = Etiqueta.objects.get(uuid=uuid_limpio)
        except Etiqueta.DoesNotExist:
            return Response(
                {"error": "QR no encontrado."},
                status=status.HTTP_404_NOT_FOUND,
            )

        error = _validar_estado_operable(etiqueta)
        if error:
            return error

        error = _verificar_vigencia(etiqueta)
        if error:
            return error

        logger.info(
            "[CU-03] QR validado correctamente. uuid=%s pk=%s",
            etiqueta.uuid,
            etiqueta.pk,
        )

        serializer = EtiquetaValidacionSerializer(etiqueta)
        return Response(serializer.data, status=status.HTTP_200_OK)


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
        uuid_limpio, error = _parsear_uuid(
            uuid_str, "Formato de UUID inválido."
        )
        if error:
            return error

        input_serializer = ConfirmarDepositoInputSerializer(
            data=request.data
        )
        if not input_serializer.is_valid():
            primer_error = next(iter(input_serializer.errors.values()))[0]
            return Response(
                {"error": str(primer_error)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            try:
                etiqueta = Etiqueta.objects.select_for_update().get(
                    uuid=uuid_limpio
                )
            except Etiqueta.DoesNotExist:
                return Response(
                    {"error": "UUID no encontrado."},
                    status=status.HTTP_404_NOT_FOUND,
                )

            error = _validar_estado_operable(etiqueta)
            if error:
                return error

            error = _verificar_vigencia(etiqueta)
            if error:
                return error

            etiqueta.estado = Etiqueta.ESTADO_DEPOSITADO
            etiqueta.fecha_deposito = timezone.now()
            etiqueta.save(update_fields=["estado", "fecha_deposito"])

        logger.info(
            "[CU-04] Depósito confirmado. uuid=%s pk=%s fecha=%s",
            etiqueta.uuid,
            etiqueta.pk,
            etiqueta.fecha_deposito,
        )

        # CU-05: encolar tarea asíncrona (RNF-07)
        # El fallo del correo NO invalida el depósito
        try:
            enviar_acuse_correo.delay(etiqueta.pk)
            logger.info(
                "[CU-05] Tarea de correo encolada para etiqueta pk=%s",
                etiqueta.pk,
            )
        except Exception as e:
            logger.error(
                "[CU-05] Error al encolar correo para etiqueta pk=%s: %s",
                etiqueta.pk,
                e,
                exc_info=True,
            )

        serializer = EtiquetaDepositoSerializer(etiqueta)
        return Response(serializer.data, status=status.HTTP_200_OK)
