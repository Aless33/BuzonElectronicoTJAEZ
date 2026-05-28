# language: es
Característica: Generar Etiquetas QR

Escenario: Generación exitosa de códigos QR y Acuse Provisional (Happy Path)
Dado que un ciudadano completó exitosamente el formulario de pre-registro
Y declaró 2 sobres físicos
Cuando el sistema procesa la solicitud para generar los códigos
Entonces se deben crear 2 registros de etiquetas en la base de datos
Y cada etiqueta debe contener un UUID v4 único e irrepetible
Y la caducidad de cada etiqueta debe establecerse a las 23:59 horas del día de su expedición
Y el sistema debe iniciar la descarga de un archivo PDF con formato de recorte

Escenario: Fallo en la generación por falta de sobres físicos
Dado que el sistema recibe una petición para generar códigos QR
Cuando la cantidad de sobres físicos declarados es 0 o nula
Entonces el sistema interrumpe el proceso
Y se realiza un rollback en la base de datos
Y el sistema retorna un mensaje de error indicando que la cantidad de sobres es requerida

Escenario: Fallo por tipo de promoción ausente
Dado que el sistema recibe una petición para generar códigos QR
Cuando el tipo de promoción no es proporcionado
Entonces el sistema interrumpe el proceso
Y el sistema retorna un error indicando que el tipo de promoción es obligatorio

Escenario: Fallo por cantidad de sobres no válida
Dado que el sistema recibe una petición para generar códigos QR
Cuando la cantidad de sobres físicos es un tipo de dato incorrecto
Entonces el sistema interrumpe el proceso
Y el sistema retorna un error indicando que el número de sobres debe ser al menos 1