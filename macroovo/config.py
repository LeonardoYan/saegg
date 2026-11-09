"""Ajustes padrão e leitura/gravação da configuração."""
import json
import os
from pathlib import Path


VERSAO = "1.1"
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
    "max_falhas": 5,           # parar depois de X ciclos seguidos sem minigame (0 = nunca parar)
    "webhook_url": "",         # link do webhook do Discord para os avisos (vazio = sem aviso)
    "clipe_ativo": True,       # gravar o timelapse da pesca (vai ao Discord quando o macro para por falhas)
    "clipe_minutos": 5,        # quantos minutos de pesca o clipe cobre (1 a 15)
    "controle_ativo": False,      # obedecer comandos do Discord (bot) num canal
    "controle_token": "",         # token do bot (fica só neste computador)
    "controle_canal": "",         # ID do canal onde os comandos são lidos
    "webhook_logs": "problemas",   # o que do Registro vai ao Discord: off, problemas, importante, tudo
    "clipe_equipar": True,     # mandar o clipe ao Discord quando o macro for equipar a vara de novo
    "detectar": True,          # detectar o minigame pelo botão PARAR
    "reequipar_vara": False,   # se o minigame não aparecer, apertar a tecla do slot da vara para equipá-la de novo
    "inv_aba": None,           # posição da aba Equipamento no inventário {"rx", "ry"} (proporção da janela)
    "vara_ref_eq": None,       # aparência do espaço da vara no inventário COM a vara equipada (assinatura de cores)
    "vara_ref_gu": None,       # idem com a vara guardada
    "inv_vara": None,          # posição da vara dentro da aba Equipamento {"rx", "ry"}
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
    "idioma": "pt",            # idioma da interface: pt ou en
    "minimizar_bandeja": False,  # ao minimizar, esconder a janela na bandeja do sistema
    "mini_pos": None,          # última posição do modo mini [x, y]
    "janela_pos": None,        # última posição da janela [x, y]
    "tema": "claro",           # aparência: claro ou escuro (vale ao abrir o programa)
    "teclas": {"pesca": "f1", "ac": "f2", "calibrar": "f3", "parar": "esc", "clipe": "f4"},  # atalhos globais
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
    from .teclas import validar_teclas, completar_teclas
    cfg["teclas"] = completar_teclas(cfg.get("teclas"), PADRAO["teclas"])
    cfg["teclas"] = validar_teclas(cfg.get("teclas"), PADRAO["teclas"])
    if cfg.get("tema") not in ("claro", "escuro"):
        cfg["tema"] = "claro"
    if cfg.get("iniciar_em") not in ("janela", "mini", "bandeja"):
        cfg["iniciar_em"] = "janela"
    for chave in ("inv_aba", "inv_vara"):
        v = cfg.get(chave)
        try:
            ok = isinstance(v, dict) and 0 <= float(v["rx"]) <= 1 and 0 <= float(v["ry"]) <= 1
        except (KeyError, TypeError, ValueError):
            ok = False
        if not ok:
            cfg[chave] = None
    for chave in ("vara_ref_eq", "vara_ref_gu"):  # assinaturas: 36 células x R,G,B (0 a 255)
        v = cfg.get(chave)
        if not (isinstance(v, list) and len(v) == 108
                and all(isinstance(x, int) and not isinstance(x, bool) and 0 <= x <= 255 for x in v)):
            cfg[chave] = None
    if not isinstance(cfg.get("webhook_url"), str):
        cfg["webhook_url"] = ""
    cfg["controle_ativo"] = bool(cfg.get("controle_ativo", False))
    for chave in ("controle_token", "controle_canal"):
        if not isinstance(cfg.get(chave), str):
            cfg[chave] = ""
        cfg[chave] = cfg[chave].strip()
    if cfg.get("webhook_logs") not in ("off", "problemas", "importante", "tudo"):
        cfg["webhook_logs"] = "problemas"
    cfg["clipe_ativo"] = bool(cfg.get("clipe_ativo", True))
    cfg["clipe_equipar"] = bool(cfg.get("clipe_equipar", True))
    try:
        cfg["clipe_minutos"] = max(1, min(15, int(cfg["clipe_minutos"])))
    except (TypeError, ValueError):
        cfg["clipe_minutos"] = 5
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
