from django import forms
from django.utils import timezone

from .models import (
    BuzonDemanda, BuzonContestacion, BuzonAlegatos, BuzonInformeAutoridad,
    BuzonRecurso, BuzonIncidente, BuzonAmparo, BuzonExpedienteRAG, BuzonOtros,
    TipoPromocion, Ponencia, EstatusPromocion
)


'''
Campos comunes
'''
CAMPOS_BASE = ['tipo_promocion', 'correo_electronico', 'numero_sobres']
CAMPOS_EXPEDIENTE = ['numero_expediente', 'anio', 'ponencia']


class BaseWidgets:
    """Widgets y labels compartidos entre formularios"""
    base_widgets = {
        'tipo_promocion': forms.Select(attrs={'class': 'form-select', 'id': 'id_tipo_promocion'}),
        'correo_electronico': forms.EmailInput(attrs={'class': 'form-control'}),
        'numero_sobres': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
    }
    expediente_widgets = {
        'numero_expediente': forms.TextInput(attrs={'class': 'form-control'}),
        'anio': forms.NumberInput(attrs={'class': 'form-control', 'min': 2000, 'max': 2100}),
        'ponencia': forms.Select(attrs={'class': 'form-select'}),
    }

'''
Mixin para confirmar correo electrónico
'''
class CorreoConfirmacionMixin:
    """Valida que ambos correos coincidan."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Se agrega el campo dinamicamente
        self.fields['correo_electronico_confirmacion'] = forms.EmailField(
            label='Confirmar Correo Electrónico',
            widget=forms.EmailInput(attrs={'class': 'form-input'}),
        )
        fields_order = list(self.fields)
        fields_order.remove('correo_electronico_confirmacion')
        idx = fields_order.index('correo_electronico') + 1
        fields_order.insert(idx, 'correo_electronico_confirmacion')
        self.fields = {k: self.fields[k] for k in fields_order}

    def clean(self):
        cleaned_data = super().clean()
        correo       = cleaned_data.get('correo_electronico')
        confirmacion = cleaned_data.get('correo_electronico_confirmacion')

        if correo and confirmacion and correo != confirmacion:
            self.add_error(
                'correo_electronico_confirmacion',
                'Los correos electrónicos no coinciden.'
            )
        return cleaned_data

'''
Formularios por tipo
'''

class BuzonDemandaForm(CorreoConfirmacionMixin, BaseWidgets, forms.ModelForm):
    class Meta:
        model = BuzonDemanda
        fields = CAMPOS_BASE
        widgets = BaseWidgets.base_widgets


class BuzonContestacionForm(CorreoConfirmacionMixin, BaseWidgets, forms.ModelForm):
    class Meta:
        model = BuzonContestacion
        fields = CAMPOS_BASE + CAMPOS_EXPEDIENTE
        widgets = {**BaseWidgets.base_widgets, **BaseWidgets.expediente_widgets}


class BuzonAlegatosForm(CorreoConfirmacionMixin, BaseWidgets, forms.ModelForm):
    class Meta:
        model = BuzonAlegatos
        fields = CAMPOS_BASE + CAMPOS_EXPEDIENTE
        widgets = {**BaseWidgets.base_widgets, **BaseWidgets.expediente_widgets}


class BuzonInformeAutoridadForm(CorreoConfirmacionMixin, BaseWidgets, forms.ModelForm):
    class Meta:
        model = BuzonInformeAutoridad
        fields = CAMPOS_BASE + CAMPOS_EXPEDIENTE
        widgets = {**BaseWidgets.base_widgets, **BaseWidgets.expediente_widgets}


class BuzonRecursoForm(CorreoConfirmacionMixin, BaseWidgets, forms.ModelForm):
    class Meta:
        model = BuzonRecurso
        fields = CAMPOS_BASE + CAMPOS_EXPEDIENTE
        widgets = {**BaseWidgets.base_widgets, **BaseWidgets.expediente_widgets}


class BuzonIncidenteForm(CorreoConfirmacionMixin, BaseWidgets, forms.ModelForm):
    class Meta:
        model = BuzonIncidente
        fields = CAMPOS_BASE + CAMPOS_EXPEDIENTE
        widgets = {**BaseWidgets.base_widgets, **BaseWidgets.expediente_widgets}


class BuzonAmparoForm(CorreoConfirmacionMixin, BaseWidgets, forms.ModelForm):
    class Meta:
        model = BuzonAmparo
        fields = CAMPOS_BASE + CAMPOS_EXPEDIENTE
        widgets = {**BaseWidgets.base_widgets, **BaseWidgets.expediente_widgets}


class BuzonExpedienteRAGForm(CorreoConfirmacionMixin, BaseWidgets, forms.ModelForm):
    class Meta:
        model = BuzonExpedienteRAG
        fields = CAMPOS_BASE + CAMPOS_EXPEDIENTE
        widgets = {**BaseWidgets.base_widgets, **BaseWidgets.expediente_widgets}


class BuzonOtrosForm(CorreoConfirmacionMixin, BaseWidgets, forms.ModelForm):
    class Meta:
        model = BuzonOtros
        fields = CAMPOS_BASE + CAMPOS_EXPEDIENTE + ['especifique']
        widgets = {
            **BaseWidgets.base_widgets,
            **BaseWidgets.expediente_widgets,
            'especifique': forms.TextInput(attrs={'class': 'form-control'}),
        }


'''
Mapa tipo → formulario
'''

FORM_MAP = {
    TipoPromocion.DEMANDA:                BuzonDemandaForm,
    TipoPromocion.CONTESTACION:           BuzonContestacionForm,
    TipoPromocion.ALEGATOS:               BuzonAlegatosForm,
    TipoPromocion.INFORME_AUTORIDAD:      BuzonInformeAutoridadForm,
    TipoPromocion.RECURSO:                BuzonRecursoForm,
    TipoPromocion.INCIDENTE:              BuzonIncidenteForm,
    TipoPromocion.AMPARO:                 BuzonAmparoForm,
    TipoPromocion.EXPEDIENTE_RAG_INICIAL: BuzonDemandaForm,   # solo base
    TipoPromocion.EXPEDIENTE_RAG:         BuzonExpedienteRAGForm,
    TipoPromocion.OTROS:                  BuzonOtrosForm,
}