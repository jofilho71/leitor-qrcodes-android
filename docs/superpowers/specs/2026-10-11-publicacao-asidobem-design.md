# Publicação de listas para o ASIdoBem — design (repositório GitHub público)

Data: 2026-10-11 (3ª revisão: Worker+R2 → Firestore → **repositório público no GitHub**, com sessão guiada
por código). Contrato de conteúdo: `IMPORTACAO_WEB.md` (formato 1). Neste desenho o **ASIdoBem não muda**:
ele lê `indice.csv` e as listas por HTTPS/GET, sem token. Os `IMPORTACAO*.md` não são alterados.

## 1. Objetivo

O leitor é o "site" do contrato. Um técnico abre o link, informa o código de 5 dígitos do ASIdoBem, lê os QRs
das urnas, escolhe a operação de cada uma e **publica** a lista. A lista vai para um repositório público; o
ASIdoBem a coleta de lá.

Entregas:

1. Simplificar o app: só Inventário, só QR, única recusa por repetição (além do padrão de patrimônio).
2. Operação do contrato no lugar das categorias antigas.
3. Fluxo guiado: **Iniciar → código → configuração → leitura → publicar → nova configuração**.
4. Publicar a lista (formato 1) no repositório; o índice é gerado por GitHub Actions.
5. Som de sucesso e de erro, além da vibração já existente.
6. Configuração do aparelho por link com token.

Fora de escopo: fila offline automática, alterar o ASIdoBem, alterar os `IMPORTACAO*.md`.

## 2. Arquitetura

```
Celular (index.html, GitHub Pages) ──PUT contents API (token fine-grained)──► repo público asidobem-listas
                                                                               listas/<id>.csv
                                      GitHub Actions (push em listas/**) ──►  indice.csv  (id;codigo;gerado_em;titulo;linhas;sha256;arquivo)
ASIdoBem ──GET https://raw.githubusercontent.com/jofilho71/asidobem-listas/main/indice.csv e listas/<id>.csv
```

- Repositório **novo e público**: `jofilho71/asidobem-listas` (branch `main`). Separado do app, de propósito:
  o token do celular não pode alterar o código do próprio app.
- `index.html` segue único, sem build, sem SDK: `fetch` direto na API do GitHub (suporta CORS).
- ASIdoBem: *Site…* → `https://raw.githubusercontent.com/jofilho71/asidobem-listas/main/indice.csv`, token em
  branco. `raw.githubusercontent.com` responde 200 sem redirecionamento, como o contrato exige. O CDN guarda
  cache de ~5 min; a lista chega ao ASIdoBem alguns minutos depois de publicada (aceito).

## 3. Repositório e Actions

- `listas/<id>.csv`: um arquivo por lista, formato 1, nunca editado (convenção; o app só cria).
- `.github/workflows/indice.yml`: dispara em push que toque `listas/**`; `concurrency` em um único grupo
  (um por vez); roda `scripts/gerar_indice.py` (Python da imagem do runner, sem dependências); se `indice.csv`
  mudou, commita como `github-actions[bot]` com `[skip ci]` (e o filtro de path evita laço).
- `scripts/gerar_indice.py`, para cada `listas/*.csv`: lê a linha `#ASIDOBEM;…`; **valida** formato 1,
  `codigo` de 5 dígitos, `id` válido e igual ao nome do arquivo, cabeçalho exato, 3 colunas por linha,
  ≤ 20.000 linhas, ≤ 5 MB; arquivo inválido é **deixado fora do índice** e registrado no log do Actions.
  Calcula SHA-256 dos bytes exatos, conta as linhas de dados, e escreve `indice.csv` com o cabeçalho
  `id;codigo;gerado_em;titulo;linhas;sha256;arquivo` ordenado por `gerado_em` desc (desempate por `id`),
  `arquivo` = `listas/<id>.csv`. Não-determinismo zero: mesma entrada, mesmo índice.

## 4. Token e configuração do aparelho

- **Token**: *fine-grained personal access token* do GitHub, restrito ao repositório `asidobem-listas`,
  permissão *Contents: Read and write*, validade máxima (1 ano). **Um token por aparelho/técnico**,
  revogáveis individualmente. O token **nunca** está no `index.html` nem em nenhum repositório.
- **Link de configuração**: `https://jofilho71.github.io/leitor-qrcodes-android/#cfg=<token>`. Ao abrir, o
  app valida o formato, guarda o token em `localStorage`, **remove o fragmento** com `history.replaceState`
  e mostra "Aparelho configurado". O fragmento não é enviado a servidor.
- **Ajustes** (alternativa discreta): campo para colar o token e botão para apagá-lo.
- Sem token no aparelho, **Iniciar** avisa e não prossegue (ver §5.1).

## 5. Fluxo e telas

### 5.1 Estados
```
INICIO ──Iniciar──► CODIGO ──ok──► CONFIG ──ok──► LEITURA ──Publicar ok──► INICIO (configuração nova)
                                                     │  ├─ Excluir último
                                                     │  └─ Cancelar leitura (confirmação) ──► INICIO
```

- **INICIO**: botão Iniciar (e acesso aos ajustes). Se existe uma sessão salva (§5.6), pergunta
  "Retomar leitura de N itens (código X)?" com Retomar / Descartar.
- **Ao tocar Iniciar**: verifica o token (`GET /repos/jofilho71/asidobem-listas` com o token). 401/403/404 →
  "Token ausente ou vencido" e não segue. Falha de rede → segue com aviso "sem conexão: confira antes de
  publicar" (não impede a coleta em campo).
- **CODIGO**: campo numérico de 5 dígitos (10000–99999, sem zeros à esquerda). Obrigatório para seguir.
- **CONFIG**: responsável e local (`POLO` ou `Z<n>`, opcionais; **lembrados** no aparelho), operação
  inicial (+ zona ou status, conforme §5.4) e nota inicial. Botão que leva à leitura com o botão da câmera
  disponível (a câmera só liga por toque do usuário, o que também libera o áudio).
- **LEITURA**: o **código aparece grande** no topo (o técnico confere com o que o ASIdoBem mostrou), seguido
  de câmera/galeria, operação/parâmetro/nota (**editáveis durante a leitura**: uma lista pode misturar
  operações), a lista dos itens lidos e o rodapé.

### 5.2 Rodapé na leitura
Contador `Itens coletados: N`, e botões (ícone, sem texto): **Excluir último**, **Cancelar leitura**,
**Publicar**; Salvar CSV e Compartilhar seguem como backup local.

- **Excluir último**: remove o item mais recente da lista **e do `codigosInventarioVistos`**, para poder ser
  lido de novo. Pode ser acionado repetidamente (remove um por vez, do mais novo ao mais antigo). Sem
  confirmação (ação barata e reversível relendo). Sem itens: desabilitado.
- **Cancelar leitura**: pede confirmação nativa (`window.confirm`) citando N itens; confirmado, para a
  câmera, descarta a sessão (inclui a salva) e volta a INICIO. Sem itens: volta direto.
- **Publicar**: com 0 itens, desabilitado. Ver §5.5.

### 5.3 Aceitação de uma detecção
1. `format !== "qr_code"` → descarta, silêncio.
2. Sem `IDEQ` em `parsearCampos()` → descarta, silêncio.
3. `"45"+IDEQ` fora de `PADRAO_PATRIMONIO` → **erro com som**.
4. `IDEQ` já em `codigosInventarioVistos` → **erro com som**.
5. Senão aceita: grava o `IDEQ` puro (8 dígitos) com a operação/nota atuais; vibração + som de sucesso.

`codigosInventarioVistos` vale para a sessão e só zera ao publicar, cancelar ou descartar. A unicidade é
**dentro da lista**; a mesma urna em listas de técnicos diferentes quem trata é a conferência do ASIdoBem.

### 5.4 Operação
Select: Recolher, Transferir, Devolver TRE, Descartar, Status, Cadastrar (`RECOLHER`, `TRANSFERIR:Z<n>`,
`DEVOLVER_TRE`, `DESCARTAR`, `STATUS:<status>`, `CADASTRAR`).

- Transferir mostra campo de zona: aceita `Z59`/`59`/`Z059`, grava `Z<n sem zeros>`; `POLO` também. Zona
  inválida marca o campo e **impede a leitura de ser aceita** (som de erro).
- Status mostra select: Pronta, Defeituosa, Danificada, Sucateada, Nao Certificada, Sem Bateria,
  Indisponivel.
- A nota vira `descricao`: até 200 caracteres; `;` e quebras de linha viram espaço.

### 5.5 Publicar
O código e a identificação já existem desde o início da sessão: **não há mais diálogo**.

- `id` = `aaaa-mm-dd-<local em minúsculas ou sem-local>-<seq 2 dígitos>`; `titulo` automático
  ("Inventário dd/mm").
- CSV de formato 1: `#ASIDOBEM;formato=1;codigo=<código>;id=<id>;titulo=…;local=…;responsavel=…;gerado_em=…`,
  cabeçalho `patrimonio;operacao;descricao`, UTF-8, `;`, patrimônio como texto.
- `PUT https://api.github.com/repos/jofilho71/asidobem-listas/contents/listas/<id>.csv`
  (`Authorization: Bearer <token>`, corpo `{message, content: <base64 UTF-8>}`, **sem `sha`**, logo falha
  se o arquivo existir). `201` = publicada. `422` (já existe) → incrementa `seq` e repete. Até 99.
- Sucesso: "Publicada (N linhas). O ASIdoBem a verá em alguns minutos", limpa a sessão e **volta a INICIO**
  para uma nova configuração. Falha (rede, 401/403, 5xx): mostra o motivo, **mantém a lista na tela** para
  tentar de novo, e o CSV continua salvável. Lista com mais de 15.000 linhas: recusa local e orienta a
  publicar parte e continuar.

### 5.6 Sessão salva (retomada)
A cada item aceito ou excluído, a sessão (código, configuração, itens) é gravada em `localStorage`. Se o
Chrome do Android descartar a aba (ligação, outro app, falta de memória), nada se perde: ao reabrir, INICIO
oferece **Retomar** ou **Descartar**. Publicar com sucesso, Cancelar e Descartar apagam a sessão salva.
Sem `localStorage`, tudo funciona, só sem retomada.

### 5.7 Som
Web Audio API, tons gerados no código, sem arquivos; `AudioContext` criado/retomado no toque do botão de
câmera/galeria.

- Sucesso: dois tons ascendentes curtos, junto da vibração `[40,40,60]` existente.
- Erro: tom grave único mais longo, junto de vibração `[120]`.
- Erro tocado **uma vez por valor** enquanto o mesmo valor continuar sendo lido na câmera (lê a cada
  ~320 ms). Na galeria, cada foto é independente.
- Sem Web Audio ou áudio bloqueado: falha em silêncio.

### 5.8 Remoções
Modo Bateria inteiro (segmented control, pareamento, decoy `CDJE`, `ultimoCodigo`/`candidato`, `pendente`,
confirmação de troca de modo, `gerarCsvBateria`, CSV `bateria_*`); leitura de código de barras;
`diferencaPequena`, `ultimoPatrimonioAceito`, `LIMITE_DIFERENCA_PATRIMONIO`; `codigoTocaBorda` e
`MARGEM_BORDA_FRACAO`. `FORMATOS_DESEJADOS` = `["qr_code"]`. A confirmação de "dados não exportados" some
junto com os modos; sua função é substituída pelo Cancelar e pela retomada da sessão.

## 6. Testes

Playwright (Python) com stubs de `BarcodeDetector` e câmera, como hoje; a API do GitHub é simulada com
`page.route` (201, 422, 401, rede).

- Fluxo: Iniciar → código inválido (4 dígitos, zeros) bloqueia → válido avança → configuração → câmera.
- Aceitação (§5.3): barcode ignorado mesmo com valor válido; sem IDEQ silêncio; fora do padrão e repetido →
  som de erro 1× por valor; aceito → som de sucesso e vibração; IDEQ puro gravado.
- **Excluir último** remove da lista e do Set (o mesmo valor é aceito de novo); repetido remove vários.
- **Cancelar**: confirmação, descarta sessão e câmera; volta a INICIO.
- **Publicar**: CSV exato enviado (identificação, cabeçalho, ordem, `;`, base64 UTF-8 ↔ bytes); 201 limpa a
  sessão e volta a INICIO; 422 incrementa `seq`; 401/rede mantêm a lista; sem token não inicia.
- **Retomada**: recarregar a página no meio da leitura oferece Retomar com os mesmos itens e código.
- **Link de configuração**: token guardado, fragmento removido da URL.
- **Actions**: `gerar_indice.py` testado localmente com listas válidas e inválidas (formato, código, id≠nome,
  cabeçalho, colunas); ordem e SHA-256 conferidos contra `sha256sum`.
- Regressão: falha de câmera (getUserMedia e play), galeria, operações/parâmetros no CSV.

## 7. Documentação

Atualizar `CLAUDE.md` (Bateria e similaridade saem; fluxo guiado; operações; Publicar; repositório de
listas; som; sessão salva), `MANUAL.md` (o passo a passo do técnico, incluindo o link de configuração e o
significado dos sons) e `README.md` (repositório de listas, Actions, geração/renovação de tokens, endereço
para o ASIdoBem). Deploy do app continua exigindo `git push origin master` com confirmação.

## 8. Riscos e decisões aceitas

- Quem tiver o token pode alterar/apagar listas **daquele repositório** (histórico do git permite
  restaurar; token revogável por aparelho). Os dados já são públicos.
- O código digitado errado não é detectável pelo app: o ASIdoBem ignora em silêncio listas de outros
  códigos. Mitigação: o código fica grande na tela e na mensagem de sucesso.
- Atraso de alguns minutos até a lista aparecer no ASIdoBem (Actions + cache do CDN).
- Token vence em até 1 ano; o app avisa ao Iniciar, antes da coleta.
- `4551` continua obrigatório; se a numeração mudar, ajustar `PADRAO_PATRIMONIO`.
- A conferência final contra o cadastro é do ASIdoBem; o app não valida existência da urna.
