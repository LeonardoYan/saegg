"""Threads que executam o macro de pesca (Pescador) e o AutoClick (AutoClicker)."""
import collections
import math
import queue
import threading
import time

from .deteccao import LIMITE_CLIQUES, minigame_visivel, ponto_calibrado, ponto_clique
from .winapi import (
    BOTOES_MOUSE,
    clicar,
    mouse_down,
    mouse_up,
    mover_cursor,
    posicao_cursor,
    rect_janela_roblox,
    roblox_em_primeiro_plano,
)


class Pescador(threading.Thread):
    """Executa o ciclo de pesca. Lê os ajustes de `cfg` a cada ciclo (mudanças valem no ciclo seguinte)."""

    def __init__(self, cfg: dict, fila: queue.Queue):
        super().__init__(daemon=True)
        self.cfg = cfg
        self.fila = fila
        self.parar = threading.Event()
        self._visivel_antes = None

    def log(self, msg: str, nivel: str = "info", **kw) -> None:
        self.fila.put(("log", (nivel, msg, kw)))

    def fase(self, nome: str, duracao: float, texto: str = "") -> None:
        self.fila.put(("fase", (nome, duracao, texto)))

    def esperar(self, segundos: float) -> bool:
        """Dorme em fatias. Retorna False se mandaram parar."""
        fim = time.perf_counter() + segundos
        while time.perf_counter() < fim:
            if self.parar.is_set():
                return False
            time.sleep(min(0.02, max(0.0, fim - time.perf_counter())))
        return not self.parar.is_set()

    def visivel(self, cal: dict, tol: int) -> bool:
        v = minigame_visivel(cal, tol)
        if v != self._visivel_antes:
            self._visivel_antes = v
            self.fila.put(("visivel", v))
        return v

    def run(self) -> None:
        c = self.cfg
        aviso = ""
        sem_roblox_desde = None    # desde quando a janela do Roblox não é encontrada
        avisou_sem_roblox = False

        def avisar(texto: str) -> None:
            nonlocal aviso
            if aviso != texto:
                aviso = texto
                self.log(texto, "aviso")

        try:
            while not self.parar.is_set():
                rect = rect_janela_roblox()
                if rect is None:
                    if sem_roblox_desde is None:
                        sem_roblox_desde = time.time()
                    elif not avisou_sem_roblox and time.time() - sem_roblox_desde > 60:
                        avisou_sem_roblox = True  # avisa uma vez só; o macro segue esperando o jogo voltar
                        self.log("A janela do Roblox sumiu há mais de 1 minuto. O jogo fechou?", "erro")
                    self.fase("Aguardando o Roblox", 0)
                    avisar("Janela do Roblox não encontrada. Aguardando...")
                    self.esperar(1.0)
                    continue
                sem_roblox_desde, avisou_sem_roblox = None, False
                if c["so_roblox"] and not roblox_em_primeiro_plano():
                    self.fase("Aguardando o Roblox", 0)
                    avisar("Aguardando o Roblox ficar em primeiro plano...")
                    self.esperar(0.5)
                    continue
                aviso = ""

                cal = c.get("cal") if c["detectar"] else None
                tol = int(c["tolerancia"])
                alvo = ponto_calibrado(cal, rect) if cal else None
                x, y = ponto_clique(rect, alvo)

                # 1) lançar a vara
                hold = c["hold_carga"] / 1000
                self.fase("Lançando a vara", hold)
                mover_cursor(x, y)
                mouse_down()
                try:
                    ok = self.esperar(hold)
                finally:
                    mouse_up()
                if not ok:
                    break

                # 2) esperar o minigame aparecer
                if cal:
                    limite = float(c["limite_espera"])
                    self.fase("Aguardando o minigame", limite, "tempo máximo restante:")
                    t_ini = time.perf_counter()
                    vistos = 0
                    achou = False
                    while not self.parar.is_set() and time.perf_counter() - t_ini < limite:
                        if self.visivel(cal, tol):
                            vistos += 1
                            if vistos >= 2:  # confirma em 2 leituras seguidas
                                achou = True
                                break
                        else:
                            vistos = 0
                        time.sleep(0.03)
                    if self.parar.is_set():
                        break
                    if not achou:
                        self.log(
                            "O minigame não apareceu em {limite:.0f}s. A vara pode não ter sido lançada "
                            "(aviso do prêmio ainda na tela?). Se repetir, aumente a pausa entre ciclos.",
                            "aviso", limite=limite,
                        )
                        self.fase("Pausa", c["pausa"])
                        if not self.esperar(c["pausa"]):
                            break
                        continue
                    self.log("Minigame detectado após {t:.1f}s", "ok", t=time.perf_counter() - t_ini)
                else:
                    self.fase("Aguardando o minigame", c["espera_minigame"])
                    if not self.esperar(c["espera_minigame"]):
                        break

                # 3) clicar rápido
                delay = c["delay_clique"] / 1000
                if cal:
                    self.fase("Clicando", 0, "Clicando até o botão PARAR sumir")
                    duracao = LIMITE_CLIQUES
                else:
                    duracao = c["duracao_cliques"]
                    self.fase("Clicando", duracao)
                cliques = 0
                t0 = time.perf_counter()
                fim = t0 + duracao
                visto = {"t": t0}
                encerrar_vigia = threading.Event()

                erros_vigia = [0]

                def vigiar() -> None:
                    """Confere o botão PARAR em outra thread, para a leitura da tela não atrasar os cliques."""
                    while not encerrar_vigia.is_set() and not self.parar.is_set():
                        try:
                            if self.visivel(cal, tol):
                                visto["t"] = time.perf_counter()
                        except Exception as e:  # noqa: BLE001
                            erros_vigia[0] += 1
                            if erros_vigia[0] == 1:  # avisa só na primeira falha de cada minigame
                                self.log("Falha ao ler a tela durante os cliques: {e}", "aviso", e=e)
                        encerrar_vigia.wait(0.1)

                if cal:
                    threading.Thread(target=vigiar, daemon=True).start()
                proxima_checagem = t0
                interrompido = False
                try:
                    while not self.parar.is_set() and time.perf_counter() < fim:
                        agora = time.perf_counter()
                        if agora >= proxima_checagem:
                            proxima_checagem = agora + 0.25
                            if c["so_roblox"] and not roblox_em_primeiro_plano():
                                self.log("O Roblox saiu do primeiro plano. Cliques interrompidos.", "aviso")
                                interrompido = True
                                break
                            mover_cursor(x, y)  # mantém o mouse no ponto de cliques
                            self.fila.put(("cliques", cliques))
                        if cal and agora - visto["t"] >= 0.6:  # botão sumiu por 0,6 s seguidos = acabou
                            break
                        clicar()
                        cliques += 1
                        time.sleep(delay)
                finally:
                    encerrar_vigia.set()
                dur = max(0.001, time.perf_counter() - t0)
                if self.parar.is_set():
                    break
                self.fila.put(("ciclo", (cliques, dur, interrompido)))

                # 4) pausa para o aviso do prêmio sumir
                self.fase("Pausa", c["pausa"])
                if not self.esperar(c["pausa"]):
                    break
        except Exception as e:  # noqa: BLE001
            self.log("Erro: {e}", "erro", e=e)
        finally:
            mouse_up()
            self.fila.put(("fim", None))


class AutoClicker(threading.Thread):
    """Clica sem parar na posição atual do mouse. Lê os ajustes de `cfg` a cada clique (mudanças valem na hora)."""

    def __init__(self, cfg: dict, fila: queue.Queue):
        super().__init__(daemon=True)
        self.cfg = cfg
        self.fila = fila
        self.parar = threading.Event()

    def log(self, msg: str, nivel: str = "info", **kw) -> None:
        self.fila.put(("log", (nivel, msg, kw)))

    def _mouse_foi_movido(self, ref, fixa: bool, desvios) -> bool:
        """True se o usuário afastou o mouse mais que `ac_dist_mouse` pixels.

        Sem posição fixa, vale a distância até o ponto onde o mouse estava ao começar. Com posição fixa o cursor
        é devolvido ao ponto a cada clique, então um afastamento lento nunca passaria da distância de uma vez:
        somam-se os desvios do último segundo."""
        try:
            limite = max(1.0, float(self.cfg["ac_dist_mouse"]))
        except (TypeError, ValueError):
            limite = 150.0
        x, y = posicao_cursor()
        d = math.hypot(x - ref[0], y - ref[1])
        if not fixa:
            return d > limite
        agora = time.perf_counter()
        if d > 0:
            desvios.append((agora, d))
        while desvios and agora - desvios[0][0] > 1.0:
            desvios.popleft()
        return sum(v for _t, v in desvios) > limite

    def run(self) -> None:
        c = self.cfg
        cliques = 0
        t0 = time.perf_counter()
        try:
            atraso = float(c["ac_atraso"])
            if atraso > 0:
                self.fila.put(("ac_atraso", atraso))
                if self.parar.wait(atraso):
                    return
            botao = c["ac_botao"] if c["ac_botao"] in BOTOES_MOUSE else "esquerdo"
            alvo = None  # posição fixa: o cursor volta a este ponto antes de cada clique
            if c.get("ac_pos_fixa") and c.get("ac_pos"):
                alvo = (int(c["ac_pos"][0]), int(c["ac_pos"][1]))
            ref = alvo or posicao_cursor()  # ponto de referência para saber se o mouse foi movido
            desvios = collections.deque()   # (instante, quanto o mouse saiu do ponto), só do último segundo
            if alvo:
                mover_cursor(*alvo)         # vai ao ponto antes do primeiro clique
            self.fila.put(("ac_inicio", None))
            t0 = time.perf_counter()
            proximo = t0
            ultimo_aviso_ui = t0
            esperando_roblox = False
            while not self.parar.is_set():
                limite = int(c["ac_limite"])
                if limite and cliques >= limite:
                    self.log("Limite de {limite} cliques atingido. AutoClick parado.", "ok", limite=limite)
                    break
                if c["ac_so_roblox"] and not roblox_em_primeiro_plano():
                    if not esperando_roblox:
                        esperando_roblox = True
                        self.log("Roblox fora de primeiro plano. AutoClick em pausa.", "aviso")
                    self.parar.wait(0.2)
                    proximo = time.perf_counter()
                    continue
                if esperando_roblox:
                    esperando_roblox = False
                    self.log("Roblox em primeiro plano. AutoClick retomado.", "ok")
                    if alvo:
                        mover_cursor(*alvo)
                    ref = alvo or posicao_cursor()  # o mouse pode ter passeado durante a pausa
                    desvios.clear()
                if c.get("ac_parar_mouse") and self._mouse_foi_movido(ref, bool(alvo), desvios):
                    self.log("AutoClick parado: o mouse foi movido para longe.", "aviso")
                    break
                if alvo:
                    mover_cursor(*alvo)
                clicar(botao)
                cliques += 1
                agora = time.perf_counter()
                if agora - ultimo_aviso_ui >= 0.1:
                    ultimo_aviso_ui = agora
                    self.fila.put(("ac_cliques", cliques))
                proximo += max(0.001, float(c["ac_intervalo"]) / 1000)
                if proximo < agora:  # atrasou: não acumula "dívida" de cliques
                    proximo = agora
                if proximo > agora and self.parar.wait(proximo - agora):
                    break
        except Exception as e:  # noqa: BLE001
            self.log("Erro no AutoClick: {e}", "erro", e=e)
        finally:
            self.fila.put(("ac_fim", (cliques, max(0.001, time.perf_counter() - t0))))
