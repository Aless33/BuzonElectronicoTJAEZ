from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from . import views

urlpatterns = [
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path(
        'validar-qr/<str:uuid_str>/',
        views.ValidarQRView.as_view(),
        name='validar_qr'
    ),
    path(
        'confirmar-deposito/<str:uuid_str>/',
        views.ConfirmarDepositoView.as_view(),
        name='confirmar_deposito'
    ),
]