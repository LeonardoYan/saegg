"""Teclas de atalho que o usuário pode escolher (globais: funcionam com outra janela na frente)."""

# id interno (formato do pynput sem os <>) -> (nome mostrado, nome da tecla no tkinter)
TECLAS = {f"f{n}": (f"F{n}", f"F{n}") for n in range(1, 13)}
TECLAS.update({
    "esc": ("Esc", "Escape"),
    "pause": ("Pause", "Pause"),
    "insert": ("Insert", "Insert"),
    "home": ("Home", "Home"),
    "end": ("End", "End"),
    "page_up": ("PgUp", "Prior"),
    "page_down": ("PgDn", "Next"),
})
POR_KEYSYM = {tk: ident for ident, (_nome, tk) in TECLAS.items()}

# ações: (chave no ajuste, nome padrão da tecla no texto do programa, texto da linha em Opções)
ACOES = [
    ("pesca", "F1", "Iniciar ou parar a pesca"),
    ("ac", "F2", "Iniciar ou parar o AutoClick"),
    ("calibrar", "F3", "Calibrar o botão PARAR"),
    ("parar", "Esc", "Parar tudo na hora"),
    ("clipe", "F4", "Enviar o clipe da pesca ao Discord"),
]


def nome_tecla(ident: str) -> str:
    return TECLAS.get(ident, (ident.upper(), ""))[0]


def validar_teclas(valor, padrao: dict) -> dict:
    """Aceita só teclas conhecidas e sem repetição; qualquer erro devolve os atalhos padrão."""
    try:
        res = {k: str(valor[k]) for k in padrao}
        if all(v in TECLAS for v in res.values()) and len(set(res.values())) == len(res):
            return res
    except Exception:
        pass
    return dict(padrao)


def completar_teclas(valor, padrao: dict) -> dict:
    """Configurações antigas não têm os atalhos novos: acrescenta cada um com a tecla padrão (ou outra livre)."""
    if not isinstance(valor, dict):
        return valor
    res = dict(valor)
    usadas = {str(v) for v in res.values()}
    for acao, tecla_padrao in padrao.items():
        if acao in res:
            continue
        livre = tecla_padrao if tecla_padrao not in usadas else next((t for t in TECLAS if t not in usadas), None)
        if livre:
            res[acao] = livre
            usadas.add(livre)
    return res
