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
