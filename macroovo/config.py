"""Ajustes padrão e leitura/gravação da configuração."""
import json
import os
from pathlib import Path


VERSAO = "1.0"
_BASE = Path(os.environ.get("APPDATA", Path.home()))
PASTA_CONFIG = _BASE / "MacroOvo"  # nunca na área de trabalho
CONFIG_PATH = PASTA_CONFIG / "config_ovo.json"
CONFIG_ANTIGO = _BASE / "MacroPesca" / "config_pesca.json"  # versões 3.x: os ajustes e a calibração são aproveitados
PADRAO = {
    "hold_carga": 1150,        # ms segurando o clique para carregar a vara
    "espera_minigame": 6.5,    # s de espera fixa (usada só se a detecção estiver desligada/sem calibração)
    "duracao_cliques": 3.0,    # s de cliques fixos (idem)
    "delay_clique": 15,        # ms entre cliques
    "pausa": 3.5,              # s de pausa após o minigame acabar (o aviso do prêmio dura ~3-4 s)
    "limite_espera": 20,       # s máximos esperando o minigame aparecer (detecção)
    "tolerancia": 45,          # tolerância de cor (0-255 por canal) na detecção
    "detectar": True,          # detectar o minigame pelo botão PARAR
    "so_roblox": True,         # só rodar com o Roblox em primeiro plano
    "sempre_no_topo": True,    # janela do programa sempre por cima
    "ac_intervalo": 100,       # AutoClick: ms entre cliques
    "ac_atraso": 3.0,          # AutoClick: s de espera antes de começar (tempo de levar o mouse ao alvo)
    "ac_limite": 0,            # AutoClick: parar após X cliques (0 = sem limite)
    "ac_botao": "esquerdo",    # AutoClick: botão do mouse (esquerdo, direito ou meio)
    "ac_so_roblox": False,     # AutoClick: só clicar com o Roblox em primeiro plano
    "ac_pos_fixa": False,      # AutoClick: clicar sempre no mesmo ponto da tela
    "ac_pos": None,            # AutoClick: o ponto escolhido [x, y]
    "ac_parar_mouse": False,   # AutoClick: parar se o mouse for movido para longe
    "ac_dist_mouse": 150,      # AutoClick: distância (px) que conta como "mexeu o mouse"
    "idioma": "pt",            # idioma da interface: pt ou en
    "minimizar_bandeja": False,  # ao minimizar, esconder a janela na bandeja do sistema
    "mini_pos": None,          # última posição do modo mini [x, y]
    "janela_pos": None,        # última posição da janela [x, y]
    "tema": "claro",           # aparência: claro ou escuro (vale ao abrir o programa)
    "teclas": {"pesca": "f1", "ac": "f2", "calibrar": "f3", "parar": "esc"},  # atalhos globais
    "iniciar_windows": False,  # abrir junto com o Windows
    "iniciar_em": "janela",    # como abrir: janela, mini ou bandeja
    "mini_opacidade": 100,     # opacidade do modo mini (40 a 100 %)
    "cal": None,              # calibração do botão PARAR: {rx, ry, cor, larg, alt}
}


def carregar_config() -> dict:
    cfg = dict(PADRAO)
    for caminho in (CONFIG_PATH, CONFIG_ANTIGO):  # na primeira vez usa o arquivo da versão antiga, se existir
        try:
            dados = json.loads(caminho.read_text(encoding="utf-8"))
            cfg.update({k: v for k, v in dados.items() if k in PADRAO})
            break
        except Exception:
            continue
    # valores vindos do arquivo podem estar errados: volta ao padrão em vez de quebrar a interface
    from .teclas import validar_teclas
    cfg["teclas"] = validar_teclas(cfg.get("teclas"), PADRAO["teclas"])
    if cfg.get("tema") not in ("claro", "escuro"):
        cfg["tema"] = "claro"
    if cfg.get("iniciar_em") not in ("janela", "mini", "bandeja"):
        cfg["iniciar_em"] = "janela"
    try:
        cfg["mini_opacidade"] = max(40, min(100, int(cfg["mini_opacidade"])))
    except (TypeError, ValueError):
        cfg["mini_opacidade"] = 100
    return cfg


def salvar_config(cfg: dict) -> None:
    try:
        PASTA_CONFIG.mkdir(parents=True, exist_ok=True)
        CONFIG_PATH.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
    except Exception:
        pass
