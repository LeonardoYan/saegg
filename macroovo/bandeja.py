"""Ícone na bandeja do sistema (área de notificação do Windows), feito só com ctypes, sem bibliotecas extras."""
import base64
import ctypes
import queue
import threading
from ctypes import wintypes

from .idioma import T

LRESULT = ctypes.c_ssize_t
WNDPROC = ctypes.WINFUNCTYPE(LRESULT, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM)

WM_DESTROY = 0x0002
WM_NULL = 0x0000
WM_LBUTTONUP = 0x0202
WM_RBUTTONUP = 0x0205
MSG_BANDEJA = 0x8001      # WM_APP + 1: cliques no ícone
MSG_DICA = 0x8002         # WM_APP + 2: atualizar o texto que aparece ao passar o mouse
MSG_ENCERRAR = 0x8003     # WM_APP + 3: remover o ícone e fechar
NIM_ADD, NIM_MODIFY, NIM_DELETE = 0, 1, 2
NIF_MESSAGE, NIF_ICON, NIF_TIP = 0x1, 0x2, 0x4
TPM_RIGHTBUTTON, TPM_NONOTIFY, TPM_RETURNCMD = 0x0002, 0x0080, 0x0100
MF_STRING, MF_SEPARATOR = 0x0000, 0x0800
IDI_APPLICATION = 32512
SM_CXSMICON = 49
ID_ICONE = 1


class GUID(ctypes.Structure):
    _fields_ = [("Data1", ctypes.c_uint32), ("Data2", ctypes.c_uint16), ("Data3", ctypes.c_uint16),
                ("Data4", ctypes.c_ubyte * 8)]


# Tipos de tamanho fixo (em vez de wintypes.DWORD etc.) para o layout ser o mesmo do Windows de 32 e 64 bits.
class NOTIFYICONDATAW(ctypes.Structure):
    _fields_ = [
        ("cbSize", ctypes.c_uint32), ("hWnd", ctypes.c_void_p), ("uID", ctypes.c_uint32),
        ("uFlags", ctypes.c_uint32), ("uCallbackMessage", ctypes.c_uint32), ("hIcon", ctypes.c_void_p),
        ("szTip", ctypes.c_wchar * 128), ("dwState", ctypes.c_uint32), ("dwStateMask", ctypes.c_uint32),
        ("szInfo", ctypes.c_wchar * 256), ("uVersion", ctypes.c_uint32), ("szInfoTitle", ctypes.c_wchar * 64),
        ("dwInfoFlags", ctypes.c_uint32), ("guidItem", GUID), ("hBalloonIcon", ctypes.c_void_p),
    ]


class WNDCLASSW(ctypes.Structure):
    _fields_ = [
        ("style", ctypes.c_uint32), ("lpfnWndProc", WNDPROC), ("cbClsExtra", ctypes.c_int),
        ("cbWndExtra", ctypes.c_int), ("hInstance", ctypes.c_void_p), ("hIcon", ctypes.c_void_p),
        ("hCursor", ctypes.c_void_p), ("hbrBackground", ctypes.c_void_p), ("lpszMenuName", ctypes.c_wchar_p),
        ("lpszClassName", ctypes.c_wchar_p),
    ]


def _carregar():
    """Abre as DLLs do Windows em instâncias próprias, para não mexer nos tipos usados pelo resto do programa."""
    u = ctypes.WinDLL("user32", use_last_error=True)
    s = ctypes.WinDLL("shell32", use_last_error=True)
    k = ctypes.WinDLL("kernel32", use_last_error=True)
    H, UINT, WP, LP, VP = wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM, ctypes.c_void_p
    u.DefWindowProcW.argtypes, u.DefWindowProcW.restype = [H, UINT, WP, LP], LRESULT
    u.RegisterClassW.argtypes, u.RegisterClassW.restype = [ctypes.POINTER(WNDCLASSW)], ctypes.c_uint16
    u.UnregisterClassW.argtypes = [ctypes.c_wchar_p, VP]
    u.CreateWindowExW.argtypes = [ctypes.c_uint32, ctypes.c_wchar_p, ctypes.c_wchar_p, ctypes.c_uint32,
                                  ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, H, VP, VP, VP]
    u.CreateWindowExW.restype = H
    u.DestroyWindow.argtypes = [H]
    u.GetMessageW.argtypes, u.GetMessageW.restype = [ctypes.POINTER(wintypes.MSG), H, UINT, UINT], ctypes.c_int
    u.TranslateMessage.argtypes = [ctypes.POINTER(wintypes.MSG)]
    u.DispatchMessageW.argtypes, u.DispatchMessageW.restype = [ctypes.POINTER(wintypes.MSG)], LRESULT
    u.PostMessageW.argtypes = [H, UINT, WP, LP]
    u.PostQuitMessage.argtypes = [ctypes.c_int]
    u.RegisterWindowMessageW.argtypes, u.RegisterWindowMessageW.restype = [ctypes.c_wchar_p], UINT
    u.CreatePopupMenu.restype = VP
    u.AppendMenuW.argtypes = [VP, UINT, ctypes.c_size_t, ctypes.c_wchar_p]
    u.TrackPopupMenu.argtypes = [VP, UINT, ctypes.c_int, ctypes.c_int, ctypes.c_int, H, VP]
    u.TrackPopupMenu.restype = ctypes.c_int
    u.DestroyMenu.argtypes = [VP]
    u.GetCursorPos.argtypes = [ctypes.POINTER(wintypes.POINT)]
    u.SetForegroundWindow.argtypes = [H]
    u.GetSystemMetrics.argtypes = [ctypes.c_int]
    u.CreateIconFromResourceEx.argtypes = [ctypes.c_char_p, ctypes.c_uint32, ctypes.c_int, ctypes.c_uint32,
                                           ctypes.c_int, ctypes.c_int, ctypes.c_uint32]
    u.CreateIconFromResourceEx.restype = VP
    u.LoadIconW.argtypes, u.LoadIconW.restype = [VP, VP], VP
    u.DestroyIcon.argtypes = [VP]
    s.Shell_NotifyIconW.argtypes, s.Shell_NotifyIconW.restype = [ctypes.c_uint32, ctypes.POINTER(NOTIFYICONDATAW)], ctypes.c_int
    k.GetModuleHandleW.argtypes, k.GetModuleHandleW.restype = [ctypes.c_wchar_p], VP
    return u, s, k


class Bandeja(threading.Thread):
    """Mantém um ícone na bandeja. Cliques viram eventos ("bandeja", comando) na fila do programa:
    1 = abrir a janela (clique esquerdo), e os números dos itens do menu (clique direito).

    `itens()` devolve a lista do menu: tuplas (número, texto) ou None para uma linha separadora.
    `ok` só fica True quando o Windows aceitou o ícone, e é por ele que o programa decide se pode esconder a janela.
    """

    def __init__(self, icone_base64, fila: queue.Queue, itens, dica: str):
        super().__init__(daemon=True)
        self.png = base64.b64decode("".join(icone_base64))
        self.fila, self.itens, self._dica = fila, itens, dica
        self.ok = False
        self.hwnd = None
        self._recriar = -1       # número da mensagem "TaskbarCreated" (o Explorer reiniciou)
        self._icone = None
        self._proc = None        # mantém a função de janela viva enquanto o ícone existir

    # ---------------------------------------------------------------- controle (outras threads)
    def atualizar_dica(self, texto: str) -> None:
        self._dica = texto
        if self.hwnd and self.ok:
            self._u.PostMessageW(self.hwnd, MSG_DICA, 0, 0)

    def encerrar(self) -> None:
        if self.hwnd:
            self._u.PostMessageW(self.hwnd, MSG_ENCERRAR, 0, 0)

    # ---------------------------------------------------------------- thread do ícone
    def run(self) -> None:
        classe = f"MacroOvoBandeja{id(self)}"  # nome único: ligar e desligar rápido não conflita
        self._u = None
        try:
            self._u, self._s, self._k = _carregar()
            u = self._u
            inst = self._k.GetModuleHandleW(None)
            self._proc = WNDPROC(self._janela_proc)
            wc = WNDCLASSW()
            wc.lpfnWndProc, wc.hInstance, wc.lpszClassName = self._proc, inst, classe
            if not u.RegisterClassW(ctypes.byref(wc)):
                raise ctypes.WinError(ctypes.get_last_error())
            self._recriar = u.RegisterWindowMessageW("TaskbarCreated")
            self.hwnd = u.CreateWindowExW(0, classe, classe, 0, 0, 0, 0, 0, None, None, inst, None)
            if not self.hwnd:
                raise ctypes.WinError(ctypes.get_last_error())
            self._icone = self._criar_icone()
            self._adicionar()
            if not self.ok:
                raise OSError(T("o Windows não aceitou o ícone"))
            msg = wintypes.MSG()
            while u.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
                u.TranslateMessage(ctypes.byref(msg))
                u.DispatchMessageW(ctypes.byref(msg))
        except Exception as e:  # noqa: BLE001
            self.fila.put(("log", ("aviso", "Não consegui criar o ícone da bandeja: {e}", {"e": str(e)})))
        finally:
            self.ok = False
            self.hwnd = None
            try:
                if self._icone:
                    self._u.DestroyIcon(self._icone)
                if self._u:
                    self._u.UnregisterClassW(classe, None)
            except Exception:  # noqa: BLE001
                pass

    def _criar_icone(self):
        """Ícone a partir do PNG do programa (o Windows 10/11 lê PNG direto). Se falhar, usa o ícone padrão."""
        u = self._u
        tam = u.GetSystemMetrics(SM_CXSMICON) or 16
        h = u.CreateIconFromResourceEx(self.png, len(self.png), 1, 0x00030000, tam, tam, 0)
        return h or u.LoadIconW(None, IDI_APPLICATION)

    def _dados(self) -> NOTIFYICONDATAW:
        nid = NOTIFYICONDATAW()
        nid.cbSize = ctypes.sizeof(NOTIFYICONDATAW)
        nid.hWnd, nid.uID, nid.uCallbackMessage, nid.hIcon = self.hwnd, ID_ICONE, MSG_BANDEJA, self._icone
        nid.uFlags = NIF_MESSAGE | NIF_ICON | NIF_TIP
        nid.szTip = self._dica[:127]
        return nid

    def _adicionar(self) -> None:
        self.ok = bool(self._s.Shell_NotifyIconW(NIM_ADD, ctypes.byref(self._dados())))

    def _menu(self, hwnd) -> None:
        u = self._u
        menu = u.CreatePopupMenu()
        for item in self.itens():
            if item is None:
                u.AppendMenuW(menu, MF_SEPARATOR, 0, None)
            else:
                u.AppendMenuW(menu, MF_STRING, item[0], item[1])
        pt = wintypes.POINT()
        u.GetCursorPos(ctypes.byref(pt))
        u.SetForegroundWindow(hwnd)  # sem isso o menu não fecha ao clicar fora dele
        cmd = u.TrackPopupMenu(menu, TPM_RIGHTBUTTON | TPM_NONOTIFY | TPM_RETURNCMD, pt.x, pt.y, 0, hwnd, None)
        u.PostMessageW(hwnd, WM_NULL, 0, 0)
        u.DestroyMenu(menu)
        if cmd:
            self.fila.put(("bandeja", cmd))

    def _janela_proc(self, hwnd, msg, wparam, lparam):
        try:
            if msg == MSG_BANDEJA:
                ev = lparam & 0xFFFF
                if ev == WM_LBUTTONUP:
                    self.fila.put(("bandeja", 1))
                elif ev == WM_RBUTTONUP:
                    self._menu(hwnd)
                return 0
            if msg == MSG_DICA:
                self._s.Shell_NotifyIconW(NIM_MODIFY, ctypes.byref(self._dados()))
                return 0
            if msg == MSG_ENCERRAR:
                self._u.DestroyWindow(hwnd)
                return 0
            if msg == self._recriar:  # o Explorer reiniciou e perdeu os ícones
                self._adicionar()
                return 0
            if msg == WM_DESTROY:
                self._s.Shell_NotifyIconW(NIM_DELETE, ctypes.byref(self._dados()))
                self._u.PostQuitMessage(0)
                return 0
        except Exception:  # noqa: BLE001
            pass
        return self._u.DefWindowProcW(hwnd, msg, wparam, lparam)
