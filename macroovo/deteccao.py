"""Detecção do botão PARAR do minigame (leitura de cor na tela) e escolha do ponto de clique."""
from .winapi import pixel_rgb, rect_janela_roblox, user32


GRADE = [(dx, dy) for dy in (-8, -4, 0, 4, 8) for dx in (-8, -4, 0, 4, 8)]  # 25 pontos ao redor do alvo
LIMITE_CLIQUES = 30.0  # s: segurança, nunca clica por mais que isso num minigame


def ponto_calibrado(cal: dict, rect) -> tuple[int, int]:
    esq, topo, larg, alt = rect
    return int(esq + cal["rx"] * larg), int(topo + cal["ry"] * alt)


def minigame_visivel(cal: dict, tol: int) -> bool:
    """True se a cor do botão PARAR está no ponto calibrado (o minigame está na tela)."""
    rect = rect_janela_roblox()
    if rect is None:
        return False
    x, y = ponto_calibrado(cal, rect)
    cor = cal["cor"]
    dc = user32.GetDC(None)
    if not dc:
        return False
    try:
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
