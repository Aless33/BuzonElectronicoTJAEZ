# admin.py
from django.contrib import admin
from .models import (
    BuzonDemanda,
    BuzonContestacion,
    BuzonAlegatos,
    BuzonInformeAutoridad,
    BuzonRecurso,
    BuzonIncidente,
    BuzonAmparo,
    BuzonExpedienteRAG,
    BuzonOtros,
)

admin.site.register(BuzonDemanda)
admin.site.register(BuzonContestacion)
admin.site.register(BuzonAlegatos)
admin.site.register(BuzonInformeAutoridad)
admin.site.register(BuzonRecurso)
admin.site.register(BuzonIncidente)
admin.site.register(BuzonAmparo)
admin.site.register(BuzonExpedienteRAG)
admin.site.register(BuzonOtros)