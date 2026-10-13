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


def test_nao_ha_campos_de_responsavel_nem_local(app):
    app.abrir()
    app.page.click("#btn-iniciar")
    app.page.fill("#input-codigo", "48213")
    app.page.click("#btn-codigo-ok")
    assert app.page.query_selector("#input-responsavel") is None
    assert app.page.query_selector("#input-local") is None


def test_transferir_comeca_a_leitura_com_qualquer_zona(app):
    app.abrir()
    app.page.click("#btn-iniciar")
    app.page.fill("#input-codigo", "48213")
    app.page.click("#btn-codigo-ok")
    app.page.select_option("#select-operacao", "TRANSFERIR")
    app.page.fill("#input-zona", "qualquer coisa")
    app.page.click("#btn-config-ok")
    assert app.page.is_visible("#tela-leitura")


def test_operacoes_oferecidas(app):
    app.abrir()
    app.page.click("#btn-iniciar")
    app.page.fill("#input-codigo", "48213")
    app.page.click("#btn-codigo-ok")
    valores = app.page.eval_on_selector_all("#select-operacao option", "o => o.map(x => x.value)")
    assert valores == ["TRANSFERIR", "EMPRESTAR", "STATUS"]
    app.page.select_option("#select-operacao", "STATUS")
    status = app.page.eval_on_selector_all("#select-status option", "o => o.map(x => x.textContent)")
    assert status == ["Laudo", "Defeito", "Pronta"]


def test_codigo_discreto_na_tela(app):
    app.abrir()
    app.iniciar()
    tamanho = app.page.evaluate("parseFloat(getComputedStyle(document.getElementById('codigo-grande')).fontSize)")
    assert tamanho <= 14


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
