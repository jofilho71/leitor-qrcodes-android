import json

from conftest import App


def lendo(app, **kw):
    app.abrir()
    app.iniciar(**kw)
    app.ligar_camera()


def test_retomar_apos_recarregar(app):
    lendo(app, codigo="48213")
    p = app.page
    p.select_option("#select-operacao", "STATUS")
    p.select_option("#select-status", "Defeito")
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
    assert app.itens() == [["51000001", "STATUS:Defeito"], ["51000002", "STATUS:Defeito"]]
    assert p.input_value("#select-operacao") == "STATUS"
    assert p.input_value("#select-status") == "Defeito"
    assert p.input_value("#texto-livre") == "lacre 7"
    # o conjunto de patrimônios já lidos também volta
    app.ligar_camera()
    app.enfileirar([App.det_qr("51000001")])
    app.esperar_fila()
    assert len(app.itens()) == 2
    # e a lista retomada gera o CSV com a identificação original
    linha = app.baixar_csv().split("\n")[0]
    assert "codigo=48213" in linha


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
        {"codigo": "abc", "itens": [{"codigo": "51000001", "operacao": "EMPRESTAR", "descricao": ""}]},
        {"codigo": "48213", "itens": [{"codigo": "<img src=x>", "operacao": "EMPRESTAR", "descricao": ""}]},
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
