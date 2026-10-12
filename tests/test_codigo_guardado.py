"""O código do ASIdoBem é digitado uma vez, no começo do trabalho, e fica guardado no aparelho.

Vale até alguém trocar; num dia novo o leitor pede para confirmar (ou digitar outro).
"""
import json

from conftest import App

HOJE = ("(() => { const d = new Date(); return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0')"
        " + '-' + String(d.getDate()).padStart(2, '0'); })()")


def hoje(app):
    return app.page.evaluate(HOJE)


def guardado(app):
    v = app.page.evaluate("localStorage.getItem('lq.codigo')")
    return json.loads(v) if v else None


def guardar(app, codigo, dia):
    app.page.evaluate("([c, d]) => localStorage.setItem('lq.codigo', JSON.stringify({codigo: c, dia: d}))", [codigo, dia])


def tocar_iniciar(app):
    app.page.click("#btn-iniciar")
    app.page.wait_for_selector("#tela-codigo:not([hidden]), #tela-config:not([hidden])")


def test_codigo_confirmado_fica_guardado_com_a_data_de_hoje(app):
    app.abrir()
    app.iniciar(codigo="48213")
    assert guardado(app) == {"codigo": "48213", "dia": hoje(app)}


def test_iniciar_com_codigo_de_hoje_pula_a_tela_de_codigo(app):
    app.abrir()
    guardar(app, "48213", hoje(app))
    tocar_iniciar(app)
    assert app.page.is_visible("#tela-config")
    assert not app.page.is_visible("#tela-codigo")
    assert app.page.inner_text("#codigo-grande") == "Código 48213"


def test_nova_lista_depois_de_publicar_nao_pede_o_codigo(app):
    app.abrir()
    app.iniciar(codigo="48213")
    app.ligar_camera()
    app.enfileirar([App.det_qr("51000001")])
    app.esperar_fila()
    app.page.click("#btn-publicar")
    app.page.wait_for_selector("#tela-inicio:not([hidden])")
    assert "48213" in app.page.inner_text("#codigo-atual")
    tocar_iniciar(app)
    assert app.page.is_visible("#tela-config")
    app.page.click("#btn-config-ok")
    app.page.wait_for_selector("#tela-leitura:not([hidden])")
    app.ligar_camera()
    app.enfileirar([App.det_qr("51000002")])
    app.esperar_fila()
    app.page.click("#btn-publicar")
    app.page.wait_for_selector("#tela-inicio:not([hidden])")
    assert len(app.puts) == 2
    assert app.csv_publicado(1).split("\n")[0].startswith("#ASIDOBEM;formato=1;codigo=48213;id=")


def test_codigo_de_outro_dia_pede_confirmacao_e_nao_pede_digitar(app):
    app.abrir()
    guardar(app, "48213", "2020-01-01")
    tocar_iniciar(app)
    assert app.page.is_visible("#tela-codigo")
    assert app.page.input_value("#input-codigo") == "48213"
    aviso = app.page.inner_text("#aviso-codigo")
    assert "48213" in aviso and "01/01/2020" in aviso
    app.page.click("#btn-codigo-ok")
    assert app.page.is_visible("#tela-config")
    assert guardado(app) == {"codigo": "48213", "dia": hoje(app)}


def test_codigo_de_hoje_nao_mostra_aviso_de_outro_dia(app):
    app.abrir()
    guardar(app, "48213", hoje(app))
    tocar_iniciar(app)
    app.page.click("#btn-config-voltar")
    assert app.page.inner_text("#aviso-codigo").strip() == ""


def test_trocar_o_codigo_pelo_voltar_da_configuracao(app):
    app.abrir()
    guardar(app, "48213", hoje(app))
    tocar_iniciar(app)
    app.page.click("#btn-config-voltar")
    assert app.page.is_visible("#tela-codigo")
    assert app.page.input_value("#input-codigo") == "48213"
    app.page.fill("#input-codigo", "55555")
    app.page.click("#btn-codigo-ok")
    assert app.page.inner_text("#codigo-grande") == "Código 55555"
    assert guardado(app) == {"codigo": "55555", "dia": hoje(app)}


def test_codigo_novo_invalido_nao_substitui_o_guardado(app):
    app.abrir()
    guardar(app, "48213", hoje(app))
    tocar_iniciar(app)
    app.page.click("#btn-config-voltar")
    app.page.fill("#input-codigo", "123")
    app.page.click("#btn-codigo-ok")
    assert app.page.is_visible("#tela-codigo")
    assert guardado(app)["codigo"] == "48213"


def test_codigo_guardado_invalido_e_ignorado(app):
    app.abrir()
    for lixo in ["abc", "01234", "123456", ""]:
        guardar(app, lixo, hoje(app))
        app.page.reload()
        tocar_iniciar(app)
        assert app.page.is_visible("#tela-codigo"), lixo
        assert app.page.input_value("#input-codigo") == "", lixo
    app.page.evaluate("localStorage.setItem('lq.codigo', '{quebrado')")
    app.page.reload()
    tocar_iniciar(app)
    assert app.page.is_visible("#tela-codigo")


def test_excluir_tudo_nao_apaga_o_codigo(app):
    app.abrir()
    app.iniciar(codigo="48213")
    app.page.click("#btn-cancelar")
    app.page.wait_for_selector("#tela-inicio:not([hidden])")
    assert guardado(app)["codigo"] == "48213"


def test_codigo_continua_discreto_na_leitura(app):
    app.abrir()
    app.iniciar(codigo="48213")
    tamanho = app.page.evaluate("parseFloat(getComputedStyle(document.getElementById('codigo-grande')).fontSize)")
    assert tamanho <= 13
