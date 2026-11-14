"""Filtros inclusivos combinados com AND; nunca modificam a entrada."""
import pandas as pd
from numbers import Integral

from .metadados import ErroBI, exigir_coluna, numeros_validos, validar_dataframe


def aplicar_filtros(df, configuracoes):
    """Configurações: coluna, tipo, valores ou minimo/maximo, incluir_nulos.

    Seleção categórica vazia seleciona zero valores. Datas abrangem o dia
    inteiro no fuso da coluna. Limites ausentes deixam o intervalo aberto.
    Nulos/infinitos só entram quando incluir_nulos é verdadeiro.
    """
    validar_dataframe(df)
    mascara = pd.Series(True, index=df.index)
    for cfg in configuracoes:
        nome, tipo = cfg.get("coluna"), cfg.get("tipo")
        s = exigir_coluna(df, nome, tipo)
        if tipo == "categoria":
            parte = s.isin(cfg.get("valores", [])) & s.notna()
        elif tipo in ("numero", "data"):
            if tipo == "numero":
                s = numeros_validos(df, nome)
                converter = lambda v: int(v) if isinstance(v, Integral) else float(v)
            else:
                # Compara dias locais sem deslocar timestamps para outro fuso.
                s = s.dt.tz_localize(None).dt.normalize()
                converter = lambda v: pd.Timestamp(v).tz_localize(None).normalize()
            try:
                lo = converter(cfg["minimo"]) if cfg.get("minimo") is not None else None
                hi = converter(cfg["maximo"]) if cfg.get("maximo") is not None else None
                if ((lo is not None and pd.isna(lo)) or (hi is not None and pd.isna(hi))
                        or (tipo == "numero" and any(
                            v is not None and v in (float("inf"), float("-inf"))
                            for v in (lo, hi)))):
                    raise ValueError("limite inválido")
                if lo is not None and hi is not None and lo > hi:
                    raise ErroBI(f"Limites invertidos para {nome!r}.")
                parte = s.notna()
                if lo is not None:
                    parte &= s >= lo
                if hi is not None:
                    parte &= s <= hi
            except (TypeError, ValueError, OverflowError) as exc:
                raise ErroBI(f"Intervalo inválido para {nome!r}: {exc}") from exc
        else:
            raise ErroBI("Tipo de filtro desconhecido.")
        if cfg.get("incluir_nulos", False):
            parte |= s.isna()
        mascara &= parte.fillna(False)
    return df.loc[mascara].copy()
