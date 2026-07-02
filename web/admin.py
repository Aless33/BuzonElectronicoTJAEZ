from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from django.utils.html import format_html

from .models import (
    BuzonDemanda, BuzonContestacion, BuzonAlegatos, BuzonInformeAutoridad,
    BuzonRecurso, BuzonIncidente, BuzonAmparo, BuzonExpedienteRAG, BuzonOtros,
    Etiqueta,
)


# ---------------------------------------------------------------------------
# Inline: muestra las etiquetas dentro de la ficha de cada Buzon
# ---------------------------------------------------------------------------
class EtiquetaInline(GenericTabularInline):
    model = Etiqueta
    extra = 0
    can_delete = False
    fields = (
        'numero_sobre', 'digito_verificador', 'estado',
        'fecha_caducidad', 'fecha_deposito', 'uuid',
    )
    readonly_fields = ('digito_verificador', 'uuid')
    ordering = ('numero_sobre',)


# ---------------------------------------------------------------------------
# Admin base para todos los tipos de Buzon
# ---------------------------------------------------------------------------
class BuzonBaseAdmin(admin.ModelAdmin):
    inlines = [EtiquetaInline]
    list_display = (
        'id', 'tipo_promocion', 'correo_electronico', 'numero_sobres',
        'estatus', 'etiquetas_resumen', 'fecha_creacion', 'fecha_recibir',
    )
    list_filter = ('estatus', 'tipo_promocion')
    search_fields = ('correo_electronico',)
    readonly_fields = ('fecha_creacion',)
    date_hierarchy = 'fecha_creacion'

    def etiquetas_resumen(self, obj):
        ct = ContentType.objects.get_for_model(obj)
        qs = Etiqueta.objects.filter(content_type=ct, object_id=obj.pk)
        total_generadas = qs.count()
        depositadas = qs.filter(estado=Etiqueta.ESTADO_DEPOSITADO).count()
        no_presentadas = qs.filter(estado=Etiqueta.ESTADO_NO_PRESENTADO).count()
        canceladas = qs.filter(estado=Etiqueta.ESTADO_CANCELADO).count()

        color = 'green' if depositadas == obj.numero_sobres else 'orange'
        detalle = f'{depositadas} depositadas'
        if no_presentadas:
            detalle += f', {no_presentadas} no presentadas'
        if canceladas:
            detalle += f', {canceladas} canceladas'

        return format_html(
            '<span style="color:{}"><b>{}</b>/{} generadas</span><br>'
            '<small style="color:#666">{}</small>',
            color, total_generadas, obj.numero_sobres, detalle,
        )
    etiquetas_resumen.short_description = 'Etiquetas (depositadas / total)'


class BuzonConExpedienteAdmin(BuzonBaseAdmin):
    list_display = BuzonBaseAdmin.list_display + ('numero_expediente', 'anio', 'ponencia')
    list_filter = BuzonBaseAdmin.list_filter + ('ponencia', 'anio')
    search_fields = BuzonBaseAdmin.search_fields + ('numero_expediente',)


# ---------------------------------------------------------------------------
# Registro de los 9 modelos concretos
# ---------------------------------------------------------------------------
@admin.register(BuzonDemanda)
class BuzonDemandaAdmin(BuzonBaseAdmin):
    pass


@admin.register(BuzonContestacion)
class BuzonContestacionAdmin(BuzonConExpedienteAdmin):
    pass


@admin.register(BuzonAlegatos)
class BuzonAlegatosAdmin(BuzonConExpedienteAdmin):
    pass


@admin.register(BuzonInformeAutoridad)
class BuzonInformeAutoridadAdmin(BuzonConExpedienteAdmin):
    pass


@admin.register(BuzonRecurso)
class BuzonRecursoAdmin(BuzonConExpedienteAdmin):
    pass


@admin.register(BuzonIncidente)
class BuzonIncidenteAdmin(BuzonConExpedienteAdmin):
    pass


@admin.register(BuzonAmparo)
class BuzonAmparoAdmin(BuzonConExpedienteAdmin):
    pass


@admin.register(BuzonExpedienteRAG)
class BuzonExpedienteRAGAdmin(BuzonConExpedienteAdmin):
    pass


@admin.register(BuzonOtros)
class BuzonOtrosAdmin(BuzonConExpedienteAdmin):
    list_display = BuzonConExpedienteAdmin.list_display + ('especifique',)


# ---------------------------------------------------------------------------
# Filtro amigable por tipo de promoción (en vez del content_type "crudo")
# ---------------------------------------------------------------------------
class TipoPromocionFilter(admin.SimpleListFilter):
    title = 'tipo de promoción'
    parameter_name = 'tipo_buzon'

    BUZON_MODELS = [
        BuzonDemanda, BuzonContestacion, BuzonAlegatos, BuzonInformeAutoridad,
        BuzonRecurso, BuzonIncidente, BuzonAmparo, BuzonExpedienteRAG, BuzonOtros,
    ]

    def lookups(self, request, model_admin):
        return [
            (model._meta.model_name, model._meta.verbose_name)
            for model in self.BUZON_MODELS
        ]

    def queryset(self, request, queryset):
        if not self.value():
            return queryset
        return queryset.filter(content_type__model=self.value())


# ---------------------------------------------------------------------------
# Admin de Etiqueta: vista central con enlace directo a su Buzon
# ---------------------------------------------------------------------------
@admin.register(Etiqueta)
class EtiquetaAdmin(admin.ModelAdmin):
    list_display = (
        'digito_verificador', 'numero_sobre', 'estado', 'tipo_buzon',
        'buzon_link', 'correo_buzon', 'fecha_caducidad', 'vigente',
    )
    list_filter = ('estado', TipoPromocionFilter)
    search_fields = ('digito_verificador', 'uuid', 'object_id')
    readonly_fields = ('uuid', 'digito_verificador')
    list_select_related = ('content_type',)

    def get_queryset(self, request):
        # Evita N+1 al resolver content_type en cada fila de la lista
        return super().get_queryset(request).select_related('content_type')

    def tipo_buzon(self, obj):
        return obj.content_type.model_class()._meta.verbose_name
    tipo_buzon.short_description = 'Tipo de Promoción'
    tipo_buzon.admin_order_field = 'content_type'

    def buzon_link(self, obj):
        buzon = obj.buzon
        if buzon is None:
            return '(promoción eliminada)'
        url = reverse(
            f'admin:{obj.content_type.app_label}_{obj.content_type.model}_change',
            args=[obj.object_id],
        )
        return format_html('<a href="{}">Ver promoción #{}</a>', url, obj.object_id)
    buzon_link.short_description = 'Promoción relacionada'

    def correo_buzon(self, obj):
        buzon = obj.buzon
        return getattr(buzon, 'correo_electronico', '-')
    correo_buzon.short_description = 'Correo'

    def vigente(self, obj):
        return obj.esta_vigente
    vigente.boolean = True
    vigente.short_description = 'Vigente'