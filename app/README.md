# spacedesk for Linux

Aplicativo de desktop para Linux que transmite a tela para o navegador de um tablet na mesma rede local.

## Usar

1. Instale Python 3, Tkinter e Pillow. Em distribuições baseadas em Debian/Ubuntu, os pacotes costumam ser `python3`, `python3-tk` e `python3-pil`.
2. No terminal, entre nesta pasta e execute `python3 main.py`.
3. Clique em **Iniciar transmissão** e digite no navegador do tablet o endereço exibido no painel. Os dois aparelhos precisam estar conectados à mesma rede.
4. Clique em **Parar transmissão** quando terminar.

A captura é enviada como JPEG por HTTP/MJPEG, em uma porta TCP local, com intervalo de 50 ms e largura máxima de 1920 px. Em Linux com X11, clique em **Criar tela estendida para o tablet** para ampliar a área de trabalho e criar um monitor lógico à direita; arraste uma janela para essa área e ela aparecerá no tablet. O tablet mostra apenas essa nova área; o botão **Remover tela estendida** restaura o tamanho anterior. No Wayland, use as configurações do ambiente gráfico para adicionar um monitor virtual. No navegador do tablet, use **Tela cheia** para ocupar a tela inteira. O navegador precisa permitir conteúdo local na rede; a porta 18900 pode precisar ser liberada no firewall do Linux.

Este aplicativo usa um receptor de navegador. A investigação do serviço spacedesk para Windows encontrou dependências de um adaptador virtual de tela e um protocolo proprietário; não confirmou compatibilidade com o app spacedesk para tablet.

## Captura de verificação

`python3 main.py --screenshot caminho.png` abre a janela, aguarda 120 quadros e salva sua imagem em PNG. No Windows, a janela de captura abre sem ativação e atrás de outras janelas.

## Ajustes

A porta, o intervalo de captura, a qualidade JPEG e a largura máxima ficam no início de `main.py` e também estão listados em `mechanics.json`.
