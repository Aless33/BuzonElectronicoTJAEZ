# language: es

Característica: Confirmación de depósito físico
  Como hardware del buzón electrónico
  Quiero confirmar el depósito físico de una etiqueta
  Para registrar que el sobre fue depositado correctamente

  Escenario: Confirmar depósito válido retorna 200
    Dado que existe una etiqueta generada y vigente para depósito
    Cuando el hardware confirma el depósito con sensor verdadero
    Entonces la API retorna el código de estado 200
    Y la respuesta contiene el campo "depositado"
    Y el estado de la etiqueta en base de datos es "DEPOSITADO"

  Escenario: Confirmar depósito asigna fecha de depósito
    Dado que existe una etiqueta generada y vigente para depósito
    Cuando el hardware confirma el depósito con sensor verdadero
    Entonces la API retorna el código de estado 200
    Y la etiqueta tiene fecha de depósito registrada

  Escenario: UUID inválido al confirmar depósito retorna 404
    Dado que el hardware tiene el UUID de depósito "uuid-invalido"
    Cuando el hardware confirma el depósito con sensor verdadero
    Entonces la API retorna el código de estado 404
    Y la respuesta contiene el mensaje de error "Formato de UUID inválido."

  Escenario: UUID inexistente al confirmar depósito retorna 404
    Dado que el hardware tiene el UUID de depósito "00000000-0000-0000-0000-000000000000"
    Cuando el hardware confirma el depósito con sensor verdadero
    Entonces la API retorna el código de estado 404
    Y la respuesta contiene el mensaje de error "UUID no encontrado."

  Escenario: Confirmar depósito sin campo sensor retorna 400
    Dado que existe una etiqueta generada y vigente para depósito
    Cuando el hardware confirma el depósito sin enviar sensor
    Entonces la API retorna el código de estado 400
    Y la respuesta contiene el mensaje de error "Falta el campo 'sensor_confirmado' en el payload."

  Escenario: Confirmar depósito con sensor falso retorna 400
    Dado que existe una etiqueta generada y vigente para depósito
    Cuando el hardware confirma el depósito con sensor falso
    Entonces la API retorna el código de estado 400
    Y la respuesta contiene el mensaje de error "El sensor no confirmó el depósito."
    Y el estado de la etiqueta en base de datos es "ETIQUETA_GENERADA"

  Escenario: Confirmar depósito duplicado retorna 409
    Dado que existe una etiqueta ya depositada
    Cuando el hardware confirma el depósito con sensor verdadero
    Entonces la API retorna el código de estado 409
    Y la respuesta contiene el mensaje de error "Esta etiqueta ya fue depositada anteriormente."

  Escenario: Confirmar depósito de etiqueta cancelada retorna 400
    Dado que existe una etiqueta cancelada para depósito
    Cuando el hardware confirma el depósito con sensor verdadero
    Entonces la API retorna el código de estado 400
    Y la respuesta contiene el campo "estado_actual"

  Escenario: Confirmar depósito de etiqueta caducada retorna 400
    Dado que existe una etiqueta caducada para depósito
    Cuando el hardware confirma el depósito con sensor verdadero
    Entonces la API retorna el código de estado 400
    Y la respuesta contiene el mensaje de error "La etiqueta ha caducado."
    Y el estado de la etiqueta en base de datos es "NO_PRESENTADO"

  Escenario: Método GET en confirmar depósito retorna 405
    Dado que existe una etiqueta generada y vigente para depósito
    Cuando el hardware envía un GET a confirmar depósito
    Entonces la API retorna el código de estado 405

  Escenario: Usuario no autenticado no puede confirmar depósito
    Dado que existe una etiqueta generada y vigente para depósito
    Y el hardware de depósito no está autenticado
    Cuando el hardware confirma el depósito con sensor verdadero
    Entonces la API retorna el código de estado 401