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


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    ]


class _INPUTUNION(ctypes.Union):
    _fields_ = [("mi", MOUSEINPUT), ("ki", KEYBDINPUT)]


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


def apertar_scancode(scan: int) -> None:
    """Aperta e solta uma tecla pelo código de varredura (a posição física da tecla; não depende do layout)."""
    for flags in (0x0008, 0x0008 | 0x0002):  # SCANCODE; SCANCODE + KEYUP
        inp = INPUT(type=1)  # INPUT_KEYBOARD
        inp.ki = KEYBDINPUT(0, scan, flags, 0, 0)
        user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))
        time.sleep(0.03)


def apertar_tecla(vk: int) -> None:
    apertar_scancode(user32.MapVirtualKeyW(vk, 0))


BOTOES_MOUSE = {"esquerdo": (0x0002, 0x0004), "direito": (0x0008, 0x0010), "meio": (0x0020, 0x0040)}


def clicar(botao: str = "esquerdo") -> None:
    baixo, cima = BOTOES_MOUSE.get(botao, BOTOES_MOUSE["esquerdo"])
    _enviar_mouse(baixo)
    time.sleep(0.001)
    _enviar_mouse(cima)


def mover_relativo(dx: int, dy: int) -> None:
    """Movimento de mouse de verdade (gera o evento que o Roblox usa para marcar o botão sob o cursor)."""
    inp = INPUT(type=0)
    inp.mi = MOUSEINPUT(int(dx), int(dy), 0, 0x0001, 0, 0)  # MOUSEEVENTF_MOVE
    user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))


def clique_de_interface(botao: str = "esquerdo") -> None:
    """Clique para botões do jogo: chega ao ponto, "passa" o mouse, espera o botão acender e segura o clique."""
    baixo, cima = BOTOES_MOUSE.get(botao, BOTOES_MOUSE["esquerdo"])
    mover_relativo(2, 0)
    time.sleep(0.05)
    mover_relativo(-2, 0)
    time.sleep(0.12)
    _enviar_mouse(baixo)
    time.sleep(0.09)
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


def trazer_roblox_para_frente() -> bool:
    """Traz a janela do Roblox para o primeiro plano. True se ela ficou na frente."""
    try:
        hwnd = user32.FindWindowW(None, "Roblox")
        if not hwnd:
            return False
        if user32.IsIconic(hwnd):
            user32.ShowWindow(hwnd, 9)  # SW_RESTORE
        user32.keybd_event(0x12, 0, 0, 0)  # um toque em ALT libera o SetForegroundWindow para um programa em segundo plano
        user32.keybd_event(0x12, 0, 2, 0)
        user32.SetForegroundWindow(hwnd)
        return roblox_em_primeiro_plano()
    except Exception:  # noqa: BLE001
        return False


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


gdi32.CreateCompatibleDC.argtypes = [wintypes.HDC]
gdi32.CreateCompatibleDC.restype = wintypes.HDC
gdi32.CreateCompatibleBitmap.argtypes = [wintypes.HDC, ctypes.c_int, ctypes.c_int]
gdi32.CreateCompatibleBitmap.restype = wintypes.HBITMAP
gdi32.SelectObject.argtypes = [wintypes.HDC, wintypes.HGDIOBJ]
gdi32.SelectObject.restype = wintypes.HGDIOBJ
gdi32.DeleteObject.argtypes = [wintypes.HGDIOBJ]
gdi32.DeleteDC.argtypes = [wintypes.HDC]
gdi32.BitBlt.argtypes = [wintypes.HDC, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
                         wintypes.HDC, ctypes.c_int, ctypes.c_int, wintypes.DWORD]
gdi32.BitBlt.restype = wintypes.BOOL


class _BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [("biSize", wintypes.DWORD), ("biWidth", wintypes.LONG), ("biHeight", wintypes.LONG),
                ("biPlanes", wintypes.WORD), ("biBitCount", wintypes.WORD), ("biCompression", wintypes.DWORD),
                ("biSizeImage", wintypes.DWORD), ("biXPelsPerMeter", wintypes.LONG),
                ("biYPelsPerMeter", wintypes.LONG), ("biClrUsed", wintypes.DWORD),
                ("biClrImportant", wintypes.DWORD)]


gdi32.GetDIBits.argtypes = [wintypes.HDC, wintypes.HBITMAP, wintypes.UINT, wintypes.UINT, ctypes.c_void_p,
                            ctypes.c_void_p, wintypes.UINT]
gdi32.GetDIBits.restype = ctypes.c_int


def capturar_regiao(dc, x: int, y: int, larg: int, alt: int):
    """Copia um retângulo da tela de uma vez só (bem mais rápido que ler pixel por pixel).

    Devolve (dados, larg): bytes B,G,R,A de cima para baixo; ou None se não conseguiu."""
    if larg <= 0 or alt <= 0:
        return None
    mem = bmp = antigo = None
    try:
        mem = gdi32.CreateCompatibleDC(dc)
        bmp = gdi32.CreateCompatibleBitmap(dc, larg, alt)
        if not mem or not bmp:
            return None
        antigo = gdi32.SelectObject(mem, bmp)
        if not gdi32.BitBlt(mem, 0, 0, larg, alt, dc, int(x), int(y), 0x00CC0020):  # SRCCOPY
            return None
        info = _BITMAPINFOHEADER(40, larg, -alt, 1, 32, 0, 0, 0, 0, 0, 0)  # altura negativa = de cima para baixo
        buf = (ctypes.c_ubyte * (larg * alt * 4))()
        if gdi32.GetDIBits(mem, bmp, 0, alt, buf, ctypes.byref(info), 0) == 0:
            return None
        return buf, larg
    except Exception:  # noqa: BLE001
        return None
    finally:
        try:
            if mem and antigo:
                gdi32.SelectObject(mem, antigo)
            if bmp:
                gdi32.DeleteObject(bmp)
            if mem:
                gdi32.DeleteDC(mem)
        except Exception:  # noqa: BLE001
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
