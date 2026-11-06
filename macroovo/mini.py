"""Modo mini: janelinha sempre por cima com o estado, os números e os botões principais."""
import time
import tkinter as tk

from .idioma import T
from .tema import TEXTO_BTN, TURQUESA, BROTO, BORDA, GEMA, F, misturar, px, SUP, TEXTO, TEXTO2, TEXTO3
from .widgets import Botao


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
        self._montar()

    def _montar(self) -> None:
        corpo = tk.Frame(self.top, bg=SUP)
        corpo.pack(padx=1, pady=1)  # 1 px de borda
        tk.Frame(corpo, width=px(250), height=1, bg=SUP).pack()  # largura mínima
        topo = tk.Frame(corpo, bg=SUP)
        topo.pack(fill="x", padx=px(10), pady=(px(8), 0))
        self.pt = tk.Canvas(topo, width=px(10), height=px(10), bg=SUP, highlightthickness=0, bd=0)
        self.pt.pack(side="left", padx=(0, px(6)))
        self._pt_id = self.pt.create_oval(1, 1, px(10) - 1, px(10) - 1, fill=TEXTO3, outline="")
        self.lbl_estado = tk.Label(topo, text="", font=F(10, "bold"), bg=SUP, fg=TEXTO, anchor="w")
        self.lbl_estado.pack(side="left")
        Botao(topo, T("Abrir"), self.app.sair_mini, altura=24, largura=70, raio=6, fonte=F(8, "bold"), icone="expandir").pack(side="right")
        self.lbl_info = tk.Label(corpo, text="", font=F(9), bg=SUP, fg=TEXTO2, anchor="w")
        self.lbl_info.pack(fill="x", padx=px(10), pady=(px(4), px(6)))
        linha = tk.Frame(corpo, bg=SUP)
        linha.pack(fill="x", padx=px(10), pady=(0, px(10)))
        self.btn_pesca = Botao(linha, "", self.app.alternar, altura=30, raio=8)
        self.btn_pesca.pack(side="left", fill="x", expand=True, padx=(0, px(4)))
        self.btn_ac = Botao(linha, "", self.app.alternar_ac, altura=30, raio=8)
        self.btn_ac.pack(side="left", fill="x", expand=True, padx=(px(4), 0))
        for w in (corpo, topo, self.pt, self.lbl_estado, self.lbl_info):
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

    def atualizar(self) -> None:
        a = self.app
        pesca, ac = a.pesca_ativa(), a._ac_ativo()
        if pesca:
            estado, cor = "Rodando", BROTO
            info = T("Ciclos {n}  ·  Cliques {c}  ·  {t}", n=a.ciclos, c=a.cliques_base + a.cliques_ciclo,
                     t=_hms(time.time() - a.inicio_execucao))
        elif ac:
            estado, cor = "AutoClick", TURQUESA
            agora = time.perf_counter()
            if a.ac_atraso_fim > agora:
                info = T("Começa em {s:.1f} s", s=a.ac_atraso_fim - agora)
            else:
                dec = max(0.001, agora - a.ac_t0) if a.ac_t0 else 0.001
                info = T("Cliques {c}  ·  {cps}/s  ·  {t}", c=a.ac_cliques, cps=f"{a.ac_cliques / dec:.0f}",
                         t=_hms(dec if a.ac_t0 else 0))
        else:
            estado, cor = "Parado", TEXTO3
            info = T("Pronto. F1 Pesca, F2 AutoClick.")
        texto = T(estado)
        if self._cache.get("estado") != (texto, cor):
            self._cache["estado"] = (texto, cor)
            self.lbl_estado.configure(text=texto)
            self.pt.itemconfigure(self._pt_id, fill=cor)
        if self._cache.get("info") != info:
            self._cache["info"] = info
            self.lbl_info.configure(text=info)
        self._botao("pesca", self.btn_pesca, "Parar (F1)" if pesca else "Pesca (F1)", pesca)
        self._botao("ac", self.btn_ac, "Parar (F2)" if ac else "AutoClick (F2)", ac)
