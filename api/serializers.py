"""
Serializers de la API REST para el Buzón Electrónico TJAEZ.
PEP8 compliant.
"""

from rest_framework import serializers

from web.models import Etiqueta


class ConfirmarDepositoInputSerializer(serializers.Serializer):
    """
    Valida el payload recibido del sensor físico en
    ConfirmarDepositoView (CU-04).
    """
    sensor_confirmado = serializers.BooleanField(
        required=True,
        allow_null=False,
        error_messages={
            'required': "Falta el campo 'sensor_confirmado' en el payload.",
            'null': "Falta el campo 'sensor_confirmado' en el payload.",
            'invalid': "El campo 'sensor_confirmado' debe ser booleano.",
        },
    )

    def validate_sensor_confirmado(self, value):
        if not value:
            raise serializers.ValidationError(
                "El sensor no confirmó el depósito."
            )
        return value


class EtiquetaValidacionSerializer(serializers.ModelSerializer):
    """
    Respuesta de éxito para ValidarQRView (CU-03).
    """
    autorizado = serializers.SerializerMethodField()

    class Meta:
        model = Etiqueta
        fields = [
            'autorizado',
            'uuid',
            'digito_verificador',
            'numero_sobre',
            'estado',
        ]

    def get_autorizado(self, obj):
        return True


class EtiquetaDepositoSerializer(serializers.ModelSerializer):
    """
    Respuesta de éxito para ConfirmarDepositoView (CU-04).
    """
    depositado = serializers.SerializerMethodField()

    class Meta:
        model = Etiqueta
        fields = [
            'depositado',
            'uuid',
            'digito_verificador',
            'fecha_deposito',
            'numero_sobre',
        ]

    def get_depositado(self, obj):
        return True