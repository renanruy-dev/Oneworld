"""Utilitários compartilhados pelos módulos de IA e DFP: leitura do .env, mascaramento de segredos e
formatação pt-BR. Não depende de Streamlit nem de banco."""
import os
import re

import pandas as pd

from .config import RAIZ


# ── Ambiente (.env + variáveis de ambiente) ──
def ler_dotenv():
    arq = RAIZ / ".env"
    out = {}
    if arq.is_file():
        for linha in arq.read_text(encoding="utf-8-sig").splitlines():
            linha = linha.strip()
            if not linha or linha.startswith("#") or "=" not in linha:
                continue
            k, val = linha.split("=", 1)
            k, val = k.strip().removeprefix("export ").strip(), val.strip()
            if len(val) >= 2 and val[0] == val[-1] and val[0] in "\"'":
                val = val[1:-1]
            elif " #" in val:
                val = val.split(" #", 1)[0].strip()
            if k:
                out[k] = val
    return out


def ler_env():
    """.env + variáveis de ambiente (estas têm prioridade)."""
    return {**ler_dotenv(), **{k: v for k, v in os.environ.items() if v}}


def mascarar(texto):
    """Remove qualquer chave/segredo conhecido de uma mensagem antes de exibi-la."""
    texto = str(texto)
    for nome, val in ler_env().items():
        if val and len(val) >= 8 and re.search(r"(KEY|TOKEN|SECRET|PASSWORD)", nome.upper()):
            texto = texto.replace(val, "***")
    return re.sub(r"\b(sk-|gsk_|xai-|AIza)[A-Za-z0-9_\-]{8,}", lambda m: m.group(1) + "***", texto)


# ── Formatação (pt-BR) usada nos textos de contexto ──
def brl(v):
    if v is None or pd.isna(v):
        return "n/d"
    a, s = abs(float(v)), "-" if v < 0 else ""
    for lim, suf in ((1e12, " tri"), (1e9, " bi"), (1e6, " mi")):
        if a >= lim:
            return f"{s}R$ {a / lim:.2f}".replace(".", ",") + suf
    return f"{s}R$ {a:,.0f}".replace(",", ".")


def pct(v):
    return "n/d" if v is None else f"{v * 100:+.1f}%".replace(".", ",")


def razao(a, b):
    return None if a is None or b in (None, 0) else a / b
