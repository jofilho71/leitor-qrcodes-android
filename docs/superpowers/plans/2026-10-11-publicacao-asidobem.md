# Publicação de listas para o ASIdoBem — Plano de Implementação

> **Para agentes:** SUB-SKILL OBRIGATÓRIA: use superpowers:subagent-driven-development (recomendado) ou superpowers:executing-plans para executar este plano tarefa a tarefa. Os passos usam checkbox (`- [ ]`).

**Objetivo:** transformar o leitor em um app só de Inventário/QR com fluxo guiado por código, operações do contrato e publicação das listas (formato 1) em um repositório público do GitHub, de onde o ASIdoBem as coleta.

**Arquitetura:** `index.html` (arquivo único, sem build) vira uma máquina de telas (`inicio → codigo → config → leitura`) e publica via `PUT` na API de conteúdo do GitHub com um token fine-grained guardado no aparelho. Um repositório separado (`asidobem-listas`) recebe `listas/<id>.csv`; um workflow do GitHub Actions regenera o `indice.csv` (com SHA-256), então o ASIdoBem não muda.

**Tecnologias:** HTML/CSS/JS puro (Chrome Android), Web Audio API, `fetch`, `localStorage`; Python 3 (stdlib) para o gerador de índice; GitHub Actions; testes com Playwright (Python) + pytest.

**Spec:** `docs/superpowers/specs/2026-10-11-publicacao-asidobem-design.md`

## Restrições globais

- Arquivo único `index.html`, sem framework, sem TypeScript, sem bundler, sem `package.json`; JS compatível com Chrome Android atual.
- Nomes de variáveis, funções e comentários em **português**.
- Só QR (`format === "qr_code"`); código de barras **nunca** é lido.
- Valor gravado = `IDEQ` puro (8 dígitos); `PADRAO_PATRIMONIO = /^4551\d{6}$/` aplicado a `"45" + IDEQ`.
- Única recusa por repetição: patrimônio já lido **na sessão** (sem checagem de semelhança). `PADRAO_PATRIMONIO` continua valendo (validação de formato, não de semelhança).
- Código do ASIdoBem: `/^[1-9]\d{4}$/` (10000–99999).
- Formato 1 do CSV: UTF-8 sem BOM, `;`, linha `#ASIDOBEM;formato=1;codigo=…;id=…`, cabeçalho exato `patrimonio;operacao;descricao`, 3 colunas, descrição ≤ 200 caracteres sem `;`/quebra de linha, até 15.000 linhas no app (20.000 no contrato).
- Operações: `RECOLHER`, `TRANSFERIR:Z<n>|POLO`, `DEVOLVER_TRE`, `DESCARTAR`, `STATUS:<status>`, `CADASTRAR`. Status: `Pronta, Defeituosa, Danificada, Sucateada, Nao Certificada, Sem Bateria, Indisponivel`.
- `id` da lista: `aaaa-mm-dd-<local em minúsculas ou sem-local>-<seq 2 dígitos>`, letras/números/`-`, ≤ 60.
- Repositório de listas: `jofilho71/asidobem-listas` (público, branch `main`); ASIdoBem lê `https://raw.githubusercontent.com/jofilho71/asidobem-listas/main/indice.csv`.
- Token: `github_pat_…` fine-grained, restrito ao repositório, em `localStorage` (`lq.token`); **nunca** no `index.html`. Link de configuração: `#cfg=<token>`, fragmento removido logo após ler.
- Conteúdo lido é texto não confiável: `escaparHtml()` antes de qualquer `innerHTML`.
- Toda leitura/gravação de `localStorage` dentro de `try/catch`; o app funciona sem ele.
- `git push` do app **só com confirmação do usuário** (ação pública); criar repositório/token no GitHub também só com confirmação. Commits locais são livres.
- Não tocar em `IMPORTACAO*.md` nem em `index (11).html` (cópia antiga, não versionada); usar `git add` com caminhos explícitos.
- Mensagens de commit terminam com `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`.

## Foco da revisão

Entradas que a spec não nomeia mas que mais provavelmente quebram o uso (cada uma tem teste na tarefa dona):

1. **Excluir último com o QR ainda na frente da câmera** — o próximo frame não pode readicionar o item (Tarefa 3).
2. **Sessão salva corrompida ou com formato inválido** — ignorada, sem exceção, sem travar o Iniciar (Tarefa 4).
3. **Toque duplo em Publicar** — um único `PUT` (Tarefa 7).
4. **Texto com acento, emoji, `;` e travessão em nota/responsável** — CSV publicado idêntico ao esperado em UTF-8 (Tarefa 7, e `;` na Tarefa 2).
5. **Mais de 15.000 itens** — Publicar recusa localmente sem enviar nada (Tarefa 7).
6. Mesmo `IDEQ` em QRs com outros campos diferentes, e QR com espaço/quebra de linha no final (Tarefa 2).

---

## Estrutura de arquivos

| Arquivo | Responsabilidade |
|---|---|
| `index.html` (modificar) | App inteiro: CSS, telas, leitura, sessão, CSV, sons, token, publicação |
| `tests/conftest.py` (criar) | Servidor HTTP local, stubs (detector, câmera, áudio, vibração), simulação da API do GitHub, classe `App` |
| `tests/test_fluxo.py` (criar) | Telas, código, configuração |
| `tests/test_leitura.py` (criar) | Aceitação de QR, operações, lista em tela, CSV, galeria, falha de câmera |
| `tests/test_edicao.py` (criar) | Excluir último, Cancelar |
| `tests/test_sessao.py` (criar) | Sessão salva e retomada |
| `tests/test_sons.py` (criar) | Sons e vibrações |
| `tests/test_token.py` (criar) | Link de configuração, ajustes, verificação ao Iniciar |
| `tests/test_publicar.py` (criar) | Publicação |
| `tests/test_indice.py` (criar) | `gerar_indice.py` |
| `requirements-teste.txt`, `.gitignore` (criar) | Dependências de teste; ignorar caches |
| `repositorio-listas/` (criar) | Conteúdo do repositório `asidobem-listas`: `.github/workflows/indice.yml`, `scripts/gerar_indice.py`, `listas/.gitkeep`, `README.md` |
| `CLAUDE.md`, `MANUAL.md`, `README.md` (reescrever) | Documentação |

---

### Tarefa 1: Infraestrutura de testes

**Arquivos:**
- Criar: `requirements-teste.txt`, `.gitignore`, `tests/conftest.py`, `tests/test_fluxo.py` (só um teste de fumaça por enquanto)

**Interfaces:**
- Produz (usado por todas as tarefas): fixture `app` (instância de `App`) com métodos `abrir(token=TOKEN_TESTE, hash="")`, `iniciar(codigo="48213", responsavel=None, local=None)`, `ligar_camera()`, `enfileirar(*lotes)`, `esperar_fila(extra=700)`, `itens()` → `[[codigo, operacao], …]`, `baixar_csv()` → `str`, `csv_publicado(i=-1)` → `str`, `det_qr(ideq, vere="1")`, `det_barra(valor)`; atributos `page`, `puts`, `respostas_put`, `status_get`, `push`, `rede_caida`, `atraso_put`, `erros_pagina`. Constantes `TOKEN_TESTE`, `REPO`, `PNG_1x1`, `RAIZ`.
- Stubs injetados em toda página: `window.__fila` (cada `detect()` consome um lote), `window.__tons` (frequências de osciladores iniciados), `window.__vibracoes`.

- [ ] **Passo 1: Instalar dependências de teste**

Crie `requirements-teste.txt`:

```
playwright
pytest
```

Crie `.gitignore`:

```
__pycache__/
.pytest_cache/
```

Execute:

```bash
cd /home/jayme/Projects/leitor-qrcodes-android
python3 -m pip install -r requirements-teste.txt
python3 -m playwright install chromium
```

Esperado: Playwright e Chromium instalados (precisa de internet; é ferramenta de desenvolvimento, não entra no app).

- [ ] **Passo 2: Escrever o `conftest.py`**

Crie `tests/conftest.py`:

```python
import base64
import functools
import http.server
import json
import pathlib
import threading
import time

import pytest
from playwright.sync_api import sync_playwright

RAIZ = pathlib.Path(__file__).resolve().parent.parent
TOKEN_TESTE = "github_pat_TESTE0123456789ABCDEFGH"
REPO = "jofilho71/asidobem-listas"
PNG_1x1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
)

INIT_STUBS = """
window.__fila = [];
window.__tons = [];
window.__vibracoes = [];
window.BarcodeDetector = class {
  constructor(o) {}
  static getSupportedFormats() { return Promise.resolve(['qr_code']); }
  async detect(source) { return window.__fila.length ? window.__fila.shift() : []; }
};
if (!navigator.mediaDevices) {
  Object.defineProperty(navigator, 'mediaDevices', { value: {}, configurable: true });
}
navigator.mediaDevices.getUserMedia = async () => {
  const c = document.createElement('canvas');
  c.width = 320; c.height = 240;
  c.getContext('2d').fillRect(0, 0, 320, 240);
  return c.captureStream(15);
};
navigator.vibrate = (p) => { window.__vibracoes.push(p); return true; };
window.AudioContext = class {
  constructor() { this.state = 'running'; this.currentTime = 0; this.destination = {}; }
  resume() { return Promise.resolve(); }
  createGain() {
    return { gain: { setValueAtTime() {}, exponentialRampToValueAtTime() {} }, connect() {} };
  }
  createOscillator() {
    const o = { type: '', frequency: { value: 0 }, connect() {}, stop() {} };
    o.start = () => window.__tons.push(o.frequency.value);
    return o;
  }
};
"""


class _Silencioso(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


@pytest.fixture(scope="session")
def url_base():
    handler = functools.partial(_Silencioso, directory=str(RAIZ))
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{srv.server_address[1]}/index.html"
    srv.shutdown()


@pytest.fixture(scope="session")
def browser():
    with sync_playwright() as p:
        b = p.chromium.launch(args=["--use-fake-ui-for-media-stream"])
        yield b
        b.close()


@pytest.fixture
def contexto(browser):
    c = browser.new_context(permissions=["camera"], viewport={"width": 390, "height": 780})
    c.route("https://cdn.jsdelivr.net/**", lambda r: r.abort())
    yield c
    c.close()


class App:
    def __init__(self, contexto, url):
        self.contexto = contexto
        self.url = url
        self.page = None
        self.erros_pagina = []
        self.puts = []
        self.respostas_put = [(201, {})]
        self.status_get = 200
        self.push = True
        self.rede_caida = False
        self.atraso_put = 0

    # ---- simulação da API do GitHub ----
    def _github(self, route, request):
        cors = {
            "access-control-allow-origin": "*",
            "access-control-allow-headers": "authorization,content-type,accept",
            "access-control-allow-methods": "GET,PUT,OPTIONS",
        }
        if self.rede_caida:
            return route.abort()
        if request.method == "OPTIONS":
            return route.fulfill(status=204, headers=cors)
        if request.method == "GET":
            return route.fulfill(
                status=self.status_get, headers=cors, content_type="application/json",
                body=json.dumps({"permissions": {"push": self.push}}),
            )
        if request.method == "PUT":
            if self.atraso_put:
                time.sleep(self.atraso_put)
            self.puts.append({
                "url": request.url,
                "auth": request.headers.get("authorization"),
                "corpo": json.loads(request.post_data),
            })
            if len(self.respostas_put) > 1:
                status, corpo = self.respostas_put.pop(0)
            else:
                status, corpo = self.respostas_put[0]
            return route.fulfill(
                status=status, headers=cors, content_type="application/json", body=json.dumps(corpo)
            )
        return route.continue_()

    def csv_publicado(self, i=-1):
        return base64.b64decode(self.puts[i]["corpo"]["content"]).decode("utf-8")

    # ---- página ----
    def abrir(self, token=TOKEN_TESTE, hash=""):
        self.page = self.contexto.new_page()
        self.page.on("pageerror", lambda e: self.erros_pagina.append(str(e)))
        self.page.add_init_script(INIT_STUBS)
        if token:
            literal = json.dumps(json.dumps(token))
            self.page.add_init_script(
                "try{if(!localStorage.getItem('lq.token'))localStorage.setItem('lq.token'," + literal + ")}catch(e){}"
            )
        self.page.route("https://api.github.com/**", self._github)
        self.page.goto(self.url + hash)
        return self.page

    def iniciar(self, codigo="48213", responsavel=None, local=None):
        p = self.page
        p.click("#btn-iniciar")
        p.fill("#input-codigo", codigo)
        p.click("#btn-codigo-ok")
        if responsavel is not None:
            p.fill("#input-responsavel", responsavel)
        if local is not None:
            p.fill("#input-local", local)
        p.click("#btn-config-ok")
        p.wait_for_selector("#tela-leitura:not([hidden])")

    def ligar_camera(self):
        self.page.click("#btn-camera")
        self.page.wait_for_selector("body.camera-ativa")

    def enfileirar(self, *lotes):
        self.page.evaluate("l => window.__fila.push(...l)", [list(l) for l in lotes])

    def esperar_fila(self, extra=700):
        self.page.wait_for_function("window.__fila.length === 0", timeout=20000)
        self.page.wait_for_timeout(extra)

    def itens(self):
        return self.page.eval_on_selector_all(
            "#lista-itens .item",
            "els => els.map(e => [e.querySelector('.codigo').textContent, e.querySelector('.op').textContent])",
        )

    def baixar_csv(self):
        with self.page.expect_download() as d:
            self.page.click("#btn-csv")
        return pathlib.Path(d.value.path()).read_bytes().decode("utf-8")

    @staticmethod
    def det_qr(ideq, vere="1"):
        return {"rawValue": f"APLC:TSE APLF:QRC.PATR VERE:{vere} TPEQ:UE MDEQ:UE2020 IDEQ:{ideq}",
                "format": "qr_code"}

    @staticmethod
    def det_barra(valor):
        return {"rawValue": valor, "format": "code_128"}


@pytest.fixture
def app(contexto, url_base):
    return App(contexto, url_base)
```

- [ ] **Passo 3: Teste de fumaça (deve falhar, a página nova ainda não existe)**

Crie `tests/test_fluxo.py`:

```python
def test_inicio_mostra_so_iniciar(app):
    app.abrir()
    assert app.page.is_visible("#btn-iniciar")
    assert not app.page.is_visible("#tela-leitura")
    assert not app.page.is_visible("#rodape")
```

- [ ] **Passo 4: Rodar e ver falhar**

```bash
python3 -m pytest tests/test_fluxo.py -v
```

Esperado: FAIL (`#btn-iniciar` não existe na página atual). Isso confirma que a infraestrutura sobe a página e roda o teste.

- [ ] **Passo 5: Commit**

```bash
git add requirements-teste.txt .gitignore tests/conftest.py tests/test_fluxo.py
git commit -m "test: infraestrutura Playwright com stubs de detector, câmera, áudio e API do GitHub" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Tarefa 2: Núcleo do app — telas, aceitação de QR, operações, CSV formato 1

Substitui o `index.html` inteiro. Remove o modo Bateria, a leitura de código de barras, a checagem de semelhança e as categorias antigas. O rodapé aqui tem só contador, Salvar e Compartilhar (Excluir/Cancelar/Publicar entram nas Tarefas 3 e 7).

**Arquivos:**
- Modificar (reescrever): `index.html`
- Testar: `tests/test_fluxo.py`, `tests/test_leitura.py`

**Interfaces:**
- Consome: fixture `app` da Tarefa 1.
- Produz (ids/funções que as próximas tarefas estendem): ids `tela-inicio/codigo/config/leitura`, `btn-iniciar`, `aviso-inicio`, `input-codigo`, `erro-codigo`, `btn-codigo-ok`, `btn-codigo-voltar`, `input-responsavel`, `input-local`, `slot-config`, `erro-config`, `btn-config-ok`, `btn-config-voltar`, `bloco-operacao` (`select-operacao`, `input-zona`, `select-status`, `texto-livre`), `lista-itens`, `rodape` (`contador-texto`, `btn-csv`, `btn-compartilhar`); funções JS internas `irPara(nome)`, `processarCodigoDetectado(codigo, origem)`, `sinalizar(tipo)` ("sucesso"|"erro"), `montarLista(seq)` → `{id, csv}`, `atualizarContador()`, `mostrarErroTemporario(msg, ms)`, `LS.ler/gravar/apagar`, `normalizarDestino`, `operacaoAtual()`, `limparDescricao`; estado `sessao = {codigo, responsavel, local, itens:[{codigo, operacao, descricao}]}` e `codigosVistos` (Set).

- [ ] **Passo 1: Escrever os testes de fluxo**

Substitua o conteúdo de `tests/test_fluxo.py`:

```python
import pytest


def test_inicio_mostra_so_iniciar(app):
    app.abrir()
    assert app.page.is_visible("#btn-iniciar")
    assert not app.page.is_visible("#tela-leitura")
    assert not app.page.is_visible("#rodape")


@pytest.mark.parametrize("codigo", ["", "1234", "123456", "01234", "0000", "abcde", "9999"])
def test_codigo_invalido_nao_avanca(app, codigo):
    app.abrir()
    app.page.click("#btn-iniciar")
    app.page.fill("#input-codigo", codigo)
    app.page.click("#btn-codigo-ok")
    assert app.page.is_visible("#tela-codigo")
    assert "inválido" in app.page.inner_text("#erro-codigo")


@pytest.mark.parametrize("codigo", ["10000", "48213", "99999"])
def test_codigo_valido_avanca_e_aparece_grande(app, codigo):
    app.abrir()
    app.page.click("#btn-iniciar")
    app.page.fill("#input-codigo", codigo)
    app.page.click("#btn-codigo-ok")
    assert app.page.is_visible("#tela-config")
    assert app.page.inner_text("#codigo-grande") == f"Código {codigo}"


def test_voltar_da_tela_de_codigo_e_da_config(app):
    app.abrir()
    app.page.click("#btn-iniciar")
    app.page.click("#btn-codigo-voltar")
    assert app.page.is_visible("#btn-iniciar")
    app.page.click("#btn-iniciar")
    app.page.fill("#input-codigo", "48213")
    app.page.click("#btn-codigo-ok")
    app.page.click("#btn-config-voltar")
    assert app.page.is_visible("#tela-codigo")
    assert not app.page.is_visible("#codigo-grande")


def test_responsavel_e_local_lembrados_no_aparelho(app):
    app.abrir()
    app.iniciar(responsavel="Maria S.", local="z059")
    app.page.reload()
    app.page.click("#btn-iniciar")
    app.page.fill("#input-codigo", "48213")
    app.page.click("#btn-codigo-ok")
    assert app.page.input_value("#input-responsavel") == "Maria S."
    assert app.page.input_value("#input-local") == "Z59"


def test_local_invalido_bloqueia(app):
    app.abrir()
    app.page.click("#btn-iniciar")
    app.page.fill("#input-codigo", "48213")
    app.page.click("#btn-codigo-ok")
    app.page.fill("#input-local", "Zona 5")
    app.page.click("#btn-config-ok")
    assert app.page.is_visible("#tela-config")
    assert "Local inválido" in app.page.inner_text("#erro-config")


def test_leitura_mostra_codigo_operacao_e_camera(app):
    app.abrir()
    app.iniciar(codigo="48213")
    assert app.page.is_visible("#btn-camera")
    assert app.page.is_visible("#bloco-operacao")
    assert app.page.is_visible("#rodape")
    assert app.page.inner_text("#codigo-grande") == "Código 48213"


def test_operacao_visivel_ja_na_configuracao(app):
    app.abrir()
    app.page.click("#btn-iniciar")
    app.page.fill("#input-codigo", "48213")
    app.page.click("#btn-codigo-ok")
    assert app.page.is_visible("#slot-config #bloco-operacao")
```

- [ ] **Passo 2: Escrever os testes de leitura**

Crie `tests/test_leitura.py`:

```python
import re

import pytest

from conftest import PNG_1x1, App


def lendo(app, **kw):
    app.abrir()
    app.iniciar(**kw)
    app.ligar_camera()


def test_aceita_qr_valido_e_grava_ideq_puro(app):
    lendo(app)
    app.enfileirar([App.det_qr("51432890")])
    app.esperar_fila()
    assert app.itens() == [["51432890", "RECOLHER"]]
    assert "1" in app.page.inner_text("#contador-texto")


def test_codigo_de_barras_nunca_e_lido(app):
    lendo(app)
    app.enfileirar([App.det_barra("4551432890")], [App.det_barra("51432890")])
    app.esperar_fila()
    assert app.itens() == []


@pytest.mark.parametrize("bruto", ["https://exemplo.com/x", "APLC:TSE APLF:QRC.PATR", "qualquer texto"])
def test_qr_sem_ideq_e_ignorado(app, bruto):
    lendo(app)
    app.enfileirar([{"rawValue": bruto, "format": "qr_code"}])
    app.esperar_fila()
    assert app.itens() == []


@pytest.mark.parametrize("ideq", ["12345678", "5143289", "514328901", "41432890", "5143289A"])
def test_ideq_fora_do_padrao_e_ignorado(app, ideq):
    lendo(app)
    app.enfileirar([App.det_qr(ideq)])
    app.esperar_fila()
    assert app.itens() == []


def test_frames_repetidos_contam_uma_vez(app):
    lendo(app)
    app.enfileirar(*[[App.det_qr("51432890")] for _ in range(5)])
    app.esperar_fila()
    assert len(app.itens()) == 1


def test_repetido_na_sessao_e_descartado_mesmo_depois_de_outro(app):
    lendo(app)
    app.enfileirar([App.det_qr("51432890")], [App.det_qr("51432891")], [App.det_qr("51432890")])
    app.esperar_fila()
    assert [i[0] for i in app.itens()] == ["51432890", "51432891"]


def test_semelhante_ao_ultimo_nao_e_mais_descartado(app):
    lendo(app)
    app.enfileirar([App.det_qr("51432890")], [App.det_qr("51432891")], [App.det_qr("51432990")])
    app.esperar_fila()
    assert len(app.itens()) == 3


def test_mesmo_ideq_com_outros_campos_diferentes_e_duplicado(app):
    lendo(app)
    app.enfileirar([App.det_qr("51432890", vere="1")], [App.det_qr("51432890", vere="2")])
    app.esperar_fila()
    assert len(app.itens()) == 1


def test_qr_com_espaco_e_quebra_de_linha_no_final_e_aceito(app):
    lendo(app)
    det = App.det_qr("51432890")
    det["rawValue"] += "  \n"
    app.enfileirar([det])
    app.esperar_fila()
    assert app.itens() == [["51432890", "RECOLHER"]]


def test_duplicado_entre_camera_e_galeria(app):
    lendo(app)
    app.enfileirar([App.det_qr("51432890")])
    app.esperar_fila()
    app.enfileirar([App.det_qr("51432890")])
    app.page.set_input_files("#input-fotos", {"name": "f.png", "mimeType": "image/png", "buffer": PNG_1x1})
    app.esperar_fila()
    assert len(app.itens()) == 1


def test_galeria_sem_codigo_avisa(app):
    app.abrir()
    app.iniciar()
    app.page.set_input_files("#input-fotos", {"name": "f.png", "mimeType": "image/png", "buffer": PNG_1x1})
    app.page.wait_for_selector("#erro-camera", state="visible", timeout=15000)
    assert "Nenhum código encontrado" in app.page.inner_text("#erro-camera")
    assert app.itens() == []


def test_operacoes_e_parametros(app):
    lendo(app)
    p = app.page

    def ler(ideq):
        app.enfileirar([App.det_qr(ideq)])
        app.esperar_fila()

    ler("51000001")  # RECOLHER é o padrão
    p.select_option("#select-operacao", "TRANSFERIR")
    assert p.is_visible("#input-zona")
    p.fill("#input-zona", "59")
    ler("51000002")
    p.fill("#input-zona", "polo")
    ler("51000003")
    p.select_option("#select-operacao", "STATUS")
    assert p.is_visible("#select-status") and not p.is_visible("#input-zona")
    p.select_option("#select-status", "Defeituosa")
    ler("51000004")
    p.select_option("#select-operacao", "DEVOLVER_TRE")
    ler("51000005")
    p.select_option("#select-operacao", "DESCARTAR")
    ler("51000006")
    p.select_option("#select-operacao", "CADASTRAR")
    ler("51000007")
    assert app.itens() == [
        ["51000001", "RECOLHER"],
        ["51000002", "TRANSFERIR:Z59"],
        ["51000003", "TRANSFERIR:POLO"],
        ["51000004", "STATUS:Defeituosa"],
        ["51000005", "DEVOLVER_TRE"],
        ["51000006", "DESCARTAR"],
        ["51000007", "CADASTRAR"],
    ]


def test_zona_invalida_nao_aceita_e_corrigir_aceita_a_mesma_urna(app):
    lendo(app)
    p = app.page
    p.select_option("#select-operacao", "TRANSFERIR")
    p.fill("#input-zona", "abc")
    app.enfileirar([App.det_qr("51000001")])
    app.esperar_fila()
    assert app.itens() == []
    assert "invalido" in p.get_attribute("#input-zona", "class")
    p.fill("#input-zona", "z012")
    app.enfileirar([App.det_qr("51000001")])
    app.esperar_fila()
    assert app.itens() == [["51000001", "TRANSFERIR:Z12"]]


def test_csv_formato_1(app):
    lendo(app, codigo="48213", responsavel="Maria S.", local="Z59")
    p = app.page
    p.fill("#texto-livre", "Não liga; tela apagada")
    app.enfileirar([App.det_qr("51000001")])
    app.esperar_fila()
    p.fill("#texto-livre", "")
    p.select_option("#select-operacao", "DESCARTAR")
    app.enfileirar([App.det_qr("51000002")])
    app.esperar_fila()
    csv = app.baixar_csv()
    linhas = csv.split("\n")
    assert re.fullmatch(
        r"#ASIDOBEM;formato=1;codigo=48213;id=\d{4}-\d{2}-\d{2}-z59-01;titulo=Inventário \d{2}/\d{2};"
        r"local=Z59;responsavel=Maria S\.;gerado_em=\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2}",
        linhas[0],
    )
    assert linhas[1] == "patrimonio;operacao;descricao"
    assert linhas[2] == "51000001;RECOLHER;Não liga tela apagada"
    assert linhas[3] == "51000002;DESCARTAR;"
    assert csv.endswith("\n") and not csv.startswith("﻿")


def test_csv_sem_local_nem_responsavel(app):
    lendo(app, codigo="48213", responsavel="", local="")
    app.enfileirar([App.det_qr("51000001")])
    app.esperar_fila()
    linha = app.baixar_csv().split("\n")[0]
    assert "-sem-local-01;" in linha
    assert "local=" not in linha and "responsavel=" not in linha


def test_responsavel_com_ponto_e_virgula_e_sanitizado(app):
    lendo(app, responsavel="Maria;S=x")
    app.enfileirar([App.det_qr("51000001")])
    app.esperar_fila()
    linha = app.baixar_csv().split("\n")[0]
    assert "responsavel=Maria S x;" in linha


def test_lista_em_tela_segue_a_ordem_do_csv(app):
    lendo(app)
    app.enfileirar([App.det_qr("51000001")], [App.det_qr("51000002")], [App.det_qr("51000003")])
    app.esperar_fila()
    ordens = app.page.eval_on_selector_all("#lista-itens .ordem", "els => els.map(e => e.textContent)")
    assert ordens == ["1.", "2.", "3."]
    csv_codigos = [l.split(";")[0] for l in app.baixar_csv().split("\n")[2:5]]
    assert csv_codigos == [i[0] for i in app.itens()]


def test_falha_de_getusermedia_mostra_erro_sem_camera_fantasma(app):
    app.abrir()
    app.iniciar()
    app.page.evaluate("navigator.mediaDevices.getUserMedia = () => Promise.reject(new Error('negada'))")
    app.page.click("#btn-camera")
    app.page.wait_for_selector("#erro-camera", state="visible")
    assert "Câmera indisponível" in app.page.inner_text("#erro-camera")
    assert app.page.evaluate("document.body.classList.contains('camera-ativa')") is False


def test_falha_de_play_para_o_stream_e_mostra_erro(app):
    app.abrir()
    app.iniciar()
    app.page.evaluate("HTMLMediaElement.prototype.play = () => Promise.reject(new Error('bloqueado'))")
    app.page.click("#btn-camera")
    app.page.wait_for_selector("#erro-camera", state="visible")
    assert "falha ao iniciar o vídeo" in app.page.inner_text("#erro-camera")
    assert app.page.evaluate("document.body.classList.contains('camera-ativa')") is False
    assert app.page.evaluate("document.getElementById('video').srcObject === null") is True
```

- [ ] **Passo 3: Rodar e ver falhar**

```bash
python3 -m pytest tests/test_fluxo.py tests/test_leitura.py -v
```

Esperado: todos FAIL (a página ainda é a antiga).

- [ ] **Passo 4: Reescrever o `index.html`**

Substitua o arquivo inteiro por (as funções `parsearCampos`, `escaparHtml`, `garantirJsQR`, `carregarImagem`, `desenharEmCanvas`, `decodificarCanvasComJsQR` são as mesmas do código atual):

```html
<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1">
<title>Leitor de QR Codes</title>
<style>
  :root {
    --bg: #14171c;
    --bg-panel: #1c2028;
    --line: #323944;
    --ink: #e8eaed;
    --ink-dim: #8b93a1;
    --accent: #d3a12e;
    --accent-ink: #14171c;
    --ok: #4caf7d;
    --err: #e0615a;
    --mono: ui-monospace, "SF Mono", "JetBrains Mono", "Roboto Mono", Consolas, monospace;
    --sans: -apple-system, "Segoe UI", Roboto, Inter, Arial, sans-serif;
  }
  * { box-sizing: border-box; }
  [hidden] { display: none !important; }
  html, body {
    margin: 0; padding: 0;
    background: var(--bg);
    color: var(--ink);
    font-family: var(--sans);
    -webkit-tap-highlight-color: transparent;
  }
  body { padding-bottom: 16px; }
  body.camera-ativa { display: flex; flex-direction: column; min-height: 100vh; min-height: 100dvh; padding-bottom: 0; }
  body.camera-ativa main { flex: 1; display: flex; flex-direction: column; min-height: 0; }
  body.camera-ativa #tela-leitura { flex: 1; display: flex; flex-direction: column; min-height: 0; }
  body.camera-ativa #slot-leitura,
  body.camera-ativa .botoes-modo,
  body.camera-ativa .status-bar,
  body.camera-ativa .pendencia,
  body.camera-ativa .lista-itens { flex: none; }
  body.camera-ativa .rodape { flex: none; }

  header { padding: 10px 14px 8px; }
  .topo-linha { display: flex; align-items: center; justify-content: space-between; gap: 10px; }
  .titulo-mini {
    font-family: var(--mono); font-size: 11px; letter-spacing: .08em;
    text-transform: uppercase; color: var(--ink-dim); white-space: nowrap;
  }
  .codigo-grande {
    font-family: var(--mono); font-size: 28px; font-weight: 800; letter-spacing: .06em;
    color: var(--accent); margin: 6px 0 0;
  }

  main { padding: 8px 14px 0; max-width: 520px; margin: 0 auto; }
  .tela { display: block; }
  .tela input[type=text],
  .bloco-operacao select,
  .bloco-operacao input[type=text] {
    background: var(--bg-panel); border: 1px solid var(--line); color: var(--ink);
    border-radius: 8px; padding: 10px 10px; font-size: 14px; font-family: var(--sans);
    width: 100%; margin-top: 8px;
  }
  .rotulo { display: block; margin-top: 6px; font-size: 12.5px; color: var(--ink-dim); }
  input.invalido { border-color: var(--err) !important; }
  .btn-texto {
    display: block; width: 100%; height: 46px; margin-top: 10px; cursor: pointer;
    border: 1.5px solid var(--accent); background: var(--accent); color: var(--accent-ink);
    border-radius: 10px; font-size: 15px; font-weight: 800;
  }
  .btn-texto.sec { background: var(--bg-panel); color: var(--ink); border-color: var(--line); font-weight: 600; }
  .btn-texto:disabled { opacity: .5; }
  .msg-erro { color: #f3a9a5; font-size: 12.5px; margin: 6px 0 0; min-height: 1em; }
  .aviso { color: var(--ink-dim); font-size: 12.5px; margin: 10px 0 0; min-height: 1em; }

  .bloco-operacao { margin-top: 4px; }
  .bloco-operacao input, .bloco-operacao select { margin-top: 6px; }

  .botoes-modo { display: flex; gap: 8px; margin-top: 10px; }
  .btn-icone {
    flex: 1;
    border: 1.5px solid var(--line);
    background: var(--bg-panel);
    color: var(--ink);
    border-radius: 10px;
    height: 46px;
    display: flex; align-items: center; justify-content: center;
    cursor: pointer;
  }
  .btn-icone svg { width: 20px; height: 20px; }
  .btn-icone:disabled { opacity: .4; }
  .btn-icone.ativo { border-color: var(--accent); color: var(--accent); background: #241f13; }
  input[type=file] { display: none; }

  .pendencia {
    display: none;
    margin-top: 8px; padding: 7px 10px; border-radius: 8px;
    background: var(--bg-panel); border: 1px solid var(--line);
    font-size: 12px; text-align: center;
  }
  .pendencia.estado-branco { border-color: var(--ink-dim); color: var(--ink-dim); }
  .pendencia.estado-verde { border-color: var(--ok); color: var(--ok); }

  .camera-wrap {
    display: none; margin-top: 8px; border-radius: 12px; overflow: hidden;
    background: #000; position: relative; aspect-ratio: 4 / 3; min-height: 160px;
  }
  body.camera-ativa .camera-wrap { flex: 1; aspect-ratio: auto; min-height: 0; }
  .camera-wrap video { width: 100%; height: 100%; object-fit: cover; display: block; }
  .camera-wrap .moldura {
    position: absolute; inset: 14%; border: 2px solid rgba(232,234,237,.85);
    border-radius: 14px; pointer-events: none;
    transition: border-color .15s ease, transform .15s ease;
  }
  .camera-wrap .moldura.estado-branco { border-color: rgba(232,234,237,.85); }
  .camera-wrap .moldura.estado-verde { border-color: rgba(76,175,125,.85); }
  .camera-wrap .moldura.flash { transform: scale(0.97); }

  .erro-camera {
    display: none; margin-top: 8px; padding: 8px 10px; border-radius: 8px;
    background: #2a1416; border: 1px solid var(--err); color: #f3a9a5; font-size: 12px; line-height: 1.4;
  }

  .status-bar {
    display: none; margin-top: 8px; padding: 8px 10px; border-radius: 8px;
    background: var(--bg-panel); border: 1px solid var(--line);
    font-family: var(--mono); font-size: 11.5px; color: var(--ink-dim);
  }
  .status-bar .barra { height: 3px; border-radius: 3px; background: var(--line); margin-top: 6px; overflow: hidden; }
  .status-bar .barra i { display: block; height: 100%; width: 0%; background: var(--accent); transition: width .2s ease; }

  .lista-itens {
    display: none;
    margin-top: 8px; padding: 6px 10px; border-radius: 8px;
    background: var(--bg-panel); border: 1px solid var(--line);
    font-family: var(--mono); font-size: 12px;
    max-height: 160px; overflow-y: auto;
  }
  .lista-itens .item { display: flex; gap: 6px; padding: 3px 0; }
  .lista-itens .item .ordem { color: var(--ink-dim); flex: none; }
  .lista-itens .item .codigo { overflow-wrap: anywhere; }
  .lista-itens .item .op { margin-left: auto; color: var(--ink-dim); flex: none; }
  body.camera-ativa .lista-itens { max-height: 25vh; }

  .rodape {
    display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 8px 10px;
    padding: 8px 14px; border-top: 1px solid var(--line); background: var(--bg-panel);
  }
  .rodape-contador { font-size: 12.5px; color: var(--ink-dim); white-space: nowrap; }
  .rodape-contador b { color: var(--ink); font-weight: 700; }
  .rodape-botoes { display: flex; gap: 6px; }
  .rodape-botoes .btn-icone { height: 38px; width: 38px; flex: none; }
  .rodape-botoes .btn-icone svg { width: 17px; height: 17px; }
</style>
</head>
<body>

<header>
  <div class="topo-linha">
    <span class="titulo-mini">Leitor PAT - Polo 24 (v 1.0)</span>
  </div>
  <div class="codigo-grande" id="codigo-grande" hidden></div>
</header>

<main>
  <section class="tela" id="tela-inicio">
    <button class="btn-texto" id="btn-iniciar" type="button">Iniciar</button>
    <p class="aviso" id="aviso-inicio"></p>
  </section>

  <section class="tela" id="tela-codigo" hidden>
    <label class="rotulo" for="input-codigo">Código do ASIdoBem</label>
    <input type="text" id="input-codigo" inputmode="numeric" maxlength="5" autocomplete="off" placeholder="5 dígitos">
    <p class="msg-erro" id="erro-codigo"></p>
    <button class="btn-texto" id="btn-codigo-ok" type="button">Continuar</button>
    <button class="btn-texto sec" id="btn-codigo-voltar" type="button">Voltar</button>
  </section>

  <section class="tela" id="tela-config" hidden>
    <input type="text" id="input-responsavel" maxlength="60" placeholder="Responsável (opcional)" autocomplete="off">
    <input type="text" id="input-local" maxlength="6" placeholder="Local: POLO ou Z59 (opcional)" autocomplete="off">
    <div id="slot-config"></div>
    <p class="msg-erro" id="erro-config"></p>
    <button class="btn-texto" id="btn-config-ok" type="button">Começar leitura</button>
    <button class="btn-texto sec" id="btn-config-voltar" type="button">Voltar</button>
  </section>

  <section class="tela" id="tela-leitura" hidden>
    <div id="slot-leitura">
      <div class="bloco-operacao" id="bloco-operacao">
        <select id="select-operacao">
          <option value="RECOLHER">Recolher</option>
          <option value="TRANSFERIR">Transferir</option>
          <option value="DEVOLVER_TRE">Devolver TRE</option>
          <option value="DESCARTAR">Descartar</option>
          <option value="STATUS">Status</option>
          <option value="CADASTRAR">Cadastrar</option>
        </select>
        <input type="text" id="input-zona" maxlength="6" placeholder="Zona (59) ou POLO" autocomplete="off" hidden>
        <select id="select-status" hidden>
          <option>Pronta</option>
          <option>Defeituosa</option>
          <option>Danificada</option>
          <option>Sucateada</option>
          <option>Nao Certificada</option>
          <option>Sem Bateria</option>
          <option>Indisponivel</option>
        </select>
        <input type="text" id="texto-livre" maxlength="200" placeholder="Nota (opcional)" autocomplete="off">
      </div>
    </div>

    <div class="botoes-modo">
      <label class="btn-icone" for="input-fotos" id="btn-galeria" title="Galeria">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="3" y="5" width="18" height="14" rx="2"/><circle cx="8.5" cy="10.5" r="1.5"/><path d="M21 15l-5-5-9 9"/></svg>
      </label>
      <input type="file" id="input-fotos" accept="image/*" multiple>

      <button class="btn-icone" id="btn-camera" type="button" title="Câmera">
        <span id="icone-camera">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M4 8a2 2 0 0 1 2-2h1.2a1 1 0 0 0 .9-.55L8.7 4.1A1 1 0 0 1 9.6 3.5h4.8a1 1 0 0 1 .9.6l.6 1.35a1 1 0 0 0 .9.55H18a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2Z"/><circle cx="12" cy="13" r="3.3"/></svg>
        </span>
      </button>
    </div>

    <div class="pendencia" id="pendencia"></div>

    <div class="camera-wrap" id="camera-wrap">
      <video id="video" playsinline muted autoplay></video>
      <div class="moldura" id="moldura"></div>
    </div>

    <div class="erro-camera" id="erro-camera"></div>

    <div class="status-bar" id="status-bar">
      <span id="status-texto">Processando…</span>
      <div class="barra"><i id="status-fill"></i></div>
    </div>

    <div class="lista-itens" id="lista-itens"></div>
  </section>
</main>

<footer class="rodape" id="rodape" hidden>
  <span class="rodape-contador" id="contador-texto">Itens coletados: 0</span>
  <div class="rodape-botoes">
    <button class="btn-icone" id="btn-csv" type="button" title="Salvar CSV">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M5 4h11l3 3v13a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V5a1 1 0 0 1 1-1Z"/><path d="M8 4v5h8V4M8 14h8v6H8v-6Z"/></svg>
    </button>
    <button class="btn-icone" id="btn-compartilhar" type="button" title="Compartilhar CSV">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="6" cy="12" r="2.4" fill="currentColor" stroke="none"/><circle cx="18" cy="6" r="2.4" fill="currentColor" stroke="none"/><circle cx="18" cy="18" r="2.4" fill="currentColor" stroke="none"/><path d="M8.1 10.8 15.9 7.2M8.1 13.2l7.8 3.6"/></svg>
    </button>
  </div>
</footer>

<canvas id="canvas" style="display:none"></canvas>

<script>
(function () {
  "use strict";

  const $ = (id) => document.getElementById(id);
  const codigoGrande = $("codigo-grande");
  const telaInicio = $("tela-inicio");
  const telaCodigo = $("tela-codigo");
  const telaConfig = $("tela-config");
  const telaLeitura = $("tela-leitura");
  const rodape = $("rodape");
  const btnIniciar = $("btn-iniciar");
  const avisoInicio = $("aviso-inicio");
  const inputCodigo = $("input-codigo");
  const erroCodigo = $("erro-codigo");
  const btnCodigoOk = $("btn-codigo-ok");
  const btnCodigoVoltar = $("btn-codigo-voltar");
  const inputResponsavel = $("input-responsavel");
  const inputLocal = $("input-local");
  const slotConfig = $("slot-config");
  const erroConfig = $("erro-config");
  const btnConfigOk = $("btn-config-ok");
  const btnConfigVoltar = $("btn-config-voltar");
  const slotLeitura = $("slot-leitura");
  const blocoOperacao = $("bloco-operacao");
  const selectOperacao = $("select-operacao");
  const inputZona = $("input-zona");
  const selectStatus = $("select-status");
  const textoLivre = $("texto-livre");
  const inputFotos = $("input-fotos");
  const btnGaleria = $("btn-galeria");
  const btnCamera = $("btn-camera");
  const iconeCamera = $("icone-camera");
  const pendenciaEl = $("pendencia");
  const cameraWrap = $("camera-wrap");
  const video = $("video");
  const moldura = $("moldura");
  const erroCamera = $("erro-camera");
  const statusBar = $("status-bar");
  const statusTexto = $("status-texto");
  const statusFill = $("status-fill");
  const contadorTexto = $("contador-texto");
  const listaItens = $("lista-itens");
  const canvas = $("canvas");
  const ctx = canvas.getContext("2d", { willReadFrequently: true });
  const btnCsv = $("btn-csv");
  const btnCompartilhar = $("btn-compartilhar");

  const ICONE_CAMERA = iconeCamera.innerHTML;
  const ICONE_PARAR = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="6" y="6" width="12" height="12" rx="2" fill="currentColor" stroke="none"/></svg>';

  // patrimônio da empresa: 10 dígitos começando com 4551. O QR traz só o IDEQ (8 dígitos);
  // "45" + IDEQ reconstrói o formato só para validar — o valor gravado é o IDEQ puro
  const PADRAO_PATRIMONIO = /^4551\d{6}$/;
  const CODIGO_VALIDO = /^[1-9]\d{4}$/;
  const INTERVALO_MS = 320;
  const JANELA_REPETIDO_MS = 2000;

  let tela = "inicio";          // "inicio" | "codigo" | "config" | "leitura"
  let sessao = null;            // {codigo, responsavel, local, itens: [{codigo, operacao, descricao}]}
  let codigosVistos = new Set(); // patrimônios já aceitos nesta sessão (único dedup do app)
  let jsQRCarregado = null;
  let streamAtivo = null;
  let intervaloId = null;
  let timerEstadoVisual = null;
  let timerErro = null;
  // último IDEQ visto na câmera: frames seguidos do mesmo QR não geram novo sinal de erro
  const recente = { valor: null, visto: 0 };

  // ---------- armazenamento local (nunca quebra se estiver bloqueado) ----------
  const LS = {
    ler(chave) { try { return JSON.parse(localStorage.getItem(chave)); } catch (e) { return null; } },
    gravar(chave, valor) { try { localStorage.setItem(chave, JSON.stringify(valor)); } catch (e) {} },
    apagar(chave) { try { localStorage.removeItem(chave); } catch (e) {} }
  };

  // ---------- utilidades ----------
  // escapa o conteúdo lido antes de injetar via innerHTML: o valor vem direto do QR
  // (não é texto confiável) e pode conter caracteres de marcação
  function escaparHtml(valor) {
    return String(valor ?? "").replace(/[&<>"']/g, (c) => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
    }[c]));
  }

  function pad2(n) { return String(n).padStart(2, "0"); }

  // zona ("59", "Z059", "z59") -> "Z59"; "polo" -> "POLO"; qualquer outra coisa -> null
  function normalizarDestino(texto) {
    const t = String(texto || "").trim().toUpperCase();
    if (t === "POLO") return "POLO";
    const m = /^Z?(\d{1,3})$/.exec(t);
    if (!m) return null;
    const n = parseInt(m[1], 10);
    return n > 0 ? "Z" + n : null;
  }

  // valores da identificação não podem ter ";" nem quebra de linha ("=" também sai: separa chave/valor)
  function limparIdentificacao(texto) {
    return String(texto || "").replace(/[;=\r\n]+/g, " ").replace(/\s+/g, " ").trim().slice(0, 60);
  }

  // a descrição vai numa coluna do CSV: sem ";" nem quebra de linha, até 200 caracteres
  function limparDescricao(texto) {
    return String(texto || "").replace(/[;\r\n]+/g, " ").replace(/\s+/g, " ").trim().slice(0, 200);
  }

  // operação do contrato conforme os campos da tela; null se faltar/for inválido o parâmetro
  function operacaoAtual() {
    const op = selectOperacao.value;
    if (op === "TRANSFERIR") {
      const destino = normalizarDestino(inputZona.value);
      return destino ? "TRANSFERIR:" + destino : null;
    }
    if (op === "STATUS") return "STATUS:" + selectStatus.value;
    return op;
  }

  function atualizarCamposOperacao() {
    inputZona.hidden = selectOperacao.value !== "TRANSFERIR";
    selectStatus.hidden = selectOperacao.value !== "STATUS";
    inputZona.classList.remove("invalido");
  }
  selectOperacao.addEventListener("change", atualizarCamposOperacao);
  inputZona.addEventListener("input", () => inputZona.classList.remove("invalido"));

  function mostrarErroTemporario(msg, ms) {
    erroCamera.textContent = msg;
    erroCamera.style.display = "block";
    if (timerErro) clearTimeout(timerErro);
    timerErro = setTimeout(() => { erroCamera.style.display = "none"; timerErro = null; }, ms || 3500);
  }

  // ---------- telas ----------
  function irPara(nome) {
    tela = nome;
    telaInicio.hidden = nome !== "inicio";
    telaCodigo.hidden = nome !== "codigo";
    telaConfig.hidden = nome !== "config";
    telaLeitura.hidden = nome !== "leitura";
    rodape.hidden = nome !== "leitura";
    codigoGrande.hidden = !(sessao && (nome === "config" || nome === "leitura"));
    if (sessao) codigoGrande.textContent = "Código " + sessao.codigo;
    (nome === "config" ? slotConfig : slotLeitura).appendChild(blocoOperacao);
    if (nome !== "leitura") pararCamera();
    if (nome === "leitura") atualizarEstadoVisual();
    atualizarContador();
  }

  btnIniciar.addEventListener("click", () => {
    avisoInicio.textContent = "";
    erroCodigo.textContent = "";
    inputCodigo.value = "";
    irPara("codigo");
    inputCodigo.focus();
  });

  btnCodigoVoltar.addEventListener("click", () => irPara("inicio"));

  btnCodigoOk.addEventListener("click", () => {
    const codigo = inputCodigo.value.trim();
    if (!CODIGO_VALIDO.test(codigo)) {
      erroCodigo.textContent = "Código inválido: 5 dígitos, de 10000 a 99999.";
      return;
    }
    erroCodigo.textContent = "";
    erroConfig.textContent = "";
    sessao = { codigo, responsavel: "", local: "", itens: [] };
    codigosVistos = new Set();
    const lembrado = LS.ler("lq.cfg") || {};
    inputResponsavel.value = lembrado.responsavel || "";
    inputLocal.value = lembrado.local || "";
    irPara("config");
  });

  btnConfigVoltar.addEventListener("click", () => {
    sessao = null;
    codigosVistos = new Set();
    irPara("codigo");
  });

  btnConfigOk.addEventListener("click", () => {
    const responsavel = limparIdentificacao(inputResponsavel.value);
    const localTexto = inputLocal.value.trim();
    const local = localTexto ? normalizarDestino(localTexto) : "";
    if (local === null) {
      erroConfig.textContent = "Local inválido: use POLO ou Z59.";
      return;
    }
    erroConfig.textContent = "";
    sessao.responsavel = responsavel;
    sessao.local = local;
    LS.gravar("lq.cfg", { responsavel, local });
    irPara("leitura");
  });

  // ---------- estado visual (borda da câmera + caixa de status) ----------
  function definirEstadoVisual(cor, texto) {
    pendenciaEl.textContent = texto;
    pendenciaEl.style.display = "block";
    pendenciaEl.classList.remove("estado-branco", "estado-verde");
    pendenciaEl.classList.add("estado-" + cor);
    moldura.classList.remove("estado-branco", "estado-verde");
    moldura.classList.add("estado-" + cor);
  }

  function atualizarEstadoVisual() {
    if (timerEstadoVisual) { clearTimeout(timerEstadoVisual); timerEstadoVisual = null; }
    definirEstadoVisual("branco", "Esperando leitura");
  }

  function mostrarItemIncluido() {
    definirEstadoVisual("verde", "Item incluído");
    if (timerEstadoVisual) clearTimeout(timerEstadoVisual);
    timerEstadoVisual = setTimeout(() => { timerEstadoVisual = null; atualizarEstadoVisual(); }, 1000);
  }

  function sinalizar(tipo) {
    moldura.classList.add("flash");
    setTimeout(() => moldura.classList.remove("flash"), 300);
    if (navigator.vibrate) {
      try { navigator.vibrate(tipo === "sucesso" ? [40, 40, 60] : [120]); } catch (e) {}
    }
  }

  // ---------- parsing dos campos CHAVE:VALOR (do conteúdo do QR) ----------
  function parsearCampos(texto) {
    const campos = {};
    const partes = texto.split(/\s+/).filter(Boolean);
    let chaveAtual = null;
    let valorAtual = [];
    const ehChave = (parte) => {
      const idx = parte.indexOf(":");
      if (idx <= 0) return false;
      const chave = parte.slice(0, idx);
      return chave.length <= 6 && /^[A-Z0-9]+$/.test(chave);
    };
    for (const parte of partes) {
      if (ehChave(parte)) {
        if (chaveAtual) campos[chaveAtual] = valorAtual.join(" ").trim();
        const idx = parte.indexOf(":");
        chaveAtual = parte.slice(0, idx);
        const primeiroValor = parte.slice(idx + 1);
        valorAtual = primeiroValor ? [primeiroValor] : [];
      } else if (chaveAtual) {
        valorAtual.push(parte);
      }
    }
    if (chaveAtual) campos[chaveAtual] = valorAtual.join(" ").trim();
    return Object.keys(campos).length > 1 ? campos : {};
  }

  // ---------- lista em tela e contador ----------
  function atualizarContador() {
    const n = sessao ? sessao.itens.length : 0;
    contadorTexto.innerHTML = `Itens coletados: <b>${n}</b>`;
    btnCsv.disabled = !n;
    btnCompartilhar.disabled = !n;
    atualizarLista();
  }

  function atualizarLista() {
    const itens = sessao ? sessao.itens : [];
    if (!itens.length) { listaItens.style.display = "none"; listaItens.innerHTML = ""; return; }
    listaItens.innerHTML = itens.map((it, i) =>
      `<div class="item"><span class="ordem">${i + 1}.</span><span class="codigo">${escaparHtml(it.codigo)}</span><span class="op">${escaparHtml(it.operacao)}</span></div>`
    ).join("");
    listaItens.style.display = "block";
    listaItens.scrollTop = listaItens.scrollHeight;
  }

  // ---------- aceitação de cada QR detectado ----------
  function processarCodigoDetectado(codigo, origem) {
    if (!sessao || tela !== "leitura") return;
    // só QR: o código de barras da urna é ignorado por completo (ver CLAUDE.md)
    if (codigo.format !== "qr_code") return;
    const campos = parsearCampos(codigo.rawValue);
    // QR sem IDEQ não é o QR de patrimônio da urna: ruído de cena, ignora em silêncio
    if (!campos.IDEQ) return;
    const patrimonio = campos.IDEQ;

    const agora = Date.now();
    const mesmoFrame = origem === "câmera" && recente.valor === patrimonio && agora - recente.visto < JANELA_REPETIDO_MS;
    recente.valor = patrimonio;
    recente.visto = agora;
    const rejeitar = () => { if (!mesmoFrame) sinalizar("erro"); };

    if (!PADRAO_PATRIMONIO.test("45" + patrimonio)) return rejeitar();
    if (codigosVistos.has(patrimonio)) return rejeitar();
    const operacao = operacaoAtual();
    if (!operacao) { inputZona.classList.add("invalido"); return rejeitar(); }

    codigosVistos.add(patrimonio);
    sessao.itens.push({ codigo: patrimonio, operacao, descricao: limparDescricao(textoLivre.value) });
    atualizarContador();
    sinalizar("sucesso");
    mostrarItemIncluido();
  }

  // ---------- CSV (formato 1 do contrato com o ASIdoBem) ----------
  function isoComFuso(d) {
    const minutos = -d.getTimezoneOffset();
    const sinal = minutos >= 0 ? "+" : "-";
    const a = Math.abs(minutos);
    return `${d.getFullYear()}-${pad2(d.getMonth() + 1)}-${pad2(d.getDate())}T${pad2(d.getHours())}:${pad2(d.getMinutes())}:${pad2(d.getSeconds())}${sinal}${pad2(Math.floor(a / 60))}:${pad2(a % 60)}`;
  }

  function gerarId(d, seq) {
    const slug = sessao.local ? sessao.local.toLowerCase().replace(/[^a-z0-9]/g, "") : "";
    return `${d.getFullYear()}-${pad2(d.getMonth() + 1)}-${pad2(d.getDate())}-${slug || "sem-local"}-${pad2(seq)}`;
  }

  function montarLista(seq) {
    const agora = new Date();
    const id = gerarId(agora, seq);
    const titulo = `Inventário ${pad2(agora.getDate())}/${pad2(agora.getMonth() + 1)}`;
    const ident = ["#ASIDOBEM", "formato=1", `codigo=${sessao.codigo}`, `id=${id}`, `titulo=${titulo}`];
    if (sessao.local) ident.push(`local=${sessao.local}`);
    if (sessao.responsavel) ident.push(`responsavel=${sessao.responsavel}`);
    ident.push(`gerado_em=${isoComFuso(agora)}`);
    const linhas = [ident.join(";"), "patrimonio;operacao;descricao"];
    for (const it of sessao.itens) linhas.push(`${it.codigo};${it.operacao};${it.descricao}`);
    return { id, csv: linhas.join("\n") + "\n" };
  }

  btnCsv.addEventListener("click", () => {
    if (!sessao || !sessao.itens.length) return;
    const { id, csv } = montarLista(1);
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `lista_${id}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    setTimeout(() => URL.revokeObjectURL(url), 5000);
  });

  btnCompartilhar.addEventListener("click", async () => {
    if (!sessao || !sessao.itens.length) return;
    const { id, csv } = montarLista(1);
    let arquivo;
    try {
      arquivo = new File([csv], `lista_${id}.csv`, { type: "text/csv" });
    } catch (e) {
      mostrarErroTemporario("Compartilhamento não suportado neste navegador.");
      return;
    }
    if (!navigator.canShare || !navigator.canShare({ files: [arquivo] })) {
      mostrarErroTemporario("Este navegador não aceita compartilhar arquivos. Use Salvar.");
      return;
    }
    try {
      await navigator.share({ files: [arquivo] });
    } catch (e) {
      if (e && e.name !== "AbortError") mostrarErroTemporario("Falha ao compartilhar: " + (e.message || e.name));
    }
  });

  // ---------- detector nativo / jsQR (só QR) ----------
  let detectorCache = null;
  function obterDetectorNativo() {
    if (detectorCache) return detectorCache;
    try { detectorCache = new window.BarcodeDetector({ formats: ["qr_code"] }); }
    catch (e) { detectorCache = null; }
    return detectorCache;
  }

  function garantirJsQR() {
    if (window.jsQR) return Promise.resolve();
    if (jsQRCarregado) return jsQRCarregado;
    jsQRCarregado = new Promise((resolve, reject) => {
      const s = document.createElement("script");
      s.src = "https://cdn.jsdelivr.net/npm/jsqr@1.4.0/dist/jsQR.js";
      s.onload = () => resolve();
      s.onerror = () => reject(new Error("sem conexão para carregar biblioteca de apoio"));
      document.head.appendChild(s);
    });
    // se falhar (rede indisponível no momento), não guarda a rejeição em cache — senão uma
    // queda de conexão pontual trava o fallback pro resto da sessão, mesmo com internet de volta
    jsQRCarregado.catch(() => { jsQRCarregado = null; });
    return jsQRCarregado;
  }

  // ================= GALERIA =================
  function carregarImagem(arquivo) {
    return new Promise((resolve, reject) => {
      const leitor = new FileReader();
      leitor.onload = () => {
        const img = new Image();
        img.onload = () => resolve(img);
        img.onerror = () => reject(new Error("não foi possível decodificar a imagem"));
        img.src = leitor.result;
      };
      leitor.onerror = () => reject(new Error("não foi possível ler o arquivo"));
      leitor.readAsDataURL(arquivo);
    });
  }

  function desenharEmCanvas(img, escala) {
    const w = Math.max(1, Math.round(img.naturalWidth * escala));
    const h = Math.max(1, Math.round(img.naturalHeight * escala));
    canvas.width = w; canvas.height = h;
    ctx.clearRect(0, 0, w, h);
    ctx.drawImage(img, 0, 0, w, h);
    return { w, h };
  }

  // decodifica o canvas (já desenhado pelo chamador) via jsQR — compartilhado entre galeria e
  // câmera pra não duplicar o trio getImageData/jsQR/montagem do resultado nos dois lugares
  function decodificarCanvasComJsQR(w, h) {
    const dados = ctx.getImageData(0, 0, w, h);
    const resultado = window.jsQR(dados.data, w, h);
    return resultado && resultado.data ? [{ rawValue: resultado.data, format: "qr_code" }] : [];
  }

  async function detectarCodigosEmImagem(img) {
    if ("BarcodeDetector" in window) {
      const detector = obterDetectorNativo();
      if (detector) {
        for (const escala of [1, 0.5, 1.5]) {
          const fator = Math.min(escala, (1600 / Math.max(img.naturalWidth, img.naturalHeight)) * escala || escala);
          desenharEmCanvas(img, fator);
          try {
            const codigos = await detector.detect(canvas);
            if (codigos && codigos.length) return codigos.map(c => ({ rawValue: c.rawValue, format: c.format }));
          } catch (e) { /* tenta próxima escala */ }
        }
      }
    }
    try {
      await garantirJsQR();
      for (const escala of [1, 0.5, 1.5]) {
        const { w, h } = desenharEmCanvas(img, escala);
        const codigos = decodificarCanvasComJsQR(w, h);
        if (codigos.length) return codigos;
      }
    } catch (e) { /* sem internet e sem suporte nativo */ }
    return [];
  }

  inputFotos.addEventListener("change", async (ev) => {
    const arquivos = Array.from(ev.target.files || []);
    if (!arquivos.length) return;
    pararCamera();
    statusBar.style.display = "block";
    let processados = 0;
    let falhas = 0;

    for (const arquivo of arquivos) {
      statusTexto.textContent = `${processados + 1}/${arquivos.length}`;
      statusFill.style.width = Math.round((processados / arquivos.length) * 100) + "%";
      try {
        const img = await carregarImagem(arquivo);
        const codigos = await detectarCodigosEmImagem(img);
        if (!codigos.length) falhas++;
        for (const codigo of codigos) processarCodigoDetectado(codigo, "galeria");
      } catch (e) {
        falhas++;
      }
      processados++;
      statusFill.style.width = Math.round((processados / arquivos.length) * 100) + "%";
      await new Promise(res => setTimeout(res, 0));
    }

    statusTexto.textContent = `${processados} processada(s)`;
    setTimeout(() => { statusBar.style.display = "none"; }, 1500);
    inputFotos.value = "";
    if (falhas) mostrarErroTemporario(`Nenhum código encontrado em ${falhas} foto(s).`);
  });

  // ================= CÂMERA =================
  async function iniciarCamera() {
    erroCamera.style.display = "none";
    recente.valor = null;
    try {
      streamAtivo = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: { ideal: "environment" } }, audio: false
      });
    } catch (e) {
      erroCamera.textContent = "Câmera indisponível: " + (e.message || e.name || "permissão negada.");
      erroCamera.style.display = "block";
      return;
    }
    video.srcObject = streamAtivo;
    try {
      await video.play();
    } catch (e) {
      // sem isso, um play() rejeitado (ex.: restrição de autoplay em WebView) deixava a UI
      // da câmera "ativa" com o vídeo congelado, sem detectar nada e sem aviso nenhum
      streamAtivo.getTracks().forEach(t => t.stop());
      streamAtivo = null;
      video.srcObject = null;
      erroCamera.textContent = "Câmera indisponível: falha ao iniciar o vídeo (" + (e.message || e.name || "erro desconhecido") + ").";
      erroCamera.style.display = "block";
      return;
    }
    cameraWrap.style.display = "block";
    document.body.classList.add("camera-ativa");
    btnCamera.classList.add("ativo");
    iconeCamera.innerHTML = ICONE_PARAR;
    btnGaleria.style.opacity = ".5";
    btnGaleria.style.pointerEvents = "none";
    atualizarEstadoVisual();

    const detectorNativo = ("BarcodeDetector" in window) ? obterDetectorNativo() : null;

    const tick = async () => {
      if (!streamAtivo || video.readyState < 2) return;
      try {
        let codigos = [];
        if (detectorNativo) {
          const brutos = await detectorNativo.detect(video);
          codigos = (brutos || []).map(c => ({ rawValue: c.rawValue, format: c.format }));
        } else {
          await garantirJsQR();
          const w = video.videoWidth, h = video.videoHeight;
          if (w && h) {
            canvas.width = w; canvas.height = h;
            ctx.drawImage(video, 0, 0, w, h);
            codigos = decodificarCanvasComJsQR(w, h);
          }
        }
        for (const codigo of codigos) processarCodigoDetectado(codigo, "câmera");
      } catch (e) { /* ignora falha pontual de um frame */ }
    };
    intervaloId = setInterval(tick, INTERVALO_MS);
  }

  function pararCamera() {
    if (intervaloId) clearInterval(intervaloId);
    intervaloId = null;
    if (streamAtivo) { streamAtivo.getTracks().forEach(t => t.stop()); streamAtivo = null; }
    video.srcObject = null;
    cameraWrap.style.display = "none";
    document.body.classList.remove("camera-ativa");
    btnCamera.classList.remove("ativo");
    iconeCamera.innerHTML = ICONE_CAMERA;
    btnGaleria.style.opacity = "";
    btnGaleria.style.pointerEvents = "";
  }

  btnCamera.addEventListener("click", () => { if (streamAtivo) pararCamera(); else iniciarCamera(); });

  irPara("inicio");
})();
</script>
</body>
</html>
```

- [ ] **Passo 5: Rodar e ver passar**

```bash
python3 -m pytest tests/test_fluxo.py tests/test_leitura.py -v
```

Esperado: todos PASS. Se `test_galeria_sem_codigo_avisa` demorar, o aborto da CDN do jsQR deve falhar rápido (rota do `contexto`); confira que a rota está registrada.

- [ ] **Passo 6: Commit**

```bash
git add index.html tests/test_fluxo.py tests/test_leitura.py
git commit -m "feat: fluxo guiado só com QR, operações do contrato e CSV formato 1

Remove o modo Bateria, a leitura de código de barras e a checagem de
semelhança entre patrimônios. O app passa a ter telas
inicio -> codigo -> config -> leitura." -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Tarefa 3: Excluir último e Cancelar leitura

**Arquivos:**
- Modificar: `index.html` (rodapé, CSS, JS)
- Testar: `tests/test_edicao.py`

**Interfaces:**
- Consome: `sessao`, `codigosVistos`, `atualizarContador()`, `irPara()`, `recente` (Tarefa 2).
- Produz: ids `btn-excluir-ultimo`, `btn-cancelar`; funções `encerrarSessao()` (zera `sessao`/`codigosVistos`; a Tarefa 4 acrescenta o apagamento da sessão salva) e `bloqueioCamera` (valor recém-excluído que a câmera não readiciona enquanto continuar à vista).

- [ ] **Passo 1: Escrever os testes**

Crie `tests/test_edicao.py`:

```python
from conftest import App


def lendo(app, **kw):
    app.abrir()
    app.iniciar(**kw)
    app.ligar_camera()


def test_excluir_ultimo_remove_da_lista_e_libera_para_reler(app):
    lendo(app)
    app.enfileirar([App.det_qr("51000001")], [App.det_qr("51000002")])
    app.esperar_fila()
    assert len(app.itens()) == 2
    app.page.click("#btn-excluir-ultimo")
    assert [i[0] for i in app.itens()] == ["51000001"]
    app.page.wait_for_timeout(2300)  # sai da janela de bloqueio da câmera
    app.enfileirar([App.det_qr("51000002")])
    app.esperar_fila()
    assert [i[0] for i in app.itens()] == ["51000001", "51000002"]


def test_excluir_varias_vezes_remove_do_mais_novo_ao_mais_antigo(app):
    lendo(app)
    app.enfileirar([App.det_qr("51000001")], [App.det_qr("51000002")], [App.det_qr("51000003")])
    app.esperar_fila()
    app.page.click("#btn-excluir-ultimo")
    app.page.click("#btn-excluir-ultimo")
    assert [i[0] for i in app.itens()] == ["51000001"]
    app.page.click("#btn-excluir-ultimo")
    assert app.itens() == []
    assert app.page.is_disabled("#btn-excluir-ultimo")


def test_excluir_com_o_qr_ainda_na_frente_da_camera_nao_readiciona(app):
    lendo(app)
    app.enfileirar([App.det_qr("51000001")])
    app.esperar_fila(extra=300)
    app.page.click("#btn-excluir-ultimo")
    app.enfileirar(*[[App.det_qr("51000001")] for _ in range(4)])  # câmera ainda apontada para o mesmo QR
    app.esperar_fila()
    assert app.itens() == []
    app.page.wait_for_timeout(2500)  # QR saiu de vista
    app.enfileirar([App.det_qr("51000001")])
    app.esperar_fila()
    assert [i[0] for i in app.itens()] == ["51000001"]


def test_cancelar_com_confirmacao_descarta_e_volta_ao_inicio(app):
    lendo(app)
    app.enfileirar([App.det_qr("51000001")])
    app.esperar_fila()
    mensagens = []
    app.page.once("dialog", lambda d: (mensagens.append(d.message), d.accept()))
    app.page.click("#btn-cancelar")
    assert "1 item" in mensagens[0]
    assert app.page.is_visible("#btn-iniciar")
    assert app.page.evaluate("document.body.classList.contains('camera-ativa')") is False
    app.iniciar(codigo="48213")
    assert app.itens() == []


def test_cancelar_recusado_mantem_a_leitura(app):
    lendo(app)
    app.enfileirar([App.det_qr("51000001")])
    app.esperar_fila()
    app.page.once("dialog", lambda d: d.dismiss())
    app.page.click("#btn-cancelar")
    assert app.page.is_visible("#tela-leitura")
    assert len(app.itens()) == 1


def test_cancelar_sem_itens_nao_pergunta(app):
    app.abrir()
    app.iniciar()
    app.page.click("#btn-cancelar")
    assert app.page.is_visible("#btn-iniciar")


def test_apos_cancelar_o_mesmo_patrimonio_pode_ser_lido_em_nova_sessao(app):
    lendo(app)
    app.enfileirar([App.det_qr("51000001")])
    app.esperar_fila()
    app.page.once("dialog", lambda d: d.accept())
    app.page.click("#btn-cancelar")
    app.iniciar()
    app.ligar_camera()
    app.enfileirar([App.det_qr("51000001")])
    app.esperar_fila()
    assert len(app.itens()) == 1
```

- [ ] **Passo 2: Rodar e ver falhar**

```bash
python3 -m pytest tests/test_edicao.py -v
```

Esperado: FAIL (botões não existem).

- [ ] **Passo 3: Implementar**

Em `index.html`, no `<style>`, depois da regra `.rodape-botoes .btn-icone svg { … }`, acrescente:

```css
  #btn-cancelar { margin-right: 14px; }
```

No `<div class="rodape-botoes">`, **antes** do botão `btn-csv`, insira:

```html
    <button class="btn-icone" id="btn-excluir-ultimo" type="button" title="Excluir último">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M9 14 4 9l5-5"/><path d="M4 9h10.5a5.5 5.5 0 0 1 0 11H11"/></svg>
    </button>
    <button class="btn-icone" id="btn-cancelar" type="button" title="Cancelar leitura">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M6 6l12 12M18 6 6 18"/></svg>
    </button>
```

No script, junto das outras referências (`const btnCompartilhar = $("btn-compartilhar");`), acrescente:

```js
  const btnExcluirUltimo = $("btn-excluir-ultimo");
  const btnCancelar = $("btn-cancelar");
```

Junto de `const recente = { valor: null, visto: 0 };` acrescente:

```js
  // QR recém-excluído com "Excluir último": a câmera, ainda apontada para ele, não pode readicioná-lo
  // no frame seguinte. O bloqueio dura enquanto o valor continuar à vista (renovado a cada frame)
  const bloqueioCamera = { valor: null, visto: 0 };
```

Em `atualizarContador()`, depois de `btnCompartilhar.disabled = !n;`, acrescente:

```js
    btnExcluirUltimo.disabled = !n;
```

Em `processarCodigoDetectado`, logo depois de `const patrimonio = campos.IDEQ;`, acrescente:

```js
    if (origem === "câmera" && bloqueioCamera.valor === patrimonio &&
        Date.now() - bloqueioCamera.visto < JANELA_REPETIDO_MS) {
      bloqueioCamera.visto = Date.now();
      return;
    }
```

Antes de `irPara("inicio");` (última linha do script) acrescente:

```js
  // ---------- excluir último / cancelar ----------
  btnExcluirUltimo.addEventListener("click", () => {
    if (!sessao || !sessao.itens.length) return;
    const item = sessao.itens.pop();
    codigosVistos.delete(item.codigo);
    bloqueioCamera.valor = item.codigo;
    bloqueioCamera.visto = Date.now();
    atualizarContador();
  });

  function encerrarSessao() {
    sessao = null;
    codigosVistos = new Set();
    bloqueioCamera.valor = null;
    recente.valor = null;
  }

  btnCancelar.addEventListener("click", () => {
    const n = sessao ? sessao.itens.length : 0;
    if (n && !window.confirm(`Cancelar a leitura? ${n} item(ns) serão descartados.`)) return;
    encerrarSessao();
    irPara("inicio");
  });
```

- [ ] **Passo 4: Rodar e ver passar**

```bash
python3 -m pytest tests -v
```

Esperado: todos PASS (inclusive as tarefas anteriores).

- [ ] **Passo 5: Commit**

```bash
git add index.html tests/test_edicao.py
git commit -m "feat: botões Excluir último e Cancelar leitura" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Tarefa 4: Sessão salva e retomada

**Arquivos:**
- Modificar: `index.html`
- Testar: `tests/test_sessao.py`

**Interfaces:**
- Consome: `LS`, `sessao`, `codigosVistos`, `irPara`, `encerrarSessao` (Tarefas 2–3).
- Produz: chave `lq.sessao`; ids `caixa-retomar`, `texto-retomar`, `btn-retomar`, `btn-descartar`; funções `salvarSessao()`, `sessaoSalvaValida(s)`, `prepararInicio()`. `encerrarSessao()` passa a apagar `lq.sessao`.

- [ ] **Passo 1: Escrever os testes**

Crie `tests/test_sessao.py`:

```python
import json

from conftest import App


def lendo(app, **kw):
    app.abrir()
    app.iniciar(**kw)
    app.ligar_camera()


def test_retomar_apos_recarregar(app):
    lendo(app, codigo="48213", responsavel="Maria", local="Z59")
    p = app.page
    p.select_option("#select-operacao", "STATUS")
    p.select_option("#select-status", "Defeituosa")
    p.fill("#texto-livre", "lacre 7")
    app.enfileirar([App.det_qr("51000001")], [App.det_qr("51000002")])
    app.esperar_fila()
    p.reload()
    assert p.is_visible("#caixa-retomar")
    texto = p.inner_text("#texto-retomar")
    assert "2 itens" in texto and "48213" in texto
    assert not p.is_visible("#btn-iniciar")
    p.click("#btn-retomar")
    assert p.is_visible("#tela-leitura")
    assert p.inner_text("#codigo-grande") == "Código 48213"
    assert app.itens() == [["51000001", "STATUS:Defeituosa"], ["51000002", "STATUS:Defeituosa"]]
    assert p.input_value("#select-operacao") == "STATUS"
    assert p.input_value("#select-status") == "Defeituosa"
    assert p.input_value("#texto-livre") == "lacre 7"
    # o conjunto de patrimônios já lidos também volta
    app.ligar_camera()
    app.enfileirar([App.det_qr("51000001")])
    app.esperar_fila()
    assert len(app.itens()) == 2
    # e a lista retomada gera o CSV com a identificação original
    linha = app.baixar_csv().split("\n")[0]
    assert "codigo=48213" in linha and "local=Z59" in linha and "responsavel=Maria" in linha


def test_descartar_sessao_salva(app):
    lendo(app)
    app.enfileirar([App.det_qr("51000001")])
    app.esperar_fila()
    app.page.reload()
    app.page.click("#btn-descartar")
    assert app.page.is_visible("#btn-iniciar")
    app.page.reload()
    assert not app.page.is_visible("#caixa-retomar")


def test_sessao_sem_itens_nao_e_salva(app):
    lendo(app)
    app.page.reload()
    assert not app.page.is_visible("#caixa-retomar")
    assert app.page.is_visible("#btn-iniciar")


def test_cancelar_apaga_a_sessao_salva(app):
    lendo(app)
    app.enfileirar([App.det_qr("51000001")])
    app.esperar_fila()
    app.page.once("dialog", lambda d: d.accept())
    app.page.click("#btn-cancelar")
    assert app.page.evaluate("localStorage.getItem('lq.sessao')") is None


def test_excluir_ultimo_atualiza_a_sessao_salva(app):
    lendo(app)
    app.enfileirar([App.det_qr("51000001")], [App.det_qr("51000002")])
    app.esperar_fila()
    app.page.click("#btn-excluir-ultimo")
    salva = json.loads(app.page.evaluate("localStorage.getItem('lq.sessao')"))
    assert [i["codigo"] for i in salva["itens"]] == ["51000001"]


def test_sessao_salva_corrompida_e_ignorada(app):
    app.abrir()
    app.page.evaluate("localStorage.setItem('lq.sessao', '{quebrado')")
    app.page.reload()
    assert app.page.is_visible("#btn-iniciar")
    assert not app.page.is_visible("#caixa-retomar")
    assert app.erros_pagina == []


def test_sessao_salva_com_formato_invalido_e_ignorada_e_apagada(app):
    app.abrir()
    invalidas = [
        {"codigo": "abc", "itens": [{"codigo": "51000001", "operacao": "RECOLHER", "descricao": ""}]},
        {"codigo": "48213", "itens": [{"codigo": "<img src=x>", "operacao": "RECOLHER", "descricao": ""}]},
        {"codigo": "48213", "itens": "nao-e-lista"},
        {"codigo": "48213", "itens": []},
        [1, 2, 3],
    ]
    for s in invalidas:
        app.page.evaluate("v => localStorage.setItem('lq.sessao', JSON.stringify(v))", s)
        app.page.reload()
        assert app.page.is_visible("#btn-iniciar"), s
        assert not app.page.is_visible("#caixa-retomar"), s
        assert app.page.evaluate("localStorage.getItem('lq.sessao')") is None, s
    assert app.erros_pagina == []
```

- [ ] **Passo 2: Rodar e ver falhar**

```bash
python3 -m pytest tests/test_sessao.py -v
```

Esperado: FAIL.

- [ ] **Passo 3: Implementar**

HTML — dentro de `<section class="tela" id="tela-inicio">`, depois do `<p class="aviso" id="aviso-inicio"></p>`:

```html
    <div id="caixa-retomar" hidden>
      <p class="aviso" id="texto-retomar"></p>
      <button class="btn-texto" id="btn-retomar" type="button">Retomar</button>
      <button class="btn-texto sec" id="btn-descartar" type="button">Descartar</button>
    </div>
```

JS — junto das referências:

```js
  const caixaRetomar = $("caixa-retomar");
  const textoRetomar = $("texto-retomar");
  const btnRetomar = $("btn-retomar");
  const btnDescartar = $("btn-descartar");
```

Em `irPara(nome)`, depois de `atualizarContador();` (última linha da função), acrescente:

```js
    if (nome === "inicio") prepararInicio();
```

Antes de `irPara("inicio");` (última linha), acrescente:

```js
  // ---------- sessão salva (o Chrome do Android pode descartar a aba em segundo plano) ----------
  function salvarSessao() {
    if (!sessao || !sessao.itens.length) { LS.apagar("lq.sessao"); return; }
    LS.gravar("lq.sessao", {
      codigo: sessao.codigo, responsavel: sessao.responsavel, local: sessao.local, itens: sessao.itens,
      op: { operacao: selectOperacao.value, zona: inputZona.value, status: selectStatus.value, nota: textoLivre.value }
    });
  }

  // o conteúdo salvo não é confiável (pode estar corrompido ou ter sido editado): valida a forma inteira
  function sessaoSalvaValida(s) {
    return !!s && typeof s === "object" && !Array.isArray(s) &&
      CODIGO_VALIDO.test(String(s.codigo)) &&
      Array.isArray(s.itens) && s.itens.length > 0 &&
      s.itens.every(it => it && /^\d{1,20}$/.test(String(it.codigo)) &&
        typeof it.operacao === "string" && typeof it.descricao === "string");
  }

  function prepararInicio() {
    const s = LS.ler("lq.sessao");
    if (sessaoSalvaValida(s)) {
      textoRetomar.textContent = `Retomar leitura de ${s.itens.length} itens (código ${s.codigo})?`;
      caixaRetomar.hidden = false;
    } else {
      caixaRetomar.hidden = true;
      if (s !== null) LS.apagar("lq.sessao");
    }
    btnIniciar.hidden = !caixaRetomar.hidden;
  }

  btnRetomar.addEventListener("click", () => {
    const s = LS.ler("lq.sessao");
    if (!sessaoSalvaValida(s)) { prepararInicio(); return; }
    sessao = {
      codigo: String(s.codigo),
      responsavel: limparIdentificacao(s.responsavel),
      local: s.local ? (normalizarDestino(s.local) || "") : "",
      itens: s.itens.map(it => ({ codigo: String(it.codigo), operacao: it.operacao, descricao: limparDescricao(it.descricao) }))
    };
    codigosVistos = new Set(sessao.itens.map(it => it.codigo));
    const op = s.op || {};
    if (Array.from(selectOperacao.options).some(o => o.value === op.operacao)) selectOperacao.value = op.operacao;
    if (Array.from(selectStatus.options).some(o => o.value === op.status)) selectStatus.value = op.status;
    inputZona.value = typeof op.zona === "string" ? op.zona.slice(0, 6) : "";
    textoLivre.value = typeof op.nota === "string" ? op.nota.slice(0, 200) : "";
    atualizarCamposOperacao();
    irPara("leitura");
  });

  btnDescartar.addEventListener("click", () => {
    LS.apagar("lq.sessao");
    prepararInicio();
  });

  [selectOperacao, selectStatus, inputZona, textoLivre].forEach(el => {
    el.addEventListener("input", () => { if (tela === "leitura") salvarSessao(); });
    el.addEventListener("change", () => { if (tela === "leitura") salvarSessao(); });
  });
```

Em `processarCodigoDetectado`, depois de `sessao.itens.push(...)`, acrescente `salvarSessao();`. No handler de `btnExcluirUltimo`, depois de `codigosVistos.delete(item.codigo);`, acrescente `salvarSessao();`. Em `encerrarSessao()`, acrescente `LS.apagar("lq.sessao");`.

- [ ] **Passo 4: Rodar e ver passar**

```bash
python3 -m pytest tests -v
```

Esperado: todos PASS.

- [ ] **Passo 5: Commit**

```bash
git add index.html tests/test_sessao.py
git commit -m "feat: sessão salva no aparelho e retomada após recarregar" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Tarefa 5: Sons de sucesso e de erro

**Arquivos:**
- Modificar: `index.html`
- Testar: `tests/test_sons.py`

**Interfaces:**
- Consome: `sinalizar(tipo)` (Tarefa 2), stubs `window.__tons`, `window.__vibracoes` (Tarefa 1).
- Produz: `prepararAudio()`, `tocarSom("sucesso"|"erro")`. Sucesso = osciladores 880 Hz e 1320 Hz; erro = 180 Hz.

- [ ] **Passo 1: Escrever os testes**

Crie `tests/test_sons.py`:

```python
from conftest import PNG_1x1, App


def lendo(app):
    app.abrir()
    app.iniciar()
    app.ligar_camera()


def tons(app):
    return app.page.evaluate("window.__tons")


def vibracoes(app):
    return app.page.evaluate("window.__vibracoes")


def test_leitura_valida_toca_som_de_sucesso_e_vibra(app):
    lendo(app)
    app.enfileirar([App.det_qr("51000001")])
    app.esperar_fila()
    assert tons(app) == [880, 1320]
    assert [40, 40, 60] in vibracoes(app)


def test_frames_repetidos_do_mesmo_qr_nao_repetem_som(app):
    lendo(app)
    app.enfileirar(*[[App.det_qr("51000001")] for _ in range(5)])
    app.esperar_fila()
    assert tons(app) == [880, 1320]


def test_repetido_toca_erro_uma_vez_e_vibra_diferente(app):
    lendo(app)
    app.enfileirar([App.det_qr("51000001")])
    app.esperar_fila()
    app.page.wait_for_timeout(2300)  # o QR saiu de vista
    app.enfileirar(*[[App.det_qr("51000001")] for _ in range(4)])
    app.esperar_fila()
    assert tons(app) == [880, 1320, 180]
    assert [120] in vibracoes(app)


def test_fora_do_padrao_toca_erro_uma_vez(app):
    lendo(app)
    app.enfileirar(*[[App.det_qr("12345678")] for _ in range(4)])
    app.esperar_fila()
    assert tons(app) == [180]


def test_valores_diferentes_com_problema_tocam_cada_um(app):
    lendo(app)
    app.enfileirar([App.det_qr("12345678")], [App.det_qr("87654321")])
    app.esperar_fila()
    assert tons(app) == [180, 180]


def test_zona_invalida_toca_erro(app):
    lendo(app)
    app.page.select_option("#select-operacao", "TRANSFERIR")
    app.page.fill("#input-zona", "xx")
    app.enfileirar([App.det_qr("51000001")])
    app.esperar_fila()
    assert tons(app) == [180]


def test_sem_ideq_e_codigo_de_barras_sao_silenciosos(app):
    lendo(app)
    app.enfileirar(
        [{"rawValue": "https://exemplo.com", "format": "qr_code"}],
        [App.det_barra("4551432890")],
    )
    app.esperar_fila()
    assert tons(app) == []
    assert vibracoes(app) == []


def test_galeria_cada_foto_e_independente(app):
    app.abrir()
    app.iniciar()
    arquivo = {"name": "f.png", "mimeType": "image/png", "buffer": PNG_1x1}
    app.enfileirar([App.det_qr("51000001")], [App.det_qr("51000001")])
    app.page.set_input_files("#input-fotos", [arquivo, arquivo])
    app.esperar_fila()
    assert tons(app) == [880, 1320, 180]


def test_sem_web_audio_nao_quebra_a_leitura(app):
    app.abrir()
    app.page.evaluate("window.AudioContext = undefined; window.webkitAudioContext = undefined")
    app.iniciar()
    app.ligar_camera()
    app.enfileirar([App.det_qr("51000001")])
    app.esperar_fila()
    assert len(app.itens()) == 1
    assert app.erros_pagina == []
```

- [ ] **Passo 2: Rodar e ver falhar**

```bash
python3 -m pytest tests/test_sons.py -v
```

Esperado: FAIL (nenhum som é tocado).

- [ ] **Passo 3: Implementar**

Em `index.html`, logo antes de `function sinalizar(tipo) {`, acrescente:

```js
  // ---------- som (Web Audio, tons gerados no código — sem arquivos) ----------
  let audioCtx = null;

  // precisa nascer/ser retomado num gesto do usuário (toques em Iniciar, câmera e galeria)
  function prepararAudio() {
    try {
      const AC = window.AudioContext || window.webkitAudioContext;
      if (!AC) return;
      if (!audioCtx) audioCtx = new AC();
      if (audioCtx.state === "suspended") audioCtx.resume();
    } catch (e) { /* sem áudio: segue só com a vibração */ }
  }

  function tom(frequencia, inicio, duracao, tipo) {
    const t0 = audioCtx.currentTime + inicio;
    const osc = audioCtx.createOscillator();
    const ganho = audioCtx.createGain();
    osc.type = tipo;
    osc.frequency.value = frequencia;
    ganho.gain.setValueAtTime(0.0001, t0);
    ganho.gain.exponentialRampToValueAtTime(0.35, t0 + 0.01);
    ganho.gain.exponentialRampToValueAtTime(0.0001, t0 + duracao);
    osc.connect(ganho);
    ganho.connect(audioCtx.destination);
    osc.start(t0);
    osc.stop(t0 + duracao + 0.02);
  }

  function tocarSom(tipo) {
    prepararAudio();
    if (!audioCtx) return;
    try {
      if (tipo === "sucesso") { tom(880, 0, 0.09, "sine"); tom(1320, 0.1, 0.12, "sine"); }
      else tom(180, 0, 0.35, "square");
    } catch (e) { /* falha de áudio nunca atrapalha a leitura */ }
  }

```

Em `sinalizar(tipo)`, depois do bloco `if (navigator.vibrate) { … }`, acrescente `tocarSom(tipo);`.

Registre o gesto: no handler de `btnIniciar`, como primeira linha, acrescente `prepararAudio();`; no handler `btnCamera.addEventListener("click", () => { … })` troque por:

```js
  btnCamera.addEventListener("click", () => { prepararAudio(); if (streamAtivo) pararCamera(); else iniciarCamera(); });
  btnGaleria.addEventListener("click", prepararAudio);
```

- [ ] **Passo 4: Rodar e ver passar**

```bash
python3 -m pytest tests -v
```

Esperado: todos PASS.

- [ ] **Passo 5: Commit**

```bash
git add index.html tests/test_sons.py
git commit -m "feat: sons de sucesso e de erro além da vibração" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Tarefa 6: Token — link de configuração, ajustes e verificação ao Iniciar

**Arquivos:**
- Modificar: `index.html`
- Testar: `tests/test_token.py`

**Interfaces:**
- Consome: `LS`, `irPara`, `avisoInicio`, `erroCodigo`, `prepararAudio` (Tarefas 2–5).
- Produz: constante `REPO`, `API`; chave `lq.token`; `cabecalhosGithub(token)`; `verificarToken()` → `"ok"|"invalido"|"offline"`; ids `btn-ajustes`, `painel-ajustes`, `input-token`, `btn-token-salvar`, `btn-token-apagar`, `estado-token`, `erro-token`.

- [ ] **Passo 1: Escrever os testes**

Crie `tests/test_token.py`:

```python
import json

from conftest import TOKEN_TESTE


def token_guardado(app):
    return app.page.evaluate("localStorage.getItem('lq.token')")


def test_link_de_configuracao_guarda_token_e_limpa_o_fragmento(app):
    app.abrir(token=None, hash="#cfg=" + TOKEN_TESTE)
    assert "#" not in app.page.url and "cfg" not in app.page.url
    assert token_guardado(app) == json.dumps(TOKEN_TESTE)
    assert "configurado" in app.page.inner_text("#aviso-inicio").lower()


def test_link_de_configuracao_invalido_nao_guarda(app):
    app.abrir(token=None, hash="#cfg=curto")
    assert token_guardado(app) is None
    assert "inválido" in app.page.inner_text("#aviso-inicio")
    assert "cfg" not in app.page.url


def test_sem_token_nao_inicia_e_nao_chama_a_api(app):
    chamadas = []
    app.abrir(token=None)
    app.page.on("request", lambda r: chamadas.append(r.url) if "api.github.com" in r.url else None)
    app.page.click("#btn-iniciar")
    assert "Token ausente" in app.page.inner_text("#aviso-inicio")
    assert app.page.is_visible("#tela-inicio")
    assert chamadas == []


def test_token_rejeitado_pelo_github_bloqueia(app):
    app.status_get = 401
    app.abrir()
    app.page.click("#btn-iniciar")
    app.page.wait_for_function("document.getElementById('aviso-inicio').textContent.includes('vencido')")
    assert app.page.is_visible("#tela-inicio")


def test_token_sem_permissao_de_escrita_bloqueia(app):
    app.push = False
    app.abrir()
    app.page.click("#btn-iniciar")
    app.page.wait_for_function("document.getElementById('aviso-inicio').textContent.includes('permissão')")
    assert app.page.is_visible("#tela-inicio")


def test_sem_rede_deixa_iniciar_com_aviso(app):
    app.rede_caida = True
    app.abrir()
    app.page.click("#btn-iniciar")
    app.page.wait_for_selector("#tela-codigo:not([hidden])")
    assert "Sem conexão" in app.page.inner_text("#erro-codigo")


def test_token_valido_inicia_normalmente(app):
    app.abrir()
    app.iniciar()
    assert app.page.is_visible("#tela-leitura")


def test_ajustes_colar_e_apagar_token(app):
    app.abrir(token=None)
    p = app.page
    p.click("#btn-ajustes")
    assert "Sem token" in p.inner_text("#estado-token")
    p.fill("#input-token", "abc")
    p.click("#btn-token-salvar")
    assert "inválido" in p.inner_text("#erro-token")
    assert token_guardado(app) is None
    p.fill("#input-token", TOKEN_TESTE)
    p.click("#btn-token-salvar")
    assert "Token configurado" in p.inner_text("#estado-token")
    assert token_guardado(app) == json.dumps(TOKEN_TESTE)
    p.click("#btn-token-apagar")
    assert "Sem token" in p.inner_text("#estado-token")
    assert token_guardado(app) is None


def test_localstorage_bloqueado_nao_quebra_a_pagina(app):
    app.abrir(token=None)
    app.page.add_init_script(
        "Object.defineProperty(window, 'localStorage', {get() { throw new Error('bloqueado'); }})"
    )
    app.page.reload()
    assert app.page.is_visible("#btn-iniciar")
    app.page.click("#btn-iniciar")
    assert "Token ausente" in app.page.inner_text("#aviso-inicio")
    assert app.erros_pagina == []
```

- [ ] **Passo 2: Rodar e ver falhar**

```bash
python3 -m pytest tests/test_token.py -v
```

Esperado: FAIL.

- [ ] **Passo 3: Implementar**

HTML — dentro de `<section class="tela" id="tela-inicio">`, depois do `<div id="caixa-retomar" …>…</div>`:

```html
    <button class="btn-texto sec" id="btn-ajustes" type="button">Ajustes</button>
    <div id="painel-ajustes" hidden>
      <p class="aviso" id="estado-token"></p>
      <input type="text" id="input-token" placeholder="Colar token" autocomplete="off">
      <p class="msg-erro" id="erro-token"></p>
      <button class="btn-texto" id="btn-token-salvar" type="button">Guardar token</button>
      <button class="btn-texto sec" id="btn-token-apagar" type="button">Apagar token</button>
    </div>
```

CSS — o seletor `.tela input[type=text]` já estiliza `#input-token`.

JS — junto das referências:

```js
  const btnAjustes = $("btn-ajustes");
  const painelAjustes = $("painel-ajustes");
  const estadoToken = $("estado-token");
  const inputToken = $("input-token");
  const erroToken = $("erro-token");
  const btnTokenSalvar = $("btn-token-salvar");
  const btnTokenApagar = $("btn-token-apagar");
```

Junto das constantes (depois de `JANELA_REPETIDO_MS`):

```js
  const REPO = "jofilho71/asidobem-listas";
  const API = "https://api.github.com/repos/" + REPO;
  const RE_TOKEN = /^[A-Za-z0-9_\-]{20,255}$/;
```

Substitua o handler atual de `btnIniciar` por:

```js
  btnIniciar.addEventListener("click", async () => {
    prepararAudio();
    btnIniciar.disabled = true;
    avisoInicio.textContent = "Verificando…";
    const estado = await verificarToken();
    btnIniciar.disabled = false;
    if (estado === "ausente") {
      avisoInicio.textContent = "Token ausente. Peça o link de configuração.";
      return;
    }
    if (estado === "invalido") {
      avisoInicio.textContent = "Token vencido ou sem permissão de escrita. Peça um novo link de configuração.";
      return;
    }
    avisoInicio.textContent = "";
    erroCodigo.textContent = estado === "offline" ? "Sem conexão: confira antes de publicar." : "";
    inputCodigo.value = "";
    irPara("codigo");
    inputCodigo.focus();
  });
```

E acrescente, antes de `irPara("inicio");`:

```js
  // ---------- token do GitHub ----------
  function cabecalhosGithub(token) {
    return { "Authorization": "Bearer " + token, "Accept": "application/vnd.github+json" };
  }

  // "ausente" | "invalido" | "offline" | "ok". 401/403/404 ou permissão de escrita explicitamente
  // negada = inválido; falha de rede/5xx = offline (não impede a coleta em campo)
  async function verificarToken() {
    const token = LS.ler("lq.token");
    if (!token) return "ausente";
    try {
      const r = await fetch(API, { headers: cabecalhosGithub(token) });
      if (r.status === 401 || r.status === 403 || r.status === 404) return "invalido";
      if (!r.ok) return "offline";
      const j = await r.json().catch(() => ({}));
      if (j.permissions && j.permissions.push === false) return "invalido";
      return "ok";
    } catch (e) { return "offline"; }
  }

  function aplicarLinkDeConfiguracao() {
    const m = /^#cfg=(.+)$/.exec(location.hash);
    if (!m) return;
    let token = m[1];
    try { token = decodeURIComponent(token); } catch (e) { /* usa como veio */ }
    // o token nunca fica na barra de endereço nem no histórico
    try { history.replaceState(null, "", location.pathname + location.search); } catch (e) {}
    if (!RE_TOKEN.test(token)) { avisoInicio.textContent = "Link de configuração inválido."; return; }
    LS.gravar("lq.token", token);
    avisoInicio.textContent = "Aparelho configurado.";
  }

  function atualizarEstadoToken() {
    estadoToken.textContent = LS.ler("lq.token") ? "Token configurado." : "Sem token.";
  }

  btnAjustes.addEventListener("click", () => {
    painelAjustes.hidden = !painelAjustes.hidden;
    erroToken.textContent = "";
    inputToken.value = "";
    atualizarEstadoToken();
  });

  btnTokenSalvar.addEventListener("click", () => {
    const token = inputToken.value.trim();
    if (!RE_TOKEN.test(token)) { erroToken.textContent = "Token inválido."; return; }
    erroToken.textContent = "";
    LS.gravar("lq.token", token);
    inputToken.value = "";
    atualizarEstadoToken();
  });

  btnTokenApagar.addEventListener("click", () => {
    LS.apagar("lq.token");
    atualizarEstadoToken();
  });

  aplicarLinkDeConfiguracao();
```

(`aplicarLinkDeConfiguracao();` fica imediatamente antes de `irPara("inicio");`, de modo que `irPara("inicio")` não apaga o aviso.)

- [ ] **Passo 4: Rodar e ver passar**

```bash
python3 -m pytest tests -v
```

Esperado: todos PASS. Nota: `test_localstorage_bloqueado_nao_quebra_a_pagina` depende de `LS` com `try/catch` (já existente).

- [ ] **Passo 5: Commit**

```bash
git add index.html tests/test_token.py
git commit -m "feat: link de configuração com token, ajustes e verificação ao Iniciar" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Tarefa 7: Publicar

**Arquivos:**
- Modificar: `index.html`
- Testar: `tests/test_publicar.py`

**Interfaces:**
- Consome: `montarLista(seq)`, `LS`, `API`, `cabecalhosGithub`, `encerrarSessao`, `irPara`, `mostrarErroTemporario(msg, ms)` (Tarefas 2–6).
- Produz: id `btn-publicar`; `base64Utf8(texto)`; `enviarLista(token, id, csv)` → `Response`; `publicar()`; constante `MAX_LINHAS_PUBLICACAO = 15000`.

- [ ] **Passo 1: Escrever os testes**

Crie `tests/test_publicar.py`:

```python
import json

from conftest import REPO, TOKEN_TESTE, App


def preparar(app, n=2, **kw):
    app.abrir()
    app.iniciar(**kw)
    app.ligar_camera()
    app.enfileirar(*[[App.det_qr(f"5100000{i + 1}")] for i in range(n)])
    app.esperar_fila()


def test_publicar_envia_csv_e_volta_ao_inicio(app):
    preparar(app, n=2, codigo="48213", responsavel="Maria S.", local="Z59")
    app.page.click("#btn-publicar")
    app.page.wait_for_selector("#tela-inicio:not([hidden])")
    put = app.puts[0]
    csv = app.csv_publicado(0)
    id_lista = csv.split("\n")[0].split(";")[3].removeprefix("id=")
    assert put["url"].endswith(f"/repos/{REPO}/contents/listas/{id_lista}.csv")
    assert put["auth"] == "Bearer " + TOKEN_TESTE
    assert "sha" not in put["corpo"]
    assert csv.split("\n")[0].startswith("#ASIDOBEM;formato=1;codigo=48213;id=")
    assert csv.split("\n")[2:4] == ["51000001;RECOLHER;", "51000002;RECOLHER;"]
    assert "Publicada (2 linhas)" in app.page.inner_text("#aviso-inicio")
    assert app.page.evaluate("localStorage.getItem('lq.sessao')") is None
    app.iniciar(codigo="48213")  # nova configuração oferecida
    assert app.itens() == []


def test_id_incrementa_quando_o_arquivo_ja_existe(app):
    app.respostas_put = [(422, {"message": 'Invalid request.\n\n"sha" wasn\'t supplied.'}), (201, {})]
    preparar(app, n=1, local="Z59")
    app.page.click("#btn-publicar")
    app.page.wait_for_selector("#tela-inicio:not([hidden])")
    assert len(app.puts) == 2
    assert app.puts[0]["url"].endswith("-z59-01.csv")
    assert app.puts[1]["url"].endswith("-z59-02.csv")
    assert app.csv_publicado(1).split("\n")[0].count("-z59-02") == 1


def test_422_por_outro_motivo_nao_incrementa_e_mantem_a_lista(app):
    app.respostas_put = [(422, {"message": "Validation Failed"})]
    preparar(app, n=1)
    app.page.click("#btn-publicar")
    app.page.wait_for_selector("#erro-camera", state="visible")
    assert len(app.puts) == 1
    assert "HTTP 422" in app.page.inner_text("#erro-camera")
    assert len(app.itens()) == 1


def test_conflito_409_tenta_de_novo_o_mesmo_id(app):
    app.respostas_put = [(409, {"message": "conflict"}), (201, {})]
    preparar(app, n=1)
    app.page.click("#btn-publicar")
    app.page.wait_for_selector("#tela-inicio:not([hidden])", timeout=10000)
    assert len(app.puts) == 2
    assert app.puts[0]["url"] == app.puts[1]["url"]


def test_falha_de_rede_mantem_a_lista_e_permite_tentar_de_novo(app):
    preparar(app, n=2)
    app.rede_caida = True
    app.page.click("#btn-publicar")
    app.page.wait_for_selector("#erro-camera", state="visible")
    assert "Sem conexão" in app.page.inner_text("#erro-camera")
    assert app.page.is_visible("#tela-leitura")
    assert len(app.itens()) == 2
    assert app.page.is_enabled("#btn-publicar")
    app.rede_caida = False
    app.page.click("#btn-publicar")
    app.page.wait_for_selector("#tela-inicio:not([hidden])")
    assert len(app.puts) == 1


def test_token_rejeitado_na_publicacao_mantem_a_lista(app):
    app.respostas_put = [(401, {"message": "Bad credentials"})]
    preparar(app, n=1)
    app.page.click("#btn-publicar")
    app.page.wait_for_selector("#erro-camera", state="visible")
    assert "token" in app.page.inner_text("#erro-camera").lower()
    assert len(app.itens()) == 1


def test_sem_token_no_momento_de_publicar(app):
    preparar(app, n=1)
    app.page.evaluate("localStorage.removeItem('lq.token')")
    app.page.click("#btn-publicar")
    app.page.wait_for_selector("#erro-camera", state="visible")
    assert "token" in app.page.inner_text("#erro-camera").lower()
    assert app.puts == []


def test_toque_duplo_em_publicar_envia_uma_vez(app):
    app.atraso_put = 0.6
    preparar(app, n=1)
    app.page.dblclick("#btn-publicar")
    app.page.wait_for_selector("#tela-inicio:not([hidden])", timeout=10000)
    app.page.wait_for_timeout(500)
    assert len(app.puts) == 1


def test_lista_vazia_deixa_publicar_desabilitado(app):
    app.abrir()
    app.iniciar()
    assert app.page.is_disabled("#btn-publicar")
    assert app.puts == []


def test_texto_com_acento_emoji_e_travessao_chega_identico(app):
    app.abrir()
    app.iniciar(responsavel="José Álvaro", local="Z59")
    app.ligar_camera()
    app.page.fill("#texto-livre", "Não liga — lacre nº 7 ✓ 🚫")
    app.enfileirar([App.det_qr("51000001")])
    app.esperar_fila()
    app.page.click("#btn-publicar")
    app.page.wait_for_selector("#tela-inicio:not([hidden])")
    csv = app.csv_publicado(0)
    assert "responsavel=José Álvaro;" in csv.split("\n")[0]
    assert csv.split("\n")[2] == "51000001;RECOLHER;Não liga — lacre nº 7 ✓ 🚫"


def test_mais_de_15000_itens_nao_publica(app):
    app.abrir()
    # sessão salva com 15.001 itens, retomada de uma vez (ler tudo pela câmera/galeria re-renderiza a lista a cada item)
    app.page.evaluate(
        """() => localStorage.setItem('lq.sessao', JSON.stringify({
              codigo: '48213', responsavel: '', local: '',
              itens: Array.from({length: 15001}, (_, i) => ({
                codigo: '51' + String(i).padStart(6, '0'), operacao: 'RECOLHER', descricao: ''})),
              op: {}}))"""
    )
    app.page.reload()
    app.page.click("#btn-retomar")
    app.page.wait_for_function("document.getElementById('contador-texto').textContent.includes('15001')")
    app.page.click("#btn-publicar")
    app.page.wait_for_selector("#erro-camera", state="visible")
    assert "15000" in app.page.inner_text("#erro-camera")
    assert app.puts == []
    assert app.page.is_visible("#tela-leitura")
```

- [ ] **Passo 2: Rodar e ver falhar**

```bash
python3 -m pytest tests/test_publicar.py -v
```

Esperado: FAIL (`#btn-publicar` não existe).

- [ ] **Passo 3: Implementar**

HTML — no `<div class="rodape-botoes">`, **depois** do botão `btn-compartilhar`:

```html
    <button class="btn-icone" id="btn-publicar" type="button" title="Publicar">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M12 16V4M7 9l5-5 5 5M5 20h14"/></svg>
    </button>
```

CSS — depois de `#btn-cancelar { … }`:

```css
  #btn-publicar { border-color: var(--accent); color: var(--accent); }
```

JS — referência: `const btnPublicar = $("btn-publicar");`. Constantes:

```js
  const MAX_LINHAS_PUBLICACAO = 15000;
```

Estado, junto de `let timerErro = null;`: `let publicando = false;`.

Em `atualizarContador()`, depois de `btnExcluirUltimo.disabled = !n;`, acrescente `btnPublicar.disabled = !n || publicando;`.

Antes de `// ---------- token do GitHub ----------`, acrescente:

```js
  // ---------- publicação ----------
  function base64Utf8(texto) {
    const bytes = new TextEncoder().encode(texto);
    let binario = "";
    for (let i = 0; i < bytes.length; i += 0x8000) {
      binario += String.fromCharCode.apply(null, bytes.subarray(i, i + 0x8000));
    }
    return btoa(binario);
  }

  // PUT sem "sha": o GitHub recusa (422) se o arquivo já existe — a lista publicada nunca é sobrescrita
  function enviarLista(token, id, csv) {
    return fetch(`${API}/contents/listas/${id}.csv`, {
      method: "PUT",
      headers: Object.assign({ "Content-Type": "application/json" }, cabecalhosGithub(token)),
      body: JSON.stringify({ message: `Lista ${id}`, content: base64Utf8(csv) })
    });
  }

  function concluirPublicacao(id, linhas) {
    encerrarSessao();
    avisoInicio.textContent = `Publicada (${linhas} linhas): ${id}. O ASIdoBem a verá em alguns minutos.`;
    irPara("inicio");
  }

  async function publicar() {
    if (publicando || !sessao || !sessao.itens.length) return;
    if (sessao.itens.length > MAX_LINHAS_PUBLICACAO) {
      mostrarErroTemporario(`Lista com mais de ${MAX_LINHAS_PUBLICACAO} itens: publique esta parte e continue em outra lista.`, 8000);
      return;
    }
    const token = LS.ler("lq.token");
    if (!token) {
      mostrarErroTemporario("Aparelho sem token. Peça o link de configuração.", 8000);
      return;
    }
    publicando = true;
    atualizarContador();
    try {
      for (let seq = 1; seq <= 99; seq++) {
        const { id, csv } = montarLista(seq);
        let resposta = null;
        for (let tentativa = 0; tentativa < 3; tentativa++) {
          resposta = await enviarLista(token, id, csv);
          if (resposta.status !== 409) break;          // 409: outro envio simultâneo no repositório
          await new Promise(res => setTimeout(res, 800));
        }
        if (resposta.status === 201) { concluirPublicacao(id, sessao.itens.length); return; }
        const corpo = await resposta.json().catch(() => ({}));
        if (resposta.status === 422 && /sha/i.test(corpo.message || "")) continue; // id já existe: próximo seq
        if (resposta.status === 401 || resposta.status === 403) {
          mostrarErroTemporario("Token vencido ou sem permissão. A lista continua na tela; peça um novo link de configuração.", 8000);
        } else {
          mostrarErroTemporario(`Falha ao publicar (HTTP ${resposta.status}). A lista continua na tela.`, 8000);
        }
        return;
      }
      mostrarErroTemporario("Não foi possível encontrar um id livre para a lista.", 8000);
    } catch (e) {
      mostrarErroTemporario("Sem conexão: a lista continua na tela. Tente de novo ou salve o CSV.", 8000);
    } finally {
      publicando = false;
      atualizarContador();
    }
  }

  btnPublicar.addEventListener("click", publicar);

```

- [ ] **Passo 4: Rodar e ver passar**

```bash
python3 -m pytest tests -v
```

Esperado: todos PASS. `test_mais_de_15000_itens_nao_publica` pode levar alguns segundos (renderiza 15.001 linhas).

- [ ] **Passo 5: Commit**

```bash
git add index.html tests/test_publicar.py
git commit -m "feat: botão Publicar envia a lista ao repositório de listas" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Tarefa 8: Repositório de listas — gerador de índice e workflow

**Arquivos:**
- Criar: `repositorio-listas/scripts/gerar_indice.py`, `repositorio-listas/.github/workflows/indice.yml`, `repositorio-listas/listas/.gitkeep`, `repositorio-listas/README.md`
- Testar: `tests/test_indice.py`

**Interfaces:**
- Produz: `python3 scripts/gerar_indice.py <raiz>` lê `<raiz>/listas/*.csv`, escreve `<raiz>/indice.csv` (cabeçalho `id;codigo;gerado_em;titulo;linhas;sha256;arquivo`, mais recente primeiro), registra em `stderr` as listas ignoradas e sai com código 0.

- [ ] **Passo 1: Escrever os testes**

Crie `tests/test_indice.py`:

```python
import hashlib
import pathlib
import subprocess
import sys

import pytest

RAIZ = pathlib.Path(__file__).resolve().parent.parent
SCRIPT = RAIZ / "repositorio-listas" / "scripts" / "gerar_indice.py"
CABECALHO_INDICE = "id;codigo;gerado_em;titulo;linhas;sha256;arquivo"


def lista(id_, codigo="48213", gerado="2026-10-20T16:42:05-03:00", linhas=("51250523;RECOLHER;ok",),
          cabecalho="patrimonio;operacao;descricao", formato="1"):
    ident = f"#ASIDOBEM;formato={formato};codigo={codigo};id={id_};titulo=Teste {id_};gerado_em={gerado}"
    return "\n".join([ident, cabecalho, *linhas]) + "\n"


def gravar(raiz, id_, conteudo, nome=None):
    pasta = raiz / "listas"
    pasta.mkdir(exist_ok=True)
    caminho = pasta / ((nome or id_) + ".csv")
    dados = conteudo if isinstance(conteudo, bytes) else conteudo.encode("utf-8")
    caminho.write_bytes(dados)
    return caminho


def rodar(raiz):
    r = subprocess.run([sys.executable, "-I", str(SCRIPT), str(raiz)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    return r


def indice(raiz):
    return (raiz / "indice.csv").read_text(encoding="utf-8").split("\n")


def test_indice_ordenado_do_mais_recente_com_sha256_e_linhas(tmp_path):
    a = gravar(tmp_path, "2026-10-20-z59-01", lista("2026-10-20-z59-01", gerado="2026-10-20T16:42:05-03:00",
                                                    linhas=("51250523;RECOLHER;a", "51250524;DESCARTAR;")))
    b = gravar(tmp_path, "2026-10-21-polo-01", lista("2026-10-21-polo-01", gerado="2026-10-21T09:10:00-03:00"))
    rodar(tmp_path)
    linhas = indice(tmp_path)
    assert linhas[0] == CABECALHO_INDICE
    assert linhas[1] == (
        f"2026-10-21-polo-01;48213;2026-10-21T09:10:00-03:00;Teste 2026-10-21-polo-01;1;"
        f"{hashlib.sha256(b.read_bytes()).hexdigest()};listas/2026-10-21-polo-01.csv"
    )
    assert linhas[2] == (
        f"2026-10-20-z59-01;48213;2026-10-20T16:42:05-03:00;Teste 2026-10-20-z59-01;2;"
        f"{hashlib.sha256(a.read_bytes()).hexdigest()};listas/2026-10-20-z59-01.csv"
    )
    assert linhas[3] == ""  # termina com quebra de linha


def test_ordem_considera_o_fuso(tmp_path):
    gravar(tmp_path, "a-01", lista("a-01", gerado="2026-10-20T23:00:00-03:00"))   # 02:00 UTC do dia 21
    gravar(tmp_path, "b-01", lista("b-01", gerado="2026-10-21T01:00:00+00:00"))   # 01:00 UTC do dia 21
    rodar(tmp_path)
    assert indice(tmp_path)[1].startswith("a-01;")


def test_saida_deterministica(tmp_path):
    gravar(tmp_path, "a-01", lista("a-01"))
    gravar(tmp_path, "b-01", lista("b-01", gerado="2026-10-21T09:10:00-03:00"))
    rodar(tmp_path)
    primeira = (tmp_path / "indice.csv").read_bytes()
    rodar(tmp_path)
    assert (tmp_path / "indice.csv").read_bytes() == primeira


def test_sem_listas_gera_so_o_cabecalho(tmp_path):
    (tmp_path / "listas").mkdir()
    rodar(tmp_path)
    assert (tmp_path / "indice.csv").read_text(encoding="utf-8") == CABECALHO_INDICE + "\n"


def test_bom_e_tolerado(tmp_path):
    gravar(tmp_path, "a-01", b"\xef\xbb\xbf" + lista("a-01").encode("utf-8"))
    rodar(tmp_path)
    assert indice(tmp_path)[1].startswith("a-01;")


@pytest.mark.parametrize("motivo,conteudo,nome", [
    ("formato 2", lista("x-01", formato="2"), None),
    ("codigo curto", lista("x-01", codigo="1234"), None),
    ("codigo com zero", lista("x-01", codigo="01234"), None),
    ("id diferente do nome", lista("outro-01"), "x-01"),
    ("id invalido", lista("x_01"), "x_01"),
    ("cabecalho errado", lista("x-01", cabecalho="patrimonio;operacao"), None),
    ("linha com 2 colunas", lista("x-01", linhas=("51250523;RECOLHER",)), None),
    ("linha com 4 colunas", lista("x-01", linhas=("51250523;RECOLHER;a;b",)), None),
    ("sem identificacao", "patrimonio;operacao;descricao\n51250523;RECOLHER;a\n", None),
    ("nao utf8", b"#ASIDOBEM;formato=1;codigo=48213;id=x-01\n\xff\xfe\n", None),
    ("mais de 20000 linhas", lista("x-01", linhas=tuple(f"{i};RECOLHER;" for i in range(20001))), None),
])
def test_lista_invalida_fica_fora_do_indice_e_e_registrada(tmp_path, motivo, conteudo, nome):
    gravar(tmp_path, "x-01", conteudo, nome=nome)
    gravar(tmp_path, "ok-01", lista("ok-01"))
    r = rodar(tmp_path)
    linhas = indice(tmp_path)
    assert [l.split(";")[0] for l in linhas[1:] if l] == ["ok-01"], motivo
    assert "ignorada" in r.stderr.lower(), motivo
```

- [ ] **Passo 2: Rodar e ver falhar**

```bash
python3 -m pytest tests/test_indice.py -v
```

Esperado: FAIL (script inexistente).

- [ ] **Passo 3: Implementar o script**

Crie `repositorio-listas/scripts/gerar_indice.py`:

```python
#!/usr/bin/env python3
"""Gera indice.csv a partir de listas/*.csv (formato 1 do contrato com o ASIdoBem).

Uso: gerar_indice.py <raiz-do-repositorio>

Lista inválida fica FORA do índice e é registrada em stderr ("ignorada"); o script nunca
falha por causa de uma lista ruim, para não travar a publicação das demais.
"""
import hashlib
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

MAX_LINHAS = 20000
MAX_BYTES = 5 * 1024 * 1024
RE_ID = re.compile(r"^[A-Za-z0-9-]{1,60}$")
RE_CODIGO = re.compile(r"^[1-9]\d{4}$")
CABECALHO_LISTA = "patrimonio;operacao;descricao"
CABECALHO_INDICE = "id;codigo;gerado_em;titulo;linhas;sha256;arquivo"
PREFIXO = "#ASIDOBEM;"


def ler_lista(caminho: Path):
    """Devolve (metadados, quantidade_de_linhas, bytes) ou levanta ValueError com o motivo."""
    dados = caminho.read_bytes()
    if len(dados) > MAX_BYTES:
        raise ValueError("maior que 5 MB")
    try:
        texto = dados.decode("utf-8")
    except UnicodeDecodeError:
        raise ValueError("não é UTF-8")
    if texto.startswith("﻿"):
        texto = texto[1:]
    linhas = texto.splitlines()
    if not linhas or not linhas[0].startswith(PREFIXO):
        raise ValueError("sem linha de identificação")
    meta = {}
    for par in linhas[0][len(PREFIXO):].split(";"):
        if "=" in par:
            chave, valor = par.split("=", 1)
            meta[chave.strip()] = valor.strip()
    if meta.get("formato") != "1":
        raise ValueError("formato diferente de 1")
    if not RE_CODIGO.match(meta.get("codigo", "")):
        raise ValueError("código inválido")
    if not RE_ID.match(meta.get("id", "")):
        raise ValueError("id inválido")
    if meta["id"] != caminho.stem:
        raise ValueError("id diferente do nome do arquivo")
    if len(linhas) < 2 or linhas[1] != CABECALHO_LISTA:
        raise ValueError("cabeçalho diferente do exigido")
    dados_linhas = [l for l in linhas[2:] if l.strip()]
    if len(dados_linhas) > MAX_LINHAS:
        raise ValueError("mais de 20.000 linhas")
    for n, linha in enumerate(dados_linhas, 1):
        if linha.count(";") != 2:
            raise ValueError(f"linha {n} com número de colunas diferente de 3")
    return meta, len(dados_linhas), dados


def instante(texto: str) -> datetime:
    try:
        d = datetime.fromisoformat(texto)
    except ValueError:
        return datetime.min.replace(tzinfo=timezone.utc)
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def main(raiz: Path) -> None:
    entradas = []
    for caminho in sorted((raiz / "listas").glob("*.csv")):
        try:
            meta, quantidade, dados = ler_lista(caminho)
        except ValueError as erro:
            print(f"ignorada: {caminho.name}: {erro}", file=sys.stderr)
            continue
        entradas.append({
            "id": meta["id"],
            "codigo": meta["codigo"],
            "gerado_em": meta.get("gerado_em", ""),
            "titulo": meta.get("titulo", "").replace(";", " "),
            "linhas": quantidade,
            "sha256": hashlib.sha256(dados).hexdigest(),
            "arquivo": f"listas/{meta['id']}.csv",
        })
    entradas.sort(key=lambda e: (instante(e["gerado_em"]), e["id"]), reverse=True)
    saida = [CABECALHO_INDICE] + [
        ";".join(str(e[c]) for c in ("id", "codigo", "gerado_em", "titulo", "linhas", "sha256", "arquivo"))
        for e in entradas
    ]
    (raiz / "indice.csv").write_bytes(("\n".join(saida) + "\n").encode("utf-8"))


if __name__ == "__main__":
    main(Path(sys.argv[1]))
```

Crie `repositorio-listas/.github/workflows/indice.yml`:

```yaml
name: indice

on:
  push:
    branches: [main]
    paths: ["listas/**"]
  workflow_dispatch:

# uma execução por vez: dois celulares publicando juntos não disputam o índice
concurrency:
  group: indice
  cancel-in-progress: false

permissions:
  contents: write

jobs:
  gerar:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Gera o índice
        run: python3 scripts/gerar_indice.py .
      - name: Commita o índice se mudou
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
          git add indice.csv
          if git diff --cached --quiet; then exit 0; fi
          git commit -m "Atualiza índice [skip ci]"
          git pull --rebase origin main
          git push origin main
```

Crie `repositorio-listas/listas/.gitkeep` (arquivo vazio) e `repositorio-listas/README.md`:

```markdown
# asidobem-listas

Listas de patrimônio de urnas publicadas pelo leitor de QR Codes
(https://jofilho71.github.io/leitor-qrcodes-android/) e coletadas pelo ASIdoBem.

- `listas/<id>.csv` — uma lista por coleta, formato 1 (ver `IMPORTACAO_WEB.md` no projeto do ASIdoBem).
  Só são criadas pelo leitor; nunca editadas.
- `indice.csv` — gerado automaticamente pelo workflow `indice` (não editar à mão). Listas inválidas ficam de
  fora; o motivo aparece no log da execução (aba Actions).

**Endereço para o ASIdoBem** (*Site…*, token em branco):

    https://raw.githubusercontent.com/jofilho71/asidobem-listas/main/indice.csv

O cache do GitHub pode atrasar a chegada de uma lista em alguns minutos.
```

- [ ] **Passo 4: Rodar e ver passar**

```bash
python3 -m pytest tests -v
```

Esperado: todos PASS.

- [ ] **Passo 5: Commit**

```bash
git add repositorio-listas tests/test_indice.py
git commit -m "feat: gerador de índice e workflow do repositório de listas" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Tarefa 9: Documentação

**Arquivos:**
- Modificar (reescrever): `CLAUDE.md`, `MANUAL.md`, `README.md`

- [ ] **Passo 1: Reescrever `CLAUDE.md`**

Substitua o conteúdo inteiro por:

````markdown
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

Telas: `inicio → codigo → config → leitura` (função `irPara`). Estado em `sessao = {codigo, responsavel, local,
itens:[{codigo, operacao, descricao}]}` e `codigosVistos` (Set).

1. **Iniciar** verifica o token do aparelho (`verificarToken`: `GET` no repositório de listas; `permissions.push`
   explicitamente falso, 401/403/404 → bloqueia; rede/5xx → segue com aviso).
2. **Código** do ASIdoBem: 5 dígitos, `/^[1-9]\d{4}$/`. Fica grande no topo para o técnico conferir (o ASIdoBem
   ignora em silêncio listas de códigos que não são dele — o app não tem como detectar código errado).
3. **Config**: responsável e local (`POLO`/`Z<n>`, lembrados no aparelho em `lq.cfg`) + operação inicial.
4. **Leitura**: câmera/galeria. Operação, zona/status e nota podem mudar durante a leitura (uma lista pode
   misturar operações). Rodapé: Excluir último, Cancelar (confirma), Salvar, Compartilhar, Publicar.
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

Operações: `RECOLHER`, `TRANSFERIR:Z<n>|POLO`, `DEVOLVER_TRE`, `DESCARTAR`, `STATUS:<status>`, `CADASTRAR`.
Status: Pronta, Defeituosa, Danificada, Sucateada, Nao Certificada, Sem Bateria, Indisponivel.

CSV (Salvar, Compartilhar e o conteúdo publicado são o mesmo, de `montarLista(seq)`): UTF-8 **sem BOM**, `;`,
`\n`; linha `#ASIDOBEM;formato=1;codigo=…;id=…;titulo=…[;local=…][;responsavel=…];gerado_em=…`, cabeçalho
`patrimonio;operacao;descricao`, uma linha por item. Descrição ≤ 200 chars, sem `;`/quebra de linha
(`limparDescricao`); responsável sem `;`, `=` e quebras (`limparIdentificacao`). `id` =
`aaaa-mm-dd-<local|sem-local>-<seq>`. Sem `escaparCsv`: o contrato proíbe aspas/`;` nos valores. Limite local:
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
````

- [ ] **Passo 2: Reescrever `MANUAL.md`**

```markdown
# Manual de uso — Leitor de QR Codes (Polo 24)

Para quem lê as urnas em campo. Sem termos técnicos.

## Antes de começar (só na primeira vez)

1. Receba do responsável um **link de configuração** (pelo WhatsApp, só para você).
2. Toque no link. Aparece "Aparelho configurado". Pronto: não precisa fazer de novo, a não ser que o app
   avise que o acesso venceu — aí peça um link novo.
3. Quando o Chrome pedir, **permita a câmera**.

## Fazendo uma leitura

1. Abra o app e toque em **Iniciar**.
2. Digite o **código de 5 dígitos** que o ASIdoBem mostrou. Confira: ele aparece grande no alto da tela
   durante toda a leitura. Se estiver errado, o ASIdoBem **não vai ver a sua lista**.
3. Preencha o **responsável** e o **local** (POLO ou Z59, por exemplo). O app lembra do que você usou.
4. Escolha a **operação**:
   - **Recolher** — a urna volta ao polo.
   - **Transferir** — vai para outra zona (digite o número, ex.: 59) ou para o polo.
   - **Devolver TRE** — a urna sai para o TRE.
   - **Descartar** — a urna foi baixada/sucateada.
   - **Status** — mudou a condição da urna (Pronta, Defeituosa…). A urna não muda de lugar.
   - **Cadastrar** — urna nova que ainda não está no sistema.
   - Se quiser, escreva uma nota (defeito, lacre…). A operação e a nota valem para as próximas leituras
     até você mudar.
5. Toque em **Começar leitura** e no botão da **câmera**. Aponte para o QR da urna (o QR do TSE ao lado do
   código de barras). Só o QR é lido.
6. Cada leitura boa faz **dois bipes agudos** e a tela mostra "Item incluído". Um **bipe grave** é problema:
   QR que não é de patrimônio válido ou **urna já lida nesta lista**.
7. Errou? **Excluir último** (seta) tira o último item da lista; pode tocar várias vezes.
8. Terminou? Toque em **Publicar** (seta para cima). Aparece "Publicada" e o app volta ao começo,
   pronto para uma nova leitura. O ASIdoBem enxerga a lista em alguns minutos.

## Botões do rodapé

| Botão | Para quê |
|---|---|
| Seta curva | Excluir o último item lido |
| X | Cancelar a leitura inteira (pede confirmação; perde os itens) |
| Disquete | Salvar a lista em arquivo (cópia de segurança) |
| Compartilhar | Enviar o arquivo por WhatsApp, e-mail… |
| Seta para cima | **Publicar** a lista para o ASIdoBem |

## Problemas comuns

- **"Token ausente" ou "vencido"** ao tocar Iniciar: peça um novo link de configuração.
- **"Sem conexão"** ao publicar: a lista **continua na tela**. Procure sinal e toque em Publicar de novo, ou
  use Salvar/Compartilhar como cópia.
- **O app fechou ou a tela recarregou no meio da leitura**: abra de novo e toque em **Retomar**.
- **Bipe grave numa urna que você não leu ainda**: confira se o QR é o certo e se não está cortado ou
  desfocado; leia de novo com mais luz.
- **A câmera não liga**: veja se o Chrome tem permissão de câmera.
```

- [ ] **Passo 3: Reescrever `README.md`**

```markdown
# Leitor PAT — Polo 24

Aplicativo web (arquivo único, sem build) para ler o QR Code oficial do TSE das urnas no navegador do
celular, escolher a operação de cada urna e **publicar a lista** para o ASIdoBem.

🔗 **App publicado:** https://jofilho71.github.io/leitor-qrcodes-android/

Manual da equipe: **[MANUAL.md](MANUAL.md)**. Detalhes para quem mexe no código: **[CLAUDE.md](CLAUDE.md)**.

## Como funciona

```
Celular (este app) ──PUT──► repositório público asidobem-listas: listas/<id>.csv
                              GitHub Actions gera indice.csv (SHA-256)
ASIdoBem ──GET──► https://raw.githubusercontent.com/jofilho71/asidobem-listas/main/indice.csv
```

Formato das listas: ver `IMPORTACAO_WEB.md` (formato 1). No ASIdoBem: *Site…* → o endereço acima, token em
branco.

## Stack

- `index.html` único (HTML + CSS + JS), sem framework nem build.
- `BarcodeDetector` nativo com fallback `jsQR` via CDN (só QR).
- Publicação pela API de conteúdo do GitHub; sons por Web Audio.

## Configuração (uma vez)

1. Criar o repositório público `jofilho71/asidobem-listas` com o conteúdo de `repositorio-listas/`.
2. Em *Settings → Actions → General*, permitir que workflows tenham permissão de escrita.
3. Gerar, em github.com/settings/tokens, um *fine-grained token* **por aparelho**: só o repositório
   `asidobem-listas`, permissão *Contents: Read and write*, validade máxima.
4. Enviar a cada técnico, em privado: `https://jofilho71.github.io/leitor-qrcodes-android/#cfg=<token>`.
   Para revogar um aparelho, apague o token dele no GitHub. Tokens vencem em até 1 ano.

## Deploy do app

GitHub Pages serve o `index.html` da branch `master`. Um commit local não atualiza o site: é preciso
`git push origin master`; aguarde 1–2 min e recarregue com Ctrl+Shift+R.

## Testes

```bash
python3 -m pip install -r requirements-teste.txt
python3 -m playwright install chromium
python3 -m pytest tests -v
```
```

- [ ] **Passo 4: Conferir que nada ficou citando Bateria/barras como funcionalidade**

```bash
grep -n -i "bateria\|código de barras\|PAT_UE\|CDJE" CLAUDE.md MANUAL.md README.md
```

Esperado: nenhuma ocorrência, exceto "Código de barras nunca é lido"/"ao lado do código de barras" em contexto de exclusão. Ajuste o que sobrar.

- [ ] **Passo 5: Commit**

```bash
git add CLAUDE.md MANUAL.md README.md
git commit -m "docs: reescreve CLAUDE.md, MANUAL.md e README.md para o novo fluxo" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Tarefa 10: Verificação final e entrega (passos com confirmação do usuário)

**Arquivos:** nenhum novo.

- [ ] **Passo 1: Suíte completa e estado do repositório**

```bash
python3 -m pytest tests -v
git status --short
git log --oneline -12
```

Esperado: todos os testes PASS; `git status` mostra apenas os não versionados antigos (`IMPORTACAO_*.md`, `index (11).html`).

- [ ] **Passo 2: Conferir regressão visual no navegador real**

Rodar um servidor estático e abrir a página no Chrome (largura de celular) para ver as quatro telas, a leitura e o rodapé:

```bash
python3 -m http.server 8000
```

Abrir `http://localhost:8000/index.html` com o devtools em modo celular. Conferir: telas se alternam, o rodapé com 5 botões não corta em 360 px de largura (os botões podem quebrar de linha), o código aparece grande. Anotar para o usuário qualquer ajuste visual (ele disse que os detalhes de interface ficam para depois).

- [ ] **Passo 3: Pedir ao usuário as confirmações externas** (não executar sem o "pode")

Perguntar, em uma mensagem:
1. Criar o repositório público `jofilho71/asidobem-listas` com o conteúdo de `repositorio-listas/` e habilitar permissão de escrita dos workflows? (Se `gh` estiver instalado: `gh repo create jofilho71/asidobem-listas --public --source repositorio-listas --push`; senão, passo a passo manual.)
2. O usuário gera o(s) token(s) fine-grained (passo 3 do README) e os envia por link `#cfg=` aos técnicos.
3. Dar `git push origin master` para publicar o app no GitHub Pages?
4. O usuário aponta o ASIdoBem (*Site…*) para o endereço `raw.githubusercontent.com/…/indice.csv`.

- [ ] **Passo 4: Teste de ponta a ponta real (com o usuário, após os passos acima)**

1. Abrir o link de configuração no celular; Iniciar; código gerado no ASIdoBem; ler 2–3 urnas; Publicar.
2. Em ~1 min conferir no GitHub: `listas/<id>.csv` criado e `indice.csv` atualizado pelo Actions.
3. No ASIdoBem, *Buscar no site (F5)* e conferir que a lista chega, com o SHA-256 batendo.

Registrar o resultado e ajustes necessários.
