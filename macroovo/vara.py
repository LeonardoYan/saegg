"""Verifica, olhando o inventário, se a vara já está equipada (clicar nela de novo a guardaria).

O usuário ensina duas "aparências" do espaço da vara no inventário: com a vara equipada e com ela guardada. Cada uma é
uma assinatura pequena: a média de cor de uma grade 6x6 em volta da posição marcada. Na hora de equipar, o macro mede o
espaço de novo e vê de qual das duas aparências ele se parece mais.
"""
from .winapi import capturar_regiao, user32

GRADE = 6
LIMIAR_SO_EQUIPADA = 14.0    # só há a aparência "equipada": diferença média máxima para considerar equipada
LIMIAR_IGUAIS = 6.0          # equipada e guardada com diferença menor que isto = o jogo não distingue os dois estados
LIMIAR_DESCONHECIDO = 45.0   # longe das duas aparências: o espaço mostra outra coisa (a vara mudou de lugar?)


def meia_area(alt_janela: int) -> int:
    """Metade do lado da área medida, em pixels (proporcional à janela)."""
    return max(10, round(alt_janela * 0.035))


def assinatura_de_bgra(dados, lado: int) -> list[int]:
    """Média de R, G, B de cada célula da grade, de um quadrado lado x lado em bytes B,G,R,A."""
    cel = max(1, lado // GRADE)
    sig: list[int] = []
    for gy in range(GRADE):
        for gx in range(GRADE):
            b = g = r = n = 0
            for y in range(gy * cel, (gy + 1) * cel):
                ini = (y * lado + gx * cel) * 4
                seg = dados[ini: ini + cel * 4]
                b += sum(seg[0::4])
                g += sum(seg[1::4])
                r += sum(seg[2::4])
                n += cel
            sig += [round(r / n), round(g / n), round(b / n)]
    return sig


def capturar_assinatura(cx: int, cy: int, alt_janela: int):
    """Assinatura da área em volta de (cx, cy), em coordenadas da tela. None se a captura falhar."""
    meia = meia_area(alt_janela)
    lado = meia * 2
    dc = user32.GetDC(None)
    try:
        r = capturar_regiao(dc, cx - meia, cy - meia, lado, lado)
    finally:
        user32.ReleaseDC(None, dc)
    if r is None:
        return None
    return assinatura_de_bgra(bytes(r[0]), lado)


def distancia(a, b) -> float:
    """Diferença média por canal (0 a 255) entre duas assinaturas."""
    return sum(abs(x - y) for x, y in zip(a, b)) / max(1, min(len(a), len(b)))


def classificar(atual, ref_eq, ref_gu):
    """True = vara equipada, False = guardada, None = não dá para saber (sem calibração ou aparência desconhecida)."""
    if not atual or not ref_eq:
        return None
    d_eq = distancia(atual, ref_eq)
    if ref_gu:
        if distancia(ref_eq, ref_gu) < LIMIAR_IGUAIS:
            return None
        d_gu = distancia(atual, ref_gu)
        if min(d_eq, d_gu) > LIMIAR_DESCONHECIDO:
            return None
        return d_eq < d_gu
    return d_eq < LIMIAR_SO_EQUIPADA


def assinatura_valida(v) -> bool:
    return (isinstance(v, list) and len(v) == GRADE * GRADE * 3
            and all(isinstance(x, int) and not isinstance(x, bool) and 0 <= x <= 255 for x in v))
