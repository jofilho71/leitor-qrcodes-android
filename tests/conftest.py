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
        self.simular_existentes = False   # PUT em arquivo já gravado -> 422; GET devolve o conteúdo
        self.perder_resposta = 0          # próximos PUTs gravam no servidor mas a resposta se perde
        self.arquivos = {}

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
        if request.method == "GET" and "/contents/" in request.url:
            conteudo = self.arquivos.get(request.url)
            if conteudo is None:
                return route.fulfill(status=404, headers=cors, content_type="application/json", body="{}")
            return route.fulfill(status=200, headers=cors, content_type="application/json",
                                 body=json.dumps({"content": conteudo, "encoding": "base64"}))
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
            if self.simular_existentes:
                corpo = json.loads(request.post_data)
                if request.url in self.arquivos:
                    return route.fulfill(status=422, headers=cors, content_type="application/json",
                                         body=json.dumps({"message": "\"sha\" wasn't supplied."}))
                self.arquivos[request.url] = corpo["content"]
                if self.perder_resposta:
                    self.perder_resposta -= 1
                    return route.abort()
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

    def iniciar(self, codigo="48213", operacao="EMPRESTAR"):
        p = self.page
        p.click("#btn-iniciar")
        # com código guardado de hoje o leitor pula a tela de código
        p.wait_for_selector("#tela-codigo:not([hidden]), #tela-config:not([hidden])")
        if p.is_visible("#tela-codigo"):
            p.fill("#input-codigo", codigo)
            p.click("#btn-codigo-ok")
        p.select_option("#select-operacao", operacao)
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
