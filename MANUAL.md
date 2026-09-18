# Manual de uso — Leitor PAT & BAT (Polo 24)

Guia rápido para operar o aplicativo de leitura de QR code e código de barras no celular.

🔗 **Acesse pelo navegador do celular:** https://jofilho71.github.io/leitor-qrcodes-android/

> Dica: no Chrome do Android, toque no menu (⋮) e em **"Adicionar à tela inicial"** para abrir o app como
> um atalho, sem precisar digitar o link toda vez.

---

## 1. Visão geral da tela

No topo há dois botões: **Bateria** e **Inventário**. Escolha o modo antes de começar a escanear — eles
funcionam de formas diferentes e não podem ser misturados na mesma coleta.

Abaixo dos botões de modo, ficam os controles de leitura (Galeria e Câmera) e, durante a leitura, um aviso
colorido mostrando o que o app está esperando.

No rodapé, sempre visível: o contador de itens lidos e três botões — **Salvar CSV**, **Compartilhar CSV**
e **Limpar**.

⚠️ **Trocar de modo (Bateria ↔ Inventário) com leituras ainda não exportadas apaga essas leituras** — o
app pergunta antes de trocar ("Trocar de modo? Os dados ainda não exportados serão perdidos."). Se tiver
dúvida, cancele, exporte primeiro e só depois troque de modo.

---

## 2. Modo Bateria

Usado para parear o **QR code da etiqueta da bateria** com o **código de barras (patrimônio) da urna**.

### Como ler

1. Toque no botão de **Câmera** (ícone de câmera) para ligar a leitura ao vivo, ou no botão de
   **Galeria** para escolher fotos já tiradas.
2. **Aponte primeiro para o QR code.** A ordem importa: o QR sempre precisa ser lido antes do código de
   barras.
3. Depois que o QR for aceito, aponte para o **código de barras** da urna. Quando os dois forem lidos, o
   par é gravado automaticamente.
4. Repita para o próximo par: QR → código de barras.

### O que o aviso colorido significa

| Cor | Texto | Situação |
|---|---|---|
| Branco | "Esperando leitura de QR Code" | Nenhuma leitura pendente — pode escanear um QR |
| Amarelo | "Esperando leitura de CB" | QR já lido, falta o código de barras da mesma urna |
| Verde | "Par incluído" | Par gravado com sucesso (some sozinho depois de 1 segundo) |

### Situações especiais (o app já trata sozinho)

- **Código de barras lido sem ter lido o QR antes**: é ignorado, nada acontece. Aponte primeiro para o QR.
- **Etiqueta com um código de barras "decoy" colado perto do QR**: se esse código repetir os mesmos dados
  do QR, o app ignora e continua esperando o código de barras verdadeiro da urna.
- **Leitura ruidosa do código de barras** (pouca luz, fora de foco, câmera tremendo): se o número lido não
  bater com o padrão do patrimônio (10 dígitos começando com `4551`), o app ignora essa leitura e continua
  esperando — aponte de novo, com mais luz e mantendo o celular firme, até o código ser lido certo.
- **Código de barras cortado na borda da tela**: se o código estiver parcialmente fora do enquadramento, a
  leitura é ignorada mesmo que pareça um número válido — centralize o código de barras dentro da moldura
  antes de aproximar, em vez de deixá-lo perto da borda da imagem.
- **Parar a câmera com um QR pendente** (sem ter lido o código de barras ainda): o app grava esse QR
  sozinho (sem patrimônio) e avisa: *"QR gravado sem par (código de barras não lido)."* Se precisar
  completar depois, ligue a câmera de novo e leia um novo QR + código de barras normalmente — não dá para
  editar o registro já gravado.
- **Não existe gravação automática por demora** — o app não grava nada sozinho só porque você demorou
  entre o QR e o código de barras. Ele só grava incompleto se você **parar a câmera manualmente**.

---

## 3. Modo Inventário

Usado para contar/registrar patrimônios (urnas, peças, etc.) avulsos, sem parear nada.

### Antes de escanear

1. Escolha a **opção** no menu (Runin, Reserva, Movimentação ou Conserto).
2. Se quiser, escreva uma **nota** curta (opcional, até 80 caracteres).

Essas duas informações valem para todas as leituras seguintes, até você mudar — não precisa escolher de
novo a cada leitura, só se a categoria mudar no meio da coleta.

### Como ler

- Toque em **Câmera** ou **Galeria**, igual ao modo Bateria.
- **Só QR code é lido — código de barras é ignorado nesse modo.** Aponte para o QR code que fica ao lado
  do código de barras na etiqueta da urna, não para o código de barras.
- O app lê o número de patrimônio de dentro do QR (não precisa mais mirar no código de barras, que é mais
  sujeito a erro de leitura). **Só patrimônios no padrão correto são aceitos** (equivalente a 10 dígitos
  começando com `4551`). Qualquer QR sem essa informação, ou fora do padrão, é ignorado, sem aviso de erro.
- **Um mesmo patrimônio nunca é contado duas vezes** na mesma coleta — se por engano você passar a câmera
  de novo sobre um código já lido (ou ler a mesma etiqueta em outra foto da galeria), ele é descartado
  automaticamente. Não precisa se preocupar em escanear "de mais".
- **Leitura muito parecida com a anterior**: se um número lido tiver só 1 ou 2 dígitos diferentes do
  último patrimônio aceito, o app descarta — é sinal de decodificação errada do mesmo código físico, não
  um item novo. Se por acaso dois itens diferentes de verdade tiverem números vizinhos (ex.: patrimônios
  sequenciais) e o segundo for descartado por engano, escaneie outro item qualquer no meio e depois volte
  nele — repetir a mesma leitura na hora não resolve, porque o "último aceito" continua sendo o mesmo.

À medida que os patrimônios são lidos, eles aparecem numa lista na tela, numerados na ordem da leitura —
use essa lista para conferir o que já foi escaneado sem precisar exportar o arquivo.

---

## 4. Câmera ao vivo x Fotos da galeria

- **Câmera**: aponte o celular e mantenha firme por um instante sobre o código — o app lê sozinho, sem
  precisar tocar em nada. Toque de novo no botão (que vira um ícone de "parar") para desligar a câmera.
- **Galeria**: útil para lotes de fotos já tiradas antes, ou quando a câmera ao vivo não funciona bem
  (pouca luz, foco). Pode selecionar várias fotos de uma vez; o app processa uma por uma e mostra uma
  barra de progresso.

Se uma foto da galeria não tiver nenhum código legível, o app avisa "Nenhum código encontrado" (no modo
Bateria isso também vira uma linha no CSV, marcando o erro).

---

## 5. Exportando os dados

Os três botões do rodapé:

- **Salvar CSV**: baixa o arquivo direto no celular (pasta de Downloads).
- **Compartilhar CSV**: abre o menu de compartilhar do celular (WhatsApp, e-mail, Drive, etc.) já com o
  arquivo CSV pronto como anexo. Se o navegador não suportar, aparece um aviso pedindo para usar Salvar.
- **Limpar**: apaga tudo o que foi lido até agora **sem confirmação** — use com cuidado, principalmente se
  ainda não exportou.

Nome do arquivo gerado:

- **Bateria**: `bateria_AAAA-MM-DD-hh-mm-ss.csv`
- **Inventário**: `Inventário_<Opção>_<Nota>_AAAA-MM-DD-hh-mm-ss.csv` (a nota some do nome se estiver
  vazia)

---

## 6. Problemas comuns

- **"Câmera indisponível: permissão negada"**: o navegador não recebeu autorização para usar a câmera. Vá
  nas configurações do site (ícone de cadeado/informação na barra de endereço) e permita o acesso à
  câmera, depois recarregue a página.
- **Câmera abre mas não lê nada**: confira a iluminação e a distância — aproxime ou afaste o celular até o
  código ficar nítido dentro da moldura.
- **App muito lento ou não reconhece código de barras (só QR funciona)**: pode estar rodando sem suporte
  nativo do navegador e caiu no modo de reserva, que só lê QR code. Nesse caso, tente em outro navegador
  (Chrome atualizado no Android costuma funcionar melhor) ou verifique a conexão com a internet.
- **Trocar de modo apagou minhas leituras**: é esperado — cada modo é uma coleta separada. Sempre exporte
  (Salvar ou Compartilhar) antes de trocar de modo ou apertar Limpar.
