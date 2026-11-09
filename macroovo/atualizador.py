"""Verificação de versão nova no GitHub (só leitura; nada é baixado nem instalado sozinho)."""
import json
import os
import re
import shutil
import sys
import tempfile
import threading
import urllib.request
import zipfile

from .config import VERSAO

# Para trocar de repositório, mude só esta linha.
REPOSITORIO = "LeonardoYan/saegg"
URL_API = f"https://api.github.com/repos/{REPOSITORIO}/releases/latest"
URL_PAGINA = f"https://github.com/{REPOSITORIO}/releases/latest"
PREFIXO_DOWNLOAD = f"https://github.com/{REPOSITORIO}/releases/download/"
LIMITE_ZIP = 50 * 1024 * 1024  # recusa arquivos maiores que 50 MB
PASTA_PROGRAMA = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Arquivos que a atualização troca. Nada além disso é tocado (os ajustes ficam em %APPDATA%).
ARQUIVOS = ("ovo_macro.py", "Abrir.bat", "criar_exe.bat", "icone.ico", "LEIA-ME.txt")


def pode_instalar() -> bool:
    """Só a versão em Python (Abrir.bat) se atualiza sozinha; o .exe precisa ser gerado de novo."""
    return not getattr(sys, "frozen", False) and os.access(PASTA_PROGRAMA, os.W_OK)


def _numeros(v: str) -> tuple:
    return tuple(int(n) for n in re.findall(r"\d+", v)[:4])


def mais_nova(remota: str, local: str = VERSAO) -> bool:
    a, b = _numeros(remota), _numeros(local)
    return bool(a) and a > b


def consultar() -> tuple:
    """Retorna (versao_remota, url_da_pagina, url_do_zip). Levanta exceção se não conseguir consultar."""
    req = urllib.request.Request(URL_API, headers={"User-Agent": f"RoubeUmOvo/{VERSAO}",
                                                   "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req, timeout=8) as r:  # noqa: S310 (URL fixa https)
        dado = json.loads(r.read().decode("utf-8"))
    tag = str(dado.get("tag_name", "")).lstrip("vV")
    zip_url = ""
    for a in dado.get("assets", []):
        u = str(a.get("browser_download_url", ""))
        if u.lower().endswith(".zip") and u.startswith(PREFIXO_DOWNLOAD):
            zip_url = u
            break
    return tag, URL_PAGINA, zip_url


def consultar_em_segundo_plano(fila, manual: bool) -> None:
    """Coloca ('atualizacao', (status, versao, manual)) na fila. status: nova | atual | erro."""
    def trabalho():
        try:
            tag, _, zip_url = consultar()
            if not tag:
                raise ValueError("sem versão")
            fila.put(("atualizacao", ("nova" if mais_nova(tag) else "atual", tag, manual, zip_url)))
        except Exception:  # noqa: BLE001
            fila.put(("atualizacao", ("erro", "", manual, "")))
    threading.Thread(target=trabalho, daemon=True).start()


def baixar(url: str, destino: str) -> None:
    if not url.startswith(PREFIXO_DOWNLOAD):
        raise ValueError("endereço de download inválido")
    req = urllib.request.Request(url, headers={"User-Agent": f"RoubeUmOvo/{VERSAO}"})
    total = 0
    with urllib.request.urlopen(req, timeout=20) as r, open(destino, "wb") as f:  # noqa: S310
        while True:
            bloco = r.read(65536)
            if not bloco:
                break
            total += len(bloco)
            if total > LIMITE_ZIP:
                raise ValueError("arquivo grande demais")
            f.write(bloco)


def _raiz_do_programa(pasta: str) -> str:
    for atual, _dirs, arqs in os.walk(pasta):
        if "ovo_macro.py" in arqs and os.path.isfile(os.path.join(atual, "macroovo", "__init__.py")):
            return atual
    raise ValueError("o zip não contém o programa")


def instalar_zip(caminho_zip: str, destino: str = PASTA_PROGRAMA) -> None:
    """Extrai o zip (recusando caminhos suspeitos), guarda cópia da versão atual e troca os arquivos."""
    with tempfile.TemporaryDirectory() as tmp:
        base = os.path.realpath(tmp)
        with zipfile.ZipFile(caminho_zip) as z:
            for nome in z.namelist():
                alvo = os.path.realpath(os.path.join(base, nome))
                if os.path.isabs(nome) or not (alvo == base or alvo.startswith(base + os.sep)):
                    raise ValueError("zip com caminho inválido")
            z.extractall(base)
        raiz = _raiz_do_programa(base)
        # cópia de segurança da versão atual
        copia = os.path.join(destino, "_versao_anterior")
        shutil.rmtree(copia, ignore_errors=True)
        os.makedirs(copia)
        for nome in ARQUIVOS:
            if os.path.isfile(os.path.join(destino, nome)):
                shutil.copy2(os.path.join(destino, nome), copia)
        if os.path.isdir(os.path.join(destino, "macroovo")):
            shutil.copytree(os.path.join(destino, "macroovo"), os.path.join(copia, "macroovo"),
                            ignore=shutil.ignore_patterns("__pycache__"))
        # troca
        novo_pkg = os.path.join(destino, "macroovo_novo")
        shutil.rmtree(novo_pkg, ignore_errors=True)
        shutil.copytree(os.path.join(raiz, "macroovo"), novo_pkg, ignore=shutil.ignore_patterns("__pycache__"))
        for nome in ARQUIVOS:
            if os.path.isfile(os.path.join(raiz, nome)):
                shutil.copy2(os.path.join(raiz, nome), os.path.join(destino, nome))
        shutil.rmtree(os.path.join(destino, "macroovo"), ignore_errors=True)
        os.rename(novo_pkg, os.path.join(destino, "macroovo"))


def instalar_em_segundo_plano(fila, url: str) -> None:
    """Baixa e instala. Põe ('instalacao', (ok, mensagem)) na fila."""
    def trabalho():
        try:
            with tempfile.TemporaryDirectory() as tmp:
                zip_ = os.path.join(tmp, "novo.zip")
                baixar(url, zip_)
                instalar_zip(zip_)
            fila.put(("instalacao", (True, "")))
        except Exception as e:  # noqa: BLE001
            fila.put(("instalacao", (False, str(e))))
    threading.Thread(target=trabalho, daemon=True).start()


def reabrir_depois() -> None:
    """Inicia uma nova cópia do programa daqui a 2 s (tempo da cópia atual fechar). Sem cmd e sem aspas."""
    import subprocess
    pythonw = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
    if not os.path.isfile(pythonw):
        pythonw = sys.executable
    script = os.path.join(PASTA_PROGRAMA, "ovo_macro.py")
    ajudante = ("import subprocess, sys, time; time.sleep(2); "
                "subprocess.Popen([sys.argv[1], sys.argv[2]], cwd=sys.argv[3])")
    subprocess.Popen([pythonw, "-c", ajudante, pythonw, script, PASTA_PROGRAMA],  # noqa: S603
                     cwd=PASTA_PROGRAMA, creationflags=0x00000008 | 0x08000000, close_fds=True)
