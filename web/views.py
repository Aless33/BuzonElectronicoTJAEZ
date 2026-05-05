from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.contrib import messages
from .forms import FORM_MAP, BuzonDemandaForm
from .models import TipoPromocion


def buzon_crear(request):
    """
    Vista principal,
    GET muestra el form inicial, 
    POST guarda el registro.

    """
    tipo = request.POST.get('tipo_promocion') or request.GET.get('tipo_promocion', TipoPromocion.DEMANDA)
    FormClass = FORM_MAP.get(tipo, BuzonDemandaForm)

    if request.method == 'POST':
        form = FormClass(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Buzón registrado correctamente.')

            #Aqui redirige al PDF con las etiquetas generadas PUSSYS 
            return redirect('buzon_crear')
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