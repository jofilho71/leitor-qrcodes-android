# CLAUDE.md

Instruções de contexto para o Claude Code trabalhar neste projeto. Leia antes de qualquer alteração.

## O que é

Utilitário Android de uso restrito e específico (equipe treinada, sem necessidade de UI autoexplicativa)
para ler QR code e código de barras direto do navegador do celular — câmera ao vivo ou fotos da galeria
— e exportar os dados em CSV. Roda 100% client-side, sem servidor, sem build.

**Arquivo único**: todo o app (HTML + CSS + JS) vive em um `.html` autocontido, hospedado como página
estática (GitHub Pages). Não há bundler, não há `package.json`, não há dependências instaladas — é editar
o arquivo diretamente. O único recurso externo é o fallback `jsQR` via CDN (`cdn.jsdelivr.net`), carregado
sob demanda apenas se `window.BarcodeDetector` não existir no navegador.

Ao propor qualquer mudança, prefira sempre a solução mais simples que resolve o pedido — este é o critério
usado em todo o histórico do projeto, não frameworks, não build step, não dependência nova salvo
necessidade real.

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
pendência. Se nenhum código de barras válido aparecer, **depois de 20s** (`JANELA_PAREAMENTO_MS`), grava
o QR sozinho em vez de descartar a leitura. Usuários são treinados nessa ordem; o app ainda assim mostra
avisos curtos (ver "Interface / layout") reforçando o estado esperado. **Não há gravação automática por
tempo de um QR sem par** — foi removida de propósito (ver histórico: causava perda silenciosa do
`PAT_UE` quando o usuário demorava mais que o timeout entre QR e CB). Um QR pendente só vira registro
"sozinho" (`PAT_UE` vazio) quando o usuário interrompe a câmera (botão "Parar") com esse QR ainda em
espera — nesse momento o par incompleto é gravado e um aviso temporário é exibido informando o fato. Se
o usuário quiser completar a leitura, basta ligar a câmera de novo e ler um novo QR + CB (não há edição
retroativa do registro já gravado); se não quiser, basta salvar o arquivo normalmente.

### Modo Inventário
Mais simples: não pareia nada. Cada código lido (de qualquer tipo) é gravado direto, junto com uma
categoria (select: Runin/Reserva/Movimentação/Conserto) e uma nota curta opcional, ambos definidos uma vez
e reaproveitados em leituras sucessivas até o usuário mudar.

## Lógica crítica: deduplicação de leitura contínua

A câmera roda em loop (`setInterval`, ~320ms) chamando o detector a cada tick — então o **mesmo código
físico aparece em dezenas de frames** enquanto o usuário mira o celular. Isso já causou um bug sério
(ver histórico): uma dedupe por janela de tempo deixava o mesmo QR "expirar" e voltar a ser tratado como
novo se ficasse mais de ~1s na tela, multiplicando pares fantasmas.

**A regra correta e definitiva**: comparar sempre com o **último código aceito daquele tipo** (`qr` e `pat`
são rastreados separadamente no modo Bateria; um único "genérico" no modo Inventário) — sem prazo de
validade. Só um valor **diferente** do último quebra a repetição e conta como leitura nova. Essa memória
é resetada em: início de nova sessão de câmera, início de novo lote de galeria, troca de modo, e no
botão Limpar. **Nunca reintroduza dedupe por tempo/janela** — foi tentado e é a causa raiz de dados
incorretos.

## Formatos de CSV

Os dois modos exportam formatos **diferentes e específicos** — não unifique:

- **Bateria** (separador `,`, BOM UTF-8): `PAT_UE,CDJE,origem,status,<campos dinâmicos do QR>,conteudo_bruto`.
  `PAT_UE` é sempre a primeira coluna (é o campo-alvo do processo). `CDJE` vem sempre em segundo. Os
  demais campos do QR (`FORN`, `FABR`, `MDBT`, `LTFB`, `DTFB` etc.) são descobertos dinamicamente a partir
  do conteúdo real do QR — não hardcode uma lista fixa. Linhas de falha (nenhum código encontrado numa
  foto da galeria) também entram no CSV, com `status` explicando o motivo.
- **Inventário** (separador `;`, BOM UTF-8): exatamente `Patrimônio;Opção;Nota`, sem colunas extras.
  Falhas **não** geram linha aqui (só contam no rodapé).
- Removido por pedido explícito: coluna `arquivo`/nome de arquivo — não reintroduzir sem pedido novo.
- O valor de patrimônio/código de barras é sempre o `rawValue` bruto do detector, **nunca** com prefixo,
  sufixo ou qualquer transformação.

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
- `BarcodeDetector` depende de Google Play Services no Android — funciona no Chrome real de Android, mas
  **não** em Chromium headless genérico (por isso os testes sempre fazem stub, ver seção Testes).

## Interface / layout

- Utilitário de espaço mínimo: sem textos longos, sem explicações no app — quem usa já foi treinado.
  Botões de ação são só ícone (SVG inline, sem texto alternativo).
- Rodapé (`#rodape`) fica **sempre visível**: contador em linha única (`Pares coletados: N` no modo
  Bateria, `Itens coletados: N` no Inventário — conta só aprovados, sem total/falhas na tela) + botões
  Salvar/Compartilhar/Limpar. É o último elemento de uma coluna flexível (`body` vira `display:flex;
  flex-direction:column` quando a câmera está ativa via classe `.camera-ativa`), então o preview da
  câmera (`flex:1`) cresce pra ocupar só o espaço que sobra acima do rodapé — nunca sobrepõe, nunca some.
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
QR repetido N vezes, código de barras chegando antes/depois, timeout de pareamento etc.).

Sempre validar, no mínimo, antes de considerar uma mudança pronta:
1. Modo Bateria: pareamento QR→CB (única ordem válida), os dois códigos na mesma foto (a leitura de
   galeria ordena QR antes de CB dentro da mesma foto porque a ordem de retorno do detector não é
   garantida), interrupção da câmera com QR pendente gravando leitura solo (`PAT_UE` vazio) e mostrando o
   aviso — e confirmando que **não** existe gravação automática por tempo (esperar bastante com um QR
   pendente e a câmera ligada não deve gravar nada sozinho).
2. Modo Bateria — regra de ordem e decoy: código de barras lido **sem** QR pendente é ignorado por
   completo (nenhum estado muda, nada é gravado); código de barras lido **com** QR pendente e valor igual
   ao campo `CDJE` desse QR também é ignorado (continua aguardando CB de verdade).
3. Estado visual (`#pendencia` + `#moldura`): branco no início/aguardando QR, amarelo com QR pendente,
   verde por 1s ao fechar um par (completo ou "sozinho" por timeout) ou ao gravar um item no Inventário,
   com retorno ao estado correto depois do 1s.
4. Deduplicação: mesmo código repetido em sequência conta 1 vez; código diferente interrompe a repetição
   e volta a contar normalmente depois.
5. Modo Inventário: com e sem nota, opção correta no CSV.
6. Conteúdo exato do CSV baixado (`page.expect_download()`) — cabeçalho, separador, ordem das colunas.
7. Regressão dos dois modos sempre que mexer em lógica compartilhada (parsing, detecção, dedupe).

## Convenções

- Nomes de variáveis, funções e comentários em **português**, consistente com o resto do código.
- Sem framework, sem TypeScript, sem transpilação — JS puro compatível com Chrome Android atual.
- Preferir editar em blocos pequenos e testar cada mudança isoladamente antes de composição — este
  arquivo cresceu de forma incremental, sempre com teste automatizado confirmando antes da entrega.
