"""Execute da raiz: .venv/Scripts/python.exe -B docs/parte4_entrega/evidencias/validacao_20261027/preparar_demo.py

Cria uma NOVA cópia isolada por execução; nunca copia/abre o banco real.
"""
from pathlib import Path
from contextlib import closing
from dataclasses import asdict
import hashlib
import json
import platform
import shutil
import sqlite3
import tempfile

import pandas as pd
import streamlit
import openpyxl

RAIZ = Path(__file__).resolve().parents[4]
SAIDA = Path(__file__).resolve().parent


def main():
    import sys
    sys.path.insert(0, str(RAIZ))
    from oneworld.indicadores import OPERACOES, calcular_kpi
    from oneworld.filtros import aplicar_filtros
    from oneworld.analises import preparar_grafico
    from oneworld.metadados import configurar_datas
    from oneworld.fontes_sqlite import carregar_tabela

    isolado = Path(tempfile.mkdtemp(prefix="demo_", dir=SAIDA))
    for pasta in ("oneworld", "exemplos", ".streamlit"):
        shutil.copytree(RAIZ / pasta, isolado / pasta,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    for nome in ("app.py", "OneWorld-logo.jpg", "requirements.txt"):
        shutil.copy2(RAIZ / nome, isolado / nome)
    resultados = {}
    with closing(sqlite3.connect(isolado / "oneworld.db")) as con:
        for nome, grupo, medida, soma in (("vendas", "produto", "valor", 450),
                                        ("educacao", "turma", "nota", 24),
                                        ("estoque", "categoria", "quantidade", 47)):
            df = pd.read_csv(isolado / "exemplos" / (nome + ".csv"))
            df.to_sql("demo_" + nome, con, index=False)
            kpis = {op: asdict(calcular_kpi(df, {"operacao": op,
                    "coluna": grupo if op == "distintos" else medida})) for op in OPERACOES}
            assert kpis["soma"]["valor"] == soma
            filtrado = aplicar_filtros(df, [{"tipo": "categoria", "coluna": grupo,
                                           "valores": [df[grupo].iloc[0]]}])
            barras = preparar_grafico(filtrado, {"tipo": "barras", "grupo": grupo,
                                     "operacao": "soma", "coluna": medida})
            assert barras.valor.sum() == calcular_kpi(filtrado, {"operacao": "soma", "coluna": medida}).valor
            csv = SAIDA / (nome + "_filtrado.csv")
            filtrado.to_csv(csv, index=False, encoding="utf-8-sig")
            pd.testing.assert_frame_equal(pd.read_csv(csv), filtrado.reset_index(drop=True))
            assert preparar_grafico(df, {"tipo": "histograma", "coluna": medida}).frequencia.sum() == len(df)
            resultados[nome] = {"kpis": kpis, "linhas_filtradas": len(filtrado),
                                "csv_sha256": hashlib.sha256(csv.read_bytes()).hexdigest()}
        con.commit()
    for nome, medida in (("vendas", "valor"), ("educacao", "nota"), ("estoque", "quantidade")):
        lido = carregar_tabela(isolado / "oneworld.db", "demo_" + nome)
        assert calcular_kpi(lido, {"operacao": "soma", "coluna": medida}).valor == resultados[nome]["kpis"]["soma"]["valor"]
    vendas, _ = configurar_datas(pd.read_csv(isolado / "exemplos/vendas.csv"), ["data"])
    linhas = preparar_grafico(vendas, {"tipo": "linhas", "grupo": "data", "coluna": "valor", "operacao": "soma"})
    assert linhas.valor.tolist() == [100, 200, 100, 50]
    resultados["linhas_vendas"] = linhas.valor.tolist()
    resultados["ambiente"] = {"python": platform.python_version(), "pandas": pd.__version__,
                              "streamlit": streamlit.__version__, "openpyxl": openpyxl.__version__,
                              "sqlite": sqlite3.sqlite_version}
    resultados["isolado"] = str(isolado)
    (SAIDA / "demonstracao.json").write_text(json.dumps(resultados, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(resultados, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
