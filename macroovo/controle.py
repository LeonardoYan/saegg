"""Controle pelo Discord: um bot lê comandos (!iniciar, !parar...) num canal e o macro obedece.

O programa só PERGUNTA ao Discord de tempos em tempos (conexão de saída, sem abrir porta no computador). O token do bot e o
ID do canal ficam só no arquivo de configuração. Quem puder escrever no canal escolhido pode mandar os comandos.
"""
import json
import queue
import re
import threading
import time
import urllib.error
import urllib.request

from .config import VERSAO
from .idioma import T
from .webhook import LIMITE_ARQUIVO, montar_multipart

API = "https://discord.com/api/v10"
INTERVALO = 5.0   # segundos entre uma pergunta e outra ao Discord
COMANDOS = {
    "iniciar": "iniciar", "pesca": "iniciar", "pescar": "iniciar",
    "autoclick": "autoclick", "ac": "autoclick",
    "parar": "parar", "pare": "parar",
    "status": "status", "clipe": "clipe",
    "print": "print", "foto": "print",
    "mouse": "mouse", "mover": "mouse",
    "ajuda": "ajuda", "comandos": "ajuda",
}
DIRECOES = {"cima": (0, -1), "up": (0, -1), "baixo": (0, 1), "down": (0, 1),
            "esquerda": (-1, 0), "left": (-1, 0), "direita": (1, 0), "right": (1, 0)}
PASSO_PADRAO = 50   # pixels de um "!mouse cima"
PASSO_MAX = 500     # no máximo isto por comando


def token_valido(token) -> bool:
    return isinstance(token, str) and re.fullmatch(r"[A-Za-z0-9._-]{40,120}", token) is not None


def canal_valido(canal) -> bool:
    return isinstance(canal, str) and canal.isdigit() and 15 <= len(canal) <= 22


def interpretar_comando(texto: str):
    """'!mouse cima 30' -> ('mouse', ['cima', '30']). None se não for um comando conhecido."""
    t = (texto or "").strip().lower()
    if not t.startswith("!"):
        return None
    partes = t[1:].split()
    cmd = COMANDOS.get(partes[0]) if partes else None
    return (cmd, partes[1:]) if cmd else None


def interpretar(texto: str):
    """'!iniciar' -> 'iniciar'. None se não for um comando conhecido."""
    r = interpretar_comando(texto)
    return r[0] if r else None


def _numero(txt: str):
    try:
        return float(txt.replace("px", "").replace("%", "").replace(",", "."))
    except ValueError:
        return None


def interpretar_mouse(args: list):
    """Argumentos de !mouse -> ("rel", dx, dy) | ("centro",) | ("pct", x, y). None se não entendeu.
    cima/baixo/esquerda/direita [pixels]; centro; X Y (porcentagem da janela, 0 a 100)."""
    if not args:
        return None
    a0 = args[0]
    if a0 in ("centro", "center", "meio"):
        return ("centro",)
    if a0 in DIRECOES:
        n = PASSO_PADRAO
        if len(args) > 1:
            n = _numero(args[1])
            if n is None:
                return None
        n = int(max(1, min(PASSO_MAX, round(n))))
        dx, dy = DIRECOES[a0]
        return ("rel", dx * n, dy * n)
    if len(args) >= 2:
        x, y = _numero(args[0]), _numero(args[1])
        if x is not None and y is not None and 0 <= x <= 100 and 0 <= y <= 100:
            return ("pct", x, y)
    return None


class ControleDiscord(threading.Thread):
    def __init__(self, token: str, canal: str, fila: queue.Queue, saudar: bool = True):
        super().__init__(daemon=True)
        self.token, self.canal, self.fila = token, canal, fila
        self.saudar = saudar  # escreve "Controle ligado" no canal (só quando a configuração acabou de mudar)
        self.parar = threading.Event()
        self._avisou_conteudo = False

    # ------------------------------------------------------------ HTTP
    def _pedir(self, metodo: str, caminho: str, corpo=None):
        dados = json.dumps(corpo).encode("utf-8") if corpo is not None else None
        req = urllib.request.Request(
            API + caminho, data=dados, method=metodo,
            headers={"Authorization": f"Bot {self.token}", "Content-Type": "application/json",
                     "User-Agent": f"DiscordBot (https://github.com/LeonardoYan/saegg, {VERSAO})"},
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                texto = r.read().decode("utf-8") or "null"
                return r.status, json.loads(texto), 0.0
        except urllib.error.HTTPError as e:
            espera = 0.0
            try:
                espera = float(json.loads(e.read().decode("utf-8")).get("retry_after", 0))
            except Exception:  # noqa: BLE001
                pass
            return e.code, None, espera
        except Exception:  # noqa: BLE001
            return 0, None, 0.0

    def _log(self, msg: str, nivel: str = "info", **kw) -> None:
        self.fila.put(("log", (nivel, msg, kw)))

    def responder(self, texto: str) -> None:
        """Escreve no canal (sem marcar ninguém). Roda em outra thread para não travar o programa."""
        def enviar() -> None:
            self._pedir("POST", f"/channels/{self.canal}/messages",
                        {"content": texto[:1900], "allowed_mentions": {"parse": []}})
        threading.Thread(target=enviar, daemon=True).start()

    def enviar_arquivo(self, texto: str, nome: str, dados: bytes, tipo: str) -> bool:
        """Posta uma imagem no canal (sem marcar ninguém). Bloqueia até terminar: chame de uma thread."""
        if len(dados) > LIMITE_ARQUIVO:
            return False
        corpo, limite = montar_multipart(texto, nome, dados, tipo)
        req = urllib.request.Request(
            API + f"/channels/{self.canal}/messages", data=corpo, method="POST",
            headers={"Authorization": f"Bot {self.token}", "Content-Type": f"multipart/form-data; boundary={limite}",
                     "User-Agent": f"DiscordBot (https://github.com/LeonardoYan/saegg, {VERSAO})"},
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return 200 <= r.status < 300
        except Exception:  # noqa: BLE001
            return False

    # ------------------------------------------------------------ laço
    def run(self) -> None:
        ultimo = None
        falhou_antes = False
        avisou_inicio = False
        while not self.parar.is_set():
            if ultimo is None:  # marca o ponto de partida: comandos antigos do canal não são executados
                status, msgs, espera = self._pedir("GET", f"/channels/{self.canal}/messages?limit=1")
                if status == 200 and isinstance(msgs, list):
                    ultimo = int(msgs[0]["id"]) if msgs else 0
            else:
                status, msgs, espera = self._pedir("GET", f"/channels/{self.canal}/messages?after={ultimo}&limit=20")
                if status == 200 and isinstance(msgs, list):
                    for m in sorted(msgs, key=lambda x: int(x["id"])):
                        ultimo = max(ultimo, int(m["id"]))
                        self._tratar(m)
            if status == 200:
                if falhou_antes:
                    self._log("Controle pelo Discord voltou a funcionar.", "ok")
                    falhou_antes = False
                if not avisou_inicio:
                    avisou_inicio = True
                    self._log("Controle pelo Discord ligado.", "ok")
                    if self.saudar:
                        self.responder(T("Controle ligado. Comandos: !iniciar, !autoclick, !parar, !status, !clipe, !print, !mouse, !ajuda"))
            elif status in (401, 403, 404):
                self._log({401: "O Discord recusou o token do bot. Confira o token e tente de novo.",
                           403: "O bot não tem permissão para ler esse canal. Dê a ele ver o canal e ler o histórico.",
                           404: "Canal não encontrado. Confira o ID do canal."}[status], "erro")
                return  # configuração errada: não adianta insistir
            elif status == 429:
                self.parar.wait(min(max(espera, 1.0), 60.0))
                continue
            elif not falhou_antes:
                falhou_antes = True
                self._log("Controle pelo Discord sem conexão. Vou tentar de novo sozinho.", "aviso")
            self.parar.wait(INTERVALO if status == 200 else 15.0)

    def _tratar(self, m: dict) -> None:
        autor = m.get("author") or {}
        if autor.get("bot"):
            return  # ignora bots (inclusive as respostas do próprio macro)
        conteudo = m.get("content") or ""
        if not conteudo and not m.get("attachments") and not m.get("embeds") and not self._avisou_conteudo:
            self._avisou_conteudo = True
            self._log("O Discord entregou uma mensagem sem texto. Ligue 'Message Content Intent' nas configurações do bot "
                      "(portal de desenvolvedores, aba Bot).", "aviso")
        r = interpretar_comando(conteudo)
        if r:
            self.fila.put(("controle", r))
