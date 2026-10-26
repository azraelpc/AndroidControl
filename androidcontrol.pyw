import sys
import os
import subprocess
import threading
import time
import ctypes
import json
import shutil

# --- FLAGS DE CREACIÓN PARA EVITAR CONSOLAS DE CMD EN WINDOWS ---
CREATE_NO_WINDOW = 0x08000000 if sys.platform == "win32" else 0
IS_WINDOWS = sys.platform == "win32"
PROCESS_CREATION_OPTIONS = {"creationflags": CREATE_NO_WINDOW} if IS_WINDOWS else {}

# --- RESOLUCIÓN DE RUTAS PARA AUTORUN / STARTUP ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "androidcontrol_config.json")

os.chdir(BASE_DIR)

DEFAULT_CONFIG = {
    "ip_port": "192.168.1.XX:5555",
    "device_pin": "",
    "stay_awake": True,
    "turn_screen_off": True,
    "auto_reconnect": True,
    "last_pc_pull_dir": os.path.expanduser("~/Downloads")
}

# Lista de Bloatware Seguro para Xiaomi / POCO (HyperOS / MIUI)
SAFE_POCO_BLOATWARE = [
    ("com.miui.analytics", "Xiaomi Analytics (Rastreo de analítica)"),
    ("com.miui.msa.global", "MIUI System Ads (Servicio de anuncios)"),
    ("com.mi.health", "Mi Health (Salud / Podómetro)"),
    ("com.miui.player", "Mi Music (Reproductor nativo con anuncios)"),
    ("com.miui.videoplayer", "Mi Video (Reproductor de vídeo con anuncios)"),
    ("com.miui.compass", "Brújula MIUI"),
    ("com.miui.bugreport", "Mi Bug Report (Envío de reportes de error)"),
    ("com.miui.miservice", "Servicios de soporte Xiaomi"),
    ("com.miui.hybrid", "Quick Apps / Aplicaciones Híbridas"),
    ("com.miui.hybrid.accessory", "Accesorios Quick Apps"),
    ("com.miui.carousel", "Carrusel de Fondos de Pantalla / Glance"),
    ("com.mi.globalbrowser", "Mi Browser (Navegador predeterminado)"),
    ("com.miui.cleanmaster", "Cleaner / Limpiador (Cheetah Mobile integration)"),
    ("com.miui.cloudservice", "Mi Cloud Sync (Sincronización de nube Xiaomi)"),
    ("com.miui.cloudbackup", "Mi Cloud Backup"),
    ("com.miui.cloudservice.sysbase", "Base de Servicios Mi Cloud"),
    ("com.miui.micloudsync", "Sincronizador Mi Cloud"),
    ("com.xiaomi.glgm", "Games App Store / Tienda de Juegos Xiaomi"),
    ("com.xiaomi.mipicks", "GetApps (Tienda de aplicaciones Xiaomi)"),
    ("com.xiaomi.payment", "Mi Pay (Pasarela de pago Xiaomi)"),
    ("com.facebook.system", "Facebook System Service"),
    ("com.facebook.appmanager", "Facebook App Manager"),
    ("com.facebook.services", "Facebook Services"),
    ("com.google.android.videos", "Google TV / películas"),
    ("com.google.android.music", "YouTube Music System Stub"),
    ("com.google.android.apps.subscriptions.redium", "Google One")
]

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                config = DEFAULT_CONFIG.copy()
                config.update(data)
                return config
        except Exception:
            pass
    return DEFAULT_CONFIG.copy()

def save_config(config_dict):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config_dict, f, indent=4, ensure_ascii=False)
    except Exception:
        pass

# --- INSTANCIA ÚNICA (SINGLE INSTANCE LOCK USING WINDOWS MUTEX) ---
if IS_WINDOWS:
    MUTEX_NAME = "Local\\AndroidControlCenterSingleInstanceMutex"
    kernel32 = ctypes.windll.kernel32
    mutex_handle = kernel32.CreateMutexW(None, True, MUTEX_NAME)
    last_error = kernel32.GetLastError()
    ERROR_ALREADY_EXISTS = 183

    if last_error == ERROR_ALREADY_EXISTS:
        try:
            ctypes.windll.user32.MessageBoxW(
                0,
                "El programa 'Android Control Center' ya se encuentra en ejecución.\nRevisa la bandeja del sistema (al lado del reloj).",
                "Instancia única",
                0x40 | 0x1
            )
        except Exception:
            pass
        sys.exit(0)

# --- COMPROBACIÓN PREVIA DE DEPENDENCIAS DE PYTHON ---
REQUIRED_MODULES = {
    "tkinter": "Interfaz gráfica (en Linux suele instalarse como paquete python3-tk).",
    "subprocess": "Gestión de comandos ADB y scrcpy.",
    "ctypes": "Integración con el sistema operativo."
}

missing_modules = []
for mod in REQUIRED_MODULES:
    try:
        __import__(mod)
    except ImportError:
        missing_modules.append(mod)

if missing_modules:
    error_msg = (
        "¡Atención!\n\n"
        "Faltan los siguientes módulos esenciales de Python:\n"
        f"• {', '.join(missing_modules)}\n\n"
        "Instala los módulos indicados con el instalador de Python o el gestor "
        "de paquetes de tu distribución."
    )
    if IS_WINDOWS:
        ctypes.windll.user32.MessageBoxW(0, error_msg, "Error de dependencias", 0x10)
    else:
        print(error_msg)
    sys.exit(1)

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog

# --- Windows Win32 Constants & Structures ---
NIM_ADD = 0x00000000
NIM_MODIFY = 0x00000001
NIM_DELETE = 0x00000002
NIF_MESSAGE = 0x0001
NIF_ICON = 0x0002
NIF_TIP = 0x0004
NIF_INFO = 0x0010
WM_USER = 0x0400
WM_TRAYICON = WM_USER + 0x100
WM_RBUTTONUP = 0x0205
WM_LBUTTONDBLCLK = 0x0203
GWLP_WNDPROC = -4
ID_M_RESTORE = 1001
ID_M_EXIT = 1002

WNDPROC_TYPE = (
    ctypes.WINFUNCTYPE(ctypes.c_int64, ctypes.c_void_p, ctypes.c_uint, ctypes.c_void_p, ctypes.c_void_p)
    if IS_WINDOWS else None
)

class POINT(ctypes.Structure):
    _fields_ = [
        ("x", ctypes.c_long),
        ("y", ctypes.c_long)
    ]

class NOTIFYICONDATAW(ctypes.Structure):
    _fields_ = [
        ("cbSize", ctypes.c_ulong),
        ("hWnd", ctypes.c_void_p),
        ("uID", ctypes.c_uint),
        ("uFlags", ctypes.c_uint),
        ("uCallbackMessage", ctypes.c_uint),
        ("hIcon", ctypes.c_void_p),
        ("szTip", ctypes.c_wchar * 128),
        ("dwState", ctypes.c_uint),
        ("dwStateMask", ctypes.c_uint),
        ("szInfo", ctypes.c_wchar * 256),
        ("uTimeout", ctypes.c_uint),
        ("szInfoTitle", ctypes.c_wchar * 64),
        ("dwInfoFlags", ctypes.c_uint),
        ("guidItem", ctypes.c_ubyte * 16),
        ("hBalloonIcon", ctypes.c_void_p)
    ]

if IS_WINDOWS:
    SetWindowLongPtrW = getattr(ctypes.windll.user32, 'SetWindowLongPtrW', ctypes.windll.user32.SetWindowLongW)
    SetWindowLongPtrW.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p]
    SetWindowLongPtrW.restype = ctypes.c_void_p

    CallWindowProcW = ctypes.windll.user32.CallWindowProcW
    CallWindowProcW.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint, ctypes.c_void_p, ctypes.c_void_p]
    CallWindowProcW.restype = ctypes.c_int64

class WindowsTrayIcon:
    def __init__(self, app_instance, title="Android Control Center"):
        self.app = app_instance
        self.title = title
        self.hwnd = self.app.root.winfo_id()
        self.nid = None
        self.old_wndproc = None
        self.new_wndproc_cb = None
        self._hook_tkinter_hwnd()

    def _hook_tkinter_hwnd(self):
        self.new_wndproc_cb = WNDPROC_TYPE(self._wnd_proc)
        self.old_wndproc = SetWindowLongPtrW(self.hwnd, GWLP_WNDPROC, self.new_wndproc_cb)

    def add_icon(self):
        hicon = ctypes.windll.user32.LoadIconW(None, ctypes.c_wchar_p(32516)) # IDI_INFORMATION
        if not hicon:
            hicon = ctypes.windll.user32.LoadIconW(None, ctypes.c_wchar_p(32512))
            
        nid = NOTIFYICONDATAW()
        nid.cbSize = ctypes.sizeof(NOTIFYICONDATAW)
        nid.hWnd = self.hwnd
        nid.uID = 1
        nid.uFlags = NIF_MESSAGE | NIF_ICON | NIF_TIP
        nid.uCallbackMessage = WM_TRAYICON
        nid.hIcon = hicon
        nid.szTip = self.title
        ctypes.windll.shell32.Shell_NotifyIconW(NIM_ADD, ctypes.byref(nid))
        self.nid = nid

    def remove_icon(self):
        if self.nid:
            ctypes.windll.shell32.Shell_NotifyIconW(NIM_DELETE, ctypes.byref(self.nid))
            self.nid = None

    def show_balloon(self, title, message):
        if self.nid:
            self.nid.uFlags = NIF_MESSAGE | NIF_ICON | NIF_TIP | NIF_INFO
            self.nid.szInfoTitle = title
            self.nid.szInfo = message
            self.nid.dwInfoFlags = 0x00000001
            ctypes.windll.shell32.Shell_NotifyIconW(NIM_MODIFY, ctypes.byref(self.nid))
            self.nid.uFlags = NIF_MESSAGE | NIF_ICON | NIF_TIP

    def _wnd_proc(self, hwnd, msg, wparam, lparam):
        if msg == WM_TRAYICON:
            if lparam == WM_RBUTTONUP:
                hmenu = ctypes.windll.user32.CreatePopupMenu()
                ctypes.windll.user32.AppendMenuW(hmenu, 0, ID_M_RESTORE, "Restaurar Ventana")
                ctypes.windll.user32.AppendMenuW(hmenu, 0, ID_M_EXIT, "Salir de la Aplicación")
                
                pt = POINT()
                ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
                ctypes.windll.user32.SetForegroundWindow(hwnd)
                cmd = ctypes.windll.user32.TrackPopupMenu(
                    hmenu, 0x0002 | 0x0100, pt.x, pt.y, 0, hwnd, None
                )
                ctypes.windll.user32.DestroyMenu(hmenu)
                
                if cmd == ID_M_RESTORE:
                    self.app.restore_window()
                elif cmd == ID_M_EXIT:
                    self.app.real_exit()
            elif lparam == WM_LBUTTONDBLCLK:
                self.app.restore_window()
            return 0

        return CallWindowProcW(self.old_wndproc, hwnd, msg, wparam, lparam)


class ADBScrcpyApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Android Control Center Ultimate")
        
        self.width = 540
        self.height = 840
        self.root.minsize(480, 700)
        
        self.config = load_config()
        self.scrcpy_process = None
        self.logcat_process = None
        self.is_monitoring_notifications = False
        
        self.is_auto_reconnect_enabled = self.config.get("auto_reconnect", True)
        self.current_connected_device = None
        self._is_closing = False
        self._check_in_progress = False

        self.root.protocol("WM_DELETE_WINDOW", self.hide_to_tray)

        self.create_widgets()
        self.center_window()
        self.root.update()

        self.tray = None
        if IS_WINDOWS:
            self.tray = WindowsTrayIcon(self)
            self.tray.add_icon()

        self.verify_external_tools()

        self.root.after(2000, self.periodic_check)
        self.check_adb_connection()

    def center_window(self):
        self.root.update_idletasks()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        x = max(0, (screen_width // 2) - (self.width // 2))
        y = max(0, (screen_height // 2) - (self.height // 2))
        
        self.root.geometry(f"{self.width}x{self.height}+{x}+{y}")

    def verify_external_tools(self):
        missing = []
        if not shutil.which("adb"):
            missing.append("• ADB (Android Debug Bridge)")
        if not shutil.which("scrcpy"):
            missing.append("• scrcpy (Screen Mirroring tool)")

        if missing:
            missing_tools = "\n".join(missing)
            msg = (
                "⚠️ Advertencia de Herramientas Externas:\n\n"
                "No se han encontrado en el PATH del sistema:\n"
                f"{missing_tools}\n\n"
                "Para un funcionamiento completo, asegúrate de tener estas herramientas "
                "instaladas e incluidas en las variables de entorno (PATH)."
            )
            messagebox.showwarning("Herramientas faltantes", msg)
            self.log("ADVERTENCIA: Faltan herramientas en PATH: " + ", ".join(missing))

    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        title_label = ttk.Label(main_frame, text="Android Control Center Ultimate", font=("Segoe UI", 14, "bold"))
        title_label.pack(anchor="w", pady=(0, 4))

        status_frame = ttk.LabelFrame(main_frame, text=" Conexión y Estado ", padding=6)
        status_frame.pack(fill=tk.X, pady=(0, 6))

        self.status_lbl = ttk.Label(status_frame, text="Comprobando conexión ADB...", font=("Segoe UI", 9))
        self.status_lbl.pack(side=tk.LEFT, fill=tk.X, expand=True)

        refresh_btn = ttk.Button(status_frame, text="🔄 Recargar", width=10, command=self.check_adb_connection)
        refresh_btn.pack(side=tk.RIGHT)

        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 6))

        # --- TAB 1: CONTROL Y ESPEJO ---
        tab_control = ttk.Frame(notebook, padding=8)
        notebook.add(tab_control, text="🎮 Control & Espejo")

        wifi_frame = ttk.LabelFrame(tab_control, text=" Depuración Inalámbrica y PIN ", padding=6)
        wifi_frame.pack(fill=tk.X, pady=(0, 6))

        wifi_top = ttk.Frame(wifi_frame)
        wifi_top.pack(fill=tk.X, pady=2)
        ttk.Label(wifi_top, text="IP:Puerto:", font=("Segoe UI", 9), width=10).pack(side=tk.LEFT)
        self.ip_entry = ttk.Entry(wifi_top, font=("Consolas", 9))
        self.ip_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4))
        self.ip_entry.insert(0, self.config.get("ip_port", "192.168.1.XX:5555"))
        self.ip_entry.bind("<KeyRelease>", lambda e: self.save_current_settings())
        ttk.Button(wifi_top, text="Conectar", width=9, command=self.connect_wireless).pack(side=tk.RIGHT)

        pin_row = ttk.Frame(wifi_frame)
        pin_row.pack(fill=tk.X, pady=2)
        ttk.Label(pin_row, text="PIN/Pass:", font=("Segoe UI", 9), width=10).pack(side=tk.LEFT)
        self.pin_entry = ttk.Entry(pin_row, font=("Consolas", 9), show="*")
        self.pin_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4))
        self.pin_entry.insert(0, self.config.get("device_pin", ""))
        self.pin_entry.bind("<KeyRelease>", lambda e: self.save_current_settings())

        self.show_pin_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(pin_row, text="👁️", variable=self.show_pin_var, command=self.toggle_pin_visibility).pack(side=tk.RIGHT)

        wifi_btm = ttk.Frame(wifi_frame)
        wifi_btm.pack(fill=tk.X, pady=(4, 0))
        ttk.Button(wifi_btm, text="🔗 Modo TCP/IP (USB)", command=self.enable_tcpiip).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 2))
        ttk.Button(wifi_btm, text="🔑 Emparejar (Android 11+)", command=self.pair_wireless).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        ttk.Button(wifi_btm, text="🔓 Auto-Desbloquear PIN", command=self.unlock_device_with_pin).pack(side=tk.RIGHT, expand=True, fill=tk.X, padx=(2, 0))

        mirror_frame = ttk.LabelFrame(tab_control, text=" Pantalla y Espejo (scrcpy) ", padding=6)
        mirror_frame.pack(fill=tk.X, pady=(0, 6))

        btn_frame = ttk.Frame(mirror_frame)
        btn_frame.pack(fill=tk.X, pady=2)
        self.start_mirror_btn = ttk.Button(btn_frame, text="▶ Iniciar Control & Espejo", command=self.start_scrcpy)
        self.start_mirror_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 2))
        self.stop_mirror_btn = ttk.Button(btn_frame, text="⏹ Detener Espejo", command=self.stop_scrcpy, state=tk.DISABLED)
        self.stop_mirror_btn.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(2, 0))

        ttk.Button(mirror_frame, text="📺 Castear pantalla del PC a una TV", command=self.open_cast_dialog).pack(fill=tk.X, pady=(4, 2))

        opts_frame = ttk.Frame(mirror_frame)
        opts_frame.pack(fill=tk.X, pady=2)
        self.stay_awake_var = tk.BooleanVar(value=self.config.get("stay_awake", True))
        ttk.Checkbutton(opts_frame, text="Mantener móvil despierto en carga", variable=self.stay_awake_var, command=self.save_current_settings).pack(anchor="w")
        self.turn_screen_off_var = tk.BooleanVar(value=self.config.get("turn_screen_off", True))
        ttk.Checkbutton(opts_frame, text="Apagar pantalla física durante el espejo", variable=self.turn_screen_off_var, command=self.save_current_settings).pack(anchor="w")

        actions_frame = ttk.LabelFrame(tab_control, text=" Botones Físicos y Navegación ", padding=6)
        actions_frame.pack(fill=tk.X, pady=(0, 6))

        g1 = ttk.Frame(actions_frame)
        g1.pack(fill=tk.X, pady=2)
        ttk.Button(g1, text="🏠 Inicio", command=lambda: self.run_adb_cmd(["shell", "input", "keyevent", "3"])).grid(row=0, column=0, padx=2, pady=2, sticky="ew")
        ttk.Button(g1, text="🔙 Atrás", command=lambda: self.run_adb_cmd(["shell", "input", "keyevent", "4"])).grid(row=0, column=1, padx=2, pady=2, sticky="ew")
        ttk.Button(g1, text="🔲 Recientes", command=lambda: self.run_adb_cmd(["shell", "input", "keyevent", "187"])).grid(row=0, column=2, padx=2, pady=2, sticky="ew")
        ttk.Button(g1, text="⚡ Encender/Enc", command=lambda: self.run_adb_cmd(["shell", "input", "keyevent", "26"])).grid(row=0, column=3, padx=2, pady=2, sticky="ew")

        for i in range(4):
            g1.columnconfigure(i, weight=1)

        g2 = ttk.Frame(actions_frame)
        g2.pack(fill=tk.X, pady=2)
        ttk.Button(g2, text="🔊 Vol +", command=lambda: self.run_adb_cmd(["shell", "input", "keyevent", "24"])).grid(row=0, column=0, padx=2, pady=2, sticky="ew")
        ttk.Button(g2, text="🔉 Vol -", command=lambda: self.run_adb_cmd(["shell", "input", "keyevent", "25"])).grid(row=0, column=1, padx=2, pady=2, sticky="ew")
        ttk.Button(g2, text="🔇 Silencio", command=lambda: self.run_adb_cmd(["shell", "input", "keyevent", "164"])).grid(row=0, column=2, padx=2, pady=2, sticky="ew")
        ttk.Button(g2, text="⏯ Play/Pausa", command=lambda: self.run_adb_cmd(["shell", "input", "keyevent", "85"])).grid(row=0, column=3, padx=2, pady=2, sticky="ew")

        for i in range(4):
            g2.columnconfigure(i, weight=1)

        g3 = ttk.Frame(actions_frame)
        g3.pack(fill=tk.X, pady=2)
        ttk.Button(g3, text="📸 Captura Pantalla", command=self.take_screenshot).grid(row=0, column=0, padx=2, pady=2, sticky="ew")
        ttk.Button(g3, text="📋 Enviar Portapapeles", command=self.send_clipboard_to_android).grid(row=0, column=1, padx=2, pady=2, sticky="ew")
        ttk.Button(g3, text="📋 Obtener Portapapeles", command=self.get_clipboard_from_android).grid(row=0, column=2, padx=2, pady=2, sticky="ew")

        for i in range(3):
            g3.columnconfigure(i, weight=1)

        # BOTÓN SISTEMA / AIDA32 - INFORMACIÓN DEL MÓVIL
        info_frame = ttk.Frame(actions_frame)
        info_frame.pack(fill=tk.X, pady=(4, 2))
        ttk.Button(info_frame, text="ℹ️ Información del Móvil (Estilo AIDA32)", command=self.show_device_info_dialog).pack(fill=tk.X)

        # --- TAB 2: ARCHIVOS Y APKS ---
        tab_files = ttk.Frame(notebook, padding=8)
        notebook.add(tab_files, text="📁 Transferencia Archivos & APKs")

        send_frame = ttk.LabelFrame(tab_files, text=" 📤 Enviar Archivo o Instalar APK (PC ➔ Móvil) ", padding=6)
        send_frame.pack(fill=tk.X, pady=(0, 6))

        send_btn_row = ttk.Frame(send_frame)
        send_btn_row.pack(fill=tk.X, pady=2)
        ttk.Button(send_btn_row, text="📁 Seleccionar y Enviar Archivo (/sdcard/Download)", command=self.push_file_to_android).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 2))
        ttk.Button(send_btn_row, text="📦 Instalar APK de PC", command=self.install_apk_from_pc).pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(2, 0))

        pull_frame = ttk.LabelFrame(tab_files, text=" 📥 Descargar Archivos (Móvil ➔ PC) ", padding=6)
        pull_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 6))

        pull_top = ttk.Frame(pull_frame)
        pull_top.pack(fill=tk.X, pady=2)
        ttk.Label(pull_top, text="Ruta Android:", font=("Segoe UI", 9)).pack(side=tk.LEFT, padx=(0, 4))
        self.remote_path_entry = ttk.Entry(pull_top, font=("Consolas", 9))
        self.remote_path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4))
        self.remote_path_entry.insert(0, "/sdcard/Download")

        ttk.Button(pull_top, text="🔍 Listar", width=8, command=self.list_remote_files).pack(side=tk.RIGHT)

        list_sub = ttk.Frame(pull_frame)
        list_sub.pack(fill=tk.BOTH, expand=True, pady=4)

        self.file_listbox = tk.Listbox(list_sub, font=("Consolas", 8), bg="#1e1e1e", fg="#d4d4d4")
        self.file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        file_scroll = ttk.Scrollbar(list_sub, orient=tk.VERTICAL, command=self.file_listbox.yview)
        file_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.file_listbox.configure(yscrollcommand=file_scroll.set)

        ttk.Button(pull_frame, text="⬇️ Descargar Selección al PC", command=self.pull_selected_file).pack(fill=tk.X, pady=2)

        # --- TAB 3: NOTIFICACIONES Y LOGS ---
        tab_notif = ttk.Frame(notebook, padding=8)
        notebook.add(tab_notif, text="🔔 Notificaciones & Log")

        notif_sub = ttk.Frame(tab_notif)
        notif_sub.pack(fill=tk.X, pady=(0, 6))
        self.notif_btn = ttk.Button(notif_sub, text="🔔 Activar Puente de Notificaciones a Windows", command=self.toggle_notifications)
        self.notif_btn.pack(fill=tk.X)

        log_frame = ttk.LabelFrame(tab_notif, text=" Registro de Actividad ", padding=4)
        log_frame.pack(fill=tk.BOTH, expand=True)

        self.log_text = tk.Text(log_frame, height=10, wrap=tk.WORD, font=("Consolas", 8), bg="#1e1e1e", fg="#d4d4d4")
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.configure(yscrollcommand=scrollbar.set)

    def toggle_pin_visibility(self):
        if self.show_pin_var.get():
            self.pin_entry.config(show="")
        else:
            self.pin_entry.config(show="*")

    def save_current_settings(self):
        self.config["ip_port"] = self.ip_entry.get().strip()
        self.config["device_pin"] = self.pin_entry.get().strip()
        self.config["stay_awake"] = self.stay_awake_var.get()
        self.config["turn_screen_off"] = self.turn_screen_off_var.get()
        save_config(self.config)

    def unlock_device_with_pin(self):
        pin = self.pin_entry.get().strip()
        def task():
            try:
                self.log("Iniciando secuencia de desbloqueo...")
                self._safe_adb_run(["shell", "input", "keyevent", "224"], timeout=2)
                time.sleep(0.3)
                
                self._safe_adb_run(["shell", "input", "swipe", "300", "1200", "300", "200", "150"], timeout=2)
                time.sleep(0.4)
                
                if pin:
                    self._safe_adb_run(["shell", "input", "text", pin], timeout=2)
                    time.sleep(0.2)
                    self._safe_adb_run(["shell", "input", "keyevent", "66"], timeout=2)
                    self._safe_adb_run(["shell", "input", "keyevent", "160"], timeout=2)
                    self.log("PIN enviado correctamente.")
                else:
                    self.log("Pantalla encendida y deslizada (sin PIN guardado).")
            except Exception as e:
                self.log(f"Error en auto-desbloqueo: {e}")

        threading.Thread(target=task, daemon=True).start()

    def _safe_adb_run(self, args, timeout=3):
        """Ejecuta un comando ADB de forma segura apuntando al dispositivo activo."""
        cmd = ["adb"]
        if self.current_connected_device:
            cmd.extend(["-s", self.current_connected_device])
        cmd.extend(args)
        
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, **PROCESS_CREATION_OPTIONS)
            return res.stdout.strip()
        except Exception:
            return ""

    # --- RECOPILADOR SAFE Y GARANTIZADO DE INFORMACIÓN AIDA32 DEL MÓVIL ---
    def show_device_info_dialog(self):
        if not self.current_connected_device:
            messagebox.showwarning("Sin Dispositivo", "Conecta un dispositivo Android por USB o Wi-Fi para obtener la información.")
            return

        device_target = self.current_connected_device

        info_win = tk.Toplevel(self.root)
        info_win.title(f"Información del Sistema (AIDA32) - {device_target}")
        info_win.geometry("640x680")
        info_win.transient(self.root)

        # Centrar ventana secundaria
        info_win.update_idletasks()
        x = max(0, self.root.winfo_x() + (self.root.winfo_width() // 2) - (640 // 2))
        y = max(0, self.root.winfo_y() + (self.root.winfo_height() // 2) - (680 // 2))
        info_win.geometry(f"640x680+{x}+{y}")

        status_bar = ttk.Label(info_win, text="⏳ Obteniendo especificaciones del dispositivo...", font=("Segoe UI", 10, "bold"), padding=8)
        status_bar.pack(side=tk.TOP, fill=tk.X)

        content_frame = ttk.Frame(info_win, padding=6)
        content_frame.pack(fill=tk.BOTH, expand=True)

        tree = ttk.Treeview(content_frame, columns=("Valor",), show="tree headings")
        tree.heading("#0", text="Categoría / Propiedad")
        tree.heading("Valor", text="Valor / Detalle")
        tree.column("#0", width=300, anchor="w")
        tree.column("Valor", width=300, anchor="w")

        scrolly = ttk.Scrollbar(content_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrolly.set)

        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrolly.pack(side=tk.RIGHT, fill=tk.Y)

        btn_box = ttk.Frame(info_win, padding=6)
        btn_box.pack(fill=tk.X, side=tk.BOTTOM)
        
        # Botones de la barra inferior
        copy_btn = ttk.Button(btn_box, text="💾 Copiar Reporte al Portapapeles", state=tk.DISABLED)
        copy_btn.pack(side=tk.RIGHT, padx=4)

        debloat_btn = ttk.Button(btn_box, text="⚡ Advanced: Debloat", command=lambda: self.open_debloat_poco_dialog(info_win))

        def fetch_and_populate():
            info_data = {}

            def get_prop(name, default="Desconocido"):
                v = self._safe_adb_run(["shell", "getprop", name], timeout=2)
                return v if v else default

            try:
                brand = get_prop("ro.product.brand")
                manufacturer = get_prop("ro.product.manufacturer")
                model = get_prop("ro.product.model")
                device_name = get_prop("ro.product.device")

                # 1. Dispositivo y Sistema
                info_data["📱 Dispositivo y Sistema"] = [
                    ("Marca", brand),
                    ("Fabricante", manufacturer),
                    ("Modelo", model),
                    ("Nombre Comercial / Dispositivo", device_name),
                    ("Versión Android", get_prop("ro.build.version.release")),
                    ("Nivel de API (SDK)", get_prop("ro.build.version.sdk")),
                    ("Parche de Seguridad", get_prop("ro.build.version.security_patch")),
                    ("Número de Compilación (Build)", get_prop("ro.build.display.id")),
                    ("Arquitectura (ABI)", get_prop("ro.product.cpu.abi")),
                    ("Bootloader", get_prop("ro.bootloader")),
                    ("Número de Serie", get_prop("ro.serialno", get_prop("ro.boot.serialno", "N/A")))
                ]

                # 2. CPU / SoC
                soc = get_prop("ro.board.platform", get_prop("ro.hardware", "Desconocido"))
                cpu_out = self._safe_adb_run(["shell", "cat", "/proc/cpuinfo"], timeout=2)
                processors = cpu_out.count("processor") if cpu_out else 0

                info_data["⚙️ Procesador (SoC)"] = [
                    ("Plataforma / Hardware", soc),
                    ("Arquitectura CPU", get_prop("ro.product.cpu.abi")),
                    ("Núcleos detectados", str(processors) if processors > 0 else "Desconocido"),
                    ("Gobernador CPU", get_prop("sys.io.scheduler", "Estándar"))
                ]

                # 3. Batería
                bat_out = self._safe_adb_run(["shell", "dumpsys", "battery"], timeout=2)
                bat_dict = {}
                if bat_out:
                    for line in bat_out.splitlines():
                        if ":" in line:
                            k, v = line.split(":", 1)
                            bat_dict[k.strip()] = v.strip()

                tech = bat_dict.get("technology", "Li-ion")
                temp_raw = bat_dict.get("temperature")
                temp = f"{float(temp_raw)/10.0} °C" if temp_raw and temp_raw.isdigit() else "N/A"
                volt_raw = bat_dict.get("voltage")
                volt = f"{float(volt_raw)/1000.0} V" if volt_raw and volt_raw.isdigit() else "N/A"

                info_data["🔋 Batería y Salud"] = [
                    ("Nivel de Carga", f"{bat_dict.get('level', 'N/A')}%"),
                    ("Estado Carga", "Cargando" if bat_dict.get("powered") == "true" or bat_dict.get("AC powered") == "true" or bat_dict.get("USB powered") == "true" else "En descarga"),
                    ("Salud Batería", "Buena (Good)" if bat_dict.get("health") == "2" else f"Estado {bat_dict.get('health', 'OK')}"),
                    ("Temperatura", temp),
                    ("Voltaje", volt),
                    ("Tecnología", tech)
                ]

                # 4. Memoria y Almacenamiento
                mem_out = self._safe_adb_run(["shell", "cat", "/proc/meminfo"], timeout=2)
                mem_total, mem_free = "N/A", "N/A"
                if mem_out:
                    for line in mem_out.splitlines():
                        if "MemTotal" in line:
                            mem_total = line.split(":")[1].strip()
                        elif "MemAvailable" in line:
                            mem_free = line.split(":")[1].strip()

                df_out = self._safe_adb_run(["shell", "df", "-h", "/sdcard"], timeout=2)
                df_lines = df_out.strip().splitlines() if df_out else []
                storage_str = df_lines[-1] if len(df_lines) > 1 else "N/A"

                info_data["💾 Memoria y Almacenamiento"] = [
                    ("RAM Total", mem_total),
                    ("RAM Disponible", mem_free),
                    ("Espacio /sdcard (Uso/Total)", storage_str)
                ]

                # 5. Pantalla
                wm_size = self._safe_adb_run(["shell", "wm", "size"], timeout=2)
                wm_density = self._safe_adb_run(["shell", "wm", "density"], timeout=2)

                info_data["🖥️ Pantalla & Gráficos"] = [
                    ("Resolución Física", wm_size.replace("Physical size:", "").strip() if wm_size else "N/A"),
                    ("Densidad Píxeles (DPI)", wm_density.replace("Physical density:", "").strip() if wm_density else "N/A"),
                    ("Renderizador GPU", get_prop("ro.hardware.egl", "Desconocido"))
                ]

                # Comprobar si coincide con Marca: POCO, Fabricante: Xiaomi, Dispositivo: duchamp
                is_poco_duchamp = (
                    "POCO" in brand.upper() or 
                    "XIAOMI" in manufacturer.upper() or 
                    "DUCHAMP" in device_name.lower() or
                    "DUCHAMP" in model.lower()
                )

                def update_tree():
                    for cat, items in info_data.items():
                        node = tree.insert("", tk.END, text=cat, values=("",), open=True)
                        for k, v in items:
                            tree.insert(node, tk.END, text=f"  {k}", values=(v,))
                    
                    status_bar.config(text="✅ Especificaciones cargadas con éxito.", foreground="green")
                    copy_btn.config(state=tk.NORMAL, command=lambda: self._copy_info_report(info_data))

                    if is_poco_duchamp:
                        debloat_btn.pack(side=tk.LEFT, padx=4)

                info_win.after(0, update_tree)

            except Exception as e:
                info_win.after(0, lambda: status_bar.config(text=f"⚠️ Error cargando datos: {e}", foreground="red"))

        threading.Thread(target=fetch_and_populate, daemon=True).start()

    def _copy_info_report(self, info_data):
        lines = ["==========================================", "   ANDROID CONTROL CENTER - INFORME AIDA32", "==========================================\n"]
        for cat, items in info_data.items():
            lines.append(f"[{cat}]")
            for k, v in items:
                lines.append(f"  • {k}: {v}")
            lines.append("")
        report_text = "\n".join(lines)
        self.root.clipboard_clear()
        self.root.clipboard_append(report_text)
        messagebox.showinfo("Reporte Copiado", "El informe de especificaciones se ha copiado al portapapeles.")

    # --- DEBLOAT Y RESTAURACIÓN SAFE PARA POCO X6 PRO (duchamp) ---
    def open_debloat_poco_dialog(self, parent_win):
        try:
            parent_win.destroy()
        except Exception:
            pass

        debloat_win = tk.Toplevel(self.root)
        debloat_win.title("Debloat Poco X6 Pro (duchamp)")
        debloat_win.geometry("620x680")
        debloat_win.transient(self.root)

        debloat_win.update_idletasks()
        x = max(0, self.root.winfo_x() + (self.root.winfo_width() // 2) - (620 // 2))
        y = max(0, self.root.winfo_y() + (self.root.winfo_height() // 2) - (680 // 2))
        debloat_win.geometry(f"620x680+{x}+{y}")

        title_lbl = ttk.Label(debloat_win, text="🧹 Optimización & Debloat Seguro (POCO X6 Pro)", font=("Segoe UI", 11, "bold"), padding=10)
        title_lbl.pack(anchor="w")

        info_lbl = ttk.Label(
            debloat_win, 
            text="Selecciona las aplicaciones que deseas desinstalar del sistema.\nAntes de realizar cualquier cambio, se creará un Punto de Restauración local automáticamente.",
            font=("Segoe UI", 9),
            padding=(10, 0, 10, 10)
        )
        info_lbl.pack(anchor="w")

        # Contenedor scrollable con Checkbuttons para desmarcar libremente
        list_frame = ttk.LabelFrame(debloat_win, text=" Aplicaciones Básicas / Bloatware Detectado ", padding=6)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        canvas = tk.Canvas(list_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        checkbox_vars = {}

        # Listar paquetes detectados en el dispositivo o predefinidos
        installed_pkgs = self._safe_adb_run(["shell", "pm", "list", "packages"], timeout=3)

        for pkg_name, desc in SAFE_POCO_BLOATWARE:
            is_installed = (f"package:{pkg_name}" in installed_pkgs) if installed_pkgs else True
            var = tk.BooleanVar(value=is_installed)
            checkbox_vars[pkg_name] = var
            
            chk_state_str = "" if is_installed else " (No detectada / ya retirada)"
            chk = ttk.Checkbutton(
                scrollable_frame, 
                text=f"{pkg_name}\n   └ {desc}{chk_state_str}", 
                variable=var,
                state=tk.NORMAL if is_installed else tk.DISABLED
            )
            chk.pack(anchor="w", pady=4, padx=5)

        # Botones inferiores
        btn_box = ttk.Frame(debloat_win, padding=10)
        btn_box.pack(fill=tk.X, side=tk.BOTTOM)

        def execute_debloat():
            selected_pkgs = [pkg for pkg, var in checkbox_vars.items() if var.get()]
            if not selected_pkgs:
                messagebox.showwarning("Sin selección", "No has seleccionado ninguna aplicación para quitar.")
                return

            if not messagebox.askyesno("Confirmar Debloat", f"¿Estás seguro de desinstalar las {len(selected_pkgs)} aplicaciones seleccionadas?\n\nSe creará automáticamente una carpeta de Punto de Restauración antes de proceder."):
                return

            def task():
                try:
                    timestamp = time.strftime('%Y%m%d_%H%M%S')
                    restore_dir = os.path.join(BASE_DIR, f"Punto_de_Restauracion_{timestamp}")
                    os.makedirs(restore_dir, exist_ok=True)

                    self.log(f"Creando Punto de Restauración en: {restore_dir}...")

                    # Guardar manifest JSON del punto de restauración
                    restore_manifest = {
                        "timestamp": timestamp,
                        "device": self.current_connected_device,
                        "removed_packages": selected_pkgs,
                        "paths": {}
                    }

                    for pkg in selected_pkgs:
                        pkg_path = self._safe_adb_run(["shell", "pm", "path", pkg], timeout=2)
                        if pkg_path:
                            clean_path = pkg_path.replace("package:", "").strip()
                            restore_manifest["paths"][pkg] = clean_path

                    manifest_path = os.path.join(restore_dir, "restore_info.json")
                    with open(manifest_path, "w", encoding="utf-8") as f:
                        json.dump(restore_manifest, f, indent=4, ensure_ascii=False)

                    self.log("✅ Punto de Restauración creado con éxito.")

                    # Desinstalar mediante ADB (pm uninstall -k --user 0)
                    success_count = 0
                    for pkg in selected_pkgs:
                        self.log(f"Desinstalando {pkg}...")
                        res = self._safe_adb_run(["shell", "pm", "uninstall", "-k", "--user", "0", pkg], timeout=4)
                        if "Success" in res:
                            success_count += 1
                            self.log(f"  └ ✅ {pkg} eliminado.")
                        else:
                            self.log(f"  └ ⚠️ {pkg}: {res}")

                    messagebox.showinfo(
                        "Debloat Finalizado", 
                        f"Proceso completado.\n\n"
                        f"• Eliminadas: {success_count}/{len(selected_pkgs)} aplicaciones.\n"
                        f"• Punto de Restauración guardado en:\n{restore_dir}"
                    )
                except Exception as e:
                    self.log(f"Error en debloat: {e}")
                    messagebox.showerror("Error", f"Ocurrió un error durante el debloat: {e}")

            threading.Thread(target=task, daemon=True).start()

        def execute_restore():
            restore_dir = filedialog.askdirectory(title="Seleccionar carpeta de Punto de Restauración", initialdir=BASE_DIR)
            if not restore_dir:
                return

            manifest_path = os.path.join(restore_dir, "restore_info.json")
            if not os.path.exists(manifest_path):
                messagebox.showerror("Error de Punto de Restauración", "La carpeta seleccionada no contiene un archivo 'restore_info.json' válido.")
                return

            def task():
                try:
                    with open(manifest_path, "r", encoding="utf-8") as f:
                        data = json.load(f)

                    pkgs_to_restore = data.get("removed_packages", [])
                    self.log(f"Iniciando restauración de {len(pkgs_to_restore)} aplicaciones desde {restore_dir}...")

                    restored_count = 0
                    for pkg in pkgs_to_restore:
                        self.log(f"Reinstalando/Habilitando {pkg}...")
                        res = self._safe_adb_run(["shell", "cmd", "package", "install-existing", pkg], timeout=4)
                        if "installed for user" in res.lower() or "success" in res.lower():
                            restored_count += 1
                            self.log(f"  └ ✅ {pkg} restaurado.")
                        else:
                            self.log(f"  └ ⚠️ {pkg}: {res}")

                    messagebox.showinfo("Restauración Completada", f"Se han restaurado {restored_count}/{len(pkgs_to_restore)} aplicaciones correctamente.")
                except Exception as e:
                    self.log(f"Error en restauración: {e}")
                    messagebox.showerror("Error", f"Fallo al restaurar: {e}")

            threading.Thread(target=task, daemon=True).start()

        ttk.Button(btn_box, text="🧹 Debloat (Limpiar Apps Basura)", command=execute_debloat).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_box, text="↺ Recuperar desde Punto de Restauración", command=execute_restore).pack(side=tk.RIGHT, padx=4)

    # --- TRANSFERENCIA DE ARCHIVOS Y PORTAPAPELES ---
    def push_file_to_android(self):
        file_path = filedialog.askopenfilename(title="Seleccionar archivo para enviar al móvil")
        if not file_path:
            return

        def task():
            try:
                filename = os.path.basename(file_path)
                remote_dest = f"/sdcard/Download/{filename}"
                self.log(f"Enviando archivo {filename} a {remote_dest}...")
                res = subprocess.run(["adb", "-s", self.current_connected_device or "", "push", file_path, remote_dest], capture_output=True, text=True, timeout=30, **PROCESS_CREATION_OPTIONS)
                if res.returncode == 0:
                    self.log(f"✅ Archivo enviado con éxito: {filename}")
                    messagebox.showinfo("Envío Correcto", f"Archivo enviado a:\n{remote_dest}")
                else:
                    self.log(f"❌ Error al enviar archivo: {res.stderr}")
            except Exception as e:
                self.log(f"Error al enviar: {e}")

        threading.Thread(target=task, daemon=True).start()

    def install_apk_from_pc(self):
        file_path = filedialog.askopenfilename(title="Seleccionar APK para instalar", filetypes=[("Android Packages", "*.apk")])
        if not file_path:
            return

        def task():
            try:
                self.log(f"Instalando APK: {os.path.basename(file_path)}...")
                res = subprocess.run(["adb", "-s", self.current_connected_device or "", "install", "-r", file_path], capture_output=True, text=True, timeout=60, **PROCESS_CREATION_OPTIONS)
                if "Success" in res.stdout:
                    self.log(f"✅ Aplicación instalada correctamente.")
                    messagebox.showinfo("Instalación Exitosa", "La APK se ha instalado correctamente en el teléfono.")
                else:
                    self.log(f"❌ Error de instalación: {res.stdout or res.stderr}")
            except Exception as e:
                self.log(f"Error instalando APK: {e}")

        threading.Thread(target=task, daemon=True).start()

    def list_remote_files(self):
        remote_path = self.remote_path_entry.get().strip()
        def task():
            try:
                self.log(f"Listando archivos en {remote_path}...")
                res = subprocess.run(["adb", "-s", self.current_connected_device or "", "shell", "ls", "-1", remote_path], capture_output=True, text=True, timeout=5, **PROCESS_CREATION_OPTIONS)
                if res.returncode == 0:
                    files = [f.strip() for f in res.stdout.strip().split("\n") if f.strip()]
                    self.root.after(0, lambda: self._update_file_listbox(files))
                    self.log(f"Encontrados {len(files)} elementos.")
                else:
                    self.log(f"Error listando directorio: {res.stderr}")
            except Exception as e:
                self.log(f"Error al listar: {e}")

        threading.Thread(target=task, daemon=True).start()

    def _update_file_listbox(self, files):
        self.file_listbox.delete(0, tk.END)
        for f in files:
            self.file_listbox.insert(tk.END, f)

    def pull_selected_file(self):
        sel = self.file_listbox.curselection()
        if not sel:
            messagebox.showwarning("Selección vacía", "Selecciona un archivo de la lista para descargar.")
            return

        selected_filename = self.file_listbox.get(sel[0])
        remote_path = self.remote_path_entry.get().strip()
        full_remote_file = f"{remote_path.rstrip('/')}/{selected_filename}"

        dest_dir = filedialog.askdirectory(title="Seleccionar carpeta de destino en PC", initialdir=self.config.get("last_pc_pull_dir"))
        if not dest_dir:
            return

        self.config["last_pc_pull_dir"] = dest_dir
        self.save_current_settings()

        def task():
            try:
                self.log(f"Descargando {selected_filename} a {dest_dir}...")
                res = subprocess.run(["adb", "-s", self.current_connected_device or "", "pull", full_remote_file, dest_dir], capture_output=True, text=True, timeout=60, **PROCESS_CREATION_OPTIONS)
                if res.returncode == 0:
                    self.log(f"✅ Descarga completada: {selected_filename}")
                    messagebox.showinfo("Descarga Exitosa", f"Archivo guardado en:\n{dest_dir}")
                else:
                    self.log(f"❌ Error al descargar: {res.stderr}")
            except Exception as e:
                self.log(f"Error al descargar: {e}")

        threading.Thread(target=task, daemon=True).start()

    def send_clipboard_to_android(self):
        try:
            text = self.root.clipboard_get()
            if not text:
                return
            def task():
                escaped_text = text.replace('"', '\\"').replace("'", "\\'")
                self._safe_adb_run(["shell", "input", "text", f'"{escaped_text}"'], timeout=3)
                self.log("Texto del portapapeles del PC pegado en el móvil.")
            threading.Thread(target=task, daemon=True).start()
        except Exception as e:
            self.log(f"No se pudo leer el portapapeles del PC: {e}")

    def get_clipboard_from_android(self):
        def task():
            try:
                out = self._safe_adb_run(["shell", "cmd", "clipboard", "get"], timeout=3)
                if out:
                    self.root.clipboard_clear()
                    self.root.clipboard_append(out)
                    self.log("Portapapeles del móvil copiado al PC.")
                    messagebox.showinfo("Portapapeles Copiado", f"Texto recuperado del móvil:\n{out[:100]}...")
                else:
                    self.log("El portapapeles del móvil está vacío o no se pudo obtener.")
            except Exception as e:
                self.log(f"Error obteniendo portapapeles: {e}")

        threading.Thread(target=task, daemon=True).start()

    def log(self, message):
        try:
            if self._is_closing:
                return
            timestamp = time.strftime('%H:%M:%S')
            self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
            line_count = int(self.log_text.index('end-1c').split('.')[0])
            if line_count > 300:
                self.log_text.delete('1.0', f'{line_count - 300}.0')
            self.log_text.see(tk.END)
        except Exception:
            pass

    def hide_to_tray(self):
        if not IS_WINDOWS:
            self.real_exit()
            return

        try:
            self.save_current_settings()
            self.root.withdraw()
            self.show_windows_toast("Android Control Center", "App minimizada al tray. Clic derecho para salir.")
        except Exception:
            pass

    def restore_window(self):
        try:
            self.root.deiconify()
            self.root.state('normal')
            self.root.lift()
            self.root.focus_force()
        except Exception:
            pass

    def real_exit(self):
        if self._is_closing:
            return
        self._is_closing = True
        try:
            self.save_current_settings()
            if self.scrcpy_process and self.scrcpy_process.poll() is None:
                try:
                    self.scrcpy_process.terminate()
                except Exception:
                    pass
            if self.logcat_process and self.logcat_process.poll() is None:
                try:
                    self.logcat_process.terminate()
                except Exception:
                    pass
            if self.tray is not None:
                try:
                    self.tray.remove_icon()
                except Exception:
                    pass
            self.root.destroy()
        except Exception:
            pass
        sys.exit(0)

    def run_adb_cmd(self, args):
        def task():
            if self._is_closing:
                return
            try:
                res = subprocess.run(["adb", "-s", self.current_connected_device or ""] + args, capture_output=True, text=True, timeout=5, **PROCESS_CREATION_OPTIONS)
                if self._is_closing:
                    return
                if res.returncode == 0:
                    self.log(f"ADB Éxito: {' '.join(args)}")
                else:
                    self.log(f"ADB Error: {res.stderr.strip()}")
            except Exception as e:
                if not self._is_closing:
                    self.log(f"Fallo al ejecutar ADB: {e}")
        threading.Thread(target=task, daemon=True).start()

    def check_adb_connection(self):
        if self._is_closing:
            return
        def task():
            if self._is_closing:
                return
            try:
                res = subprocess.run(["adb", "devices"], capture_output=True, text=True, timeout=3, **PROCESS_CREATION_OPTIONS)
                if self._is_closing:
                    return
                lines = res.stdout.strip().split("\n")[1:]
                devices = [line.split()[0] for line in lines if "device" in line and not "offline" in line]
                
                if devices:
                    self.current_connected_device = devices[0]
                    try:
                        if not self._is_closing:
                            self.root.after(0, lambda: self.status_lbl.config(text=f"Conectado: {devices[0]}", foreground="green"))
                    except Exception:
                        pass
                else:
                    self.current_connected_device = None
                    try:
                        if not self._is_closing:
                            self.root.after(0, lambda: self.status_lbl.config(text="No se detecta dispositivo (reconectando...)", foreground="orange"))
                    except Exception:
                        pass
            except Exception:
                self.current_connected_device = None
                try:
                    if not self._is_closing:
                        self.root.after(0, lambda: self.status_lbl.config(text="Error ADB / verificando...", foreground="red"))
                except Exception:
                    pass
        
        threading.Thread(target=task, daemon=True).start()

    def periodic_check(self):
        if self._is_closing:
            return
        
        if self._check_in_progress:
            if not self._is_closing:
                self.root.after(5000, self.periodic_check)
            return

        self._check_in_progress = True

        def background_task():
            try:
                if self._is_closing:
                    return
                res = subprocess.run(["adb", "devices"], capture_output=True, text=True, timeout=3, **PROCESS_CREATION_OPTIONS)
                if self._is_closing:
                    return
                lines = res.stdout.strip().split("\n")[1:]
                devices = [line.split()[0] for line in lines if "device" in line and not "offline" in line]
                
                if not devices and self.is_auto_reconnect_enabled:
                    target = self.ip_entry.get().strip()
                    if target and target != "192.168.1.XX:5555":
                        subprocess.run(["adb", "connect", target], capture_output=True, text=True, timeout=3, **PROCESS_CREATION_OPTIONS)
                
                if not self._is_closing:
                    self.check_adb_connection()
            except Exception:
                pass
            finally:
                self._check_in_progress = False

        threading.Thread(target=background_task, daemon=True).start()
        
        if not self._is_closing:
            self.root.after(5000, self.periodic_check)

    def enable_tcpiip(self):
        def task():
            try:
                self.log("Cambiando ADB a modo TCP/IP en puerto 5555...")
                res = subprocess.run(["adb", "-s", self.current_connected_device or "", "tcpip", "5555"], capture_output=True, text=True, timeout=5, **PROCESS_CREATION_OPTIONS)
                self.log(res.stdout.strip() or res.stderr.strip())
                messagebox.showinfo("Modo TCP/IP", "ADB reiniciado en modo TCP/IP (puerto 5555).\nYa puedes desconectar el cable USB y conectar por Wi-Fi.")
            except Exception as e:
                self.log(f"Fallo al activar TCP/IP: {e}")
        threading.Thread(target=task, daemon=True).start()

    def connect_wireless(self):
        target = self.ip_entry.get().strip()
        if not target or target == "192.168.1.XX:5555":
            messagebox.showwarning("IP Inválida", "Introduce una dirección IP y puerto válidos (ej. 192.168.1.50:5555)")
            return

        def task():
            try:
                self.log(f"Conectando a dispositivo inalámbrico {target}...")
                res = subprocess.run(["adb", "connect", target], capture_output=True, text=True, timeout=6, **PROCESS_CREATION_OPTIONS)
                out = res.stdout.strip()
                self.log(out)
                if "connected" in out:
                    messagebox.showinfo("Conectado", f"Conectado correctamente a {target}")
                    self.check_adb_connection()
                else:
                    messagebox.showerror("Conexión Fallida", f"No se pudo conectar a {target}.\n{out}")
            except Exception as e:
                self.log(f"Error conexión inalámbrica: {e}")
        threading.Thread(target=task, daemon=True).start()

    def pair_wireless(self):
        target = simpledialog.askstring("Emparejamiento Wi-Fi", "Introduce IP:Puerto de emparejamiento (ej. 192.168.1.50:37000):")
        if not target:
            return
        code = simpledialog.askstring("Emparejamiento Wi-Fi", "Introduce el código de 6 dígitos del teléfono:")
        if not code:
            return

        def task():
            try:
                self.log(f"Emparejando con {target}...")
                res = subprocess.run(["adb", "pair", target, code], capture_output=True, text=True, timeout=8, **PROCESS_CREATION_OPTIONS)
                out = res.stdout.strip()
                self.log(out)
                messagebox.showinfo("Resultado Emparejamiento", out)
            except Exception as e:
                self.log(f"Error de emparejamiento: {e}")
        threading.Thread(target=task, daemon=True).start()

    def start_scrcpy(self):
        if self.scrcpy_process and self.scrcpy_process.poll() is None:
            self.log("scrcpy ya se encuentra en ejecución.")
            return

        cmd = ["scrcpy"]
        if self.current_connected_device:
            cmd.extend(["-s", self.current_connected_device])
        if self.stay_awake_var.get():
            cmd.append("--stay-awake")
        if self.turn_screen_off_var.get():
            cmd.append("--turn-screen-off")

        def task():
            try:
                self.log(f"Lanzando: {' '.join(cmd)}")
                self.scrcpy_process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, **PROCESS_CREATION_OPTIONS)
                self.root.after(0, lambda: self.start_mirror_btn.config(state=tk.DISABLED))
                self.root.after(0, lambda: self.stop_mirror_btn.config(state=tk.NORMAL))
                
                self.scrcpy_process.wait()
                self.log("Sesión de scrcpy finalizada.")
            except FileNotFoundError:
                messagebox.showerror("scrcpy no encontrado", "scrcpy no está instalado o no se encuentra en el PATH del sistema.")
            except Exception as e:
                self.log(f"Error en scrcpy: {e}")
            finally:
                self.scrcpy_process = None
                self.root.after(0, lambda: self.start_mirror_btn.config(state=tk.NORMAL))
                self.root.after(0, lambda: self.stop_mirror_btn.config(state=tk.DISABLED))

        threading.Thread(target=task, daemon=True).start()

    def stop_scrcpy(self):
        if self.scrcpy_process and self.scrcpy_process.poll() is None:
            self.scrcpy_process.terminate()
            self.log("scrcpy finalizado.")

    def open_cast_dialog(self):
        cast_win = tk.Toplevel(self.root)
        cast_win.title("Castear pantalla del PC")
        cast_win.transient(self.root)
        cast_win.update_idletasks()
        width = 460
        height = 250
        x = self.root.winfo_rootx() + max(0, (self.root.winfo_width() - width) // 2)
        y = self.root.winfo_rooty() + max(0, (self.root.winfo_height() - height) // 2)
        x = min(x, max(0, cast_win.winfo_screenwidth() - width))
        y = min(y, max(0, cast_win.winfo_screenheight() - height))
        cast_win.geometry(f"{width}x{height}+{x}+{y}")
        cast_win.grab_set()

        ttk.Label(
            cast_win,
            text="Esto comparte la pantalla completa del PC, no solo la ventana de scrcpy.\n"
            "Deja scrcpy visible y selecciona el televisor en el panel que se abrirá.",
            wraplength=420,
            justify=tk.LEFT,
            padding=12
        ).pack(fill=tk.X)

        options = ttk.LabelFrame(cast_win, text="Selecciona el tipo de receptor", padding=10)
        options.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 12))

        ttk.Button(
            options,
            text="Google Cast (Chromecast / Google TV)",
            command=self.open_google_cast
        ).pack(fill=tk.X, pady=4)
        ttk.Button(
            options,
            text="Miracast (pantalla inalámbrica / algunos AnyCast)",
            command=self.open_miracast
        ).pack(fill=tk.X, pady=4)

        ttk.Label(
            options,
            text="El PC y la TV deben estar preparados para el mismo protocolo.\n"
            "La compatibilidad depende del sistema, el adaptador Wi-Fi y el modelo de TV.",
            wraplength=410,
            justify=tk.LEFT
        ).pack(anchor="w", pady=(8, 0))

    def open_google_cast(self):
        browser = self._find_google_cast_browser()
        if not browser:
            messagebox.showerror(
                "Navegador compatible no encontrado",
                "Instala Google Chrome para escritorio y vuelve a intentarlo.\n\n"
                "Descarga: https://www.google.com/chrome/"
            )
            return

        try:
            subprocess.Popen([browser, "--new-window"], **PROCESS_CREATION_OPTIONS)
            messagebox.showinfo(
                "Iniciar Google Cast",
                "En la ventana del navegador:\n"
                "1. Abre el menú ⋮.\n"
                "2. Selecciona «Transmitir», «Cast» o «Guardar y compartir > Transmitir».\n"
                "3. En «Fuentes», elige «Transmitir pantalla» y selecciona la TV.\n\n"
                "Mantén scrcpy visible en el escritorio que vas a compartir."
            )
            self.log("Abierto el navegador para iniciar Google Cast de pantalla.")
        except OSError as e:
            messagebox.showerror("No se pudo abrir el navegador", str(e))
            self.log(f"Error al abrir el navegador para Google Cast: {e}")

    def _find_google_cast_browser(self):
        browser_names = (
            ("chrome", "google-chrome", "google-chrome-stable")
            if not IS_WINDOWS else ("chrome",)
        )
        for name in browser_names:
            browser = shutil.which(name)
            if browser:
                return browser

        if IS_WINDOWS:
            local_app_data = os.environ.get("LOCALAPPDATA", "")
            program_files = os.environ.get("PROGRAMFILES", "")
            program_files_x86 = os.environ.get("PROGRAMFILES(X86)", "")
            candidates = [
                os.path.join(local_app_data, "Google", "Chrome", "Application", "chrome.exe"),
                os.path.join(program_files, "Google", "Chrome", "Application", "chrome.exe"),
                os.path.join(program_files_x86, "Google", "Chrome", "Application", "chrome.exe")
            ]
            for candidate in candidates:
                if candidate and os.path.isfile(candidate):
                    return candidate
        return None

    def open_miracast(self):
        if IS_WINDOWS:
            try:
                user32 = ctypes.windll.user32
                key_up = 0x0002
                vk_lwin = 0x5B
                vk_k = 0x4B
                user32.keybd_event(vk_lwin, 0, 0, 0)
                user32.keybd_event(vk_k, 0, 0, 0)
                user32.keybd_event(vk_k, 0, key_up, 0)
                user32.keybd_event(vk_lwin, 0, key_up, 0)
                self.log("Abierto el selector de pantalla inalámbrica de Windows (Win+K).")
            except Exception as e:
                messagebox.showerror("No se pudo abrir Miracast", str(e))
                self.log(f"Error al abrir el selector Miracast de Windows: {e}")
            return

        network_displays = shutil.which("gnome-network-displays")
        if not network_displays:
            messagebox.showwarning(
                "GNOME Network Displays no está instalado",
                "Para probar Miracast en Linux, instala GNOME Network Displays "
                "desde los repositorios de tu distribución.\n\n"
                "La disponibilidad depende del escritorio, los controladores y "
                "el adaptador Wi-Fi. No todos los AnyCast son compatibles."
            )
            return

        try:
            subprocess.Popen([network_displays], **PROCESS_CREATION_OPTIONS)
            self.log("Abierto GNOME Network Displays para buscar receptores Miracast.")
        except OSError as e:
            messagebox.showerror("No se pudo abrir GNOME Network Displays", str(e))
            self.log(f"Error al abrir GNOME Network Displays: {e}")

    def take_screenshot(self):
        def task():
            filename = f"screenshot_{int(time.time())}.png"
            try:
                self._safe_adb_run(["shell", "screencap", "-p", f"/sdcard/{filename}"], timeout=5)
                self._safe_adb_run(["pull", f"/sdcard/{filename}", filename], timeout=5)
                self._safe_adb_run(["shell", "rm", f"/sdcard/{filename}"], timeout=3)
                self.log(f"Captura guardada: {filename}")
                messagebox.showinfo("Captura Guardada", f"Guardada en la carpeta del programa como:\n{filename}")
            except Exception as e:
                self.log(f"Captura fallida: {e}")
        threading.Thread(target=task, daemon=True).start()

    def toggle_notifications(self):
        if not self.is_monitoring_notifications:
            self.is_monitoring_notifications = True
            self.notif_btn.config(text="🔕 Desactivar Puente de Notificaciones")
            self.log("Monitoreo de notificaciones activado por logcat.")
            self.start_notification_listener()
        else:
            self.is_monitoring_notifications = False
            self.notif_btn.config(text="🔔 Activar Puente de Notificaciones a Windows")
            self.log("Monitoreo de notificaciones detenido.")
            if self.logcat_process:
                self.logcat_process.terminate()

    def start_notification_listener(self):
        def task():
            try:
                cmd = ["adb"]
                if self.current_connected_device:
                    cmd.extend(["-s", self.current_connected_device])
                cmd.extend(["logcat", "-s", "NotificationManagerService:I", "Telecom:I"])

                self.logcat_process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="ignore",
                    **PROCESS_CREATION_OPTIONS
                )
                while self.is_monitoring_notifications and not self._is_closing and self.logcat_process and self.logcat_process.poll() is None:
                    line = self.logcat_process.stdout.readline()
                    if not line:
                        break
                    
                    if "enqueueNotification" in line or "pkg=" in line or "onIncomingCall" in line:
                        app_name = "Android Alert"
                        detail = "Nueva notificación recibida"
                        
                        if "pkg=" in line:
                            try:
                                parts = line.split("pkg=")
                                if len(parts) > 1:
                                    app_name = parts[1].split()[0]
                            except Exception:
                                pass
                        
                        if "onIncomingCall" in line or "call" in line.lower():
                            app_name = "Llamada Entrante"
                            detail = "El teléfono está sonando..."
                        
                        self.log(f"[Notificación] {line.strip()[-80:]}")
                        self.show_windows_toast(f"📱 {app_name}", detail)
            except Exception as e:
                if not self._is_closing:
                    self.log(f"Error en oyente de notificaciones: {e}")

        threading.Thread(target=task, daemon=True).start()

    def show_windows_toast(self, title, message):
        try:
            if IS_WINDOWS and self.tray is not None and not self._is_closing:
                self.tray.show_balloon(title, message)
        except Exception:
            pass

if __name__ == "__main__":
    root = tk.Tk()
    app = ADBScrcpyApp(root)
    root.mainloop()