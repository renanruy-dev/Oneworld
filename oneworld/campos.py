"""Tipos e conversão dos valores de campos personalizados."""

import math
import re
from datetime import date, datetime
from numbers import Integral, Real

import pandas as pd


TIPOS_CAMPOS = {
    "texto": "Texto",
    "inteiro": "Número inteiro",
    "decimal": "Número decimal",
    "data": "Data",
    "booleano": "Sim/não",
}


def converter_valor(valor, tipo):
    """Retorna um escalar JSON; valores ausentes continuam nulos."""
    if isinstance(valor, str):
        valor = valor.strip()
    if valor is None or (pd.api.types.is_scalar(valor) and pd.isna(valor)) or valor == "":
        return None
    if tipo == "texto":
        return str(valor)
    if tipo == "inteiro":
        if isinstance(valor, Integral) and not isinstance(valor, bool):
            valor = int(valor)
        elif isinstance(valor, Real) and not isinstance(valor, bool) and float(valor).is_integer() and abs(valor) <= 2**53:
            valor = int(valor)
        if isinstance(valor, str) and re.fullmatch(r"[+-]?[0-9]{1,19}", valor):
            valor = int(valor)
        if type(valor) is int and -(2**63) <= valor < 2**63:
            return valor
        raise ValueError("informe um número inteiro entre −2⁶³ e 2⁶³ − 1.")
    if tipo == "decimal":
        if isinstance(valor, str):
            if not re.fullmatch(r"[+-]?(?:[0-9]+(?:[.,][0-9]*)?|[.,][0-9]+)(?:[eE][+-]?[0-9]+)?", valor):
                raise ValueError("informe um número decimal, como 12,5 ou 12.5, sem separador de milhar.")
            valor = valor.replace(",", ".")
        elif not isinstance(valor, Real) or isinstance(valor, bool):
            raise ValueError("informe um número decimal, como 12,5 ou 12.5.")
        try:
            numero = float(valor)
        except (ValueError, OverflowError) as exc:
            raise ValueError("o número decimal excede o limite suportado.") from exc
        if not math.isfinite(numero):
            raise ValueError("informe um número decimal finito.")
        return numero
    if tipo == "data":
        if isinstance(valor, datetime) and valor.time() == datetime.min.time():
            valor = valor.date()
        if type(valor) is date:
            return valor.isoformat()
        if isinstance(valor, str):
            if re.fullmatch(r"[0-9]{2}/[0-9]{2}/[0-9]{4}", valor):
                dia, mes, ano = valor.split("/")
                valor = f"{ano}-{mes}-{dia}"
            if re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", valor):
                try:
                    return date.fromisoformat(valor).isoformat()
                except ValueError:
                    pass
        raise ValueError("informe uma data válida no formato DD/MM/AAAA ou AAAA-MM-DD.")
    if tipo == "booleano":
        if type(valor) is bool:
            return valor
        if isinstance(valor, str):
            opcoes = {"sim": True, "não": False, "nao": False, "true": True, "false": False}
            if valor.casefold() in opcoes:
                return opcoes[valor.casefold()]
        raise ValueError("escolha Sim ou Não.")
    raise ValueError(f"Tipo de campo desconhecido: {tipo!r}.")
