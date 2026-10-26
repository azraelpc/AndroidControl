# Android Control Center

Aplicación de escritorio para Windows y Linux que reúne en una interfaz gráfica
varias funciones de Android Debug Bridge (ADB) y scrcpy. Permite conectar un
teléfono Android por USB o Wi-Fi, controlarlo y reflejar su pantalla, transferir
archivos, instalar APK y consultar información del dispositivo.

La aplicación está escrita en Python y utiliza Tkinter para la interfaz. No
requiere paquetes de Python de terceros; sí necesita Python 3.10 o posterior,
Tkinter y las herramientas externas ADB y scrcpy. En Linux, cerrar la ventana
termina la aplicación; la bandeja del sistema y las notificaciones emergentes
están disponibles solo en Windows.

<img width="500" alt="image" src="https://github.com/user-attachments/assets/a492e765-e9b7-40e1-88d1-90f1ceebe6f5" /> <img width="475" alt="image" src="https://github.com/user-attachments/assets/fb7ffae3-2061-4b9b-bdb6-449e371d78c9" />


## Funciones

- **Conexión ADB:** comprueba los dispositivos conectados, permite conectar por
  IP y puerto, y emparejar dispositivos mediante la depuración inalámbrica de
  Android 11 o posterior.
- **Control y espejo:** inicia y detiene scrcpy, con opciones para mantener el
  teléfono despierto y apagar su pantalla física durante el espejo.
- **Cast a TV:** abre Google Chrome para emitir el escritorio a receptores
  Google Cast, o el selector Miracast del sistema cuando esté disponible.
  Mantén la ventana de scrcpy visible en el escritorio compartido.
- **Controles del teléfono:** envía acciones de inicio, atrás, aplicaciones
  recientes, encendido, volumen y reproducción multimedia.
- **Capturas y portapapeles:** guarda capturas de pantalla en la carpeta del
  programa y permite enviar texto del portapapeles del PC al móvil o recuperar
  texto del móvil.
- **Información del dispositivo:** muestra datos del sistema, procesador,
  batería, memoria, almacenamiento y pantalla; permite copiar el informe.
- **Gestor de archivos:** ventana de dos paneles PC/móvil, navegación por
  carpetas, selección múltiple, cola de subidas y descargas e instalación de APK.
  Previsualización integrada de fotos y fragmentos de vídeo con dependencias opcionales.
- **Notificaciones y registro:** puede supervisar determinados mensajes de
  `logcat`; muestra avisos emergentes en Windows y registra actividad dentro de
  la aplicación en ambos sistemas.
- **Bandeja del sistema (Windows):** al cerrar la ventana, la aplicación se
  minimiza a la bandeja; desde su menú contextual se puede restaurar o salir.
- **Debloat opcional:** en dispositivos detectados como Xiaomi/POCO ofrece una
  lista seleccionable de paquetes para desinstalarlos para el usuario actual y
  permite volver a habilitarlos desde un punto de restauración.
- **Análisis de estado:** junto al debloat y con la misma detección existente,
  consulta el estado del móvil sin modificar ajustes ni proponer optimizaciones.

## Gestor de archivos

En **Transferencia Archivos & APKs**, pulsa **Abrir gestor de archivos** con el
móvil conectado. El panel izquierdo corresponde al PC y el derecho al móvil.
Introduce una ruta y pulsa Intro, usa la carpeta superior o haz doble clic en
una carpeta. El selector del PC permite cambiar también de unidad; el móvil
incluye accesos a Descargas, Cámara, Imágenes y Vídeos.

Selecciona uno o varios elementos y pulsa **Subir** o **Descargar**. El destino
es la carpeta abierta en el panel contrario. Las carpetas se copian completas.
Se pide confirmación y se rechazan destinos ya existentes, sin sobrescribir ni
combinar contenido. La cola muestra los archivos pendientes, en curso,
completados o con error; selecciona una fila para consultar su detalle.
**Cancelar pendientes** no interrumpe la transferencia activa. Un error puede
dejar un archivo o carpeta parcial en el destino; no se borra automáticamente.
El gestor conserva el dispositivo elegido al abrirse aunque cambie la conexión
activa en la ventana principal. No permite borrar archivos del móvil.

### Fotos y vídeos

Selecciona una imagen para verla en el panel **Vista previa**, sin abrir una
aplicación externa. Los vídeos muestran en bucle un fragmento de hasta seis
segundos, a cinco fotogramas por segundo y sin sonido, con pausa/reproducción.
No es un reproductor completo. Puedes desactivar la vista previa automática o
solicitarla con doble clic o con el menú contextual.

Las fotos y vídeos del móvil se descargan primero a una carpeta temporal del PC,
que se elimina al terminar de generar la vista previa; no se modifica el original.
Los archivos remotos mayores de 32 MB no se descargan automáticamente y requieren
confirmación manual. La compatibilidad depende de los formatos que admitan los
decodificadores; no se garantiza HEIC, contenido protegido ni todos los códecs.

El gestor y las transferencias funcionan con la biblioteca estándar. Para las
previsualizaciones, instala las dependencias opcionales en el **mismo Python
con el que ejecutes la aplicación**:

```powershell
py -m pip install Pillow imageio-ffmpeg
```

En Linux, usa `python3 -m pip install Pillow imageio-ffmpeg` dentro de un entorno
virtual. Pillow decodifica las imágenes e `imageio-ffmpeg` proporciona FFmpeg para
el vídeo; si ya hay `ffmpeg` en `PATH`, se utiliza ese ejecutable.
En el entorno virtual de este proyecto ya están instaladas. En Windows puedes
ejecutar la aplicación con ese entorno:

```powershell
.\.venv\Scripts\pythonw.exe .\androidcontrol.pyw
```

## Análisis de estado

Abre **Información del dispositivo** y pulsa **Analizar estado** cuando aparezca
junto al botón de debloat. Se conserva la detección Xiaomi/POCO existente.
El informe consulta batería, temperatura, RAM disponible, almacenamiento y los
valores actuales de las escalas de animación, mantener despierto al cargar y
no mantener actividades. **Analizar de nuevo** actualiza las lecturas.

Este diagnóstico es exclusivamente de lectura: no aplica ni restaura ajustes,
no crea puntos de restauración y no modifica swap, zRAM, extensión de memoria,
servicios, aplicaciones ni datos. Las lecturas que Android no permita consultar
se indican como no disponibles. El debloat y sus puntos de restauración siguen
siendo una función independiente y opcional, sin cambios.

No se ofrece una optimización general porque reducir animaciones solo acorta
esperas visuales y cambiar preferencias no garantiza más rendimiento. Tener
poca RAM libre tampoco justifica vaciarla: Android conserva aplicaciones en
memoria para reutilizarlas. Referencias oficiales:

- [Android Settings.Global](https://developer.android.com/reference/android/provider/Settings.Global).
- [Opciones de desarrollador](https://developer.android.com/studio/debug/dev-options).
- [Gestión de memoria de Android](https://developer.android.com/topic/performance/memory-management).

Todo el código de la aplicación, incluido el diagnóstico, está integrado en
`androidcontrol.pyw`; no necesita módulos locales ni archivos de pruebas auxiliares.

## Requisitos e instalación

### Windows (ejecutar la aplicación)

Necesitas Windows 10/11, Python 3.10 o posterior con Tcl/Tk, ADB, scrcpy y un
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

Google Chrome es opcional para el resto de la aplicación, pero necesario para
usar el botón de Google Cast. Puedes instalarlo desde
[google.com/chrome](https://www.google.com/chrome/).

Descarga o clona el repositorio y ejecuta `androidcontrol.pyw` con doble clic.
También puedes iniciarlo desde PowerShell:

```powershell
pyw .\androidcontrol.pyw
```

Para ver los mensajes de error en una terminal, utiliza:

```powershell
py .\androidcontrol.pyw
```

### Linux

En Debian o Ubuntu, instala Python, Tkinter, ADB y scrcpy desde la terminal:

```bash
sudo apt update && sudo apt install python3 python3-tk adb scrcpy
```

La aplicación necesita Python **3.10 o posterior**. Comprueba la versión con
`python3 --version`; si la distribución instala una versión anterior, instala
Python 3.10+ desde los repositorios oficiales de esa distribución antes de
continuar. En otras distribuciones, instala `python3` (3.10+), Tkinter, `adb` y
`scrcpy` mediante el gestor de paquetes correspondiente. Consulta las instrucciones oficiales de
[instalación de scrcpy en Linux](https://github.com/Genymobile/scrcpy/blob/master/doc/linux.md).
Los paquetes de la distribución pueden ofrecer una versión anterior; la misma
guía incluye opciones oficiales para obtener una versión más reciente.

Descarga o clona el repositorio y, desde su carpeta, ejecuta:

```bash
python3 androidcontrol.pyw
```

No hace falta instalar paquetes con `pip`. En algunas distribuciones puede ser
necesario configurar permisos USB/udev para que tu usuario pueda acceder al
teléfono; sigue las instrucciones de Android o de tu distribución y vuelve a
conectar el dispositivo después de cambiar permisos.

Para la opción Miracast, instala también **GNOME Network Displays** desde los
repositorios de tu distribución si está disponible. Es opcional y requiere un
escritorio/controlador Wi-Fi compatible con Miracast.

Para Google Cast, instala Google Chrome para Linux desde
[google.com/chrome](https://www.google.com/chrome/). Algunos paquetes de
Chromium no incluyen el soporte Google Cast; por eso la aplicación busca
Google Chrome para esa opción.

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

Python debe informar la versión 3.10 o posterior. Si un comando no se reconoce,
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

### Castear scrcpy a una TV

En **Control & Espejo**, pulsa **Castear pantalla del PC a una TV**. Se abrirá
un diálogo centrado sobre la ventana principal; elige ahí el protocolo que
corresponda a tu receptor:

- **Google Cast (Chromecast / Google TV):** la aplicación abre Google Chrome.
  Desde el menú del navegador, selecciona **Transmitir/Cast**, elige la fuente
  **Transmitir pantalla** y selecciona la TV.
- **Miracast:** en Windows se abre el selector de pantalla inalámbrica
  (**Win+K**). En Linux se inicia **GNOME Network Displays**, si está instalado.

Esta función transmite el **escritorio completo del PC**, no únicamente la
ventana de scrcpy. Deja scrcpy visible en el escritorio o monitor que compartas.
La selección y conexión a la TV se confirman en Chrome o en el panel del
sistema, no dentro de AndroidControl. El audio recibido por la TV depende del
protocolo, navegador y sistema operativo; comprueba que el sonido de scrcpy se
está reproduciendo y compartiendo desde el PC.

Chromecast/Google TV necesita que el navegador tenga disponible Google Cast;
en Linux, la compatibilidad de Cast depende de la distribución y del paquete de
Chrome/Chromium. Miracast requiere compatibilidad tanto del PC y su adaptador
inalámbrico como del televisor/receptor. Algunos dispositivos vendidos como
AnyCast funcionan como Miracast, mientras que otros ofrecen AirPlay o DLNA, que
no son intercambiables; AndroidControl no garantiza compatibilidad con todos
ellos. Mantén el PC y la TV en la red o modo inalámbrico requerido por el
receptor (Google Cast suele requerir la misma red local; Miracast suele usar
Wi-Fi Direct). Al compartir el escritorio, otras ventanas visibles también
podrían aparecer en la TV.

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
- **La aplicación no inicia:** confirma que estás usando Python 3.10 o posterior
  con Tkinter habilitado (`python3-tk` en Debian/Ubuntu).
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
