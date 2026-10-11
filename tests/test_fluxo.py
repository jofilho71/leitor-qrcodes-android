def test_inicio_mostra_so_iniciar(app):
    app.abrir()
    assert app.page.is_visible("#btn-iniciar")
    assert not app.page.is_visible("#tela-leitura")
    assert not app.page.is_visible("#rodape")
