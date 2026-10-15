# Listas de patrimônio — implementação no ASIdoBem

O contrato com o site (código, arquivo, índice, operações) está em
[`IMPORTACAO_WEB.md`](IMPORTACAO_WEB.md). Este documento é o lado do ASIdoBem:
o que foi feito, onde está e os passos que faltam. Implementado em 10/10/2026; vocabulário e empréstimo ajustados em 11/10/2026 para o leitor de QR Codes v1.2
(desenho em `docs/superpowers/specs/2026-10-11-integracao-leitor-design.md`).

## 1. Visão geral

```
ASIdoBem                         site                          ASIdoBem
─────────                        ────                          ─────────
Gerar código (48213)  ──────►  pessoa digita 48213
                               monta a lista, publica
                               lista + índice (SHA-256)
                                                   ◄────────  Buscar no site (F5)
                                                              baixa só as novas com código daqui
                                                              guarda no histórico (listas_recebidas)
                                                              Conferência linha a linha
                                                              Aplicar lista (planos, status, empréstimos)
                                                              → planos pendentes com patrimônios
                                                              → Planos › Efetivar → transação + recibo
```

Princípios que guiaram o desenho:

- **A lista nunca move nada sozinha.** `TRANSFERIR` vira **plano**; o plano se
  efetiva no editor de Planos, onde tudo ainda é editável. `STATUS` (cadastro) e
  `EMPRESTAR` (empréstimo, sem mudar a urna de local) valem na hora de aplicar a lista.
- **Vocabulário = o que o leitor emite**: `TRANSFERIR:Z<n>|POLO`, `STATUS:Pronta|Defeituosa`,
  `EMPRESTAR` e `LEITURA` (desde 0.10.0: só observação, sem efeito no cadastro). O resto é recusado como "fora do vocabulário".
- **Nada volta como novidade.** Tudo o que chega fica em `listas_recebidas`
  (aceita ou recusada), e a busca não baixa de novo um `id` já conhecido.
- **Sem dependência nova.** Java 8 puro: `HttpURLConnection`, `MessageDigest`,
  `SecureRandom`. Nada de JSON (índice e lista são CSV).
- **A origem vem do cadastro**, nunca da lista — a mesma regra de toda
  transação (`DAOTransacoes.moverUrnas`).

## 2. Onde está

| Peça | Arquivo | O que faz |
|---|---|---|
| Tabelas | `db/ConexaoDB` | `listas_codigos` (código, finalidade, aberto/encerrado) e `listas_recebidas` (id da lista, código, SHA-256, metadados, **conteúdo**, origem site/arquivo, situação, resultado) |
| Formato | `util/ListaCSV` | Lê a lista (identificação, cabeçalho, linhas, limites, repetidos) e o índice. Só formato; nada de cadastro |
| Download | `util/BuscaListas` | GET com timeout, sem redirecionamento, token Bearer, limite de 5 MB, `https://` ou `file://`; SHA-256 |
| Regras | `db/DAOListas` | Códigos (gerar, listar, encerrar/reabrir), recebimento, histórico, busca no site, conferência contra o cadastro, aplicação, descarte |
| Preferência | `util/Config` | `listas.endereco` (padrão: o índice do leitor, `Config.ENDERECO_LISTAS_PADRAO`) e `listas.token`, no arquivo da máquina (fora do banco); "Restaurar padrões" dos documentos não os apaga |
| Tela | `ui/panels/ListasPanel` | Aba **Movimentar › Listas**: códigos, receber (site, arquivo, configurar site), histórico, conferência (coluna **Tomador**, editável por linha nas `EMPRESTAR`; caixa em toda linha com efeito — desmarcada fica de fora —, com caixa no cabeçalho para marcar/desmarcar tudo, e coluna **Devolução em**), aplicar/descartar |
| Título da aba | `ui/panels/MovimentarPanel` | "Listas · N a tratar" (recebidas ainda não aplicadas nem descartadas) |
| Testes | `testes/interface/TesteListasEdicao` (correção por grupo, lote, célula, restauração, nomes parecidos, aplicação) e `testes/interface/TesteListas` | Código, busca por `file://` (nova, outro código, SHA errado, índice malformado), segunda busca sem repetir, conferência linha a linha (inclusive `EMPRESTAR`: sem tomador, edição do tomador), devolução (simples, parcial, tomador diferente, desmarcada, data editada, desfeita se a urna voltou antes) e marcar/desmarcar tudo, aplicação, desfazer tudo se o empréstimo falhar, efetivação do plano gerado, código encerrado, endereço padrão |

## 3. Dados

`listas_codigos`

| Coluna | |
|---|---|
| `codigo` | 5 dígitos, 10000–99999, UNIQUE, sorteado com `SecureRandom` até não colidir |
| `finalidade` | Texto livre do operador ("Coleta pós-eleição Zona 59") |
| `situacao` | `aberto` (aceita listas) / `encerrado` (recusa as novas) |

`listas_recebidas`

| Coluna | |
|---|---|
| `lista_id` | `id` da lista, UNIQUE — é o que impede receber duas vezes |
| `sha256` | Do arquivo recebido |
| `conteudo` | O arquivo inteiro (texto), para rever e reconferir depois; nulo na recusada |
| `origem` | `site` ou `arquivo` |
| `situacao` | `recebida` (a tratar) → `aplicada` / `descartada`; ou `recusada` na chegada |
| `resultado` | O que foi feito ("plano #31 (Zona 59 → Polo 24, 260 urnas); status alterado em 3 urnas") ou o motivo da recusa |

## 4. Fluxos

**Gerar código.** `DAOListas.gerarCodigo(finalidade)` → código aberto; a tela
copia para a área de transferência e o mostra grande.

**Buscar no site** (`DAOListas.buscarNoSite`):

1. Baixa o índice (`Config.listasEndereco` — por padrão o do leitor, sem token —, com o token se houver).
2. Para cada anúncio: código que não é desta base → conta como "de outros
   códigos", sem baixar; `id` já em `listas_recebidas` → "já recebida" (se o
   SHA-256 mudou, conta como "mudou no site", sem aviso repetido); senão baixa.
3. `receber`: lê o arquivo; confere SHA-256, `id` e `codigo` contra o anúncio;
   confere o código (desta base, aberto). Recusa → registra como `recusada`
   com o motivo (não volta a ser oferecida). Aceita → registra `recebida` com
   o conteúdo.

**Abrir arquivo.** O mesmo `receber`, sem anúncio (sem SHA-256 a conferir).

**Conferência** (`DAOListas.conferir`), sempre contra o cadastro **de hoje**:
erros de formato (inclusive operação fora do vocabulário) vêm do `ListaCSV`;
depois, por linha: urna cadastrada, local atual (origem), zona de destino
existente, já no destino, status igual, tamanho do patrimônio. `EMPRESTAR`: recusa
urna em local virtual e linha sem tomador (o tomador começa
como a descrição e é editável na tela — `Conferida.definirTomador` reconfere;
só a recusa "sem tomador" se desfaz assim). `TRANSFERIR`/`STATUS` de urna
emprestada saem com aviso. `EMPRESTAR` de urna **já emprestada** vira **devolução** (resultado
`devolução`, marcada por padrão, ao tomador original; aviso se a descrição for diferente do tomador;
data de hoje, editável, nunca futura nem anterior à coleta). Resultado
válida/aviso/recusada/devolução e o motivo.

**LEITURA e CSV** (desde 2026-10-15). `LEITURA` não leva parâmetro; a `descricao` é a observação. Na conferência é
`Conferida.leitura`: válida (aviso se a urna não estiver cadastrada), sem caixa e sem efeito (`marcavel()` falso), "só leitura"
em *Vai para*. `aplicar` aceita lista só de leituras (resultado "N leituras registradas, sem efeito no cadastro"); o grupo
tem rótulo próprio. **Baixar CSV…** (`ListasPanel.baixarCsv`, `DAOListas.csv`) vale para toda lista cujo arquivo foi guardado
(a recusada na chegada não tem): sem correções sai o arquivo como veio; com correções pergunta *Como veio* ou *Com as minhas
correções* — nesta, só as linhas corrigidas mudam, as demais saem exatamente como vieram, e o tomador corrigido de um
`EMPRESTAR` vai na descrição, que é onde o formato o guarda. A pasta e o modo de salvar são os de `Config.Documento.LISTA`
(padrão `listas/`, ignorada pelo Git); depois de gravar, `Dialogos.documentoGerado` oferece abrir o arquivo ou a pasta.

**Correção pelo operador** (desde 2026-10-14). A lista do técnico é uma sugestão: com ela
pendente (`recebida`), tudo se corrige **menos o patrimônio**, que vem do QR Code. O arquivo
recebido (`listas_recebidas.conteudo`) nunca muda; as correções ficam em `listas_ajustes`
(`lista_id`, `linha`, `operacao`, `descricao`, `tomador`, quem e quando), uma por linha
corrigida, e `conferir` as aplica por cima do original — `Conferida.opOriginal`/`descOriginal`
guardam o que veio, `ajustada()` diz se difere e `comoVeio()` alimenta a coluna *Como veio*.
Voltar ao original apaga a linha da tabela.

- `ListaCSV.definir(linha, operacao, descricao)` reaplica as regras de formato; `Linha.fixa` marca o
  que não se corrige (patrimônio vazio, não numérico, repetido; linha com número errado de colunas).
- Três caminhos de edição: célula (`guardar`, que grava o estado atual da `Conferida`), lote
  (`ajustar(rec, linhas, Alteracao)`: tipo/parâmetro/descrição, tudo ou nada) e `restaurar`. Após `ajustar`
  e `restaurar` a tela reconfere a lista (`ListasPanel.reconferir`, que preserva caixas e seleção).
- **Tomador**: em `EMPRESTAR` começa como a descrição; na primeira correção da linha ele é "travado"
  (`listas_ajustes.tomador`) e deixa de acompanhar a descrição.
- **Grupos** (`DAOListas.agrupar`): linhas com a mesma operação e destino/status/tomador (comparados sem
  caixa nem acento); o rótulo cita o destino e de onde as urnas saem. Corrigir o grupo é `ajustar` nas suas linhas.
- **Parecidos** (`parecidos`): cada pedaço do nome mais curto tem de ser começo, ou diferir em até 1 letra, do
  pedaço correspondente do outro. Gera aviso (nunca troca sozinho) contra os tomadores já usados em empréstimos
  e os da própria lista. Zona inexistente cita as cadastradas a um dígito de diferença.
- Lista aplicada ou descartada não aceita correção; o resultado diz "N linhas corrigidas pelo operador".

**Aplicar** (`DAOListas.aplicar`, um commit): agrupa as linhas aplicáveis por
rota (local atual → destino) e cria **um plano pendente por rota**, com
quantidade = número de urnas e os patrimônios em `plano_patrimonios`;
observação "Lista <id> (código N): descrições". `STATUS` → `DAOUrnas.salvarUrna`
(grava `urna_eventos`), descrição acrescentada ao complemento. Marca a lista
`aplicada` com o resultado. `EMPRESTAR` → um empréstimo por tomador (comparado
sem diferenciar caixa nem espaços nas pontas) via `DAOEmprestimo.salvar`: data
de coleta = hoje, a urna fica onde está, observação "Lista <id> (código N)", sem
recibo (impresso depois, na tela de Empréstimos). Tudo na mesma transação: se um
empréstimo for recusado, nada da lista é gravado e ela continua "recebida".
Devoluções marcadas: o item do empréstimo é marcado como devolvido na data indicada, via
`DAOEmprestimo.salvar`, na mesma transação (se a urna já não estiver emprestada, a lista inteira
é desfeita); devolve a mesma urna (sem troca), sem recibo, sem mover nada. Desmarcadas ficam
de fora e entram no resultado. Recusadas ficam de fora. Não aplica duas vezes.

**Depois.** Os planos gerados se efetivam em Planos como qualquer outro: F5
abre o editor com os patrimônios marcados; um `TRANSFERIR:POLO` vindo de uma
zona também aparece no **Retorno ao polo** dela (planos pendentes zona → polo).

## 5. Base que tornou isso possível: planos com patrimônios

Implementado junto, e pré-requisito das listas:

- `plano_patrimonios` (plano_id, patrimonio): patrimônios planejados,
  **opcionais e parciais** — um plano de 100 urnas pode ter 0, 10 ou 100.
  `DAOPlanos.salvarPlano(p, patrimonios)` recusa repetidos e mais patrimônios
  que a quantidade.
- **Efetivação editável** (`DAORascunho` + `EfetivacaoPanel`): F5 num plano
  carrega ele e os demais pendentes da mesma data e rota — itens com a
  quantidade, urnas planejadas marcadas e o número de urnas previstas. Tudo se
  edita: quantidade, itens tirados/acrescentados, urnas acrescentadas pelo
  patrimônio, desmarcadas. A quantidade efetivada de urnas é **sempre a das
  urnas marcadas** (o plano fica com esse número). Confirmar grava uma transação
  por material, efetiva os planos e numera o recibo, num commit.

## 6. Passos que faltam (próximas etapas)

Em ordem de valor:

1. **Busca em segundo plano.** Hoje a busca roda na thread da tela, com cursor
   de espera e timeouts de 15 s (conexão) e 30 s (leitura). Passar para um
   `SwingWorker` com botão de cancelar, se o site for lento.
2. **Busca ao abrir a aba** (opcional, desligável em Configurações): só o
   índice, mostrando "N listas novas no site" no título da aba, sem baixar.
3. **Ir para o plano gerado.** Depois de aplicar, um botão que leva à aba
   Planos com o plano selecionado (hoje a mensagem diz onde estão).
4. **Configurações.** Mover endereço e token do diálogo *Site…* para a área
   Configurações, ao lado das pastas, se a tela ganhar seções.
5. **Relatório da lista.** PDF da conferência (linhas, resultado, motivo) para
   devolver ao responsável da coleta as recusadas.
6. **Versão 2 do formato**, se o site precisar de itens sem patrimônio
   (quantidades): coluna `quantidade` e operação por item — exige combinar com
   o site (IMPORTACAO_WEB.md, seção 8).

## 7. Como testar sem o site

```
mkdir /tmp/site
# lista.csv com a identificação (codigo = um código aberto gerado no ASIdoBem)
sha256sum /tmp/site/lista.csv
# indice.csv: id;codigo;gerado_em;titulo;linhas;sha256;arquivo
```

No ASIdoBem, *Site…* → `file:///tmp/site/indice.csv` → **Buscar no site (F5)**.
`testes/interface/TesteListas.java` faz exatamente isso, numa cópia do banco.
