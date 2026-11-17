"""Prepara tabelas para gráficos; não renderiza nem acessa serviços."""
import pandas as pd
from pandas.api.types import is_bool_dtype, is_datetime64_any_dtype, is_numeric_dtype

from .indicadores import AGREGACOES
from .metadados import ErroBI, exigir_coluna, numeros_validos, validar_dataframe


def preparar_grafico(df, configuracao):
    """Barras/linhas retornam grupo e valor; histograma, intervalo e frequencia.

    Grupos nulos são excluídos. Medidas ignoram nulos e infinitos; grupos sem
    medidas válidas não aparecem. Contagem contabiliza linhas por grupo.
    Valores distintos contabilizam os valores não nulos da medida por grupo.
    Linhas ordenam dimensões numéricas ou datas agrupadas por dia/mês.
    """
    validar_dataframe(df)
    tipo = configuracao.get("tipo")
    if tipo == "histograma":
        s = numeros_validos(df, configuracao.get("coluna")).dropna()
        bins = configuracao.get("intervalos", 10)
        if isinstance(bins, bool) or not isinstance(bins, int) or not 1 <= bins <= 100:
            raise ErroBI("Escolha de 1 a 100 intervalos para o histograma.")
        if s.empty:
            return pd.DataFrame(columns=["intervalo", "frequencia"])
        try:
            contagens = pd.cut(s, bins=bins, include_lowest=True).value_counts(sort=False)
        except (ValueError, TypeError, OverflowError) as exc:
            raise ErroBI(f"Não foi possível construir os intervalos: {exc}") from exc
        return pd.DataFrame({"intervalo": contagens.index.astype(str),
                             "frequencia": contagens.to_numpy()})
    if tipo not in ("barras", "linhas"):
        raise ErroBI("Tipo de gráfico desconhecido.")
    nome_grupo = configuracao.get("grupo")
    grupo = exigir_coluna(df, nome_grupo)
    numerico = is_numeric_dtype(grupo.dtype) and not is_bool_dtype(grupo.dtype)
    if numerico:
        grupo = numeros_validos(df, nome_grupo)
    elif tipo == "linhas" and is_datetime64_any_dtype(grupo.dtype):
        periodo = configuracao.get("periodo", "dia")
        if periodo not in ("dia", "mes"):
            raise ErroBI("Período temporal inválido; escolha dia ou mes.")
        grupo = grupo.dt.tz_localize(None)
        grupo = (grupo.dt.normalize() if periodo == "dia"
                 else grupo.dt.to_period("M").dt.to_timestamp())
    else:
        exigir_coluna(df, nome_grupo, "data" if tipo == "linhas" else "categoria")
    operacao = configuracao.get("operacao", "contagem")
    # Constrói nomes internos novos para aceitar quaisquer nomes na origem.
    tabela = pd.DataFrame({"grupo": grupo.to_numpy()})
    if operacao == "contagem":
        resultado = tabela.groupby("grupo", observed=True, dropna=True, sort=False).size()
    elif operacao == "distintos":
        tabela["medida"] = exigir_coluna(df, configuracao.get("coluna")).to_numpy()
        resultado = tabela.groupby("grupo", observed=True, sort=False)["medida"].nunique()
    elif operacao in AGREGACOES:
        medida = numeros_validos(df, configuracao.get("coluna"))
        # Preserva inteiros nullable; to_numpy() pode convertê-los para float
        # e perder precisão antes mesmo da agregação.
        tabela["valor"] = pd.Series(medida.array)
        tabela = tabela.dropna(subset=["valor"])
        if operacao == "soma" and medida.dtype.kind in "iu":
            resultado = tabela.groupby("grupo", observed=True, sort=False)["valor"].agg(
                lambda s: sum(int(v) for v in s))
        else:
            resultado = tabela.groupby("grupo", observed=True, sort=False)["valor"].agg(AGREGACOES[operacao])
        if resultado.isin([float("inf"), float("-inf")]).any():
            raise ErroBI("A agregação excede o intervalo numérico suportado.")
    else:
        raise ErroBI("Agregação de gráfico desconhecida.")
    # Categorias compatíveis podem misturar texto e booleanos (por exemplo JSON).
    # Ordena pelos rótulos sem comparar str com bool nem alterar os grupos.
    chave = (lambda indice: indice.map(str)) if tipo == "barras" and not numerico else None
    return resultado.rename("valor").sort_index(key=chave).reset_index()
