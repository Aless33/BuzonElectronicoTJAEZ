# language: es

Característica: Registro de promociones en el Buzón Electrónico
  Como usuario del sistema TJAEZ
  Quiero registrar distintos tipos de promociones en el buzón electrónico
  Para que queden debidamente ingresadas y se genere un acuse provisional

  # ─── Escenarios: Demanda (solo campos base) ───────────────────────────────

  Escenario: Registro exitoso de una Demanda
    Dado que el usuario abre el formulario de registro
    Y selecciona el tipo de promoción "DEMANDA"
    Cuando llena el correo "usuario@correo.com" y lo confirma con "usuario@correo.com"
    Y llena el número de sobres con 1
    Y envía el formulario
    Entonces el sistema guarda el registro exitosamente
    Y muestra el mensaje "Buzón registrado correctamente."

  
  # ─── Escenarios: Contestación (campos base + expediente) ──────────────────

  Escenario: Registro exitoso de una Contestación con expediente
    Dado que el usuario abre el formulario de registro
    Y selecciona el tipo de promoción "CONTESTACION"
    Cuando llena el correo "abogado@tjaez.gob.mx" y lo confirma con "abogado@tjaez.gob.mx"
    Y llena el número de sobres con 2
    Y llena el número de expediente "123" con año 2024 y ponencia "PONENCIA_1"
    Y envía el formulario
    Entonces el sistema guarda el registro exitosamente
    Y muestra el mensaje "Buzón registrado correctamente."


  # ─── Escenarios: Otros (campos base + expediente + especifique) ───────────

  Escenario: Registro exitoso de tipo Otros con descripción
    Dado que el usuario abre el formulario de registro
    Y selecciona el tipo de promoción "OTROS"
    Cuando llena el correo "usuario@correo.com" y lo confirma con "usuario@correo.com"
    Y llena el número de sobres con 3
    Y llena el número de expediente "456" con año 2025 y ponencia "PONENCIA_2"
    Y especifica "Escrito de aclaraciones adicionales"
    Y envía el formulario
    Entonces el sistema guarda el registro exitosamente
    Y muestra el mensaje "Buzón registrado correctamente."

  # ─── Escenarios: Carga dinámica de campos extra ───────────────────────────

  Escenario: Cambio de tipo muestra campos de expediente
    Dado que el usuario abre el formulario de registro
    Y selecciona el tipo de promoción "AMPARO"
    Entonces el formulario muestra los campos de expediente

  Escenario: Cambio a Demanda oculta campos de expediente
    Dado que el usuario abre el formulario de registro
    Y selecciona el tipo de promoción "DEMANDA"
    Entonces el formulario no muestra campos de expediente

