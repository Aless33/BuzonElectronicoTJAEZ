"""
Modelos del Buzón Electrónico TJAEZ.

Define Promocion (registro padre) y Etiqueta (registro hijo por sobre),
siguiendo las reglas de negocio del SRS: UUID v4 único por sobre,
caducidad a las 23:59 hrs del día de emisión y estados controlados.
"""

import uuid
import random
import string
from django.db import models
from django.utils import timezone


def _generar_digito_verificador():
    """Genera un código alfanumérico corto de 6 caracteres (RF-02)."""
    caracteres = string.ascii_uppercase + string.digits
    return "".join(random.choices(caracteres, k=6))


class Promocion(models.Model):
    """
    Registro padre que agrupa los datos capturados en el formulario web.
    Corresponde al pre-registro del ciudadano (CU-01).
    """

    TIPO_CHOICES = [
        ("DEMANDA", "Demanda"),
        ("RAG_INICIAL", "Expediente RAG Inicial"),
        ("CONTESTACION", "Contestación"),
        ("ALEGATOS", "Alegatos"),
        ("AMPARO", "Amparo"),
        ("OTRO", "Otro"),
    ]

    tipo_promocion = models.CharField(max_length=50, choices=TIPO_CHOICES)
    # Campos opcionales: solo aplican si NO es trámite inicial (RF-01)
    numero_expediente = models.CharField(max_length=20, blank=True, null=True)
    anio = models.PositiveIntegerField(blank=True, null=True)
    ponencia = models.CharField(max_length=100, blank=True, null=True)
    correo_ciudadano = models.EmailField()
    numero_sobres = models.PositiveIntegerField(default=1)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Promoción"
        verbose_name_plural = "Promociones"

    def __str__(self):
        return (
            f"Promoción {self.id} - {self.tipo_promocion} "
            f"({self.fecha_creacion.strftime('%Y-%m-%d')})"
        )

    @property
    def es_tramite_inicial(self):
        """Retorna True si el tipo es de inicio (no requiere expediente)."""
        return self.tipo_promocion in ("DEMANDA", "RAG_INICIAL")


class Etiqueta(models.Model):
    """
    Registro hijo: una Etiqueta por sobre físico declarado.
    Contiene el UUID que se convierte en código QR (RF-02, RF-03, RF-04).
    """

    ESTADO_ETIQUETA_GENERADA = "ETIQUETA_GENERADA"
    ESTADO_DEPOSITADO = "DEPOSITADO"
    ESTADO_NO_PRESENTADO = "NO_PRESENTADO"
    ESTADO_CANCELADO = "CANCELADO"

    ESTADO_CHOICES = [
        (ESTADO_ETIQUETA_GENERADA, "Etiqueta Generada"),
        (ESTADO_DEPOSITADO, "Depositado"),
        (ESTADO_NO_PRESENTADO, "No Presentado"),
        (ESTADO_CANCELADO, "Cancelado"),
    ]

    promocion = models.ForeignKey(
        Promocion, on_delete=models.CASCADE, related_name="etiquetas"
    )
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    digito_verificador = models.CharField(
        max_length=6, default=_generar_digito_verificador
    )
    estado = models.CharField(
        max_length=20, choices=ESTADO_CHOICES, default=ESTADO_ETIQUETA_GENERADA
    )
    # Caducidad: 23:59 hrs del día de emisión (Regla de Negocio 1)
    fecha_caducidad = models.DateTimeField()
    numero_sobre = models.PositiveIntegerField()  # Ej: 1, 2, 3 (de N totales)
    fecha_deposito = models.DateTimeField(blank=True, null=True)

    class Meta:
        verbose_name = "Etiqueta"
        verbose_name_plural = "Etiquetas"
        ordering = ["numero_sobre"]

    def __str__(self):
        return (
            f"Etiqueta {self.digito_verificador} - "
            f"Sobre {self.numero_sobre}/{self.promocion.numero_sobres} "
            f"[{self.estado}]"
        )

    @property
    def esta_vigente(self):
        """Verifica que la etiqueta no haya caducado (RF-05)."""
        return timezone.now() <= self.fecha_caducidad

    @property
    def uuid_str(self):
        """Retorna el UUID como cadena sin guiones para el QR."""
        return str(self.uuid)
