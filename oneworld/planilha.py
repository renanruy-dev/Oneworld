"""Leitura de planilhas com openpyxl (sem Streamlit): modo read-only e conversão para DataFrame de strings.
Usada pela base DFP (quando entregue em .xlsx) e pelo mapeamento de planilhas livres."""
import io
from datetime import date, datetime

import pandas as pd
from openpyxl import load_workbook


def _para_str(v):
    """Célula do Excel -> texto equivalente ao que o CSV traria."""
    if v is None:
        return None
    if isinstance(v, datetime):
        return v.date().isoformat() if v.time() == datetime.min.time() else v.isoformat(sep=" ")
    if isinstance(v, date):
        return v.isoformat()
    if isinstance(v, float) and v.is_integer() and abs(v) < 1e18:
        return str(int(v))
    if isinstance(v, bool):
        return str(v)
    return str(v).strip()


def ler_planilha(origem, aba=0, texto_obrigatorio=()):
    """Lê uma aba .xlsx em modo read-only e devolve DataFrame de strings (células vazias = NaN, como no CSV).
    `origem`: caminho ou bytes/arquivo. `texto_obrigatorio`: colunas que DEVEM estar formatadas como texto
    no Excel (ex.: CD_CONTA '3.10' e CNPJ). Se o Excel as converteu em número, o dado já se perdeu
    ('3.10' virou 3.1) e levantamos erro em vez de importar números errados."""
    if isinstance(origem, (bytes, bytearray)):
        origem = io.BytesIO(origem)
    wb = load_workbook(origem, read_only=True, data_only=True)
    try:
        ws = wb.worksheets[aba] if isinstance(aba, int) else wb[aba]
        ws.reset_dimensions()  # alguns arquivos declaram dimensão errada; isto lê até a última linha real
        it = ws.iter_rows(values_only=True)
        cab = next(it, None)
        if not cab:
            return pd.DataFrame()
        idx = [(i, str(h).strip()) for i, h in enumerate(cab) if h not in (None, "")]
        nomes = [n for _, n in idx]
        obrig = [n for n in nomes if n in set(texto_obrigatorio)]
        pos = {n: i for i, n in idx}
        linhas = []
        for lin, row in enumerate(it, start=2):
            if row is None or all(v is None for v in row):
                continue
            for n in obrig:
                v = row[pos[n]] if pos[n] < len(row) else None
                if v is not None and not isinstance(v, str):
                    raise ValueError(f"linha {lin}: a coluna {n} contém número ({v!r}); o Excel pode ter "
                                     f"removido zeros/pontos. Formate a coluna como Texto e gere o arquivo de novo.")
            linhas.append([_para_str(row[i]) if i < len(row) else None for i, _ in idx])
    finally:
        wb.close()
    return pd.DataFrame(linhas, columns=nomes, dtype=object)
