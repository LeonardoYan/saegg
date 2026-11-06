"""Componentes visuais próprios (botão, toggle, slider, anel de progresso, campo de ajuste)."""
import math
import tkinter as tk
from tkinter import font as tkfont

from . import tema
from .idioma import T
from .tema import (
    BG, BORDA, BROTO, ERRO, F, FN, GEMA, GRADIENTE_HERO, LILAS, misturar, PALHA, PLACA_HERO, px, SUP, SUP2, SUP3, TEXTO,
    TEXTO2, TEXTO3, TEXTO_BTN, TURQUESA,
)


def retangulo_redondo(cv: tk.Canvas, x1, y1, x2, y2, r, **kw) -> int:
    r = max(0, min(r, (x2 - x1) / 2, (y2 - y1) / 2))
    pts = [x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r, x2, y2 - r, x2, y2,
           x2 - r, y2, x1 + r, y2, x1, y2, x1, y2 - r, x1, y1 + r, x1, y1]
    return cv.create_polygon(pts, smooth=True, **kw)


def cartao(pai: tk.Misc) -> tk.Frame:
    return tk.Frame(pai, bg=SUP, highlightbackground=BORDA, highlightcolor=BORDA, highlightthickness=1)


def titulo_secao(pai, texto: str, bg: str = SUP) -> tk.Label:
    return tk.Label(pai, text=texto, font=F(9, "bold"), bg=bg, fg=TEXTO2, anchor="w")


def tecla(pai, texto: str) -> tk.Label:
    return tk.Label(pai, text=texto, font=(tema.MONO, 8, "bold"), bg=SUP2, fg=TEXTO2, padx=px(6), pady=px(1),
                    bd=0, highlightthickness=1, highlightbackground=BORDA)


class Logo(tk.Canvas):
    """O ovo (marca do programa): casca clara com pintinhas sobre um ninho dourado."""

    def __init__(self, pai, tam: int = 40, bg: str = BG):
        t = px(tam)
        super().__init__(pai, width=t, height=t, bg=bg, highlightthickness=0, bd=0)
        s = t / 40
        retangulo_redondo(self, 1, 1, t - 1, t - 1, 11 * s, fill="#243447", outline="#243447")
        pontos = []  # silhueta do ovo: mais larga embaixo
        for k in range(72):
            a = 2 * math.pi * k / 72
            pontos += [(20 + 8.6 * math.sin(a) * (1 - 0.17 * math.cos(a))) * s, (19.5 - 11.5 * math.cos(a)) * s]
        self.create_polygon(pontos, fill="#fff6e3", outline="")
        self.create_oval(14.0 * s, 11.2 * s, 17.4 * s, 16.6 * s, fill="#ffffff", outline="")  # brilho
        for x, y, r in ((22.5, 17.0, 0.95), (18.4, 24.0, 0.85), (24.2, 24.6, 0.7), (21.0, 12.4, 0.6)):
            self.create_oval((x - r) * s, (y - r) * s, (x + r) * s, (y + r) * s, fill="#d9b27c", outline="")
        self.create_arc(7 * s, 26 * s, 33 * s, 38 * s, start=205, extent=130, style="arc",
                        outline=GEMA, width=max(1, int(2 * s)))


class Botao(tk.Canvas):
    """Botão com cantos arredondados, hover e clique."""

    def __init__(self, pai, texto, comando, bg=SUP2, fg=TEXTO, hover=SUP3, fonte=None, altura=30, largura=None,
                 raio=8, fundo=SUP, contorno=None, icone=None):
        super().__init__(pai, height=px(altura), width=px(largura) if largura else px(10), bg=fundo,
                         highlightthickness=0, bd=0, cursor="hand2")
        self.texto, self.comando = texto, comando
        self.cor, self.fg, self.hover, self.contorno = bg, fg, hover, contorno
        self.fonte = fonte or F(9, "bold")
        self.raio = raio
        self.icone = icone  # "play", "stop" ou "expandir": desenhado à mão, sem depender da fonte
        self._sobre = False
        self._baixo = False
        self.bind("<Configure>", lambda _e: self._desenhar())
        self.bind("<Enter>", lambda _e: self._estado(sobre=True))
        self.bind("<Leave>", lambda _e: self._estado(sobre=False, baixo=False))
        self.bind("<ButtonPress-1>", lambda _e: self._estado(baixo=True))
        self.bind("<ButtonRelease-1>", self._soltar)

    def _estado(self, sobre=None, baixo=None) -> None:
        if sobre is not None:
            self._sobre = sobre
        if baixo is not None:
            self._baixo = baixo
        self._desenhar()

    def _soltar(self, e) -> None:
        estava = self._baixo
        self._estado(baixo=False)
        if estava and 0 <= e.x <= self.winfo_width() and 0 <= e.y <= self.winfo_height() and self.comando:
            self.comando()

    def _desenhar(self) -> None:
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        if w < 6 or h < 6:
            return
        cor = self.hover if self._sobre else self.cor
        if self._baixo:
            cor = misturar(cor, "#000000", 0.18)
        retangulo_redondo(self, 1, 1, w - 1, h - 1, px(self.raio), fill=cor, outline=self.contorno or cor,
                          width=max(1, px(1)))
        if not self.icone:
            self.create_text(w / 2, h / 2, text=self.texto, fill=self.fg, font=self.fonte)
            return
        lado = int(h * 0.34)
        folga = px(8)
        larg_txt = tkfont.Font(font=self.fonte).measure(self.texto) if self.texto else 0
        total = lado + (folga + larg_txt if self.texto else 0)
        x0 = (w - total) / 2
        cy = h / 2
        if self.icone == "play":
            self.create_polygon(x0, cy - lado * 0.6, x0, cy + lado * 0.6, x0 + lado, cy, fill=self.fg, outline="")
        elif self.icone == "stop":
            self.create_rectangle(x0, cy - lado / 2, x0 + lado, cy + lado / 2, fill=self.fg, outline="")
        elif self.icone == "expandir":  # dois cantos opostos apontando para fora
            e, k = max(2, px(2)), lado * 0.45
            for (ax, ay, dx, dy) in ((x0, cy + lado / 2, 1, -1), (x0 + lado, cy - lado / 2, -1, 1)):
                self.create_line(ax, ay + dy * k, ax, ay, ax + dx * k, ay, fill=self.fg, width=e, capstyle="round",
                                 joinstyle="round")
        if self.texto:
            self.create_text(x0 + lado + folga, cy, text=self.texto, fill=self.fg, font=self.fonte, anchor="w")

    def ajustar(self, texto=None, bg=None, hover=None, fg=None, contorno="-", icone="-") -> None:
        if icone != "-":
            self.icone = icone
        if texto is not None:
            self.texto = texto
        if bg is not None:
            self.cor = bg
        if hover is not None:
            self.hover = hover
        if fg is not None:
            self.fg = fg
        if contorno != "-":
            self.contorno = contorno
        self._desenhar()


class Toggle(tk.Canvas):
    """Interruptor ligado a uma BooleanVar, com animação curta."""

    def __init__(self, pai, var: tk.BooleanVar, comando=None, bg: str = SUP):
        self.L, self.A = px(38), px(20)
        super().__init__(pai, width=self.L, height=self.A, bg=bg, highlightthickness=0, bd=0, cursor="hand2")
        self.var, self.comando = var, comando
        self._pos = 1.0 if var.get() else 0.0
        self._job = None
        self.bind("<Button-1>", self._clicar)
        var.trace_add("write", lambda *_: self._iniciar_animacao())
        self._desenhar()

    def _clicar(self, _e) -> None:
        self.var.set(not self.var.get())
        if self.comando:
            self.comando()

    def _iniciar_animacao(self) -> None:
        if self._job is None:
            self._passo()

    def _passo(self) -> None:
        alvo = 1.0 if self.var.get() else 0.0
        try:
            if abs(self._pos - alvo) < 0.02:
                self._pos, self._job = alvo, None
                self._desenhar()
                return
            self._pos += (alvo - self._pos) * 0.45
            self._desenhar()
            self._job = self.after(16, self._passo)
        except tk.TclError:
            self._job = None

    def _desenhar(self) -> None:
        self.delete("all")
        L, A = self.L, self.A
        cor = misturar(SUP3, TURQUESA, self._pos)
        self.create_oval(0, 0, A, A, fill=cor, outline=cor)
        self.create_oval(L - A, 0, L, A, fill=cor, outline=cor)
        self.create_rectangle(A / 2, 0, L - A / 2, A, fill=cor, outline=cor)
        r = A / 2 - px(3)
        cx = A / 2 + self._pos * (L - A)
        self.create_oval(cx - r, A / 2 - r, cx + r, A / 2 + r, fill="#ffffff", outline="#ffffff")


class Slider(tk.Canvas):
    """Controle deslizante fino, arrastável com o mouse."""

    def __init__(self, pai, minimo, maximo, passo, valor, comando, bg: str = SUP):
        super().__init__(pai, height=px(22), width=px(80), bg=bg, highlightthickness=0, bd=0, cursor="hand2")
        self.minimo, self.maximo, self.passo, self.valor, self.comando = minimo, maximo, passo, valor, comando
        self.m = px(9)
        self.bind("<Configure>", lambda _e: self._desenhar())
        self.bind("<ButtonPress-1>", self._mover)
        self.bind("<B1-Motion>", self._mover)

    def _x(self, v: float) -> float:
        w = max(self.winfo_width(), 2 * self.m + 1)
        f = (v - self.minimo) / (self.maximo - self.minimo)
        return self.m + max(0.0, min(1.0, f)) * (w - 2 * self.m)

    def _desenhar(self) -> None:
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        if w < 4 * self.m:
            return
        cy, xv, esp = h / 2, self._x(self.valor), px(4)
        self.create_line(self.m, cy, w - self.m, cy, fill=SUP3, width=esp, capstyle="round")
        self.create_line(self.m, cy, xv, cy, fill=TURQUESA, width=esp, capstyle="round")
        r = px(7)
        self.create_oval(xv - r, cy - r, xv + r, cy + r, fill="#ffffff", outline=TURQUESA, width=max(1, px(2)))

    def _mover(self, e) -> None:
        w = max(self.winfo_width(), 2 * self.m + 1)
        f = max(0.0, min(1.0, (e.x - self.m) / (w - 2 * self.m)))
        v = self.minimo + f * (self.maximo - self.minimo)
        v = round(v / self.passo) * self.passo
        v = max(self.minimo, min(self.maximo, v))
        if v != self.valor:
            self.valor = v
            self._desenhar()
            self.comando(v)

    def definir(self, v: float) -> None:
        self.valor = v
        self._desenhar()


class Anel(tk.Canvas):
    """Anel de progresso da etapa atual. Com o macro rodando, ondas saem do centro como um sonar."""

    def __init__(self, pai, tam: int = 140, espessura: int = 8, bg: str = SUP):
        t = px(tam)
        super().__init__(pai, width=t, height=t, bg=bg, highlightthickness=0, bd=0)
        self.t, self.esp, self.fundo = t, px(espessura), bg
        self.cor, self.pct, self.rot, self.fase = TEXTO3, 0.0, 0.0, 0.0
        self.indeterminado, self.ativo = False, False
        self.centro, self.rotulo = "—", "parado"
        self._desenhar()

    def definir(self, cor=None, pct=None, indeterminado=None, centro=None, rotulo=None, ativo=None) -> None:
        mudou = False
        for nome, valor in (("cor", cor), ("pct", pct), ("indeterminado", indeterminado),
                            ("centro", centro), ("rotulo", rotulo), ("ativo", ativo)):
            if valor is not None and getattr(self, nome) != valor:
                setattr(self, nome, valor)
                mudou = True
        if mudou:
            self._desenhar()

    def animar(self) -> None:
        self.fase = (self.fase + 0.02) % 1.0
        if self.indeterminado:
            self.rot = (self.rot - 8) % 360
        self._desenhar()

    def _desenhar(self) -> None:
        self.delete("all")
        c = self.t / 2
        m = self.esp / 2 + px(3)
        caixa = (m, m, self.t - m, self.t - m)
        raio_int = c - m - self.esp / 2 - px(4)
        r0 = self.t * 0.23  # as ondas ficam fora da área do número central
        if raio_int - r0 < px(12):  # anel pequeno: sem ondas, só o anel de progresso
            pass
        elif self.ativo:  # ondas que nascem junto ao número e somem perto do anel
            for deslocamento in (0.0, 0.5):
                f = (self.fase + deslocamento) % 1.0
                r = r0 + f * (raio_int - r0)
                self.create_oval(c - r, c - r, c + r, c + r, outline=misturar(self.cor, self.fundo, 0.25 + 0.75 * f),
                                 width=max(1, px(1)))
        else:  # ondas paradas, só como textura
            for f in (0.35, 0.8):
                r = r0 + f * (raio_int - r0)
                self.create_oval(c - r, c - r, c + r, c + r, outline=misturar(SUP2, self.fundo, 0.2),
                                 width=max(1, px(1)))
        self.create_oval(*caixa, outline=SUP2, width=self.esp)
        if self.indeterminado:
            self.create_arc(*caixa, start=self.rot, extent=95, style="arc", outline=self.cor, width=self.esp)
        elif self.pct > 0:
            self.create_arc(*caixa, start=90, extent=-max(1.0, 359.9 * min(1.0, self.pct)), style="arc",
                            outline=self.cor, width=self.esp)
        self.create_text(c, c - px(5), text=self.centro, fill=TEXTO, font=FN(18))
        self.create_text(c, c + px(16), text=self.rotulo, fill=TEXTO3, font=F(8))


class Campo:
    """Uma linha de ajuste: rótulo + controle deslizante + caixa para digitar o valor."""

    def __init__(self, pai, linha, chave, rotulo, minimo, maximo, passo_slider, passo_fino, unidade, valor, ao_mudar,
                 empilhado=False, fundo=SUP, ajuda=None, padrao=None):
        self.chave = chave
        self._ajuda, self._padrao, self._unidade = ajuda, padrao, unidade
        self.minimo, self.maximo = minimo, maximo
        self.passo_slider, self.passo_fino = passo_slider, passo_fino
        self.inteiro = isinstance(passo_fino, int)
        self.ao_mudar = ao_mudar

        self.var = tk.DoubleVar(value=valor)
        self.txt = tk.StringVar(value=self._fmt(valor))

        if ajuda:  # rótulo + ícone ? (o balão com a explicação aparece ao passar o mouse)
            topo = tk.Frame(pai, bg=fundo)
            rot = tk.Label(topo, text=rotulo, bg=fundo, fg=TEXTO, font=F(9), anchor="w")
            rot.pack(side="left")
            AjudaIcone(topo, self._texto_ajuda, fundo).pack(side="left", padx=(px(6), 0))
            Dica(rot, self._texto_ajuda)
        else:
            topo = rot = tk.Label(pai, text=rotulo, bg=fundo, fg=TEXTO, font=F(9), anchor="w")
        self.slider = Slider(pai, minimo, maximo, passo_slider, valor, self._mover, bg=fundo)
        entrada = tk.Entry(
            pai, textvariable=self.txt, width=6, justify="center", bg=SUP2, fg=TEXTO, insertbackground=TEXTO,
            relief="flat", highlightthickness=1, highlightbackground=BORDA, highlightcolor=TURQUESA, font=F(9),
        )
        un = tk.Label(pai, text=unidade, bg=fundo, fg=TEXTO3, font=F(9), width=5, anchor="w")
        if empilhado:  # rótulo em cima; embaixo o controle deslizante, o valor e a unidade
            topo.grid(row=2 * linha, column=0, columnspan=3, sticky="w", pady=(px(6), 0))
            self.slider.grid(row=2 * linha + 1, column=0, sticky="ew", padx=(0, px(10)))
            entrada.grid(row=2 * linha + 1, column=1, ipady=px(3))
            un.grid(row=2 * linha + 1, column=2, padx=(px(4), 0))
        else:
            topo.grid(row=linha, column=0, sticky="w", pady=px(5))
            self.slider.grid(row=linha, column=1, sticky="ew", padx=(px(10), px(12)))
            entrada.grid(row=linha, column=2, ipady=px(3))
            un.grid(row=linha, column=3, padx=(px(4), 0))
        entrada.bind("<Return>", self._digitar)
        entrada.bind("<FocusOut>", self._digitar)

    def _fmt(self, v: float) -> str:
        return str(int(round(v))) if self.inteiro else f"{v:.1f}"

    def _texto_ajuda(self) -> str:
        """Explicação do ajuste e o valor padrão (no idioma atual)."""
        texto = T(self._ajuda) if self._ajuda else ""
        if self._padrao is not None:
            texto += "\n" + T("Padrão: {v} {u}", v=self._fmt(float(self._padrao)), u=self._unidade).strip()
        return texto

    def _ajustar(self, v: float, passo: float):
        v = round(v / passo) * passo
        v = max(self.minimo, min(self.maximo, v))
        return int(round(v)) if self.inteiro else round(v, 1)

    def _mover(self, valor) -> None:
        v = self._ajustar(float(valor), self.passo_slider)
        self.var.set(v)
        self.txt.set(self._fmt(v))
        self.ao_mudar(self.chave, v)

    def _digitar(self, _evento=None) -> None:
        try:
            v = self._ajustar(float(self.txt.get().replace(",", ".")), self.passo_fino)
        except ValueError:
            v = self.get()
        self.var.set(v)
        self.txt.set(self._fmt(v))
        self.slider.definir(v)
        self.ao_mudar(self.chave, v)

    def get(self):
        return self._ajustar(self.var.get(), self.passo_fino)

    def definir(self, valor) -> None:
        v = self._ajustar(float(valor), self.passo_fino)
        self.var.set(v)
        self.txt.set(self._fmt(v))
        self.slider.definir(v)


# ====================================================================== ícones e componentes da nova interface
def _estrela(cx, cy, r1, r2, pontas=5) -> list:
    pts = []
    for k in range(2 * pontas):
        a = -math.pi / 2 + k * math.pi / pontas
        r = r1 if k % 2 == 0 else r2
        pts += [cx + r * math.cos(a), cy + r * math.sin(a)]
    return pts


def desenhar_icone(cv: tk.Canvas, nome: str, cx: float, cy: float, tam: float, cor: str) -> None:
    """Desenha um ícone simples (traços e formas) centrado em (cx, cy), cabendo num quadrado de `tam` pixels."""
    u = tam / 24.0
    w = max(1.4, 1.9 * u)

    def P(*v):  # grade de 24x24 -> pixels
        return [(cx if i % 2 == 0 else cy) + (c - 12) * u for i, c in enumerate(v)]

    def linha(*v):
        cv.create_line(*P(*v), fill=cor, width=w, capstyle="round", joinstyle="round")

    def contorno(*v):
        cv.create_polygon(*P(*v), fill="", outline=cor, width=w, joinstyle="round")

    def cheio(*v):
        cv.create_polygon(*P(*v), fill=cor, outline=cor, width=1, joinstyle="round")

    def oval(x1, y1, x2, y2, preenchido=False):
        cv.create_oval(*P(x1, y1, x2, y2), fill=cor if preenchido else "", outline=cor, width=w)

    if nome == "casa":
        linha(3, 11, 12, 3.5, 21, 11)
        linha(5.5, 9.5, 5.5, 20, 10, 20, 10, 14.5, 14, 14.5, 14, 20, 18.5, 20, 18.5, 9.5)
    elif nome == "alvo":
        oval(4, 4, 20, 20)
        oval(10, 10, 14, 14, True)
        linha(12, 1.5, 12, 6)
        linha(12, 18, 12, 22.5)
        linha(1.5, 12, 6, 12)
        linha(18, 12, 22.5, 12)
    elif nome == "cursor":
        cheio(6.5, 3, 6.5, 19.5, 10.5, 15.5, 13.5, 21.5, 16.2, 20.3, 13.2, 14.2, 18.8, 14.2)
    elif nome == "engrenagem":
        oval(7, 7, 17, 17)
        oval(10.5, 10.5, 13.5, 13.5, True)
        for k in range(8):
            a = k * math.pi / 4
            linha(12 + 8 * math.cos(a), 12 + 8 * math.sin(a), 12 + 11 * math.cos(a), 12 + 11 * math.sin(a))
    elif nome == "lista":
        for y in (6, 12, 18):
            oval(3.2, y - 1.3, 5.8, y + 1.3, True)
            linha(9, y, 21, y)
    elif nome == "ovo":
        pts = []
        for k in range(36):
            a = 2 * math.pi * k / 36
            pts += [12 + 6.4 * math.sin(a) * (1 - 0.17 * math.cos(a)), 13.2 - 8.6 * math.cos(a)]
        contorno(*pts)
    elif nome == "pasta":
        contorno(3, 6.5, 3, 19, 21, 19, 21, 9, 11.5, 9, 9.5, 6.5)
    elif nome == "parar":
        cheio(6.5, 6.5, 17.5, 6.5, 17.5, 17.5, 6.5, 17.5)
    elif nome == "mini":
        contorno(3, 5, 21, 5, 21, 19, 3, 19)
        cheio(12, 11, 19, 11, 19, 17, 12, 17)
    elif nome == "relogio":
        oval(3.5, 3.5, 20.5, 20.5)
        linha(12, 7.5, 12, 12, 15.8, 14)
    elif nome == "ciclos":
        cv.create_arc(*P(4, 4, 20, 20), start=30, extent=290, style="arc", outline=cor, width=w)
        cheio(16, 5, 21.5, 6, 19, 11.5)
    elif nome == "raio":
        cheio(13.5, 2, 5, 13.5, 11, 13.5, 10, 22, 19, 10, 13, 10)
    elif nome == "ampulheta":
        contorno(6, 3, 18, 3, 18, 6.5, 13, 12, 18, 17.5, 18, 21, 6, 21, 6, 17.5, 11, 12, 6, 6.5)
    elif nome == "barras":
        cheio(4, 13, 8, 13, 8, 20, 4, 20)
        cheio(10, 7, 14, 7, 14, 20, 10, 20)
        cheio(16, 10, 20, 10, 20, 20, 16, 20)
    elif nome == "estrela":
        contorno(*_estrela(12, 12.5, 9.5, 4.2))
    elif nome == "olho":
        oval(2.5, 7, 21.5, 17)
        oval(9, 9, 15, 15, True)
    elif nome == "janela":
        contorno(3, 4.5, 21, 4.5, 21, 19.5, 3, 19.5)
        linha(3, 9.5, 21, 9.5)
    elif nome == "play":
        cheio(8, 5, 8, 19, 19, 12)
    elif nome == "check":
        linha(5, 12.5, 10, 17.5, 19, 7)
    elif nome == "ajuda":
        oval(3.5, 3.5, 20.5, 20.5)
        cv.create_text(cx, cy - 0.5 * u, text="?", fill=cor, font=(tema.FONTE, max(8, int(13 * u)), "bold"))
    else:  # ícone desconhecido: um ponto
        oval(9, 9, 15, 15, True)


def cabecalho_cartao(pai, icone: str, texto: str, bg: str = SUP) -> tk.Frame:
    """Título de cartão: ícone pequeno e texto em maiúsculas (ex.: SESSÃO)."""
    f = tk.Frame(pai, bg=bg)
    t = px(16)
    cv = tk.Canvas(f, width=t, height=t, bg=bg, highlightthickness=0, bd=0)
    cv.pack(side="left", padx=(0, px(8)))
    desenhar_icone(cv, icone, t / 2, t / 2, t * 0.95, GEMA)
    tk.Label(f, text=texto.upper(), font=F(9, "bold"), bg=bg, fg=TEXTO2, anchor="w").pack(side="left")
    return f


def etiqueta(pai, texto: str, fg: str, bg: str) -> tk.Label:
    """Etiqueta pequena (OK, AVISO...)."""
    return tk.Label(pai, text=texto, font=F(7, "bold"), bg=bg, fg=fg, padx=px(6), pady=px(2))


class IconeTile(tk.Canvas):
    """Quadrado arredondado com cor suave e um ícone."""

    def __init__(self, pai, nome: str, cor: str, tam: int = 36, fundo: str = SUP, raio: int = 10, mistura: float = 0.2):
        t = px(tam)
        super().__init__(pai, width=t, height=t, bg=fundo, highlightthickness=0, bd=0)
        retangulo_redondo(self, 0, 0, t, t, px(raio), fill=misturar(fundo, cor, mistura), outline="")
        desenhar_icone(self, nome, t / 2, t / 2, t * 0.52, cor)


class BotaoLateral(tk.Canvas):
    """Item da barra lateral: ícone com o nome embaixo. O item ativo ganha fundo e uma barrinha na borda."""

    def __init__(self, pai, icone: str, texto: str, comando, largura: int, altura: int = 60):
        super().__init__(pai, width=px(largura), height=px(altura), bg=BG, highlightthickness=0, bd=0, cursor="hand2")
        self.icone, self.texto, self.comando = icone, texto, comando
        self.ativo, self._sobre = False, False
        self.bind("<Configure>", lambda _e: self._desenhar())
        self.bind("<Enter>", lambda _e: self._estado(True))
        self.bind("<Leave>", lambda _e: self._estado(False))
        self.bind("<ButtonRelease-1>", self._soltar)

    def _estado(self, sobre: bool) -> None:
        self._sobre = sobre
        self._desenhar()

    def _soltar(self, e) -> None:
        if 0 <= e.x <= self.winfo_width() and 0 <= e.y <= self.winfo_height() and self.comando:
            self.comando()

    def definir_ativo(self, ativo: bool) -> None:
        if ativo != self.ativo:
            self.ativo = ativo
            self._desenhar()

    def _desenhar(self) -> None:
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        if w < 10 or h < 10:
            return
        if self.ativo:
            retangulo_redondo(self, px(9), px(2), w - px(9), h - px(2), px(12), fill=SUP2, outline=BORDA)
            self.create_rectangle(0, px(14), px(3), h - px(14), fill=GEMA, outline="")
        elif self._sobre:
            retangulo_redondo(self, px(9), px(2), w - px(9), h - px(2), px(12), fill=SUP, outline="")
        cor = GEMA if self.ativo else (TEXTO if self._sobre else TEXTO2)
        desenhar_icone(self, self.icone, w / 2, h * 0.36, px(22), cor)
        self.create_text(w / 2, h * 0.74, text=self.texto, fill=TEXTO if self.ativo else TEXTO3, font=F(8, "bold"))

    def traduzir(self, texto: str) -> None:
        self.texto = texto
        self._desenhar()


class Aba(tk.Canvas):
    """Aba da navegação no topo: ícone e nome lado a lado. A aba aberta ganha fundo azul claro e uma linha embaixo."""

    def __init__(self, pai, icone: str, texto: str, comando, largura: int = 124, altura: int = 40):
        super().__init__(pai, width=px(largura), height=px(altura), bg=BG, highlightthickness=0, bd=0, cursor="hand2")
        self.icone, self.texto, self.comando = icone, texto, comando
        self.ativo, self._sobre = False, False
        self.bind("<Configure>", lambda _e: self._desenhar())
        self.bind("<Enter>", lambda _e: self._estado(True))
        self.bind("<Leave>", lambda _e: self._estado(False))
        self.bind("<ButtonRelease-1>", self._soltar)

    def _estado(self, sobre: bool) -> None:
        self._sobre = sobre
        self._desenhar()

    def _soltar(self, e) -> None:
        if 0 <= e.x <= self.winfo_width() and 0 <= e.y <= self.winfo_height() and self.comando:
            self.comando()

    def definir_ativo(self, ativo: bool) -> None:
        if ativo != self.ativo:
            self.ativo = ativo
            self._desenhar()

    def traduzir(self, texto: str) -> None:
        self.texto = texto
        self._desenhar()

    def _desenhar(self) -> None:
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        if w < 10 or h < 10:
            return
        if self.ativo:
            retangulo_redondo(self, px(2), px(2), w - px(2), h - px(2), px(10), fill=misturar(SUP, GEMA, 0.12), outline="")
        elif self._sobre:
            retangulo_redondo(self, px(2), px(2), w - px(2), h - px(2), px(10), fill=SUP3, outline="")
        cor = GEMA if self.ativo else (TEXTO if self._sobre else TEXTO2)
        fonte = F(10, "bold") if self.ativo else F(10)
        # ícone + texto centralizados juntos
        largura_txt = tkfont.Font(font=fonte).measure(self.texto)
        total = px(18) + px(8) + largura_txt
        x0 = (w - total) / 2
        desenhar_icone(self, self.icone, x0 + px(9), h / 2, px(18), cor)
        self.create_text(x0 + px(26), h / 2, text=self.texto, anchor="w", fill=TEXTO if self.ativo else cor, font=fonte)
        if self.ativo:
            self.create_rectangle(px(14), h - px(3), w - px(14), h - px(1), fill=GEMA, outline="")


class AcaoRapida(tk.Canvas):
    """Atalho em forma de cartão: quadrado colorido com ícone, nome e uma dica curta."""

    def __init__(self, pai, icone: str, cor: str, texto: str, dica: str, comando, altura: int = 58, fundo: str = BG):
        super().__init__(pai, height=px(altura), width=px(10), bg=fundo, highlightthickness=0, bd=0, cursor="hand2")
        self.icone, self.cor, self.texto, self.dica, self.comando = icone, cor, texto, dica, comando
        self.destaque, self._sobre, self._baixo = False, False, False
        self.bind("<Configure>", lambda _e: self._desenhar())
        self.bind("<Enter>", lambda _e: self._estado(sobre=True))
        self.bind("<Leave>", lambda _e: self._estado(sobre=False, baixo=False))
        self.bind("<ButtonPress-1>", lambda _e: self._estado(baixo=True))
        self.bind("<ButtonRelease-1>", self._soltar)

    def _estado(self, sobre=None, baixo=None) -> None:
        if sobre is not None:
            self._sobre = sobre
        if baixo is not None:
            self._baixo = baixo
        self._desenhar()

    def _soltar(self, e) -> None:
        estava = self._baixo
        self._estado(baixo=False)
        if estava and 0 <= e.x <= self.winfo_width() and 0 <= e.y <= self.winfo_height() and self.comando:
            self.comando()

    def ajustar(self, texto=None, dica=None, cor=None, destaque=None) -> None:
        if texto is not None:
            self.texto = texto
        if dica is not None:
            self.dica = dica
        if cor is not None:
            self.cor = cor
        if destaque is not None:
            self.destaque = destaque
        self._desenhar()

    def _desenhar(self) -> None:
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        if w < 20 or h < 20:
            return
        fundo = SUP3 if self._baixo else (SUP2 if self._sobre else SUP)
        borda = self.cor if self.destaque else BORDA
        retangulo_redondo(self, 1, 1, w - 1, h - 1, px(12), fill=fundo, outline=borda, width=max(1, px(1)))
        t = px(34)
        x0, y0 = px(12), (h - t) / 2
        retangulo_redondo(self, x0, y0, x0 + t, y0 + t, px(9), fill=misturar(fundo, self.cor, 0.22), outline="")
        desenhar_icone(self, self.icone, x0 + t / 2, y0 + t / 2, t * 0.52, self.cor)
        x = x0 + t + px(12)
        if self.dica:
            self.create_text(x, h / 2 - px(8), text=self.texto, anchor="w", fill=TEXTO, font=F(10, "bold"))
            self.create_text(x, h / 2 + px(9), text=self.dica, anchor="w", fill=TEXTO3, font=F(8))
        else:
            self.create_text(x, h / 2, text=self.texto, anchor="w", fill=TEXTO, font=F(10, "bold"))


class Mosaico(tk.Canvas):
    """Número da sessão: ícone colorido, legenda pequena em maiúsculas e o valor."""

    def __init__(self, pai, icone: str, cor: str, legenda: str, valor: str = "0", altura: int = 60, fundo: str = SUP):
        super().__init__(pai, height=px(altura), width=px(10), bg=fundo, highlightthickness=0, bd=0)
        self.icone, self.cor, self.legenda, self.valor, self.fundo = icone, cor, legenda, valor, fundo
        self._id_valor = None
        self.bind("<Configure>", lambda _e: self._desenhar())

    @staticmethod
    def _fonte_valor(valor: str) -> tuple:
        return FN(14) if len(valor) <= 9 else FN(11)  # textos longos (ex.: "Sem calibração") ficam menores e cabem

    def definir(self, valor: str) -> None:
        if valor != self.valor:
            self.valor = valor
            if self._id_valor is not None:
                self.itemconfigure(self._id_valor, text=valor, font=self._fonte_valor(valor))

    def definir_legenda(self, legenda: str) -> None:
        self.legenda = legenda
        self._desenhar()

    def _desenhar(self) -> None:
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        if w < 20 or h < 20:
            return
        retangulo_redondo(self, 0, 0, w, h, px(11), fill=SUP2, outline="")
        t = px(34)
        x0, y0 = px(11), (h - t) / 2
        retangulo_redondo(self, x0, y0, x0 + t, y0 + t, px(9), fill=misturar(SUP2, self.cor, 0.22), outline="")
        desenhar_icone(self, self.icone, x0 + t / 2, y0 + t / 2, t * 0.52, self.cor)
        x = x0 + t + px(11)
        self.create_text(x, h * 0.31, text=self.legenda.upper(), anchor="w", fill=TEXTO3, font=F(8, "bold"))
        self._id_valor = self.create_text(x, h * 0.67, text=self.valor, anchor="w", fill=TEXTO,
                                          font=self._fonte_valor(self.valor))


class Hero(tk.Canvas):
    """Faixa de destaque com degradê e a etapa atual (título, descrição). O texto é desenhado no próprio canvas."""

    def __init__(self, pai, altura: int = 142, recuo: int = 160):
        super().__init__(pai, height=px(altura), width=px(10), bg=BG, highlightthickness=0, bd=0)
        self.c1, self.c2 = GRADIENTE_HERO
        self.alt = px(altura)
        x = px(recuo)
        self._tit = self.create_text(x, px(36), text="", anchor="w", fill=TEXTO, font=FN(21), tags="txt")
        self._desc = self.create_text(x, px(58), text="", anchor="nw", fill=TEXTO2, font=F(9), width=px(380), tags="txt")
        self.bind("<Configure>", lambda _e: self._fundo())

    def cor_em(self, x_rel: float) -> str:
        return misturar(self.c1, self.c2, max(0.0, min(1.0, x_rel)))

    def _fundo(self) -> None:
        self.delete("bg")
        w, h = self.winfo_width(), self.winfo_height()
        if w < 20 or h < 20:
            return
        passo = max(2, px(4))
        for x in range(0, w, passo):
            self.create_rectangle(x, 0, x + passo, h, fill=self.cor_em(x / w), outline="", tags="bg")
        r = px(14)  # cantos arredondados: pinta de BG o que sobra fora do arco
        for (cx, cy, sx, sy) in ((0, 0, 1, 1), (w, 0, -1, 1), (0, h, 1, -1), (w, h, -1, -1)):
            pts = [cx, cy]
            for k in range(0, 91, 10):
                a = math.radians(k)
                pts += [cx + sx * r * (1 - math.sin(a)), cy + sy * r * (1 - math.cos(a))]
            self.create_polygon(pts, fill=BG, outline="", tags="bg")
        p = px(126)  # placa escura atrás do anel de progresso
        retangulo_redondo(self, px(14), px(8), px(14) + p, px(8) + p, px(16), fill=PLACA_HERO, outline="#3a2a18",
                          width=max(1, px(1)), tags="bg")
        self.tag_lower("bg")

    def definir(self, titulo=None, cor=None, descricao=None) -> None:
        if titulo is not None:
            self.itemconfigure(self._tit, text=titulo)
        if cor is not None:
            self.itemconfigure(self._tit, fill=cor)
        if descricao is not None:
            self.itemconfigure(self._desc, text=descricao)


# ====================================================================== ajuda e guia de primeiros passos
class Dica:
    """Balão de ajuda: aparece ao passar o mouse sobre o widget (depois de uma pausa curta) e some ao sair.

    `texto_fn` é chamado na hora de mostrar, então o texto acompanha o idioma atual.
    """

    def __init__(self, widget: tk.Misc, texto_fn, largura: int = 280, atraso: int = 350):
        self.w, self.texto_fn, self.largura, self.atraso = widget, texto_fn, largura, atraso
        self._job = None
        self._top = None
        widget.bind("<Enter>", self._agendar, add="+")
        widget.bind("<Leave>", self._esconder, add="+")
        widget.bind("<ButtonPress>", self._esconder, add="+")
        widget.bind("<Destroy>", self._esconder, add="+")

    def _agendar(self, _e=None) -> None:
        self._esconder()
        try:
            self._job = self.w.after(self.atraso, self._mostrar)
        except tk.TclError:
            self._job = None

    def _mostrar(self) -> None:
        self._job = None
        try:
            texto = self.texto_fn()
            if not texto:
                return
            top = tk.Toplevel(self.w)
            top.withdraw()
            top.overrideredirect(True)
            top.attributes("-topmost", True)
            top.configure(bg=BORDA)
            corpo = tk.Frame(top, bg=SUP2)
            corpo.pack(padx=1, pady=1)
            tk.Label(corpo, text=texto, font=F(9), bg=SUP2, fg=TEXTO, justify="left", anchor="w",
                     wraplength=px(self.largura), padx=px(12), pady=px(9)).pack()
            top.update_idletasks()
            larg, alt = top.winfo_reqwidth(), top.winfo_reqheight()
            x = self.w.winfo_rootx() + px(8)
            y = self.w.winfo_rooty() + self.w.winfo_height() + px(6)
            x = max(4, min(x, self.w.winfo_screenwidth() - larg - 8))
            if y + alt > self.w.winfo_screenheight() - 8:  # sem espaço embaixo: abre acima
                y = max(4, self.w.winfo_rooty() - alt - px(6))
            top.geometry(f"+{x}+{y}")
            top.deiconify()
            self._top = top
        except tk.TclError:
            self._top = None

    def _esconder(self, _e=None) -> None:
        if self._job is not None:
            try:
                self.w.after_cancel(self._job)
            except tk.TclError:
                pass
            self._job = None
        if self._top is not None:
            try:
                self._top.destroy()
            except tk.TclError:
                pass
            self._top = None


class AjudaIcone(tk.Canvas):
    """Bolinha com "?" ao lado de um ajuste. Passe o mouse para ver a explicação."""

    def __init__(self, pai, texto_fn, fundo: str = SUP, tam: int = 16):
        t = px(tam)
        super().__init__(pai, width=t, height=t, bg=fundo, highlightthickness=0, bd=0, cursor="question_arrow")
        self.t = t
        self._desenhar(False)
        self.bind("<Enter>", lambda _e: self._desenhar(True), add="+")
        self.bind("<Leave>", lambda _e: self._desenhar(False), add="+")
        Dica(self, texto_fn)

    def _desenhar(self, sobre: bool) -> None:
        self.delete("all")
        cor = GEMA if sobre else TEXTO3
        m = max(1, px(1))
        self.create_oval(m, m, self.t - m, self.t - m, outline=cor, width=max(1, px(1)))
        self.create_text(self.t / 2, self.t / 2, text="?", fill=cor, font=F(8, "bold"))


class Marcador(tk.Canvas):
    """Bolinha de um passo do guia: vazia com o número (a fazer), com borda laranja (é o próximo) ou verde com visto (feito)."""

    def __init__(self, pai, tam: int, numero: int, fundo: str = SUP):
        t = px(tam)
        super().__init__(pai, width=t, height=t, bg=fundo, highlightthickness=0, bd=0)
        self.t, self.numero, self.fundo = t, numero, fundo
        self.feito, self.destaque = False, False
        self._desenhar()

    def definir(self, feito: bool, destaque: bool = False) -> None:
        if (feito, destaque) != (self.feito, self.destaque):
            self.feito, self.destaque = feito, destaque
            self._desenhar()

    def _desenhar(self) -> None:
        self.delete("all")
        t, m = self.t, px(2)
        if self.feito:
            self.create_oval(m, m, t - m, t - m, fill=BROTO, outline=BROTO)
            desenhar_icone(self, "check", t / 2, t / 2, t * 0.6, "#ffffff")
        else:
            cor = GEMA if self.destaque else TEXTO3
            self.create_oval(m, m, t - m, t - m, fill=SUP2 if self.destaque else self.fundo, outline=cor,
                             width=max(1, px(2)))
            self.create_text(t / 2, t / 2, text=str(self.numero), fill=cor, font=FN(10))


class CampoIntervalo:
    """Intervalo em quatro caixas (horas, minutos, segundos e milissegundos), como nos autoclickers clássicos.

    Guarda o total em milissegundos. Digitar 90 em segundos vira 1 min 30 s. Mesma interface do Campo
    (get, definir, _digitar, chave), então o resto do programa trata os dois igual.
    """
    UNIDADES = (("h", 3_600_000, 99), ("min", 60_000, 59), ("s", 1_000, 59), ("ms", 1, 999))
    MINIMO, MAXIMO = 1, 99 * 3_600_000 + 59 * 60_000 + 59_000 + 999

    def __init__(self, pai, linha, chave, rotulo, valor_ms, ao_mudar, fundo=SUP, ajuda=None, padrao=None):
        self.chave, self.ao_mudar, self._ajuda, self._padrao = chave, ao_mudar, ajuda, padrao
        self.total = self._limitar(valor_ms)
        topo = tk.Frame(pai, bg=fundo)
        topo.grid(row=2 * linha, column=0, sticky="w", pady=(px(6), 0))
        tk.Label(topo, text=rotulo, bg=fundo, fg=TEXTO, font=F(9), anchor="w").pack(side="left")
        if ajuda:
            AjudaIcone(topo, self._texto_ajuda, fundo).pack(side="left", padx=(px(6), 0))
        linha_f = tk.Frame(pai, bg=fundo)
        linha_f.grid(row=2 * linha + 1, column=0, sticky="w", pady=(px(4), 0))
        self.vars, self.entradas = [], []
        for i, (nome, _f, _m) in enumerate(self.UNIDADES):
            v = tk.StringVar()
            e = tk.Entry(linha_f, textvariable=v, width=4, justify="center", bg=SUP2, fg=TEXTO,
                         insertbackground=TEXTO, relief="flat", highlightthickness=1, highlightbackground=BORDA,
                         highlightcolor=TURQUESA, font=F(10))
            e.pack(side="left", ipady=px(3))
            tk.Label(linha_f, text=nome, bg=fundo, fg=TEXTO3, font=F(9)).pack(
                side="left", padx=(px(4), px(12) if i < 3 else 0))
            e.bind("<Return>", self._digitar)
            e.bind("<FocusOut>", self._digitar)
            e.bind("<FocusIn>", lambda ev: ev.widget.after(10, lambda w=ev.widget: w.select_range(0, "end")))
            self.vars.append(v)
            self.entradas.append(e)
        self._mostrar()

    @classmethod
    def _limitar(cls, ms) -> int:
        try:
            ms = int(round(float(ms)))
        except (TypeError, ValueError):
            ms = 100
        return max(cls.MINIMO, min(cls.MAXIMO, ms))

    def _texto_ajuda(self) -> str:
        texto = T(self._ajuda) if self._ajuda else ""
        if self._padrao is not None:
            texto += "\n" + T("Padrão: {v} {u}", v=str(int(self._padrao)), u="ms")
        return texto

    def _mostrar(self) -> None:
        resto = self.total
        for (nome, fator, _m), v in zip(self.UNIDADES, self.vars):
            v.set(str(resto // fator))
            resto %= fator

    def _digitar(self, _evento=None) -> None:
        total = 0
        for (nome, fator, _m), v in zip(self.UNIDADES, self.vars):
            try:
                n = max(0, int(float(v.get().replace(",", ".") or 0)))
            except ValueError:
                n = 0
            total += n * fator
        self.total = self._limitar(total)
        self._mostrar()
        self.ao_mudar(self.chave, self.total)

    def get(self) -> int:
        return self.total

    def definir(self, valor_ms) -> None:
        self.total = self._limitar(valor_ms)
        self._mostrar()


def texto_duracao(ms: float) -> str:
    """1500 -> '1,5 s'; 90000 -> '1 min 30 s'; 3 600 000 -> '1 h'. Usado na taxa de cliques do AutoClick."""
    s = ms / 1000
    if s < 60:
        return f"{s:.1f} s".replace(".0 ", " ")
    partes, h, resto = [], int(s // 3600), s % 3600
    m, seg = int(resto // 60), round(resto % 60)
    for n, u in ((h, "h"), (m, "min"), (seg, "s")):
        if n:
            partes.append(f"{n} {u}")
    return " ".join(partes) or "0 s"


class DialogoFechar(tk.Toplevel):
    """Janela de confirmação ao fechar o programa: Cancelar, Fechar ou só minimizar para a bandeja.

    Sem barra de título (como um cartão sobre a janela principal). Esc e o × cancelam.
    """

    def __init__(self, janela, titulo: str, texto: str, rot_cancelar: str, rot_fechar: str, rot_bandeja: str,
                 ao_fechar, ao_bandeja):
        super().__init__(janela)
        self.withdraw()
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.configure(bg=BORDA)
        self._ao_fechar, self._ao_bandeja = ao_fechar, ao_bandeja
        corpo = tk.Frame(self, bg=SUP)
        corpo.pack(padx=1, pady=1)
        miolo = tk.Frame(corpo, bg=SUP)
        miolo.pack(padx=px(26), pady=px(22))
        topo = tk.Frame(miolo, bg=SUP)
        topo.pack(fill="x")
        IconeTile(topo, "ajuda", GEMA, tam=44, fundo=SUP).pack(side="left")
        x = tk.Label(topo, text="×", font=F(11), bg=SUP, fg=TEXTO3, cursor="hand2")
        x.pack(side="right", anchor="n")
        x.bind("<Button-1>", lambda _e: self.cancelar())
        x.bind("<Enter>", lambda _e: x.configure(fg=TEXTO))
        x.bind("<Leave>", lambda _e: x.configure(fg=TEXTO3))
        tk.Label(miolo, text=titulo, font=FN(14), bg=SUP, fg=TEXTO, anchor="w", justify="left",
                 wraplength=px(390)).pack(fill="x", pady=(px(16), px(8)))
        tk.Label(miolo, text=texto, font=F(9), bg=SUP, fg=TEXTO2, anchor="w", justify="left",
                 wraplength=px(390)).pack(fill="x")
        linha = tk.Frame(miolo, bg=SUP)
        linha.pack(fill="x", pady=(px(20), px(14)))
        linha.grid_columnconfigure(0, weight=1, uniform="bt")
        linha.grid_columnconfigure(1, weight=1, uniform="bt")
        self.btn_cancelar = Botao(linha, rot_cancelar, self.cancelar, altura=40, raio=10, fundo=SUP,
                                  fonte=F(10, "bold"))
        self.btn_cancelar.grid(row=0, column=0, sticky="ew", padx=(0, px(6)))
        Botao(linha, rot_fechar, self._fechar_tudo, bg=GEMA, fg=TEXTO_BTN, hover=misturar(GEMA, "#ffffff", 0.14),
              altura=40, raio=10, fundo=SUP, fonte=F(10, "bold")).grid(row=0, column=1, sticky="ew", padx=(px(6), 0))
        link = tk.Label(miolo, text=rot_bandeja, font=tkfont.Font(family=F(9)[0], size=F(9)[1], underline=True),
                        bg=SUP, fg=GEMA, cursor="hand2")
        link.pack()
        link.bind("<Button-1>", lambda _e: self._ir_bandeja())
        self.bind("<Escape>", lambda _e: self.cancelar())
        self.bind("<Return>", lambda _e: self.cancelar())

        self.update_idletasks()
        w, h = self.winfo_reqwidth(), self.winfo_reqheight()
        px0 = janela.winfo_rootx() + (janela.winfo_width() - w) // 2
        py0 = janela.winfo_rooty() + (janela.winfo_height() - h) // 2
        self.geometry(f"+{max(0, px0)}+{max(0, py0)}")
        self.deiconify()
        self.grab_set()
        self.focus_force()

    def _sair(self) -> None:
        try:
            self.grab_release()
        except tk.TclError:
            pass
        self.destroy()

    def cancelar(self) -> None:
        self._sair()

    def _fechar_tudo(self) -> None:
        self._sair()
        self._ao_fechar()

    def _ir_bandeja(self) -> None:
        self._sair()
        self._ao_bandeja()
