# Briefing para a sessão do ASIdoBem — o novo leitor de QR Codes (site do contrato)

> Cole/copie este arquivo no repositório do ASIdoBem e abra a sessão pedindo que ele seja lido antes de
> qualquer coisa. Ele descreve **o outro lado** do contrato `IMPORTACAO_WEB.md` / `IMPORTACAO_SISTEMA.md`:
> o app que publica as listas. Data: 2026-10-11. Versão do leitor: **v 1.1**.

## 1. Em uma frase

O leitor (`https://jofilho71.github.io/leitor-qrcodes-android/`) virou o **"site" do contrato**: o técnico
digita o **código de 5 dígitos** que o ASIdoBem mostrou, lê o **QR Code oficial do TSE** das urnas, escolhe a
ação e **publica** uma lista no formato 1 num repositório público do GitHub. O ASIdoBem coleta de lá.
**Nenhuma alteração no ASIdoBem é necessária para a coleta funcionar** — mas o vocabulário de operações mudou
(seção 5) e isso precisa de uma decisão do lado de vocês.

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
51250524;STATUS:Defeito;
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

## 5. ⚠️ Divergência com o contrato atual — decisão necessária no ASIdoBem

Por pedido do usuário, o leitor agora oferece só estas **ações**:

| No app | Grava no CSV | Está no contrato (§3.4)? |
|---|---|---|
| Transferir (zona ou POLO) | `TRANSFERIR:Z<n>` / `TRANSFERIR:POLO` | **Sim** |
| Emprestar | `EMPRESTAR` | **Não** |
| Status → Pronta | `STATUS:Pronta` | **Sim** |
| Status → Defeito | `STATUS:Defeito` | **Não** (existe `Defeituosa`) |
| Status → Laudo | `STATUS:Laudo` | **Não** |

`RECOLHER`, `DEVOLVER_TRE`, `DESCARTAR`, `CADASTRAR` **saíram do app** (continuam válidos no contrato).

O contrato diz que o vocabulário é **fechado** e que **empréstimos ficam de fora de propósito** ("não movem
material e o tomador não tem cadastro"). Hoje, portanto, o ASIdoBem **recusa a linha inteira** de
`EMPRESTAR`, `STATUS:Defeito` e `STATUS:Laudo` (e `STATUS:Pronta` e `TRANSFERIR:*` são aceitos normalmente). As
demais linhas da mesma lista não são afetadas (recusa por linha). O usuário sabe disso e escolheu assim; as linhas
recusadas ficam disponíveis no arquivo para a conferência offline dele.

**Decisões a tomar na sessão do ASIdoBem** (com o usuário):
1. Aceitar `EMPRESTAR`? Se sim: o que faz (registro/histórico sem mover material? plano?), e como tratar o
   tomador (a `descricao` é o único lugar para ele). Hoje o contrato diz que empréstimo não entra.
2. Aceitar `STATUS:Defeito` como sinônimo de `Defeituosa`, ou o leitor passa a gravar `Defeituosa`?
   (Mudança de uma palavra no app, se preferirem manter o vocabulário oficial.)
3. `STATUS:Laudo`: é um status novo da urna (qual o significado: "aguardando laudo"?) ou uma anotação? Se for
   status novo, entra na lista de §3.4.
4. Quando decidido, **atualizar `IMPORTACAO_WEB.md`/`IMPORTACAO_SISTEMA.md`** (os dois lados do contrato) e avisar
   o projeto do leitor para ajustar o vocabulário — o ajuste no app é trivial (opções do `<select>` em
   `index.html`).

Também confirmar: a ausência de `local`/`responsavel` na linha de identificação não deve quebrar nada (são
opcionais pelo contrato §3.1) — vale um teste.

## 6. Como testar ponta a ponta

- O repositório do leitor tem **50 QR codes de teste** (`qrcodes-teste/folha-1..5.png`, números em
  `qrcodes-teste/lista.txt`). Os patrimônios `512502xx…5125xxxx` são fictícios e **podem não existir no cadastro**
  do ASIdoBem: para testar `TRANSFERIR`/`STATUS` de verdade, cadastre alguns deles na base de teste ou use
  patrimônios reais; os desconhecidos devem ser recusados com o motivo apropriado.
- Roteiro: publicar uma lista com 1 `TRANSFERIR:Z59`, 1 `STATUS:Pronta`, 1 `EMPRESTAR`, 1 `STATUS:Defeito`,
  1 `STATUS:Laudo` → no ASIdoBem, *Buscar no site (F5)* → conferir que a lista chega, o SHA-256 bate, os dois
  primeiros itens entram e os três últimos são recusados com mensagem clara (enquanto a seção 5 não for resolvida).
- Verificar o comportamento com `codigo` diferente do configurado (lista ignorada sem baixar) e com índice sem
  nenhuma lista (só o cabeçalho).

## 7. Referências (repositório do leitor, `jofilho71/leitor-qrcodes-android`)

- `CLAUDE.md`: regras do app (aceitação de QR, CSV, publicação, token). `MANUAL.md`: manual do técnico.
- `docs/superpowers/specs/2026-10-11-publicacao-asidobem-design.md`: o desenho completo desta integração.
- `repositorio-listas/`: workflow + `gerar_indice.py` do repositório público `jofilho71/asidobem-listas`.
- Contrato: `IMPORTACAO_WEB.md` (lado do site) e `IMPORTACAO_SISTEMA.md` (lado do ASIdoBem) — **não foram
  alterados** por este trabalho.
