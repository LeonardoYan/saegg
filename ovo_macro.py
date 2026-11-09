"""
Macro do Ovo - Roube um Ovo (Roblox)

Requisitos: Windows, Python 3.10+
Instalação:  pip install pynput
Execução:    python ovo_macro.py

Fluxo do macro:
  1) Segura o clique para carregar a vara e solta
  2) Espera o minigame "Clique Rápido!" aparecer. Isso é detectado olhando um ponto fixo da tela
     (o botão vermelho PARAR), então funciona não importa quanto tempo o minigame demore.
  3) Clica rápido até o botão PARAR sumir (peixe fisgado)
  4) Pausa (o aviso do prêmio some) e repete

Calibração (uma vez só): com o minigame na tela, passe o mouse sobre a parte vermelha do botão
PARAR e aperte F3. A posição é guardada em proporção da janela do Roblox.

Atalhos globais: F1 = iniciar/parar a pesca | F2 = iniciar/parar o AutoClick | F3 = calibrar o botão PARAR
                | Esc = parada de emergência (para tudo)

Aba AutoClick: clica sem parar onde o mouse estiver (botão esquerdo, direito ou do meio), com intervalo,
atraso inicial e limite de cliques ajustáveis. Não roda ao mesmo tempo que o macro de pesca.
Sem calibração, o macro usa os tempos fixos dos ajustes.

Interface: barra lateral com as páginas Painel (resumo e controle), Detecção, AutoClick, Ajustes, Registro e Ajuda.
O Painel tem um Guia que marca sozinho o que falta fazer; passe o mouse no ícone ? dos ajustes para ver a explicação.

Modo mini: uma janelinha sempre por cima com o estado, os números e os botões de iniciar/parar (botão Mini).
Bandeja: opção em Ajustes para minimizar a janela para a bandeja do sistema (clique no ícone para abrir;
clique direito abre o menu).
Idioma: português ou inglês, em Ajustes (vale na hora, sem reiniciar).

Parada: o macro roda até você parar (F1 ou o botão), e Esc é a parada de emergência. O registro do que
acontece aparece na aba Registro (fica só na tela, nada é gravado em arquivo).
"""
from macroovo.app import main

if __name__ == "__main__":
    main()
