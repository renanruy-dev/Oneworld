"""Regras de negócio do OneWorld: formatação, importação de planilhas, validação,
IA simulada, exportação em Markdown e lembretes. Não depende de Streamlit nem de SQL —
recebe DataFrames/valores e devolve DataFrames/valores."""
import json
import re
import unicodedata
from datetime import date, datetime

import pandas as pd

from .config import (ALIAS_OPCAO, ASSETS_DIR, LOGO_PADRAO, ROTULOS, SINONIMOS,
                     STATUS_CONV, STATUS_EVENTO)


# ── Texto e conversões ──
def sem_acento(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode()
    return s.lower().strip()


def chave(s):
    return re.sub(r"[^a-z0-9]", "", sem_acento(s))


def _vazio(v):
    return v is None or (not isinstance(v, str) and pd.isna(v))


def texto(v):
    return "" if _vazio(v) else str(v).strip()


def parse_date(v):
    if _vazio(v) or str(v).strip() == "":
        return None
    s = str(v).strip()
    iso = bool(re.match(r"^\d{4}-\d{2}-\d{2}", s))
    t = pd.to_datetime(v if not isinstance(v, str) else s, dayfirst=not iso, errors="coerce")
    return None if pd.isna(t) else t.date()


def fmt_data(iso):
    d = parse_date(iso)
    return d.strftime("%d/%m/%Y") if d else str(iso or "")


def parse_valor(v):
    if _vazio(v) or str(v).strip() == "":
        return 0.0
    if isinstance(v, (int, float)):
        return float(v)
    s = re.sub(r"[^\d,.\-]", "", str(v))
    if "," in s:
        s = s.replace(".", "").replace(",", ".")
    elif s.count(".") > 1:
        s = s.replace(".", "")
    return float(s)


def norm_opcao(v, opcoes, padrao):
    """Reconhece 'confirmado', 'sim', 'planejamento' etc. Retorna (valor, usou_padrao)."""
    k = "" if _vazio(v) else sem_acento(v)
    for o in opcoes:
        if sem_acento(o) == k:
            return o, False
    if k in ALIAS_OPCAO and ALIAS_OPCAO[k] in opcoes:
        return ALIAS_OPCAO[k], False
    return padrao, True


# ── Formatação para exibição ──
def moeda(v, cfg):
    simbolo = {"BRL": "R$", "USD": "US$", "EUR": "€"}[cfg["moeda"]]
    try:
        v = float(v)
    except (TypeError, ValueError):
        v = 0.0
    txt = f"{v:,.2f}"
    if cfg["moeda"] == "BRL" or cfg["idioma"] != "English":
        txt = txt.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{simbolo} {txt}"


def formatar(df, tab, cfg):
    """Versão amigável para tela: datas dd/mm/aaaa, valores em moeda, cabeçalhos em português."""
    t = df.copy()
    if tab == "eventos":
        t["data"] = t["data"].apply(fmt_data)
        t["valor"] = t["valor"].apply(lambda v: moeda(v, cfg))
    return t.rename(columns=ROTULOS)


def md_tabela(df):
    if df.empty:
        return "_Sem registros._\n"
    cab = "| " + " | ".join(map(str, df.columns)) + " |"
    sep = "| " + " | ".join("---" for _ in df.columns) + " |"
    linhas = ["| " + " | ".join(str(x).replace("|", "/") for x in r) + " |"
              for r in df.itertuples(index=False)]
    return "\n".join([cab, sep] + linhas) + "\n"


# ── Indicadores e filtros do dashboard ──
def meses_disponiveis(e):
    if e.empty:
        return []
    return sorted(pd.to_datetime(e["data"]).dt.strftime("%Y-%m").unique())


def filtrar_eventos(e, mes="Todos", status=()):
    f = e.copy()
    if mes != "Todos":
        f = f[pd.to_datetime(f["data"]).dt.strftime("%Y-%m") == mes]
    if status:
        f = f[f["status"].isin(status)]
    return f


def lembretes(e, hoje=None, dias=7):
    """Eventos não concluídos que acontecem nos próximos `dias` dias."""
    hoje = hoje or date.today()
    out = []
    for r in e.itertuples():
        d = parse_date(r.data)
        if d and 0 <= (d - hoje).days <= dias and r.status != "Concluído":
            quando = "hoje" if d == hoje else f"em {(d - hoje).days} dia(s)"
            out.append(f"{r.cliente}: {quando} ({fmt_data(r.data)})")
    return out


# ── Importação de planilhas ──
def ler_arquivo(arq):
    """Lê CSV (separador detectado), XLSX ou JSON de um arquivo enviado."""
    nome = arq.name.lower()
    if nome.endswith(".csv"):
        df = pd.read_csv(arq, sep=None, engine="python", encoding="utf-8-sig")
    elif nome.endswith(".xlsx"):
        df = pd.read_excel(arq)
    else:
        dados = json.load(arq)
        if isinstance(dados, dict):
            dados = next((v for v in dados.values() if isinstance(v, list)), [dados])
        df = pd.json_normalize(dados)
    df.columns = [str(c) for c in df.columns]
    return df


def sugerir(colunas, destino):
    """Sugere qual coluna do arquivo corresponde a cada campo (por nome; sem IA)."""
    norm = {c: chave(c) for c in colunas}
    usadas, resultado = set(), {}
    for campo, sins in SINONIMOS[destino].items():
        achada = None
        for sin in sins:  # primeiro igualdade exata, depois "contém"
            achada = next((c for c in colunas if c not in usadas and norm[c] == sin), None)
            if achada:
                break
        if not achada:
            for sin in sins:
                achada = next((c for c in colunas if c not in usadas and sin in norm[c]), None)
                if achada:
                    break
        if achada:
            usadas.add(achada)
            resultado[campo] = achada
    return resultado


def validar(df, destino, mapa, existentes):
    """Valida linha a linha. NÃO grava nada.
    `existentes` = DataFrame atual da tabela (para detectar duplicados).
    Retorna dict(ok=[registros], erros=[{linha, motivo}], duplicados=int, padrao=int)."""
    if destino == "eventos":
        vistos = {(r.data, texto(r.cliente).lower()) for r in existentes.itertuples()}
    else:
        vistos = {(texto(r.evento).lower(), texto(r.nome).lower()) for r in existentes.itertuples()}
    ok, erros, dup, padrao = [], [], 0, 0
    for i, row in df.iterrows():
        if row.isna().all():
            continue
        linha = i + 2  # +1 do cabeçalho, +1 por começar em 1
        g = {campo: (row[col] if col else None) for campo, col in mapa.items()}
        try:
            if destino == "eventos":
                d = parse_date(g.get("data"))
                if not d:
                    raise ValueError("data inválida ou vazia")
                nome = texto(g.get("cliente"))
                if not nome:
                    raise ValueError("identificação do evento vazia")
                status, usou = norm_opcao(g.get("status"), STATUS_EVENTO, "Em planejamento")
                padrao += usou and bool(texto(g.get("status")))
                reg = {"data": d.isoformat(), "cliente": nome, "local": texto(g.get("local")),
                       "convidados": int(parse_valor(g.get("convidados"))),
                       "valor": parse_valor(g.get("valor")), "status": status}
                k = (reg["data"], nome.lower())
            else:
                nome = texto(g.get("nome"))
                if not nome:
                    raise ValueError("nome vazio")
                conf, usou = norm_opcao(g.get("confirmacao"), STATUS_CONV, "Pendente")
                padrao += usou and bool(texto(g.get("confirmacao")))
                reg = {"evento": texto(g.get("evento")), "nome": nome, "mesa": texto(g.get("mesa")),
                       "acompanhantes": int(parse_valor(g.get("acompanhantes"))),
                       "contato": texto(g.get("contato")),
                       "restricao": texto(g.get("restricao")) or "—", "confirmacao": conf}
                k = (reg["evento"].lower(), nome.lower())
        except ValueError as ex:
            erros.append({"Linha no arquivo": linha, "Motivo": str(ex)})
            continue
        if k in vistos:
            dup += 1
            continue
        vistos.add(k)
        ok.append(reg)
    return {"ok": ok, "erros": erros, "duplicados": dup, "padrao": padrao}


# ── IA simulada e exportação ──
def responder_ia(pergunta, e, cv, cfg):
    """Resposta SIMULADA por regras locais (não há IA externa conectada)."""
    p = sem_acento(pergunta)
    if e.empty:
        return "Não existem dados suficientes para análise."
    m = lambda v: moeda(v, cfg)  # noqa: E731
    if re.search(r"\b(mes|meses|periodo)\b", p):
        por_mes = e.assign(mes=pd.to_datetime(e["data"]).dt.strftime("%m/%Y")).groupby("mes")["valor"].sum()
        return "Receita prevista por mês: " + "; ".join(f"{k}: {m(v)}" for k, v in por_mes.items()) + "."
    if any(k in p for k in ["receita", "valor", "faturamento"]):
        top = e.sort_values("valor", ascending=False).iloc[0]
        return (f"A receita prevista cadastrada é {m(e['valor'].sum())}, média de "
                f"{m(e['valor'].mean())} por evento. O maior valor previsto é de "
                f"{top['cliente']} ({m(top['valor'])}). Valores previstos não são pagamentos recebidos.")
    if "convidado" in p:
        conf = int((cv["confirmacao"] == "Confirmado").sum()) if not cv.empty else 0
        return (f"O total previsto nos eventos é {int(e['convidados'].sum())} convidados; "
                f"{conf} de {len(cv)} convidados cadastrados já confirmaram.")
    if "pendente" in p or "planejamento" in p:
        pend = e[e["status"].isin(["Pendente", "Em planejamento"])]
        return f"Há {len(pend)} evento(s) pendentes ou em planejamento: " + (
            ", ".join(pend["cliente"]) if len(pend) else "nenhum.")
    if "confirm" in p:
        return f"Existem {int((e['status'] == 'Confirmado').sum())} eventos confirmados de {len(e)}."
    return (f"Resumo: {len(e)} eventos, {int(e['convidados'].sum())} convidados previstos e "
            f"{m(e['valor'].sum())} de receita prevista.")


def gerar_markdown(e, cv, cfg):
    ev = formatar(e.drop(columns=["id"]), "eventos", cfg)
    cvf = formatar(cv.drop(columns=["id"]), "convidados", cfg)
    resumo = [f"- Eventos: {len(e)}",
              f"- Convidados previstos: {int(e['convidados'].sum())}",
              f"- Receita prevista: {moeda(e['valor'].sum(), cfg)} (valores previstos, não pagamentos recebidos)",
              f"- Convidados confirmados: {int((cv['confirmacao'] == 'Confirmado').sum())} de {len(cv)}"]
    return (f"# {cfg['nome']} — exportação de dados\n\n"
            f"Gerado em {datetime.now():%d/%m/%Y %H:%M}\n\n## Resumo\n" + "\n".join(resumo) +
            f"\n\n## Eventos\n{md_tabela(ev)}\n## Convidados\n{md_tabela(cvf)}\n"
            "## Sugestão de prompt para IA externa\n"
            "Analise os dados acima, destaque padrões e riscos (ex.: eventos pendentes, concentração de "
            "receita por mês) e sugira alternativas. Não invente dados que não estejam nas tabelas.\n")


# ── Logotipo ──
def logo_personalizado():
    return next(iter(sorted(ASSETS_DIR.glob("logo_personalizada.*"))), None) if ASSETS_DIR.exists() else None


def logo_atual():
    return logo_personalizado() or (LOGO_PADRAO if LOGO_PADRAO.exists() else None)


def salvar_logo(nome_arquivo, conteudo):
    ASSETS_DIR.mkdir(exist_ok=True)
    remover_logo()
    sufixo = "." + nome_arquivo.rsplit(".", 1)[-1].lower()
    (ASSETS_DIR / f"logo_personalizada{sufixo}").write_bytes(conteudo)


def remover_logo():
    if ASSETS_DIR.exists():
        for velho in ASSETS_DIR.glob("logo_personalizada.*"):
            velho.unlink()
