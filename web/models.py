from django.db import models
from django.utils import timezone
from datetime import datetime, time, timedelta


def default_fecha_recibir():
    hoy = timezone.localdate()
    medianoche = datetime.combine(hoy + timedelta(days=1), time(0, 0, 0))
    return timezone.make_aware(medianoche)


'''
opciones
'''

class TipoPromocion(models.TextChoices):
    DEMANDA                = 'DEMANDA',               'Demanda'
    CONTESTACION           = 'CONTESTACION',           'Contestación'
    ALEGATOS               = 'ALEGATOS',               'Alegatos'
    INFORME_AUTORIDAD      = 'INFORME_AUTORIDAD',      'Informe de Autoridad'
    RECURSO                = 'RECURSO',                'Recurso'
    INCIDENTE              = 'INCIDENTE',              'Incidente'
    AMPARO                 = 'AMPARO',                 'Amparo'
    EXPEDIENTE_RAG_INICIAL = 'EXPEDIENTE_RAG_INICIAL', 'Expediente de Resp. Admvas (RAG) Inicial'
    EXPEDIENTE_RAG         = 'EXPEDIENTE_RAG',         'Expediente de Resp. Admvas (RAG)'
    OTROS                  = 'OTROS',                  'Otros'


class EstatusPromocion(models.TextChoices):
    ACTIVO    = 'ACTIVO',    'Activo'
    RETRASADO = 'RETRASADO', 'Retrasado'


class Ponencia(models.TextChoices):
    PONENCIA_1 = 'PONENCIA_1', 'Ponencia 1'
    PONENCIA_2 = 'PONENCIA_2', 'Ponencia 2'
    PONENCIA_3 = 'PONENCIA_3', 'Ponencia 3'


'''
Modelo abstracto base
'''
class BuzonBase(models.Model):
    tipo_promocion = models.CharField(
        max_length=30,
        choices=TipoPromocion.choices,
        verbose_name='Tipo de Promoción'
    )
    correo_electronico = models.EmailField(
        verbose_name='Correo Electrónico para acuse provisional'
    )
    numero_sobres = models.PositiveIntegerField(
        verbose_name='Número de Sobres'
    )
    estatus = models.CharField(
        max_length=20,
        choices=EstatusPromocion.choices,
        default=EstatusPromocion.ACTIVO,
        verbose_name='Estatus'
    )
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha y Hora de Creación'
    )
    fecha_recibir = models.DateTimeField(
        default=default_fecha_recibir,
        verbose_name='Fecha para Recibir'
    )

    class Meta:
        abstract = True
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"#{self.pk} - {self.get_tipo_promocion_display()} ({self.correo_electronico})"


'''
Mixin con campos extra compartidos
'''
class ExpedienteMixin(models.Model):
    """
    Campos extra compartidos por: Contestación, Alegatos, Informe de Autoridad,
    Recurso, Incidente, Amparo y Expediente RAG.
    """
    numero_expediente = models.CharField(
        max_length=100,
        verbose_name='Número de Expediente'
    )
    anio = models.PositiveIntegerField(
        verbose_name='Año'
    )
    ponencia = models.CharField(
        max_length=20,
        choices=Ponencia.choices,
        verbose_name='Ponencia'
    )

    class Meta:
        abstract = True


'''
Modelos concretos
'''
class BuzonDemanda(BuzonBase):
    """Solo campos base."""

    class Meta:
        verbose_name        = 'Buzón - Demanda'
        verbose_name_plural = 'Buzones - Demanda'


class BuzonConExpedinteBase(ExpedienteMixin, BuzonBase):
    """
    Base intermedia (abstracta) para los tipos que comparten
    exactamente los mismos campos extra sin agregar nada más.
    """

    class Meta:
        abstract = True


class BuzonContestacion(BuzonConExpedinteBase):
    class Meta:
        verbose_name        = 'Buzón - Contestación'
        verbose_name_plural = 'Buzones - Contestación'


class BuzonAlegatos(BuzonConExpedinteBase):
    class Meta:
        verbose_name        = 'Buzón - Alegatos'
        verbose_name_plural = 'Buzones - Alegatos'


class BuzonInformeAutoridad(BuzonConExpedinteBase):
    class Meta:
        verbose_name        = 'Buzón - Informe de Autoridad'
        verbose_name_plural = 'Buzones - Informe de Autoridad'


class BuzonRecurso(BuzonConExpedinteBase):
    class Meta:
        verbose_name        = 'Buzón - Recurso'
        verbose_name_plural = 'Buzones - Recurso'


class BuzonIncidente(BuzonConExpedinteBase):
    class Meta:
        verbose_name        = 'Buzón - Incidente'
        verbose_name_plural = 'Buzones - Incidente'


class BuzonAmparo(BuzonConExpedinteBase):
    class Meta:
        verbose_name        = 'Buzón - Amparo'
        verbose_name_plural = 'Buzones - Amparo'


class BuzonExpedienteRAG(BuzonConExpedinteBase):
    class Meta:
        verbose_name        = 'Buzón - Expediente RAG'
        verbose_name_plural = 'Buzones - Expediente RAG'


class BuzonOtros(ExpedienteMixin, BuzonBase):
    """
    Campos base + expediente + campo 'especifique'.
    """
    especifique = models.CharField(
        max_length=255,
        verbose_name='Especifique'
    )

    class Meta:
        verbose_name        = 'Buzón - Otros'
        verbose_name_plural = 'Buzones - Otros'