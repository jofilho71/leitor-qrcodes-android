"""Câmera: abertura concorrente, lente, fallback jsQR e segundo plano."""
import json

from conftest import App

# conta streams/trilhas abertos e registra as restrições pedidas; __atraso adia o getUserMedia
CONTAR = """
window.__streams = []; window.__pedidos = []; window.__atraso = 0;
const orig = navigator.mediaDevices.getUserMedia;
navigator.mediaDevices.getUserMedia = async function (c) {
  window.__pedidos.push(c);
  if (window.__atraso) await new Promise(r => setTimeout(r, window.__atraso));
  const s = await orig(c);
  window.__streams.push(s);
  return s;
};
window.__vivas = () => window.__streams.reduce((n, s) => n + s.getTracks().filter(t => t.readyState === 'live').length, 0);
"""

LENTES = [
    {"kind": "videoinput", "deviceId": "t1", "label": "camera2 0, facing back"},
    {"kind": "videoinput", "deviceId": "f1", "label": "camera2 1, facing front"},
    {"kind": "videoinput", "deviceId": "t2", "label": "camera2 2, facing back"},
]


def abrir(app, atraso=0):
    """Abre o app e inicia a leitura; a câmera liga sozinha (com `atraso` ms no getUserMedia)."""
    app.abrir()
    app.page.evaluate(CONTAR)
    app.page.evaluate("a => { window.__atraso = a; }", atraso)
    app.iniciar()


def test_botao_lente_so_aparece_com_a_camera_ligada(app):
    abrir(app)
    app.ligar_camera()
    assert app.page.is_visible("#btn-lente")
    app.page.click("#btn-camera")
    assert not app.page.is_visible("#btn-lente")


def test_comecar_leitura_liga_a_camera_sozinha(app):
    abrir(app)
    app.page.wait_for_selector("body.camera-ativa")
    assert app.page.evaluate("window.__vivas()") == 1


def test_toque_duplo_em_camera_nao_deixa_trilha_viva(app):
    abrir(app, atraso=400)
    # a abertura automática ainda está em andamento: o 1º toque a cancela, o 2º abre outra
    app.page.click("#btn-camera")
    app.page.click("#btn-camera")
    app.page.wait_for_selector("body.camera-ativa")
    app.page.wait_for_timeout(1000)
    assert app.page.evaluate("window.__vivas()") == 1  # nenhum stream órfão


def test_parar_durante_a_abertura_nao_deixa_camera_ligada(app):
    abrir(app, atraso=400)
    app.page.click("#btn-camera")  # cancela a abertura em andamento
    app.page.wait_for_timeout(1500)
    assert app.page.evaluate("window.__vivas()") == 0
    assert not app.page.evaluate("document.body.classList.contains('camera-ativa')")


def test_lente_cicla_so_entre_traseiras_e_guarda_a_escolha(app):
    abrir(app)
    app.page.evaluate("l => { navigator.mediaDevices.enumerateDevices = async () => l; }", LENTES)
    app.ligar_camera()
    app.page.click("#btn-lente")
    app.page.wait_for_function("localStorage.getItem('lq.lente') !== null")
    escolhida = json.loads(app.page.evaluate("localStorage.getItem('lq.lente')"))
    assert escolhida in ("t1", "t2")  # nunca a frontal
    app.page.wait_for_selector("body.camera-ativa")
    ultimo = app.page.evaluate("window.__pedidos[window.__pedidos.length - 1]")
    assert ultimo["video"]["deviceId"] == {"exact": escolhida}
    assert app.page.evaluate("window.__vivas()") == 1  # a anterior foi parada


def test_lente_guardada_invalida_cai_no_padrao_e_apaga_a_chave(app):
    abrir(app)
    app.page.evaluate("""() => {
      localStorage.setItem('lq.lente', JSON.stringify('sumiu'));
      const g = navigator.mediaDevices.getUserMedia;
      navigator.mediaDevices.getUserMedia = async (c) => {
        if (c.video.deviceId) { const e = new Error('x'); e.name = 'OverconstrainedError'; throw e; }
        return g(c);
      };
    }""")
    app.religar_camera()
    assert app.page.evaluate("localStorage.getItem('lq.lente')") is None


def test_lente_guardada_com_falha_passageira_nao_e_apagada(app):
    abrir(app)
    app.page.evaluate("""() => {
      localStorage.setItem('lq.lente', JSON.stringify('t2'));
      const g = navigator.mediaDevices.getUserMedia;
      navigator.mediaDevices.getUserMedia = async (c) => {
        if (c.video.deviceId) { const e = new Error('ocupada'); e.name = 'NotReadableError'; throw e; }
        return g(c);
      };
    }""")
    app.religar_camera()
    assert json.loads(app.page.evaluate("localStorage.getItem('lq.lente')")) == "t2"


def test_so_uma_lente_avisa(app):
    abrir(app)
    app.page.evaluate("l => { navigator.mediaDevices.enumerateDevices = async () => l; }", LENTES[:1])
    app.ligar_camera()
    app.page.click("#btn-lente")
    app.page.wait_for_selector("#erro-camera", state="visible")
    assert "só mostra uma lente" in app.page.inner_text("#erro-camera")


def test_nativo_com_erro_cai_no_jsqr(app):
    app.abrir()
    app.page.evaluate("""() => {
      window.BarcodeDetector = class { constructor() {} async detect() { throw new Error('indisponível'); } };
      window.__jsqr = [{ data: 'APLC:TSE APLF:QRC.PATR VERE:1 TPEQ:UE MDEQ:UE2020 IDEQ:51432890' }];
      window.jsQR = () => window.__jsqr.shift() || null;
    }""")
    app.iniciar()
    app.ligar_camera()
    app.page.wait_for_function("document.querySelectorAll('#lista-itens .item').length === 1", timeout=15000)
    assert app.itens() == [["51432890", "EMPRESTAR"]]


def test_nativo_vazio_consulta_o_jsqr(app):
    app.abrir()
    app.page.evaluate("""() => {
      window.__jsqr = [{ data: 'APLC:TSE APLF:QRC.PATR VERE:1 TPEQ:UE MDEQ:UE2020 IDEQ:51432890' }];
      window.jsQR = () => window.__jsqr.shift() || null;
    }""")
    app.iniciar()
    app.ligar_camera()
    app.page.wait_for_function("document.querySelectorAll('#lista-itens .item').length === 1", timeout=15000)


def test_nativo_funcionando_sem_jsqr_nao_mostra_aviso_falso(app):
    app.abrir()
    app.page.evaluate("delete window.jsQR")  # o CDN também está bloqueado nos testes
    app.iniciar()
    app.ligar_camera()
    app.page.wait_for_timeout(2500)  # vários quadros vazios
    assert not app.page.is_visible("#erro-camera")


def test_sem_nativo_e_sem_jsqr_avisa(app):
    app.abrir()
    app.page.evaluate("delete window.jsQR; delete window.BarcodeDetector")
    app.iniciar()
    app.ligar_camera()
    app.page.wait_for_selector("#erro-camera", state="visible", timeout=10000)
    assert "indisponível" in app.page.inner_text("#erro-camera")


def test_detect_lento_nao_empilha_chamadas(app):
    app.abrir()
    app.page.evaluate("""() => {
      window.__ativas = 0; window.__maxAtivas = 0;
      window.BarcodeDetector = class {
        constructor() {}
        async detect() {
          window.__ativas++; window.__maxAtivas = Math.max(window.__maxAtivas, window.__ativas);
          await new Promise(r => setTimeout(r, 900));
          window.__ativas--; return [];
        }
      };
    }""")
    app.iniciar()
    app.ligar_camera()
    app.page.wait_for_timeout(3000)
    assert app.page.evaluate("window.__maxAtivas") == 1


def test_app_em_segundo_plano_desliga_a_camera(app):
    abrir(app)
    app.ligar_camera()
    app.page.evaluate("""() => {
      Object.defineProperty(document, 'hidden', { get: () => true, configurable: true });
      document.dispatchEvent(new Event('visibilitychange'));
    }""")
    assert not app.page.evaluate("document.body.classList.contains('camera-ativa')")
    assert app.page.evaluate("window.__vivas()") == 0


def test_trilha_encerrada_avisa_e_desliga(app):
    abrir(app)
    app.ligar_camera()
    app.page.evaluate("""() => {
      const t = window.__streams[window.__streams.length - 1].getVideoTracks()[0];
      t.stop(); t.dispatchEvent(new Event('ended'));
    }""")
    app.page.wait_for_selector("#erro-camera", state="visible")
    assert "interrompida" in app.page.inner_text("#erro-camera")
    assert not app.page.evaluate("document.body.classList.contains('camera-ativa')")


def test_sessao_salva_com_operacao_invalida_e_descartada(app):
    app.abrir()
    app.page.evaluate("""() => localStorage.setItem('lq.sessao', JSON.stringify({
      codigo: '48213', itens: [{ codigo: '51432890', operacao: 'EMPRESTAR;x', descricao: '' }] }))""")
    app.page.reload()
    assert app.page.is_hidden("#caixa-retomar") or app.page.evaluate("document.getElementById('caixa-retomar').hidden")
    assert app.page.evaluate("localStorage.getItem('lq.sessao')") is None
