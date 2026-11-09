"""Detecção do botão PARAR do minigame (leitura de cor na tela) e escolha do ponto de clique."""
from .winapi import capturar_regiao, pixel_rgb, rect_janela_roblox, user32


GRADE = [(dx, dy) for dy in (-8, -4, 0, 4, 8) for dx in (-8, -4, 0, 4, 8)]  # 25 pontos ao redor do alvo
LIMITE_CLIQUES = 30.0  # s: segurança, nunca clica por mais que isso num minigame


def ponto_calibrado(cal: dict, rect) -> tuple[int, int]:
    esq, topo, larg, alt = rect
    return int(esq + cal["rx"] * larg), int(topo + cal["ry"] * alt)


COLUNAS, LINHAS = 14, 7          # amostras da região em volta do botão (98 pontos)
MEIA_LARG, MEIA_ALT = 0.045, 0.030  # meia largura/altura da região, em fração da janela
LIMIAR_REGIAO = 0.10             # fração mínima da região com o vermelho do botão


def _vermelho_do_botao(rgb) -> bool:
    """O botão PARAR é um vermelho forte (do claro 247,112,112 ao escuro 206,44,51)."""
    r, g, b = rgb
    return r >= 170 and 25 <= g <= 130 and 25 <= b <= 130 and r - g >= 90 and r - b >= 90


def cor_e_vermelha(cor) -> bool:
    return _vermelho_do_botao(cor) or (cor[0] - (cor[1] + cor[2]) / 2) >= 60


def _limites(rect, alvo):
    """Retângulo (x0, y0, largura, altura) em pixels da região de busca."""
    _, _, larg, alt = rect
    x0 = int(alvo[0] - MEIA_LARG * larg)
    y0 = int(alvo[1] - MEIA_ALT * alt)
    return x0, y0, int(2 * MEIA_LARG * larg) + 2, int(2 * MEIA_ALT * alt) + 2


def fracao_vermelha(amostrar, rect, alvo) -> float:
    """Fração da região em volta do botão PARAR que tem o vermelho dele. `amostrar(x, y)` devolve (r, g, b) ou None."""
    _, _, larg, alt = rect
    achou = total = 0
    for i in range(COLUNAS):
        for j in range(LINHAS):
            x = int(alvo[0] + (i / (COLUNAS - 1) * 2 - 1) * MEIA_LARG * larg)
            y = int(alvo[1] + (j / (LINHAS - 1) * 2 - 1) * MEIA_ALT * alt)
            rgb = amostrar(x, y)
            if rgb:
                total += 1
                achou += _vermelho_do_botao(rgb)
    return achou / total if total else 0.0


_captura_ok = True  # vira False se a captura rápida não bater com a leitura pixel a pixel
_verif = {"bate": 0, "difere": 0}


def _desligar_captura() -> None:
    global _captura_ok
    _captura_ok = False


def _amostrador(dc, rect, alvo):
    """Leitor de pixels: copia a região de uma vez (rápido); se isso falhar, lê pixel a pixel."""
    if _captura_ok:
        x0, y0, w, h = _limites(rect, alvo)
        cap = capturar_regiao(dc, x0, y0, w, h)
        if cap is not None:
            buf, larg = cap

            def ler(px, py):
                i = ((py - y0) * larg + (px - x0)) * 4
                if not (0 <= px - x0 < larg) or i < 0 or i + 2 >= len(buf):
                    return None
                return buf[i + 2], buf[i + 1], buf[i]

            # nas primeiras vezes, confere com a leitura lenta; se as cores não baterem, desiste da captura rápida
            if _verif["bate"] < 2:
                cx, cy = x0 + w // 2, y0 + h // 2
                lento, rapido = pixel_rgb(dc, cx, cy), ler(cx, cy)
                if lento and rapido:
                    if max(abs(a - b) for a, b in zip(lento, rapido)) > 12:
                        _verif["difere"] += 1
                        if _verif["difere"] >= 3:
                            _desligar_captura()
                        return lambda px, py: pixel_rgb(dc, px, py)
                    else:
                        _verif["bate"] += 1
            return ler
    return lambda px, py: pixel_rgb(dc, px, py)


def minigame_visivel(cal: dict, tol: int) -> bool:
    """True se o botão PARAR está na tela, perto do ponto calibrado.

    Procura o vermelho do botão numa região (e não num pixel só), então aguenta pequenas diferenças de
    posição, de tamanho da janela e o degradê do botão. Se a calibração não for vermelha, usa a cor calibrada."""
    rect = rect_janela_roblox()
    if rect is None:
        return False
    x, y = ponto_calibrado(cal, rect)
    cor = cal["cor"]
    dc = user32.GetDC(None)
    if not dc:
        return False
    try:
        if cor_e_vermelha(cor):
            return fracao_vermelha(_amostrador(dc, rect, (x, y)), rect, (x, y)) >= LIMIAR_REGIAO
        acertos = 0
        for dx, dy in GRADE:
            rgb = pixel_rgb(dc, x + dx, y + dy)
            if rgb and abs(rgb[0] - cor[0]) <= tol and abs(rgb[1] - cor[1]) <= tol and abs(rgb[2] - cor[2]) <= tol:
                acertos += 1
        return acertos / len(GRADE) >= 0.30
    finally:
        user32.ReleaseDC(None, dc)


def ponto_clique(rect, alvo=None) -> tuple[int, int]:
    """Onde o mouse fica clicando: centro da janela, longe do botão PARAR."""
    esq, topo, larg, alt = rect
    candidatos = [
        (esq + larg // 2, topo + alt // 2),
        (esq + larg // 2, topo + int(alt * 0.30)),
        (esq + int(larg * 0.25), topo + alt // 2),
    ]
    if alvo is None:
        return candidatos[0]
    for x, y in candidatos:
        if abs(x - alvo[0]) > 150 or abs(y - alvo[1]) > 100:
            return x, y
    return candidatos[1]
