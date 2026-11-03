"""Contratos e tipos usados pelo BI, sem inferência de significado de negócio."""
from dataclasses import dataclass

import pandas as pd
from pandas.api.types import (
    is_bool_dtype, is_complex_dtype, is_datetime64_any_dtype, is_numeric_dtype,
)


class ErroBI(ValueError):
    """Dados ou configuração incompatíveis com uma operação analítica."""


@dataclass(frozen=True)
class Coluna:
    nome: str
    tipo: str
    nulos: int


def validar_dataframe(df):
    if not isinstance(df, pd.DataFrame):
        raise ErroBI("Forneça um pandas.DataFrame.")
    if not df.columns.is_unique or any(not isinstance(c, str) for c in df.columns):
        raise ErroBI("As colunas precisam ter nomes textuais únicos.")


def inspecionar_colunas(df):
    """Datas textuais continuam texto até conversão explícita do usuário.

    Booleanos são categorias, não medidas. Objetos aninhados e números
    complexos não recebem operações automáticas.
    """
    validar_dataframe(df)
    resultado = {}
    for nome in df.columns:
        s = df[nome]
        if is_datetime64_any_dtype(s.dtype):
            tipo = "data"
        elif is_bool_dtype(s.dtype):
            tipo = "categoria"
        elif is_complex_dtype(s.dtype):
            tipo = "incompativel"
        elif is_numeric_dtype(s.dtype):
            tipo = "numero"
        elif s.dropna().map(lambda v: isinstance(v, (str, bool))).all():
            tipo = "categoria"
        else:
            tipo = "incompativel"
        resultado[nome] = Coluna(nome, tipo, int(s.isna().sum()))
    return resultado


def exigir_coluna(df, nome, tipo=None):
    meta = inspecionar_colunas(df)
    if nome not in meta:
        raise ErroBI(f"Coluna ausente: {nome!r}.")
    if meta[nome].tipo == "incompativel" or (tipo and meta[nome].tipo != tipo):
        raise ErroBI(f"A coluna {nome!r} não é compatível com esta operação"
                     + (f" (tipo necessário: {tipo})." if tipo else "."))
    return df[nome]


def numeros_validos(df, nome):
    """Ignora nulos e infinitos; não converte texto silenciosamente."""
    s = exigir_coluna(df, nome, "numero")
    return s.where(~s.isin([float("inf"), float("-inf")]))


def configurar_datas(df, colunas, formato="%Y-%m-%d"):
    """Converte apenas colunas escolhidas, retornando cópia e falhas por coluna."""
    validar_dataframe(df)
    convertido, falhas = df.copy(), {}
    for nome in colunas:
        s = exigir_coluna(df, nome)
        try:
            datas = pd.to_datetime(s, format=formato, errors="coerce")
        except (ValueError, TypeError, OverflowError) as exc:
            raise ErroBI(f"Não foi possível interpretar as datas; confira o formato: {exc}") from exc
        if not is_datetime64_any_dtype(datas.dtype):
            raise ErroBI(f"A coluna {nome!r} contém fusos incompatíveis.")
        falhas[nome] = int((s.notna() & datas.isna()).sum())
        convertido[nome] = datas
    return convertido, falhas
