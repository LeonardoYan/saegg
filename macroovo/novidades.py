"""Resumo das atualizações mostrado no painel (cartão Novidades).

Para registrar uma atualização nova, acrescente uma linha NO TOPO da lista:
    (versão, data, tipo, texto)
Tipos: "novo", "melhoria" ou "correcao". O texto é escrito em português; se quiser a tradução em inglês,
coloque a frase também no dicionário EN do arquivo idioma.py.
"""

NOVIDADES = [
    ("1.0", "06/11/2026", "novo", "Lançamento oficial do Roube um Ovo."),
]

# tipo -> rótulo da etiqueta
TIPOS = {"novo": "NOVO", "melhoria": "MELHORIA", "correcao": "CORREÇÃO"}
