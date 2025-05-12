@echo off
REM Script para inicializar el proyecto EventosYA en Windows
echo Inicializando el proyecto de Gestion de Eventos y Entradas...

REM Crear entorno virtual
echo Creando entorno virtual...
python -m venv venv

REM Activar entorno virtual
echo Activando entorno virtual...
call venv\Scripts\activate

REM Instalar dependencias
echo Instalando dependencias...
pip install -r requirements.txt

REM Crear archivo .env con las variables de entorno
echo Creando archivo .env...
echo SECRET_KEY=django-insecure-^i6^9g4^0g0gm^q2^n#@l3j9^+wm=$^p^&^76s@4ecp=x@=q4e > .env
echo DEBUG=True >> .env
echo DB_NAME=camilo >> .env
echo DB_USER=root >> .env
echo DB_PASSWORD=camilo >> .env
echo DB_HOST=localhost >> .env
echo DB_PORT=3306 >> .env

REM Crear las carpetas de static y media
echo Creando carpetas para archivos estaticos y media...
mkdir static\css
mkdir static\js
mkdir static\img
mkdir media\event_images

REM Copiar archivos estáticos desde la carpeta source (si existe)
echo Copiando archivos estaticos...
xcopy /E /I /Y source\static static

REM Crear base de datos (asumiendo que MySQL está en el PATH)
echo Configurando la base de datos...
echo Asegurate de tener MySQL instalado y ejecutando
echo Iniciando script SQL para crear la base de datos...
mysql -u root -pcamilo < db_setup.sql

REM Realizar las migraciones de Django
echo Realizando migraciones de Django...
python manage.py makemigrations
python manage.py migrate

REM Crear superusuario
echo Creando superusuario...
python manage.py createsuperuser

REM Recolectar archivos estáticos
echo Recolectando archivos estaticos...
python manage.py collectstatic --noinput

REM Iniciar el servidor
echo Iniciando el servidor...
python manage.py runserver

REM Fin
echo Proyecto inicializado correctamente
echo Accede a http://localhost:8000/ para ver la aplicacion