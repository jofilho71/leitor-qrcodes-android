# Briefing para a sessão do ASIdoBem — o novo leitor de QR Codes (site do contrato)

> Cole/copie este arquivo no repositório do ASIdoBem e abra a sessão pedindo que ele seja lido antes de
> qualquer coisa. Ele descreve **o outro lado** do contrato `IMPORTACAO_WEB.md` / `IMPORTACAO_SISTEMA.md`:
> o app que publica as listas. Data: 2026-10-11. Versão do leitor: **v 1.2**.

## 1. Em uma frase

O leitor (`https://jofilho71.github.io/leitor-qrcodes-android/`) virou o **"site" do contrato**: o técnico
digita o **código de 5 dígitos** que o ASIdoBem mostrou, lê o **QR Code oficial do TSE** das urnas, escolhe a
ação e **publica** uma lista no formato 1 num repositório público do GitHub. O ASIdoBem coleta de lá.
A coleta (índice + download + SHA-256) funciona como o contrato já previa; o que **precisa mudar no ASIdoBem** é o
vocabulário de operações e de status (seção 5): o usuário decidiu que o ASIdoBem se adapta ao leitor, não o contrário.

## 2. Como o ASIdoBem deve apontar para o leitor

- Em *Site…*: `https://raw.githubusercontent.com/jofilho71/asidobem-listas/main/indice.csv`
- **Token em branco** (o repositório é público; leitura sem autenticação).
- `raw.githubusercontent.com` responde **200 direto**, sem redirecionamento (exigência do contrato, §4).
- **Atraso esperado**: GitHub Actions gera o índice (~1 min) + cache do CDN (~5 min). Uma lista recém-publicada
  pode demorar alguns minutos para aparecer. Isso foi aceito; não é bug.
- Cada lista: `https://raw.githubusercontent.com/jofilho71/asidobem-listas/main/listas/<id>.csv`
  (coluna `arquivo` do índice = `listas/<id>.csv`, relativa à pasta do índice).

## 3. O que o leitor publica

### Arquivo de lista (formato 1, conforme o contrato)
```
#ASIDOBEM;formato=1;codigo=48213;id=2026-10-20-48213-01;titulo=Inventário 20/10;gerado_em=2026-10-20T16:42:05-03:00
patrimonio;operacao;descricao
51250523;TRANSFERIR:Z59;nota do técnico
51250524;STATUS:Defeituosa;LAUDO
```
- UTF-8 **sem BOM**, separador `;`, fim de linha LF, última linha termina com `\n`, sempre 3 colunas.
- **Mudanças em relação ao exemplo do contrato**:
  - **Não há mais `local=` nem `responsavel=`** (campos opcionais, simplesmente omitidos). O código de 5 dígitos
    já identifica a origem.
  - `id` = `aaaa-mm-dd-<codigo>-<seq 2 dígitos>` (ex.: `2026-10-20-48213-01`). Único porque o arquivo nunca é
    sobrescrito: se o id já existe, o app usa o próximo `seq`. `titulo` = `Inventário dd/mm`.
- `patrimonio` = **`IDEQ` do QR do TSE, puro, 8 dígitos** (ex.: `51250523`). Só passa o padrão
  `"45"+IDEQ` ~ `/^4551\d{6}$/`, ou seja, patrimônios que começam com `51`. Um patrimônio aparece **uma vez por
  lista** (o app recusa repetido na leitura, então o §3.3 do contrato não deve ser violado).
- `descricao`: nota livre do técnico, ≤ 200 caracteres, `;` e quebras viram espaço.
- Limites no app: até 15.000 itens e 5 MB por lista (abaixo dos 20.000 / 5 MB do contrato).
- O **conteúdo do QR** lido é `APLC:TSE APLF:QRC.PATR VERE:1 TPEQ:UE MDEQ:... IDEQ:<8 dígitos>`; o leitor extrai
  só o `IDEQ`. Código de barras **não** é mais lido (ruído de decodificação).

### Índice (`indice.csv`) — gerado por GitHub Actions, não pelo celular
Cabeçalho exato `id;codigo;gerado_em;titulo;linhas;sha256;arquivo`, UTF-8, `;`, mais recente primeiro
(por `gerado_em` convertido a UTC; desempate por `id` decrescente). `sha256` = SHA-256 dos **bytes exatos** do
arquivo; `linhas` = linhas de dados. O gerador (`repositorio-listas/scripts/gerar_indice.py`, no repositório do
leitor) **valida**: formato 1, `codigo` de 5 dígitos, `id` válido e igual ao nome do arquivo, cabeçalho exato,
3 colunas, ≤ 20.000 linhas, ≤ 5 MB. **Lista inválida fica fora do índice** (só registrada no log do Actions).
**O gerador não valida o vocabulário de `operacao`/`status`** — isso é do ASIdoBem.

## 4. Fluxo do técnico (para entender os dados que chegam)

1. Toca **Iniciar** → informa o **código de 5 dígitos** do ASIdoBem. Se digitar errado, o ASIdoBem **ignora a
   lista** (código que não é dele); ela continua no repositório para conferência offline — decisão do usuário.
2. Escolhe a ação (e a zona, se Transferir), lê os QRs com câmera ou fotos da galeria, pode mudar a ação/nota no meio
   (uma lista pode misturar ações).
3. **Publicar** → `PUT` na API de conteúdo do GitHub (token fine-grained **por aparelho**, restrito ao repositório
   `asidobem-listas`, só no `localStorage` do aparelho). Nunca sobrescreve: arquivo existente → próximo `seq`.
   Uma nova tentativa depois de resposta perdida é idempotente (mesmo id e mesmo conteúdo), então **não há lista
   duplicada por reenvio**.
4. Volta ao início para nova configuração. Cada publicação = uma lista nova com id novo.

## 5. Mudanças pedidas ao ASIdoBem (decisões do usuário — o leitor é o modelo; o ASIdoBem se adapta)

Decisões já tomadas, sem necessidade de nova consulta:

- **Todas as operações vindas do leitor entram como PLANO** e só depois são efetivadas (confirmação no ASIdoBem),
  como o contrato já previa para movimentações. Isso passa a valer também para `STATUS` e `EMPRESTAR`.
- **Vocabulário aceito na importação = só o que o leitor emite** (tabela 5.1). `RECOLHER`, `DEVOLVER_TRE`,
  `DESCARTAR`, `CADASTRAR` e os demais status saem do vocabulário de importação; linhas assim são recusadas.
- **Laudo e Defeito não existem como status novos**: o leitor já os converte para o status oficial **`Defeituosa`**
  (Laudo = `STATUS:Defeituosa` com `descricao` iniciando em `LAUDO`; Defeito = `STATUS:Defeituosa`). Nada a criar
  no cadastro de status para isso; a `descricao` vai para o complemento do cadastro, como já ocorre em `STATUS`.

### 5.1 O que o leitor emite (única fonte de `operacao` na importação)

| Ação no app | `operacao` gravada | `descricao` | Situação no contrato atual |
|---|---|---|---|
| Transferir (zona ou polo) | `TRANSFERIR:Z<n>` / `TRANSFERIR:POLO` | nota livre | já existe |
| Emprestar | `EMPRESTAR` (sem parâmetro) | nota livre (o técnico pode escrever o tomador) | **nova** |
| Status → Pronta | `STATUS:Pronta` | nota livre | já existe |
| Status → Defeito | `STATUS:Defeituosa` | nota livre | já existe |
| Status → Laudo | `STATUS:Defeituosa` | `LAUDO` ou `LAUDO - <nota>` | já existe (a marca vai na descrição) |

`descricao`: ≤ 200 caracteres, `;`/quebra de linha viram espaço.

### 5.2 `EMPRESTAR` — nova operação (definição do usuário)

- Gera um **plano de empréstimo** (como as outras operações), que depois é efetivado.
- **Efeito ao efetivar**: registra no **histórico da urna** e marca a urna como **Emprestada**. A urna **não muda
  de local** no cadastro. A devolução é tratada como outra operação, fora deste escopo (hoje o leitor não a emite).
- Parâmetro necessário: **tomador** (quem fica com a urna). O leitor não envia o tomador como campo; ele deve ser
  informado **na tela de importação do ASIdoBem** (seção 5.3). A `descricao` do leitor (nota livre) pode já trazer
  essa informação e deve ser exibida ao lado para o técnico copiar/conferir.
- A ser definido pela sessão do ASIdoBem junto ao usuário: **"Emprestada"** vira um **status novo** no cadastro
  (entra na lista de status e nos filtros/relatórios) ou uma marcação separada do status técnico da urna (uma urna
  pode estar Pronta *e* Emprestada)? Como tratar `EMPRESTAR` sobre uma urna já emprestada (aviso/recusa, como já
  ocorre com `STATUS` igual ao atual)? Remover do contrato a frase que exclui empréstimos.

### 5.3 Tela de importação — revisar

Pedido do usuário: **revisar a tela de importação** para que, **depois da leitura e da exibição em tela** das linhas
da lista, seja possível **definir os parâmetros necessários de cada operação** antes de gerar os planos.

- Preenchimento **por linha**, com **preenchimento em lote** (ex.: "aplicar este tomador a todas as linhas
  `EMPRESTAR`") para agilizar listas longas.
- Parâmetro hoje identificado: **tomador** para `EMPRESTAR`. Revisar com o usuário se outras operações também se
  beneficiam de parâmetros editados na tela (por exemplo, confirmar/alterar o destino de `TRANSFERIR`); o leitor
  continua enviando o destino em `TRANSFERIR:<destino>`, e o que for definido na tela vale a partir dali.
- Linhas recusadas (padrão inválido, patrimônio repetido, operação fora do vocabulário, urna desconhecida…) seguem
  exibidas com o motivo, como já no contrato.
- A `descricao` de cada linha deve aparecer na tela (é a única comunicação livre do técnico de campo).

### 5.4 Reescrever os contratos

Atualizar `IMPORTACAO_WEB.md` e `IMPORTACAO_SISTEMA.md`: §3.4 (vocabulário = 3 operações; status aceitos; a nota
sobre empréstimos), os exemplos (ainda usam `local=`, `responsavel=`, `RECOLHER`), o §3.1 (`local`/`responsavel`
continuam opcionais, mas o leitor v1.2 não os envia) e a descrição da tela de importação. Se qualquer coisa do que o
leitor grava precisar mudar, **avisar o projeto do leitor** — o ajuste no app é pequeno (`<option>` e constantes
`STATUS_OFICIAL`/`descricaoAtual` em `index.html`).

Confirmar com teste: a ausência de `local`/`responsavel` na linha de identificação não quebra a leitura.

## 6. Como testar ponta a ponta

- O repositório do leitor tem **50 QR codes de teste** (`qrcodes-teste/folha-1..5.png`, números em
  `qrcodes-teste/lista.txt`). Os patrimônios `512502xx…5125xxxx` são fictícios e **podem não existir no cadastro**
  do ASIdoBem: para testar `TRANSFERIR`/`STATUS` de verdade, cadastre alguns deles na base de teste ou use
  patrimônios reais; os desconhecidos devem ser recusados com o motivo apropriado.
- Roteiro: publicar uma lista com 1 `TRANSFERIR:Z59`, 1 `TRANSFERIR:POLO`, 1 `STATUS:Pronta`, 1 `STATUS:Defeituosa`,
  1 `STATUS:Defeituosa` com descrição `LAUDO`, 2 `EMPRESTAR` → no ASIdoBem, *Buscar no site (F5)* → conferir que a
  lista chega, o SHA-256 bate, **todas as linhas viram planos**, na tela de importação é possível informar o
  **tomador** (por linha e em lote) nas linhas `EMPRESTAR`, e ao efetivar o histórico da urna registra o empréstimo
  e a urna fica marcada como Emprestada, sem trocar de local. Incluir uma linha `RECOLHER` à mão e conferir que é
  recusada (fora do vocabulário).
- Verificar o comportamento com `codigo` diferente do configurado (lista ignorada sem baixar) e com índice sem
  nenhuma lista (só o cabeçalho).

## 7. Referências (repositório do leitor, `jofilho71/leitor-qrcodes-android`)

- `CLAUDE.md`: regras do app (aceitação de QR, CSV, publicação, token). `MANUAL.md`: manual do técnico.
- `docs/superpowers/specs/2026-10-11-publicacao-asidobem-design.md`: o desenho completo desta integração.
- `repositorio-listas/`: workflow + `gerar_indice.py` do repositório público `jofilho71/asidobem-listas`.
- Contrato: `IMPORTACAO_WEB.md` (lado do site) e `IMPORTACAO_SISTEMA.md` (lado do ASIdoBem) — **não foram
  alterados** por este trabalho.
