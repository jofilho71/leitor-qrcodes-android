import json

from conftest import REPO, TOKEN_TESTE, App


def preparar(app, n=2, **kw):
    app.abrir()
    app.iniciar(**kw)
    app.ligar_camera()
    app.enfileirar(*[[App.det_qr(f"5100000{i + 1}")] for i in range(n)])
    app.esperar_fila()


def test_publicar_envia_csv_e_volta_ao_inicio(app):
    preparar(app, n=2, codigo="48213")
    app.page.click("#btn-publicar")
    app.page.wait_for_selector("#tela-inicio:not([hidden])")
    put = app.puts[0]
    csv = app.csv_publicado(0)
    id_lista = csv.split("\n")[0].split(";")[3].removeprefix("id=")
    assert put["url"].endswith(f"/repos/{REPO}/contents/listas/{id_lista}.csv")
    assert put["auth"] == "Bearer " + TOKEN_TESTE
    assert "sha" not in put["corpo"]
    assert csv.split("\n")[0].startswith("#ASIDOBEM;formato=1;codigo=48213;id=")
    assert csv.split("\n")[2:4] == ["51000001;EMPRESTAR;", "51000002;EMPRESTAR;"]
    assert "Publicada (2 linhas)" in app.page.inner_text("#aviso-inicio")
    assert app.page.evaluate("localStorage.getItem('lq.sessao')") is None
    app.iniciar(codigo="48213")  # nova configuração oferecida
    assert app.itens() == []


def test_id_incrementa_quando_o_arquivo_ja_existe(app):
    app.respostas_put = [(422, {"message": 'Invalid request.\n\n"sha" wasn\'t supplied.'}), (201, {})]
    preparar(app, n=1)
    app.page.click("#btn-publicar")
    app.page.wait_for_selector("#tela-inicio:not([hidden])")
    assert len(app.puts) == 2
    assert app.puts[0]["url"].endswith("-48213-01.csv")
    assert app.puts[1]["url"].endswith("-48213-02.csv")
    assert app.csv_publicado(1).split("\n")[0].count("-48213-02") == 1


def test_422_por_outro_motivo_nao_incrementa_e_mantem_a_lista(app):
    app.respostas_put = [(422, {"message": "Validation Failed"})]
    preparar(app, n=1)
    app.page.click("#btn-publicar")
    app.page.wait_for_selector("#erro-camera", state="visible")
    assert len(app.puts) == 1
    assert "HTTP 422" in app.page.inner_text("#erro-camera")
    assert len(app.itens()) == 1


def test_conflito_409_tenta_de_novo_o_mesmo_id(app):
    app.respostas_put = [(409, {"message": "conflict"}), (201, {})]
    preparar(app, n=1)
    app.page.click("#btn-publicar")
    app.page.wait_for_selector("#tela-inicio:not([hidden])", timeout=10000)
    assert len(app.puts) == 2
    assert app.puts[0]["url"] == app.puts[1]["url"]


def test_falha_de_rede_mantem_a_lista_e_permite_tentar_de_novo(app):
    preparar(app, n=2)
    app.rede_caida = True
    app.page.click("#btn-publicar")
    app.page.wait_for_selector("#erro-camera", state="visible")
    assert "Sem conexão" in app.page.inner_text("#erro-camera")
    assert app.page.is_visible("#tela-leitura")
    assert len(app.itens()) == 2
    assert app.page.is_enabled("#btn-publicar")
    app.rede_caida = False
    app.page.click("#btn-publicar")
    app.page.wait_for_selector("#tela-inicio:not([hidden])")
    assert len(app.puts) == 1


def test_token_rejeitado_na_publicacao_mantem_a_lista(app):
    app.respostas_put = [(401, {"message": "Bad credentials"})]
    preparar(app, n=1)
    app.page.click("#btn-publicar")
    app.page.wait_for_selector("#erro-camera", state="visible")
    assert "token" in app.page.inner_text("#erro-camera").lower()
    assert len(app.itens()) == 1


def test_sem_token_no_momento_de_publicar(app):
    preparar(app, n=1)
    app.page.evaluate("localStorage.removeItem('lq.token')")
    app.page.click("#btn-publicar")
    app.page.wait_for_selector("#erro-camera", state="visible")
    assert "token" in app.page.inner_text("#erro-camera").lower()
    assert app.puts == []


def test_toque_duplo_em_publicar_envia_uma_vez(app):
    app.atraso_put = 0.6
    preparar(app, n=1)
    app.page.dblclick("#btn-publicar")
    app.page.wait_for_selector("#tela-inicio:not([hidden])", timeout=10000)
    app.page.wait_for_timeout(500)
    assert len(app.puts) == 1


def test_lista_vazia_deixa_publicar_desabilitado(app):
    app.abrir()
    app.iniciar()
    assert app.page.is_disabled("#btn-publicar")
    assert app.puts == []


def test_texto_com_acento_emoji_e_travessao_chega_identico(app):
    app.abrir()
    app.iniciar()
    app.ligar_camera()
    app.page.fill("#texto-livre", "Não liga — lacre nº 7 ✓ 🚫")
    app.enfileirar([App.det_qr("51000001")])
    app.esperar_fila()
    app.page.click("#btn-publicar")
    app.page.wait_for_selector("#tela-inicio:not([hidden])")
    csv = app.csv_publicado(0)
    assert "responsavel" not in csv.split("\n")[0] and "local=" not in csv.split("\n")[0]
    assert csv.split("\n")[2] == "51000001;EMPRESTAR;Não liga — lacre nº 7 ✓ 🚫"


def test_mais_de_15000_itens_nao_publica(app):
    app.abrir()
    # sessão salva com 15.001 itens, retomada de uma vez (ler tudo pela câmera/galeria re-renderiza a lista a cada item)
    app.page.evaluate(
        """() => localStorage.setItem('lq.sessao', JSON.stringify({
              codigo: '48213', responsavel: '', local: '',
              itens: Array.from({length: 15001}, (_, i) => ({
                codigo: '51' + String(i).padStart(6, '0'), operacao: 'EMPRESTAR', descricao: ''})),
              op: {}}))"""
    )
    app.page.reload()
    app.page.click("#btn-retomar")
    app.page.wait_for_function("document.getElementById('contador-texto').textContent.includes('15001')")
    app.page.click("#btn-publicar")
    app.page.wait_for_selector("#erro-camera", state="visible")
    assert "15000" in app.page.inner_text("#erro-camera")
    assert app.puts == []
    assert app.page.is_visible("#tela-leitura")
