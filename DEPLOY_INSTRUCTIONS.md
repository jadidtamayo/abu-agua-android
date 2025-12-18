# Cómo desplegar AbuAgua en Android

Para instalar la aplicación en tu teléfono, utilizaremos `buildozer`. Sigue estos pasos:

## 1. Instalar Dependencias del Sistema
Abre una terminal y ejecuta el siguiente comando para instalar las librerías necesarias (requiere contraseña de administrador/root):

```bash
sudo apt update
sudo apt install -y git zip unzip openjdk-17-jdk python3-pip autoconf libtool pkg-config zlib1g-dev libncurses5-dev libncursesw5-dev libtinfo5 cmake libffi-dev libssl-dev
```

## 2. Instalar Buildozer
Instala la herramienta de automatización de compilación:

```bash
pip3 install --user --upgrade buildozer
```

Asegúrate de que la ruta de instalación esté en tu PATH (normalmente `~/.local/bin`).

## 3. Preparar el Teléfono
1. **Activa las Opciones de Desarrollador**: Ve a `Ajustes` > `Acerca del teléfono` y toca `Número de compilación` 7 veces.
2. **Activa la Depuración por USB**: Ve a `Ajustes` > `Sistema` > `Opciones para desarrolladores` y activa `Depuración por USB`.
3. Conecta tu teléfono al PC con un cable USB.
4. Acepta la confirmación de huella digital RSA en la pantalla de tu teléfono si aparece.

## 4. Construir e Instalar
Navega a la carpeta del proyecto (`abuAguaApk`) y ejecuta:

```bash
cd /home/jadid/Desktop/AbuAgua/abuAguaApk
buildozer android debug deploy run
```

*Nota: La primera vez que ejecutes esto, tardará bastante (puede ser más de 30 minutos) porque descargará el SDK y NDK de Android. Ten paciencia.*

## Solución de Problemas Comunes

### Error: `adb command not found`
Si falla diciendo que no encuentra `adb`, instálalo:
```bash
sudo apt install adb
```

### El teléfono no se detecta
Ejecuta `adb devices`. Si sale "unauthorized", revisa la pantalla de tu teléfono para aceptar el permiso.

### Error de compilación con Cython
Si ves errores relacionados con Cython, intenta reinstalarlo:
```bash
pip3 install --user --upgrade "cython<3.0.0"
```
(Buildozer a veces prefiere versiones antiguas de Cython).
