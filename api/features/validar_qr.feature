# language: es

Característica: Validación de QR en el Buzón Electrónico
  Como hardware del buzón electrónico
  Quiero consultar la validez de un código QR escaneado
  Para autorizar o rechazar la apertura de la compuerta física

  Escenario: UUID con formato inválido retorna 404
    Dado que el hardware escanea el código "esto-no-es-un-uuid"
    Cuando consulta la validez del QR
    Entonces la API retorna el código de estado 404
    Y la respuesta contiene el mensaje de error "Formato de QR inválido."

  Escenario: UUID válido pero inexistente retorna 404
    Dado que el hardware escanea el código "00000000-0000-0000-0000-000000000000"
    Cuando consulta la validez del QR
    Entonces la API retorna el código de estado 404
    Y la respuesta contiene el mensaje de error "QR no encontrado."

  Escenario: QR ya depositado retorna 400
    Dado que existe una etiqueta con estado "DEPOSITADO"
    Cuando el hardware consulta la validez de esa etiqueta
    Entonces la API retorna el código de estado 400
    Y la respuesta contiene el campo "estado_actual"

  Escenario: QR cancelado retorna 400
    Dado que existe una etiqueta con estado "CANCELADO"
    Cuando el hardware consulta la validez de esa etiqueta
    Entonces la API retorna el código de estado 400
    Y la respuesta contiene el campo "estado_actual"

  Escenario: QR no presentado retorna 400
    Dado que existe una etiqueta con estado "NO_PRESENTADO"
    Cuando el hardware consulta la validez de esa etiqueta
    Entonces la API retorna el código de estado 400
    Y la respuesta contiene el campo "estado_actual"

  Escenario: QR caducado retorna 400 y cambia estado en base de datos
    Dado que existe una etiqueta caducada
    Cuando el hardware consulta la validez de esa etiqueta
    Entonces la API retorna el código de estado 400
    Y la respuesta contiene el mensaje de error "La etiqueta ha caducado."
    Y el estado de la etiqueta en base de datos es "NO_PRESENTADO"

  Escenario: QR válido y vigente retorna 200 con autorización
    Dado que existe una etiqueta válida y vigente
    Cuando el hardware consulta la validez de esa etiqueta
    Entonces la API retorna el código de estado 200
    Y la respuesta contiene el campo "autorizado"
    Y la respuesta contiene el campo "uuid"
    Y la respuesta contiene el campo "digito_verificador"
    Y la respuesta contiene el campo "numero_sobre"

  Escenario: Consultar QR válido no cambia su estado en base de datos
    Dado que existe una etiqueta válida y vigente
    Cuando el hardware consulta la validez de esa etiqueta
    Entonces el estado de la etiqueta en base de datos es "ETIQUETA_GENERADA"

  Escenario: Método POST en validar QR retorna 405
    Dado que existe una etiqueta válida y vigente
    Cuando el hardware envía un POST a validar QR
    Entonces la API retorna el código de estado 405

  Escenario: Usuario no autenticado no puede validar QR
    Dado que existe una etiqueta válida y vigente
    Y el hardware no está autenticado
    Cuando el hardware consulta la validez de esa etiqueta
    Entonces la API retorna el código de estado 401