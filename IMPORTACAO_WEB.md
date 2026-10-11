# Listas de patrimônio pela internet — instruções para o site

**Para quem é este documento.** Para o projeto que vai **criar e publicar** as
listas de patrimônio que o ASIdoBem busca pela internet — um site (ou app) em
que o pessoal do polo e das zonas lê a plaqueta das urnas e diz o que fazer com
cada uma. Ele define o **contrato**: o código que autoriza a lista, o formato do
arquivo, o vocabulário de operações, onde os arquivos ficam e o que o ASIdoBem
recusa. Como o ASIdoBem implementa o lado dele está em
[`IMPORTACAO_SISTEMA.md`](IMPORTACAO_SISTEMA.md).

**Situação.** O lado do ASIdoBem está **implementado** (Movimentar › Listas).
Este é o **formato 1**. Qualquer mudança é combinada entre os projetos e entra
numa nova versão do formato (seção 8) — nunca por conta própria de um dos lados.

---

## 1. O princípio

> **A lista diz o quê e com qual patrimônio. O ASIdoBem decide de onde, confere, planeja e grava.**

O ASIdoBem controla o material de um polo de urnas eletrônicas: em que local
(o polo, uma zona eleitoral ou a "fronteira" TRE/Ajuste/Descarte) está cada
urna, identificada pelo número de **patrimônio**. Toda movimentação passa por
regras que o site **não precisa** (e não deve tentar) reproduzir:

- uma urna só sai de onde ela está no cadastro do ASIdoBem — por isso a lista
  **não informa a origem**; o ASIdoBem a tira do próprio cadastro;
- urna ainda não cadastrada só entra vinda de fora (pelo TRE);
- a gravação é **tudo ou nada**.

Uma lista **nunca grava movimentação sozinha**. No ASIdoBem ela é baixada,
conferida linha a linha e, quando o operador manda aplicar, as movimentações
viram **planos** com os patrimônios — que ele ainda pode editar e só depois
confirma como transação. (A troca de status, operação de cadastro, é aplicada
na hora em que o operador aplica a lista.)

## 2. O código de 5 dígitos

Toda lista tem de trazer um **código de 5 dígitos gerado pelo ASIdoBem**. É
assim que o sistema sabe que a lista foi pedida por ele, e não é de outro polo
nem de um arquivo qualquer.

1. No ASIdoBem, o operador clica em **Gerar código…** (Movimentar › Listas) e
   escreve para que é (ex.: "Coleta pós-eleição Zona 59"). Sai um número como
   **`48213`** — sempre de 10000 a 99999, nunca começa com zero.
2. No site, quem monta a lista **digita esse código** antes de começar (ou ao
   publicar). O site não valida o código contra nada: só o guarda e o escreve
   no arquivo (seção 3.1) e no índice (seção 4.1).
3. O ASIdoBem só aceita a lista se o código for **dele e estiver aberto**. O
   operador encerra o código quando a coleta acaba; listas que chegarem depois
   com ele são recusadas.

Um código pode autorizar **várias** listas (uma coleta dividida em partes).
Recomendações ao site:

- pedir o código **uma vez por sessão de coleta** e mostrá-lo grande na tela,
  para a pessoa conferir com o que o ASIdoBem mostrou;
- aceitar só 5 dígitos (sem espaço, ponto, letra);
- se o site atender **vários polos**, o código é o que separa as listas de cada
  um: o ASIdoBem de um polo ignora, sem baixar, as listas com códigos que não
  são dele.

O código não é senha: ele organiza e autoriza o recebimento. Se o site precisar
restringir o acesso, use o token da seção 4.3.

## 3. A lista

Arquivo de texto **CSV**: uma linha de **identificação**, o **cabeçalho** e uma
linha por patrimônio.

```
#ASIDOBEM;formato=1;codigo=48213;id=2026-10-20-z59-01;titulo=Coleta pós-eleição Zona 59;local=Z59;responsavel=Maria S.;gerado_em=2026-10-20T16:42:05-03:00
patrimonio;operacao;descricao
51250523;RECOLHER;Coletada no cartório após a eleição
51251189;RECOLHER;
51253188;STATUS:Defeituosa;Não liga — tela apagada
51254114;TRANSFERIR:Z59;Reposição de urna defeituosa
51260164;CADASTRAR;Urna nova, lote 2026 do TRE
```

### 3.1 A linha de identificação

Primeira linha do arquivo, começando com `#ASIDOBEM;`, seguida de pares
`chave=valor` separados por `;`, em qualquer ordem:

| Chave | Obrigatória | Conteúdo |
|---|---|---|
| `formato` | sim | `1` |
| `codigo` | sim | O código de 5 dígitos informado no site (seção 2) |
| `id` | sim | Identificador **único e imutável** da lista: letras, números e `-`, até 60. Sugestão: `aaaa-mm-dd-<local>-<seq>` |
| `titulo` | não | Uma linha que o operador lê para reconhecer a lista (até 80 caracteres) |
| `local` | não | Onde a coleta foi feita: `POLO` ou `Z<número da zona>`. Informativo — **não** é a origem |
| `responsavel` | não | Quem fez a coleta (nome curto) |
| `gerado_em` | não | Data e hora da publicação, ISO 8601 com fuso |

Os valores não podem conter `;` nem quebra de linha.

### 3.2 Regras do arquivo

| Regra | Valor |
|---|---|
| Codificação | **UTF-8**, sem BOM (o BOM é tolerado) |
| Separador | **ponto e vírgula** (`;`) |
| Fim de linha | LF ou CRLF |
| Linha 1 | identificação (seção 3.1) |
| Linha 2 | cabeçalho exato `patrimonio;operacao;descricao` (minúsculas, sem acento) |
| Colunas | sempre **3** por linha de dados — a descrição vazia ainda leva o segundo `;` |
| Aspas | **não usar**: a descrição não pode conter `;` nem quebra de linha |
| Linhas em branco | ignoradas |
| Tamanho | até **20.000 linhas** e **5 MB**; acima disso, dividir em mais de uma lista |
| Resposta HTTP | `text/csv; charset=utf-8` |

### 3.3 `patrimonio`

- **Sempre texto, nunca número.** Zeros à esquerda fazem parte do número.
  Cuidado com planilhas (Excel/LibreOffice), que convertem `051250001` em
  `51250001`: gere o CSV pelo programa, não por planilha.
- **Só dígitos**, sem espaço, ponto ou traço. Os patrimônios de urna em uso hoje
  têm **8 dígitos** (ex.: `51250523`); outro tamanho é aceito com aviso.
- **Um patrimônio aparece uma única vez por lista.** Repetido, **todas** as
  ocorrências são recusadas. Se duas coletas dizem coisas diferentes sobre a
  mesma urna, o site resolve antes de publicar.
- Ao ler a plaqueta (digitação ou código de barras), confira o formato na hora
  e mostre o número lido em fonte grande. A letra `O` no lugar do zero é o erro
  mais comum de digitação — e é recusado.

### 3.4 `operacao` — vocabulário fechado

Uma palavra em **MAIÚSCULAS, sem acento**, às vezes com um parâmetro depois de
`:` (sem espaços). **Só estas seis existem**; qualquer outra é recusada.

| Operação | O que pede | O que o ASIdoBem faz |
|---|---|---|
| `RECOLHER` | A urna volta ao polo | Plano **do local onde ela está para o polo**, com o patrimônio. Aparece também no **Retorno ao polo** daquela zona |
| `TRANSFERIR:<destino>` | A urna vai para outro local | Plano do local onde ela está para `<destino>` |
| `DEVOLVER_TRE` | A urna sai para o TRE | Plano do local onde ela está para o local virtual **TRE** |
| `DESCARTAR` | A urna foi sucateada/baixada | Plano do local onde ela está para o local virtual **Descarte** |
| `STATUS:<status>` | Mudou a condição da urna | Troca do status no cadastro, com registro no histórico da urna; **não move** a urna |
| `CADASTRAR` | Urna nova, ainda desconhecida | Plano de **entrada** TRE → polo; a urna é criada quando o plano for confirmado |

**`<destino>`** em `TRANSFERIR`: `POLO` (prefira `RECOLHER`) ou `Z<número da
zona>` — pelo número da zona, não pelo município: `Z59`, `Z146` (`Z059` =
`Z59`). `TRANSFERIR:TRE` e `TRANSFERIR:DESCARTE` são recusados: use
`DEVOLVER_TRE` e `DESCARTAR`.

**`<status>`** em `STATUS`, um destes (o ASIdoBem não diferencia maiúsculas e
acentos, mas publique assim):

```
Pronta · Defeituosa · Danificada · Sucateada · Nao Certificada · Sem Bateria · Indisponivel
```

`STATUS:Pronta` diz que a urna foi consertada.

Fora do vocabulário, de propósito: **itens sem patrimônio** (cabos, baterias,
cabines — quantidades continuam lançadas no ASIdoBem), **empréstimos** (não
movem material e o tomador não tem cadastro) e **origem** (seção 1).

### 3.5 `descricao`

Texto livre, opcional, **até 200 caracteres**, sem `;` e sem quebra de linha.
É o que o coletor quer registrar: defeito, quem entregou, lacre. No ASIdoBem:

- nas movimentações, as descrições vão para a **observação** do plano gerado;
- em `STATUS`, é acrescentada ao **complemento** do cadastro da urna.

Não coloque dados pessoais além do necessário (nome de quem entregou basta;
CPF e telefone não).

## 4. Publicação: o índice e as listas

As listas ficam num endereço **HTTPS** fixo, com um **índice**. O ASIdoBem lê o
índice, baixa só as listas **novas** com códigos dele e confere a integridade
antes de aceitar.

### 4.1 O índice

Endereço configurado no ASIdoBem (botão **Site…**), por exemplo
`https://exemplo.org/asidobem/indice.csv`. CSV, UTF-8, `;`, com o cabeçalho exato:

```
id;codigo;gerado_em;titulo;linhas;sha256;arquivo
2026-10-20-z59-01;48213;2026-10-20T16:42:05-03:00;Coleta pós-eleição Zona 59;262;9f2c…e1;listas/2026-10-20-z59-01.csv
2026-10-21-polo-01;48213;2026-10-21T09:10:00-03:00;Urnas novas do TRE;40;41aa…07;listas/2026-10-21-polo-01.csv
```

| Coluna | Conteúdo |
|---|---|
| `id` | O mesmo `id` da identificação da lista |
| `codigo` | O mesmo `codigo` da identificação da lista |
| `gerado_em` | Data e hora da publicação, ISO 8601 com fuso |
| `titulo` | Sem `;` |
| `linhas` | Quantidade de linhas de dados da lista |
| `sha256` | SHA-256 do arquivo da lista, em hexadecimal minúsculo (64 caracteres) |
| `arquivo` | Caminho relativo ao índice, ou URL HTTPS absoluta |

Ordem: mais recente primeiro. O índice pode listar só os últimos meses. Linha
malformada do índice é ignorada (e contada) — não derruba as outras.

### 4.2 Regras de publicação

1. **Lista publicada não muda.** Corrigir é publicar outra lista, com outro
   `id`. O ASIdoBem recusa um arquivo cujo SHA-256 não bate com o do índice, e
   ignora a mesma `id` com conteúdo diferente de um que já recebeu.
2. **Publicar a lista antes do índice.** O índice só cita o arquivo depois que
   ele estiver completo no servidor.
3. **Uma lista por coleta**, de um local, de um dia. Misturar locais funciona
   (cada urna sai de onde está), mas dificulta a conferência.
4. **Só HTTPS**, com certificado de uma autoridade reconhecida pelo **Java 8**
   das máquinas do polo. Teste o endereço com o próprio ASIdoBem antes de
   divulgar: Java 8 desatualizado não reconhece algumas autoridades recentes.
5. **Sem redirecionamento** e sem página de login no meio: a resposta ao GET é
   o próprio CSV (status 200).

### 4.3 Acesso

- **Endereço não divulgado**, só de leitura (caminho longo e aleatório); ou
- **Token**: o site exige o cabeçalho `Authorization: Bearer <token>`. O token é
  informado uma vez no ASIdoBem (botão **Site…**), fica na máquina, fora do
  banco, e nunca vai na URL. Responda **401/403** a token errado.

Só `GET`. O ASIdoBem não envia nada ao site.

### 4.4 Alternativa sem servidor

O ASIdoBem também aceita a lista como **arquivo** (botão *Abrir arquivo…*) ou
uma **pasta** como "site" (`file:///…/indice.csv`, com o índice e as listas
nela). A lista vale igual — com o código —, só que sem a conferência do
SHA-256 do índice no caso do arquivo avulso.

## 5. O que o ASIdoBem confere

Cada linha sai como **válida**, **com aviso** (segue; o operador vê) ou
**recusada** (fica de fora). Ao aplicar, só as recusadas ficam de fora.

| Situação | Resultado |
|---|---|
| Sem a linha de identificação, sem `codigo` de 5 dígitos ou sem `id` válido; cabeçalho diferente; mais de 20.000 linhas ou 5 MB | **Lista inteira recusada** |
| `formato` diferente de `1` | **Lista inteira recusada** |
| SHA-256 diferente do índice; `id` ou `codigo` do arquivo diferentes do índice | **Lista inteira recusada** (registrada, não volta a ser oferecida) |
| Código que não é deste ASIdoBem | Ignorada sem download (é de outro polo) |
| Código encerrado | **Lista inteira recusada** (registrada) |
| `id` já recebido antes | Não é baixada de novo (nem mostrada como novidade) |
| Linha com outra quantidade de colunas | Recusada |
| Patrimônio vazio ou com algo além de dígitos | Recusada |
| Patrimônio repetido na lista | Recusadas todas as ocorrências |
| Operação fora do vocabulário, ou parâmetro inválido | Recusada |
| Descrição com mais de 200 caracteres | Recusada |
| Zona de destino que não existe no cadastro | Recusada |
| `CADASTRAR` de patrimônio já cadastrado | Recusada (diz onde ele está) |
| Outra operação com patrimônio não cadastrado | Recusada |
| Movimentação para o local onde a urna já está | Recusada |
| Patrimônio com tamanho diferente de 8 | Aviso |
| `STATUS` igual ao status atual | Aviso (nada a mudar) |
| Urna em empréstimo aberto | Aviso |

## 6. Lista de verificação do site

- [ ] Pede o código de 5 dígitos e o escreve na identificação e no índice
- [ ] Gera o CSV por programa, em UTF-8, com `;`, identificação e cabeçalho exatos
- [ ] Patrimônio guardado e escrito como **texto**, só dígitos, zeros preservados
- [ ] Um patrimônio por lista; conflitos resolvidos antes de publicar
- [ ] Operações só do vocabulário da seção 3.4, em maiúsculas; zona por número (`Z59`)
- [ ] Descrição até 200 caracteres, sem `;` nem quebra de linha
- [ ] `id` único e nunca reutilizado; lista imutável depois de publicada
- [ ] SHA-256 calculado sobre os bytes exatos do arquivo publicado
- [ ] Lista publicada antes de entrar no índice; mais recente primeiro
- [ ] HTTPS aceito pelo Java 8 do polo; sem redirecionamento; 401/403 para token errado
- [ ] Testado com os casos da seção 7

## 7. Casos de teste

Com o código `48213` aberto no ASIdoBem, a urna `51250523` na Zona 59 e
Pronta, `51251189` no polo e `51269999` não cadastrada:

```
#ASIDOBEM;formato=1;codigo=48213;id=teste-01;titulo=Casos de teste
patrimonio;operacao;descricao
51250523;RECOLHER;Coleta pós-eleição
51251189;TRANSFERIR:Z59;
51269999;CADASTRAR;Urna nova, lote 2026
51251189;STATUS:Defeituosa;Repetida: recusada
051250523;RECOLHER;9 dígitos: aviso de tamanho, e recusada por não cadastrada
5125O523;RECOLHER;Letra O no lugar do zero: recusada
51250524;Recolher;Operação em minúsculas: recusada
51250525;TRANSFERIR:Z999;Zona inexistente: recusada
51250526;STATUS:Quebrada;Status fora da lista: recusada
51250527;TRANSFERIR:TRE;Use DEVOLVER_TRE: recusada
```

Resultado esperado: válidas só a 1ª linha de dados (`51250523`, RECOLHER) e a
3ª (`51269999`, CADASTRAR). A `51251189` aparece duas vezes, então **as duas**
são recusadas. As demais são recusadas pelos motivos da própria descrição.
Trocando o código por um que o ASIdoBem não gerou, a lista inteira é ignorada.

## 8. Versões do formato

Este é o **formato 1**. Muda de versão qualquer coisa que um leitor do formato
1 interpretaria errado: chave obrigatória nova, coluna nova, operação nova,
parâmetro novo, outra codificação. A mudança é combinada entre os projetos; o
site passa a publicar `formato=2`, e o ASIdoBem só lê as listas de uma versão
depois de atualizado para ela. Chaves **opcionais** novas na identificação não
mudam a versão: o ASIdoBem ignora as que não conhece.
