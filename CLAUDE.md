# CLAUDE.md

Instruções de contexto para o Claude Code trabalhar neste projeto. Leia antes de qualquer alteração.

## O que é

Utilitário Android de uso restrito (equipe treinada, sem UI autoexplicativa) para ler o **QR Code oficial do
TSE** das urnas no navegador do celular — câmera ao vivo ou fotos da galeria — escolher a operação de cada urna
e **publicar a lista** num repositório público do GitHub, de onde o ASIdoBem a coleta. Sem servidor próprio, sem build.

**Arquivo único**: todo o app (HTML + CSS + JS) vive em `index.html`, hospedado em GitHub Pages. Não há bundler,
`package.json` nem dependências. O único recurso externo é o fallback `jsQR` via CDN, carregado só se
`window.BarcodeDetector` não existir. Prefira sempre a solução mais simples que resolve o pedido.

## Documentação do projeto

- **`CLAUDE.md`** (este arquivo): para quem mexe no código. Regras de negócio, decisões de design e o porquê.
- **`README.md`**: visão geral, deploy, repositório de listas, tokens.
- **`MANUAL.md`**: manual da equipe em português simples. Ao mudar qualquer regra que afete o que o usuário
  vê ou faz, atualize também o `MANUAL.md`.
- `docs/superpowers/specs/` e `docs/superpowers/plans/`: spec e plano da integração com o ASIdoBem.
- `IMPORTACAO_WEB.md` / `IMPORTACAO_SISTEMA.md`: contrato do formato 1 (lado do site / lado do ASIdoBem).
  Não alterar por conta própria — mudanças são combinadas entre os projetos.

## Deploy

App: **GitHub Pages**, `index.html` da branch `master` de `jofilho71/leitor-qrcodes-android`. Commit local não
atualiza o site: é preciso `git push origin master`. Ao terminar uma mudança que o usuário vá querer ver no
ar, **pergunte se deve dar push** (ação pública) e avise que o Pages leva 1–2 min (Ctrl+Shift+R).

Listas: repositório público separado `jofilho71/asidobem-listas` (branch `main`), cujo conteúdo-modelo está em
`repositorio-listas/` (workflow + script do índice + README). Criar/alterar esse repositório e gerar tokens
são ações externas: só com confirmação do usuário.

## Fluxo do app

Telas: `inicio → codigo → config → leitura` (função `irPara`). Estado em `sessao = {codigo,
itens:[{codigo, operacao, descricao}]}` e `codigosVistos` (Set).

1. **Iniciar** verifica o token do aparelho (`verificarToken`: `GET` no repositório de listas; `permissions.push`
   explicitamente falso, 401/403/404 → bloqueia; rede/5xx → segue com aviso).
2. **Código** do ASIdoBem: 5 dígitos, `/^[1-9]\d{4}$/`. Aparece discreto no topo (decisão do usuário: menos espaço).
   Lista com código errado não é lida pelo ASIdoBem, mas continua no repositório para conferência offline.
3. **Config**: operação inicial (e zona, se Transferir; zona inválida bloqueia). **Não há** responsável nem local:
   o código já identifica a origem (removidos a pedido do usuário).
4. **Leitura**: câmera/galeria. Operação, zona/status e nota podem mudar durante a leitura (uma lista pode
   misturar operações). Rodapé: Excluir último (vermelho claro), Excluir tudo (`btn-cancelar`, vermelho escuro, confirma), Salvar,
   Compartilhar (cores padrão), Publicar (verde).
5. **Publicar** → `PUT` no repositório; sucesso limpa a sessão e volta a `inicio` (nova configuração).

## Aceitação de um QR (`processarCodigoDetectado`)

1. `format !== "qr_code"` → descarta em silêncio. **Código de barras nunca é lido** (decisão do usuário; QR
   tem correção de erro própria, barras lineares não).
2. Sem `IDEQ` (`parsearCampos`) → descarta em silêncio.
3. `"45"+IDEQ` fora de `PADRAO_PATRIMONIO = /^4551\d{6}$/` → **erro** (som + vibração).
4. `IDEQ` já em `codigosVistos` → **erro**. É a **única regra de recusa por repetição**; não há mais checagem de
   semelhança entre patrimônios (removida a pedido do usuário) nem dedup por tempo/janela para aceitação.
5. Operação inválida (zona de `TRANSFERIR` mal formada) → erro; a urna não entra no Set (corrigir a zona e reler aceita).
6. Aceito: grava o `IDEQ` **puro** (8 dígitos, sem prefixo) com operação e nota atuais.

Som/vibração: sucesso `[40,40,60]` + tons 880/1320 Hz; erro `[120]` + tom 180 Hz. Erro soa **uma vez por valor**
enquanto o mesmo QR continua na câmera (`recente`, janela de 2 s) — a câmera lê a cada ~320 ms. Na galeria cada
foto é independente. **Excluir último** libera o patrimônio no Set e bloqueia a câmera de readicioná-lo
enquanto o QR continuar à vista (`bloqueioCamera`).

## Operações e CSV (formato 1)

Operações do app: `TRANSFERIR:Z<n>|POLO`, `EMPRESTAR`, `STATUS:<status>`. Na tela o status é Laudo/Defeito/Pronta, mas o
valor gravado é o oficial do ASIdoBem: **Defeito → `STATUS:Defeituosa`**, **Laudo → `STATUS:Defeituosa` com a
descrição `LAUDO`** (ou `LAUDO - <nota>`), Pronta → `STATUS:Pronta` (`STATUS_OFICIAL`, `descricaoAtual`).

**Decisão do usuário (2026-10-11)**: o leitor só emite essas três operações; toda operação do leitor entra no
ASIdoBem como **plano** (depois efetivado). `EMPRESTAR` não consta do contrato original (`IMPORTACAO_WEB.md`): o
pedido de mudança ao ASIdoBem está em `docs/INTEGRACAO_ASIDOBEM.md` (§5). O índice não valida o vocabulário.

CSV (Salvar, Compartilhar e o conteúdo publicado são o mesmo, de `montarLista(seq)`): UTF-8 **sem BOM**, `;`,
`\n`; linha `#ASIDOBEM;formato=1;codigo=…;id=…;titulo=…;gerado_em=…`, cabeçalho
`patrimonio;operacao;descricao`, uma linha por item. Descrição ≤ 200 chars, sem `;`/quebra de linha
(`limparDescricao`). `id` = `aaaa-mm-dd-<código>-<seq>` (backup: `-HHMMSS` no lugar do seq). Sem `escaparCsv`: o contrato proíbe aspas/`;` nos valores. Limite local:
15.000 itens por lista.

## Publicação e token

- `PUT https://api.github.com/repos/jofilho71/asidobem-listas/contents/listas/<id>.csv` com `Bearer <token>` e
  **sem `sha`**: se o arquivo existe o GitHub responde 422 ("sha wasn't supplied") e o app tenta o próximo `seq`
  (até 99); 409 (envio simultâneo) repete o mesmo id até 3 vezes. Falhas mantêm a lista na tela. `publicando`
  impede toque duplo.
- O índice (`indice.csv`, com SHA-256) é gerado pelo workflow do repositório de listas; o celular não o toca.
  O ASIdoBem lê `https://raw.githubusercontent.com/jofilho71/asidobem-listas/main/indice.csv` sem token.
- **Token**: fine-grained, só no repositório de listas, *Contents: Read and write*, em `localStorage` (`lq.token`).
  Chega ao aparelho pelo link `…/leitor-qrcodes-android/#cfg=<token>` (o app guarda e apaga o fragmento da URL
  com `history.replaceState`) ou colado em Ajustes. **Nunca** no `index.html` nem em repositório. Um token por
  aparelho, revogáveis individualmente.

## Sessão salva

A cada item aceito/excluído a sessão vai para `localStorage` (`lq.sessao`); ao reabrir, `inicio` oferece
Retomar/Descartar. O conteúdo salvo é não confiável: `sessaoSalvaValida` valida a forma inteira e apaga o
que não passar. Sessão com 0 itens não é salva. Todo acesso a `localStorage` passa por `LS` (try/catch).

## Detecção

- **Preferência**: `BarcodeDetector` nativo com `formats: ["qr_code"]`.
- **Fallback**: `jsQR` via CDN (só QR — e só QR é o que o app quer). `garantirJsQR()` não guarda promise
  rejeitada em cache. A decodificação via jsQR está centralizada em `decodificarCanvasComJsQR(w, h)`.
- `BarcodeDetector` depende de Google Play Services no Android; não existe em Chromium headless (por isso os
  testes fazem stub).

## Câmera: falha ao iniciar

`iniciarCamera()` trata `getUserMedia()` rejeitando e `video.play()` rejeitando; os dois mostram erro em
`#erro-camera`. Não deixe o `play()` falhar em silêncio: já deixou a UI "ativa" com vídeo congelado.

## Interface

Utilitário de espaço mínimo: botões de ação só com ícone. Rodapé sempre visível na leitura. `#lista-itens` tem
`max-height` com scroll. Conteúdo lido entra via `innerHTML` **somente** após `escaparHtml()`. Status colorido
(`#pendencia` + borda de `#moldura`): branco "Esperando leitura", verde 1 s "Item incluído". Compartilhar usa a
Web Share API com arquivo; `AbortError` não gera mensagem.

## Testes

Playwright (Python) + pytest em `tests/`: `python3 -m pytest tests -v` (dependências em `requirements-teste.txt`;
`python3 -m playwright install chromium`). `tests/conftest.py` serve o `index.html` por HTTP local e injeta
stubs: `BarcodeDetector` (fila `window.__fila`, um lote por `detect()`), `getUserMedia`, `AudioContext`
(`window.__tons`), `navigator.vibrate` (`window.__vibracoes`) e a API do GitHub (`page.route`). O workflow do
índice é testado em `tests/test_indice.py`. Rode a suíte inteira antes de considerar uma mudança pronta.

## Convenções

- Nomes de variáveis, funções e comentários em **português**.
- Sem framework, sem TypeScript, sem transpilação — JS puro compatível com Chrome Android atual.
- Editar em blocos pequenos e testar cada mudança isoladamente.
