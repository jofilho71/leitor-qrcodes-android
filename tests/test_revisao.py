import base64
import json

from conftest import App

ATRASO = """
() => {
  const f = window.fetch;
  window.fetch = async (u, o) => {
    if (o && o.method === 'PUT') await new Promise(r => setTimeout(r, 1500));
    return f(u, o);
  };
}
"""


def preparar(app, n, atraso=False, **kw):
    app.abrir()
    if atraso:
        app.page.evaluate(ATRASO)
    app.iniciar(**kw)
    app.ligar_camera()
    if n:
        app.enfileirar(*[[App.det_qr(f"5100000{i + 1}")] for i in range(n)])
        app.esperar_fila()


# ---- C1-C3: nada muda enquanto a publicação está em andamento ----
def test_item_lido_durante_publicacao_nao_se_perde_nem_e_contado(app):
    preparar(app, 1, atraso=True)
    app.page.click("#btn-publicar")
    app.page.wait_for_timeout(300)
    app.enfileirar([App.det_qr("51000009")])
    app.page.wait_for_timeout(900)
    app.page.wait_for_selector("#tela-inicio:not([hidden])", timeout=10000)
    linhas_dados = app.csv_publicado(0).strip().split("\n")[2:]
    assert linhas_dados == ["51000001;EMPRESTAR;"]
    assert "Publicada (1 linhas)" in app.page.inner_text("#aviso-inicio")


def test_cancelar_e_excluir_ficam_desabilitados_durante_publicacao(app):
    preparar(app, 2, atraso=True)
    app.page.click("#btn-publicar")
    app.page.wait_for_timeout(300)
    assert app.page.is_disabled("#btn-cancelar")
    assert app.page.is_disabled("#btn-excluir-ultimo")
    app.page.wait_for_selector("#tela-inicio:not([hidden])", timeout=10000)
    assert len(app.csv_publicado(0).strip().split("\n")[2:]) == 2


# ---- I1: dois QRs já lidos no quadro não apitam sem parar ----
def test_dois_qrs_ja_lidos_no_quadro_apitam_erro_uma_vez_cada(app):
    preparar(app, 2)
    app.page.wait_for_timeout(2300)  # os dois saíram de vista
    app.page.evaluate("window.__tons = []")
    dois = [App.det_qr("51000001"), App.det_qr("51000002")]
    app.enfileirar(*[dois for _ in range(6)])
    app.esperar_fila()
    assert app.page.evaluate("window.__tons").count(180) == 2


# ---- I2: excluir duas vezes com os dois QRs ainda à vista não readiciona ----
def test_excluir_duas_vezes_com_dois_qrs_a_vista_nao_readiciona(app):
    preparar(app, 0)
    dois = [App.det_qr("51000001"), App.det_qr("51000002")]
    app.enfileirar(dois, dois)
    app.esperar_fila()
    assert len(app.itens()) == 2
    app.page.click("#btn-excluir-ultimo")
    app.page.click("#btn-excluir-ultimo")
    app.enfileirar(dois, dois)
    app.esperar_fila()
    assert app.itens() == []


# ---- I4: resposta perdida + nova tentativa não duplica a lista ----
def test_resposta_perdida_e_nova_tentativa_nao_publica_duas_vezes(app):
    app.simular_existentes = True
    app.perder_resposta = 1
    preparar(app, 2)
    app.page.click("#btn-publicar")
    app.page.wait_for_selector("#erro-camera", state="visible")
    assert app.page.is_visible("#tela-leitura")
    app.page.click("#btn-publicar")
    app.page.wait_for_selector("#tela-inicio:not([hidden])", timeout=10000)
    assert len(app.arquivos) == 1
    assert "Publicada (2 linhas)" in app.page.inner_text("#aviso-inicio")


def test_id_ocupado_por_lista_diferente_ainda_incrementa(app):
    app.simular_existentes = True
    preparar(app, 1)
    app.page.evaluate("() => 0")
    # lista de outro técnico já ocupa o -01 (conteúdo diferente)
    app.arquivos = {u: "b3V0cm8=" for u in [
        f"https://api.github.com/repos/jofilho71/asidobem-listas/contents/listas/"
        + app.page.evaluate("() => { const d = new Date(); const p = n => String(n).padStart(2,'0'); return `${d.getFullYear()}-${p(d.getMonth()+1)}-${p(d.getDate())}-48213-01.csv`; }")
    ]}
    app.page.click("#btn-publicar")
    app.page.wait_for_selector("#tela-inicio:not([hidden])", timeout=10000)
    assert len(app.arquivos) == 2


# ---- I5: o id do CSV de backup não colide com o publicado (-01) ----
def test_csv_de_backup_usa_id_proprio(app):
    preparar(app, 1)
    linha = app.baixar_csv().split("\n")[0]
    assert "-48213-01;" not in linha
    assert any(p.startswith("id=") and p.endswith(tuple("0123456789")) and len(p.split("-")[-1]) == 6
               for p in linha.split(";"))


# ---- I6: limite aplicado na leitura e checagem de tamanho ----
def _sessao_grande(app, n, descricao=""):
    app.abrir()
    app.page.evaluate(
        """([n, d]) => localStorage.setItem('lq.sessao', JSON.stringify({
              codigo: '48213', responsavel: '', local: '',
              itens: Array.from({length: n}, (_, i) => ({
                codigo: '51' + String(i).padStart(6, '0'), operacao: 'EMPRESTAR', descricao: d})),
              op: {}}))""", [n, descricao])
    app.page.reload()
    app.page.click("#btn-retomar")
    app.page.wait_for_function(f"document.getElementById('contador-texto').textContent.includes('{n}')")


def test_leitura_alem_do_limite_e_recusada_com_erro(app):
    _sessao_grande(app, 15000)
    app.ligar_camera()
    app.page.evaluate("window.__tons = []")
    app.enfileirar([App.det_qr("51999999")])
    app.esperar_fila()
    assert "15000" in app.page.inner_text("#contador-texto")
    assert app.page.evaluate("window.__tons") == [180]


def test_lista_acima_de_5mb_nao_e_publicada(app):
    _sessao_grande(app, 14000, descricao="é" * 200)
    app.page.click("#btn-publicar")
    app.page.wait_for_selector("#erro-camera", state="visible")
    assert "5 MB" in app.page.inner_text("#erro-camera")
    assert app.puts == []


# ---- layout e cores (pedido do usuário) ----
def _cor(app, seletor, prop="borderTopColor"):
    return app.page.evaluate(f"getComputedStyle(document.querySelector('{seletor}')).{prop}")


def test_botoes_coloridos(app):
    app.abrir()
    app.iniciar()
    verde = _cor(app, "#btn-publicar")
    claro = _cor(app, "#btn-excluir-ultimo")
    escuro = _cor(app, "#btn-cancelar")
    padrao = _cor(app, "#btn-csv")

    def rgb(c):
        return [int(x) for x in c[c.index("(") + 1:c.index(")")].split(",")[:3]]
    g, l, e = rgb(verde), rgb(claro), rgb(escuro)
    assert g[1] > g[0] and g[1] > g[2]                       # verde
    assert l[0] > 200 and l[1] > 80 and l[0] > l[1] + 60     # vermelho claro
    assert e[0] < 190 and e[0] > e[1] + 60 and e[1] < 60     # vermelho escuro
    assert padrao == _cor(app, "#btn-compartilhar")          # Salvar e Compartilhar mantêm o padrão


def test_camera_ocupa_menos_da_tela(app):
    app.abrir()
    app.iniciar()
    app.ligar_camera()
    altura = app.page.evaluate("document.getElementById('camera-wrap').getBoundingClientRect().height")
    assert altura <= 780 * 0.42
    assert altura >= 150
