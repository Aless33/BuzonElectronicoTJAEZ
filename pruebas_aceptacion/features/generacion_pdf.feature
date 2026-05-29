# language: es
Característica: Generación de PDF de etiquetas para el Buzón Electrónico
  Como ciudadano del estado de Zacatecas
  Quiero generar un PDF con mis etiquetas de depósito
  Para poder imprimir mis etiquetas QR y depositar mis sobres en el buzón físico fuera de horario

  # ---------------------------------------------------------------------------
  # Escenario 1 – Happy Path: Trámite de seguimiento
  # ---------------------------------------------------------------------------
  Escenario: Ciudadano genera PDF para una contestación con un sobre
    Dado que el ciudadano ingresó los siguientes datos de trámite de seguimiento:
      | campo               | valor                    |
      | tipo_promocion      | CONTESTACION             |
      | numero_expediente   | 12                       |
      | anio                | 2019                     |
      | ponencia            | PRIMERA PONENCIA         |
      | correo_ciudadano    | ciudadano@example.com    |
      | numero_sobres       | 1                        |
    Cuando el sistema procesa la solicitud de generación de etiquetas
    Entonces el sistema retorna un archivo PDF válido
    Y el PDF contiene exactamente 1 etiqueta generada
    Y cada etiqueta tiene un UUID único
    Y cada etiqueta tiene un dígito verificador de 6 caracteres
    Y la fecha de caducidad de cada etiqueta es a las 23:59 del día actual

  # ---------------------------------------------------------------------------
  # Escenario 2 – Happy Path: Trámite inicial (Demanda)
  # ---------------------------------------------------------------------------
  Escenario: Ciudadano genera PDF para una demanda inicial sin expediente
    Dado que el ciudadano ingresó los siguientes datos de trámite inicial:
      | campo               | valor                    |
      | tipo_promocion      | DEMANDA                  |
      | correo_ciudadano    | abogado@despacho.mx      |
      | numero_sobres       | 1                        |
    Cuando el sistema procesa la solicitud de generación de etiquetas
    Entonces el sistema retorna un archivo PDF válido
    Y el PDF contiene exactamente 1 etiqueta generada

  # ---------------------------------------------------------------------------
  # Escenario 3 – Múltiples sobres
  # ---------------------------------------------------------------------------
  Escenario: Ciudadano solicita etiquetas para tres sobres
    Dado que el ciudadano ingresó los siguientes datos de trámite de seguimiento:
      | campo               | valor                    |
      | tipo_promocion      | ALEGATOS                 |
      | numero_expediente   | 45                       |
      | anio                | 2023                     |
      | ponencia            | SEGUNDA PONENCIA         |
      | correo_ciudadano    | litigante@correo.com     |
      | numero_sobres       | 3                        |
    Cuando el sistema procesa la solicitud de generación de etiquetas
    Entonces el sistema retorna un archivo PDF válido
    Y el PDF contiene exactamente 3 etiquetas generadas
    Y los números de sobre son consecutivos del 1 al 3

  # ---------------------------------------------------------------------------
  # Escenario 4 – Límite máximo de sobres (RNF-02)
  # ---------------------------------------------------------------------------
  Escenario: Ciudadano solicita el máximo de 20 sobres
    Dado que el ciudadano ingresó los siguientes datos de trámite de seguimiento:
      | campo               | valor                    |
      | tipo_promocion      | AMPARO                   |
      | numero_expediente   | 77                       |
      | anio                | 2024                     |
      | ponencia            | TERCERA PONENCIA         |
      | correo_ciudadano    | ciudadano@example.com    |
      | numero_sobres       | 20                       |
    Cuando el sistema procesa la solicitud de generación de etiquetas
    Entonces el sistema retorna un archivo PDF válido
    Y el PDF contiene exactamente 20 etiquetas generadas

  # ---------------------------------------------------------------------------
  # Escenario 5 – Alternativo: Demanda con expediente (violación RN-02)
  # ---------------------------------------------------------------------------
  Escenario: El sistema rechaza una demanda que incluye número de expediente
    Dado que el ciudadano ingresó los siguientes datos incorrectos:
      | campo               | valor                    |
      | tipo_promocion      | DEMANDA                  |
      | numero_expediente   | 999                      |
      | correo_ciudadano    | ciudadano@example.com    |
      | numero_sobres       | 1                        |
    Cuando el sistema procesa la solicitud de generación de etiquetas
    Entonces el sistema lanza un error de validación
    Y el mensaje de error menciona "iniciales"

  # ---------------------------------------------------------------------------
  # Escenario 6 – Alternativo: Correo inválido
  # ---------------------------------------------------------------------------
  Escenario: El sistema rechaza un formulario con correo electrónico inválido
    Dado que el ciudadano ingresó los siguientes datos incorrectos:
      | campo               | valor                    |
      | tipo_promocion      | CONTESTACION             |
      | numero_expediente   | 12                       |
      | anio                | 2019                     |
      | correo_ciudadano    | correoSinArroba          |
      | numero_sobres       | 1                        |
    Cuando el sistema procesa la solicitud de generación de etiquetas
    Entonces el sistema lanza un error de validación
    Y el mensaje de error menciona "correo"

  # ---------------------------------------------------------------------------
  # Escenario 7 – Alternativo: Más de 20 sobres
  # ---------------------------------------------------------------------------
  Escenario: El sistema rechaza una solicitud con más de 20 sobres
    Dado que el ciudadano ingresó los siguientes datos incorrectos:
      | campo               | valor                    |
      | tipo_promocion      | CONTESTACION             |
      | numero_expediente   | 12                       |
      | anio                | 2019                     |
      | correo_ciudadano    | ciudadano@example.com    |
      | numero_sobres       | 25                       |
    Cuando el sistema procesa la solicitud de generación de etiquetas
    Entonces el sistema lanza un error de validación
    Y el mensaje de error menciona "20"

  # ---------------------------------------------------------------------------
  # Escenario 8 – Alternativo: Trámite de seguimiento sin expediente
  # ---------------------------------------------------------------------------
  Escenario: El sistema rechaza una contestación sin número de expediente
    Dado que el ciudadano ingresó los siguientes datos incorrectos:
      | campo               | valor                    |
      | tipo_promocion      | CONTESTACION             |
      | numero_expediente   |                          |
      | anio                | 2024                     |
      | correo_ciudadano    | ciudadano@example.com    |
      | numero_sobres       | 1                        |
    Cuando el sistema procesa la solicitud de generación de etiquetas
    Entonces el sistema lanza un error de validación
    Y el mensaje de error menciona "expediente"
