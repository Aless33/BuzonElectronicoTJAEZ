from django.test import SimpleTestCase
from django.urls import resolve, reverse

from web import views


class BuzonURLTestCase(SimpleTestCase):
    """
    Pruebas unitarias de URLs bajo enfoque TDD.
    """

    def test_reverse_buzon_crear(self):
        """

        Se espera que el nombre buzon_crear resuelva a la ruta principal.
        """

        url = reverse("buzon_crear")

        self.assertEqual(url, "/buzon/")

    def test_reverse_buzon_form_parcial(self):
        """

        Se espera que el nombre buzon_form_parcial resuelva correctamente.
        """

        url = reverse("buzon_form_parcial")

        self.assertEqual(url, "/buzon/form-parcial/")

    def test_resolve_buzon_crear_vista_correcta(self):
        """

        Se espera que la ruta principal use la vista buzon_crear.
        """

        resolver = resolve(reverse("buzon_crear"))

        self.assertEqual(resolver.func, views.buzon_crear)

    def test_resolve_buzon_form_parcial_vista_correcta(self):
        """

        Se espera que la ruta form-parcial use la vista buzon_form_parcial.
        """

        resolver = resolve(reverse("buzon_form_parcial"))

        self.assertEqual(resolver.func, views.buzon_form_parcial)

    def test_nombre_url_buzon_crear_correcto(self):
        """

        Se espera que la URL principal conserve el nombre buzon_crear.
        """

        resolver = resolve(reverse("buzon_crear"))

        self.assertEqual(resolver.url_name, "buzon_crear")

    def test_nombre_url_buzon_form_parcial_correcto(self):
        """

        Se espera que la URL parcial conserve el nombre buzon_form_parcial.
        """

        resolver = resolve(reverse("buzon_form_parcial"))

        self.assertEqual(resolver.url_name, "buzon_form_parcial")
