# CLAUDE.md

Instruções de contexto para o Claude Code trabalhar neste projeto. Leia antes de qualquer alteração.

## O que é

Utilitário Android de uso restrito e específico (equipe treinada, sem necessidade de UI autoexplicativa)
para ler QR code e código de barras direto do navegador do celular — câmera ao vivo ou fotos da galeria
— e exportar os dados em CSV. Roda 100% client-side, sem servidor, sem build.

**Arquivo único**: todo o app (HTML + CSS + JS) vive em `index.html`, autocontido, hospedado como página
estática. Não há bundler, não há `package.json`, não há dependências instaladas — é editar o arquivo
diretamente. O único recurso externo é o fallback `jsQR` via CDN (`cdn.jsdelivr.net`), carregado sob
demanda apenas se `window.BarcodeDetector` não existir no navegador.

Ao propor qualquer mudança, prefira sempre a solução mais simples que resolve o pedido — este é o critério
usado em todo o histórico do projeto, não frameworks, não build step, não dependência nova salvo
necessidade real.

## Documentação do projeto

Três arquivos, três públicos diferentes — não misture o conteúdo entre eles:

- **`CLAUDE.md`** (este arquivo): para quem mexe no código (humano ou agente). Regras de negócio, decisões
  de design e por que elas existem.
- **`README.md`**: visão geral rápida do repositório — o que é, link do site, como fazer deploy.
- **`MANUAL.md`**: manual de uso em português simples, para a equipe operacional (Polo 24) que escaneia as
  urnas/baterias/patrimônios no campo. Sem jargão de código. Ao mudar qualquer regra de negócio que afete o
  que o usuário vê ou precisa fazer (novo campo, nova validação, novo nome de arquivo, etc.), atualize o
  `MANUAL.md` também — ele descreve o comportamento atual, não pode ficar defasado igual ao `CLAUDE.md`
  antigo já ficou uma vez (ver git log: foi apagado e recriado).

## Deploy

Hospedado via **GitHub Pages**, servindo o `index.html` da branch `master` do repositório
`jofilho71/leitor-qrcodes-android`. **Um commit local não atualiza o site sozinho** — é preciso
`git push origin master` explicitamente. Isso já causou confusão real: um commit (`v6`) ficou só local por
um tempo enquanto o link público continuava servindo a versão anterior. Ao terminar uma mudança que o
usuário vai querer ver no ar, **pergunte se deve dar push** (é uma ação visível publicamente, não local) —
não empurre por padrão, mas não deixe de avisar que o commit sozinho não é suficiente. Depois do push, o
GitHub Pages leva 1–2 minutos para reconstruir; oriente a aguardar e recarregar com cache limpo
(Ctrl+Shift+R) se a página parecer não ter mudado.

## Modos de operação

O app tem dois modos, alternados por um segmented control no topo (`data-modo="bateria"` /
`data-modo="inventario"`). Trocar de modo com dados não exportados pede confirmação nativa
(`window.confirm`) e limpa o estado (resultados, pendências, dedupe) — cada modo é uma sessão isolada.

### Modo Bateria (padrão)
Pareia um **QR code** com um **código de barras** (o QR traz os dados da etiqueta da bateria; o código de
barras é o patrimônio da urna — `PAT_UE`). **A ordem é fixa: QR sempre primeiro.** Um código de barras
lido sem QR pendente é **ignorado por completo, em silêncio** (não vira pendência, não gera aviso) — a
etiqueta da bateria tem um código de barras colado logo acima do QR que repete o valor do campo `CDJE`
do próprio QR, e sem essa regra de ordem ele poderia ser confundido com o `PAT_UE` da urna. Depois que o
QR é lido e vira pendente, se o código de barras seguinte tiver o **mesmo valor do `CDJE`** desse QR, é
esse mesmo decoy da etiqueta (não o `PAT_UE`) e também é ignorado em silêncio, sem sair do estado de
espera. Só um código de barras com valor diferente do `CDJE` fecha o par, registra a linha e limpa a
pendência.

**Validação de padrão do `PAT_UE`**: o patrimônio da urna segue o mesmo padrão do modo Inventário —
`PADRAO_PATRIMONIO = /^4551\d{6}$/` (10 dígitos, sempre começando com `4551`), constante compartilhada
entre os dois modos. Um código de barras lido com QR pendente que não bater com esse padrão é **ignorado
em silêncio**, exatamente como o decoy do `CDJE` — o app continua esperando o CB de verdade, sem fechar o
par com lixo. Essa checagem existe porque testes de campo mostraram o mesmo código de barras físico sendo
lido pela câmera com numerações diferentes entre tentativas (dígito trocado, dígito a mais/a menos) —
ruído de decodificação em condições de pouca luz/foco, não um bug de pareamento. A validação de padrão
filtra o ruído mais grosseiro (tamanho errado, prefixo errado); um valor com 10 dígitos começando com
`4551` mas com dígitos internos ainda assim incorretos **não** é pego por essa checagem — não há como
validar o conteúdo exato sem um checksum conhecido do formato de barras usado.

**Não há gravação automática por tempo** de um QR sem par — foi removida de propósito (causava perda
silenciosa do `PAT_UE` quando o usuário demorava mais que um timeout entre QR e CB; ver seção
"Deduplicação"). Um QR pendente só vira registro "sozinho" (`PAT_UE` vazio) quando o usuário interrompe a
câmera (botão "Parar") com esse QR ainda em espera — nesse momento o par incompleto é gravado e um aviso
temporário é exibido informando o fato. Se o usuário quiser completar a leitura, basta ligar a câmera de
novo e ler um novo QR + CB (não há edição retroativa do registro já gravado); se não quiser, basta salvar
o arquivo normalmente.

### Modo Inventário
Mais simples: não pareia nada, mas tem regras próprias de aceitação bem mais restritas que o modo Bateria:

- **Só lê código de barras** — qualquer detecção com `codigo.format === "qr_code"` é ignorada de imediato,
  antes de qualquer outra checagem.
- **Só aceita o padrão de patrimônio da empresa**: `PADRAO_PATRIMONIO = /^4551\d{6}$/` (constante
  compartilhada com o `PAT_UE` do modo Bateria, ver seção "Modo Bateria") — 10 dígitos numéricos, sempre
  começando com `4551`. Qualquer código de barras fora desse padrão (outro formato de etiqueta, código de
  outro sistema, leitura ruidosa) é ignorado em silêncio, sem virar linha de erro. Se a numeração real do
  patrimônio mudar de prefixo/tamanho um dia, é só ajustar essa regex (afeta os dois modos).
- **Nunca duplica um patrimônio na mesma sessão**: `codigosInventarioVistos` (um `Set`) guarda todo código
  já aceito; uma leitura repetida — de qualquer origem (câmera ou galeria), a qualquer momento, não só a
  leitura imediatamente anterior — é descartada em silêncio. Esse Set **não é resetado** junto com
  `ultimoCodigo`/`candidato` em `resetarUltimosCodigos()` (que roda a cada início de câmera/lote de
  galeria) — só é zerado quando `resultados` também é: troca de modo e botão Limpar. Isso também elimina a
  necessidade de confirmação-por-repetição na câmera: como o próprio código já registrado vira duplicata
  descartada, frames repetidos do mesmo patrimônio já são tratados corretamente sem lógica extra.
- **Descarte por diferença pequena do último aceito** (`ultimoPatrimonioAceito` +
  `diferencaPequena(a, b, limite)`, `LIMITE_DIFERENCA_PATRIMONIO = 2`): decode ruidoso do mesmo código
  físico às vezes produz um valor diferente do último aceito mas ainda dentro do padrão de patrimônio
  (poucos dígitos trocados, mesmo comprimento) — foi observado em campo o mesmo código de barras saindo
  com números como `4551265139`/`4551265239`/`4551265269` em leituras sucessivas. Uma leitura com 1 ou 2
  caracteres diferentes do **último patrimônio aceito** (não do histórico inteiro — esse é o papel do
  `codigosInventarioVistos`, que é um dedup exato) é descartada em silêncio, mesma lógica de "ruído,
  ignora e continua" das outras checagens desta seção. `ultimoPatrimonioAceito` só é atualizado quando um
  código é de fato aceito, e só é zerado junto com `codigosInventarioVistos`: troca de modo e botão
  Limpar (não é resetado por reinício de câmera/lote de galeria, mesma vida útil do Set).
  **Risco conhecido e aceito**: se a numeração de patrimônio for sequencial (dois itens genuinamente
  diferentes lidos em sequência, com números vizinhos, ex. `...269` depois `...270`), essa checagem pode
  descartar por engano o segundo item por engano — nesse caso, uma segunda leitura (ela já não vai mais
  ser "a última aceita") é aceita normalmente. Se isso se mostrar um problema recorrente em campo, a
  correção é aumentar `LIMITE_DIFERENCA_PATRIMONIO` pra baixo (ex. 1) ou remover essa checagem — não
  tentar arbitrar automaticamente "qual dos dois é o valor certo" sem mais contexto do formato do CB.

Cada código aceito é gravado junto com uma categoria (select: Runin/Reserva/Movimentação/Conserto) e uma
nota curta opcional, ambos definidos uma vez e reaproveitados em leituras sucessivas até o usuário mudar.

Os patrimônios lidos são listados em tela (`#lista-inventario`), sempre precedidos do número de ordem da
leitura — a numeração é gerada a partir de `resultados.filter(r => r.ok)`, então bate exatamente com a
ordem das linhas do CSV exportado (`gerarCsvInventario` também pula os `!r.ok`; como não há mais
duplicata nem falha registrada nesse modo, na prática todo item em `resultados` é `ok`). A lista é
reconstruída inteira a cada `atualizarContador()` (chamado por `registrar`, troca de modo e botão Limpar)
— não há patch incremental, é sempre um re-render completo a partir de `resultados`. O conteúdo lido é
injetado via `innerHTML` e por isso passa por `escaparHtml()` antes — o valor vem direto do código
escaneado, não é texto confiável, e sem escapar um código malicioso poderia quebrar o layout ou injetar
HTML/script.

## Lógica crítica: deduplicação de leitura contínua (modo Bateria)

A câmera roda em loop (`setInterval`, ~320ms) chamando o detector a cada tick — então o **mesmo código
físico aparece em dezenas de frames** enquanto o usuário mira o celular. Isso já causou um bug sério: uma
dedupe por janela de tempo deixava o mesmo QR "expirar" e voltar a ser tratado como novo se ficasse mais
de ~1s na tela, multiplicando pares fantasmas.

**A regra correta e definitiva** (só existe no modo Bateria — o Inventário usa um mecanismo diferente, ver
seção "Modo Inventário"): comparar sempre com o **último código aceito daquele tipo** (`qr` e `pat` são
rastreados separadamente em `ultimoCodigo`) — sem prazo de validade. Só um valor **diferente** do último
quebra a repetição e conta como leitura nova. Essa memória é resetada em `resetarUltimosCodigos()`: início
de nova sessão de câmera, início de novo lote de galeria, troca de modo, e no botão Limpar. **Nunca
reintroduza dedupe por tempo/janela** — foi tentado e é a causa raiz de dados incorretos.

**Esse dedup só se aplica a leituras de origem `"câmera"`.** Na galeria, cada foto é uma leitura
deliberada e distinta do usuário, não uma sequência de frames do mesmo objeto físico — se duas fotos
diferentes do lote produzirem o mesmo valor (etiqueta com erro de impressão, código duplicado por engano),
elas precisam ser tratadas como leituras independentes. Aplicar o dedup por igual às duas origens já foi
a causa de um bug real: um código de barras repetido numa foto seguinte do mesmo lote era descartado, e o
QR pendente daquela foto acabava sendo fechado com o código de barras de uma **terceira** foto,
atribuindo um `PAT_UE` errado sem qualquer aviso. Ao mexer em `processarCodigoDetectado`, mantenha o guard
`origem === "câmera"` nesse ponto de dedup do modo Bateria.

O Inventário **não** usa `ultimoCodigo`/`candidato` — ele dedupa contra o histórico completo da sessão
(`codigosInventarioVistos`), então não sofre do mesmo problema entre fotos da galeria; ver seção "Modo
Inventário".

## Formatos de CSV

Os dois modos exportam formatos **diferentes e específicos** — não unifique:

- **Bateria** (separador `,`, BOM UTF-8): `PAT_UE,CDJE,origem,status,<campos dinâmicos do QR>,conteudo_bruto`.
  `PAT_UE` é sempre a primeira coluna (é o campo-alvo do processo). `CDJE` vem sempre em segundo. Os
  demais campos do QR (`FORN`, `FABR`, `MDBT`, `LTFB`, `DTFB` etc.) são descobertos dinamicamente a partir
  do conteúdo real do QR — não hardcode uma lista fixa. Linhas de falha (nenhum código encontrado numa
  foto da galeria) também entram no CSV, com `status` explicando o motivo.
- **Inventário** (separador `;`, BOM UTF-8): exatamente `Patrimônio;Opção;Nota`, sem colunas extras.
  Falhas **não** geram linha aqui (só contam no rodapé e ficam fora da lista em tela).
- Removido por pedido explícito: coluna `arquivo`/nome de arquivo — não reintroduzir sem pedido novo.
- O valor de patrimônio/código de barras é sempre o `rawValue` bruto do detector, **nunca** com prefixo,
  sufixo ou qualquer transformação.
- `escaparCsv()` usa regex pré-compiladas por delimitador (`RE_CSV_ESPECIAL`) — os dois delimitadores
  usados no app são `,` e `;`; se um dia precisar de um terceiro, adicione a entrada no mapa em vez de
  voltar a montar `RegExp` dinamicamente por célula.

### Nome do arquivo exportado

`gerarNomeArquivo()` tem uma regra por modo:

- **Bateria**: `bateria_<timestamp>.csv` (comportamento original, inalterado).
- **Inventário**: `Inventário_<Opção>_<Nota>_<timestamp>.csv`, onde `<Opção>` é o valor atual do select
  (Runin/Reserva/Movimentação/Conserto) e `<Nota>` é o texto livre atual — ambos lidos no momento do
  clique em Salvar/Compartilhar, sanitizados por `sanitizarNomeArquivo()` (troca caracteres inválidos em
  nome de arquivo por `-`). Se a nota estiver vazia, esse segmento é omitido (não gera `__` duplo no
  nome). Isso significa que o nome do arquivo reflete a última opção/nota selecionadas na tela, não
  necessariamente as mesmas de todos os itens escaneados — o app já assume que opção/nota são definidas
  uma vez por sessão de coleta (ver "Modo Inventário").

## Parsing do conteúdo do QR

O QR das etiquetas segue o padrão `CHAVE:VALOR CHAVE:VALOR ...` (ex.: `CDJE:92005320367483
FORN:POSITIVO...`). `parsearCampos()` faz esse split por espaço, tratando um token como nova chave
quando tem até 6 caracteres maiúsculos/dígitos seguidos de `:`. Só é considerado um QR estruturado se
resultar em mais de um campo — caso contrário o conteúdo bruto é tratado como texto solto.

## Detecção de código

- **Preferência**: `BarcodeDetector` nativo do navegador (Shape Detection API), com lista de formatos
  (`FORMATOS_DESEJADOS`) que inclui QR e os principais códigos de barras lineares. A lista efetiva é
  intersectada com `BarcodeDetector.getSupportedFormats()` quando disponível.
- **Fallback**: `jsQR` via CDN, carregado só se `BarcodeDetector` não existir. **Limitação importante**:
  jsQR só decodifica QR code — código de barras linear (`PAT_UE`) só funciona com o detector nativo. Isso
  é esperado e deve ser documentado para o usuário se o fallback disparar, não "corrigido" adicionando
  outra lib sem necessidade real.
- `garantirJsQR()` **não** guarda em cache uma promise rejeitada: se o CDN estiver fora do ar no momento
  do primeiro uso, `jsQRCarregado` é resetado pra `null` no catch, permitindo nova tentativa na próxima
  chamada. Sem isso, uma queda de rede pontual travava o fallback pelo resto da sessão mesmo com a conexão
  de volta.
- A decodificação via jsQR (desenhar no canvas já preenchido + `getImageData` + `window.jsQR`) é
  centralizada em `decodificarCanvasComJsQR(w, h)`, chamada tanto pela galeria (`detectarCodigosEmImagem`,
  em até 3 escalas) quanto pelo tick da câmera (uma escala só, direto do frame de vídeo). Não duplique essa
  lógica de novo nos dois lugares — qualquer ajuste no fallback (nova escala, tratamento de borda) deve
  entrar só nessa função.
- `BarcodeDetector` depende de Google Play Services no Android — funciona no Chrome real de Android, mas
  **não** em Chromium headless genérico (por isso os testes sempre fazem stub, ver seção Testes).
- **Descarte de leitura cortada na borda** (`codigoTocaBorda()`): toda detecção do detector nativo (câmera
  e galeria) é checada contra o `boundingBox` que a própria API devolve — se a caixa encostar na borda do
  frame (margem de `MARGEM_BORDA_FRACAO = 0.02`, 2% da largura/altura), a leitura é descartada em silêncio,
  igual às outras checagens de ruído (padrão de patrimônio, decoy do CDJE). Motivo: um código de barras
  parcialmente fora do quadro pode, em formatos lineares mais fracos (ex.: ITF, sem checksum obrigatório),
  ainda assim decodificar — só que como um valor menor/diferente do código inteiro, não como falha. Isso foi
  identificado em testes de campo como causa de leituras do mesmo código físico saindo com numerações
  diferentes. `boundingBox` só existe no resultado do detector nativo — jsQR (fallback, só QR) não fornece
  essa informação nesse formato e nem precisa, já que QR tem correção de erro própria; por isso
  `codigoTocaBorda()` retorna `false` (não bloqueia) quando `boundingBox` está ausente — **fail-open**,
  pra não quebrar o fallback nem os stubs de teste que não simulam essa propriedade.

## Câmera: falha ao iniciar

`iniciarCamera()` trata dois pontos de falha separadamente: `getUserMedia()` rejeitando (permissão negada
ou sem câmera) e `video.play()` rejeitando (ex.: restrição de autoplay em algum WebView, mesmo com
`muted`+`playsinline`). Os dois abortam a ativação e mostram erro em `#erro-camera` — **não** deixe o
`play()` falhar em silêncio (`.catch(() => {})`): isso já aconteceu e deixava a UI da câmera "ativa" com o
vídeo congelado, o loop de detecção rodando sem nunca detectar nada (`video.readyState` preso `< 2`) e
nenhum aviso pro usuário.

## Interface / layout

- Utilitário de espaço mínimo: sem textos longos, sem explicações no app — quem usa já foi treinado.
  Botões de ação são só ícone (SVG inline, sem texto alternativo).
- Rodapé (`#rodape`) fica **sempre visível**: contador em linha única (`Pares coletados: N` no modo
  Bateria, `Itens coletados: N` no Inventário — conta só aprovados, sem total/falhas na tela) + botões
  Salvar/Compartilhar/Limpar. É o último elemento de uma coluna flexível (`body` vira `display:flex;
  flex-direction:column` quando a câmera está ativa via classe `.camera-ativa`), então o preview da
  câmera (`flex:1`) cresce pra ocupar só o espaço que sobra acima do rodapé — nunca sobrepõe, nunca some.
- `#lista-inventario` (só modo Inventário) tem `max-height` com scroll próprio (`overflow-y: auto`) — ela
  nunca deve crescer livremente, principalmente com a câmera ativa, onde o espaço vertical já é disputado
  entre header, controles e preview.
- Ao ativar a câmera, o botão de câmera vira "Parar" (ícone muda de câmera pra quadrado sólido) — um
  botão só, sem par Iniciar/Parar separado.
- **Status colorido** (`#pendencia` + borda do `#moldura` na câmera, ambos sempre com a mesma cor):
  branco = aguardando leitura (Bateria: "Esperando leitura de QR Code"; Inventário: "Esperando leitura");
  amarelo = só no modo Bateria, QR pendente aguardando o código de barras ("Esperando leitura de CB");
  verde = leitura concluída ("Par incluído" / "Par incluso (sozinho)" no timeout / "Item incluído" no
  Inventário) — fica **1s** e volta pro branco (ou amarelo, se um novo QR já tiver sido lido nesse
  intervalo). É reflexo direto do estado interno de pareamento, não um elemento decorativo independente.

## Compartilhamento

Usa a Web Share API (`navigator.share` com `files: [File]`) — o CSV vira um arquivo de verdade, não texto
solto, então some no destino como anexo (WhatsApp, Drive, e-mail etc.). Tem checagem de suporte
(`navigator.canShare`) com aviso inline se o navegador não aceitar; cancelamento do usuário (`AbortError`)
não deve gerar mensagem de erro.

## Testes

Não há dispositivo Android real disponível neste fluxo de desenvolvimento, e o Chromium usado em CI/testes
não tem `BarcodeDetector` funcional nem acesso à internet (CDN do jsQR fica inacessível). **Todo teste
precisa stubar os dois**:

```js
// stub do detector nativo — controla exatamente o que cada chamada de detect() retorna
window.BarcodeDetector = class {
  constructor(o) {}
  static getSupportedFormats() { return Promise.resolve(['qr_code','code_128', ...]); }
  async detect(source) { return [{ rawValue: '...', format: 'qr_code' }]; }
};

// stub da câmera — getUserMedia real não funciona headless
navigator.mediaDevices.getUserMedia = async () => {
  const c = document.createElement('canvas');
  c.width = 320; c.height = 240;
  c.getContext('2d').fillRect(0,0,320,240);
  return c.captureStream(15);
};
```

Ferramenta usada até aqui: Playwright (Python), lançando Chromium com
`args=["--use-fake-ui-for-media-stream"]` e `permissions=["camera"]` no contexto. Padrão de teste: montar
uma "fila" de resultados que o detector consome a cada chamada (permite simular sequências específicas —
QR repetido N vezes, código de barras chegando antes/depois de outra foto no mesmo lote, etc.).

Sempre validar, no mínimo, antes de considerar uma mudança pronta:
1. Modo Bateria: pareamento QR→CB (única ordem válida), os dois códigos na mesma foto (a leitura de
   galeria ordena QR antes de CB dentro da mesma foto porque a ordem de retorno do detector não é
   garantida), interrupção da câmera com QR pendente gravando leitura solo (`PAT_UE` vazio) e mostrando o
   aviso — e confirmando que **não** existe gravação automática por tempo (esperar bastante com um QR
   pendente e a câmera ligada não deve gravar nada sozinho).
2. Modo Bateria — regra de ordem e decoy: código de barras lido **sem** QR pendente é ignorado por
   completo (nenhum estado muda, nada é gravado); código de barras lido **com** QR pendente e valor igual
   ao campo `CDJE` desse QR também é ignorado (continua aguardando CB de verdade); código de barras lido
   **com** QR pendente e valor fora do padrão `PADRAO_PATRIMONIO` (ex.: 11 dígitos, ou não começando com
   `4551`) também é ignorado, tanto vindo da câmera quanto da galeria.
2b. Descarte por borda (`codigoTocaBorda`): uma detecção com `boundingBox` encostando na margem do frame
   (câmera ou galeria) é ignorada mesmo que o valor decodificado bata com o padrão de patrimônio; uma
   detecção sem `boundingBox` (stub de teste, ou navegador que não populou essa propriedade) não é
   bloqueada por essa checagem (fail-open).
3. Deduplicação por tipo (câmera): mesmo código repetido em sequência na câmera conta 1 vez; código
   diferente interrompe a repetição e volta a contar normalmente depois.
4. Deduplicação não se aplica entre fotos da galeria: duas fotos distintas de um lote com o mesmo valor de
   código de barras (simulando etiqueta duplicada/erro de impressão) devem gerar dois pares distintos, não
   um descartado silenciosamente.
5. Estado visual (`#pendencia` + `#moldura`): branco no início/aguardando QR, amarelo com QR pendente,
   verde por 1s ao fechar um par (completo ou "sozinho" por interrupção manual) ou ao gravar um item no
   Inventário, com retorno ao estado correto depois do 1s.
6. Modo Inventário: com e sem nota, opção correta no CSV, e a lista em tela (`#lista-inventario`)
   numerada na mesma ordem das linhas do CSV.
7. Modo Inventário — filtros de aceitação: um `qr_code` é sempre ignorado, mesmo com conteúdo que pareça
   um patrimônio válido; um código de barras fora do padrão `4551` + 6 dígitos é ignorado; e um código já
   lido nesta sessão é descartado mesmo vindo de origem diferente (câmera depois de galeria, ou vice-versa)
   ou bem depois da primeira leitura (não é um dedup de curto prazo); um código com 1 ou 2 dígitos
   diferentes do **último** aceito é descartado (decode ruidoso do mesmo físico), mas um código bem
   diferente do último (mesmo que perto de um item aceito bem antes na sessão) é aceito normalmente.
8. Nome do arquivo exportado no Inventário: contém a opção selecionada e a nota atual (sanitizadas), na
   ordem `Inventário_<Opção>_<Nota>_<timestamp>.csv`, com o segmento da nota omitido quando ela está vazia.
9. Conteúdo exato do CSV baixado (`page.expect_download()`) — cabeçalho, separador, ordem das colunas.
10. Falha de câmera: `getUserMedia()` rejeitando e `video.play()` rejeitando devem levar ao mesmo resultado
    (erro visível, sem UI de câmera "ativa" fantasma, sem stream ficando aberto).
11. Regressão dos dois modos sempre que mexer em lógica compartilhada (parsing, detecção, dedupe, CSV).

## Convenções

- Nomes de variáveis, funções e comentários em **português**, consistente com o resto do código.
- Sem framework, sem TypeScript, sem transpilação — JS puro compatível com Chrome Android atual.
- Preferir editar em blocos pequenos e testar cada mudança isoladamente antes de composição — este
  arquivo cresceu de forma incremental, sempre com teste automatizado confirmando antes da entrega.
