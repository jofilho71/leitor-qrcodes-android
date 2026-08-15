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
Pareia um **QR code** com um **código de barras** lido em qualquer ordem (o QR traz os dados da etiqueta
da bateria; o código de barras é o patrimônio da urna — `PAT_UE`). A lógica mantém um "QR pendente" e um
"código de barras pendente"; assim que os dois existem, fecha o par, registra uma linha e limpa a
pendência. Se só um dos dois aparecer, mostra um aviso curto ("QR lido — falta o código de barras") e
**depois de 20s sem completar** (`JANELA_PAREAMENTO_MS`), grava o que tiver sozinho em vez de descartar a
leitura.

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

Para acelerar o timeout de pareamento (20s) em teste, o código lê
`window.__JANELA_PAREAMENTO_MS_OVERRIDE` antes de definir a constante — sobrescreva via
`page.add_init_script()` para não esperar 20s de verdade.

Sempre validar, no mínimo, antes de considerar uma mudança pronta:
1. Modo Bateria: pareamento nas duas ordens (QR→CB e CB→QR), os dois códigos na mesma foto, timeout
   gravando leitura solo.
2. Deduplicação: mesmo código repetido em sequência conta 1 vez; código diferente interrompe a repetição
   e volta a contar normalmente depois.
3. Modo Inventário: com e sem nota, opção correta no CSV.
4. Conteúdo exato do CSV baixado (`page.expect_download()`) — cabeçalho, separador, ordem das colunas.
5. Regressão dos dois modos sempre que mexer em lógica compartilhada (parsing, detecção, dedupe).

## Convenções

- Nomes de variáveis, funções e comentários em **português**, consistente com o resto do código.
- Sem framework, sem TypeScript, sem transpilação — JS puro compatível com Chrome Android atual.
- Preferir editar em blocos pequenos e testar cada mudança isoladamente antes de composição — este
  arquivo cresceu de forma incremental, sempre com teste automatizado confirmando antes da entrega.
