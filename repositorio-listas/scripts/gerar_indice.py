#!/usr/bin/env python3
"""Gera indice.csv a partir de listas/*.csv (formato 1 do contrato com o ASIdoBem).

Uso: gerar_indice.py <raiz-do-repositorio>

Lista inválida fica FORA do índice e é registrada em stderr ("ignorada"); o script nunca
falha por causa de uma lista ruim, para não travar a publicação das demais.
"""
import hashlib
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

MAX_LINHAS = 20000
MAX_BYTES = 5 * 1024 * 1024
RE_ID = re.compile(r"^[A-Za-z0-9-]{1,60}$")
RE_CODIGO = re.compile(r"^[1-9]\d{4}$")
CABECALHO_LISTA = "patrimonio;operacao;descricao"
CABECALHO_INDICE = "id;codigo;gerado_em;titulo;linhas;sha256;arquivo"
PREFIXO = "#ASIDOBEM;"


def ler_lista(caminho: Path):
    """Devolve (metadados, quantidade_de_linhas, bytes) ou levanta ValueError com o motivo."""
    dados = caminho.read_bytes()
    if len(dados) > MAX_BYTES:
        raise ValueError("maior que 5 MB")
    try:
        texto = dados.decode("utf-8")
    except UnicodeDecodeError:
        raise ValueError("não é UTF-8")
    if texto.startswith("﻿"):
        texto = texto[1:]
    linhas = texto.splitlines()
    if not linhas or not linhas[0].startswith(PREFIXO):
        raise ValueError("sem linha de identificação")
    meta = {}
    for par in linhas[0][len(PREFIXO):].split(";"):
        if "=" in par:
            chave, valor = par.split("=", 1)
            meta[chave.strip()] = valor.strip()
    if meta.get("formato") != "1":
        raise ValueError("formato diferente de 1")
    if not RE_CODIGO.match(meta.get("codigo", "")):
        raise ValueError("código inválido")
    if not RE_ID.match(meta.get("id", "")):
        raise ValueError("id inválido")
    if meta["id"] != caminho.stem:
        raise ValueError("id diferente do nome do arquivo")
    if len(linhas) < 2 or linhas[1] != CABECALHO_LISTA:
        raise ValueError("cabeçalho diferente do exigido")
    dados_linhas = [l for l in linhas[2:] if l.strip()]
    if len(dados_linhas) > MAX_LINHAS:
        raise ValueError("mais de 20.000 linhas")
    for n, linha in enumerate(dados_linhas, 1):
        if linha.count(";") != 2:
            raise ValueError(f"linha {n} com número de colunas diferente de 3")
    return meta, len(dados_linhas), dados


def instante(texto: str) -> datetime:
    try:
        d = datetime.fromisoformat(texto)
    except ValueError:
        return datetime.min.replace(tzinfo=timezone.utc)
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def main(raiz: Path) -> None:
    entradas = []
    for caminho in sorted((raiz / "listas").glob("*.csv")):
        try:
            meta, quantidade, dados = ler_lista(caminho)
        except ValueError as erro:
            print(f"ignorada: {caminho.name}: {erro}", file=sys.stderr)
            continue
        entradas.append({
            "id": meta["id"],
            "codigo": meta["codigo"],
            "gerado_em": meta.get("gerado_em", ""),
            "titulo": meta.get("titulo", "").replace(";", " "),
            "linhas": quantidade,
            "sha256": hashlib.sha256(dados).hexdigest(),
            "arquivo": f"listas/{meta['id']}.csv",
        })
    entradas.sort(key=lambda e: (instante(e["gerado_em"]), e["id"]), reverse=True)
    saida = [CABECALHO_INDICE] + [
        ";".join(str(e[c]) for c in ("id", "codigo", "gerado_em", "titulo", "linhas", "sha256", "arquivo"))
        for e in entradas
    ]
    (raiz / "indice.csv").write_bytes(("\n".join(saida) + "\n").encode("utf-8"))


if __name__ == "__main__":
    main(Path(sys.argv[1]))
