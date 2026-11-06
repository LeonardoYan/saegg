"""Paleta de cores, fontes, textos de cada etapa e lista de ajustes da interface."""
from tkinter import font as tkfont


# Duas paletas (clara e escura). A escolhida fica em Opções > Aparência e vale ao abrir o programa.
# Para mudar o visual, edite só estes dois blocos. Nomes antigos mantidos (GEMA = cor de destaque).
CLARA = dict(
    BG="#dde4ed", SUP="#ffffff", SUP2="#d3dce8", SUP3="#bfccdc", BORDA="#98a9bf",
    TEXTO="#0c1626", TEXTO2="#2b394d", TEXTO3="#4a5a73", GEMA="#1d5ccf", TEXTO_BTN="#ffffff",
    TURQUESA="#0a766c", PALHA="#8a5200", BROTO="#1b7532", LILAS="#5a3dbf", ERRO="#c0302a",
)
ESCURA = dict(
    BG="#10151e", SUP="#1a212d", SUP2="#263040", SUP3="#334057", BORDA="#46546d",
    TEXTO="#eef2f8", TEXTO2="#c4cedd", TEXTO3="#97a5bc", GEMA="#5b95ff", TEXTO_BTN="#07122b",
    TURQUESA="#3dd6c3", PALHA="#f0b35a", BROTO="#5fd283", LILAS="#a898ff", ERRO="#ff7b71",
)


def _tema_salvo() -> str:
    """Lê só o tema do arquivo de ajustes (antes de tudo, pois as cores são fixadas ao importar este módulo)."""
    try:
        import json
        import os
        from pathlib import Path
        base = Path(os.environ.get("APPDATA", Path.home()))
        dados = json.loads((base / "MacroOvo" / "config_ovo.json").read_text(encoding="utf-8"))
        return "escuro" if dados.get("tema") == "escuro" else "claro"
    except Exception:
        return "claro"


ESCURO = _tema_salvo() == "escuro"
_P = ESCURA if ESCURO else CLARA
BG, SUP, SUP2, SUP3, BORDA = _P["BG"], _P["SUP"], _P["SUP2"], _P["SUP3"], _P["BORDA"]
TEXTO, TEXTO2, TEXTO3 = _P["TEXTO"], _P["TEXTO2"], _P["TEXTO3"]
GEMA, TEXTO_BTN = _P["GEMA"], _P["TEXTO_BTN"]  # destaque: ação principal; texto sobre o destaque
TURQUESA, PALHA, BROTO, LILAS, ERRO = _P["TURQUESA"], _P["PALHA"], _P["BROTO"], _P["LILAS"], _P["ERRO"]

FONTE = "Segoe UI"
FONTE_NUM = "Segoe UI"  # fonte dos números e títulos (Bahnschrift, se existir)
MONO = "Consolas"
ESCALA = 1.0            # ajustado ao DPI da tela em App.__init__

# Janela: barra superior, barra lateral de páginas e área de conteúdo (pixels de projeto, 96 dpi)
LARG_JANELA, ALT_JANELA = 920, 620
ALT_TOPO = 56
ALT_ABAS = 46
ALT_RODAPE = 32
LARG_LATERAL = 78
GRADIENTE_HERO = ("#4d3312", "#2f2748")   # faixa de destaque do painel: âmbar para violeta escuro
PLACA_HERO = "#160f09"                    # placa escura onde fica o anel de progresso

# nome que aparece na aba (as chaves internas continuam as mesmas)
ROTULO_ABA = {"Painel": "Pescar", "Detecção": "Calibrar"}

# páginas (abas no topo): (nome, ícone)
ABAS = [
    ("Painel", "casa"),
    ("Detecção", "alvo"),
    ("AutoClick", "cursor"),
    ("Ajustes", "raio"),
    ("Opções", "engrenagem"),
    ("Registro", "lista"),
    ("Ajuda", "ajuda"),
]
SUBTITULO_ABA = {
    "Painel": "Comece por aqui: veja o que falta e controle a pesca.",
    "Detecção": "Ensine o macro a reconhecer o botão PARAR (uma vez só).",
    "AutoClick": "Clica sem parar onde o mouse estiver. Não é a pesca.",
    "Ajustes": "Velocidade, pausas e comportamento da janela. Passe o mouse no ? para ver o que cada um faz.",
    "Opções": "Atalhos do teclado, modo mini, início com o Windows e aparência.",
    "Registro": "Tudo o que o macro fez, em ordem. Se algo der errado, a pista está aqui.",
    "Ajuda": "Passo a passo e soluções para os problemas mais comuns.",
}

# Painel: o que dizer na faixa de destaque quando o macro está parado (depende do que já está pronto)
DESC_PARADO = {
    "sem_roblox": "Abra o Roblox e deixe o jogo de frente para a água.",
    "sem_calibracao": "Falta calibrar o botão PARAR. Abra a aba Calibrar e siga os 3 passos.",
    "pronto": "Tudo pronto. Fique de frente para a água e aperte F1.",
}

# Painel > Guia: (título, descrição, aba para onde o clique leva ou None)
GUIA = [
    ("Abrir o Roblox", "Deixe o jogo aberto, de frente para a água.", None),
    ("Calibrar o botão PARAR", "Só na primeira vez, leva 1 minuto. Clique aqui para ir à aba Calibrar.", "Detecção"),
    ("Apertar F1", "A pesca roda sozinha. Para parar, aperte F1 de novo ou Esc.", None),
]

# Página Ajuda
PASSOS_AJUDA = [
    "Abra o Roblox e fique de frente para a água.",
    "Na aba Calibrar, calibre o botão PARAR. Só na primeira vez.",
    "Aperte F1. O macro lança a vara, espera o minigame e clica rápido sozinho.",
    "Para parar, aperte F1 de novo. Em emergência, aperte Esc.",
]
ATALHOS_AJUDA = [
    ("F1", "Iniciar ou parar a pesca"),
    ("F2", "Iniciar ou parar o AutoClick"),
    ("F3", "Calibrar o botão PARAR"),
    ("Esc", "Parar tudo na hora"),
]
PROBLEMAS_AJUDA = [
    ("O macro não faz nada",
     "Deixe o Roblox na frente das outras janelas. Se não for isso, abra a aba Registro: ela diz o que o macro "
     "está esperando."),
    ("A vara não é lançada",
     "Aumente a Carga da vara nos Ajustes e confira se o personagem está de frente para a água."),
    ("O minigame não é detectado",
     "Calibre de novo (F3) com o minigame na tela e o mouse sobre a parte vermelha do botão PARAR. Se você mudou "
     "o tamanho da janela do jogo, calibre outra vez."),
    ("Os cliques estão rápidos ou lentos demais",
     "Mude o Intervalo entre cliques nos Ajustes. Quanto menor o intervalo, mais rápido ele clica."),
    ("Quero usar outros programas enquanto roda",
     "O macro clica com o mouse de verdade, então o Roblox precisa ficar na frente. Use o Modo mini para "
     "acompanhar sem cobrir o jogo."),
]

# Ajustes: uma frase sob o título de cada grupo
SUBTITULO_GRUPO = {
    "Lançamento e cliques": "Como o macro lança a vara e clica no minigame.",
    "Sem detecção (tempos fixos)": "Tempos usados no lugar da detecção.",
}
FIXOS_EM_USO = "Em uso agora: a detecção está desligada ou sem calibração."
FIXOS_SEM_USO = "Não usados agora: a detecção está ligada e calibrada."

# Explicação de cada ajuste e opção (aparece ao passar o mouse no ?)
AJUDA = {
    "hold_carga": "Quanto tempo o clique fica segurado para lançar a vara. Aumente se ela não chega na água; "
                  "diminua se o lançamento passa do ponto.",
    "delay_clique": "Tempo entre um clique e outro durante o minigame. Menor = clica mais rápido "
                    "(15 ms são cerca de 60 cliques por segundo).",
    "pausa": "Espera depois de cada pesca, para o aviso do prêmio sumir antes de lançar de novo. Se o macro "
             "lançar com o aviso ainda na tela, aumente.",
    "limite_espera": "Quanto tempo o macro espera o minigame aparecer depois de lançar a vara. Passou disso, ele "
                     "tenta de novo.",
    "tolerancia": "O quanto a cor lida pode variar da cor calibrada. Aumente se o macro não acha o botão PARAR; "
                  "diminua se ele confunde com outras coisas vermelhas.",
    "espera_minigame": "Só vale com a detecção desligada ou sem calibração: tempo de espera até o minigame aparecer.",
    "duracao_cliques": "Só vale com a detecção desligada ou sem calibração: por quanto tempo clicar no minigame.",
    "ac_intervalo": "Tempo entre um clique e outro, em horas, minutos, segundos e milissegundos. Menor = clica mais rápido. 100 ms são 10 cliques por segundo.",
    "ac_atraso": "Tempo de espera depois de iniciar, para você levar o mouse até o alvo.",
    "ac_limite": "O AutoClick para sozinho depois desse número de cliques. Zero = clica até você parar.",
    "detectar": "Liga a leitura do botão vermelho PARAR do minigame. Com ela o macro sabe quando o minigame começa e "
                "acaba. Precisa de calibração (nesta aba).",
    "so_roblox": "O macro só clica enquanto o Roblox estiver na frente. Evita clicar em outros programas por "
                 "engano. Recomendado.",
    "sempre_no_topo": "Mantém esta janela na frente das outras, para você acompanhar o macro.",
    "minimizar_bandeja": "Ao minimizar, a janela some e o ícone fica na bandeja do sistema, perto do relógio. "
                         "Clique no ícone para abrir de novo.",
    "ac_pos_fixa": "O AutoClick leva o cursor ao mesmo ponto da tela antes de cada clique. Enquanto ele roda, o cursor "
                   "fica preso nesse ponto. Use Parar se eu mexer o mouse para poder retomar o controle.",
    "ac_parar_mouse": "Para o AutoClick sozinho se você afastar o mouse do ponto de clique. Pequenos tremores "
                      "não contam: só um movimento maior que a distância escolhida.",
    "ac_dist_mouse": "Quantos pixels o mouse precisa se afastar para o AutoClick parar. 150 px é um movimento "
                     "claro de propósito; aumente se parar sem querer.",
    "mini_opacidade": "Deixa a janelinha do modo mini mais transparente para não atrapalhar o jogo. 100% é totalmente opaca.",
    "iniciar_windows": "O programa abre sozinho quando você liga o computador. Dá para desligar aqui a qualquer hora.",
    "tema": "Claro ou escuro. A mudança vale na próxima vez que o programa abrir.",
    "ac_so_roblox": "O AutoClick só clica enquanto o Roblox estiver na frente. Se o Roblox sair da frente, ele "
                    "pausa.",
}
AJUDA_ACOES = {  # atalhos do painel
    "Calibrar": "Ensina o macro a achar o botão vermelho PARAR do minigame. Faça uma vez, com o minigame na tela e "
                "o mouse sobre o botão.",
    "AutoClick": "Clica sem parar onde o mouse estiver, em qualquer jogo ou programa. Não é a pesca.",
    "Modo mini": "Troca esta janela por uma janelinha que fica por cima do jogo, só com o essencial.",
    "Abrir pasta": "Abre a pasta onde ficam salvos os seus ajustes e a calibração.",
    "Parar tudo": "Para a pesca e o AutoClick na hora. Também funciona com a tecla Esc.",
}

COR_FASE = {
    "Parado": TEXTO3,
    "Aguardando o Roblox": TEXTO2,
    "Lançando a vara": PALHA,
    "Aguardando o minigame": TURQUESA,
    "Clicando": BROTO,
    "Pausa": LILAS,
}
DESC_FASE = {
    "Parado": "Abra o Roblox, fique de frente para a água e aperte F1.",
    "Aguardando o Roblox": "Deixe a janela do Roblox aberta e em primeiro plano.",
    "Lançando a vara": "Segurando o clique para carregar a vara.",
    "Aguardando o minigame": "Esperando o botão PARAR aparecer.",
    "Clicando": "Clicando rápido no minigame.",
    "Pausa": "Esperando o aviso do prêmio sumir.",
}
DESC_AC = {
    "Parado": "Leve o mouse ao alvo e aperte F2, ou defina uma posição fixa.",
    "Contagem": "Leve o mouse até onde quer clicar.",
    "Clicando": "Clicando na posição do mouse. Aperte F2 ou Esc para parar.",
}
COR_LOG = {"info": TEXTO2, "ok": BROTO, "aviso": PALHA, "erro": ERRO}

# chave, rótulo, mínimo, máximo, passo do controle deslizante, passo ao digitar, unidade
AJUSTES = [
    ("hold_carga", "Carga da vara", 100, 5000, 50, 1, "ms"),
    ("delay_clique", "Intervalo entre cliques", 1, 200, 1, 1, "ms"),
    ("pausa", "Pausa entre ciclos", 0.0, 20.0, 0.1, 0.1, "s"),
    ("limite_espera", "Tempo máx. de espera", 5, 60, 1, 1, "s"),
    ("tolerancia", "Tolerância de cor", 10, 120, 1, 1, ""),
    ("espera_minigame", "Espera fixa (sem detecção)", 1.0, 20.0, 0.1, 0.1, "s"),
    ("duracao_cliques", "Cliques fixos (sem detecção)", 0.5, 30.0, 0.1, 0.1, "s"),
]
AJUSTES_AC = [
    ("ac_intervalo", "Intervalo entre cliques", 1, 1000, 1, 1, "ms"),
    ("ac_atraso", "Atraso para começar", 0.0, 10.0, 0.5, 0.1, "s"),
    ("ac_limite", "Limite de cliques", 0, 10000, 100, 1, "cliques"),
]
GRUPOS = [  # grupos da página Ajustes
    ("Lançamento e cliques", ("hold_carga", "delay_clique", "pausa")),
    ("Sem detecção (tempos fixos)", ("espera_minigame", "duracao_cliques")),
]
AJUSTES_DETECCAO = ("limite_espera", "tolerancia")  # ficam na página Detecção, junto da calibração


def px(v: float) -> int:
    """Converte pixels de projeto (96 dpi) para pixels reais da tela."""
    return max(1, int(round(v * ESCALA)))


def F(tam: int, peso: str = "normal") -> tuple:
    return (FONTE, tam, peso)


def FN(tam: int) -> tuple:
    peso = "normal" if any(s in FONTE_NUM for s in ("SemiBold", "Semibold")) else "bold"
    return (FONTE_NUM, tam, peso)


def escolher_fontes() -> None:
    """Usa Bahnschrift nos números (Windows 10+) e Consolas no registro, se estiverem instaladas."""
    global FONTE, FONTE_NUM, MONO
    try:
        nomes = set(tkfont.families())
    except Exception:
        return
    for nome in ("Bahnschrift SemiBold", "Bahnschrift", "Segoe UI Semibold"):
        if nome in nomes:
            FONTE_NUM = nome
            break
    if "Segoe UI" in nomes:
        FONTE = "Segoe UI"
    if "Consolas" not in nomes:
        for nome in ("DejaVu Sans Mono", "Courier New"):
            if nome in nomes:
                MONO = nome
                break


def misturar(c1: str, c2: str, t: float) -> str:
    """Mistura duas cores hexadecimais (t=0 devolve c1, t=1 devolve c2)."""
    a = [int(c1[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(c2[i:i + 2], 16) for i in (1, 3, 5)]
    return "#%02x%02x%02x" % tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def resumir(msg: str, n: int = 56) -> str:
    msg = " ".join(msg.split())
    return msg if len(msg) <= n else msg[: n - 1] + "…"
