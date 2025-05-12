# Sistema de Gestión de Eventos y Entradas

Este es un sistema completo para la gestión de eventos y venta de entradas, desarrollado con Python, Django, MySQL, HTML, CSS y JavaScript.

## Características

- Gestión completa de eventos (creación, edición, eliminación)
- Diferentes tipos de entradas para cada evento
- Sistema de compra de entradas con códigos QR únicos
- Verificación de entradas mediante escáner QR o código manual
- Perfiles de usuario personalizados
- Panel de control con estadísticas y gráficos
- Diseño responsive y moderno

## Requisitos

- Python 3.8 o superior
- MySQL 5.7 o superior
- Pip (gestor de paquetes de Python)
- Virtualenv (opcional, pero recomendado)

## Instalación

1. Clona este repositorio en tu máquina local:

```bash
git clone https://github.com/tuusuario/evento-manager.git
cd evento-manager
```

2. Crea y activa un entorno virtual (opcional):

```bash
python -m venv venv
# En Windows
venv\Scripts\activate
# En Linux/Mac
source venv/bin/activate
```

3. Instala las dependencias:

```bash
pip install -r requirements.txt
```

4. Crea la base de datos en MySQL:

```sql
CREATE DATABASE camilo;
```

5. Configura tu archivo `.env` con tus datos de conexión a MySQL (crea un archivo nuevo en la raíz del proyecto):

```
SECRET_KEY=tu_clave_secreta_django
DEBUG=True
DB_NAME=camilo
DB_USER=root
DB_PASSWORD=camilo
DB_HOST=localhost
DB_PORT=3306
```

6. Ejecuta las migraciones para crear las tablas en la base de datos:

```bash
python manage.py makemigrations
python manage.py migrate
```

7. Crea un superusuario (administrador):

```bash
python manage.py createsuperuser
```

8. Inicia el servidor de desarrollo:

```bash
python manage.py runserver
```

9. Accede a la aplicación en tu navegador:

```
http://localhost:8000/
```

## Estructura del Proyecto

El proyecto sigue una estructura MVC (Modelo-Vista-Controlador):

- **Models**: Definición de los modelos de datos (eventos, tipos de entradas, entradas, usuarios, etc.)
- **Views**: Lógica de negocio y procesamiento de datos
- **Templates**: Plantillas HTML para la interfaz de usuario
- **Static**: Archivos estáticos (CSS, JavaScript, imágenes)
- **URLs**: Configuración de rutas URL

## Uso

### Para Administradores

1. Accede al panel de administración en `http://localhost:8000/admin/`
2. Crea eventos, tipos de entradas y gestiona usuarios
3. Utiliza el panel de control en `http://localhost:8000/panel-control/` para ver estadísticas
4. Verifica entradas en `http://localhost:8000/verificar-entrada/`

### Para Usuarios

1. Regístrate en la plataforma
2. Explora eventos y compra entradas
3. Accede a tus entradas en "Mis Entradas"
4. Visualiza tus entradas con códigos QR únicos

## Personalización

- Modifica los archivos CSS en `/static/css/` para cambiar el diseño
- Ajusta los templates en `/eventos/templates/` para personalizar las vistas
- Extiende los modelos en `/eventos/models.py` para añadir nuevas funcionalidades

## Licencia

Este proyecto está bajo la Licencia MIT. Consulta el archivo `LICENSE` para más detalles.

## Contacto

Si tienes preguntas o sugerencias, no dudes en contactarnos:

- **Email**: tu@email.com
- **Sitio web**: www.tusitio.com