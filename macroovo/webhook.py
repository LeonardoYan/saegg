"""Aviso opcional no Discord via webhook (só aceita endereços do próprio Discord)."""
import json
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
