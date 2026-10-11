# Publicação de listas para o ASIdoBem — design (Firestore)

Data: 2026-10-11 (revisado: Worker+R2 trocado por Firestore). Contrato de conteúdo: `IMPORTACAO_WEB.md`
(formato 1). O **transporte** muda em relação ao contrato (ver §3); os `IMPORTACAO*.md` **não são alterados**
nesta etapa e ficam defasados nesse ponto até a revisão que o usuário fará.

## 1. Objetivo

O leitor passa a ser o "site" do contrato: a equipe lê o QR oficial do TSE das urnas, escolhe a operação
de cada uma e **publica** uma lista no Firestore. O ASIdoBem lê as listas de lá e as confere como hoje.

Entregas:

1. Simplificar o app: só Inventário, só QR, única recusa por repetição (além do padrão de patrimônio).
2. Escolher a operação do contrato em vez das categorias antigas.
3. Gerar e publicar a lista (formato 1) no Firestore.
4. Som de sucesso e de erro, além da vibração já existente.
5. Lado ASIdoBem: o que ele precisa mudar para ler do Firestore (especificado aqui, implementado por
   quem mantém o ASIdoBem; o app Java não está neste repositório).

Fora de escopo: fila offline automática, alterar o `ListaCSV` do ASIdoBem, alterar os `IMPORTACAO*.md`.

## 2. Arquitetura

```
Celular (index.html) ──REST + idToken (conta escritora)──► Firestore: listas/<id>
ASIdoBem ──REST + idToken (conta leitora)──► Firestore: runQuery listas → campo csv → ListaCSV (já existente)
```

- `index.html` segue único, sem build, sem SDK: usa `fetch` na REST API do Firestore e do Identity Toolkit.
- Arquivos novos no repositório: `firestore.rules`, `firebase.json` (só a seção firestore) e
  `.firebaserc`. Deploy das regras com `firebase deploy --only firestore:rules`.
- Plano gratuito (Spark): 20 mil gravações e 50 mil leituras por dia; sobra para o uso.
- **Autenticação**: Authentication por e-mail e senha, duas contas — `escritora` (celulares da equipe) e
  `leitora` (ASIdoBem). Papel identificado pelo e-mail na regra.

## 3. Modelo de dados

Coleção `listas`, documento de id = `id` da lista (`aaaa-mm-dd-<local>-<seq>`, letras/números/`-`, ≤ 60).

| Campo | Tipo | Conteúdo |
|---|---|---|
| `codigo` | string | 5 dígitos (10000–99999) |
| `titulo` | string | ≤ 80, sem `;` |
| `local` | string | `POLO`, `Z<n>` ou vazio |
| `responsavel` | string | curto, opcional |
| `gerado_em` | string | ISO 8601 com fuso (ordenável) |
| `linhas` | integer | quantidade de linhas de dados |
| `csv` | string | **a lista inteira no formato 1** (identificação, cabeçalho, linhas), idêntica à que o `ListaCSV` já lê |

O texto do campo `csv` continua sendo o contrato de conteúdo. Mudam só o transporte (Firestore, não HTTP+
índice) e as garantias: o **índice e o SHA-256 saem**; a ordem vem de `orderBy gerado_em desc`; a
imutabilidade e a unicidade do `id` vêm das regras (create-only; o id do documento é o `id` da lista).
Limite do Firestore: documento ≤ 1 MiB. Com ~40 bytes por linha cabem ~25.000 linhas; o limite de 20.000
linhas do contrato se mantém, e o app recusa localmente acima de 15.000 linhas por segurança (>15.000 → dividir
em mais de uma lista).

## 4. Regras de segurança (`firestore.rules`)

- `listas/{id}`: `create` só se `request.auth.token.email` for a conta escritora; `read` (get/list) só para
  a conta leitora (e a escritora, para a confirmação pós-publicar); `update`/`delete` nunca.
- Validação na criação: `id` do documento bate com o `id` dentro do `csv`; `codigo` bate com o do `csv`;
  `codigo` = 5 dígitos; `csv` começa com `#ASIDOBEM;formato=1;`; tamanho de `csv` ≤ 1 MiB; os campos
  esperados e só eles.
- Os e-mails das duas contas ficam como constantes no arquivo de regras (não são segredos).
- Cadastros abertos de Authentication ficam **desligados**: as contas são criadas pelo console/CLI.

## 5. App

### 5.1 Remoções
Modo Bateria inteiro (segmented control, pareamento, decoy `CDJE`, `ultimoCodigo`/`candidato`,
`pendente`, confirmação de troca de modo, `gerarCsvBateria`, CSV `bateria_*`); leitura de código de barras;
`diferencaPequena`, `ultimoPatrimonioAceito`, `LIMITE_DIFERENCA_PATRIMONIO`; `codigoTocaBorda` e
`MARGEM_BORDA_FRACAO`. `FORMATOS_DESEJADOS` = `["qr_code"]`.

### 5.2 Aceitação de uma detecção
1. `format !== "qr_code"` → descarta, silêncio.
2. Sem `IDEQ` em `parsearCampos()` → descarta, silêncio.
3. `"45"+IDEQ` fora de `PADRAO_PATRIMONIO` → **erro com som**.
4. `IDEQ` já em `codigosInventarioVistos` → **erro com som**.
5. Senão aceita: grava o `IDEQ` puro (8 dígitos) com a operação e a nota atuais; vibração + som de sucesso.

`codigosInventarioVistos` só zera junto com `resultados` (Limpar e após publicar com sucesso).

### 5.3 Operação
O select de categoria vira select de operação: Recolher, Transferir, Devolver TRE, Descartar, Status,
Cadastrar (valores do contrato: `RECOLHER`, `TRANSFERIR:Z<n>`, `DEVOLVER_TRE`, `DESCARTAR`,
`STATUS:<status>`, `CADASTRAR`).

- Transferir mostra um campo de zona; aceita `Z59`/`59`/`Z059`, grava `Z<número sem zeros à esquerda>`;
  `POLO` também é aceito. Zona inválida impede a leitura de ser aceita (campo marcado).
- Status mostra select com: Pronta, Defeituosa, Danificada, Sucateada, Nao Certificada, Sem Bateria,
  Indisponivel.
- A nota vira `descricao`: até 200 caracteres; `;` e quebras de linha são trocados por espaço.
- Operação/parâmetro/nota são definidos uma vez e reaproveitados até mudarem.

### 5.4 Lista em tela e CSV
- `#lista-inventario` mostra número de ordem, `IDEQ` e operação (com parâmetro), na ordem do CSV;
  conteúdo escapado com `escaparHtml()`.
- CSV (Salvar/Compartilhar **e** o campo `csv` publicado) = formato 1: linha
  `#ASIDOBEM;formato=1;codigo=<código>;id=<id>;titulo=…;local=…;responsavel=…;gerado_em=…`, cabeçalho
  `patrimonio;operacao;descricao`, UTF-8 com `;`. Patrimônio como texto, só dígitos.
- Salvar/Compartilhar abrem o mesmo diálogo de identificação da publicação (código, responsável, local),
  para que o arquivo local também seja aceito pelo ASIdoBem ("Abrir arquivo…"). Cancelar cancela a ação.
- Nome do arquivo: `lista_<id>.csv`.

### 5.5 Publicar
Botão novo no rodapé (ícone, sem texto). Diálogo com:

- **Código** (5 dígitos, obrigatório, 10000–99999; digitado a cada coleta, não lembrado).
- **Responsável** e **local** (`POLO` ou `Z<n>`), opcionais, lembrados no aparelho (`localStorage`).
- O app gera `id` = `aaaa-mm-dd-<local em minúsculas ou sem-local>-<seq>` (seq de 2 dígitos; se o
  Firestore recusar por documento já existente, incrementa e tenta de novo) e `titulo` automático
  ("Inventário dd/mm").

Fluxo: login (`signInWithPassword`, token em memória e renovado por `refreshToken`) → `POST
documents/listas?documentId=<id>` com os campos da §3. Criar com `documentId` já existente devolve 409
(ALREADY_EXISTS), que é o sinal de colisão.

Sucesso: "Publicada (N linhas)", limpa a sessão. Falha (rede, auth, regra, 409 persistente): mostra o motivo e
**mantém a lista na tela** para tentar de novo ou salvar o CSV. Lista vazia: o botão não faz nada.

Configuração (única por aparelho, em `localStorage`): `apiKey` e `projectId` do Firebase, e e-mail/senha da
conta escritora. A `apiKey` do Firebase não é segredo (a proteção está nas regras). A senha da conta escritora
só consegue criar listas; é rotacionável trocando a senha no console. Sem configuração, Publicar avisa e abre
os ajustes.

### 5.6 Som
Web Audio API, tons gerados no código, sem arquivos. O `AudioContext` é criado/retomado no clique do botão
de câmera/galeria (gesto do usuário).

- Sucesso: dois tons ascendentes curtos, junto da vibração `[40,40,60]` existente.
- Erro: tom grave único mais longo, junto de vibração própria (`[120]`).
- Erro tocado **uma vez por valor** enquanto o mesmo valor continuar sendo lido na câmera (lê a cada
  ~320 ms). Na galeria, cada foto é independente.
- Sem Web Audio ou áudio bloqueado: falha em silêncio.

## 6. Lado ASIdoBem (especificação para quem mantém o Java)

Substitui `BuscaListas` (GET de índice/arquivo) por:

1. `POST https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=<apiKey>` com e-mail/senha
   da conta leitora → `idToken` (válido 1 h).
2. `POST https://firestore.googleapis.com/v1/projects/<projectId>/databases/(default)/documents:runQuery`
   com `Authorization: Bearer <idToken>`: coleção `listas`, `orderBy gerado_em desc`, `limit` configurável.
3. Para cada documento: `id` = último segmento de `name`; `codigo` = `fields.codigo.stringValue`; ignora sem
   baixar nada extra os de código que não é desta base; para os demais, `fields.csv.stringValue` é o conteúdo
   que já entra em `receber` do `DAOListas`, sem SHA-256 (não há índice). A regra "id já recebido não volta"
   continua valendo (`listas_recebidas.lista_id`). Se o conteúdo de um `id` já recebido for diferente,
   conta como "mudou" (não deveria ocorrer: as regras proíbem update).
4. Parsing JSON mínimo, sem dependência (as respostas têm forma fixa); `Config`: trocar `listas.endereco` /
   `listas.token` por `projectId`, `apiKey`, e-mail e senha da conta leitora.

O `ListaCSV`, a conferência, o `aplicar` e as telas permanecem como estão.

## 7. Testes

Playwright com stubs de `BarcodeDetector` e câmera, como hoje. Para o Firestore: **Firebase Emulator Suite**
(Firestore + Auth) rodando local; o app aponta o `projectId`/endereço para o emulador em teste.

- App: só QR (barcode ignorado, mesmo com valor válido); sem IDEQ ignorado; fora do padrão e repetido →
  som de erro, 1× por valor; aceito → som de sucesso; dedup entre câmera e galeria; valor gravado é o IDEQ
  puro; operações e parâmetros (zona, status) no CSV; nota limpa de `;`; conteúdo exato do CSV; lista em
  tela na ordem do CSV; falha de câmera sem regressão.
- Publicar: sucesso limpa a sessão; falha de rede/auth/regra mantém a lista; `id` sequencial após colisão.
- Regras (emulador): escritora cria; escritora não altera nem apaga; leitora não cria; anônimo não lê nem
  escreve; `id`/`codigo` divergentes do `csv` recusados; formato ≠ 1 recusado; documento > 1 MiB recusado.
- Ponta a ponta: celular (Playwright) → emulador → consulta `runQuery` como o ASIdoBem faria, conferindo
  que o `csv` lido é byte a byte o publicado.

## 8. Documentação

Atualizar `CLAUDE.md` (Bateria e similaridade saem; operações; Publicar; Firestore; som), `MANUAL.md`
(escolher operação, publicar, sons, configuração do aparelho) e `README.md` (projeto Firebase, contas,
regras, deploy). Deploy do app continua exigindo `git push origin master` com confirmação.

## 9. Riscos e decisões aceitas

- A senha da conta escritora fica no `localStorage` do celular: só cria listas; rotacionável.
- Sem fila offline: a lista fica na tela até o envio dar certo (ou o CSV é salvo).
- `4551` continua obrigatório; se a numeração mudar, ajustar `PADRAO_PATRIMONIO`.
- O contrato permite STATUS/CADASTRAR etc. sem validar contra o cadastro: quem confere é o ASIdoBem.
- O ASIdoBem **deixa de funcionar com o site antigo** (HTTP+índice) assim que trocar o transporte; como esse
  site ainda não existia, não há migração.
