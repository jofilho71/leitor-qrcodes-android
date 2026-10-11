import json

from conftest import TOKEN_TESTE


def token_guardado(app):
    return app.page.evaluate("localStorage.getItem('lq.token')")


def test_link_de_configuracao_guarda_token_e_limpa_o_fragmento(app):
    app.abrir(token=None, hash="#cfg=" + TOKEN_TESTE)
    assert "#" not in app.page.url and "cfg" not in app.page.url
    assert token_guardado(app) == json.dumps(TOKEN_TESTE)
    assert "configurado" in app.page.inner_text("#aviso-inicio").lower()


def test_link_de_configuracao_invalido_nao_guarda(app):
    app.abrir(token=None, hash="#cfg=curto")
    assert token_guardado(app) is None
    assert "inválido" in app.page.inner_text("#aviso-inicio")
    assert "cfg" not in app.page.url


def test_sem_token_nao_inicia_e_nao_chama_a_api(app):
    chamadas = []
    app.abrir(token=None)
    app.page.on("request", lambda r: chamadas.append(r.url) if "api.github.com" in r.url else None)
    app.page.click("#btn-iniciar")
    assert "Token ausente" in app.page.inner_text("#aviso-inicio")
    assert app.page.is_visible("#tela-inicio")
    assert chamadas == []


def test_token_rejeitado_pelo_github_bloqueia(app):
    app.status_get = 401
    app.abrir()
    app.page.click("#btn-iniciar")
    app.page.wait_for_function("document.getElementById('aviso-inicio').textContent.includes('vencido')")
    assert app.page.is_visible("#tela-inicio")


def test_token_sem_permissao_de_escrita_bloqueia(app):
    app.push = False
    app.abrir()
    app.page.click("#btn-iniciar")
    app.page.wait_for_function("document.getElementById('aviso-inicio').textContent.includes('permissão')")
    assert app.page.is_visible("#tela-inicio")


def test_sem_rede_deixa_iniciar_com_aviso(app):
    app.rede_caida = True
    app.abrir()
    app.page.click("#btn-iniciar")
    app.page.wait_for_selector("#tela-codigo:not([hidden])")
    assert "Sem conexão" in app.page.inner_text("#erro-codigo")


def test_token_valido_inicia_normalmente(app):
    app.abrir()
    app.iniciar()
    assert app.page.is_visible("#tela-leitura")


def test_ajustes_colar_e_apagar_token(app):
    app.abrir(token=None)
    p = app.page
    p.click("#btn-ajustes")
    assert "Sem token" in p.inner_text("#estado-token")
    p.fill("#input-token", "abc")
    p.click("#btn-token-salvar")
    assert "inválido" in p.inner_text("#erro-token")
    assert token_guardado(app) is None
    p.fill("#input-token", TOKEN_TESTE)
    p.click("#btn-token-salvar")
    assert "Token configurado" in p.inner_text("#estado-token")
    assert token_guardado(app) == json.dumps(TOKEN_TESTE)
    p.click("#btn-token-apagar")
    assert "Sem token" in p.inner_text("#estado-token")
    assert token_guardado(app) is None


def test_localstorage_bloqueado_nao_quebra_a_pagina(app):
    app.abrir(token=None)
    app.page.add_init_script(
        "Object.defineProperty(window, 'localStorage', {get() { throw new Error('bloqueado'); }})"
    )
    app.page.reload()
    assert app.page.is_visible("#btn-iniciar")
    app.page.click("#btn-iniciar")
    assert "Token ausente" in app.page.inner_text("#aviso-inicio")
    assert app.erros_pagina == []
