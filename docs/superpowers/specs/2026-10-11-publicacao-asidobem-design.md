# Publicação de listas para o ASIdoBem — design

Data: 2026-10-11. Contrato externo: `IMPORTACAO_WEB.md` (formato 1) e `IMPORTACAO_SISTEMA.md`
(lado do ASIdoBem). Esses dois arquivos **não são alterados** nesta etapa.

## 1. Objetivo

O leitor passa a ser o "site" do contrato: a equipe lê o QR oficial do TSE das urnas, escolhe a operação
de cada uma e **publica** uma lista na web. O ASIdoBem busca o índice, baixa as listas novas e as confere.

Entregas:

1. Simplificar o app: só Inventário, só QR, única recusa por repetição (além do padrão de patrimônio).
2. Escolher a operação do contrato em vez das categorias antigas.
3. Gerar e publicar a lista no formato 1 em um Worker Cloudflare + R2.
4. Som de sucesso e de erro, além da vibração já existente.

Fora de escopo: fila offline automática, edição do contrato, alterações no ASIdoBem.

## 2. Arquitetura

```
Celular (index.html) ──POST /listas (token de escrita)──► Worker ──► R2: listas/<id>.csv, indice.csv
ASIdoBem ◄── GET /indice.csv, /listas/<id>.csv (token de leitura) ──┘
```

- `index.html` segue único, sem build.
- `worker/worker.js` + `worker/wrangler.toml` (novo; único código fora do `index.html`). Deploy manual com
  `wrangler deploy`; passo a passo documentado no `README.md`.
- Dois secrets do Worker: `TOKEN_LEITURA` (entregue ao ASIdoBem) e `TOKEN_ESCRITA` (digitado uma vez em
  cada celular, guardado no `localStorage`; só acrescenta listas, nunca apaga nem altera).

## 3. Worker

**`POST /listas`** (Bearer escrita; corpo = CSV pronto, `text/csv`):

- 401/403 com token errado ou ausente.
- Valida: linha `#ASIDOBEM;` com `formato=1`, `codigo` de 5 dígitos (10000–99999), `id` válido
  (letras, números e `-`, até 60); cabeçalho exato `patrimonio;operacao;descricao`; 3 colunas por linha;
  até 20.000 linhas e 5 MB; UTF-8. Falha → 400 com o motivo.
- `id` já existente → 409 (lista imutável).
- Calcula o SHA-256 dos bytes recebidos, grava `listas/<id>.csv`, **depois** reescreve `indice.csv` com a
  linha nova no topo (`id;codigo;gerado_em;titulo;linhas;sha256;arquivo`). Responde 201.
- O Worker revalida tudo; não confia no cliente. A concorrência de dois POST simultâneos é aceita como
  risco baixo (uso por equipe pequena); o índice é sempre reconstruído lendo o R2 no momento da escrita.

**`GET /indice.csv`** e **`GET /listas/<id>.csv`** (Bearer leitura): 200 `text/csv; charset=utf-8`, sem
redirecionamento; 401/403 com token errado; 404 se não existe.

## 4. App

### 4.1 Remoções
Modo Bateria inteiro (segmented control, pareamento, decoy `CDJE`, `ultimoCodigo`/`candidato`,
`pendente`, confirmação de troca de modo, `gerarCsvBateria`, CSV `bateria_*`); leitura de código de barras;
`diferencaPequena`, `ultimoPatrimonioAceito`, `LIMITE_DIFERENCA_PATRIMONIO`; `codigoTocaBorda` e
`MARGEM_BORDA_FRACAO` (existiam por causa do barcode). `FORMATOS_DESEJADOS` = `["qr_code"]`.

### 4.2 Aceitação de uma detecção
1. `format !== "qr_code"` → descarta, silêncio.
2. Sem `IDEQ` em `parsearCampos()` → descarta, silêncio.
3. `"45"+IDEQ` fora de `PADRAO_PATRIMONIO` → **erro com som**.
4. `IDEQ` já em `codigosInventarioVistos` → **erro com som**.
5. Senão aceita: grava o `IDEQ` puro (8 dígitos) com a operação e a nota atuais; vibração + som de sucesso.

`codigosInventarioVistos` só zera junto com `resultados` (Limpar e após publicar com sucesso).

### 4.3 Operação
O select de categoria vira select de operação: Recolher, Transferir, Devolver TRE, Descartar, Status,
Cadastrar (valores do contrato: `RECOLHER`, `TRANSFERIR:Z<n>`, `DEVOLVER_TRE`, `DESCARTAR`,
`STATUS:<status>`, `CADASTRAR`).

- Transferir mostra um campo de zona; aceita `Z59`/`59`/`Z059`, grava `Z<número sem zeros à esquerda>`;
  `POLO` também é aceito. Zona inválida impede a leitura de ser aceita (campo marcado).
- Status mostra select com: Pronta, Defeituosa, Danificada, Sucateada, Nao Certificada, Sem Bateria,
  Indisponivel.
- A nota vira `descricao`: até 200 caracteres; `;` e quebras de linha são trocados por espaço.
- Operação/parâmetro/nota são definidos uma vez e reaproveitados até mudarem (como hoje).

### 4.4 Lista em tela e CSV
- `#lista-inventario` mostra número de ordem, `IDEQ` e operação (com parâmetro) de cada item, na ordem do
  CSV; conteúdo escapado com `escaparHtml()`.
- CSV (Salvar/Compartilhar **e** o que é publicado) = formato 1 do contrato: linha
  `#ASIDOBEM;formato=1;codigo=<código>;id=<id>;titulo=…;local=…;responsavel=…;gerado_em=…`, cabeçalho
  `patrimonio;operacao;descricao`, UTF-8 com `;`. O patrimônio vai como texto, só dígitos.
  Salvar/Compartilhar abrem o mesmo diálogo de identificação da publicação (código, responsável, local),
  para que o arquivo local também seja aceito pelo ASIdoBem ("Abrir arquivo…"). Cancelar o diálogo
  cancela a ação.
- Nome do arquivo: `lista_<id>.csv`.

### 4.5 Publicar
Botão novo no rodapé (ícone, sem texto). Abre diálogo com:

- **Código** (5 dígitos, obrigatório, validado 10000–99999; digitado a cada coleta, não lembrado).
- **Responsável** e **local** (`POLO` ou `Z<n>`), opcionais, lembrados no aparelho (`localStorage`).
- O app gera `id` = `aaaa-mm-dd-<local em minúsculas ou sem-local>-<seq>` (seq de 2 dígitos, incrementa se o
  Worker responder 409) e `titulo` automático ("Inventário dd/mm").

Sucesso (201): mensagem "Publicada (N linhas)", limpa a sessão (resultados, Set de vistos). Falha (rede,
401/403, 400, 409 após retentativas): mostra o motivo e **mantém a lista na tela** para tentar de novo ou
salvar o CSV. Sem lista (0 itens), o botão não faz nada.

Configuração (endereço do Worker + token de escrita): área discreta de ajustes, definida uma vez por
aparelho, em `localStorage`. Sem configuração, Publicar avisa e abre os ajustes.

### 4.6 Som
Web Audio API, tons gerados no código, sem arquivos. O `AudioContext` é criado/retomado no clique do botão
de câmera (e de galeria), que é um gesto do usuário.

- Sucesso: dois tons ascendentes curtos, junto da vibração `[40,40,60]` existente.
- Erro: tom grave único mais longo, junto de uma vibração própria (`[120]`).
- Erro tocado **uma vez por valor**: enquanto o mesmo valor continuar sendo lido na câmera, não repete
  (a câmera lê a cada ~320 ms). Na galeria, cada foto é independente.
- Sem Web Audio ou com áudio bloqueado: falha em silêncio, sem quebrar a leitura.

## 5. Testes

Playwright com stubs de `BarcodeDetector` e câmera, como hoje; Worker local com `wrangler dev`/Miniflare.

- App: só QR (barcode ignorado, mesmo com valor válido); sem IDEQ ignorado; fora do padrão e repetido →
  chamada do som de erro, 1× por valor; aceito → som de sucesso; dedup entre câmera e galeria; valor
  gravado é o IDEQ puro; operações e parâmetros (zona, status) no CSV; nota limpa de `;`; conteúdo exato do
  CSV (identificação, cabeçalho, ordem); lista em tela na ordem do CSV; falha de câmera (getUserMedia e
  play) sem regressão.
- Publicar: sucesso limpa a sessão; falha de rede/401/409 mantém a lista; `id` sequencial após 409.
- Worker: casos do `IMPORTACAO_WEB.md` §5 aplicáveis (formato ≠ 1, código inválido, `id` repetido, cabeçalho
  errado, limites, token errado); índice com a linha nova no topo; SHA-256 do índice = SHA-256 dos bytes
  baixados; GET sem token → 401.
- Ponta a ponta: celular (Playwright) → Worker local → conferência do índice e da lista baixada.

## 6. Documentação

Atualizar `CLAUDE.md` (Bateria e similaridade saem; operações; Publicar; Worker; som), `MANUAL.md`
(fluxo operacional: escolher operação, publicar, sons) e `README.md` (setup do Worker, secrets, deploy,
endpoint para o ASIdoBem). Deploy do app continua exigindo `git push origin master` com confirmação.

## 7. Riscos e decisões aceitas

- Token de escrita no `localStorage` do celular: só acrescenta listas; rotacionável trocando o secret.
- Sem fila offline: a lista fica na tela até o envio dar certo (ou o CSV é salvo).
- `4551` continua obrigatório; se a numeração mudar, ajustar `PADRAO_PATRIMONIO`.
- O contrato permite STATUS/CADASTRAR etc. sem validação de existência no cadastro: quem confere é o
  ASIdoBem.
