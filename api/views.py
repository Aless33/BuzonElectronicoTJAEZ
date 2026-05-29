import uuid as uuid_lib
import json
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db import transaction

from web.models import Etiqueta


@require_GET
def validar_qr(request, uuid_str):
    """
    CU-03: Consultar Validez del QR
    GET /api/validar-qr/<uuid>/
    """
    try:
        uuid_limpio = uuid_lib.UUID(uuid_str)
    except ValueError:
        return JsonResponse({"error": "Formato de QR inválido."}, status=404)

    try:
        etiqueta = Etiqueta.objects.get(uuid=uuid_limpio)
    except Etiqueta.DoesNotExist:
        return JsonResponse({"error": "QR no encontrado."}, status=404)

    estados_rechazados = {
        Etiqueta.ESTADO_DEPOSITADO,
        Etiqueta.ESTADO_CANCELADO,
        Etiqueta.ESTADO_NO_PRESENTADO,
    }
    if etiqueta.estado in estados_rechazados:
        return JsonResponse(
            {"error": "Etiqueta no disponible.", "estado_actual": etiqueta.estado},
            status=400
        )

    if not etiqueta.esta_vigente:
        etiqueta.estado = Etiqueta.ESTADO_NO_PRESENTADO
        etiqueta.save(update_fields=["estado"])
        return JsonResponse({"error": "La etiqueta ha caducado."}, status=400)

    return JsonResponse(
        {
            "autorizado": True,
            "uuid": str(etiqueta.uuid),
            "digito_verificador": etiqueta.digito_verificador,
            "numero_sobre": etiqueta.numero_sobre,
            "estado": etiqueta.estado,
        },
        status=200
    )


@csrf_exempt
@require_POST
def confirmar_deposito(request, uuid_str):
    """
    CU-04: Confirmar Depósito Físico
    POST /api/confirmar-deposito/<uuid>/
    """
    try:
        uuid_limpio = uuid_lib.UUID(uuid_str)
    except ValueError:
        return JsonResponse({"error": "Formato de UUID inválido."}, status=404)

    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "El cuerpo de la petición no es JSON válido."}, status=400)

    if "sensor_confirmado" not in body:
        return JsonResponse({"error": "Falta el campo 'sensor_confirmado' en el payload."}, status=400)

    if not body["sensor_confirmado"]:
        return JsonResponse({"error": "El sensor no confirmó el depósito."}, status=400)

    try:
        etiqueta = Etiqueta.objects.get(uuid=uuid_limpio)
    except Etiqueta.DoesNotExist:
        return JsonResponse({"error": "UUID no encontrado."}, status=404)

    if etiqueta.estado == Etiqueta.ESTADO_DEPOSITADO:
        return JsonResponse({"error": "Esta etiqueta ya fue depositada anteriormente."}, status=409)

    if etiqueta.estado != Etiqueta.ESTADO_ETIQUETA_GENERADA:
        return JsonResponse(
            {"error": "La etiqueta no está en un estado válido para depositar.", "estado_actual": etiqueta.estado},
            status=400
        )

    if not etiqueta.esta_vigente:
        etiqueta.estado = Etiqueta.ESTADO_NO_PRESENTADO
        etiqueta.save(update_fields=["estado"])
        return JsonResponse({"error": "La etiqueta ha caducado."}, status=400)

    with transaction.atomic():
        etiqueta.estado = Etiqueta.ESTADO_DEPOSITADO
        etiqueta.fecha_deposito = timezone.now()
        etiqueta.save(update_fields=["estado", "fecha_deposito"])

    return JsonResponse(
        {
            "depositado": True,
            "uuid": str(etiqueta.uuid),
            "digito_verificador": etiqueta.digito_verificador,
            "fecha_deposito": etiqueta.fecha_deposito.isoformat(),
            "numero_sobre": etiqueta.numero_sobre,
        },
        status=200
    )