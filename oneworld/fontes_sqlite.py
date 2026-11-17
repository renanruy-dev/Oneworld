"""Fontes tabulares do banco local, acessadas somente para leitura."""
import sqlite3
from contextlib import closing
from datetime import date
from pathlib import Path

import pandas as pd

from . import database
from .campos import converter_valor
from .config import CAMPOS


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
        df = pd.read_sql_query(f"SELECT * FROM {identificador}", con)
        gerenciada = tabela in CAMPOS and {"extras", "id", *CAMPOS[tabela]} <= set(df.columns)
        if gerenciada and con.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='config'"
        ).fetchone():
            campos = database.campos_da_tabela(database.ler_campos_personalizados(conexao=con), tabela)
            return _tipar_campos(df, campos)
        return df


def _tipar_campos(df, campos):
    tipos = {campo["nome"]: campo["tipo"] for campo in campos}
    # Nomes reservados nas definições antigas podem coincidir com colunas nativas.
    tipos = {nome: tipo for nome, tipo in tipos.items() if nome not in df.columns or nome == "extras"}
    df = database.expandir_campos(df, tipos)
    dtypes = {"texto": "string", "inteiro": "Int64", "decimal": "Float64", "data": "datetime64[us]", "booleano": "boolean"}
    falhas = {}
    for nome, tipo in tipos.items():
        valores = []
        for bruto in df[nome]:
            try:
                valor = converter_valor(bruto, tipo)
                valores.append(date.fromisoformat(valor) if tipo == "data" and valor else valor)
            except ValueError:
                valores.append(None)
                falhas[nome] = falhas.get(nome, 0) + 1
        df[nome] = pd.array(valores, dtype=dtypes[tipo])
    df.attrs["tipos_campos"] = tipos
    df.attrs["falhas_campos"] = falhas
    return df
