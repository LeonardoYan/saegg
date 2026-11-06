"""Acesso à API do Windows: DPI, temporizador, mouse (SendInput), janela do Roblox e leitura de pixels."""
import ctypes
import time
import tkinter as tk
from ctypes import wintypes


try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)  # coordenadas reais em telas com escala
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

try:
    ctypes.windll.winmm.timeBeginPeriod(1)  # temporizador de 1 ms (cliques mais rápidos)
except Exception:
    pass

user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32
user32.FindWindowW.argtypes = [wintypes.LPCWSTR, wintypes.LPCWSTR]
user32.FindWindowW.restype = wintypes.HWND
user32.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
user32.GetForegroundWindow.restype = wintypes.HWND
user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
user32.GetDC.argtypes = [wintypes.HWND]
user32.GetDC.restype = wintypes.HDC
user32.ReleaseDC.argtypes = [wintypes.HWND, wintypes.HDC]
gdi32.GetPixel.argtypes = [wintypes.HDC, ctypes.c_int, ctypes.c_int]
gdi32.GetPixel.restype = wintypes.DWORD

ULONG_PTR = wintypes.WPARAM


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    ]


class _INPUTUNION(ctypes.Union):
    _fields_ = [("mi", MOUSEINPUT)]


class INPUT(ctypes.Structure):
    _anonymous_ = ("u",)
    _fields_ = [("type", wintypes.DWORD), ("u", _INPUTUNION)]


def _enviar_mouse(flags: int) -> None:
    inp = INPUT(type=0)  # INPUT_MOUSE
    inp.mi = MOUSEINPUT(0, 0, 0, flags, 0, 0)
    user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))


def mouse_down() -> None:
    _enviar_mouse(0x0002)  # LEFTDOWN


def mouse_up() -> None:
    _enviar_mouse(0x0004)  # LEFTUP


BOTOES_MOUSE = {"esquerdo": (0x0002, 0x0004), "direito": (0x0008, 0x0010), "meio": (0x0020, 0x0040)}


def clicar(botao: str = "esquerdo") -> None:
    baixo, cima = BOTOES_MOUSE.get(botao, BOTOES_MOUSE["esquerdo"])
    _enviar_mouse(baixo)
    time.sleep(0.001)
    _enviar_mouse(cima)


def posicao_cursor() -> tuple[int, int]:
    pt = wintypes.POINT()
    user32.GetCursorPos(ctypes.byref(pt))
    return pt.x, pt.y


def mover_cursor(x: int, y: int) -> None:
    user32.SetCursorPos(int(x), int(y))


def roblox_em_primeiro_plano() -> bool:
    hwnd = user32.GetForegroundWindow()
    buf = ctypes.create_unicode_buffer(256)
    user32.GetWindowTextW(hwnd, buf, 256)
    return buf.value.startswith("Roblox")


def rect_janela_roblox() -> tuple[int, int, int, int] | None:
    """Retorna (esquerda, topo, largura, altura) da janela do Roblox, ou None se não estiver aberta."""
    hwnd = user32.FindWindowW(None, "Roblox")
    if not hwnd:
        return None
    rect = wintypes.RECT()
    if not user32.GetWindowRect(hwnd, ctypes.byref(rect)):
        return None
    larg, alt = rect.right - rect.left, rect.bottom - rect.top
    if larg < 300 or alt < 300 or rect.left <= -30000:  # minimizada
        return None
    return rect.left, rect.top, larg, alt


def barra_de_titulo_escura(root: tk.Tk) -> None:
    """Ajusta a barra de título ao tema (claro ou escuro) no Windows 10/11, se suportado."""
    try:
        from . import tema
        root.update()
        hwnd = ctypes.windll.user32.GetParent(root.winfo_id())
        valor = ctypes.c_int(1 if tema.ESCURO else 0)  # barra de título no mesmo tema da janela
        for atributo in (20, 19):  # DWMWA_USE_IMMERSIVE_DARK_MODE (versões novas e antigas)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                ctypes.c_void_p(hwnd), atributo, ctypes.byref(valor), ctypes.sizeof(valor)
            )
    except Exception:
        pass


def pixel_rgb(dc, x: int, y: int) -> tuple[int, int, int] | None:
    v = gdi32.GetPixel(dc, int(x), int(y))
    if v == 0xFFFFFFFF:  # CLR_INVALID
        return None
    return v & 0xFF, (v >> 8) & 0xFF, (v >> 16) & 0xFF


# ---------------------------------------------------------------- uma única janela do programa
_mutex_instancia = None  # mantém o mutex vivo enquanto o programa roda


def ja_esta_aberto() -> bool:
    """True se já existe outra cópia do programa rodando (cria o mutex nomeado na primeira cópia)."""
    global _mutex_instancia
    try:
        k32 = ctypes.WinDLL("kernel32", use_last_error=True)
        k32.CreateMutexW.argtypes = [wintypes.LPVOID, wintypes.BOOL, wintypes.LPCWSTR]
        k32.CreateMutexW.restype = wintypes.HANDLE
        _mutex_instancia = k32.CreateMutexW(None, False, "Local\\StealAnEgg_instancia_unica")
        return ctypes.get_last_error() == 183  # ERROR_ALREADY_EXISTS
    except Exception:
        return False


def mostrar_janela_existente(prefixo: str) -> None:
    """Traz para a frente a janela do programa que já está aberta (mesmo minimizada ou na bandeja)."""
    achadas = []
    try:
        enum_tipo = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

        def _cb(hwnd, _l):
            buf = ctypes.create_unicode_buffer(256)
            user32.GetWindowTextW(hwnd, buf, 256)
            if buf.value.startswith(prefixo):
                achadas.append(hwnd)
            return True

        user32.EnumWindows(enum_tipo(_cb), 0)
        for hwnd in achadas:
            user32.ShowWindow(hwnd, 9)  # SW_RESTORE
            user32.SetForegroundWindow(hwnd)
    except Exception:
        pass


# ---------------------------------------------------------------- iniciar com o Windows
_CHAVE_RUN = r"Software\Microsoft\Windows\CurrentVersion\Run"
_NOME_RUN = "RoubeUmOvo"


def _comando_inicio() -> str:
    """Comando que o Windows executa ao entrar: o próprio .exe, ou o script com o Python sem console."""
    import os
    import sys
    if getattr(sys, "frozen", False):
        return f'"{sys.executable}"'
    pythonw = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
    exe = pythonw if os.path.exists(pythonw) else sys.executable
    return f'"{exe}" "{os.path.abspath(sys.argv[0])}"'


def iniciar_com_windows_ativo() -> bool:
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _CHAVE_RUN) as chave:
            winreg.QueryValueEx(chave, _NOME_RUN)
        return True
    except Exception:
        return False


def definir_iniciar_com_windows(ligar: bool) -> bool:
    """Liga ou desliga a abertura junto com o Windows (só para o usuário atual, sem pedir administrador)."""
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _CHAVE_RUN, 0, winreg.KEY_SET_VALUE) as chave:
            if ligar:
                winreg.SetValueEx(chave, _NOME_RUN, 0, winreg.REG_SZ, _comando_inicio())
            else:
                try:
                    winreg.DeleteValue(chave, _NOME_RUN)
                except FileNotFoundError:
                    pass
        return True
    except Exception:
        return False
