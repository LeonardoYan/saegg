"""Aviso opcional no Discord via webhook (só aceita endereços do próprio Discord)."""
import json
import uuid
import urllib.error
import urllib.parse
import urllib.request

from .config import VERSAO
from .idioma import T


HOSTS_WEBHOOK = {"discord.com", "discordapp.com", "ptb.discord.com", "canary.discord.com"}


def url_webhook_valida(url: str) -> bool:
    """Só aceita links de webhook do próprio Discord, para o macro nunca enviar dados a outro endereço."""
    try:
        u = urllib.parse.urlparse(url)
        return u.scheme == "https" and u.hostname in HOSTS_WEBHOOK and u.path.startswith("/api/webhooks/")
    except ValueError:
        return False


def enviar_webhook(url: str, texto: str) -> tuple[bool, str]:
    """Envia uma mensagem de texto ao webhook. Retorna (deu certo, detalhe). Nunca marca ninguém (@)."""
    if not url_webhook_valida(url):
        return False, T("o link não parece um webhook do Discord (começa com https://discord.com/api/webhooks/)")
    corpo = json.dumps({"content": texto[:1900], "allowed_mentions": {"parse": []}}).encode("utf-8")
    req = urllib.request.Request(
        url, data=corpo, method="POST",
        headers={"Content-Type": "application/json", "User-Agent": f"MacroOvo/{VERSAO}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=8) as r:
            return 200 <= r.status < 300, T("resposta {status}", status=r.status)
    except urllib.error.HTTPError as e:
        return False, T("o Discord respondeu {code} (o webhook foi apagado ou o link está incompleto?)", code=e.code)
    except Exception as e:  # noqa: BLE001
        return False, str(e)


def montar_multipart(texto: str, nome: str, dados: bytes, tipo: str) -> tuple[bytes, str]:
    """Corpo multipart/form-data de uma mensagem do Discord com um arquivo anexado (sem marcar ninguém)."""
    limite = uuid.uuid4().hex
    cab = json.dumps({"content": texto[:1900], "allowed_mentions": {"parse": []}})
    corpo = b"".join([
        f"--{limite}\r\nContent-Disposition: form-data; name=\"payload_json\"\r\n"
        f"Content-Type: application/json\r\n\r\n{cab}\r\n".encode("utf-8"),
        f"--{limite}\r\nContent-Disposition: form-data; name=\"files[0]\"; filename=\"{nome}\"\r\n"
        f"Content-Type: {tipo}\r\n\r\n".encode("utf-8"),
        dados,
        f"\r\n--{limite}--\r\n".encode("utf-8"),
    ])
    return corpo, limite


LIMITE_ARQUIVO = 9_500_000  # o Discord aceita até 10 MB por mensagem de webhook


def enviar_arquivo_webhook(url: str, texto: str, nome: str, dados: bytes, tipo: str = "image/gif") -> tuple[bool, str]:
    """Envia uma mensagem com um arquivo anexado (o clipe). Retorna (deu certo, detalhe). Nunca marca ninguém (@)."""
    if not url_webhook_valida(url):
        return False, T("o link não parece um webhook do Discord (começa com https://discord.com/api/webhooks/)")
    if len(dados) > LIMITE_ARQUIVO:
        return False, T("o clipe ficou grande demais para o Discord ({mb:.1f} MB)", mb=len(dados) / 1e6)
    corpo, limite = montar_multipart(texto, nome, dados, tipo)
    req = urllib.request.Request(
        url, data=corpo, method="POST",
        headers={"Content-Type": f"multipart/form-data; boundary={limite}", "User-Agent": f"MacroOvo/{VERSAO}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return 200 <= r.status < 300, T("resposta {status}", status=r.status)
    except urllib.error.HTTPError as e:
        if e.code == 413:
            return False, T("o Discord recusou o arquivo por ser grande demais")
        return False, T("o Discord respondeu {code} (o webhook foi apagado ou o link está incompleto?)", code=e.code)
    except Exception as e:  # noqa: BLE001
        return False, str(e)
