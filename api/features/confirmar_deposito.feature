# language: es

Característica: Confirmación de depósito físico en el Buzón Electrónico
  Como hardware del buzón electrónico
  Quiero notificar al sistema que un sobre fue depositado físicamente
  Para que el sistema registre el depósito y envíe el acuse al ciudadano

  # ─── Escenarios: Formato de entrada ───────────────────────────────────────

  Escenario: UUID con formato inválido retorna 404
    Dado que el sensor detecta el depósito del sobre con UUID "no-es-uuid"
    Cuando el hardware confirma el depósito con sensor en true
    Entonces la API retorna el código de estado 404

  Escenario: JSON inválido en el cuerpo retorna 400
    Dado que existe una etiqueta válida y vigente para depósito
    Cuando el hardware envía un cuerpo JSON inválido
    Entonces la API retorna el código de estado 400

  Escenario: Falta el campo sensor_confirmado retorna 400
    Dado que existe una etiqueta válida y vigente para depósito
    Cuando el hardware confirma el depósito sin el campo sensor
    Entonces la API retorna el código de estado 400
    Y la respuesta contiene "sensor_confirmado" en el mensaje de error

  Escenario: Sensor en false retorna 400
    Dado que existe una etiqueta válida y vigente para depósito
    Cuando el hardware confirma el depósito con sensor en false
    Entonces la API retorna el código de estado 400

  Escenario: Método GET en confirmar depósito retorna 405
    Dado que existe una etiqueta válida y vigente para depósito
    Cuando el hardware envía un GET a confirmar depósito
    Entonces la API retorna el código de estado 405

  # ─── Escenarios: UUID inexistente ─────────────────────────────────────────

  Escenario: UUID inexistente retorna 404
    Dado que el sensor detecta el depósito del sobre con UUID "00000000-0000-0000-0000-000000000000"
    Cuando el hardware confirma el depósito con sensor en true
    Entonces la API retorna el código de estado 404

  # ─── Escenarios: Depósito duplicado ───────────────────────────────────────

  Escenario: Depósito duplicado retorna 409
    Dado que existe una etiqueta con estado "DEPOSITADO" para depósito
    Cuando el hardware confirma el depósito con sensor en true para esa etiqueta
    Entonces la API retorna el código de estado 409

  # ─── Escenarios: Estados inválidos ────────────────────────────────────────

  Escenario: Etiqueta cancelada retorna 400
    Dado que existe una etiqueta con estado "CANCELADO" para depósito
    Cuando el hardware confirma el depósito con sensor en true para esa etiqueta
    Entonces la API retorna el código de estado 400
    Y la respuesta contiene el campo "estado_actual"

  Escenario: Etiqueta no presentada retorna 400
    Dado que existe una etiqueta con estado "NO_PRESENTADO" para depósito
    Cuando el hardware confirma el depósito con sensor en true para esa etiqueta
    Entonces la API retorna el código de estado 400

  # ─── Escenarios: Etiqueta caducada ────────────────────────────────────────

  Escenario: Etiqueta caducada retorna 400 y cambia estado
    Dado que existe una etiqueta caducada para depósito
    Cuando el hardware confirma el depósito con sensor en true para esa etiqueta
    Entonces la API retorna el código de estado 400
    Y el estado de la etiqueta en base de datos es "NO_PRESENTADO"

  # ─── Escenarios: Depósito exitoso ─────────────────────────────────────────

  Escenario: Depósito exitoso retorna 200 y cambia estado en base de datos
    Dado que existe una etiqueta válida y vigente para depósito
    Cuando el hardware confirma el depósito con sensor en true para esa etiqueta
    Entonces la API retorna el código de estado 200
    Y la respuesta contiene el campo "depositado"
    Y la respuesta contiene el campo "uuid"
    Y la respuesta contiene el campo "fecha_deposito"
    Y la respuesta contiene el campo "digito_verificador"
    Y el estado de la etiqueta en base de datos es "DEPOSITADO"

  Escenario: Depósito exitoso registra timestamp en base de datos
    Dado que existe una etiqueta válida y vigente para depósito
    Cuando el hardware confirma el depósito con sensor en true para esa etiqueta
    Entonces la fecha de depósito queda registrada en base de datos