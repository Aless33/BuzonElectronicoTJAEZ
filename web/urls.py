from django.urls import path
from . import views

urlpatterns = [
    path('',              views.buzon_crear,        name='buzon_crear'),
    path('form-parcial/', views.buzon_form_parcial, name='buzon_form_parcial'),
]