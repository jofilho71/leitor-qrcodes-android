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
    app.page.evaluate("() => { window.AudioContext = undefined; window.webkitAudioContext = undefined; }")
    app.iniciar()
    app.ligar_camera()
    app.enfileirar([App.det_qr("51000001")])
    app.esperar_fila()
    assert len(app.itens()) == 1
    assert app.erros_pagina == []
