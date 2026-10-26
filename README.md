# Android Control Center

Aplicación de escritorio para Windows que reúne en una interfaz gráfica varias
funciones de Android Debug Bridge (ADB) y scrcpy. Permite conectar un teléfono
Android por USB o Wi-Fi, controlarlo y reflejar su pantalla, transferir
archivos, instalar APK y consultar información del dispositivo.

La aplicación está escrita en Python y utiliza Tkinter para la interfaz. No
requiere paquetes de Python de terceros; sí necesita Python 3.12 o posterior,
Tkinter y las herramientas externas ADB y scrcpy. **La interfaz actual solo es
compatible con Windows**: aunque ADB y scrcpy también se pueden instalar en
Linux, el programa usa APIs de Windows y no se ejecuta allí.

## Funciones

- **Conexión ADB:** comprueba los dispositivos conectados, permite conectar por
  IP y puerto, y emparejar dispositivos mediante la depuración inalámbrica de
  Android 11 o posterior.
- **Control y espejo:** inicia y detiene scrcpy, con opciones para mantener el
  teléfono despierto y apagar su pantalla física durante el espejo.
- **Controles del teléfono:** envía acciones de inicio, atrás, aplicaciones
  recientes, encendido, volumen y reproducción multimedia.
- **Capturas y portapapeles:** guarda capturas de pantalla en la carpeta del
  programa y permite enviar texto del portapapeles del PC al móvil o recuperar
  texto del móvil.
- **Información del dispositivo:** muestra datos del sistema, procesador,
  batería, memoria, almacenamiento y pantalla; permite copiar el informe.
- **Transferencia e instalación:** envía archivos a `/sdcard/Download`, lista y
  descarga archivos de una ruta del móvil e instala APK desde el PC.
- **Notificaciones y registro:** puede supervisar determinados mensajes de
  `logcat` y mostrarlos en el área de notificación de Windows. Incluye un
  registro de actividad en la aplicación.
- **Bandeja del sistema:** al cerrar la ventana, la aplicación se minimiza a la
  bandeja; desde su menú contextual se puede restaurar o salir.
- **Debloat opcional:** en dispositivos detectados como Xiaomi/POCO ofrece una
  lista seleccionable de paquetes para desinstalarlos para el usuario actual y
  permite volver a habilitarlos desde un punto de restauración.

## Requisitos e instalación

### Windows (ejecutar la aplicación)

Necesitas Windows 10/11, Python 3.12 o posterior con Tcl/Tk, ADB, scrcpy y un
dispositivo Android con la depuración USB o inalámbrica habilitada.

**Opción sencilla: instalar desde WinGet.** Abre PowerShell y ejecuta:

```powershell
winget install --exact --id Python.Python.3.12
winget install --exact Genymobile.scrcpy
```

La instalación de scrcpy desde WinGet incluye ADB. Si Windows pregunta si
quieres aceptar los términos, confirma para continuar. Cierra y vuelve a abrir
PowerShell después de la instalación.

Si `winget` no está disponible, usa las descargas oficiales:

1. Instala Python desde [python.org](https://www.python.org/downloads/windows/).
   Deja activadas las opciones predeterminadas, que incluyen Tcl/Tk.
2. Descarga y extrae scrcpy desde la
   [página oficial de versiones](https://github.com/Genymobile/scrcpy/releases/latest).
   ADB viene incluido en el paquete oficial de Windows de scrcpy.
3. Añade la carpeta extraída de scrcpy a `PATH` siguiendo la
   [guía oficial para Windows](https://github.com/Genymobile/scrcpy/blob/master/doc/windows.md).

No hace falta instalar módulos con `pip`: el programa solo usa la biblioteca
estándar de Python y Tkinter. Si ya tienes ADB instalado por Android Studio o
Platform-Tools, puedes conservarlo; no necesitas instalarlo por separado si
scrcpy ya lo proporciona.

Si `adb` sigue sin estar disponible, descarga las
[Android SDK Platform-Tools para Windows](https://developer.android.com/tools/releases/platform-tools),
extrae la carpeta `platform-tools` y añádela a `PATH`. Si Python se instaló sin
Tkinter, vuelve a ejecutar el instalador oficial y habilita **Tcl/Tk and IDLE**
en las opciones de instalación.

Descarga o clona el repositorio y ejecuta `androidcontrol.pyw` con doble clic.
También puedes iniciarlo desde PowerShell:

```powershell
pyw .\androidcontrol.pyw
```

Para ver los mensajes de error en una terminal, utiliza:

```powershell
py .\androidcontrol.pyw
```

### Linux (herramientas ADB y scrcpy)

**Android Control Center todavía no se ejecuta en Linux** porque su interfaz y
su bandeja del sistema dependen de APIs de Windows. Los siguientes comandos
instalan las herramientas para usar ADB y scrcpy directamente desde Linux; no
habilitan la aplicación gráfica.

En Debian o Ubuntu, abre una terminal y ejecuta:

```bash
sudo apt update && sudo apt install adb scrcpy
```

En otras distribuciones, instala `adb` y `scrcpy` con el gestor de paquetes de
tu sistema. Consulta las instrucciones oficiales de
[instalación de scrcpy en Linux](https://github.com/Genymobile/scrcpy/blob/master/doc/linux.md).
Los paquetes de la distribución pueden ofrecer una versión anterior; la misma
guía incluye opciones oficiales para obtener una versión más reciente.

Si necesitas Python y Tkinter para desarrollar o adaptar el proyecto, en
Debian/Ubuntu puedes instalarlos con:

```bash
sudo apt install python3 python3-tk
```

Esto no elimina la incompatibilidad actual de la aplicación con Linux.

### Comprobar la instalación

En Windows (PowerShell):

```powershell
py --version
adb version
scrcpy --version
```

En Linux (terminal):

```bash
python3 --version
adb version
scrcpy --version
```

Python debe informar la versión 3.12 o posterior. Si un comando no se reconoce,
reabre la terminal; si sigue sin aparecer, comprueba el `PATH` o instala la
herramienta que falta desde los enlaces anteriores. En Linux, los paquetes
Python se obtienen con el gestor de paquetes de la distribución; no se requiere
`pip` para este proyecto.

## Preparar y conectar el teléfono

### Por USB

1. Activa las **Opciones para desarrolladores** y la **Depuración USB** en el
   teléfono.
2. Conecta el teléfono al PC y acepta en el móvil la autorización de depuración
   USB, si aparece.
3. Comprueba que ADB lo detecta:

   ```powershell
   adb devices
   ```

4. En la aplicación, pulsa **Recargar** para actualizar el estado.
5. Para pasar a conexión Wi-Fi desde USB, pulsa **Modo TCP/IP (USB)**. Después,
   consulta la IP del teléfono en la red local, introdúcela junto con el puerto
   `5555` y pulsa **Conectar**. Por ejemplo: `192.168.1.50:5555`.

   El PC y el móvil deben poder comunicarse entre sí por la red local. El modo
   TCP/IP debe usarse en una red de confianza; al terminar, desconecta la sesión
   inalámbrica o desactiva la depuración si ya no la necesitas.

### Por Wi-Fi (Android 11 o posterior)

1. Activa **Opciones para desarrolladores** y **Depuración inalámbrica** en el
   teléfono.
2. En los ajustes de depuración inalámbrica, selecciona **Emparejar dispositivo
   con código**. El teléfono mostrará una dirección IP y puerto de
   emparejamiento, además de un código.
3. En la aplicación, pulsa **Emparejar (Android 11+)** e introduce la dirección
   y el código solicitados.
4. Una vez emparejado, introduce la dirección IP y el puerto de conexión ADB
   que muestra la pantalla principal de depuración inalámbrica y pulsa
   **Conectar**. El puerto de emparejamiento y el de conexión pueden ser
   distintos.

Android puede cambiar el puerto de conexión inalámbrica. Si la conexión deja de
funcionar, vuelve a consultar los ajustes del teléfono y actualiza la dirección
en la aplicación.

## Uso

La ventana está organizada en tres pestañas:

### Control y espejo

Permite administrar la conexión, iniciar scrcpy y enviar acciones de navegación.
Las casillas **Mantener móvil despierto en carga** y **Apagar pantalla física
durante el espejo** ajustan las opciones que recibe scrcpy. Desde esta pestaña
también se puede consultar la información del dispositivo y usar las funciones
de portapapeles y captura.

El botón de desbloqueo utiliza ADB para encender y deslizar la pantalla y, si se
ha guardado un PIN, escribirlo. Su comportamiento depende del bloqueo y la
configuración del teléfono; no sustituye la autorización de ADB ni garantiza
desbloquear todos los dispositivos.

### Transferencia de archivos y APK

- Para enviar un archivo, selecciónalo en el PC; se copia a
  `/sdcard/Download/`.
- Para instalar una aplicación, selecciona un archivo `.apk` local. La
  instalación usa `adb install -r`.
- Para descargar, escribe la ruta del dispositivo (por defecto
  `/sdcard/Download`), pulsa **Listar**, selecciona un elemento y elige la
  carpeta de destino en el PC.

### Notificaciones y registro

Pulsa **Activar Puente de Notificaciones a Windows** para iniciar la
supervisión, o vuelve a pulsarlo para detenerla. La disponibilidad y el detalle
de las notificaciones dependen de la versión de Android, del fabricante y de
los mensajes que exponga `logcat`.

## Debloat y restauración

La opción avanzada se muestra únicamente cuando la aplicación identifica el
dispositivo como Xiaomi/POCO. Presenta una selección de paquetes de Xiaomi,
Facebook y Google; revisa cada elemento antes de confirmar. La operación ejecuta
`pm uninstall -k --user 0`, por lo que elimina la aplicación para el usuario
actual, no necesariamente del sistema.

Antes de aplicar los cambios se crea una carpeta
`Punto_de_Restauracion_<fecha_hora>` junto al programa, con un archivo
`restore_info.json` que registra el dispositivo y los paquetes seleccionados.
La acción de restaurar usa `cmd package install-existing` para volver a
habilitar o instalar los paquetes que el sistema todavía conserva. **El punto
de restauración no guarda copias de los APK ni garantiza la recuperación** si
el paquete se ha eliminado del dispositivo o el sistema no permite habilitarlo.

El debloat puede afectar funciones del fabricante, servicios, aplicaciones o
actualizaciones. Haz una copia de seguridad y asegúrate de entender cada paquete
antes de seleccionarlo. Los cambios se realizan en el dispositivo y son bajo tu
responsabilidad.

## Configuración

La aplicación crea o actualiza `androidcontrol_config.json` en la misma carpeta
que el programa. El archivo contiene opciones como estas:

| Clave | Descripción | Valor inicial |
| --- | --- | --- |
| `ip_port` | Dirección IP y puerto para la conexión inalámbrica ADB | `192.168.1.XX:5555` |
| `device_pin` | PIN usado por la función de auto-desbloqueo | Vacío |
| `stay_awake` | Mantener el teléfono despierto durante el espejo | `true` |
| `turn_screen_off` | Apagar la pantalla física durante el espejo | `true` |
| `auto_reconnect` | Intentar reconectar a la dirección configurada | `true` |
| `last_pc_pull_dir` | Última carpeta elegida para guardar descargas | Carpeta `Downloads` del usuario |

La configuración se guarda en texto plano. **El PIN no está cifrado**: deja
`device_pin` vacío si no necesitas esta función y protege el acceso al archivo y
al equipo. No compartas `androidcontrol_config.json`.

## Solución de problemas

- **No aparece el dispositivo:** ejecuta `adb devices`, desbloquea el teléfono
  y acepta el diálogo de autorización. En Windows, puede ser necesario instalar
  el controlador USB del fabricante.
- **ADB aparece como `unauthorized`:** revoca y vuelve a autorizar la
  depuración USB desde las opciones para desarrolladores; reconecta el cable y
  acepta el aviso en el teléfono.
- **No se encuentran ADB o scrcpy:** en Windows verifica `PATH` con
  `where.exe adb` y `where.exe scrcpy`; en Linux, con `command -v adb` y
  `command -v scrcpy`. Reinicia la terminal después de instalar o modificar
  `PATH`.
- **No conecta por Wi-Fi:** comprueba que el PC y el teléfono estén en la misma
  red, que la depuración inalámbrica siga activa y que estés usando el puerto
  vigente que muestra Android.
- **La aplicación no inicia:** confirma que estás usando Python 3.12 o posterior
  con Tkinter habilitado.
- **El espejo no se inicia:** comprueba primero que `scrcpy --version` funciona
  desde la misma terminal y que ADB detecta el teléfono.

## Estructura del proyecto

```text
.
├── androidcontrol.pyw          # Aplicación de escritorio
├── androidcontrol_config.json  # Preferencias locales (se crea al usar la aplicación)
├── LICENSE                    # Licencia MIT
└── README.md                  # Esta guía
```

Las carpetas `Punto_de_Restauracion_*` se crean durante el uso de la función de
debloat y contienen metadatos para intentar restaurar los paquetes.

## Licencia

Este proyecto se distribuye bajo la licencia MIT. Consulta [LICENSE](LICENSE)
para ver el texto completo.
