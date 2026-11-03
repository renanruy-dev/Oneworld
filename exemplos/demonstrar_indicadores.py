"""Execute na raiz: python -m exemplos.demonstrar_indicadores."""
from pathlib import Path

import pandas as pd

from oneworld.indicadores import OPERACOES, calcular_kpi


def demonstrar():
    resultados = []
    for nome, categoria, medida in (
        ("vendas", "produto", "valor"),
        ("educacao", "turma", "nota"),
        ("estoque", "categoria", "quantidade"),
    ):
        df = pd.read_csv(Path(__file__).with_name(f"{nome}.csv"))
        linha = {"dataset": nome, "coluna numérica": medida, "coluna distinta": categoria}
        for operacao in OPERACOES:
            resultado = calcular_kpi(df, {
                "titulo": f"{nome}: {operacao}", "operacao": operacao,
                "coluna": categoria if operacao == "distintos" else medida,
            })
            if resultado.erro:
                raise ValueError(resultado.erro)
            linha[operacao] = resultado.valor
        resultados.append(linha)
    return pd.DataFrame(resultados)


if __name__ == "__main__":
    print(demonstrar().to_string(index=False))
