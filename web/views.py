
from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.http import require_GET
from django.contrib import messages
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from datetime import time
'''
Nueva version despues del merge
'''

from .forms import FORM_MAP, BuzonDemandaForm
from .models import TipoPromocion, Etiqueta
from .services.pdf_service import generar_pdf_etiquetas


def buzon_crear(request):
    tipo = (
        request.POST.get('tipo_promocion')
        or request.GET.get('tipo_promocion', TipoPromocion.DEMANDA)
    )
    FormClass = FORM_MAP.get(tipo, BuzonDemandaForm)

    if request.method == 'POST':
        form = FormClass(request.POST)
        if form.is_valid():

            # 1. Guardar el buzón (BuzonDemanda, BuzonContestacion, etc.)
            buzon = form.save()

            # 2. Armar dict para el servicio PDF
            datos = {
                "tipo_promocion":    buzon.tipo_promocion,
                "numero_expediente": getattr(buzon, 'numero_expediente', None),
                "anio":              getattr(buzon, 'anio', None),
                "ponencia":          getattr(buzon, 'ponencia', None),
                "correo_ciudadano":  buzon.correo_electronico,
                "numero_sobres":     buzon.numero_sobres,
            }

            try:
                pdf_bytes, etiquetas_meta = generar_pdf_etiquetas(datos)
            except ValueError as e:
                # Si falla la validación del servicio, borramos el buzón recién creado
                buzon.delete()
                messages.error(request, str(e))
                return render(request, 'Realizar_registro/buzon_form.html', {
                    'form': form,
                    'tipo_actual': tipo,
                    'tipos': TipoPromocion.choices,
                })

            # 3. Persistir etiquetas ligadas al buzón via GenericForeignKey
            ct = ContentType.objects.get_for_model(buzon)
            caducidad = timezone.make_aware(
                timezone.datetime.combine(timezone.localdate(), time(23, 59, 59))
            )
            for meta in etiquetas_meta:
                Etiqueta.objects.create(
                    content_type=ct,
                    object_id=buzon.pk,
                    uuid=meta["uuid"],
                    digito_verificador=meta["digito_verificador"],
                    fecha_caducidad=caducidad,
                    numero_sobre=meta["numero_sobre"],
                )

            # 4. Devolver PDF al navegador
            response = HttpResponse(pdf_bytes, content_type='application/pdf')
            response['Content-Disposition'] = (
                f'inline; filename="etiquetas_{buzon.pk}.pdf"'
            )
            return response

    else:
        form = FormClass(initial={'tipo_promocion': tipo})

    return render(request, 'Realizar_registro/buzon_form.html', {
        'form': form,
        'tipo_actual': tipo,
        'tipos': TipoPromocion.choices,
    })


@require_GET
def buzon_form_parcial(request):
    tipo = request.GET.get('tipo', TipoPromocion.DEMANDA)
    FormClass = FORM_MAP.get(tipo, BuzonDemandaForm)
    form = FormClass()

    campos_base = {
        'tipo_promocion',
        'correo_electronico',
        'correo_electronico_confirmacion',
        'numero_sobres',
        'fecha_recibir',
    }

    campos_extra = [
        (name, form[name])
        for name in form.fields
        if name not in campos_base
    ]

    return render(request, 'Realizar_registro/campos_extra.html', {
        'campos_extra': campos_extra,
    })