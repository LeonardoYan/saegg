"""Janela principal: barra lateral com as páginas, atalhos globais e a ligação da interface com os workers."""
import ctypes
import math
import os
import queue
import time
import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk

from pynput import keyboard

from . import tema
from .config import carregar_config, PADRAO, PASTA_CONFIG, salvar_config, VERSAO
from .bandeja import Bandeja
from .deteccao import GRADE, minigame_visivel
from .icone import ICONE_PNG
from .idioma import atual as idioma_atual, definir as definir_idioma, definir_teclas, IDIOMAS, T
from .teclas import ACOES, nome_tecla, POR_KEYSYM, TECLAS
from .mini import JanelaMini
from .novidades import NOVIDADES, TIPOS
from .tema import (
    ABAS,
    AJUDA,
    AJUDA_ACOES,
    AJUSTES,
    AJUSTES_AC,
    AJUSTES_DETECCAO,
    ALT_JANELA,
    ALT_ABAS,
    ALT_RODAPE,
    ALT_TOPO,
    ATALHOS_AJUDA,
    BG,
    BORDA,
    BROTO,
    COR_FASE,
    COR_LOG,
    DESC_AC,
    DESC_FASE,
    DESC_PARADO,
    ERRO,
    escolher_fontes,
    F,
    FIXOS_EM_USO,
    FIXOS_SEM_USO,
    FN,
    GEMA,
    GRUPOS,
    GUIA,
    LARG_JANELA,
    LILAS,
    misturar,
    PALHA,
    PASSOS_AJUDA,
    PROBLEMAS_AJUDA,
    px,
    resumir,
    ROTULO_ABA,
    SUBTITULO_ABA,
    SUBTITULO_GRUPO,
    SUP,
    TEXTO_BTN,
    SUP2,
    SUP3,
    TEXTO,
    TEXTO2,
    TEXTO3,
    TURQUESA,
)
from .widgets import (
    Aba,
    AjudaIcone,
    Anel,
    Botao,
    cabecalho_cartao,
    Campo,
    CampoIntervalo,
    cartao,
    Dica,
    DialogoFechar,
    etiqueta,
    Logo,
    Marcador,
    Mosaico,
    tecla,
    texto_duracao,
    titulo_secao,
    Toggle,
)
from .winapi import barra_de_titulo_escura, definir_iniciar_com_windows, iniciar_com_windows_ativo, ja_esta_aberto, mostrar_janela_existente, pixel_rgb, posicao_cursor, rect_janela_roblox, user32
from .workers import AutoClicker, Pescador

# nível do registro -> (rótulo da etiqueta, cor do texto, cor de fundo)
NIVEIS = {
    "info": ("INFO", TEXTO2, SUP3),
    "ok": ("OK", BROTO, misturar(SUP, BROTO, 0.2)),
    "aviso": ("AVISO", PALHA, misturar(SUP, PALHA, 0.2)),
    "erro": ("ERRO", ERRO, misturar(SUP, ERRO, 0.2)),
}
NIVEIS_NOVIDADE = {  # tipo da novidade -> (rótulo, cor do texto, cor de fundo)
    "novo": ("NOVO", BROTO, misturar(SUP, BROTO, 0.2)),
    "melhoria": ("MELHORIA", TURQUESA, misturar(SUP, TURQUESA, 0.2)),
    "correcao": ("CORREÇÃO", PALHA, misturar(SUP, PALHA, 0.2)),
}
LINHAS_ATIVIDADE = 3
LINHAS_NOVIDADES = 3


class _Oculto:
    """Faz o papel de um elemento que não existe mais na tela (assim o resto do código continua igual)."""

    def definir(self, *_a, **_k) -> None:
        pass

    ajustar = definir_legenda = definir


class EstadoAtual(tk.Frame):
    """Título grande da etapa atual e uma frase explicando o que está acontecendo."""

    def __init__(self, pai):
        super().__init__(pai, bg=SUP)
        self._tit = tk.Label(self, text="", font=FN(22), bg=SUP, fg=TEXTO, anchor="w")
        self._tit.pack(fill="x", pady=(px(14), 0))
        self._desc = tk.Label(self, text="", font=F(10), bg=SUP, fg=TEXTO2, anchor="nw", justify="left",
                              wraplength=px(210))
        self._desc.pack(fill="x", pady=(px(4), 0))

    def definir(self, titulo=None, cor=None, descricao=None) -> None:
        if titulo is not None:
            self._tit.configure(text=titulo)
        if cor is not None:
            self._tit.configure(fg=cor)
        if descricao is not None:
            self._desc.configure(text=descricao)


class App:
    def __init__(self, root: tk.Tk):
        self.root = root
        try:
            tema.ESCALA = max(1.0, root.winfo_fpixels("1i") / 96.0)
        except Exception:
            tema.ESCALA = 1.0
        escolher_fontes()

        self.cfg = carregar_config()
        definir_idioma(self.cfg.get("idioma"))
        definir_teclas(self._mapa_teclas())
        self._capturando: str | None = None   # ação cujo atalho está sendo escolhido em Opções
        self.historico_log: list = []   # (hora, nível, texto-base, argumentos): permite traduzir o registro depois
        self.bandeja: Bandeja | None = None
        self.mini: JanelaMini | None = None
        self.aba_atual = "Painel"
        self._restaurar_pendente = False   # "Restaurar padrões" espera um segundo clique para confirmar
        self.nov_pag = 0
        self._pilula = ("Parado", TEXTO3)
        self._ac_vis = ("Parado", "Parado", TEXTO3, {})
        self._lamp = None
        self.fila: queue.Queue = queue.Queue()
        self.worker: Pescador | None = None
        self.ac_worker: AutoClicker | None = None
        self.ac_cliques = 0
        self.ac_t0 = 0.0
        self.ac_atraso_fim = 0.0

        self.ciclos = 0
        self.cliques_base = 0
        self.cliques_ciclo = 0
        self.cps = 0.0
        self.cps_max = 0.0
        self.tempo_sessao = 0.0
        self.inicio_execucao = 0.0
        self.fase_nome = "Parado"
        self.fase_ini = 0.0
        self.fase_dur = 0.0
        self.fase_texto = ""
        self._desc = DESC_FASE["Parado"]
        self._salvar_id = None
        self._n = 0
        self._pulso = 0.0
        self._roblox_aberto = None
        self._lampadas: list[tk.Label] = []

        root.title(f"{T('Roube um Ovo')}  v{VERSAO}")
        root.configure(bg=BG)
        root.resizable(False, False)
        root.geometry(f"{px(LARG_JANELA)}x{px(ALT_JANELA)}")
        root.attributes("-topmost", bool(self.cfg["sempre_no_topo"]))
        try:
            self._icone = tk.PhotoImage(data="".join(ICONE_PNG))  # ícone da janela e da barra de tarefas
            root.iconphoto(True, self._icone)
        except Exception:
            pass

        self._estilos()
        self._montar_ui()
        self._set_fase("Parado", 0)
        self._atualizar_calibracao()
        self._mostrar_aba("Painel")
        self._restaurar_posicao()
        self._log("Versão {v}. Ajustes salvos em {pasta}", v=VERSAO, pasta=PASTA_CONFIG)
        barra_de_titulo_escura(root)

        self.hotkeys = None
        self._criar_hotkeys()

        root.protocol("WM_DELETE_WINDOW", self._pedir_fechar)
        root.bind("<Unmap>", self._ao_minimizar)
        self._aplicar_bandeja()
        self._tick()
        self.root.after(50, self._abrir_como_escolhido)

    # --------------------------------------------------------------- atalhos
    def _mapa_teclas(self) -> dict:
        """Nome padrão da tecla (como está nos textos) -> nome da tecla que o usuário escolheu."""
        return {padrao: nome_tecla(self.cfg["teclas"][acao]) for acao, padrao, _t in ACOES}

    def _criar_hotkeys(self) -> None:
        if self.hotkeys is not None:
            try:
                self.hotkeys.stop()
            except Exception:
                pass
        logico = {"pesca": "f1", "ac": "f2", "calibrar": "f3", "parar": "esc"}  # nomes internos dos eventos
        mapa = {}
        for acao, ident in self.cfg["teclas"].items():
            mapa[f"<{ident}>"] = lambda a=logico[acao]: self.fila.put(("hk", a))
        self.hotkeys = keyboard.GlobalHotKeys(mapa)
        self.hotkeys.daemon = True
        self.hotkeys.start()

    def _mostrar_tecla_botoes(self) -> None:
        for acao, _p, _t in ACOES:
            bt = self.btns_tecla.get(acao)
            if bt is None:
                continue
            if self._capturando == acao:
                bt.ajustar(texto=T("Aperte uma tecla…"), bg=GEMA, fg=TEXTO_BTN, hover=GEMA)
            else:
                bt.ajustar(texto=nome_tecla(self.cfg["teclas"][acao]), bg=SUP2, fg=TEXTO, hover=SUP3)

    def _escolher_tecla(self, acao: str) -> None:
        """Clique no botão do atalho: a próxima tecla apertada vira o novo atalho (clicar de novo cancela)."""
        if self._capturando == acao:
            self._parar_captura()
            return
        self._capturando = acao
        self.root.bind_all("<KeyPress>", self._tecla_capturada)
        self.root.focus_force()
        self._mostrar_tecla_botoes()

    def _parar_captura(self) -> None:
        self._capturando = None
        self.root.unbind_all("<KeyPress>")
        self._mostrar_tecla_botoes()

    def _tecla_capturada(self, ev) -> str:
        acao = self._capturando
        ident = POR_KEYSYM.get(ev.keysym)
        if acao is None:
            return "break"
        if ident is None:
            self._log("Essa tecla não pode ser usada. Escolha F1 a F12, Esc, Pause, Insert, Home, End, PgUp ou PgDn.",
                      "aviso")
            return "break"
        teclas = dict(self.cfg["teclas"])
        outra = next((a for a, v in teclas.items() if v == ident and a != acao), None)
        if outra:  # tecla já usada por outra ação: as duas trocam de tecla
            teclas[outra] = teclas[acao]
        teclas[acao] = ident
        self._capturando = None
        self.root.unbind_all("<KeyPress>")
        self.root.after(10, lambda: self._aplicar_teclas(teclas))
        return "break"

    def _aplicar_teclas(self, teclas: dict) -> None:
        self.cfg["teclas"] = dict(teclas)
        salvar_config(self.cfg)
        definir_teclas(self._mapa_teclas())
        self._criar_hotkeys()
        self._refazer_interface()
        self._log("Atalhos atualizados.", "ok")

    def _restaurar_teclas(self) -> None:
        self._parar_captura()
        self._aplicar_teclas(PADRAO["teclas"])

    def _refazer_interface(self) -> None:
        for campo in self.campos.values():
            campo._digitar()
        self._reconstruir_ui()
        if self.mini is not None:
            self.mini.traduzir()

    # --------------------------------------------------------------- estilo
    def _estilos(self) -> None:
        st = ttk.Style(self.root)
        try:
            st.theme_use("clam")
        except tk.TclError:
            pass
        st.layout("Ovo.Vertical.TScrollbar", [
            ("Vertical.Scrollbar.trough", {"sticky": "ns", "children": [
                ("Vertical.Scrollbar.thumb", {"expand": "1", "sticky": "nswe"})]})
        ])
        st.configure(
            "Ovo.Vertical.TScrollbar", background=SUP3, troughcolor=SUP, bordercolor=SUP,
            lightcolor=SUP3, darkcolor=SUP3, gripcount=0, relief="flat", width=px(8),
        )
        st.map("Ovo.Vertical.TScrollbar", background=[("active", TEXTO3)])

    # --------------------------------------------------------------- layout geral
    def _montar_ui(self) -> None:
        raiz = tk.Frame(self.root, bg=BG)
        raiz.pack(fill="both", expand=True)
        self._montar_topo(raiz)
        self._montar_abas(raiz)
        tk.Frame(raiz, bg=BORDA, height=1).pack(fill="x")
        self._montar_rodape(raiz)  # empacotado antes do conteúdo para sempre ficar visível embaixo

        conteudo = tk.Frame(raiz, bg=BG)
        conteudo.pack(fill="both", expand=True, padx=px(22), pady=(px(10), px(12)))
        self.lbl_titulo = tk.Label(conteudo, text="", font=FN(18), bg=BG, fg=TEXTO)  # não aparece: só guarda o nome
        self.lbl_subtitulo = tk.Label(conteudo, text="", font=F(10), bg=BG, fg=TEXTO2, anchor="w")
        self.lbl_subtitulo.pack(fill="x", pady=(0, px(8)))

        # páginas: todas na mesma célula; só a aberta aparece
        area = tk.Frame(conteudo, bg=BG)
        area.pack(fill="both", expand=True)
        area.grid_rowconfigure(0, weight=1)
        area.grid_columnconfigure(0, weight=1)
        self.paginas = {}
        for nome, _ in ABAS:
            pg = tk.Frame(area, bg=BG)
            pg.grid(row=0, column=0, sticky="nsew")
            self.paginas[nome] = pg
        self.campos = {}
        self._montar_painel(self.paginas["Painel"])
        self._montar_deteccao(self.paginas["Detecção"])
        self._montar_autoclick(self.paginas["AutoClick"])
        self._montar_ajustes(self.paginas["Ajustes"])
        self._montar_registro(self.paginas["Registro"])
        self._montar_opcoes(self.paginas["Opções"])
        self._montar_ajuda(self.paginas["Ajuda"])

    def _montar_topo(self, pai: tk.Frame) -> None:
        barra = tk.Frame(pai, bg=SUP, height=px(ALT_TOPO))
        barra.pack(fill="x")
        barra.pack_propagate(False)
        Logo(barra, 34, bg=SUP).pack(side="left", padx=(px(22), px(10)))
        tk.Label(barra, text=T("Roube um Ovo"), font=FN(15), bg=SUP, fg=TEXTO).pack(side="left")
        tk.Label(barra, text=f"v{VERSAO}", font=F(8, "bold"), bg=SUP2, fg=TEXTO2, padx=px(8), pady=px(3)).pack(
            side="left", padx=(px(12), 0))
        self.pilula = tk.Frame(barra, bg=SUP2)
        self.pilula.pack(side="left", padx=(px(12), 0))
        self.pilula_pt = tk.Canvas(self.pilula, width=px(10), height=px(10), bg=SUP2, highlightthickness=0, bd=0)
        self.pilula_pt.pack(side="left", padx=(px(10), px(6)), pady=px(6))
        self._pt_id = self.pilula_pt.create_oval(1, 1, px(10) - 1, px(10) - 1, fill=TEXTO3, outline="")
        self.pilula_txt = tk.Label(self.pilula, text=T("Parado"), font=F(9, "bold"), bg=SUP2, fg=TEXTO2)
        self.pilula_txt.pack(side="left", padx=(0, px(11)))
        Botao(barra, T("Mini"), self.entrar_mini, altura=30, largura=64, raio=9, fundo=SUP).pack(
            side="right", padx=(0, px(22)))

    def _montar_abas(self, pai: tk.Frame) -> None:
        """Navegação no topo: uma aba por página, com o nome sempre escrito."""
        tk.Frame(pai, bg=BORDA, height=1).pack(fill="x")
        barra = tk.Frame(pai, bg=BG, height=px(ALT_ABAS))
        barra.pack(fill="x")
        barra.pack_propagate(False)
        self.abas = {}
        for nome, icone in ABAS:
            b = Aba(barra, icone, T(ROTULO_ABA.get(nome, nome)), lambda n=nome: self._mostrar_aba(n))
            b.pack(side="left", padx=(px(18) if not self.abas else px(2), 0), pady=px(3))
            self.abas[nome] = b

    def _montar_rodape(self, pai: tk.Frame) -> None:
        """Atalhos do teclado sempre visíveis."""
        rod = tk.Frame(pai, bg=SUP, height=px(ALT_RODAPE))
        rod.pack(side="bottom", fill="x")
        rod.pack_propagate(False)
        tk.Frame(rod, bg=BORDA, height=1).pack(side="top", fill="x")
        dentro = tk.Frame(rod, bg=SUP)
        dentro.pack(side="left", padx=px(22), fill="y")
        tk.Label(dentro, text=T("Atalhos"), font=F(8, "bold"), bg=SUP, fg=TEXTO3).pack(side="left", padx=(0, px(12)))
        for tecla_txt, rotulo in (("F1", "pesca"), ("F2", "autoclick"), ("F3", "calibrar"), ("Esc", "parar tudo")):
            tecla(dentro, self._mapa_teclas()[tecla_txt]).pack(side="left")
            tk.Label(dentro, text=T(rotulo), font=F(8), bg=SUP, fg=TEXTO2).pack(side="left", padx=(px(5), px(16)))

    # --------------------------------------------------------------- página: Painel (Pescar)
    def _montar_painel(self, pg: tk.Frame) -> None:
        pg.grid_columnconfigure(0, weight=1, uniform="painel")
        pg.grid_columnconfigure(1, weight=1, uniform="painel")
        pg.grid_rowconfigure(0, weight=1)

        # esquerda: situação atual (anel + o que está acontecendo) e o botão grande
        esq = cartao(pg)
        esq.grid(row=0, column=0, sticky="nsew", padx=(0, px(14)))
        ei = tk.Frame(esq, bg=SUP)
        ei.pack(fill="both", expand=True, padx=px(20), pady=px(16))
        topo = tk.Frame(ei, bg=SUP)
        topo.pack(fill="x")
        self.anel = Anel(topo, 118, 9, bg=SUP)
        self.anel.pack(side="left")
        self.hero = EstadoAtual(topo)
        self.hero.pack(side="left", fill="both", expand=True, padx=(px(16), 0))
        self.btn = Botao(ei, T("Iniciar  (F1)"), self.alternar, icone="play", bg=GEMA, fg=TEXTO_BTN,
                         hover=misturar(GEMA, "#ffffff", 0.14), fonte=F(12, "bold"), altura=54, raio=14, fundo=SUP)
        self.btn.pack(fill="x", pady=(px(16), px(8)), side="bottom")
        lamp = tk.Label(ei, text="", font=F(9, "bold"), bg=SUP, fg=TEXTO3, anchor="w")
        lamp.pack(fill="x", side="bottom")
        self._lampadas.append(lamp)
        self.acoes = {"AutoClick": _Oculto()}

        # direita: o que falta fazer (se marca sozinho)
        dir_ = cartao(pg)
        dir_.grid(row=0, column=1, sticky="nsew")
        di = tk.Frame(dir_, bg=SUP)
        di.pack(fill="both", expand=True, padx=px(20), pady=px(16))
        titulo_secao(di, T("Antes de começar")).pack(fill="x", pady=(0, px(6)))
        self.itens_guia = []
        for n, (titulo, desc, destino) in enumerate(GUIA):
            lin = tk.Frame(di, bg=SUP)
            lin.pack(fill="x", pady=px(8))
            marc = Marcador(lin, 32, n + 1)
            marc.pack(side="left", anchor="n")
            col = tk.Frame(lin, bg=SUP)
            col.pack(side="left", fill="x", expand=True, padx=(px(12), 0))
            tit = tk.Label(col, text=T(titulo), font=F(11, "bold"), bg=SUP, fg=TEXTO, anchor="w")
            tit.pack(fill="x")
            dsc = tk.Label(col, text=T(desc), font=F(9), bg=SUP, fg=TEXTO2, anchor="w", justify="left",
                           wraplength=px(330))
            dsc.pack(fill="x")
            if destino:  # o passo leva a outra aba: a linha toda é clicável
                for w in (lin, marc, col, tit, dsc):
                    w.configure(cursor="hand2")
                    w.bind("<ButtonRelease-1>", lambda _e, d=destino: self._mostrar_aba(d))
            self.itens_guia.append((marc, tit, dsc))
        Botao(di, T("Parar tudo  (Esc)"), self.parar_tudo, altura=32, largura=150, raio=9, fundo=SUP).pack(
            side="bottom", anchor="w")

        # embaixo da tela: quatro números e as últimas mensagens
        pg.grid_rowconfigure(0, minsize=px(196))
        pg.grid_rowconfigure(0, weight=0)
        pg.grid_rowconfigure(1, weight=0)
        pg.grid_rowconfigure(2, weight=1)
        sess = cartao(pg)
        sess.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(px(8), 0))
        si = tk.Frame(sess, bg=SUP)
        si.pack(fill="x", padx=px(16), pady=px(8))
        mosaicos = [
            ("ciclos", "ciclos", LILAS, "Ciclos"),
            ("cliques", "cursor", TURQUESA, "Cliques"),
            ("tempo", "ampulheta", PALHA, "Tempo ativo"),
            ("cps", "raio", GEMA, "Cliques por s"),
        ]
        self.mosaicos = {k: _Oculto() for k in ("ciclos_min", "media", "melhor", "deteccao", "roblox")}
        for n, (chave, icone, cor, legenda) in enumerate(mosaicos):
            m = Mosaico(si, icone, cor, T(legenda), "0", altura=56)
            m.grid(row=0, column=n, sticky="ew", padx=(0 if n == 0 else px(10), 0))
            si.grid_columnconfigure(n, weight=1, uniform="mosaico")
            self.mosaicos[chave] = m
        self.mosaicos["tempo"].definir("00:00:00")

        ati = cartao(pg)
        ati.grid(row=2, column=0, columnspan=2, sticky="nsew", pady=(px(12), 0))
        ai = tk.Frame(ati, bg=SUP)
        ai.pack(fill="both", expand=True, padx=px(16), pady=px(10))
        titulo_secao(ai, T("Últimas mensagens")).pack(fill="x", pady=(0, px(2)))
        self.feed_ati = tk.Frame(ai, bg=SUP)
        self.feed_ati.pack(fill="both", expand=True)
        self.linhas_ativ = []
        for _ in range(LINHAS_ATIVIDADE):
            lin = tk.Frame(self.feed_ati, bg=SUP)
            lin.pack(fill="x", pady=px(3))
            chip = etiqueta(lin, "", TEXTO2, SUP)
            chip.configure(width=6)
            chip.pack(side="left")
            hora = tk.Label(lin, text="", font=F(8), bg=SUP, fg=TEXTO3, anchor="e")
            hora.pack(side="right")
            txt = tk.Label(lin, text="", font=F(9), bg=SUP, fg=TEXTO, anchor="w", justify="left")
            txt.pack(side="left", fill="x", expand=True, padx=(px(10), 0))
            self.linhas_ativ.append((chip, txt, hora))
        self._atualizar_atividade()
        self._atualizar_guia()

    # --------------------------------------------------------------- página: Detecção
    def _montar_deteccao(self, pg: tk.Frame) -> None:
        pg.grid_columnconfigure(0, weight=1, uniform="det")
        pg.grid_columnconfigure(1, weight=1, uniform="det")
        pg.grid_rowconfigure(0, weight=1)

        c = cartao(pg)
        c.grid(row=0, column=0, sticky="nsew", padx=(0, px(14)))
        i = tk.Frame(c, bg=SUP)
        i.pack(fill="both", expand=True, padx=px(18), pady=px(16))
        cabecalho_cartao(i, "alvo", T("Calibração")).pack(fill="x", pady=(0, px(10)))
        topo = tk.Frame(i, bg=SUP)
        topo.pack(fill="x")
        tk.Label(topo, text=T("Detectar o minigame pela cor"), font=FN(12), bg=SUP, fg=TEXTO).pack(side="left")
        AjudaIcone(topo, lambda: T(AJUDA["detectar"]), SUP).pack(side="left", padx=(px(8), 0))
        self.var_detectar = tk.BooleanVar(value=bool(self.cfg["detectar"]))
        Toggle(topo, self.var_detectar, lambda: self._opcao("detectar", self.var_detectar)).pack(side="right")
        tk.Label(
            i, text=T("O macro olha o botão vermelho PARAR para saber quando o minigame começa e quando acaba. "
                      "Sem calibração ele usa os tempos fixos dos ajustes."),
            font=F(9), bg=SUP, fg=TEXTO2, anchor="w", justify="left", wraplength=px(360),
        ).pack(fill="x", pady=(px(8), px(14)))
        for n, t in enumerate(
            ("Abra o jogo e deixe o minigame na tela.",
             "Passe o mouse sobre a parte vermelha do botão PARAR.",
             "Aperte F3 ou clique em Calibrar. Só precisa fazer uma vez."), 1
        ):
            lin = tk.Frame(i, bg=SUP)
            lin.pack(fill="x", pady=px(4))
            tk.Label(lin, text=str(n), font=FN(10), bg=SUP2, fg=GEMA, width=2).pack(side="left")
            tk.Label(lin, text=T(t), font=F(9), bg=SUP, fg=TEXTO, anchor="w", justify="left",
                     wraplength=px(330)).pack(side="left", padx=(px(10), 0))
        botoes = tk.Frame(i, bg=SUP)
        botoes.pack(fill="x", pady=(px(16), 0))
        Botao(botoes, T("Calibrar  (F3)"), self.calibrar, bg=GEMA, fg=TEXTO_BTN, hover=misturar(GEMA, "#ffffff", 0.14),
              altura=36, largura=132, raio=10).pack(side="left")
        Botao(botoes, T("Limpar"), self.limpar_calibracao, altura=36, largura=84, raio=10).pack(
            side="left", padx=(px(8), 0))
        self.cor_box = tk.Label(botoes, width=4, bg=SUP2, bd=0, highlightthickness=1, highlightbackground=BORDA)
        self.cor_box.pack(side="right", ipady=px(6))
        tk.Label(botoes, text=T("cor lida"), font=F(8), bg=SUP, fg=TEXTO3).pack(side="right", padx=(0, px(8)))

        d = cartao(pg)
        d.grid(row=0, column=1, sticky="nsew")
        di = tk.Frame(d, bg=SUP)
        di.pack(fill="both", expand=True, padx=px(18), pady=px(16))
        cabecalho_cartao(di, "olho", T("Situação agora")).pack(fill="x", pady=(0, px(10)))
        lamp = tk.Label(di, text="", font=FN(14), bg=SUP, fg=TEXTO3, anchor="w")
        lamp.pack(fill="x")
        self._lampadas.append(lamp)
        self.lbl_cal = tk.Label(di, text="", font=F(9), bg=SUP, fg=TEXTO2, anchor="w", justify="left",
                                wraplength=px(360))
        self.lbl_cal.pack(fill="x", pady=(px(6), px(8)))
        tk.Label(di, text=T("Como testar: com o minigame na tela, o botão PARAR deve aparecer como visível. "
                            "Sem o minigame, como não visível."),
                 font=F(8), bg=SUP, fg=TEXTO3, anchor="w", justify="left", wraplength=px(360)).pack(
            fill="x", pady=(0, px(12)))
        tk.Frame(di, bg=BORDA, height=1).pack(fill="x")
        titulo_secao(di, T("Ajuste fino")).pack(fill="x", pady=(px(12), px(2)))
        g = tk.Frame(di, bg=SUP)
        g.pack(fill="x")
        g.grid_columnconfigure(0, weight=1)
        por_chave = {a[0]: a for a in AJUSTES}
        for n, chave in enumerate(AJUSTES_DETECCAO):
            _, rotulo, mn, mx, p1, p2, unid = por_chave[chave]
            self.campos[chave] = Campo(g, n, chave, T(rotulo), mn, mx, p1, p2, T(unid), self._numero(chave),
                                       self._mudou, empilhado=True, ajuda=AJUDA.get(chave), padrao=PADRAO[chave])
        tk.Label(di, text=T("Dica: calibre de novo se mudar o tamanho da janela do Roblox."), font=F(8), bg=SUP,
                 fg=TEXTO3, anchor="w", justify="left", wraplength=px(360)).pack(fill="x", pady=(px(12), 0))

    # --------------------------------------------------------------- página: AutoClick
    def _montar_autoclick(self, pg: tk.Frame) -> None:
        pg.grid_columnconfigure(0, weight=1, uniform="ac")
        pg.grid_columnconfigure(1, weight=1, uniform="ac")
        pg.grid_rowconfigure(0, weight=1)

        esq = tk.Frame(pg, bg=BG)
        esq.grid(row=0, column=0, sticky="nsew", padx=(0, px(14)))
        hero = cartao(esq)
        hero.pack(fill="x")
        h = tk.Frame(hero, bg=SUP)
        h.pack(fill="x", padx=px(18), pady=px(16))
        cabecalho_cartao(h, "cursor", "AutoClick").pack(fill="x", pady=(0, px(8)))
        self.lbl_ac = tk.Label(h, text=T("Parado"), font=FN(21), bg=SUP, fg=TEXTO3, anchor="w")
        self.lbl_ac.pack(fill="x")
        self.lbl_ac_sub = tk.Label(
            h, text=T(DESC_AC["Parado"]), font=F(9), bg=SUP, fg=TEXTO2, anchor="nw", justify="left",
            wraplength=px(360), height=2,
        )
        self.lbl_ac_sub.pack(fill="x", pady=(px(2), px(10)))
        self.btn_ac = Botao(h, T("Iniciar AutoClick  (F2)"), self.alternar_ac, icone="play", bg=GEMA, fg=TEXTO_BTN,
                            hover=misturar(GEMA, "#ffffff", 0.14), fonte=F(11, "bold"), altura=44, raio=12, fundo=SUP)
        self.btn_ac.pack(fill="x")

        self.stat_ac = {}
        for n, (chave, icone, cor, legenda) in enumerate(
            [("cliques", "cursor", TURQUESA, "Cliques"), ("cps", "raio", GEMA, "Cliques por s"),
             ("tempo", "ampulheta", PALHA, "Tempo ativo")]
        ):
            m = Mosaico(esq, icone, cor, T(legenda), "0", altura=58, fundo=BG)
            m.pack(fill="x", pady=(px(12) if n == 0 else px(8), 0))
            self.stat_ac[chave] = m
        self.stat_ac["tempo"].definir("00:00:00")

        dir_ = cartao(pg)
        dir_.grid(row=0, column=1, sticky="nsew")
        d = tk.Frame(dir_, bg=SUP)
        d.pack(fill="both", expand=True, padx=px(18), pady=px(16))
        cabecalho_cartao(d, "engrenagem", T("Configuração")).pack(fill="x", pady=(0, px(4)))
        g = tk.Frame(d, bg=SUP)
        g.pack(fill="x")
        g.grid_columnconfigure(0, weight=1)
        por_chave = {a[0]: a for a in AJUSTES_AC}
        self.campos["ac_intervalo"] = CampoIntervalo(
            g, 0, "ac_intervalo", T("Intervalo entre cliques"), self._numero("ac_intervalo"), self._mudou,
            ajuda=AJUDA["ac_intervalo"], padrao=PADRAO["ac_intervalo"])
        for n, chave in ((1, "ac_atraso"), (2, "ac_limite")):
            _, rotulo, mn, mx, p1, p2, unid = por_chave[chave]
            self.campos[chave] = Campo(g, n, chave, T(rotulo), mn, mx, p1, p2, T(unid), self._numero(chave),
                                       self._mudou, empilhado=True, ajuda=AJUDA.get(chave), padrao=PADRAO[chave])
        self.lbl_ac_taxa = tk.Label(d, text="", font=F(8), bg=SUP, fg=TEXTO3, anchor="w")
        self.lbl_ac_taxa.pack(fill="x", pady=(px(6), px(8)))

        b = tk.Frame(d, bg=SUP)
        b.pack(fill="x", pady=px(4))
        tk.Label(b, text=T("Botão do mouse"), font=F(9), bg=SUP, fg=TEXTO, anchor="w").pack(side="left")
        self.btns_botao = {}
        for chave, texto in (("meio", "Meio"), ("direito", "Direito"), ("esquerdo", "Esquerdo")):
            bt = Botao(b, T(texto), lambda k=chave: self._escolher_botao(k), altura=28, largura=78, raio=8)
            bt.pack(side="right", padx=(px(4), 0))
            self.btns_botao[chave] = bt
        self._marcar_botao()

        self.var_ac_roblox = tk.BooleanVar(value=bool(self.cfg["ac_so_roblox"]))
        self._linha_toggle(d, "Só clicar com o Roblox em primeiro plano", self.var_ac_roblox,
                           lambda: self._opcao("ac_so_roblox", self.var_ac_roblox), ajuda=AJUDA["ac_so_roblox"])
        self.var_ac_fixa = tk.BooleanVar(value=bool(self.cfg["ac_pos_fixa"]))
        self._linha_toggle(d, "Clicar sempre na mesma posição", self.var_ac_fixa, self._alternar_pos_fixa,
                           ajuda=AJUDA["ac_pos_fixa"])
        lp = tk.Frame(d, bg=SUP)
        lp.pack(fill="x", pady=(0, px(4)))
        self.btn_pos = Botao(lp, T("Definir posição"), self._definir_posicao, altura=28, largura=130, raio=8)
        self.btn_pos.pack(side="left")
        self.lbl_pos = tk.Label(lp, text="", font=F(8), bg=SUP, fg=TEXTO2, anchor="w")
        self.lbl_pos.pack(side="left", padx=(px(10), 0))
        self._pos_job = None
        self._mostrar_posicao()
        self.var_ac_mouse = tk.BooleanVar(value=bool(self.cfg["ac_parar_mouse"]))
        self._linha_toggle(d, "Parar se eu mexer o mouse", self.var_ac_mouse,
                           lambda: self._opcao("ac_parar_mouse", self.var_ac_mouse), ajuda=AJUDA["ac_parar_mouse"])
        gm = tk.Frame(d, bg=SUP)
        gm.pack(fill="x")
        gm.grid_columnconfigure(0, weight=1)
        self.campos["ac_dist_mouse"] = Campo(
            gm, 0, "ac_dist_mouse", T("Distância para parar"), 50, 1000, 50, 10, "px", self._numero("ac_dist_mouse"),
            self._mudou, empilhado=True, ajuda=AJUDA["ac_dist_mouse"], padrao=PADRAO["ac_dist_mouse"])

    # --------------------------------------------------------------- página: Ajustes
    def _montar_ajustes(self, pg: tk.Frame) -> None:
        pg.grid_columnconfigure(0, weight=1, uniform="aj")
        pg.grid_columnconfigure(1, weight=1, uniform="aj")
        pg.grid_rowconfigure(0, weight=1)

        esq = tk.Frame(pg, bg=BG)
        esq.grid(row=0, column=0, sticky="nsew", padx=(0, px(14)))
        por_chave = {a[0]: a for a in AJUSTES}
        for n, (titulo, chaves) in enumerate(GRUPOS):
            c = cartao(esq)
            c.pack(fill="x", pady=(0 if n == 0 else px(12), 0))
            g = tk.Frame(c, bg=SUP)
            g.pack(fill="x", padx=px(18), pady=px(14))
            titulo_secao(g, T(titulo)).grid(row=0, column=0, columnspan=3, sticky="w")
            sub = SUBTITULO_GRUPO.get(titulo)
            if sub:
                tk.Label(g, text=T(sub), font=F(8), bg=SUP, fg=TEXTO3, anchor="w").grid(row=1, column=0, sticky="w")
            if chaves[0] == "espera_minigame":  # grupo dos tempos fixos: diz se está em uso agora
                self.lbl_fixos = tk.Label(g, text="", font=F(8, "bold"), bg=SUP, fg=TEXTO2, anchor="w")
                self.lbl_fixos.grid(row=2, column=0, sticky="w")
            f = tk.Frame(g, bg=SUP)
            f.grid(row=3, column=0, sticky="ew")
            g.grid_columnconfigure(0, weight=1)
            f.grid_columnconfigure(0, weight=1)
            for i, chave in enumerate(chaves):
                _, rotulo, mn, mx, p1, p2, unid = por_chave[chave]
                self.campos[chave] = Campo(f, i, chave, T(rotulo), mn, mx, p1, p2, T(unid), self._numero(chave),
                                           self._mudou, empilhado=True, ajuda=AJUDA.get(chave), padrao=PADRAO[chave])

        dir_ = tk.Frame(pg, bg=BG)
        dir_.grid(row=0, column=1, sticky="nsew")
        c = cartao(dir_)
        c.pack(fill="x")
        i = tk.Frame(c, bg=SUP)
        i.pack(fill="x", padx=px(18), pady=px(14))
        titulo_secao(i, T("Interface")).pack(fill="x", pady=(0, px(4)))
        lin = tk.Frame(i, bg=SUP)
        lin.pack(fill="x", pady=px(5))
        tk.Label(lin, text=T("Idioma"), font=F(9), bg=SUP, fg=TEXTO, anchor="w").pack(side="left")
        self.btns_idioma = {}
        for cod in reversed(list(IDIOMAS)):  # empacota da direita para a esquerda: fica Português, English
            bt = Botao(lin, IDIOMAS[cod], lambda k=cod: self._escolher_idioma(k), altura=28, largura=92, raio=8)
            bt.pack(side="right", padx=(px(4), 0))
            self.btns_idioma[cod] = bt
        self._marcar_idioma()
        self.var_bandeja = tk.BooleanVar(value=bool(self.cfg["minimizar_bandeja"]))
        self._linha_toggle(i, "Minimizar para a bandeja do sistema", self.var_bandeja,
                           lambda: self._opcao("minimizar_bandeja", self.var_bandeja),
                           ajuda=AJUDA["minimizar_bandeja"])

        c = cartao(dir_)
        c.pack(fill="x", pady=(px(12), 0))
        i = tk.Frame(c, bg=SUP)
        i.pack(fill="x", padx=px(18), pady=px(14))
        titulo_secao(i, T("Janela e segurança")).pack(fill="x", pady=(0, px(4)))
        self.var_roblox = tk.BooleanVar(value=bool(self.cfg["so_roblox"]))
        self.var_topo = tk.BooleanVar(value=bool(self.cfg["sempre_no_topo"]))
        for texto, var, chave in (
            ("Só rodar com o Roblox em primeiro plano", self.var_roblox, "so_roblox"),
            ("Manter esta janela sempre por cima", self.var_topo, "sempre_no_topo"),
        ):
            self._linha_toggle(i, texto, var, lambda k=chave, v=var: self._opcao(k, v), ajuda=AJUDA[chave])

        c = cartao(dir_)
        c.pack(fill="x", pady=(px(12), 0))
        i = tk.Frame(c, bg=SUP)
        i.pack(fill="x", padx=px(18), pady=px(14))
        titulo_secao(i, T("Sobre")).pack(fill="x", pady=(0, px(4)))
        tk.Label(i, text=f"{T('Versão')} {VERSAO}", font=F(9), bg=SUP, fg=TEXTO, anchor="w").pack(fill="x", pady=px(2))
        tk.Label(i, text=f"{T('Pasta de ajustes')}: {PASTA_CONFIG}", font=F(8), bg=SUP, fg=TEXTO3, anchor="w",
                 justify="left", wraplength=px(370)).pack(fill="x", pady=(px(2), px(10)))
        lin = tk.Frame(i, bg=SUP)
        lin.pack(fill="x")
        Botao(lin, T("Abrir pasta"), self._abrir_pasta, altura=32, largura=110, raio=9).pack(side="left")
        self.btn_restaurar = Botao(lin, T("Restaurar padrões"), self._pedir_restaurar, altura=32, largura=150, raio=9)
        self.btn_restaurar.pack(side="left", padx=(px(8), 0))

    def _linha_toggle(self, pai, texto: str, var: tk.BooleanVar, comando, ajuda: str | None = None) -> tk.Frame:
        lin = tk.Frame(pai, bg=SUP)
        lin.pack(fill="x", pady=px(5))
        rot = tk.Label(lin, text=T(texto), font=F(9), bg=SUP, fg=TEXTO, anchor="w")
        rot.pack(side="left")
        if ajuda:
            AjudaIcone(lin, lambda a=ajuda: T(a), SUP).pack(side="left", padx=(px(6), 0))
            Dica(rot, lambda a=ajuda: T(a))
        Toggle(lin, var, comando).pack(side="right")
        return lin

    # --------------------------------------------------------------- página: Registro
    # --------------------------------------------------------------- página: Opções
    def _montar_opcoes(self, pg: tk.Frame) -> None:
        pg.grid_columnconfigure(0, weight=1, uniform="op")
        pg.grid_columnconfigure(1, weight=1, uniform="op")
        pg.grid_rowconfigure(0, weight=1)
        esq = tk.Frame(pg, bg=BG)
        esq.grid(row=0, column=0, sticky="nsew", padx=(0, px(14)))
        dir_ = tk.Frame(pg, bg=BG)
        dir_.grid(row=0, column=1, sticky="nsew")

        # ---- atalhos do teclado
        c = cartao(esq)
        c.pack(fill="x")
        i = tk.Frame(c, bg=SUP)
        i.pack(fill="x", padx=px(18), pady=px(14))
        titulo_secao(i, T("Atalhos do teclado")).pack(fill="x", pady=(0, px(2)))
        tk.Label(i, text=T("Clique na tecla e aperte a nova. Funcionam com outra janela na frente."), font=F(8),
                 bg=SUP, fg=TEXTO3, anchor="w", justify="left", wraplength=px(370)).pack(fill="x", pady=(0, px(4)))
        self.btns_tecla = {}
        for acao, _padrao, texto in ACOES:
            lin = tk.Frame(i, bg=SUP)
            lin.pack(fill="x", pady=px(4))
            tk.Label(lin, text=T(texto), font=F(9), bg=SUP, fg=TEXTO, anchor="w").pack(side="left")
            bt = Botao(lin, "", lambda a=acao: self._escolher_tecla(a), altura=28, largura=104, raio=8)
            bt.pack(side="right")
            self.btns_tecla[acao] = bt
        self._mostrar_tecla_botoes()
        lin = tk.Frame(i, bg=SUP)
        lin.pack(fill="x", pady=(px(8), 0))
        Botao(lin, T("Restaurar atalhos"), self._restaurar_teclas, altura=28, largura=140, raio=8).pack(side="left")
        tk.Label(lin, text=T("F1 a F12, Esc, Pause, Insert, Home, End, PgUp, PgDn"), font=F(7), bg=SUP, fg=TEXTO3).pack(
            side="left", padx=(px(10), 0))

        # ---- modo mini
        c = cartao(esq)
        c.pack(fill="x", pady=(px(12), 0))
        i = tk.Frame(c, bg=SUP)
        i.pack(fill="x", padx=px(18), pady=px(14))
        titulo_secao(i, T("Modo mini")).pack(fill="x", pady=(0, px(4)))
        g = tk.Frame(i, bg=SUP)
        g.pack(fill="x")
        g.grid_columnconfigure(0, weight=1)
        self.campos["mini_opacidade"] = Campo(
            g, 0, "mini_opacidade", T("Opacidade da janela mini"), 40, 100, 5, 5, "%", self._numero("mini_opacidade"),
            self._mudou_opacidade, empilhado=True, ajuda=AJUDA["mini_opacidade"], padrao=PADRAO["mini_opacidade"])
        lin = tk.Frame(i, bg=SUP)
        lin.pack(fill="x", pady=(px(8), 0))
        Botao(lin, T("Ver o modo mini"), self.entrar_mini, altura=28, largura=140, raio=8).pack(side="left")

        # ---- ao abrir
        c = cartao(dir_)
        c.pack(fill="x")
        i = tk.Frame(c, bg=SUP)
        i.pack(fill="x", padx=px(18), pady=px(14))
        titulo_secao(i, T("Ao abrir")).pack(fill="x", pady=(0, px(4)))
        self.var_windows = tk.BooleanVar(value=iniciar_com_windows_ativo())
        self._linha_toggle(i, "Abrir junto com o Windows", self.var_windows, self._alternar_windows,
                           ajuda=AJUDA["iniciar_windows"])
        lin = tk.Frame(i, bg=SUP)
        lin.pack(fill="x", pady=px(5))
        tk.Label(lin, text=T("Abrir como"), font=F(9), bg=SUP, fg=TEXTO, anchor="w").pack(side="left")
        self.btns_iniciar = {}
        for cod, texto in reversed([("janela", "Janela"), ("mini", "Mini"), ("bandeja", "Bandeja")]):
            bt = Botao(lin, T(texto), lambda k=cod: self._escolher_iniciar(k), altura=28, largura=78, raio=8)
            bt.pack(side="right", padx=(px(4), 0))
            self.btns_iniciar[cod] = bt
        self._marcar_opcao(self.btns_iniciar, self.cfg["iniciar_em"])
        tk.Label(i, text=T("Mini e Bandeja abrem o programa escondido: use o ícone da bandeja ou o F1 para controlar."),
                 font=F(8), bg=SUP, fg=TEXTO3, anchor="w", justify="left", wraplength=px(370)).pack(
            fill="x", pady=(px(6), 0))

        # ---- aparência
        c = cartao(dir_)
        c.pack(fill="x", pady=(px(12), 0))
        i = tk.Frame(c, bg=SUP)
        i.pack(fill="x", padx=px(18), pady=px(14))
        titulo_secao(i, T("Aparência")).pack(fill="x", pady=(0, px(4)))
        lin = tk.Frame(i, bg=SUP)
        lin.pack(fill="x", pady=px(5))
        tk.Label(lin, text=T("Tema"), font=F(9), bg=SUP, fg=TEXTO, anchor="w").pack(side="left")
        AjudaIcone(lin, lambda: T(AJUDA["tema"]), SUP).pack(side="left", padx=(px(6), 0))
        self.btns_tema = {}
        for cod, texto in reversed([("claro", "Claro"), ("escuro", "Escuro")]):
            bt = Botao(lin, T(texto), lambda k=cod: self._escolher_tema(k), altura=28, largura=92, raio=8)
            bt.pack(side="right", padx=(px(4), 0))
            self.btns_tema[cod] = bt
        self._marcar_opcao(self.btns_tema, self.cfg["tema"])
        self.lbl_tema = tk.Label(i, text="", font=F(8, "bold"), bg=SUP, fg=PALHA, anchor="w")
        self.lbl_tema.pack(fill="x", pady=(px(4), 0))
        self._aviso_tema()

    def _marcar_opcao(self, botoes: dict, atual: str) -> None:
        for cod, bt in botoes.items():
            if cod == atual:
                bt.ajustar(bg=GEMA, hover=misturar(GEMA, "#ffffff", 0.14), fg=TEXTO_BTN)
            else:
                bt.ajustar(bg=SUP2, hover=SUP3, fg=TEXTO)

    # --------------------------------------------------------------- AutoClick: posição fixa
    def _mostrar_posicao(self) -> None:
        pos = self.cfg.get("ac_pos")
        self.lbl_pos.configure(text=T("Posição: {x}, {y}", x=pos[0], y=pos[1]) if pos
                               else T("Nenhuma posição definida"))

    def _alternar_pos_fixa(self) -> None:
        if self.var_ac_fixa.get() and not self.cfg.get("ac_pos"):
            self.var_ac_fixa.set(False)
            self._log("Defina a posição primeiro: clique em Definir posição.", "aviso")
            return
        self._opcao("ac_pos_fixa", self.var_ac_fixa)

    def _definir_posicao(self) -> None:
        """Contagem de 3 s para você levar o mouse ao alvo; ao zerar, a posição do cursor é guardada."""
        if self._pos_job is not None:
            return
        if self._ac_ativo():
            self._log("Pare o AutoClick antes de definir a posição.", "aviso")
            return
        self._contar_posicao(3)

    def _contar_posicao(self, n: int) -> None:
        if n > 0:
            self.btn_pos.ajustar(texto=T("Leve o mouse… {n}", n=n), bg=GEMA, fg=TEXTO_BTN, hover=GEMA)
            self._pos_job = self.root.after(1000, lambda: self._contar_posicao(n - 1))
            return
        self._pos_job = None
        x, y = posicao_cursor()
        self.cfg["ac_pos"] = [x, y]
        self._salvar_depois()
        self.btn_pos.ajustar(texto=T("Definir posição"), bg=SUP2, fg=TEXTO, hover=SUP3)
        self._mostrar_posicao()
        self._log("Posição do AutoClick definida: {x}, {y}.", "ok", x=x, y=y)

    def _mudou_opacidade(self, chave: str, valor) -> None:
        self._mudou(chave, valor)
        if self.mini is not None:
            self.mini.aplicar_opacidade()

    def _alternar_windows(self) -> None:
        if not definir_iniciar_com_windows(bool(self.var_windows.get())):
            self.var_windows.set(iniciar_com_windows_ativo())
            self._log("Não foi possível mudar a abertura com o Windows.", "aviso")
            return
        self._log("O programa vai abrir junto com o Windows." if self.var_windows.get()
                  else "O programa não abre mais junto com o Windows.", "ok")

    def _escolher_iniciar(self, cod: str) -> None:
        self.cfg["iniciar_em"] = cod
        self._salvar_depois()
        self._marcar_opcao(self.btns_iniciar, cod)
        self._aplicar_bandeja()

    def _escolher_tema(self, cod: str) -> None:
        self.cfg["tema"] = cod
        salvar_config(self.cfg)
        self._marcar_opcao(self.btns_tema, cod)
        self._aviso_tema()

    def _aviso_tema(self) -> None:
        escolhido = self.cfg["tema"] == "escuro"
        self.lbl_tema.configure(text="" if escolhido == tema.ESCURO else T("O tema novo vale quando você abrir o programa de novo."))

    def _abrir_como_escolhido(self) -> None:
        """Na abertura: janela normal, direto no modo mini ou escondido na bandeja."""
        modo = self.cfg["iniciar_em"]
        if modo == "mini":
            self.entrar_mini()
        elif modo == "bandeja":
            self.root.after(600, self._esconder_se_bandeja_ok)

    def _esconder_se_bandeja_ok(self) -> None:
        if self.bandeja is not None and self.bandeja.ok:
            self.root.withdraw()
        else:  # sem ícone a janela ficaria sem volta: abre normal
            self._log("Não foi possível criar o ícone da bandeja. A janela ficou aberta.", "aviso")

    # --------------------------------------------------------------- página: Ajuda
    def _montar_ajuda(self, pg: tk.Frame) -> None:
        pg.grid_columnconfigure(0, weight=1, uniform="aj")
        pg.grid_columnconfigure(1, weight=1, uniform="aj")
        pg.grid_rowconfigure(0, weight=1)
        esq = tk.Frame(pg, bg=BG)
        esq.grid(row=0, column=0, sticky="nsew", padx=(0, px(14)))
        dir_ = tk.Frame(pg, bg=BG)
        dir_.grid(row=0, column=1, sticky="nsew")

        c = cartao(esq)
        c.pack(fill="x")
        i = tk.Frame(c, bg=SUP)
        i.pack(fill="x", padx=px(18), pady=px(14))
        titulo_secao(i, T("Como usar em 4 passos")).pack(fill="x", pady=(0, px(6)))
        for n, texto in enumerate(PASSOS_AJUDA):
            lin = tk.Frame(i, bg=SUP)
            lin.pack(fill="x", pady=px(4))
            Marcador(lin, 24, n + 1).pack(side="left", anchor="n")
            tk.Label(lin, text=T(texto), font=F(9), bg=SUP, fg=TEXTO, anchor="w", justify="left",
                     wraplength=px(340)).pack(side="left", fill="x", expand=True, padx=(px(10), 0))

        c = cartao(esq)
        c.pack(fill="x", pady=(px(12), 0))
        i = tk.Frame(c, bg=SUP)
        i.pack(fill="x", padx=px(18), pady=px(14))
        titulo_secao(i, T("Novidades")).pack(fill="x", pady=(0, px(4)))
        self.linhas_nov = []
        for _ in range(LINHAS_NOVIDADES):
            lin = tk.Frame(i, bg=SUP)
            lin.pack(fill="x", pady=px(3))
            chip = etiqueta(lin, "", TEXTO2, SUP)
            chip.configure(width=8)
            chip.pack(side="left", anchor="n")
            col = tk.Frame(lin, bg=SUP)
            col.pack(side="left", fill="x", expand=True, padx=(px(10), 0))
            txt = tk.Label(col, text="", font=F(9), bg=SUP, fg=TEXTO, anchor="w", justify="left", wraplength=px(290))
            txt.pack(fill="x")
            sub = tk.Label(col, text="", font=F(8), bg=SUP, fg=TEXTO3, anchor="w")
            sub.pack(fill="x")
            self.linhas_nov.append((chip, txt, sub))
        nav = tk.Frame(i, bg=SUP)
        nav.pack(fill="x", pady=(px(4), 0))
        Botao(nav, "<", lambda: self._pagina_novidades(-1), altura=24, largura=30, raio=7).pack(side="left")
        self.lbl_nov_pag = tk.Label(nav, text="", font=F(8), bg=SUP, fg=TEXTO3)
        self.lbl_nov_pag.pack(side="left", padx=px(10))
        Botao(nav, ">", lambda: self._pagina_novidades(1), altura=24, largura=30, raio=7).pack(side="left")
        self._atualizar_novidades()

        c = cartao(dir_)
        c.pack(fill="both", expand=True)
        i = tk.Frame(c, bg=SUP)
        i.pack(fill="both", expand=True, padx=px(18), pady=px(14))
        titulo_secao(i, T("Se algo der errado")).pack(fill="x", pady=(0, px(6)))
        for titulo, solucao in PROBLEMAS_AJUDA:
            tk.Label(i, text=T(titulo), font=F(9, "bold"), bg=SUP, fg=GEMA, anchor="w").pack(fill="x", pady=(px(6), 0))
            tk.Label(i, text=T(solucao), font=F(8), bg=SUP, fg=TEXTO2, anchor="w", justify="left",
                     wraplength=px(370)).pack(fill="x")

    def _montar_registro(self, pg: tk.Frame) -> None:
        pg.grid_columnconfigure(0, weight=1)
        pg.grid_rowconfigure(1, weight=1)
        cab = tk.Frame(pg, bg=BG)
        cab.grid(row=0, column=0, sticky="ew", pady=(0, px(8)))
        titulo_secao(cab, T("Atividade do macro"), bg=BG).pack(side="left")
        Botao(cab, T("Limpar"), self._limpar_log, altura=28, largura=76, raio=8, fundo=BG).pack(side="right")
        Botao(cab, T("Abrir pasta"), self._abrir_pasta, altura=28, largura=100, raio=8, fundo=BG).pack(
            side="right", padx=(0, px(6)))
        c = cartao(pg)
        c.grid(row=1, column=0, sticky="nsew")
        self.txt_log = tk.Text(
            c, height=10, width=10, state="disabled", wrap="word", bg=SUP, fg=TEXTO, relief="flat", bd=0,
            highlightthickness=0, font=(tema.MONO, 9), padx=px(12), pady=px(10), spacing1=px(2), spacing3=px(2),
        )
        sb = ttk.Scrollbar(c, orient="vertical", command=self.txt_log.yview, style="Ovo.Vertical.TScrollbar")
        self.txt_log.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y", padx=(0, px(3)), pady=px(3))
        self.txt_log.pack(side="left", fill="both", expand=True)
        recuo = tkfont.Font(font=(tema.MONO, 9)).measure("00:00:00  •  ")
        self.txt_log.tag_configure("linha", lmargin1=px(10), lmargin2=px(10) + recuo)  # linhas quebradas alinham no texto
        self.txt_log.tag_configure("hora", foreground=TEXTO3)
        for nivel, cor in COR_LOG.items():
            self.txt_log.tag_configure("pt_" + nivel, foreground=cor)
            self.txt_log.tag_configure("tx_" + nivel, foreground=cor if nivel in ("aviso", "erro") else TEXTO)

    def _mostrar_aba(self, nome: str) -> None:
        self.aba_atual = nome
        for n, pg in self.paginas.items():
            if n == nome:
                pg.grid()
            else:
                pg.grid_remove()
        for n, b in self.abas.items():
            b.definir_ativo(n == nome)
        self.lbl_titulo.configure(text=T(ROTULO_ABA.get(nome, nome)))
        self.lbl_subtitulo.configure(text=T(SUBTITULO_ABA.get(nome, "")))

    # ------------------------------------------------------- idioma, modo mini e bandeja
    def pesca_ativa(self) -> bool:
        return bool(self.worker and self.worker.is_alive())

    def _marcar_idioma(self) -> None:
        for cod, bt in self.btns_idioma.items():
            if cod == idioma_atual():
                bt.ajustar(bg=GEMA, hover=misturar(GEMA, "#ffffff", 0.14), fg=TEXTO_BTN)
            else:
                bt.ajustar(bg=SUP2, hover=SUP3, fg=TEXTO)

    def _escolher_idioma(self, cod: str) -> None:
        if cod != idioma_atual():
            self.root.after(10, lambda: self._trocar_idioma(cod))  # depois do clique: o botão será recriado

    def _trocar_idioma(self, cod: str) -> None:
        for campo in self.campos.values():  # não perde o que foi digitado e ainda não confirmado
            campo._digitar()
        self.cfg["idioma"] = cod
        definir_idioma(cod)
        salvar_config(self.cfg)
        self._reconstruir_ui()
        if self.mini is not None:
            self.mini.traduzir()
        if self.bandeja is not None:
            self.bandeja.atualizar_dica(self._dica_bandeja())
        self._log("Idioma alterado para {nome}.", "ok", nome=IDIOMAS[cod])

    def _reconstruir_ui(self) -> None:
        """Recria a interface no idioma atual. Os valores vêm de self.cfg e o estado do que está rodando é repintado."""
        if getattr(self, "_pos_job", None) is not None:  # contagem da posição fixa: os botões vão ser recriados
            self.root.after_cancel(self._pos_job)
            self._pos_job = None
        for w in self.root.winfo_children():
            if w.winfo_class() != "Toplevel":  # o modo mini é uma Toplevel e fica
                w.destroy()
        self._lampadas = []
        self._roblox_aberto = None
        self._montar_ui()
        self.root.title(f"{T('Roube um Ovo')}  v{VERSAO}")
        self._mostrar_aba(self.aba_atual)
        self._set_pilula(*self._pilula)
        self._pintar_fase()
        desc, texto, cor, kw = self._ac_vis
        self._set_ac(desc, texto, cor, **kw)
        self._pintar_botao(self.pesca_ativa())
        self._pintar_botao_ac(self._ac_ativo())
        self._atualizar_calibracao()
        self._lampada(self._lamp)
        self._repintar_log()

    def entrar_mini(self) -> None:
        if self.mini is None:
            self.mini = JanelaMini(self)
        self.root.withdraw()
        self.mini.mostrar()

    def sair_mini(self) -> None:
        self.mostrar_janela()

    def mostrar_janela(self) -> None:
        if self.mini is not None:
            self.mini.esconder()
        self.root.deiconify()
        self.root.lift()
        self.root.attributes("-topmost", bool(self.cfg["sempre_no_topo"]))
        try:
            self.root.focus_force()
        except tk.TclError:
            pass

    def _itens_bandeja(self) -> list:
        """Menu do ícone da bandeja (chamado pela thread do ícone, só lê o estado)."""
        return [
            (1, T("Abrir janela")),
            (2, T("Modo mini")),
            None,
            (4, T("Parar pesca (F1)") if self.pesca_ativa() else T("Iniciar pesca (F1)")),
            (5, T("Parar AutoClick (F2)") if self._ac_ativo() else T("Iniciar AutoClick (F2)")),
            None,
            (6, T("Sair")),
        ]

    def _dica_bandeja(self) -> str:
        return f"{T('Roube um Ovo')}: {T(self._pilula[0])}"

    def _aplicar_bandeja(self) -> None:
        if self.cfg["minimizar_bandeja"] or self.cfg["iniciar_em"] == "bandeja":
            if self.bandeja is None:
                self.bandeja = Bandeja(ICONE_PNG, self.fila, self._itens_bandeja, self._dica_bandeja())
                self.bandeja.start()
        elif self.bandeja is not None:
            self.bandeja.encerrar()
            self.bandeja = None
            if self.root.state() == "withdrawn" and not (self.mini and self.mini.visivel):
                self.mostrar_janela()

    def _ao_minimizar(self, ev) -> None:
        """Ao minimizar, esconde a janela na bandeja. Só se o ícone existir de fato: senão ela ficaria sem volta."""
        if ev.widget is not self.root or not self.cfg["minimizar_bandeja"]:
            return
        if self.bandeja is not None and self.bandeja.ok and self.root.state() == "iconic":
            self.root.after_idle(self.root.withdraw)

    # ------------------------------------------------------------- utilitários
    def _numero(self, chave: str) -> float:
        try:
            return float(self.cfg[chave])
        except (TypeError, ValueError):
            return float(PADRAO[chave])

    def _log(self, msg: str, nivel: str = "info", **kw) -> None:
        """Registra uma mensagem. `msg` é o texto em português (com {campos}); ela é traduzida ao mostrar."""
        linha = (time.strftime("%H:%M:%S"), nivel, msg, kw)
        self.historico_log.append(linha)
        del self.historico_log[:-300]
        self._escrever_log(*linha)
        self._atualizar_atividade()

    def _escrever_log(self, hora: str, nivel: str, msg: str, kw: dict) -> None:
        texto = T(msg, **kw)
        t = self.txt_log
        t.configure(state="normal")
        t.insert("end", hora + "  ", ("hora", "linha"))
        t.insert("end", "•  ", ("pt_" + nivel, "linha"))
        t.insert("end", texto + "\n", ("tx_" + nivel, "linha"))
        if int(t.index("end-1c").split(".")[0]) > 300:
            t.delete("1.0", "80.0")
        t.see("end")
        t.configure(state="disabled")

    def _repintar_log(self) -> None:
        for linha in self.historico_log:
            self._escrever_log(*linha)
        self._atualizar_atividade()

    def _atualizar_atividade(self) -> None:
        """Mostra as últimas mensagens no cartão Atividade do painel (a mais recente em cima)."""
        recentes = list(reversed(self.historico_log[-LINHAS_ATIVIDADE:]))
        for n, (chip, txt, hora) in enumerate(self.linhas_ativ):
            if n < len(recentes):
                h, nivel, msg, kw = recentes[n]
                rotulo, cor, fundo = NIVEIS.get(nivel, NIVEIS["info"])
                chip.configure(text=T(rotulo), fg=cor, bg=fundo)
                txt.configure(text=resumir(T(msg, **kw), 52))
                hora.configure(text=h)
            elif n == 0:
                chip.configure(text=T("INFO"), fg=TEXTO2, bg=SUP3)
                txt.configure(text=T("Nada por aqui ainda."))
                hora.configure(text="")
            else:
                chip.configure(text="", bg=SUP)
                txt.configure(text="")
                hora.configure(text="")

    def _atualizar_guia(self) -> None:
        """Marca os passos do guia conforme o estado real: Roblox aberto, botão PARAR calibrado, pesca rodando."""
        feitos = [bool(self._roblox_aberto), bool(self.cfg.get("cal")), self.pesca_ativa()]
        proximo = next((n for n, f in enumerate(feitos) if not f), -1)
        for n, (marc, tit, _dsc) in enumerate(self.itens_guia):
            marc.definir(feitos[n], n == proximo)
            tit.configure(fg=TEXTO3 if feitos[n] else TEXTO)
        self._atualizar_parado()

    def _atualizar_parado(self) -> None:
        """Quando parado, a descrição do painel diz o próximo passo em vez de uma frase genérica."""
        if self.fase_nome != "Parado":
            return
        if not self._roblox_aberto:
            chave = "sem_roblox"
        elif not self.cfg.get("cal"):
            chave = "sem_calibracao"
        else:
            chave = "pronto"
        self._desc = DESC_PARADO[chave]
        if self.fase_dur <= 0 and not self.fase_texto:
            self.hero.definir(descricao=T(self._desc))

    def _pagina_novidades(self, passo: int) -> None:
        paginas = max(1, math.ceil(len(NOVIDADES) / LINHAS_NOVIDADES))
        self.nov_pag = (self.nov_pag + passo) % paginas
        self._atualizar_novidades()

    def _atualizar_novidades(self) -> None:
        """Mostra a página atual do resumo das atualizações (arquivo novidades.py)."""
        paginas = max(1, math.ceil(len(NOVIDADES) / LINHAS_NOVIDADES))
        self.nov_pag = min(self.nov_pag, paginas - 1)
        itens = NOVIDADES[self.nov_pag * LINHAS_NOVIDADES:(self.nov_pag + 1) * LINHAS_NOVIDADES]
        for n, (chip, txt, sub) in enumerate(self.linhas_nov):
            if n < len(itens):
                versao, data, tipo, texto = itens[n]
                rotulo, cor, fundo = NIVEIS_NOVIDADE.get(tipo, NIVEIS_NOVIDADE["novo"])
                chip.configure(text=T(TIPOS.get(tipo, "NOVO")), fg=cor, bg=fundo)
                txt.configure(text=T(texto))
                sub.configure(text=f"v{versao}  ·  {data}")
            else:
                chip.configure(text="", bg=SUP)
                txt.configure(text="")
                sub.configure(text="")
        self.lbl_nov_pag.configure(text=f"{self.nov_pag + 1}/{paginas}")

    def _abrir_pasta(self) -> None:
        try:
            PASTA_CONFIG.mkdir(parents=True, exist_ok=True)
            os.startfile(PASTA_CONFIG)  # noqa: S606  (só existe no Windows)
        except Exception as e:  # noqa: BLE001
            self._log("Não consegui abrir a pasta {pasta}: {e}", "erro", pasta=PASTA_CONFIG, e=e)

    def _restaurar_posicao(self) -> None:
        try:
            x, y = (int(v) for v in self.cfg["janela_pos"])
            if -50 <= x <= self.root.winfo_screenwidth() - 120 and 0 <= y <= self.root.winfo_screenheight() - 120:
                self.root.geometry(f"+{x}+{y}")  # só a posição: o tamanho continua o mesmo
        except Exception:
            pass

    def _limpar_log(self) -> None:
        self.historico_log.clear()
        self.txt_log.configure(state="normal")
        self.txt_log.delete("1.0", "end")
        self.txt_log.configure(state="disabled")
        self._atualizar_atividade()

    def _escolher_botao(self, chave: str) -> None:
        self.cfg["ac_botao"] = chave
        self._marcar_botao()
        self._salvar_depois()

    def _marcar_botao(self) -> None:
        atual = self.cfg.get("ac_botao")
        for chave, bt in self.btns_botao.items():
            if chave == atual:
                bt.ajustar(bg=GEMA, hover=misturar(GEMA, "#ffffff", 0.14), fg=TEXTO_BTN)
            else:
                bt.ajustar(bg=SUP2, hover=SUP3, fg=TEXTO)

    def _ac_ativo(self) -> bool:
        return bool(self.ac_worker and self.ac_worker.is_alive())

    def _set_ac(self, desc: str, texto: str, cor: str, **kw) -> None:
        """Texto grande do AutoClick (`texto`, com {campos} em `kw`) e a descrição de `desc` (chave de DESC_AC)."""
        self._ac_vis = (desc, texto, cor, kw)
        self.lbl_ac.configure(text=T(texto, **kw), fg=cor)
        self.lbl_ac_sub.configure(text=T(DESC_AC[desc]))

    def _pintar_botao_ac(self, rodando: bool) -> None:
        if rodando:
            self.btn_ac.ajustar(texto=T("Parar AutoClick  (F2)"), icone="stop", bg=SUP, fg=GEMA,
                                hover=misturar(SUP, GEMA, 0.16), contorno=GEMA)
        else:
            self.btn_ac.ajustar(texto=T("Iniciar AutoClick  (F2)"), icone="play", bg=GEMA, fg=TEXTO_BTN,
                                hover=misturar(GEMA, "#ffffff", 0.14), contorno=None)
        self.acoes["AutoClick"].ajustar(texto=T("Parar AutoClick") if rodando else T("AutoClick"), destaque=rodando)

    def parar_tudo(self) -> None:
        """Parada de emergência (botão e tecla Esc): para o macro e o AutoClick, o que estiver rodando."""
        if self.pesca_ativa():
            self.worker.parar.set()
            self._log("Parada de emergência (Esc).", "aviso")
        if self._ac_ativo():
            self.ac_worker.parar.set()
            self._log("Parada de emergência do AutoClick (Esc).", "aviso")

    def alternar_ac(self) -> None:
        if self._ac_ativo():
            self.ac_worker.parar.set()
            self._log("Parando o AutoClick...")
            return
        if self.pesca_ativa():
            self._log("Pare o macro de pesca (F1) antes de usar o AutoClick.", "aviso")
            return
        for chave in ("ac_intervalo", "ac_atraso", "ac_limite", "ac_dist_mouse"):
            self.campos[chave]._digitar()
        if self.cfg["ac_pos_fixa"] and not self.cfg.get("ac_pos"):
            self._log("Defina a posição fixa antes de iniciar (aba AutoClick).", "aviso")
            return
        salvar_config(self.cfg)
        self.ac_cliques = 0
        self.ac_t0 = 0.0
        self.ac_atraso_fim = 0.0
        self.stat_ac["cliques"].definir("0")
        self.stat_ac["cps"].definir("0")
        self.stat_ac["tempo"].definir("00:00:00")
        self.ac_worker = AutoClicker(self.cfg, self.fila)
        self.ac_worker.start()
        self._pintar_botao_ac(True)
        self._set_pilula("AutoClick", TURQUESA)
        self._log("AutoClick iniciado.", "ok")

    def _salvar_depois(self) -> None:
        if self._salvar_id:
            self.root.after_cancel(self._salvar_id)
        self._salvar_id = self.root.after(600, lambda: salvar_config(self.cfg))

    def _mudou(self, chave: str, valor) -> None:
        self.cfg[chave] = valor
        self._salvar_depois()

    def _opcao(self, chave: str, var: tk.BooleanVar) -> None:
        self.cfg[chave] = bool(var.get())
        if chave == "sempre_no_topo":
            self.root.attributes("-topmost", self.cfg[chave])
        if chave == "detectar":
            self._atualizar_calibracao()
        if chave == "minimizar_bandeja":
            self._aplicar_bandeja()
        self._salvar_depois()

    def _pedir_restaurar(self) -> None:
        """Primeiro clique pede confirmação no próprio botão; o segundo (em até 4 s) restaura."""
        if self._restaurar_pendente:
            self._cancelar_restaurar()
            self.restaurar()
            return
        self._restaurar_pendente = True
        self.btn_restaurar.ajustar(texto=T("Clique de novo para confirmar"), bg=GEMA, fg=TEXTO_BTN,
                                   hover=misturar(GEMA, "#ffffff", 0.14))
        self._restaurar_job = self.after(4000, self._cancelar_restaurar)

    def _cancelar_restaurar(self) -> None:
        self._restaurar_pendente = False
        job = getattr(self, "_restaurar_job", None)
        if job is not None:
            try:
                self.after_cancel(job)
            except tk.TclError:
                pass
            self._restaurar_job = None
        self.btn_restaurar.ajustar(texto=T("Restaurar padrões"), bg=SUP2, fg=TEXTO, hover=SUP3)

    def restaurar(self) -> None:
        for chave, campo in self.campos.items():
            campo.definir(PADRAO[chave])
            self.cfg[chave] = campo.get()
        self.var_roblox.set(PADRAO["so_roblox"])
        self.var_topo.set(PADRAO["sempre_no_topo"])
        self.var_detectar.set(PADRAO["detectar"])
        for chave, var in (("so_roblox", self.var_roblox), ("sempre_no_topo", self.var_topo),
                           ("detectar", self.var_detectar)):
            self._opcao(chave, var)
        self.var_ac_roblox.set(PADRAO["ac_so_roblox"])
        self._opcao("ac_so_roblox", self.var_ac_roblox)
        self.cfg["ac_botao"] = PADRAO["ac_botao"]
        self._marcar_botao()
        self._log("Ajustes restaurados para os padrões (a calibração foi mantida).", "ok")

    def _set_fase(self, nome: str, dur: float, texto: str = "") -> None:
        self.fase_nome, self.fase_ini, self.fase_dur, self.fase_texto = nome, time.perf_counter(), dur, texto
        self._pintar_fase()

    def _pintar_fase(self) -> None:
        nome = self.fase_nome
        self._desc = DESC_FASE.get(nome, "")
        if nome == "Parado" and hasattr(self, "itens_guia"):
            self._atualizar_parado()
        cor = COR_FASE.get(nome, TEXTO2)
        self.hero.definir(titulo=T(nome), cor=TEXTO if nome == "Parado" else cor)
        self.anel.definir(cor=cor, pct=0.0)
        if nome == "Parado":
            self.anel.definir(indeterminado=False, ativo=False, centro="—", rotulo=T("parado"))
        if self.fase_dur <= 0:
            self.hero.definir(descricao=T(self.fase_texto or self._desc))

    def _set_pilula(self, texto: str, cor: str) -> None:
        self._pilula = (texto, cor)
        self.pilula_txt.configure(text=T(texto), fg=TEXTO if cor != TEXTO3 else TEXTO2)
        self.pilula_pt.itemconfigure(self._pt_id, fill=cor)
        if self.bandeja is not None:
            self.bandeja.atualizar_dica(self._dica_bandeja())

    def _pintar_botao(self, rodando: bool) -> None:
        if rodando:
            self.btn.ajustar(texto=T("Parar  (F1)"), icone="stop", bg=SUP, fg=GEMA, hover=misturar(SUP, GEMA, 0.16), contorno=GEMA)
        else:
            self.btn.ajustar(texto=T("Iniciar  (F1)"), icone="play", bg=GEMA, fg=TEXTO_BTN,
                             hover=misturar(GEMA, "#ffffff", 0.14), contorno=None)

    def _atualizar_botao(self, rodando: bool) -> None:
        self._pintar_botao(rodando)
        self._set_pilula("Rodando", BROTO) if rodando else self._set_pilula("Parado", TEXTO3)

    def _lampada(self, visivel: bool | None) -> None:
        self._lamp = visivel
        if visivel is None:
            txt, cor = T("Botão PARAR: sem calibração"), TEXTO3
        elif visivel:
            txt, cor = T("Botão PARAR: visível agora"), BROTO
        else:
            txt, cor = T("Botão PARAR: não visível"), TEXTO2
        for lb in self._lampadas:
            lb.configure(text="•  " + txt, fg=cor)

    def _texto_deteccao(self) -> str:
        if not self.cfg.get("cal"):
            return T("Sem calibração")
        return T("Ativa") if self.cfg["detectar"] else T("Desligada")

    def _atualizar_calibracao(self) -> None:
        cal = self.cfg.get("cal")
        if cal:
            r, g, b = cal["cor"]
            self.cor_box.configure(bg=f"#{r:02x}{g:02x}{b:02x}")
            usando = T("detecção ativa") if self.cfg["detectar"] else T("tempos fixos")
            self.lbl_cal.configure(text=T("Calibrado para {larg}×{alt}, com {usando}.",
                                          larg=cal["larg"], alt=cal["alt"], usando=usando))
        else:
            self.cor_box.configure(bg=SUP2)
            self.lbl_cal.configure(text=T("Não calibrado: o macro usa os tempos fixos."))
            self._lampada(None)
        self.mosaicos["deteccao"].definir(self._texto_deteccao())
        if hasattr(self, "lbl_fixos"):
            em_uso = not (cal and self.cfg["detectar"])
            self.lbl_fixos.configure(text=T(FIXOS_EM_USO if em_uso else FIXOS_SEM_USO),
                                     fg=BROTO if em_uso else TEXTO3)
        if hasattr(self, "itens_guia"):
            self._atualizar_guia()

    def calibrar(self) -> None:
        """Com o mouse sobre a parte vermelha do botão PARAR, guarda posição (em proporção) e cor."""
        if self.pesca_ativa():
            self._log("Pare o macro (F1) antes de calibrar.", "aviso")
            return
        rect = rect_janela_roblox()
        if rect is None:
            self._log("Janela do Roblox não encontrada. Abra o jogo e deixe o minigame na tela.", "erro")
            return
        x, y = posicao_cursor()
        esq, topo, larg, alt = rect
        if not (esq <= x < esq + larg and topo <= y < topo + alt):
            self._log("O mouse precisa estar sobre a janela do Roblox, em cima do botão PARAR.", "erro")
            return
        dc = user32.GetDC(None)
        melhor, pontuacao = None, -999
        try:
            for dx, dy in GRADE:  # escolhe o ponto mais vermelho ao redor do mouse
                rgb = pixel_rgb(dc, x + dx, y + dy)
                if rgb:
                    p = rgb[0] - (rgb[1] + rgb[2]) / 2
                    if p > pontuacao:
                        melhor, pontuacao = rgb, p
        finally:
            user32.ReleaseDC(None, dc)
        if melhor is None:
            self._log("Não consegui ler a cor da tela nesse ponto.", "erro")
            return
        self.cfg["cal"] = {
            "rx": round((x - esq) / larg, 5),
            "ry": round((y - topo) / alt, 5),
            "cor": list(melhor),
            "larg": larg,
            "alt": alt,
        }
        salvar_config(self.cfg)
        self._atualizar_calibracao()
        r, g, b = melhor
        if pontuacao < 60:
            self._log("Calibrado, mas a cor RGB=({r},{g},{b}) não parece vermelha. Confira se o mouse "
                      "estava sobre o botão PARAR.", "aviso", r=r, g=g, b=b)
        else:
            self._log("Botão PARAR calibrado: cor RGB=({r},{g},{b}).", "ok", r=r, g=g, b=b)

    def limpar_calibracao(self) -> None:
        self.cfg["cal"] = None
        salvar_config(self.cfg)
        self._atualizar_calibracao()
        self._log("Calibração removida.")

    def alternar(self) -> None:
        if self.pesca_ativa():
            self.worker.parar.set()
            self._log("Parando...")
        elif self._ac_ativo():
            self._log("Pare o AutoClick (F2) antes de iniciar o macro de pesca.", "aviso")
        else:
            self.iniciar()

    def iniciar(self) -> None:
        for campo in self.campos.values():  # garante que valores digitados e não confirmados entrem
            campo._digitar()
        cal = self.cfg.get("cal")
        if self.cfg["detectar"] and not cal:
            self._log("Detecção ativada, mas sem calibração: usando os tempos fixos.", "aviso")
        elif self.cfg["detectar"] and cal:
            rect = rect_janela_roblox()
            if rect and (abs(rect[2] - cal["larg"]) > 0.02 * cal["larg"] or abs(rect[3] - cal["alt"]) > 0.02 * cal["alt"]):
                self._log("A janela do Roblox mudou de tamanho desde a calibração. Se o minigame não for "
                          "detectado, calibre de novo (F3).", "aviso")
        salvar_config(self.cfg)
        self.ciclos = self.cliques_base = self.cliques_ciclo = 0
        self.cps = self.cps_max = self.tempo_sessao = 0.0
        self.inicio_execucao = time.time()
        self.worker = Pescador(self.cfg, self.fila)
        self.worker.start()
        self._atualizar_botao(True)
        self._log("Macro iniciado.", "ok")

    # ------------------------------------------------------------------ loop
    def _tick(self) -> None:
        """Laço de atualização (a cada 50 ms). Um erro num evento é registrado e o laço continua."""
        try:
            self._tick_interno()
        except Exception as e:  # noqa: BLE001
            try:
                self._log("Erro interno: {e}", "erro", e=e)
            except Exception:  # noqa: BLE001
                pass
        self.root.after(50, self._tick)

    def _tick_interno(self) -> None:
        try:
            while True:
                tipo, dado = self.fila.get_nowait()
                if tipo == "log":
                    nivel, msg, kw = dado
                    self._log(msg, nivel, **kw)
                elif tipo == "fase":
                    self._set_fase(*dado)
                elif tipo == "visivel":
                    self._lampada(dado)
                elif tipo == "cliques":
                    self.cliques_ciclo = dado
                elif tipo == "ciclo":
                    cliques, dur, interrompido = dado
                    self.ciclos += 1
                    self.cliques_base += cliques
                    self.cliques_ciclo = 0
                    self.cps = cliques / dur
                    self.cps_max = max(self.cps_max, self.cps)
                    self._log(
                        "Ciclo {n} concluído: {cliques} cliques em {dur:.1f}s ({cps:.0f}/s)",
                        "aviso" if interrompido else "ok", n=self.ciclos, cliques=cliques, dur=dur, cps=self.cps,
                    )
                elif tipo == "fim":
                    decorrido = int(time.time() - self.inicio_execucao) if self.inicio_execucao else 0
                    self.inicio_execucao = 0.0
                    self._set_fase("Parado", 0)
                    self._atualizar_botao(False)
                    self._log("Macro parado.")
                    if self.ciclos:
                        h, m, s = decorrido // 3600, decorrido % 3600 // 60, decorrido % 60
                        self._log("Resumo da sessão: {ciclos} ciclos, {cliques} cliques em {tempo}.", "ok",
                                  ciclos=self.ciclos, cliques=self.cliques_base, tempo=f"{h:02d}:{m:02d}:{s:02d}")
                elif tipo == "ac_atraso":
                    self.ac_atraso_fim = time.perf_counter() + dado
                elif tipo == "ac_inicio":
                    self.ac_atraso_fim = 0.0
                    self.ac_t0 = time.perf_counter()
                    self._set_ac("Clicando", "Clicando", BROTO)
                elif tipo == "ac_cliques":
                    self.ac_cliques = dado
                elif tipo == "ac_fim":
                    cliques, dur = dado
                    self.ac_cliques = cliques
                    self.ac_atraso_fim = 0.0
                    self.ac_t0 = 0.0
                    self._set_ac("Parado", "Parado", TEXTO3)
                    self._pintar_botao_ac(False)
                    self._set_pilula("Parado", TEXTO3)
                    self.stat_ac["cliques"].definir(str(cliques))
                    self._log("AutoClick parado: {cliques} cliques em {dur:.1f}s ({cps:.0f}/s).", "ok",
                              cliques=cliques, dur=dur, cps=cliques / dur)
                elif tipo == "hk":
                    if self._capturando:  # escolhendo atalho: as teclas não disparam nada
                        continue
                    if dado == "f1":
                        self.alternar()
                    elif dado == "f2":
                        self.alternar_ac()
                    elif dado == "f3":
                        self.calibrar()
                    elif dado == "esc":
                        self.parar_tudo()
                elif tipo == "bandeja":
                    if dado == 1:
                        self.mostrar_janela()
                    elif dado == 2:
                        self.entrar_mini()
                    elif dado == 4:
                        self.alternar()
                    elif dado == 5:
                        self.alternar_ac()
                    elif dado == 6:
                        self.root.after(10, self._fechar)
        except queue.Empty:
            pass

        rodando = bool(self.worker and self.worker.is_alive())

        # anel, contagem regressiva e animação da etapa atual
        if rodando and self.fase_nome != "Parado":
            decorrido = time.perf_counter() - self.fase_ini
            self._pulso += 0.22
            brilho = (math.sin(self._pulso) + 1) / 2
            self.pilula_pt.itemconfigure(self._pt_id, fill=misturar(misturar(BROTO, BG, 0.6), BROTO, brilho))
            if self.fase_dur > 0:
                resta = max(0.0, self.fase_dur - decorrido)
                self.anel.definir(pct=min(1.0, decorrido / self.fase_dur), indeterminado=False,
                                  centro=f"{resta:.1f}", rotulo=T("segundos"), ativo=True)
                prefixo = T(self.fase_texto or "restam")
                self.hero.definir(descricao=f"{T(self._desc)}\n{prefixo} {resta:.1f} s")
            elif self.fase_nome == "Clicando":
                self.anel.definir(pct=0.0, indeterminado=True, centro=str(self.cliques_ciclo),
                                  rotulo=T("cliques"), ativo=True)
            else:
                self.anel.definir(pct=0.0, indeterminado=True, centro="…", rotulo=T("aguardando"), ativo=False)
            self.anel.animar()

        # teste ao vivo da detecção (só quando o macro está parado)
        self._n += 1
        cal = self.cfg.get("cal")
        if not rodando and cal and self._n % 6 == 0:
            try:
                self._lampada(minigame_visivel(cal, int(self.cfg["tolerancia"])))
            except Exception:
                pass
        if self._n % 10 == 0:  # a janela do Roblox está aberta?
            aberto = rect_janela_roblox() is not None
            if aberto != self._roblox_aberto:
                self._roblox_aberto = aberto
                self.mosaicos["roblox"].definir(T("Aberto") if aberto else T("Fechado"))
                self._atualizar_guia()

        # números da sessão
        if rodando:
            self.tempo_sessao = time.time() - self.inicio_execucao
        t = int(self.tempo_sessao)
        total_cliques = self.cliques_base + self.cliques_ciclo
        self.mosaicos["ciclos"].definir(str(self.ciclos))
        self.mosaicos["cliques"].definir(str(total_cliques))
        self.mosaicos["cps"].definir(f"{self.cps:.0f}")
        self.mosaicos["tempo"].definir(f"{t // 3600:02d}:{t % 3600 // 60:02d}:{t % 60:02d}")
        self.mosaicos["ciclos_min"].definir(f"{self.ciclos / (self.tempo_sessao / 60):.1f}" if self.tempo_sessao >= 10 and self.ciclos else "0")
        self.mosaicos["media"].definir(f"{self.cliques_base / self.ciclos:.0f}" if self.ciclos else "0")
        self.mosaicos["melhor"].definir(f"{self.cps_max:.0f}/s" if self.cps_max else "—")

        # AutoClick: contagem do atraso, estatísticas e taxa estimada
        if self._ac_ativo():
            agora = time.perf_counter()
            if self.ac_atraso_fim > agora:
                self._set_ac("Contagem", "Começa em {s:.1f} s", PALHA, s=self.ac_atraso_fim - agora)
            elif self.ac_t0:
                dec = max(0.001, agora - self.ac_t0)
                self.stat_ac["cliques"].definir(str(self.ac_cliques))
                self.stat_ac["cps"].definir(f"{self.ac_cliques / dec:.0f}")
                ts = int(dec)
                self.stat_ac["tempo"].definir(f"{ts // 3600:02d}:{ts % 3600 // 60:02d}:{ts % 60:02d}")
        try:
            ms = max(1.0, float(self.cfg["ac_intervalo"]))
            if ms >= 1000:
                self.lbl_ac_taxa.configure(text=T("1 clique a cada {t}", t=texto_duracao(ms)))
            else:
                self.lbl_ac_taxa.configure(text=T("≈ {n:.1f} cliques por segundo", n=1000 / ms))
        except (TypeError, ValueError):
            pass

        if self.mini is not None and self.mini.visivel:
            self.mini.atualizar()

    def _pedir_fechar(self) -> None:
        """Ao clicar em fechar: pergunta se é para encerrar de vez ou só minimizar para a bandeja."""
        if getattr(self, "_dialogo_fechar", None) is not None:
            try:
                if self._dialogo_fechar.winfo_exists():
                    self._dialogo_fechar.focus_force()
                    return
            except tk.TclError:
                pass
        if self.root.state() != "normal":  # escondida (bandeja/mini): mostra a janela para a pergunta aparecer
            self.mostrar_janela()
        rodando = self.pesca_ativa() or self._ac_ativo()
        texto = T("O programa será encerrado e a pesca e o AutoClick vão parar.") if rodando else \
            T("O programa será encerrado. Se preferir, ele pode continuar aberto no formato mini.")
        self._dialogo_fechar = DialogoFechar(
            self.root, T("Tem certeza que deseja fechar o programa?"), texto,
            T("Cancelar"), T("Fechar o programa"), T("Deixar no formato mini e continuar aberto"),
            self._fechar, self.entrar_mini)

    def _fechar(self) -> None:
        if self.worker and self.worker.is_alive():
            self.worker.parar.set()
        if self._ac_ativo():
            self.ac_worker.parar.set()
        if self.bandeja is not None:
            self.bandeja.encerrar()
        try:
            for campo in self.campos.values():
                campo._digitar()
            if self.root.state() == "normal":  # escondida (bandeja ou modo mini), a posição não vale
                self.cfg["janela_pos"] = [self.root.winfo_x(), self.root.winfo_y()]
            salvar_config(self.cfg)
            self.hotkeys.stop()
        except Exception:
            pass
        self.root.destroy()


def main() -> None:
    try:  # a barra de tarefas usa o ícone do programa (e não o do Python) quando roda pelo Abrir.bat
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("RoubeUmOvo.App")
    except Exception:
        pass
    if ja_esta_aberto():  # duas cópias disputariam o mouse e os atalhos: só uma roda
        mostrar_janela_existente(T("Roube um Ovo"))
        return
    janela = tk.Tk()
    App(janela)
    janela.mainloop()
