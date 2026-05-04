# Buzón Electrónico TJAEZ

**Buzón Electrónico** es un sistema web y API diseñado para el **Tribunal de Justicia Administrativa del Estado de Zacatecas (TJAEZ)**.  
Su función es permitir a los ciudadanos y abogados realizar el pre-registro digital de sus promociones y depositarlas de manera física y automatizada fuera del horario tradicional de ventanilla.

---

## Objetivo General

Modernizar la recepción de documentos mediante la migración a un entorno basado en **Python (Django)**.  
El sistema gestiona una interfaz web para el pre-registro y proporciona una API robusta para la comunicación bidireccional con el hardware del buzón físico.

---

## Arquitectura del Sistema

El sistema opera bajo una arquitectura cliente-servidor dividida en módulos.  
Contempla una plataforma web accesible para la generación de códigos QR (pre-registro) y una API RESTful que permite la integración ciber-física para la lectura, apertura y confirmación de recepción mediante sensores.

---

## Estructura del Proyecto

```plaintext
buzon_electronico_tjaez/
│
├── api/
│   ├── views.py          # Endpoints de validación y confirmación
│   ├── serializers.py    # Transformación de datos JSON
│   └── urls.py           # Rutas de la API RESTful
│
├── core/
│   ├── models.py         # Modelos de Base de Datos (Promocion, Etiqueta)
│   ├── admin.py          # Panel de monitor de TI
│   └── tasks.py          # Tareas asíncronas (Celery/CRON)
│
├── web/
│   ├── forms.py          # Lógica de formularios dinámicos
│   ├── views.py          # Renderizado de portal ciudadano
│   └── templates/        # Interfaz de usuario responsiva
│
└── utils/
    └── pdf_generator.py  # Motor de renderizado de QR y acuses
````

---

## Tecnologías y Frameworks

| Componente         | Tecnología / Framework | Descripción                                                           |
| ------------------ | ---------------------- | --------------------------------------------------------------------- |
| Lenguaje principal | Python 3.10+           | Lenguaje backend utilizado para la lógica del sistema.                |
| Framework Web      | Django 4.x+            | Provee el entorno de desarrollo, ORM y panel de administración.       |
| API                | Django REST Framework  | Creación de los endpoints para comunicación con el hardware.          |
| Seguridad          | JWT y TLS 1.2+         | Autenticación del hardware por tokens y cifrado de extremo a extremo. |
| Base de datos      | PostgreSQL / SQLite    | Persistencia relacional para el control de estados y metadatos.       |
| Tareas Asíncronas  | Celery / CRON          | Ejecución de envíos de correo e invalidación nocturna de QRs.         |

---

## Estructura de los Módulos

### Módulo Web (Frontend)

Encargado de la interacción directa con el ciudadano:

* **Formulario Condicional:** Adapta campos según el tipo de promoción, ocultando `"Número de expediente"` si es un trámite inicial.
* **Generador de Identificadores:** Crea un UUID versión 4 y un dígito verificador corto por cada sobre.
* **Renderizado de Documentos:** Genera el PDF con las etiquetas QR y acuses provisionales.

### Módulo API REST (Backend Hardware)

Gestión de la comunicación con los sensores físicos:

* **Endpoint de Validación (GET):** Recibe el UUID leído por el escáner, valida su vigencia (antes de las 23:59 hrs) y autoriza la apertura.
* **Endpoint de Confirmación (POST):** Recibe la señal del sensor físico indicando la caída del sobre y cambia el estado a `DEPOSITADO`.

### Módulo de Notificaciones y Tareas Programadas

* **Disparo de Acuse:** Envío asíncrono de correo electrónico al usuario tras confirmar el depósito.
* **Invalidación Nocturna:** Tarea programada a las 00:01 hrs para cambiar a `NO_PRESENTADO` los registros no depositados.

---

## Dependencias Clave (`requirements.txt`)

```txt
Django>=4.2.0
djangorestframework>=3.14.0
PyJWT>=2.8.0
celery>=5.3.0
reportlab>=4.0.0
qrcode>=7.4.2
```

---

## Ejecución del Proyecto

### 1. Requisitos previos

* Python 3.10 o superior instalado.
* Entorno virtual configurado (`venv`).
* Servidor con reloj sincronizado mediante NTP (CENAM) para la precisión legal.

### 2. Clonar el proyecto e instalar dependencias

```bash
git clone <URL_DEL_REPOSITORIO>
cd buzon_electronico_tjaez
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Migraciones y ejecución

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py runserver
```

---

## Créditos

**Autor:** Alessandro Villela Espino
