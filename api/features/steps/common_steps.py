from behave import then
import os
import django
django.setup()


os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "buzon_electronico_tjaez.settings",
)


@then("la API retorna el código de estado {codigo:d}")
def step_codigo_estado(context, codigo):
    assert context.response.status_code == codigo, (
        f"Se esperaba {codigo}, "
        f"se obtuvo {context.response.status_code}. "
        f"Respuesta: {context.response.content}"
    )


@then('la respuesta contiene el campo "{campo}"')
def step_contiene_campo(context, campo):
    assert campo in context.response_json, (
        f"El campo '{campo}' no está en la respuesta: "
        f"{context.response_json}"
    )


@then('la respuesta contiene el mensaje de error "{mensaje}"')
def step_contiene_mensaje_error(context, mensaje):
    assert context.response_json.get("error") == mensaje, (
        f"Se esperaba error '{mensaje}', "
        f"se obtuvo '{context.response_json.get('error')}'"
    )


@then('el estado de la etiqueta en base de datos es "{estado}"')
def step_estado_en_bd(context, estado):
    context.etiqueta.refresh_from_db()

    assert context.etiqueta.estado == estado, (
        f"Se esperaba estado '{estado}', "
        f"se obtuvo '{context.etiqueta.estado}'"
    )
