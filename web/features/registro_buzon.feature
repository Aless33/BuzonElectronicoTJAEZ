# language: es
Característica: Registro de promociones en el buzón electrónico
  Como ciudadano
  Quiero registrar una promoción en el buzón electrónico
  Para obtener etiquetas y acuse provisional en PDF

  Escenario: Registrar una demanda válida
    Dado que el ciudadano está en el formulario de registro de buzón
    Cuando selecciona el tipo de promoción "DEMANDA"
    Y captura el correo "ciudadano@example.com"
    Y confirma el correo "ciudadano@example.com"
    Y captura "1" sobres
    Y envía el formulario
    Entonces el sistema debe generar un PDF de etiquetas

  Escenario: Rechazar registro cuando los correos no coinciden
    Dado que el ciudadano está en el formulario de registro de buzón
    Cuando selecciona el tipo de promoción "DEMANDA"
    Y captura el correo "ciudadano@example.com"
    Y confirma el correo "otro@example.com"
    Y captura "1" sobres
    Y envía el formulario
    Entonces el sistema debe mostrar el error "Los correos electrónicos no coinciden."

  Escenario: Mostrar campos extra para Contestación
    Dado que el ciudadano está en el formulario de registro de buzón
    Cuando selecciona el tipo de promoción "CONTESTACION"
    Entonces el sistema debe mostrar los campos de expediente

  Escenario: Mostrar campo especifique para Otros
    Dado que el ciudadano está en el formulario de registro de buzón
    Cuando selecciona el tipo de promoción "OTROS"
    Entonces el sistema debe mostrar el campo "especifique"

  Escenario: Rechazar registro con cero sobres
    Dado que el ciudadano está en el formulario de registro de buzón
    Cuando selecciona el tipo de promoción "DEMANDA"
    Y captura el correo "ciudadano@example.com"
    Y confirma el correo "ciudadano@example.com"
    Y captura "0" sobres
    Y envía el formulario
    Entonces el sistema debe mostrar un error en el campo "numero_sobres"