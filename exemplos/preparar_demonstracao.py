"""Cria uma demonstração temporária com banco gerado dos exemplos CSV."""

from pathlib import Path
import shutil
import sqlite3
import tempfile

import pandas as pd


def main():
    raiz = Path(__file__).resolve().parents[1]
    destino = Path(tempfile.mkdtemp(prefix="oneworld-demo-"))
    for pasta in ("oneworld", "exemplos"):
        shutil.copytree(
            raiz / pasta,
            destino / pasta,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
        )
    for nome in ("app.py", "OneWorld-logo.jpg", "requirements.txt"):
        shutil.copy2(raiz / nome, destino / nome)
    conexao = sqlite3.connect(destino / "oneworld.db")
    try:
        for nome in ("vendas", "educacao", "estoque"):
            dados = pd.read_csv(destino / "exemplos" / f"{nome}.csv")
            dados.to_sql(f"demo_{nome}", conexao, index=False)
    finally:
        conexao.close()
    print(destino)


if __name__ == "__main__":
    main()
