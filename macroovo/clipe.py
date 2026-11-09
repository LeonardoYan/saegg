"""Clipe da pesca: timelapse da tela do Roblox, quadros marcados nas falhas e montagem do GIF.

Durante a pesca, um gravador guarda um quadro da janela do Roblox de tempos em tempos (só na memória,
comprimido em JPEG). Quando o macro falha ou o usuário pede, os quadros viram um GIF curto que vai ao Discord.
Nada é gravado em disco e nada sai do computador sem o webhook configurado.
"""
import collections
import io
import math
import os
import queue
import shutil
import subprocess
import sys
import tempfile
import threading
import time

from .idioma import T
from .winapi import capturar_regiao, rect_janela_roblox, user32

LARG_GUARDADA = 960          # largura dos quadros guardados (px)
QUALIDADE_JPEG = 60
MAX_MARCADOS = 20            # quadros marcados (falhas) guardados
LIMITE_BYTES = 9_000_000     # o webhook do Discord aceita arquivos de até 10 MB; deixa folga
CORES_GIF = 96
# tentativas de montagem, da melhor para a menor: (largura, usar 1 a cada N quadros do timelapse, só marcados?)
TENTATIVAS = ((480, 3, False), (400, 3, False), (400, 4, False), (320, 5, False), (256, 6, False), (256, 1, True))
# tentativas do vídeo, da melhor para a menor: (largura, crf — maior = mais compressão)
TENTATIVAS_VIDEO = ((960, 28), (854, 30), (640, 32), (480, 35))
FPS_VIDEO = 15
MS_TIMELAPSE = 67           # tempo de cada quadro do timelapse no GIF
MS_MARCADO = 1800            # tempo de cada quadro marcado (falha / agora)


# ------------------------------------------------------------------------------ Pillow
def pillow_pronto() -> bool:
    try:
        import PIL.Image  # noqa: F401
        import PIL.ImageDraw  # noqa: F401
        return True
    except Exception:  # noqa: BLE001
        return False


def _python_de_texto() -> str:
    """O python.exe ao lado do pythonw.exe (o pip precisa de um executável com console para escrever a saída)."""
    exe = sys.executable
    pasta, nome = os.path.split(exe)
    if nome.lower() == "pythonw.exe":
        alt = os.path.join(pasta, "python.exe")
        if os.path.isfile(alt):
            return alt
    return exe


_TRAVA_PIP = threading.Lock()


def _pip_instalar(pacote: str) -> bool:
    try:
        r = subprocess.run(
            [_python_de_texto(), "-m", "pip", "install", "--disable-pip-version-check", pacote],
            capture_output=True, text=True, timeout=300,
            creationflags=0x08000000 if os.name == "nt" else 0,  # sem abrir janela preta
        )
        return r.returncode == 0
    except Exception:  # noqa: BLE001
        return False


def garantir_pillow(log=None) -> bool:
    """Confere se o Pillow está instalado; se não estiver (rodando em Python), instala sozinho uma vez."""
    with _TRAVA_PIP:
        if pillow_pronto():
            return True
        if getattr(sys, "frozen", False):
            if log:
                log("O clipe precisa do Pillow. Gere o programa de novo com o criar_exe.bat.", "erro")
            return False
        if log:
            log("Instalando o Pillow (só desta vez) para gravar o clipe…", "aviso")
        ok = _pip_instalar("pillow") and pillow_pronto()
        if log:
            if ok:
                log("Pillow instalado. O clipe está pronto.", "ok")
            else:
                log("Não consegui instalar o Pillow. Abra o prompt de comando e rode: python -m pip install pillow",
                    "erro")
        return ok


def ffmpeg_exe() -> str | None:
    """Caminho do ffmpeg (do pacote imageio-ffmpeg ou do que já estiver instalado no Windows). None se não há."""
    try:
        import imageio_ffmpeg
        exe = imageio_ffmpeg.get_ffmpeg_exe()
        if exe and os.path.isfile(exe):
            return exe
    except Exception:  # noqa: BLE001
        pass
    return shutil.which("ffmpeg")


def garantir_ffmpeg(log=None) -> str | None:
    """Garante o codificador de vídeo; instala o imageio-ffmpeg sozinho uma vez. Sem ele o clipe sai em GIF."""
    with _TRAVA_PIP:
        exe = ffmpeg_exe()
        if exe or getattr(sys, "frozen", False):
            return exe
        if log:
            log("Instalando o componente de vídeo do clipe (só desta vez, pode levar um minuto)…", "aviso")
        ok = _pip_instalar("imageio-ffmpeg")
        exe = ffmpeg_exe() if ok else None
        if log:
            if exe:
                log("Componente de vídeo instalado. O clipe sai em vídeo.", "ok")
            else:
                log("Não consegui instalar o componente de vídeo. O clipe vai em GIF. Para vídeo, rode: python -m pip install imageio-ffmpeg",
                    "aviso")
        return exe


# ------------------------------------------------------------------------------ captura
def _area_de_captura() -> tuple[int, int, int, int]:
    """Janela do Roblox; se ela não existir (jogo fechou), a tela inteira, para ver o que aconteceu."""
    rect = rect_janela_roblox()
    if rect is not None:
        return rect
    return 0, 0, user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)


def _capturar_imagem(larg_max: int = LARG_GUARDADA, marca=None):
    """Uma foto da área de captura como imagem do Pillow (RGB), reduzida para no máximo larg_max. None se falhou.
    marca: (x, y) na tela; desenha um círculo vermelho ali (a captura da tela não inclui o ponteiro do mouse)."""
    from PIL import Image
    x, y, larg, alt = _area_de_captura()
    dc = user32.GetDC(None)
    try:
        r = capturar_regiao(dc, x, y, larg, alt)
    finally:
        user32.ReleaseDC(None, dc)
    if r is None:
        return None
    buf, _l = r
    im = Image.frombuffer("RGB", (larg, alt), bytes(buf), "raw", "BGRX", 0, 1)
    if larg > larg_max:
        reamostra = getattr(Image, "Resampling", Image).BILINEAR
        im = im.resize((larg_max, max(1, round(alt * larg_max / larg))), reamostra)
    if marca is not None:
        _marcar_ponteiro(im, (marca[0] - x) * im.width / larg, (marca[1] - y) * im.height / alt)
    return im


def _marcar_ponteiro(im, px: float, py: float) -> None:
    """Círculo vermelho com borda branca e um pontinho no centro, no ponto (px, py) da imagem."""
    from PIL import ImageDraw
    if not (0 <= px < im.width and 0 <= py < im.height):
        return
    r = max(10, im.width // 60)
    d = ImageDraw.Draw(im)
    d.ellipse((px - r - 2, py - r - 2, px + r + 2, py + r + 2), outline=(255, 255, 255), width=2)
    d.ellipse((px - r, py - r, px + r, py + r), outline=(255, 0, 0), width=3)
    d.ellipse((px - 2, py - 2, px + 2, py + 2), fill=(255, 0, 0))


def foto_jpeg(larg_max: int = 1280, qualidade: int = 80, marca=None) -> bytes | None:
    """Um print agora (janela do Roblox, ou a tela inteira se o jogo estiver fechado) como JPEG. None se falhou.
    marca: posição do ponteiro do mouse na tela, desenhada como um círculo vermelho."""
    im = _capturar_imagem(larg_max, marca)
    if im is None:
        return None
    bio = io.BytesIO()
    im.save(bio, "JPEG", quality=qualidade)
    return bio.getvalue()


def _para_jpeg(im) -> bytes:
    bio = io.BytesIO()
    im.save(bio, "JPEG", quality=QUALIDADE_JPEG)
    return bio.getvalue()


def _hora(t: float) -> str:
    return time.strftime("%H:%M:%S", time.localtime(t))


# ------------------------------------------------------------------------------ gravador
class Clipe:
    """Guarda os últimos minutos da pesca. O objeto vive o programa todo; o gravador roda só durante a pesca."""

    def __init__(self, cfg: dict, fila: queue.Queue):
        self.cfg = cfg
        self.fila = fila
        self.quadros: collections.deque = collections.deque()   # (hora, jpeg)
        self.marcados: collections.deque = collections.deque(maxlen=MAX_MARCADOS)  # (hora, jpeg, legenda)
        self._parar = threading.Event()
        self._thread: threading.Thread | None = None
        self._trava = threading.Lock()

    # ------------------------------------------------------------ ajustes
    def minutos(self) -> int:
        try:
            return max(1, min(15, int(self.cfg.get("clipe_minutos", 5))))
        except (TypeError, ValueError):
            return 5

    def intervalo(self) -> float:
        """Segundos entre quadros: 1 s até 5 min de clipe, 2 s em 10 e 15 min (no máximo 450 quadros, uns 30 MB)."""
        return 1.0 if self.minutos() <= 5 else 2.0

    def ativo(self) -> bool:
        return bool(self.cfg.get("clipe_ativo", True))

    def tem_quadros(self) -> bool:
        return bool(self.quadros or self.marcados)

    def _log(self, msg: str, nivel: str = "info", **kw) -> None:
        self.fila.put(("log", (nivel, msg, kw)))

    # ------------------------------------------------------------ gravação
    def iniciar(self) -> None:
        """Começa um timelapse novo (o anterior é descartado). Não faz nada se o clipe estiver desligado."""
        self.parar()
        self.quadros = collections.deque(maxlen=math.ceil(self.minutos() * 60 / self.intervalo()))
        self.marcados.clear()
        if not self.ativo():
            return
        self._parar = threading.Event()
        self._thread = threading.Thread(target=self._laco, args=(self._parar,), daemon=True)
        self._thread.start()

    def parar(self) -> None:
        """Para de gravar. O que já foi guardado continua disponível para "Enviar clipe agora"."""
        self._parar.set()

    def _laco(self, parar: threading.Event) -> None:
        if not garantir_pillow(self._log):
            return
        if ffmpeg_exe() is None and not getattr(sys, "frozen", False):  # instala o vídeo sem atrasar a gravação
            threading.Thread(target=garantir_ffmpeg, args=(self._log,), daemon=True).start()
        while not parar.is_set():
            try:
                self.capturar()
            except Exception:  # noqa: BLE001  (um quadro perdido não pode derrubar a gravação)
                pass
            parar.wait(self.intervalo())

    def capturar(self) -> bool:
        """Guarda um quadro do timelapse agora."""
        im = _capturar_imagem()
        if im is None:
            return False
        with self._trava:
            self.quadros.append((time.time(), _para_jpeg(im)))
        return True

    def marcar(self, legenda: str) -> bool:
        """Guarda um quadro com legenda (usado nas falhas e no pedido manual). Pode ser chamado de qualquer thread."""
        if not self.ativo() or not pillow_pronto():
            return False
        try:
            im = _capturar_imagem()
        except Exception:  # noqa: BLE001
            return False
        if im is None:
            return False
        with self._trava:
            self.marcados.append((time.time(), _para_jpeg(im), legenda))
        return True

    # ------------------------------------------------------------ montagem do GIF
    def montar_clipe(self) -> tuple[bytes, str, str] | None:
        """Timelapse + quadros marcados como (dados, nome do arquivo, tipo). Vídeo MP4 se houver ffmpeg, senão GIF.
        None se não há nada gravado ou o Pillow falta."""
        if not pillow_pronto():
            return None
        with self._trava:
            tempo = list(self.quadros)
            marcados = list(self.marcados)
        if not tempo and not marcados:
            return None
        ff = ffmpeg_exe()
        if ff:
            itens = [(t, j, "", MS_TIMELAPSE) for t, j in tempo] + [(t, j, leg, MS_MARCADO) for t, j, leg in marcados]
            melhor = None
            for larg, crf in TENTATIVAS_VIDEO:
                dados = _codificar_mp4(itens, larg, crf, ff)
                if dados and (melhor is None or len(dados) < len(melhor)):
                    melhor = dados
                if dados and len(dados) <= LIMITE_BYTES:
                    return dados, "clipe.mp4", "video/mp4"
            if melhor and len(melhor) <= LIMITE_BYTES:
                return melhor, "clipe.mp4", "video/mp4"
        gif = self._montar_gif(tempo, marcados)
        return (gif, "clipe.gif", "image/gif") if gif else None

    def _montar_gif(self, tempo: list, marcados: list) -> bytes | None:
        melhor = None
        for larg, passo, so_marcados in TENTATIVAS:
            itens = []
            if not so_marcados:
                itens += [(t, j, "", 100) for t, j in tempo[::passo]]
            itens += [(t, j, leg, MS_MARCADO) for t, j, leg in marcados]
            if not itens:
                continue
            dados = _codificar_gif(itens, larg)
            if dados and (melhor is None or len(dados) < len(melhor)):
                melhor = dados
            if dados and len(dados) <= LIMITE_BYTES:
                return dados
        return melhor


def _fonte(tamanho: int):
    from PIL import ImageFont
    try:
        return ImageFont.load_default(size=tamanho)   # Pillow 10.1 ou mais novo
    except TypeError:
        return ImageFont.load_default()


def _tam_fonte(larg: int) -> int:
    return max(11, larg // 28)


def _faixa(larg: int) -> int:
    """Altura (par) da faixa preta com a legenda, que fica ABAIXO da imagem para não cobrir a barra de itens do jogo."""
    h = _tam_fonte(larg) + 14
    return h + h % 2


def _legendar(im, texto: str):
    """Devolve a imagem com uma faixa preta embaixo (hora e motivo do quadro). A imagem original fica intacta."""
    from PIL import Image, ImageDraw
    faixa = _faixa(im.width)
    nova = Image.new("RGB", (im.width, im.height + faixa), (0, 0, 0))
    nova.paste(im, (0, 0))
    ImageDraw.Draw(nova).text((6, im.height + 5), texto, font=_fonte(_tam_fonte(im.width)), fill=(255, 255, 255))
    return nova


def _codificar_gif(itens: list, larg: int) -> bytes | None:
    from PIL import Image
    reamostra = getattr(Image, "Resampling", Image).BILINEAR
    quadros, duracoes = [], []
    for t, jpeg, legenda, ms in itens:
        im = Image.open(io.BytesIO(jpeg)).convert("RGB")
        if im.width != larg:
            im = im.resize((larg, max(1, round(im.height * larg / im.width))), reamostra)
        texto = f"{legenda}  {_hora(t)}" if legenda else _hora(t)
        im = _legendar(im, texto)
        quadros.append(im.quantize(colors=CORES_GIF, method=2, dither=0))
        duracoes.append(ms)
    if not quadros:
        return None
    bio = io.BytesIO()
    quadros[0].save(bio, format="GIF", save_all=True, append_images=quadros[1:], duration=duracoes, loop=0,
                    optimize=False)
    return bio.getvalue()


def _encaixar(im, larg: int, alt: int):
    """Redimensiona mantendo a proporção e centraliza num quadro larg x alt (faixas pretas), para todo quadro ter o mesmo tamanho."""
    from PIL import Image
    reamostra = getattr(Image, "Resampling", Image).BILINEAR
    esc = min(larg / im.width, alt / im.height)
    nova = im.resize((max(1, round(im.width * esc)), max(1, round(im.height * esc))), reamostra)
    if nova.size == (larg, alt):
        return nova
    fundo = Image.new("RGB", (larg, alt), (0, 0, 0))
    fundo.paste(nova, ((larg - nova.width) // 2, (alt - nova.height) // 2))
    return fundo


def _codificar_mp4(itens: list, larg: int, crf: int, ffmpeg: str) -> bytes | None:
    """Manda os quadros crus ao ffmpeg e devolve o MP4 (H.264, toca direto no Discord e no celular)."""
    from PIL import Image
    larg -= larg % 2
    primeiro = Image.open(io.BytesIO(itens[0][1]))
    alt = max(2, round(primeiro.height * larg / primeiro.width))
    alt -= alt % 2
    faixa = _faixa(larg)
    pasta = tempfile.mkdtemp(prefix="ovo_clipe_")
    saida = os.path.join(pasta, "clipe.mp4")
    try:
        cmd = [ffmpeg, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{larg}x{alt + faixa}",
               "-r", str(FPS_VIDEO), "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", str(crf),
               "-pix_fmt", "yuv420p", "-movflags", "+faststart", saida]
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                             creationflags=0x08000000 if os.name == "nt" else 0)
        try:
            for t, jpeg, legenda, ms in itens:
                im = _encaixar(Image.open(io.BytesIO(jpeg)).convert("RGB"), larg, alt)
                im = _legendar(im, f"{legenda}  {_hora(t)}" if legenda else _hora(t))
                cru = im.tobytes()
                for _ in range(max(1, round(ms * FPS_VIDEO / 1000))):
                    p.stdin.write(cru)
            p.stdin.close()
            p.wait(timeout=180)
        except Exception:  # noqa: BLE001
            p.kill()
            return None
        if p.returncode != 0 or not os.path.isfile(saida):
            return None
        with open(saida, "rb") as f:
            return f.read()
    finally:
        shutil.rmtree(pasta, ignore_errors=True)


def texto_resumo(minutos: int) -> str:
    return T("últimos {m} min da pesca em timelapse, com um quadro marcado em cada falha.", m=minutos)
