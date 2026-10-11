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
