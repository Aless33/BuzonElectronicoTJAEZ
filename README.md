
# Buzón Electrónico TJAEZ


Buzón Electrónico es un sistema web diseñado para el Tribunal de Justicia Administrativa del Estado de Zacatecas (TJAEZ). Permite a ciudadanos y abogados realizar el pre-registro digital de promociones legales y depositarlas físicamente de manera automatizada fuera del horario tradicional.

### Objetivo General

Modernizar la recepción de documentos migrando a una arquitectura en Python (Django)[cite: 1]. El sistema gestiona una interfaz web para el pre-registro y expone una API RESTful para la validación y confirmación ciber-física con el hardware del buzón.

### Arquitectura del Sistema

El sistema implementa una arquitectura cliente-servidor estructurada en:

*   **Módulo Web:** Gestión de formularios dinámicos y renderizado de etiquetas PDF con códigos QR.
*   **API REST:** Endpoints para la validación óptica y confirmación de depósito mediante sensores físicos.
*   **Tareas Asíncronas:** Procesamiento en segundo plano para el envío de acuses provisionales por correo electrónico.

### Estructura del Proyecto

```text
buzon_electronico_tjaez/
│
├───api/                  # Endpoints de comunicación con el hardware
├───web/                  # Vistas, formularios y templates del ciudadano
├───core/                 # Modelos de base de datos y tareas asíncronas
├───utils/                # Motor de renderizado PDF (ReportLab)

├───pruebas_unitarias/    # Pruebas mediante unittest
├───pruebas_aceptacion/   # Pruebas mediante behave
├───Dockerfile            # Configuración de la imagen de la aplicación
├───docker-compose.yml    # Orquestación de servicios
└───requirements.txt      # Dependencias
```

### Tecnologías y Frameworks

| Componente | Tecnología / Framework | Descripción |
| :--- | :--- | :--- |

| **Lenguaje principal** | Python 3.10+ | Lenguaje backend utilizado. |
| **Framework Web** | Django 4.x+ | Entorno de desarrollo principal y ORM. |
| **API** | Django REST Framework | Exposición de endpoints para el hardware. |
| **Base de datos** | PostgreSQL 15 | Persistencia de datos relacional. |
| **Cola de mensajes** | Redis 7 | Broker en memoria para la gestión de tareas. |
| **Tareas Asíncronas** | Celery 5.3+ | Ejecución asíncrona de correos y caducidades. |
| **Infraestructura** | Docker & Compose | Contenedorización del entorno de desarrollo. |

### Dependencias Clave

```text
Django>=4.2.0
djangorestframework>=3.14.0
psycopg2-binary>=2.9.9
celery>=5.3.0
redis>=5.0.1
reportlab>=4.0.0
qrcode>=7.4.2
```

### Ejecución del Proyecto

**1. Requisitos previos**
*   Docker y Docker Compose instalados.
*   Servidor con reloj sincronizado mediante NTP (CENAM).

**2. Clonar el repositorio**
```bash
git clone https://github.com/Aless33/BuzonElectronicoTJAEZ.git
cd buzon_electronico_tjaez
```

**3. Ejecutar los contenedores**
```bash
docker-compose up -d --build
```

**4. Aplicar migraciones de base de datos**
```bash
docker-compose exec web python manage.py migrate
```

**5. Crear superusuario (opcional para acceso al admin)**
```bash
docker-compose exec web python manage.py createsuperuser
```

### Créditos

Autor: Alessandro Villela Espino
