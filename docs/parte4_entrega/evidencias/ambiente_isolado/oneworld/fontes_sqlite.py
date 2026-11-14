"""Fontes tabulares do banco local, acessadas somente para leitura."""
import sqlite3
from contextlib import closing
from pathlib import Path

import pandas as pd


def _conectar(caminho):
    # mode=ro também impede que um caminho incorreto crie um banco vazio.
    uri = Path(caminho).resolve().as_uri() + "?mode=ro"
    return sqlite3.connect(uri, uri=True)


def listar_tabelas(caminho):
    """Retorna nomes reais do catálogo, sem tabelas internas do SQLite."""
    with closing(_conectar(caminho)) as con:
        return [r[0] for r in con.execute(
            "SELECT name FROM sqlite_master WHERE type='table' "
            "AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )]


def carregar_tabela(caminho, tabela):
    """Lê uma tabela existente; nomes não são interpretados como SQL livre."""
    with closing(_conectar(caminho)) as con:
        existe = con.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=? "
            "AND name NOT LIKE 'sqlite_%'", (tabela,)
        ).fetchone()
        if not existe:
            raise ValueError("A tabela selecionada não existe no banco local.")
        identificador = '"' + tabela.replace('"', '""') + '"'
        return pd.read_sql_query(f"SELECT * FROM {identificador}", con)
