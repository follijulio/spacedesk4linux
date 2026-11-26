# Comportamento mapeado

Os fatos do serviço original abaixo vêm de inspeção estática e decompilação de `spacedeskService.exe`; o executável não foi executado. Nenhum código decompilado foi copiado para o aplicativo.

- **O serviço depende das APIs de display e do adaptador virtual spacedesk.** A rotina de início exige as APIs de display, um identificador de adaptador válido e eventos antes de iniciar o manipulador de eventos: função `0x1400addc0`, evidência `ev_f0a5634939a6e9ab4eaf01b797301e314f465a938f68c90e327bca06df8757c9`.
- **A conexão de rede é controlada pela configuração `NetworkConnectionEnabled`.** Quando ativa, a rotina prepara o conector TCP e inicia uma thread listener: função `0x14008b560`, evidência `ev_dfa378bf0b3b3cc1a010a9cb32408ab917ae50f658b3293dc92b57320d5fb1df`.
- **O listener trata tráfego HTTP com handshake WebSocket e também identifica cabeçalhos próprios.** Função `0x1400e0710`, evidência `ev_c7661b6dc7201c1d2228fffd298f7f692e5053782ffa7124414b628d20494ce8`.
- **A seleção de formatos de captura é enviada ao driver de display por DeviceIoControl.** Função `0x14009b890`, evidência `ev_9577e0e85dcde903b5f0669f79dcea44ad133132c33ff9d01e34066034fc7d08`.

## Valores do spacedesk for Linux

A implementação oferece uma alternativa de navegador: captura a área de trabalho (todos os monitores quando disponíveis), reduz quadros largos para no máximo 1920 px, codifica como JPEG e envia quadros novos como HTTP/MJPEG. O servidor atende pela porta 18900. No X11, o app pode expandir a área de trabalho e adicionar um monitor lógico à direita com xrandr; no Wayland, a tela virtual é configurada pelo ambiente gráfico. Esses valores são estimativas de implementação, não valores do spacedesk. A inspeção do binário não encontrou uma taxa de quadros ou qualidade de imagem fixa e universal.

A opção `--screenshot <arquivo.png>` aguarda 120 atualizações da janela antes de salvar o PNG e encerrar. O modo não ativa a janela no Windows e a coloca atrás de outras janelas. No Linux, não é rebaixada.
