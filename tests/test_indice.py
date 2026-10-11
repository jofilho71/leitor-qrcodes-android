import hashlib
import pathlib
import subprocess
import sys

import pytest

RAIZ = pathlib.Path(__file__).resolve().parent.parent
SCRIPT = RAIZ / "repositorio-listas" / "scripts" / "gerar_indice.py"
CABECALHO_INDICE = "id;codigo;gerado_em;titulo;linhas;sha256;arquivo"


def lista(id_, codigo="48213", gerado="2026-10-20T16:42:05-03:00", linhas=("51250523;RECOLHER;ok",),
          cabecalho="patrimonio;operacao;descricao", formato="1"):
    ident = f"#ASIDOBEM;formato={formato};codigo={codigo};id={id_};titulo=Teste {id_};gerado_em={gerado}"
    return "\n".join([ident, cabecalho, *linhas]) + "\n"


def gravar(raiz, id_, conteudo, nome=None):
    pasta = raiz / "listas"
    pasta.mkdir(exist_ok=True)
    caminho = pasta / ((nome or id_) + ".csv")
    dados = conteudo if isinstance(conteudo, bytes) else conteudo.encode("utf-8")
    caminho.write_bytes(dados)
    return caminho


def rodar(raiz):
    r = subprocess.run([sys.executable, "-I", str(SCRIPT), str(raiz)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    return r


def indice(raiz):
    return (raiz / "indice.csv").read_text(encoding="utf-8").split("\n")


def test_indice_ordenado_do_mais_recente_com_sha256_e_linhas(tmp_path):
    a = gravar(tmp_path, "2026-10-20-z59-01", lista("2026-10-20-z59-01", gerado="2026-10-20T16:42:05-03:00",
                                                    linhas=("51250523;RECOLHER;a", "51250524;DESCARTAR;")))
    b = gravar(tmp_path, "2026-10-21-polo-01", lista("2026-10-21-polo-01", gerado="2026-10-21T09:10:00-03:00"))
    rodar(tmp_path)
    linhas = indice(tmp_path)
    assert linhas[0] == CABECALHO_INDICE
    assert linhas[1] == (
        f"2026-10-21-polo-01;48213;2026-10-21T09:10:00-03:00;Teste 2026-10-21-polo-01;1;"
        f"{hashlib.sha256(b.read_bytes()).hexdigest()};listas/2026-10-21-polo-01.csv"
    )
    assert linhas[2] == (
        f"2026-10-20-z59-01;48213;2026-10-20T16:42:05-03:00;Teste 2026-10-20-z59-01;2;"
        f"{hashlib.sha256(a.read_bytes()).hexdigest()};listas/2026-10-20-z59-01.csv"
    )
    assert linhas[3] == ""  # termina com quebra de linha


def test_ordem_considera_o_fuso(tmp_path):
    gravar(tmp_path, "a-01", lista("a-01", gerado="2026-10-20T23:00:00-03:00"))   # 02:00 UTC do dia 21
    gravar(tmp_path, "b-01", lista("b-01", gerado="2026-10-21T01:00:00+00:00"))   # 01:00 UTC do dia 21
    rodar(tmp_path)
    assert indice(tmp_path)[1].startswith("a-01;")


def test_saida_deterministica(tmp_path):
    gravar(tmp_path, "a-01", lista("a-01"))
    gravar(tmp_path, "b-01", lista("b-01", gerado="2026-10-21T09:10:00-03:00"))
    rodar(tmp_path)
    primeira = (tmp_path / "indice.csv").read_bytes()
    rodar(tmp_path)
    assert (tmp_path / "indice.csv").read_bytes() == primeira


def test_sem_listas_gera_so_o_cabecalho(tmp_path):
    (tmp_path / "listas").mkdir()
    rodar(tmp_path)
    assert (tmp_path / "indice.csv").read_text(encoding="utf-8") == CABECALHO_INDICE + "\n"


def test_bom_e_tolerado(tmp_path):
    gravar(tmp_path, "a-01", b"\xef\xbb\xbf" + lista("a-01").encode("utf-8"))
    rodar(tmp_path)
    assert indice(tmp_path)[1].startswith("a-01;")


CASOS_INVALIDOS = [
    ("formato 2", lista("x-01", formato="2"), None),
    ("codigo curto", lista("x-01", codigo="1234"), None),
    ("codigo com zero", lista("x-01", codigo="01234"), None),
    ("id diferente do nome", lista("outro-01"), "x-01"),
    ("id invalido", lista("x_01"), "x_01"),
    ("cabecalho errado", lista("x-01", cabecalho="patrimonio;operacao"), None),
    ("linha com 2 colunas", lista("x-01", linhas=("51250523;RECOLHER",)), None),
    ("linha com 4 colunas", lista("x-01", linhas=("51250523;RECOLHER;a;b",)), None),
    ("sem identificacao", "patrimonio;operacao;descricao\n51250523;RECOLHER;a\n", None),
    ("nao utf8", b"#ASIDOBEM;formato=1;codigo=48213;id=x-01\n\xff\xfe\n", None),
    ("mais de 20000 linhas", lista("x-01", linhas=tuple(f"{i};RECOLHER;" for i in range(20001))), None),
]


# ids explícitos: o conteúdo de 20.001 linhas no id do teste estoura o limite de ambiente do subprocesso
@pytest.mark.parametrize("motivo,conteudo,nome", CASOS_INVALIDOS, ids=[c[0] for c in CASOS_INVALIDOS])
def test_lista_invalida_fica_fora_do_indice_e_e_registrada(tmp_path, motivo, conteudo, nome):
    gravar(tmp_path, "x-01", conteudo, nome=nome)
    gravar(tmp_path, "ok-01", lista("ok-01"))
    r = rodar(tmp_path)
    linhas = indice(tmp_path)
    assert [l.split(";")[0] for l in linhas[1:] if l] == ["ok-01"], motivo
    assert "ignorada" in r.stderr.lower(), motivo
