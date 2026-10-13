import re

import pytest

from conftest import PNG_1x1, App


def lendo(app, **kw):
    app.abrir()
    app.iniciar(**kw)
    app.ligar_camera()


def test_aceita_qr_valido_e_grava_ideq_puro(app):
    lendo(app)
    app.enfileirar([App.det_qr("51432890")])
    app.esperar_fila()
    assert app.itens() == [["51432890", "EMPRESTAR"]]
    assert "1" in app.page.inner_text("#contador-texto")


def test_codigo_de_barras_nunca_e_lido(app):
    lendo(app)
    app.enfileirar([App.det_barra("4551432890")], [App.det_barra("51432890")])
    app.esperar_fila()
    assert app.itens() == []


@pytest.mark.parametrize("bruto", ["https://exemplo.com/x", "APLC:TSE APLF:QRC.PATR", "qualquer texto"])
def test_qr_sem_ideq_e_ignorado(app, bruto):
    lendo(app)
    app.enfileirar([{"rawValue": bruto, "format": "qr_code"}])
    app.esperar_fila()
    assert app.itens() == []


@pytest.mark.parametrize("ideq", ["12345678", "5143289", "514328901", "41432890", "5143289A"])
def test_ideq_fora_do_padrao_e_ignorado(app, ideq):
    lendo(app)
    app.enfileirar([App.det_qr(ideq)])
    app.esperar_fila()
    assert app.itens() == []


def test_frames_repetidos_contam_uma_vez(app):
    lendo(app)
    app.enfileirar(*[[App.det_qr("51432890")] for _ in range(5)])
    app.esperar_fila()
    assert len(app.itens()) == 1


def test_repetido_na_sessao_e_descartado_mesmo_depois_de_outro(app):
    lendo(app)
    app.enfileirar([App.det_qr("51432890")], [App.det_qr("51432891")], [App.det_qr("51432890")])
    app.esperar_fila()
    assert [i[0] for i in app.itens()] == ["51432890", "51432891"]


def test_semelhante_ao_ultimo_nao_e_mais_descartado(app):
    lendo(app)
    app.enfileirar([App.det_qr("51432890")], [App.det_qr("51432891")], [App.det_qr("51432990")])
    app.esperar_fila()
    assert len(app.itens()) == 3


def test_mesmo_ideq_com_outros_campos_diferentes_e_duplicado(app):
    lendo(app)
    app.enfileirar([App.det_qr("51432890", vere="1")], [App.det_qr("51432890", vere="2")])
    app.esperar_fila()
    assert len(app.itens()) == 1


def test_qr_com_espaco_e_quebra_de_linha_no_final_e_aceito(app):
    lendo(app)
    det = App.det_qr("51432890")
    det["rawValue"] += "  \n"
    app.enfileirar([det])
    app.esperar_fila()
    assert app.itens() == [["51432890", "EMPRESTAR"]]


def test_duplicado_entre_camera_e_galeria(app):
    lendo(app)
    app.enfileirar([App.det_qr("51432890")])
    app.esperar_fila()
    app.enfileirar([App.det_qr("51432890")])
    app.page.set_input_files("#input-fotos", {"name": "f.png", "mimeType": "image/png", "buffer": PNG_1x1})
    app.esperar_fila()
    assert len(app.itens()) == 1


def test_galeria_sem_codigo_avisa(app):
    app.abrir()
    app.iniciar()
    app.page.set_input_files("#input-fotos", {"name": "f.png", "mimeType": "image/png", "buffer": PNG_1x1})
    app.page.wait_for_selector("#erro-camera", state="visible", timeout=15000)
    assert "Nenhum código encontrado" in app.page.inner_text("#erro-camera")
    assert app.itens() == []


def test_operacoes_e_parametros(app):
    lendo(app)
    p = app.page

    def ler(ideq):
        app.enfileirar([App.det_qr(ideq)])
        app.esperar_fila()

    ler("51000001")  # EMPRESTAR é o que o helper escolhe
    p.select_option("#select-operacao", "TRANSFERIR")
    assert p.is_visible("#input-zona")
    p.fill("#input-zona", "59")
    ler("51000002")
    p.fill("#input-zona", "polo")
    ler("51000003")
    p.select_option("#select-operacao", "STATUS")
    assert p.is_visible("#select-status") and not p.is_visible("#input-zona")
    p.select_option("#select-status", "Defeito")
    ler("51000004")
    p.select_option("#select-status", "Laudo")
    ler("51000005")
    p.select_option("#select-status", "Pronta")
    ler("51000006")
    assert app.itens() == [
        ["51000001", "EMPRESTAR"],
        ["51000002", "TRANSFERIR:Z59"],
        ["51000003", "TRANSFERIR:POLO"],
        ["51000004", "STATUS:Defeituosa"],
        ["51000005", "STATUS:Defeituosa"],
        ["51000006", "STATUS:Pronta"],
    ]


def test_zona_invalida_nao_aceita_e_corrigir_aceita_a_mesma_urna(app):
    lendo(app)
    p = app.page
    p.select_option("#select-operacao", "TRANSFERIR")
    p.fill("#input-zona", "abc")
    app.enfileirar([App.det_qr("51000001")])
    app.esperar_fila()
    assert app.itens() == []
    assert "invalido" in p.get_attribute("#input-zona", "class")
    p.fill("#input-zona", "z012")
    app.enfileirar([App.det_qr("51000001")])
    app.esperar_fila()
    assert app.itens() == [["51000001", "TRANSFERIR:Z12"]]


def test_csv_formato_1(app):
    lendo(app, codigo="48213")
    p = app.page
    p.fill("#texto-livre", "Não liga; tela apagada")
    app.enfileirar([App.det_qr("51000001")])
    app.esperar_fila()
    p.fill("#texto-livre", "")
    p.select_option("#select-operacao", "STATUS")
    app.enfileirar([App.det_qr("51000002")])
    app.esperar_fila()
    csv = app.baixar_csv()
    linhas = csv.split("\n")
    assert re.fullmatch(
        r"#ASIDOBEM;formato=1;codigo=48213;id=\d{4}-\d{2}-\d{2}-48213-\d{6};titulo=Inventário \d{2}/\d{2};"
        r"gerado_em=\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2}",
        linhas[0],
    )
    assert linhas[1] == "patrimonio;operacao;descricao"
    assert linhas[2] == "51000001;EMPRESTAR;Não liga tela apagada"
    assert linhas[3] == "51000002;STATUS:Defeituosa;LAUDO"
    assert csv.endswith("\n") and not csv.startswith("﻿")


def test_lista_em_tela_segue_a_ordem_do_csv(app):
    lendo(app)
    app.enfileirar([App.det_qr("51000001")], [App.det_qr("51000002")], [App.det_qr("51000003")])
    app.esperar_fila()
    ordens = app.page.eval_on_selector_all("#lista-itens .ordem", "els => els.map(e => e.textContent)")
    assert ordens == ["1.", "2.", "3."]
    csv_codigos = [l.split(";")[0] for l in app.baixar_csv().split("\n")[2:5]]
    assert csv_codigos == [i[0] for i in app.itens()]


def test_falha_de_getusermedia_mostra_erro_sem_camera_fantasma(app):
    app.abrir()
    app.iniciar()
    app.page.evaluate("() => { navigator.mediaDevices.getUserMedia = () => Promise.reject(new Error('negada')); }")
    app.page.click("#btn-camera")
    app.page.wait_for_selector("#erro-camera", state="visible")
    assert "Câmera indisponível" in app.page.inner_text("#erro-camera")
    assert app.page.evaluate("document.body.classList.contains('camera-ativa')") is False


def test_falha_de_play_para_o_stream_e_mostra_erro(app):
    app.abrir()
    app.iniciar()
    app.page.evaluate("() => { HTMLMediaElement.prototype.play = () => Promise.reject(new Error('bloqueado')); }")
    app.page.click("#btn-camera")
    app.page.wait_for_selector("#erro-camera", state="visible")
    assert "falha ao iniciar o vídeo" in app.page.inner_text("#erro-camera")
    assert app.page.evaluate("document.body.classList.contains('camera-ativa')") is False
    assert app.page.evaluate("document.getElementById('video').srcObject === null") is True


def test_laudo_vai_como_defeituosa_com_descricao_laudo(app):
    lendo(app)
    p = app.page
    p.select_option("#select-operacao", "STATUS")
    p.select_option("#select-status", "Laudo")
    app.enfileirar([App.det_qr("51000001")])
    app.esperar_fila()
    p.fill("#texto-livre", "lacre 7")
    app.enfileirar([App.det_qr("51000002")])
    app.esperar_fila()
    p.select_option("#select-status", "Defeito")
    app.enfileirar([App.det_qr("51000003")])
    app.esperar_fila()
    p.select_option("#select-status", "Pronta")
    p.fill("#texto-livre", "")
    app.enfileirar([App.det_qr("51000004")])
    app.esperar_fila()
    dados = app.baixar_csv().strip().split("\n")[2:]
    assert dados == [
        "51000001;STATUS:Defeituosa;LAUDO",
        "51000002;STATUS:Defeituosa;LAUDO - lacre 7",
        "51000003;STATUS:Defeituosa;lacre 7",
        "51000004;STATUS:Pronta;",
    ]


@pytest.mark.parametrize("zona, esperado", [
    ("161", "Z161"), ("Z161", "Z161"), ("z161", "Z161"), ("Zona 161", "Z161"), ("zona161", "Z161"),
    ("Z 161", "Z161"), ("Z-161", "Z161"), ("ZE161", "Z161"), ("161ª", "Z161"), (" 059 ", "Z59"), ("Polo", "POLO"),
])
def test_zona_aceita_grafias_comuns(app, zona, esperado):
    lendo(app)
    p = app.page
    p.select_option("#select-operacao", "TRANSFERIR")
    p.fill("#input-zona", zona)
    app.enfileirar([App.det_qr("51000001")])
    app.esperar_fila()
    assert app.itens() == [["51000001", "TRANSFERIR:" + esperado]]


@pytest.mark.parametrize("zona", ["0", "Z0", "1000", "1 61", "Zona 16 1", "X161", "161 POLO", "PO"])
def test_zona_recusa_o_que_nao_e_zona(app, zona):
    lendo(app)
    p = app.page
    p.select_option("#select-operacao", "TRANSFERIR")
    p.fill("#input-zona", zona)
    app.enfileirar([App.det_qr("51000001")])
    app.esperar_fila()
    assert app.itens() == []
