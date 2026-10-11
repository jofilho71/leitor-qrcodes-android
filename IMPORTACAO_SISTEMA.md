# Listas de patrimônio — implementação no ASIdoBem

O contrato com o site (código, arquivo, índice, operações) está em
[`IMPORTACAO_WEB.md`](IMPORTACAO_WEB.md). Este documento é o lado do ASIdoBem:
o que foi feito, onde está e os passos que faltam. Implementado em 10/10/2026.

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
                                                              Gerar planos e aplicar status
                                                              → planos pendentes com patrimônios
                                                              → Planos › Efetivar → transação + recibo
```

Princípios que guiaram o desenho:

- **A lista nunca move nada sozinha.** Movimentação vira **plano**; o plano se
  efetiva no editor de Planos, onde tudo ainda é editável. Só a troca de status
  (cadastro) é aplicada ao aplicar a lista.
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
| Preferência | `util/Config` | `listas.endereco` e `listas.token`, no arquivo da máquina (fora do banco); "Restaurar padrões" dos documentos não os apaga |
| Tela | `ui/panels/ListasPanel` | Aba **Movimentar › Listas**: códigos, receber (site, arquivo, configurar site), histórico, conferência, aplicar/descartar |
| Título da aba | `ui/panels/MovimentarPanel` | "Listas · N a tratar" (recebidas ainda não aplicadas nem descartadas) |
| Testes | `testes/interface/TesteListas` | Código, busca por `file://` (nova, outro código, SHA errado, índice malformado), segunda busca sem repetir, conferência linha a linha, aplicação, efetivação do plano gerado, código encerrado |

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

1. Baixa o índice (`Config.listasEndereco`, com o token se houver).
2. Para cada anúncio: código que não é desta base → conta como "de outros
   códigos", sem baixar; `id` já em `listas_recebidas` → "já recebida" (se o
   SHA-256 mudou, conta como "mudou no site", sem aviso repetido); senão baixa.
3. `receber`: lê o arquivo; confere SHA-256, `id` e `codigo` contra o anúncio;
   confere o código (desta base, aberto). Recusa → registra como `recusada`
   com o motivo (não volta a ser oferecida). Aceita → registra `recebida` com
   o conteúdo.

**Abrir arquivo.** O mesmo `receber`, sem anúncio (sem SHA-256 a conferir).

**Conferência** (`DAOListas.conferir`), sempre contra o cadastro **de hoje**:
erros de formato vêm do `ListaCSV`; depois, por linha: urna cadastrada (ou não,
em CADASTRAR), local atual (origem), zona de destino existente, já no destino,
status igual, empréstimo aberto, tamanho do patrimônio. Resultado
válida/aviso/recusada e o motivo.

**Aplicar** (`DAOListas.aplicar`, um commit): agrupa as linhas aplicáveis por
rota (local atual → destino) e cria **um plano pendente por rota**, com
quantidade = número de urnas e os patrimônios em `plano_patrimonios`;
observação "Lista <id> (código N): descrições". `STATUS` → `DAOUrnas.salvarUrna`
(grava `urna_eventos`), descrição acrescentada ao complemento. Marca a lista
`aplicada` com o resultado. Recusadas ficam de fora. Não aplica duas vezes.

**Depois.** Os planos gerados se efetivam em Planos como qualquer outro: F5
abre o editor com os patrimônios marcados; `RECOLHER` de uma zona também
aparece no **Retorno ao polo** dela (planos pendentes zona → polo).

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
