"""Idiomas da interface. Os textos do programa são escritos em português e T() traduz na hora de mostrar."""
import re
IDIOMAS = {"pt": "Português", "en": "English"}
_atual = "pt"


def definir(codigo) -> None:
    global _atual
    _atual = codigo if codigo in IDIOMAS else "pt"


def atual() -> str:
    return _atual


_NOMES_TECLAS: dict = {}   # nome padrão da tecla (F1, F2, F3, Esc) -> nome que o usuário escolheu
_RE_TECLAS = re.compile(r"\b(F1|F2|F3|Esc)\b")


def definir_teclas(mapa: dict) -> None:
    """Os textos do programa citam F1, F2, F3 e Esc; aqui eles passam a mostrar as teclas escolhidas."""
    _NOMES_TECLAS.clear()
    _NOMES_TECLAS.update({k: v for k, v in mapa.items() if k != v})


def T(texto: str, /, **kw) -> str:
    """Devolve o texto no idioma atual. Com argumentos nomeados, preenche os {campos} do texto."""
    if _atual != "pt":
        texto = EN.get(texto, texto)
    if _NOMES_TECLAS:
        texto = _RE_TECLAS.sub(lambda m: _NOMES_TECLAS.get(m.group(1), m.group(1)), texto)
    if not kw:
        return texto
    try:
        return texto.format(**kw)
    except (KeyError, IndexError, ValueError):
        return texto


# português -> inglês (o que não estiver aqui aparece em português)
EN = {
    # cabeçalho, abas e rodapé
    "Roube um Ovo": "Steal an Egg",
    'Clicar sempre na mesma posição': 'Always click at the same position',
    'Definir posição': 'Set position',
    'Leve o mouse… {n}': 'Move the mouse… {n}',
    'Posição: {x}, {y}': 'Position: {x}, {y}',
    'Nenhuma posição definida': 'No position set',
    'Parar se eu mexer o mouse': 'Stop if I move the mouse',
    'Distância para parar': 'Distance to stop',
    'Defina a posição primeiro: clique em Definir posição.': 'Set the position first: click Set position.',
    'Pare o AutoClick antes de definir a posição.': 'Stop AutoClick before setting the position.',
    'Posição do AutoClick definida: {x}, {y}.': 'AutoClick position set: {x}, {y}.',
    'Defina a posição fixa antes de iniciar (aba AutoClick).': 'Set the fixed position before starting (AutoClick tab).',
    'AutoClick parado: o mouse foi movido para longe.': 'AutoClick stopped: the mouse was moved away.',
    'O AutoClick leva o cursor ao mesmo ponto da tela antes de cada clique. Enquanto ele roda, o cursor fica preso nesse ponto. Use Parar se eu mexer o mouse para poder retomar o controle.': 'AutoClick moves the cursor to the same screen point before every click. While it runs, the cursor stays locked there. Use Stop if I move the mouse so you can take control back.',
    'Para o AutoClick sozinho se você afastar o mouse do ponto de clique. Pequenos tremores não contam: só um movimento maior que a distância escolhida.': "Stops AutoClick by itself if you move the mouse away from the click point. Small tremors don't count: only a movement larger than the chosen distance.",
    'Quantos pixels o mouse precisa se afastar para o AutoClick parar. 150 px é um movimento claro de propósito; aumente se parar sem querer.': 'How many pixels the mouse must move away for AutoClick to stop. 150 px is a clear, deliberate movement; raise it if it stops by accident.',
    'AutoClick com posição fixa e opção de parar ao mexer o mouse.': 'AutoClick with a fixed position and an option to stop when you move the mouse.',
    'Opções': 'Options',
    'Atalhos do teclado, modo mini, início com o Windows e aparência.': 'Keyboard shortcuts, mini mode, start with Windows and appearance.',
    'Clique na tecla e aperte a nova. Funcionam com outra janela na frente.': 'Click the key and press the new one. They work with another window in front.',
    'Aperte uma tecla…': 'Press a key…',
    'Restaurar atalhos': 'Reset shortcuts',
    'F1 a F12, Esc, Pause, Insert, Home, End, PgUp, PgDn': 'F1 to F12, Esc, Pause, Insert, Home, End, PgUp, PgDn',
    'Opacidade da janela mini': 'Mini window opacity',
    'Ver o modo mini': 'Preview mini mode',
    'Ao abrir': 'On startup',
    'Abrir junto com o Windows': 'Open with Windows',
    'Abrir como': 'Open as',
    'Janela': 'Window',
    'Bandeja': 'Tray',
    'Mini e Bandeja abrem o programa escondido: use o ícone da bandeja ou o F1 para controlar.': 'Mini and Tray open the program hidden: use the tray icon or F1 to control it.',
    'Aparência': 'Appearance',
    'Tema': 'Theme',
    'Claro': 'Light',
    'Escuro': 'Dark',
    'O tema novo vale quando você abrir o programa de novo.': 'The new theme applies the next time you open the program.',
    'Não foi possível criar o ícone da bandeja. A janela ficou aberta.': 'Could not create the tray icon. The window stayed open.',
    'Essa tecla não pode ser usada. Escolha F1 a F12, Esc, Pause, Insert, Home, End, PgUp ou PgDn.': "That key can't be used. Choose F1 to F12, Esc, Pause, Insert, Home, End, PgUp or PgDn.",
    'Atalhos atualizados.': 'Shortcuts updated.',
    'Não foi possível mudar a abertura com o Windows.': 'Could not change opening with Windows.',
    'O programa vai abrir junto com o Windows.': 'The program will open with Windows.',
    'O programa não abre mais junto com o Windows.': 'The program no longer opens with Windows.',
    'Deixa a janelinha do modo mini mais transparente para não atrapalhar o jogo. 100% é totalmente opaca.': "Makes the mini window more transparent so it doesn't get in the way of the game. 100% is fully opaque.",
    'O programa abre sozinho quando você liga o computador. Dá para desligar aqui a qualquer hora.': 'The program opens by itself when you turn on the computer. You can turn it off here at any time.',
    'Claro ou escuro. A mudança vale na próxima vez que o programa abrir.': 'Light or dark. The change applies the next time the program opens.',
    'Atalhos, modo mini, abrir com o Windows e tema claro ou escuro nas novas Opções.': 'Shortcuts, mini mode, open with Windows and light or dark theme in the new Options tab.',
    "Tem certeza que deseja fechar o programa?": "Are you sure you want to close the program?",
    "O programa será encerrado e a pesca e o AutoClick vão parar.": "The program will quit and fishing and AutoClick will stop.",
    "O programa será encerrado. Se preferir, ele pode continuar aberto no formato mini.": "The program will quit. If you prefer, it can keep running in mini mode.",
    "Cancelar": "Cancel",
    "Fechar o programa": "Close the program",
    "Deixar no formato mini e continuar aberto": "Switch to mini mode and keep it open",
    "Confirmação ao fechar, com a opção de deixar o programa no formato mini.": "Close confirmation, with the option to switch to mini mode.",
    "1 clique a cada {t}": "1 click every {t}",
    "Agora o intervalo do AutoClick é em horas, minutos, segundos e milissegundos.": "The AutoClick interval is now set in hours, minutes, seconds and milliseconds.",
    "Agora só uma janela do programa abre por vez; abrir de novo traz a janela que já está aberta.": "Only one program window opens at a time; opening it again brings the existing window to the front.",
    "Cores com mais contraste e novo título: Roube um Ovo.": "Higher-contrast colors and a new title: Steal an Egg.",
    "Roube um Ovo, no Roblox": "For Steal An Egg, on Roblox",
    "Mini": "Mini",
    "Painel": "Dashboard",
    "AutoClick": "AutoClick",
    "Detecção": "Detection",
    "Ajustes": "Settings",
    "Registro": "Log",
    "pesca": "fishing",
    "autoclick": "autoclick",
    "calibrar": "calibrate",
    "parar tudo": "stop all",
    # etapas da pesca
    "Parado": "Stopped",
    "Rodando": "Running",
    "Aguardando o Roblox": "Waiting for Roblox",
    "Lançando a vara": "Casting the rod",
    "Aguardando o minigame": "Waiting for the minigame",
    "Clicando": "Clicking",
    "Pausa": "Pause",
    "Abra o Roblox, fique de frente para a água e aperte F1.": "Open Roblox, face the water and press F1.",
    "Deixe a janela do Roblox aberta e em primeiro plano.": "Keep the Roblox window open and in the foreground.",
    "Segurando o clique para carregar a vara.": "Holding the click to charge the rod.",
    "Esperando o botão PARAR aparecer.": "Waiting for the STOP button to appear.",
    "Clicando rápido no minigame.": "Clicking fast in the minigame.",
    "Esperando o aviso do prêmio sumir.": "Waiting for the prize notice to disappear.",
    "tempo máximo restante:": "max time left:",
    "Clicando até o botão PARAR sumir": "Clicking until the STOP button disappears",
    "restam": "left",
    "parado": "stopped",
    "segundos": "seconds",
    "cliques": "clicks",
    "aguardando": "waiting",
    # AutoClick
    "Leve o mouse ao alvo e aperte F2, ou defina uma posição fixa.": "Move the mouse to the target and press F2, or set a fixed position.",
    "Leve o mouse até onde quer clicar.": "Move the mouse to where you want to click.",
    "Clicando na posição do mouse. Aperte F2 ou Esc para parar.": "Clicking at the mouse position. Press F2 or Esc to stop.",
    "Começa em {s:.1f} s": "Starts in {s:.1f} s",
    "≈ {n:.1f} cliques por segundo": "≈ {n:.1f} clicks per second",
    "Configuração": "Configuration",
    "Botão do mouse": "Mouse button",
    "Meio": "Middle",
    "Direito": "Right",
    "Esquerdo": "Left",
    "Só clicar com o Roblox em primeiro plano": "Only click with Roblox in the foreground",
    "O AutoClick clica onde o mouse estiver, sem mover o cursor. Use o atraso para levar o mouse ao alvo depois de iniciar. F2 ou Esc param na hora.":
        "AutoClick clicks wherever the mouse is, without moving the cursor. Use the delay to move the mouse to the target after starting. F2 or Esc stop it immediately.",
    "Iniciar AutoClick  (F2)": "Start AutoClick  (F2)",
    "Parar AutoClick  (F2)": "Stop AutoClick  (F2)",
    # painel
    "Iniciar  (F1)": "Start  (F1)",
    "Parar  (F1)": "Stop  (F1)",
    "Ciclos": "Cycles",
    "Cliques": "Clicks",
    "Cliques por s": "Clicks per s",
    "Tempo ativo": "Active time",
    "•  Pronto para começar.": "•  Ready to start.",
    # detecção
    "Detectar o minigame pela cor": "Detect the minigame by color",
    "O macro olha o botão vermelho PARAR para saber quando o minigame começa e quando acaba. Sem calibração ele usa os tempos fixos dos ajustes.":
        "The macro watches the red STOP button to know when the minigame starts and ends. Without calibration it uses the fixed times from Settings.",
    "Abra o jogo e deixe o minigame na tela.": "Open the game and keep the minigame on screen.",
    "Passe o mouse sobre a parte vermelha do botão PARAR.": "Hover the mouse over the red part of the STOP button.",
    "Aperte F3 ou clique em Calibrar. Só precisa fazer uma vez.": "Press F3 or click Calibrate. You only need to do it once.",
    "Calibrar  (F3)": "Calibrate  (F3)",
    "Limpar": "Clear",
    "cor lida": "color read",
    "Situação agora": "Current status",
    "Botão PARAR: sem calibração": "STOP button: not calibrated",
    "Botão PARAR: visível agora": "STOP button: visible now",
    "Botão PARAR: não visível": "STOP button: not visible",
    "detecção ativa": "detection on",
    "tempos fixos": "fixed times",
    "Calibrado para {larg}×{alt}, com {usando}.": "Calibrated for {larg}×{alt}, with {usando}.",
    "Não calibrado: o macro usa os tempos fixos.": "Not calibrated: the macro uses fixed times.",
    # ajustes
    "Carga da vara": "Rod charge",
    "Intervalo entre cliques": "Click interval",
    "Pausa entre ciclos": "Pause between cycles",
    "Tempo máx. de espera": "Max wait time",
    "Tolerância de cor": "Color tolerance",
    "Espera fixa (sem detecção)": "Fixed wait (no detection)",
    "Cliques fixos (sem detecção)": "Fixed clicks (no detection)",
    "Atraso para começar": "Start delay",
    "Limite de cliques": "Click limit",
    "ciclos": "cycles",
    "Lançamento e cliques": "Casting and clicks",
    "Detecção do minigame": "Minigame detection",
    "Sem detecção (tempos fixos)": "No detection (fixed times)",
    "Interface": "Interface",
    "Idioma": "Language",
    "Minimizar para a bandeja do sistema": "Minimize to the system tray",
    "Janela e segurança": "Window and safety",
    "Só rodar com o Roblox em primeiro plano": "Only run with Roblox in the foreground",
    "Manter esta janela sempre por cima": "Keep this window always on top",
    "Restaurar padrões": "Restore defaults",
    # registro
    "Atividade do macro": "Macro activity",
    "Abrir pasta": "Open folder",
    # mensagens do app
    "Versão {v}. Ajustes salvos em {pasta}": "Version {v}. Settings saved in {pasta}",
    "Não consegui abrir a pasta {pasta}: {e}": "Could not open the folder {pasta}: {e}",
    "Parando o AutoClick...": "Stopping AutoClick...",
    "Pare o macro de pesca (F1) antes de usar o AutoClick.": "Stop the fishing macro (F1) before using AutoClick.",
    "AutoClick iniciado.": "AutoClick started.",
    "Ajustes restaurados para os padrões (a calibração foi mantida).": "Settings restored to defaults (calibration was kept).",
    "Pare o macro (F1) antes de calibrar.": "Stop the macro (F1) before calibrating.",
    "Janela do Roblox não encontrada. Abra o jogo e deixe o minigame na tela.":
        "Roblox window not found. Open the game and keep the minigame on screen.",
    "O mouse precisa estar sobre a janela do Roblox, em cima do botão PARAR.":
        "The mouse must be over the Roblox window, on top of the STOP button.",
    "Não consegui ler a cor da tela nesse ponto.": "Could not read the screen color at that point.",
    "Calibrado, mas a cor RGB=({r},{g},{b}) não parece vermelha. Confira se o mouse estava sobre o botão PARAR.":
        "Calibrated, but the RGB=({r},{g},{b}) color doesn't look red. Check that the mouse was over the STOP button.",
    "Botão PARAR calibrado: cor RGB=({r},{g},{b}).": "STOP button calibrated: color RGB=({r},{g},{b}).",
    "Calibração removida.": "Calibration removed.",
    "Parando...": "Stopping...",
    "Pare o AutoClick (F2) antes de iniciar o macro de pesca.": "Stop AutoClick (F2) before starting the fishing macro.",
    "Detecção ativada, mas sem calibração: usando os tempos fixos.": "Detection is on but not calibrated: using fixed times.",
    "A janela do Roblox mudou de tamanho desde a calibração. Se o minigame não for detectado, calibre de novo (F3).":
        "The Roblox window changed size since calibration. If the minigame isn't detected, calibrate again (F3).",
    "Macro iniciado.": "Macro started.",
    "Ciclo {n} concluído: {cliques} cliques em {dur:.1f}s ({cps:.0f}/s)": "Cycle {n} done: {cliques} clicks in {dur:.1f}s ({cps:.0f}/s)",
    "Macro parado.": "Macro stopped.",
    "Resumo da sessão: {ciclos} ciclos, {cliques} cliques em {tempo}.": "Session summary: {ciclos} cycles, {cliques} clicks in {tempo}.",
    "AutoClick parado: {cliques} cliques em {dur:.1f}s ({cps:.0f}/s).": "AutoClick stopped: {cliques} clicks in {dur:.1f}s ({cps:.0f}/s).",
    "Parada de emergência (Esc).": "Emergency stop (Esc).",
    "Parada de emergência do AutoClick (Esc).": "AutoClick emergency stop (Esc).",
    "Idioma alterado para {nome}.": "Language changed to {nome}.",
    "Não consegui criar o ícone da bandeja: {e}": "Could not create the tray icon: {e}",
    "Erro interno: {e}": "Internal error: {e}",
    "o Windows não aceitou o ícone": "Windows did not accept the icon",
    # bandeja e modo mini
    "Abrir janela": "Open window",
    "Modo mini": "Mini mode",
    "Iniciar pesca (F1)": "Start fishing (F1)",
    "Parar pesca (F1)": "Stop fishing (F1)",
    "Iniciar AutoClick (F2)": "Start AutoClick (F2)",
    "Parar AutoClick (F2)": "Stop AutoClick (F2)",
    "Sair": "Quit",
    "Ciclos {n}  ·  Cliques {c}  ·  {t}": "Cycles {n}  ·  Clicks {c}  ·  {t}",
    "Cliques {c}  ·  {cps}/s  ·  {t}": "Clicks {c}  ·  {cps}/s  ·  {t}",
    "Pronto. F1 Pesca, F2 AutoClick.": "Ready. F1 Fishing, F2 AutoClick.",
    "Pesca (F1)": "Fishing (F1)",
    "Parar (F1)": "Stop (F1)",
    "Parar (F2)": "Stop (F2)",
    "Abrir": "Open",
    # workers
    "A janela do Roblox sumiu há mais de 1 minuto. O jogo fechou?": "The Roblox window has been gone for over 1 minute. Did the game close?",
    "Janela do Roblox não encontrada. Aguardando...": "Roblox window not found. Waiting...",
    "Aguardando o Roblox ficar em primeiro plano...": "Waiting for Roblox to come to the foreground...",
    "O minigame não apareceu em {limite:.0f}s. A vara pode não ter sido lançada (aviso do prêmio ainda na tela?). Se repetir, aumente a pausa entre ciclos.":
        "The minigame didn't appear within {limite:.0f}s. The rod may not have been cast (prize notice still on screen?). If it repeats, increase the pause between cycles.",
    "Minigame detectado após {t:.1f}s": "Minigame detected after {t:.1f}s",
    "Falha ao ler a tela durante os cliques: {e}": "Failed to read the screen while clicking: {e}",
    "O Roblox saiu do primeiro plano. Cliques interrompidos.": "Roblox left the foreground. Clicks interrupted.",
    "Erro: {e}": "Error: {e}",
    "Limite de {limite} cliques atingido. AutoClick parado.": "Limit of {limite} clicks reached. AutoClick stopped.",
    "Roblox fora de primeiro plano. AutoClick em pausa.": "Roblox is not in the foreground. AutoClick paused.",
    "Roblox em primeiro plano. AutoClick retomado.": "Roblox is in the foreground. AutoClick resumed.",
    "Erro no AutoClick: {e}": "AutoClick error: {e}",
    # nova interface (barra lateral e painel)
    "Resumo da sessão e controle do ciclo automático.": "Session summary and control of the automatic cycle.",
    "Ensine o macro a reconhecer quando o minigame aparece.": "Teach the macro to recognize when the minigame appears.",
    "Clica sem parar no ponto onde o mouse estiver.": "Clicks nonstop wherever the mouse is.",
    "Tempos, idioma e comportamento da janela.": "Timings, language and window behavior.",
    "O que o macro fez, em ordem.": "What the macro did, in order.",
    "Ciclo automático": "Automatic cycle",
    "F1 inicia ou para.": "F1 starts or stops.",
    "Calibrar": "Calibrate",
    "Parar tudo": "Stop all",
    "Parar AutoClick": "Stop AutoClick",
    "F3 · botão PARAR": "F3 · STOP button",
    "F2 · sem parar": "F2 · nonstop",
    "janela pequena": "small window",
    "ajustes salvos": "saved settings",
    "Esc · emergência": "Esc · emergency",
    "Sessão": "Session",
    "Atividade": "Activity",
    "Ciclos por min": "Cycles per min",
    "Média por ciclo": "Avg per cycle",
    "Melhor ciclo": "Best cycle",
    "Roblox": "Roblox",
    "Sem calibração": "Not calibrated",
    "Ativa": "On",
    "Desligada": "Off",
    "Aberto": "Open",
    "Fechado": "Closed",
    "Nada por aqui ainda.": "Nothing here yet.",
    "INFO": "INFO",
    "OK": "OK",
    "AVISO": "WARN",
    "ERRO": "ERROR",
    "Calibração": "Calibration",
    "Ajuste fino": "Fine tuning",
    "Dica: calibre de novo se mudar o tamanho da janela do Roblox.": "Tip: calibrate again if you resize the Roblox window.",
    "Sobre": "About",
    "Versão": "Version",
    "Pasta de ajustes": "Settings folder",
    # cartão Novidades
    "Novidades": "What's new",
    "NOVO": "NEW",
    "MELHORIA": "IMPROVED",
    "CORREÇÃO": "FIX",
    "Lançamento oficial do Roube um Ovo.": "Official launch of Steal an Egg.",
    "Cartão Novidades com o resumo das atualizações.": "What's new card with a summary of the updates.",
    "Nova interface com barra lateral e cinco páginas.": "New interface with a sidebar and five pages.",
    "Painel com os números da sessão e atalhos rápidos.": "Dashboard with session numbers and quick actions.",
    "Atividade recente e botão Parar tudo no painel.": "Recent activity and a Stop all button on the dashboard.",
    "Controles deslizantes mais largos nos Ajustes.": "Wider sliders in Settings.",
    "O programa ganhou o ícone do ovo no .exe.": "The program now has the egg icon on the .exe.",
    # v5.2: guia, ajuda e explicações
    "Aba Ajuda com passo a passo e soluções para os problemas mais comuns.":
        "Help tab with a step-by-step guide and fixes for the most common problems.",
    "Guia no painel que mostra o que falta fazer e marca cada passo sozinho.":
        "Dashboard guide that shows what is left to do and checks off each step by itself.",
    "O ícone ? ao lado dos ajustes explica o que cada um faz.": "The ? icon next to each setting explains what it does.",
    "Atalhos do teclado sempre visíveis na barra lateral.": "Keyboard shortcuts always visible in the sidebar.",
    "O painel diz qual é o próximo passo e pede confirmação antes de restaurar os padrões.":
        "The dashboard tells you the next step and asks for confirmation before restoring defaults.",
    "Ajuda": "Help",
    "Guia": "Guide",
    "parar": "stop",
    "Pesca automática": "Automatic fishing",
    "Comece por aqui: veja o que falta e controle a pesca.": "Start here: see what's missing and control fishing.",
    "Ensine o macro a reconhecer o botão PARAR (uma vez só).": "Teach the macro to recognize the STOP button (only once).",
    "Clica sem parar onde o mouse estiver. Não é a pesca.": "Clicks nonstop wherever the mouse is. It is not the fishing macro.",
    "Velocidade, pausas e comportamento da janela. Passe o mouse no ? para ver o que cada um faz.":
        "Speed, pauses and window behavior. Hover the ? to see what each one does.",
    "Tudo o que o macro fez, em ordem. Se algo der errado, a pista está aqui.":
        "Everything the macro did, in order. If something goes wrong, the clue is here.",
    "Passo a passo e soluções para os problemas mais comuns.": "Step by step guide and fixes for the most common problems.",
    "Abra o Roblox e deixe o jogo de frente para a água.": "Open Roblox and face the water.",
    "Falta calibrar o botão PARAR. Abra a aba Calibrar e siga os 3 passos.":
        "The STOP button still needs calibrating. Open the Detection tab and follow the 3 steps.",
    "Tudo pronto. Fique de frente para a água e aperte F1.": "All set. Face the water and press F1.",
    "Abrir o Roblox": "Open Roblox",
    "Deixe o jogo aberto, de frente para a água.": "Keep the game open, facing the water.",
    "Calibrar o botão PARAR": "Calibrate the STOP button",
    "Só na primeira vez, leva 1 minuto. Clique aqui para ir à aba Calibrar.":
        "Only the first time, it takes 1 minute. Click here to go to the Detection tab.",
    "Apertar F1": "Press F1",
    "A pesca roda sozinha. Para parar, aperte F1 de novo ou Esc.":
        "Fishing runs by itself. To stop, press F1 again or Esc.",
    "Como usar": "How to use",
    "Abra o Roblox e fique de frente para a água.": "Open Roblox and face the water.",
    "Na aba Calibrar, calibre o botão PARAR. Só na primeira vez.":
        "In the Detection tab, calibrate the STOP button. Only the first time.",
    "Aperte F1. O macro lança a vara, espera o minigame e clica rápido sozinho.":
        "Press F1. The macro casts the rod, waits for the minigame and clicks fast by itself.",
    "Para parar, aperte F1 de novo. Em emergência, aperte Esc.": "To stop, press F1 again. In an emergency, press Esc.",
    "Atalhos do teclado": "Keyboard shortcuts",
    "Como usar em 4 passos": "How to use it in 4 steps",
    "Interface nova, clara e suave, com abas no topo e o botão Iniciar em destaque.": "New, clear and soft interface, with tabs on top and a prominent Start button.",
    "Painel mais simples: só o essencial para pescar, com o guia ao lado.": "Simpler dashboard: just what you need to fish, with the guide beside it.",
    "Os atalhos funcionam mesmo com outra janela na frente.": "Shortcuts work even with another window in front.",
    "Iniciar ou parar a pesca": "Start or stop fishing",
    "Iniciar ou parar o AutoClick": "Start or stop AutoClick",
    "Parar tudo na hora": "Stop everything immediately",
    "Se algo der errado": "If something goes wrong",
    "O macro não faz nada": "The macro does nothing",
    "Deixe o Roblox na frente das outras janelas. Se não for isso, abra a aba Registro: ela diz o que o macro está esperando.":
        "Keep Roblox in front of the other windows. If that's not it, open the Log tab: it says what the macro is waiting for.",
    "A vara não é lançada": "The rod is not cast",
    "Aumente a Carga da vara nos Ajustes e confira se o personagem está de frente para a água.":
        "Increase the Rod charge in Settings and check that the character is facing the water.",
    "O minigame não é detectado": "The minigame is not detected",
    "Calibre de novo (F3) com o minigame na tela e o mouse sobre a parte vermelha do botão PARAR. Se você mudou o tamanho da janela do jogo, calibre outra vez.":
        "Calibrate again (F3) with the minigame on screen and the mouse over the red part of the STOP button. If you resized the game window, calibrate again.",
    "Os cliques estão rápidos ou lentos demais": "Clicks are too fast or too slow",
    "Mude o Intervalo entre cliques nos Ajustes. Quanto menor o intervalo, mais rápido ele clica.":
        "Change the Click interval in Settings. The smaller the interval, the faster it clicks.",
    "Quero usar outros programas enquanto roda": "I want to use other programs while it runs",
    "O macro clica com o mouse de verdade, então o Roblox precisa ficar na frente. Use o Modo mini para acompanhar sem cobrir o jogo.":
        "The macro clicks with the real mouse, so Roblox must stay in front. Use Mini mode to follow along without covering the game.",
    "Como o macro lança a vara e clica no minigame.": "How the macro casts the rod and clicks in the minigame.",
    "Tempos usados no lugar da detecção.": "Timings used in place of detection.",
    "Em uso agora: a detecção está desligada ou sem calibração.": "In use now: detection is off or not calibrated.",
    "Não usados agora: a detecção está ligada e calibrada.": "Not used now: detection is on and calibrated.",
    "Padrão: {v} {u}": "Default: {v} {u}",
    "Quanto tempo o clique fica segurado para lançar a vara. Aumente se ela não chega na água; diminua se o lançamento passa do ponto.":
        "How long the click is held to cast the rod. Increase it if the rod doesn't reach the water; decrease it if the cast goes too far.",
    "Tempo entre um clique e outro durante o minigame. Menor = clica mais rápido (15 ms são cerca de 60 cliques por segundo).":
        "Time between clicks during the minigame. Smaller = clicks faster (15 ms is about 60 clicks per second).",
    "Espera depois de cada pesca, para o aviso do prêmio sumir antes de lançar de novo. Se o macro lançar com o aviso ainda na tela, aumente.":
        "Wait after each catch so the prize notice disappears before casting again. If the macro casts while the notice is still on screen, increase it.",
    "Quanto tempo o macro espera o minigame aparecer depois de lançar a vara. Passou disso, ele tenta de novo.":
        "How long the macro waits for the minigame after casting. Past that, it tries again.",
    "O quanto a cor lida pode variar da cor calibrada. Aumente se o macro não acha o botão PARAR; diminua se ele confunde com outras coisas vermelhas.":
        "How much the color it reads may differ from the calibrated color. Increase it if the macro can't find the STOP button; decrease it if it mistakes other red things for it.",
    "Só vale com a detecção desligada ou sem calibração: tempo de espera até o minigame aparecer.":
        "Only applies with detection off or not calibrated: how long to wait for the minigame to appear.",
    "Só vale com a detecção desligada ou sem calibração: por quanto tempo clicar no minigame.":
        "Only applies with detection off or not calibrated: how long to click in the minigame.",
    "Tempo entre um clique e outro, em horas, minutos, segundos e milissegundos. Menor = clica mais rápido. 100 ms são 10 cliques por segundo.":
        "Time between clicks, in hours, minutes, seconds and milliseconds. Smaller = clicks faster. 100 ms is 10 clicks per second.",
    "Tempo de espera depois de iniciar, para você levar o mouse até o alvo.":
        "Wait after starting, so you can move the mouse to the target.",
    "O AutoClick para sozinho depois desse número de cliques. Zero = clica até você parar.":
        "AutoClick stops by itself after this many clicks. Zero = clicks until you stop it.",
    "Liga a leitura do botão vermelho PARAR do minigame. Com ela o macro sabe quando o minigame começa e acaba. Precisa de calibração (nesta aba).":
        "Turns on reading the red STOP button of the minigame. With it the macro knows when the minigame starts and ends. It needs calibration (in this tab).",
    "O macro só clica enquanto o Roblox estiver na frente. Evita clicar em outros programas por engano. Recomendado.":
        "The macro only clicks while Roblox is in front. It avoids clicking other programs by mistake. Recommended.",
    "Mantém esta janela na frente das outras, para você acompanhar o macro.":
        "Keeps this window in front of the others so you can follow the macro.",
    "Ao minimizar, a janela some e o ícone fica na bandeja do sistema, perto do relógio. Clique no ícone para abrir de novo.":
        "When minimized, the window disappears and the icon stays in the system tray, near the clock. Click the icon to open it again.",
    "O AutoClick só clica enquanto o Roblox estiver na frente. Se o Roblox sair da frente, ele pausa.":
        "AutoClick only clicks while Roblox is in front. If Roblox leaves the front, it pauses.",
    "Ensina o macro a achar o botão vermelho PARAR do minigame. Faça uma vez, com o minigame na tela e o mouse sobre o botão.":
        "Teaches the macro to find the red STOP button of the minigame. Do it once, with the minigame on screen and the mouse over the button.",
    "Clica sem parar onde o mouse estiver, em qualquer jogo ou programa. Não é a pesca.":
        "Clicks nonstop wherever the mouse is, in any game or program. It is not the fishing macro.",
    "Troca esta janela por uma janelinha que fica por cima do jogo, só com o essencial.":
        "Swaps this window for a small one that stays on top of the game, with just the essentials.",
    "Abre a pasta onde ficam salvos os seus ajustes e a calibração.": "Opens the folder where your settings and calibration are saved.",
    "Para a pesca e o AutoClick na hora. Também funciona com a tecla Esc.":
        "Stops fishing and AutoClick immediately. The Esc key does the same.",
    "Clique de novo para confirmar": "Click again to confirm",
    "Cliques/ciclo": "Clicks/cycle",
    "Recorde": "Record",
    "Como testar: com o minigame na tela, o botão PARAR deve aparecer como visível. Sem o minigame, como não visível.":
        "How to test: with the minigame on screen, the STOP button should show as visible. Without it, as not visible.",
    "Pescar": "Fish",
    "Atalhos": "Shortcuts",
    "Antes de começar": "Before you start",
    "Últimas mensagens": "Latest messages",
    "Parar tudo  (Esc)": "Stop all  (Esc)",
}
