from django.urls import path
from . import views

urlpatterns = [
    path('validar-qr/<str:uuid_str>/',       views.validar_qr,          name='validar_qr'),
    path('confirmar-deposito/<str:uuid_str>/', views.confirmar_deposito, name='confirmar_deposito'),
]