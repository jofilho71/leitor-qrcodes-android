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
O "site" hoje é o **leitor de QR Codes** (v1.2), que publica em
`https://raw.githubusercontent.com/jofilho71/asidobem-listas/main/indice.csv`
(o endereço padrão do ASIdoBem, sem token); o vocabulário da seção 3.4 é o que ele emite.

---

## 1. O princípio

> **Nota para o site:** o ASIdoBem trata a lista como uma *sugestão*: o operador pode corrigir, antes de aplicar,
> a operação, o destino, o status, o tomador e a descrição de qualquer linha (o patrimônio, nunca). Não há mudança
> de formato: o arquivo continua o mesmo, e o que o site mandou fica guardado no histórico. Mande o que foi coletado,
> mesmo impreciso; não tente "adivinhar" nomes completos ou destinos.

> **A lista diz o quê e com qual patrimônio. O ASIdoBem decide de onde, confere, planeja e grava.**

O ASIdoBem controla o material de um polo de urnas eletrônicas: em que local
(o polo, uma zona eleitoral ou a "fronteira" TRE/Ajuste/Descarte) está cada
urna, identificada pelo número de **patrimônio**. Toda movimentação passa por
regras que o site **não precisa** (e não deve tentar) reproduzir:

- uma urna só sai de onde ela está no cadastro do ASIdoBem — por isso a lista
  **não informa a origem**; o ASIdoBem a tira do próprio cadastro;
- urna ainda não cadastrada é recusada (o cadastro de urnas novas não vem por lista);
- a gravação é **tudo ou nada**.

Uma lista **nunca grava movimentação sozinha**. No ASIdoBem ela é baixada,
conferida linha a linha e, quando o operador manda aplicar, as movimentações
viram **planos** com os patrimônios — que ele ainda pode editar e só depois
confirma como transação. (A troca de status e o empréstimo valem na hora em que
o operador aplica a lista; o empréstimo não move a urna.)

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
#ASIDOBEM;formato=1;codigo=48213;id=2026-10-20-48213-01;titulo=Inventário 20/10;gerado_em=2026-10-20T16:42:05-03:00
patrimonio;operacao;descricao
51250523;TRANSFERIR:Z59;Reposição de urna defeituosa
51251189;TRANSFERIR:POLO;
51253188;STATUS:Defeituosa;LAUDO - tela apagada
51254114;STATUS:Pronta;
51260164;EMPRESTAR;Maria Souza
```

### 3.1 A linha de identificação

Primeira linha do arquivo, começando com `#ASIDOBEM;`, seguida de pares
`chave=valor` separados por `;`, em qualquer ordem:

| Chave | Obrigatória | Conteúdo |
|---|---|---|
| `formato` | sim | `1` |
| `codigo` | sim | O código de 5 dígitos informado no site (seção 2) |
| `id` | sim | Identificador **único e imutável** da lista: letras, números e `-`, até 60. O leitor usa `aaaa-mm-dd-<codigo>-<seq 2 dígitos>` |
| `titulo` | não | Uma linha que o operador lê para reconhecer a lista (até 80 caracteres) |
| `local` | não | Onde a coleta foi feita: `POLO` ou `Z<número da zona>`. Informativo — **não** é a origem. O leitor v1.2 **não envia** |
| `responsavel` | não | Quem fez a coleta (nome curto). O leitor v1.2 **não envia** |
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
`:` (sem espaços). **Só estas existem**; qualquer outra (inclusive as antigas
`RECOLHER`, `DEVOLVER_TRE`, `DESCARTAR` e `CADASTRAR`) é recusada como "fora do vocabulário".

| Operação | O que pede | O que o ASIdoBem faz |
|---|---|---|
| `TRANSFERIR:<destino>` | A urna vai para outro local | **Plano** pendente do local onde ela está para `<destino>` (a origem vem do cadastro, nunca do arquivo) |
| `STATUS:<status>` | Mudou a condição da urna | Troca do status no cadastro, **na hora de aplicar**, com registro no histórico da urna; **não move** a urna |
| `LEITURA` | A urna foi apenas lida; a `descricao` é a observação do técnico (relação, questão técnica, lacre…) | **Nada**: não move, não troca status, não empresta. A linha aparece na conferência e vai no CSV baixado. Urna não cadastrada é só um aviso. Lista só de `LEITURA` pode ser "aplicada" (fica registrada como tratada) |
| `EMPRESTAR` | A urna foi emprestada | **Empréstimo** criado na hora de aplicar, com a data do dia; a urna **não muda de local**. O tomador é a `descricao`, editável na tela de importação; sem tomador, a linha é recusada. Se a urna **já estiver emprestada**, a mesma linha vira **devolução** ao tomador original, com a data de hoje (editável e desmarcável na tela de importação); a `descricao` não é exigida e, se for diferente do tomador, gera aviso |

**`<destino>`** em `TRANSFERIR`: `POLO` ou `Z<número da zona>` — pelo número da
zona, não pelo município: `Z59`, `Z146` (`Z059` = `Z59`). Qualquer outro destino
(`TRE`, `DESCARTE`…) é recusado.

**`<status>`** em `STATUS`, um destes (o ASIdoBem não diferencia maiúsculas e
acentos, mas publique assim):

```
Pronta · Defeituosa
```

`STATUS:Pronta` diz que a urna foi consertada. **Laudo** e **Defeito** chegam
como `STATUS:Defeituosa`; o laudo leva `LAUDO` (ou `LAUDO - <nota>`) na `descricao`.
Os demais status do cadastro não vêm por lista.

`EMPRESTAR` e `LEITURA` não levam parâmetro (`EMPRESTAR:Maria` e `LEITURA:x` são recusados). Não há operação de
devolução: `EMPRESTAR` de urna que já está emprestada é tratada como devolução (leitor v1.3).

Fora do vocabulário, de propósito: **itens sem patrimônio** (cabos, baterias,
cabines — quantidades continuam lançadas no ASIdoBem) e **origem** (seção 1).

### 3.5 `descricao`

Texto livre, opcional, **até 200 caracteres**, sem `;` e sem quebra de linha.
É o que o coletor quer registrar: defeito, quem entregou, lacre. No ASIdoBem:

- nas transferências, as descrições vão para a **observação** do plano gerado;
- em `STATUS`, é acrescentada ao **complemento** do cadastro da urna;
- em `EMPRESTAR`, é o **tomador** do empréstimo.

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
2026-10-21-48213-02;48213;2026-10-21T09:10:00-03:00;Inventário 21/10;40;41aa…07;listas/2026-10-21-48213-02.csv
2026-10-20-48213-01;48213;2026-10-20T16:42:05-03:00;Inventário 20/10;262;9f2c…e1;listas/2026-10-20-48213-01.csv
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
| Operação ou status fora do vocabulário, ou parâmetro inválido | Recusada |
| Descrição com mais de 200 caracteres | Recusada |
| Zona de destino que não existe no cadastro | Recusada |
| Patrimônio não cadastrado | Recusada |
| Transferência para o local onde a urna já está | Recusada |
| `EMPRESTAR` sem tomador | Recusada ("sem tomador"); preencher a coluna Tomador na tela libera a linha |
| `EMPRESTAR` de urna em local virtual | Recusada (a edição do tomador não resolve) |
| `EMPRESTAR` de urna já emprestada | **Devolução** ao tomador original (aviso se a `descricao` for diferente do tomador); o usuário pode desmarcá-la |
| Patrimônio com tamanho diferente de 8 | Aviso |
| `STATUS` igual ao status atual | Aviso (nada a mudar) |
| `TRANSFERIR` ou `STATUS` de urna em empréstimo aberto | Aviso |

## 6. Lista de verificação do site

- [ ] Pede o código de 5 dígitos e o escreve na identificação e no índice
- [ ] Gera o CSV por programa, em UTF-8, com `;`, identificação e cabeçalho exatos
- [ ] Patrimônio guardado e escrito como **texto**, só dígitos, zeros preservados
- [ ] Um patrimônio por lista; conflitos resolvidos antes de publicar
- [ ] Operações só do vocabulário da seção 3.4, em maiúsculas; zona por número (`Z59`); `EMPRESTAR` com o tomador na descrição
- [ ] Descrição até 200 caracteres, sem `;` nem quebra de linha
- [ ] `id` único e nunca reutilizado; lista imutável depois de publicada
- [ ] SHA-256 calculado sobre os bytes exatos do arquivo publicado
- [ ] Lista publicada antes de entrar no índice; mais recente primeiro
- [ ] HTTPS aceito pelo Java 8 do polo; sem redirecionamento; 401/403 para token errado
- [ ] Testado com os casos da seção 7

## 7. Casos de teste

Com o código `48213` aberto no ASIdoBem, a urna `51250523` na Zona 59 e
Pronta, `51251189` no polo, `51253188` no polo e `51269999` não cadastrada:

```
#ASIDOBEM;formato=1;codigo=48213;id=teste-01;titulo=Casos de teste
patrimonio;operacao;descricao
51250523;TRANSFERIR:POLO;Coleta pós-eleição
51251189;TRANSFERIR:Z59;
51253188;STATUS:Defeituosa;LAUDO
51250524;EMPRESTAR;Maria Souza
51250525;EMPRESTAR;
51250526;RECOLHER;Fora do vocabulário: recusada
51251189;STATUS:Pronta;Repetida: recusada
051250523;TRANSFERIR:POLO;9 dígitos: aviso de tamanho, e recusada por não cadastrada
5125O523;TRANSFERIR:POLO;Letra O no lugar do zero: recusada
51250527;Transferir:POLO;Operação em minúsculas: recusada
51250528;TRANSFERIR:Z999;Zona inexistente: recusada
51250529;STATUS:Quebrada;Status fora da lista: recusada
51250530;TRANSFERIR:TRE;Destino fora do vocabulário: recusada
51269999;EMPRESTAR;Urna não cadastrada: recusada
```

Se uma urna da lista já estiver emprestada (por exemplo `51250524` com Maria Souza),
a linha `EMPRESTAR` dela é uma **devolução** a Maria Souza, não um empréstimo novo.

Resultado esperado: válidas a 1ª (`51250523`), a 3ª (`51253188`) e a 4ª
(`51250524`, se estiver cadastrada e livre). A `51251189` aparece duas vezes,
então **as duas** são recusadas; o `EMPRESTAR` sem tomador (`51250525`) também
é recusado, mas passa a valer se o tomador for preenchido na tela. As demais são
recusadas pelos motivos da própria descrição.
Trocando o código por um que o ASIdoBem não gerou, a lista inteira é ignorada.

## 8. Versões do formato

Este é o **formato 1**. Muda de versão qualquer coisa que um leitor do formato
1 interpretaria errado: chave obrigatória nova, coluna nova, operação nova,
parâmetro novo, outra codificação. (Exceção combinada, 2026-10-11: ao adotar o
leitor v1.2 o vocabulário foi redefinido — saem `RECOLHER`, `DEVOLVER_TRE`,
`DESCARTAR`, `CADASTRAR` e os status além de Pronta/Defeituosa; entra `EMPRESTAR` —
sem mudar o número do formato, porque não havia listas em circulação. Terceira exceção combinada, 2026-10-15: leitor **v1.5** e ASIdoBem **0.10.0** — entra `LEITURA` (só observação, sem efeito no cadastro); o número do formato não muda porque um ASIdoBem anterior recusa a linha como "fora do vocabulário", sem gravar nada errado, e o ASIdoBem é atualizado antes de o leitor passar a emitir. Segunda exceção combinada, 2026-10-12: leitor **v1.3** — `EMPRESTAR` de urna já emprestada passa a ser devolução; o formato do arquivo e o número do formato não mudam, só o efeito.) A mudança é combinada entre os projetos; o
site passa a publicar `formato=2`, e o ASIdoBem só lê as listas de uma versão
depois de atualizado para ela. Chaves **opcionais** novas na identificação não
mudam a versão: o ASIdoBem ignora as que não conhece.
