"""Modo mini: janelinha sempre por cima com o estado, os números e os botões principais."""
import time
import tkinter as tk

from .idioma import T
from .tema import TEXTO_BTN, TURQUESA, BROTO, BORDA, GEMA, F, misturar, px, SUP, TEXTO, TEXTO2, TEXTO3
from .widgets import Botao, texto_duracao


def _hms(seg: float) -> str:
    s = int(seg)
    return f"{s // 3600:02d}:{s % 3600 // 60:02d}:{s % 60:02d}"


class JanelaMini:
    """Mostra o que importa sem cobrir o jogo. Arraste pelo texto; o botão Abrir volta à janela completa."""

    def __init__(self, app):
        self.app = app
        self.top = tk.Toplevel(app.root)
        self.top.withdraw()
        self.top.overrideredirect(True)
        self.top.attributes("-topmost", True)
        self.top.configure(bg=BORDA)
        self.visivel = False
        self._cache: dict = {}
        self._desloc = (0, 0)
        self._pct = None
        self._montar()

    def _montar(self) -> None:
        corpo = tk.Frame(self.top, bg=SUP)
        corpo.pack(padx=1, pady=1)  # 1 px de borda
        tk.Frame(corpo, width=px(256), height=1, bg=SUP).pack()  # largura mínima
        topo = tk.Frame(corpo, bg=SUP)
        topo.pack(fill="x", padx=px(10), pady=(px(5), 0))
        self.pt = tk.Canvas(topo, width=px(10), height=px(10), bg=SUP, highlightthickness=0, bd=0)
        self.pt.pack(side="left", padx=(0, px(6)))
        self._pt_id = self.pt.create_oval(1, 1, px(10) - 1, px(10) - 1, fill=TEXTO3, outline="")
        self.lbl_estado = tk.Label(topo, text="", font=F(10, "bold"), bg=SUP, fg=TEXTO, anchor="w")
        self.lbl_estado.pack(side="left")
        Botao(topo, T("Abrir"), self.app.sair_mini, altura=22, largura=62, raio=6, fonte=F(8, "bold"), icone="expandir").pack(side="right")
        self.lbl_fase = tk.Label(corpo, text="", font=F(8, "bold"), bg=SUP, fg=TEXTO2, anchor="w")
        self.lbl_fase.pack(fill="x", padx=px(10), pady=(px(1), 0))
        self.barra = tk.Canvas(corpo, width=1, height=px(4), bg=SUP, highlightthickness=0, bd=0)
        self.barra.pack(fill="x", padx=px(10), pady=(px(2), px(4)))
        self._barra_fundo = self.barra.create_rectangle(0, 0, 0, 0, fill=BORDA, outline="")
        self._barra_cheio = self.barra.create_rectangle(0, 0, 0, 0, fill=BROTO, outline="")
        self.barra.bind("<Configure>", lambda _e: self._desenhar_barra(self._pct))
        grade = self.grade = tk.Frame(corpo, bg=SUP)
        grade.pack(fill="x", padx=px(10))
        self.celulas = []
        for i in range(3):
            grade.grid_columnconfigure(i, weight=1, uniform="mini")
            col = tk.Frame(grade, bg=SUP)
            col.grid(row=0, column=i, sticky="w")
            tit = tk.Label(col, text="", font=F(7, "bold"), bg=SUP, fg=TEXTO3, anchor="w")
            tit.pack(anchor="w")
            val = tk.Label(col, text="", font=F(11, "bold"), bg=SUP, fg=TEXTO, anchor="w")
            val.pack(anchor="w")
            self.celulas.append((tit, val))
        self.lbl_info = tk.Label(corpo, text="", font=F(8), bg=SUP, fg=TEXTO2, anchor="w", justify="left", wraplength=px(212))
        self.lbl_info.pack(fill="x", padx=px(10), pady=(px(3), 0))
        chips = self.chips = tk.Frame(corpo, bg=SUP)
        chips.pack(fill="x", padx=px(10), pady=(px(1), px(5)))
        self.lbl_roblox = tk.Label(chips, text="", font=F(7), bg=SUP, fg=TEXTO3, anchor="w")
        self.lbl_roblox.pack(side="left")
        self.lbl_botao = tk.Label(chips, text="", font=F(7), bg=SUP, fg=TEXTO3, anchor="w")
        self.lbl_botao.pack(side="left", padx=(px(8), 0))
        linha = tk.Frame(corpo, bg=SUP)
        linha.pack(fill="x", padx=px(10), pady=(0, px(7)))
        self.btn_pesca = Botao(linha, "", self.app.alternar, altura=26, raio=8)
        self.btn_pesca.pack(side="left", fill="x", expand=True, padx=(0, px(4)))
        self.btn_ac = Botao(linha, "", self.app.alternar_ac, altura=26, raio=8)
        self.btn_ac.pack(side="left", fill="x", expand=True, padx=(px(4), 0))
        for w in (corpo, topo, self.pt, self.lbl_estado, self.lbl_fase, self.barra, grade, self.lbl_info, chips,
              self.lbl_roblox, self.lbl_botao, *[x for par in self.celulas for x in par]):
            w.bind("<ButtonPress-1>", self._iniciar_arrasto)
            w.bind("<B1-Motion>", self._arrastar)
            w.bind("<ButtonRelease-1>", self._soltar)

    # ------------------------------------------------------------ arrastar
    def _iniciar_arrasto(self, e) -> None:
        self._desloc = (e.x_root - self.top.winfo_x(), e.y_root - self.top.winfo_y())

    def _arrastar(self, e) -> None:
        self.top.geometry(f"+{e.x_root - self._desloc[0]}+{e.y_root - self._desloc[1]}")

    def _soltar(self, _e) -> None:
        self.app.cfg["mini_pos"] = [self.top.winfo_x(), self.top.winfo_y()]
        self.app._salvar_depois()

    # ------------------------------------------------------------ mostrar e atualizar
    def mostrar(self) -> None:
        self.top.update_idletasks()
        try:
            x, y = (int(v) for v in self.app.cfg["mini_pos"])
            if not (-50 <= x <= self.top.winfo_screenwidth() - 60 and 0 <= y <= self.top.winfo_screenheight() - 40):
                raise ValueError
        except Exception:  # noqa: BLE001
            x, y = self.top.winfo_screenwidth() - self.top.winfo_reqwidth() - px(24), px(80)
        self.top.geometry(f"+{x}+{y}")
        self.top.deiconify()
        self.top.lift()
        self.top.attributes("-topmost", True)
        self.aplicar_opacidade()
        self.visivel = True
        self.traduzir()

    def aplicar_opacidade(self) -> None:
        try:
            self.top.attributes("-alpha", max(0.4, min(1.0, float(self.app.cfg["mini_opacidade"]) / 100)))
        except (tk.TclError, TypeError, ValueError):
            pass

    def esconder(self) -> None:
        self.top.withdraw()
        self.visivel = False

    def traduzir(self) -> None:
        """Força reescrever todos os textos (usado ao abrir e ao trocar de idioma)."""
        self._cache.clear()
        self.atualizar()

    def _botao(self, nome: str, btn: Botao, rotulo: str, rodando: bool) -> None:
        chave = (rotulo, rodando)
        if self._cache.get(nome) == chave:
            return
        self._cache[nome] = chave
        texto = T(rotulo)
        if rodando:
            btn.ajustar(texto=texto, icone="stop", bg=SUP, fg=GEMA, hover=misturar(SUP, GEMA, 0.16), contorno=GEMA)
        else:
            btn.ajustar(texto=texto, icone="play", bg=GEMA, fg=TEXTO_BTN, hover=misturar(GEMA, "#ffffff", 0.14), contorno=None)

    def _desenhar_barra(self, pct) -> None:
        """pct entre 0 e 1 desenha o progresso; None deixa a barra vazia."""
        self._pct = pct
        larg = max(1, self.barra.winfo_width())
        alt = max(1, self.barra.winfo_height())
        self.barra.coords(self._barra_fundo, 0, 0, larg, alt)
        self.barra.coords(self._barra_cheio, 0, 0, larg * (pct or 0), alt)

    def _celulas(self, dados) -> None:
        dados = list(dados) + [("", "")] * (len(self.celulas) - len(dados))
        for (tit, val), (titulo, valor) in zip(self.celulas, dados):
            t = T(titulo).upper() if titulo else ""
            if tit.cget("text") != t:
                tit.configure(text=t)
            if val.cget("text") != valor:
                val.configure(text=valor)

    def atualizar(self) -> None:
        a = self.app
        pesca, ac = a.pesca_ativa(), a._ac_ativo()
        agora = time.perf_counter()
        fase, pct = "", None
        if pesca:
            estado, cor = "Rodando", BROTO
            fase = T(a.fase_nome)
            if a.fase_dur > 0:
                resta = max(0.0, a.fase_dur - (agora - a.fase_ini))
                fase += f"  ·  {resta:.1f} s"
                pct = min(1.0, (agora - a.fase_ini) / a.fase_dur)
            tempo = time.time() - a.inicio_execucao if a.inicio_execucao else 0
            dados = [("Ciclos", str(a.ciclos)), ("Tempo", _hms(tempo))]
            info = ""
        elif ac:
            estado, cor = "AutoClick", TURQUESA
            limite = int(a.cfg.get("ac_limite") or 0)
            if a.ac_atraso_fim > agora:
                fase = T("Começa em {s:.1f} s", s=a.ac_atraso_fim - agora)
                dec = 0.0
            else:
                dec = max(0.001, agora - a.ac_t0) if a.ac_t0 else 0.0
                fase = T("Clicando")
                if limite:
                    pct = min(1.0, a.ac_cliques / limite)
            dados = [("Cliques", f"{a.ac_cliques}" + (f"/{limite}" if limite else "")), ("Tempo", _hms(dec))]
            ms = a.cfg.get("ac_intervalo", 0)
            partes = [T("A cada {t}", t=(f"{float(ms):.0f} ms" if float(ms) < 1000 else texto_duracao(float(ms))))] if ms else []
            partes.append(T({"esquerdo": "Esquerdo", "direito": "Direito", "meio": "Meio"}.get(a.cfg.get("ac_botao"), "Esquerdo")))
            if a.cfg.get("ac_pos_fixa"):
                partes.append(T("Posição fixa"))
            info = "  ·  ".join(partes)
        else:
            estado, cor = "Parado", TEXTO3
            fase = ""
            dados = [("Ciclos", str(a.ciclos))]
            info = ""
        if self._cache.get("fase") != fase:
            self._cache["fase"] = fase
            self.lbl_fase.configure(text=fase)
            if fase:  # parado: sem linha de etapa nem barra
                self.lbl_fase.pack(fill="x", padx=px(10), pady=(px(1), 0), before=self.grade)
                self.barra.pack(fill="x", padx=px(10), pady=(px(2), px(4)), before=self.grade)
            else:
                self.lbl_fase.pack_forget()
                self.barra.pack_forget()
                self.grade.pack_configure(pady=(px(6), 0))
            if fase:
                self.grade.pack_configure(pady=0)
        pct_r = None if pct is None else round(pct, 3)
        if self._cache.get("pct") != pct_r:
            self._cache["pct"] = pct_r
            self._desenhar_barra(pct_r)
            self.barra.itemconfigure(self._barra_cheio, fill=cor)
        self._celulas(dados)
        # Roblox e botão PARAR
        rb = a._roblox_aberto
        txt_rb, cor_rb = (("Roblox: " + T("Aberto")), BROTO) if rb else (("Roblox: " + T("Fechado")), TEXTO3)
        lamp = getattr(a, "_lamp", None)
        if ac:
            txt_bt, cor_bt = "", TEXTO3
        elif lamp is None:
            txt_bt, cor_bt = T("Botão PARAR: sem calibração"), TEXTO3
        elif lamp:
            txt_bt, cor_bt = T("Botão PARAR: visível agora"), BROTO
        else:
            txt_bt, cor_bt = T("Botão PARAR: não visível"), TEXTO2
        if self._cache.get("chips") != (txt_rb, cor_rb, txt_bt, cor_bt):
            self._cache["chips"] = (txt_rb, cor_rb, txt_bt, cor_bt)
            self.lbl_roblox.configure(text="•  " + txt_rb, fg=cor_rb)
            self.lbl_botao.configure(text=("•  " + txt_bt) if txt_bt else "", fg=cor_bt)
        texto = T(estado)
        if self._cache.get("estado") != (texto, cor):
            self._cache["estado"] = (texto, cor)
            self.lbl_estado.configure(text=texto)
            self.pt.itemconfigure(self._pt_id, fill=cor)
        if self._cache.get("info") != info:
            self._cache["info"] = info
            self.lbl_info.configure(text=info)
            if info:
                self.lbl_info.pack(fill="x", padx=px(10), pady=(px(3), 0), before=self.chips)
            else:
                self.lbl_info.pack_forget()
        self._botao("pesca", self.btn_pesca, "Parar (F1)" if pesca else "Pesca (F1)", pesca)
        self._botao("ac", self.btn_ac, "Parar (F2)" if ac else "AutoClick (F2)", ac)
