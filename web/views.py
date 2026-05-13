from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_GET
from django.contrib import messages
from .forms import FORM_MAP, BuzonDemandaForm
from .models import TipoPromocion, Promocion, Etiqueta
from .services.pdf_service import generar_pdf_etiquetas
from django.utils import timezone
from datetime import time


def buzon_crear(request):
    tipo = request.POST.get('tipo_promocion') or request.GET.get('tipo_promocion', TipoPromocion.DEMANDA)
    FormClass = FORM_MAP.get(tipo, BuzonDemandaForm)

    if request.method == 'POST':
        form = FormClass(request.POST)
        if form.is_valid():
            # 1. Guardar la promoción en BD
            promocion = form.save()

            # 2. Armar el dict que espera el servicio PDF
            datos = {
                "tipo_promocion":    promocion.tipo_promocion,
                "numero_expediente": getattr(promocion, 'numero_expediente', None),
                "anio":              getattr(promocion, 'anio', None),
                "ponencia":          getattr(promocion, 'ponencia', None),
                "correo_ciudadano":  promocion.correo_electronico,
                "numero_sobres":     promocion.numero_sobres,
            }

            try:
                pdf_bytes, etiquetas_meta = generar_pdf_etiquetas(datos)
            except ValueError as e:
                messages.error(request, str(e))
                return render(request, 'Realizar_registro/buzon_form.html', {
                    'form': form,
                    'tipo_actual': tipo,
                    'tipos': TipoPromocion.choices,
                })

            # 3. Persistir las etiquetas en BD
            hoy = timezone.localdate()
            caducidad = timezone.make_aware(
                timezone.datetime.combine(hoy, time(23, 59, 59))
            )
            for meta in etiquetas_meta:
                Etiqueta.objects.create(
                    promocion=promocion,
                    uuid=meta["uuid"],
                    digito_verificador=meta["digito_verificador"],
                    fecha_caducidad=caducidad,
                    numero_sobre=meta["numero_sobre"],
                )

            # 4. Devolver el PDF directamente al navegador
            response = HttpResponse(pdf_bytes, content_type='application/pdf')
            response['Content-Disposition'] = (
                f'inline; filename="etiquetas_promocion_{promocion.pk}.pdf"'
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