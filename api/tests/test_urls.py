from uuid import uuid4

from django.test import SimpleTestCase
from django.urls import resolve, reverse
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from api import views


class ApiURLTestCase(SimpleTestCase):
    """
    Pruebas unitarias de URLs de la API bajo enfoque TDD.
    """

    def test_reverse_token_obtain_pair(self):
        url = reverse("token_obtain_pair")

        self.assertEqual(url, "/api/token/")

    def test_reverse_token_refresh(self):
        url = reverse("token_refresh")

        self.assertEqual(url, "/api/token/refresh/")

    def test_reverse_validar_qr(self):
        uuid_str = str(uuid4())

        url = reverse("validar_qr", kwargs={"uuid_str": uuid_str})

        self.assertEqual(url, f"/api/validar-qr/{uuid_str}/")

    def test_reverse_confirmar_deposito(self):
        uuid_str = str(uuid4())

        url = reverse(
            "confirmar_deposito",
            kwargs={"uuid_str": uuid_str},
        )

        self.assertEqual(url, f"/api/confirmar-deposito/{uuid_str}/")

    def test_resolve_token_obtain_pair(self):
        resolver = resolve(reverse("token_obtain_pair"))

        self.assertEqual(resolver.func.view_class, TokenObtainPairView)

    def test_resolve_token_refresh(self):
        resolver = resolve(reverse("token_refresh"))

        self.assertEqual(resolver.func.view_class, TokenRefreshView)

    def test_resolve_validar_qr(self):
        uuid_str = str(uuid4())

        resolver = resolve(
            reverse("validar_qr", kwargs={"uuid_str": uuid_str})
        )

        self.assertEqual(resolver.func.view_class, views.ValidarQRView)

    def test_resolve_confirmar_deposito(self):
        uuid_str = str(uuid4())

        resolver = resolve(
            reverse(
                "confirmar_deposito",
                kwargs={"uuid_str": uuid_str},
            )
        )

        self.assertEqual(
            resolver.func.view_class,
            views.ConfirmarDepositoView,
        )
