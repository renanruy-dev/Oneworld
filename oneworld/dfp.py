"""Base DFP da CVM (Demonstrações Financeiras Padronizadas de companhias abertas): carga do ZIP para um
SQLite próprio, busca de empresas e montagem do contexto financeiro que alimenta as IAs.
Não conhece Streamlit. Para atualizar a base, basta colocar o novo dfp_cia_aberta_AAAA.zip na raiz."""
import json
import os
import re
import sqlite3
import threading
import unicodedata
import zipfile
from datetime import date, datetime
from math import log
from pathlib import Path

import pandas as pd

from .config import RAIZ
from .util import brl as _brl, ler_env as _env, mascarar as _mascarar, pct as _pct, razao as _razao

# ══════════════════════════════════════════════════════════════════════════════
#  BASE DFP (CVM — Demonstrações Financeiras Padronizadas de companhias abertas)
#  Fica em um SQLite próprio (dfp_cia_aberta.db) para não inflar o oneworld.db nem os backups.
#  É dado de referência. PARA ATUALIZAR: coloque o novo dfp_cia_aberta_AAAA.zip na raiz do projeto — a
#  base é reconstruída sozinha (o ano vem dos próprios arquivos; nada no código fixa o ano).
# ══════════════════════════════════════════════════════════════════════════════
DFP_DB_PATH = RAIZ / "dfp_cia_aberta.db"
_DFP_DEMOS = ("BPA", "BPP", "DRE", "DRA", "DVA", "DFC_MD", "DFC_MI", "DMPL")
_DFP_ROTULO = {"BPA": "Balanço Patrimonial — Ativo", "BPP": "Balanço Patrimonial — Passivo",
               "DRE": "Demonstração do Resultado", "DRA": "Resultado Abrangente",
               "DFC_MI": "Fluxo de Caixa (método indireto)", "DFC_MD": "Fluxo de Caixa (método direto)",
               "DVA": "Demonstração do Valor Adicionado"}

_dfp_lock = threading.Lock()
_dfp_estado = {"estado": "nao_iniciado", "etapa": "", "erro": ""}
_dfp_cache = {"mtime": None, "empresas": None, "idx": None, "n": 0}


def _dfp_set(**kw):
    with _dfp_lock:
        _dfp_estado.update(kw)


def _norm(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode()
    return s.lower().strip()


def _dfp_fonte():
    """Procura o ZIP (ou a pasta com os arquivos) mais recente da DFP, de qualquer ano. Aceita CSV (formato
    original da CVM) ou XLSX (lido com openpyxl). Retorna Path ou None."""
    env = _env()
    if env.get("ONEWORLD_DFP_ZIP"):
        p = Path(env["ONEWORLD_DFP_ZIP"]).expanduser()
        return p if p.exists() else None
    achados = []
    for base in (RAIZ, RAIZ / "dados", RAIZ / "data", RAIZ / "dfp"):
        if base.is_dir():
            achados += [(m.group(1), z) for z in base.glob("dfp_cia_aberta_*.zip")
                        if (m := re.fullmatch(r"dfp_cia_aberta_(\d{4})\.zip", z.name))]
            achados += [(m.group(1), c.parent) for c in base.glob("dfp_cia_aberta_*.*")
                        if (m := re.fullmatch(r"dfp_cia_aberta_(\d{4})\.(csv|xlsx)", c.name))]
    return max(achados, key=lambda a: (a[0], a[1].is_file()))[1] if achados else None


def _dfp_assinatura(fonte):
    """Identifica a versão do arquivo-fonte (nome + tamanho + data): se mudar, a base é refeita."""
    alvo = fonte if fonte.is_file() else next(
        iter(sorted(fonte.glob("dfp_cia_aberta_[0-9][0-9][0-9][0-9].*"))))
    st = alvo.stat()
    return f"{alvo.name}|{st.st_size}|{int(st.st_mtime)}"


_TEXTO_NO_EXCEL = ("CD_CONTA", "CNPJ_CIA")  # colunas que o Excel costuma corromper se virarem número


def _dfp_ler_membro(nome, abrir, usecols, kw):
    """Lê um arquivo da DFP (csv ou xlsx). `abrir()` devolve um arquivo binário."""
    if nome.lower().endswith(".xlsx"):
        from . import planilha as excel  # import tardio: quem usa só CSV nem precisa do openpyxl instalado
        with abrir() as fh:
            df = excel.ler_planilha(fh.read(), texto_obrigatorio=_TEXTO_NO_EXCEL)
        return df[[c for c in df.columns if usecols(c)]] if usecols else df
    with abrir() as fh:
        return pd.read_csv(fh, sep=";", encoding="latin-1", dtype=str, **kw)


def _dfp_csv(fonte, sufixo, **kw):
    """Lê dfp_cia_aberta{sufixo}_AAAA.(csv|xlsx) do ZIP ou da pasta; prefere o .csv se houver os dois.
    Retorna None se o arquivo não existir."""
    padrao = re.compile(rf"dfp_cia_aberta{re.escape(sufixo)}_\d{{4}}\.(csv|xlsx)")
    usecols = kw.get("usecols")
    ordem = lambda n: (n.lower().endswith(".xlsx"), n)  # noqa: E731 — csv antes de xlsx
    if fonte.is_dir():
        nomes = sorted((a.name for a in fonte.iterdir() if padrao.fullmatch(a.name)), key=ordem)
        return _dfp_ler_membro(nomes[0], lambda: open(fonte / nomes[0], "rb"), usecols, kw) if nomes else None
    with zipfile.ZipFile(fonte) as zf:
        membros = sorted((m for m in zf.namelist() if padrao.fullmatch(m.rsplit("/", 1)[-1])),
                         key=lambda m: ordem(m.rsplit("/", 1)[-1]))
        if not membros:
            return None
        return _dfp_ler_membro(membros[0], lambda: zf.open(membros[0]), usecols, kw)


def _dfp_ultima_versao(df):
    """A CVM publica reapresentações: fica só a maior VERSAO de cada companhia."""
    v = pd.to_numeric(df["VERSAO"], errors="coerce").fillna(0)
    return df[v == v.groupby(df["CNPJ_CIA"]).transform("max")]


_COLUNAS_CONTA = {"CNPJ_CIA", "VERSAO", "ESCALA_MOEDA", "MOEDA", "ORDEM_EXERC", "DT_INI_EXERC",
                  "DT_FIM_EXERC", "COLUNA_DF", "CD_CONTA", "DS_CONTA", "VL_CONTA"}


def _dfp_carregar_demo(con, fonte, demo, escopo):
    df = _dfp_csv(fonte, f"_{demo}_{escopo}", usecols=lambda c: c in _COLUNAS_CONTA)
    if df is None or df.empty:
        return 0
    df = _dfp_ultima_versao(df)
    mult = df["ESCALA_MOEDA"].fillna("").str.upper().map({"MIL": 1000.0}).fillna(1.0)
    vazio = pd.Series("", index=df.index)
    out = pd.DataFrame({
        "cnpj": df["CNPJ_CIA"], "demo": demo, "escopo": escopo,
        "ordem": df["ORDEM_EXERC"].fillna("").str.upper().str.contains("PEN").map(
            {True: "PENULTIMO", False: "ULTIMO"}),
        "dt_ini": df.get("DT_INI_EXERC", vazio).fillna(""), "dt_fim": df["DT_FIM_EXERC"].fillna(""),
        "coluna_df": df.get("COLUNA_DF", vazio).fillna(""),
        "cd_conta": df["CD_CONTA"], "ds_conta": df["DS_CONTA"],
        "valor": pd.to_numeric(df["VL_CONTA"], errors="coerce") * mult,
        "moeda": df["MOEDA"].fillna("REAL")})
    out = out.dropna(subset=["valor"])
    out.to_sql("dfp_conta", con, if_exists="append", index=False, chunksize=20000)
    return len(out)


def _dfp_construir(fonte, destino):
    """Cria o banco da DFP em `destino` (arquivo temporário). Levanta exceção se algo falhar."""
    con = sqlite3.connect(destino)
    try:
        con.executescript("""
        PRAGMA journal_mode=OFF; PRAGMA synchronous=OFF;
        CREATE TABLE dfp_cia(cnpj TEXT PRIMARY KEY, cd_cvm TEXT, denom TEXT, dt_refer TEXT, versao INTEGER,
            id_doc TEXT, dt_receb TEXT, link_doc TEXT, tem_con INTEGER DEFAULT 0);
        CREATE TABLE dfp_conta(cnpj TEXT, demo TEXT, escopo TEXT, ordem TEXT, dt_ini TEXT, dt_fim TEXT,
            coluna_df TEXT, cd_conta TEXT, ds_conta TEXT, valor REAL, moeda TEXT);
        CREATE TABLE dfp_capital(cnpj TEXT PRIMARY KEY, denom TEXT, dt_refer TEXT, versao INTEGER,
            acoes_on INTEGER, acoes_pn INTEGER, acoes_total INTEGER,
            tesouro_on INTEGER, tesouro_pn INTEGER, tesouro_total INTEGER);
        CREATE TABLE dfp_parecer(cnpj TEXT, versao INTEGER, tp_relat_aud TEXT, tp_parecer TEXT,
            num_item INTEGER, texto TEXT);
        CREATE TABLE dfp_meta(chave TEXT PRIMARY KEY, valor TEXT);
        """)
        _dfp_set(etapa="Cadastro das companhias")
        cia = _dfp_csv(fonte, "")
        if cia is None:
            raise FileNotFoundError("arquivo principal dfp_cia_aberta_AAAA (csv/xlsx) não encontrado na fonte")
        cia = _dfp_ultima_versao(cia).sort_values("DT_RECEB").drop_duplicates("CNPJ_CIA", keep="last")
        pd.DataFrame({"cnpj": cia["CNPJ_CIA"], "cd_cvm": cia["CD_CVM"].str.zfill(6),  # xlsx perde zeros à esquerda
                      "denom": cia["DENOM_CIA"],
                      "dt_refer": cia["DT_REFER"], "versao": pd.to_numeric(cia["VERSAO"], errors="coerce"),
                      "id_doc": cia["ID_DOC"], "dt_receb": cia["DT_RECEB"],
                      "link_doc": cia["LINK_DOC"]}).to_sql("dfp_cia", con, if_exists="append", index=False)
        total = {"companhias": len(cia)}
        for demo in _DFP_DEMOS:
            for escopo in ("con", "ind"):
                _dfp_set(etapa=f"{demo} ({'consolidado' if escopo == 'con' else 'individual'})")
                total[f"{demo}_{escopo}"] = _dfp_carregar_demo(con, fonte, demo, escopo)
        _dfp_set(etapa="Composição do capital")
        cap = _dfp_csv(fonte, "_composicao_capital")
        if cap is not None:
            cap = _dfp_ultima_versao(cap).drop_duplicates("CNPJ_CIA", keep="last")
            num = lambda c: pd.to_numeric(cap[c], errors="coerce")  # noqa: E731
            pd.DataFrame({"cnpj": cap["CNPJ_CIA"], "denom": cap["DENOM_CIA"], "dt_refer": cap["DT_REFER"],
                          "versao": num("VERSAO"), "acoes_on": num("QT_ACAO_ORDIN_CAP_INTEGR"),
                          "acoes_pn": num("QT_ACAO_PREF_CAP_INTEGR"), "acoes_total": num("QT_ACAO_TOTAL_CAP_INTEGR"),
                          "tesouro_on": num("QT_ACAO_ORDIN_TESOURO"), "tesouro_pn": num("QT_ACAO_PREF_TESOURO"),
                          "tesouro_total": num("QT_ACAO_TOTAL_TESOURO")}
                         ).to_sql("dfp_capital", con, if_exists="append", index=False)
        _dfp_set(etapa="Pareceres e declarações")
        par = _dfp_csv(fonte, "_parecer")
        if par is not None:
            par = _dfp_ultima_versao(par)
            pd.DataFrame({"cnpj": par["CNPJ_CIA"], "versao": pd.to_numeric(par["VERSAO"], errors="coerce"),
                          "tp_relat_aud": par["TP_RELAT_AUD"], "tp_parecer": par["TP_PARECER_DECL"],
                          "num_item": pd.to_numeric(par["NUM_ITEM_PARECER_DECL"], errors="coerce"),
                          "texto": par["TXT_PARECER_DECL"]}).to_sql(
                "dfp_parecer", con, if_exists="append", index=False)
        _dfp_set(etapa="Índices")
        con.executescript("""
        CREATE INDEX ix_conta_emp ON dfp_conta(cnpj, demo, escopo, ordem, cd_conta);
        CREATE INDEX ix_conta_rank ON dfp_conta(demo, cd_conta, ordem, escopo);
        CREATE INDEX ix_parecer ON dfp_parecer(cnpj);
        UPDATE dfp_cia SET tem_con = EXISTS(SELECT 1 FROM dfp_conta x WHERE x.cnpj = dfp_cia.cnpj
                                            AND x.escopo = 'con' AND x.demo = 'BPA');
        """)
        meta = {"fonte": str(fonte), "assinatura": _dfp_assinatura(fonte),
                "ano": str(int(pd.to_numeric(cia["DT_REFER"].str[:4], errors="coerce").max())),
                "carregado_em": datetime.now().strftime("%d/%m/%Y %H:%M"),
                "linhas": json.dumps(total), "completo": "1"}
        con.executemany("INSERT INTO dfp_meta VALUES(?,?)", list(meta.items()))
        con.commit()
    finally:
        con.close()


def _dfp_trabalhar(fonte, assinatura):
    tmp = DFP_DB_PATH.with_name(DFP_DB_PATH.name + ".tmp")
    try:
        tmp.unlink(missing_ok=True)
        _dfp_construir(fonte, tmp)
        os.replace(tmp, DFP_DB_PATH)  # troca atômica: o banco só "existe" quando está completo
        _dfp_set(estado="pronto", etapa="", erro="")
    except Exception as ex:  # noqa: BLE001 — registrado em status(); nunca derruba o app
        tmp.unlink(missing_ok=True)
        _dfp_set(estado="erro", etapa="", erro=_mascarar(f"{type(ex).__name__}: {ex}")[:300],
                 falhou_em=assinatura)  # não tenta de novo a mesma fonte a cada sessão


def metadados():
    """Metadados da base carregada ({} se não existir). Ex.: ano, assinatura, carregado_em."""
    if not DFP_DB_PATH.is_file():
        return {}
    m = DFP_DB_PATH.stat().st_mtime
    if _dfp_cache.get("meta_mtime") != m:
        _dfp_cache.update(meta_mtime=m, meta=_dfp_consulta("SELECT chave, valor FROM dfp_meta")
                          .set_index("chave")["valor"].to_dict())
    return _dfp_cache["meta"]


def anos():
    """(ano_atual, ano_anterior) da base carregada, lidos dos dados — nunca fixos no código."""
    ano = int(metadados().get("ano") or 0)
    return ano, ano - 1


def iniciar(bloquear=False):
    """Garante a base DFP em segundo plano (o app não trava). Cria se não existe; refaz se o ZIP mudou
    (a base antiga continua sendo usada até a nova ficar pronta). Idempotente, segura a cada sessão."""
    with _dfp_lock:
        carregando = _dfp_estado["estado"] == "carregando"
        falhou_em = _dfp_estado.get("falhou_em")
    if not carregando:
        fonte = _dfp_fonte()
        existe = DFP_DB_PATH.is_file()
        if fonte is None:
            if not existe:
                _dfp_set(estado="sem_arquivo",
                         erro="Coloque dfp_cia_aberta_AAAA.zip na pasta do projeto (ou defina ONEWORLD_DFP_ZIP).")
        else:
            ass = _dfp_assinatura(fonte)
            if existe and metadados().get("assinatura") == ass:
                _dfp_set(estado="pronto", erro="")
            elif ass != falhou_em:
                _dfp_set(estado="carregando", etapa="Iniciando", erro="")
                t = threading.Thread(target=_dfp_trabalhar, args=(fonte, ass), name="oneworld-dfp", daemon=True)
                t.start()
                if bloquear:
                    t.join()
    elif bloquear:
        while status()["estado"] == "carregando" or _dfp_estado["estado"] == "carregando":
            threading.Event().wait(0.5)
    return status()


def status():
    """estado: pronto | carregando | sem_arquivo | erro. 'pronto' vale enquanto existir uma base utilizável,
    mesmo durante uma atualização ('atualizando')."""
    with _dfp_lock:
        est = dict(_dfp_estado)
    est["atualizando"] = est["estado"] == "carregando"
    if DFP_DB_PATH.is_file():
        est["estado"] = "pronto"
        est["ano"] = metadados().get("ano")
    return est


def _dfp_consulta(sql, params=()):
    con = sqlite3.connect(DFP_DB_PATH.resolve().as_uri() + "?mode=ro", uri=True)
    try:
        return pd.read_sql_query(sql, con, params=params)
    finally:
        con.close()


def _var(a, b):
    """Variação ano anterior→ano atual do valor (a/b − 1). Evita números enganosos: base zero, troca de sinal
    (ex.: lucro virou prejuízo) e variações acima de 1.000%."""
    if a is None or b in (None, 0) or pd.isna(a) or pd.isna(b):
        return "n/d"
    if a * b < 0:
        return "mudou de sinal"
    r = a / b - 1
    return ">+1000%" if r > 10 else _pct(r)


# ── Identificação de empresas citadas na pergunta ──
_ABREV = {"bco": "banco", "cia": "companhia", "cias": "companhias", "ind": "industria", "com": "comercio",
          "part": "participacoes", "partic": "participacoes", "distr": "distribuidora"}
_STOP = {"s", "a", "sa", "de", "do", "da", "dos", "das", "e", "ltda", "inc", "the"}
_AMBIGUAS = {"vale", "azul", "forte", "mais"}  # palavras comuns que também nomeiam companhias


def _tokens(s):
    t = [_ABREV.get(x, x) for x in re.findall(r"[a-z0-9]+", _norm(s))]
    return [x for x in t if x not in _STOP]


def _dfp_empresas():
    """Cadastro em memória + índice de tokens (recalculado se o banco mudar)."""
    m = DFP_DB_PATH.stat().st_mtime
    if _dfp_cache["mtime"] != m:
        emp = _dfp_consulta("SELECT cnpj, cd_cvm, denom, tem_con FROM dfp_cia")
        emp["tokens"] = emp["denom"].apply(_tokens)
        emp["frase"] = emp["tokens"].apply(" ".join)
        freq = {}
        for toks in emp["tokens"]:
            for t in set(toks):
                freq[t] = freq.get(t, 0) + 1
        _dfp_cache.update(mtime=m, empresas=emp, idx=freq, n=len(emp))
    return _dfp_cache["empresas"], _dfp_cache["idx"], _dfp_cache["n"]


def buscar_empresas(pergunta, limite=3):
    """Companhias citadas na pergunta: por CNPJ, por nome completo ou por palavra rara do nome.
    Heurística simples (sem IA): pode errar em nomes genéricos; por isso o contexto sempre cita
    quais empresas foram identificadas."""
    emp, freq, n = _dfp_empresas()
    achados = {}
    for c in re.findall(r"\b(\d{2})\.?(\d{3})\.?(\d{3})/?(\d{4})-?(\d{2})\b", pergunta):
        cnpj = f"{c[0]}.{c[1]}.{c[2]}/{c[3]}-{c[4]}"
        if (emp["cnpj"] == cnpj).any():
            achados[cnpj] = 1000.0
    qt = _tokens(pergunta)
    qtxt, qset = " " + " ".join(qt) + " ", set(qt)
    idf = lambda t: log(n / freq[t])  # noqa: E731
    proprio = lambda t: bool(re.search(rf"\b({t.capitalize()}|{t.upper()})\b", pergunta))  # noqa: E731
    casou, exato = {}, set()
    for r in emp.itertuples():
        toks = set(r.tokens)
        if r.frase and (len(r.tokens) >= 2 or len(r.frase) >= 4) and f" {r.frase} " in qtxt:
            score, usados = sum(idf(t) for t in r.tokens) + 5.0, toks  # nome completo citado
            exato.add(r.cnpj)
        else:  # palavra rara do nome (usada por no máximo 2 companhias); nomes curtos só se escritos "Gol"/"GOL"
            usados = {t for t in toks & qset if freq[t] <= 2 and (len(t) >= 4 or (len(t) == 3 and proprio(t)))}
            score = sum(idf(t) for t in usados)
        if usados <= _AMBIGUAS and not any(proprio(t) for t in usados):
            score = 0.0  # "isso vale a pena": palavra comum, não é a empresa
        if score:
            achados[r.cnpj], casou[r.cnpj] = max(achados.get(r.cnpj, 0), score), usados
    exatos = [casou[c] for c in exato if c in achados]
    for c in [c for c in achados if c not in exato and any(casou[c] <= e for e in exatos)]:
        del achados[c]  # "Azul" = AZUL S.A.; não puxa "SERRA AZUL WATER PARK"
    if not achados:
        return []
    topo = max(achados.values())
    ordem = sorted((c for c, sc in achados.items() if sc >= topo * 0.3), key=lambda c: -achados[c])[:limite]
    nomes = emp.set_index("cnpj")["denom"]
    return [(c, nomes[c]) for c in ordem]


# ── Blocos de contexto ──
def resumo_empresa(cnpj):
    """Texto com as linhas principais das demonstrações (ano atual x anterior) e indicadores calculados."""
    a1, a0 = anos()
    cab = _dfp_consulta("SELECT * FROM dfp_cia WHERE cnpj=?", (cnpj,)).iloc[0]
    escopo = "con" if int(cab["tem_con"]) else "ind"
    rows = _dfp_consulta(
        "SELECT demo, ordem, cd_conta, ds_conta, valor FROM dfp_conta "
        "WHERE cnpj=? AND escopo=? AND demo IN ('BPA','BPP','DRE','DRA','DFC_MI','DFC_MD','DVA') "
        "AND (cd_conta NOT LIKE '%.%.%' OR cd_conta='1.01.01') AND cd_conta NOT LIKE '3.99%' "
        "ORDER BY demo, cd_conta", (cnpj, escopo))
    v, ds, ordem_linhas = {}, {}, {}
    for r in rows.itertuples():
        v[(r.demo, r.cd_conta, r.ordem)] = r.valor
        ds[(r.demo, r.cd_conta)] = r.ds_conta
        ordem_linhas.setdefault(r.demo, [])
        if r.cd_conta not in ordem_linhas[r.demo]:
            ordem_linhas[r.demo].append(r.cd_conta)
    g = lambda d, c, o="ULTIMO": v.get((d, c, o))  # noqa: E731
    out = [f"### {cab['denom']} — CNPJ {cnpj}, CD_CVM {cab['cd_cvm']}",
           f"Demonstrações {'consolidadas' if escopo == 'con' else 'individuais (não há consolidado)'}, "
           f"exercício encerrado em {cab['dt_refer']} ({a1}) comparado a {a0}; versão {cab['versao']} "
           f"entregue à CVM em {cab['dt_receb']}. 'var.' = variação do valor {a0}→{a1} (custos e despesas "
           "são negativos: +X% significa que cresceram em módulo)."]
    demo_fluxo = "DFC_MI" if "DFC_MI" in ordem_linhas else "DFC_MD"
    for demo in ("BPA", "BPP", "DRE", "DRA", demo_fluxo, "DVA"):
        if demo not in ordem_linhas:
            continue
        out.append(f"**{_DFP_ROTULO[demo]} ({demo})**")
        for cd in ordem_linhas[demo]:
            a, b = g(demo, cd), g(demo, cd, "PENULTIMO")
            out.append(f"- {cd} {ds[(demo, cd)]}: {a1} {_brl(a)} | {a0} {_brl(b)} | var. {_var(a, b)}")
    # indicadores calculados pelo OneWorld (só quando a estrutura de contas permite)
    ind = []
    pl = _dfp_consulta(
        "SELECT ordem, valor FROM dfp_conta WHERE cnpj=? AND escopo=? AND demo='BPP' AND cd_conta LIKE '2.0_' "
        "AND ds_conta LIKE 'Patrim_nio L_quido%' ORDER BY cd_conta", (cnpj, escopo))
    pl21 = next((r.valor for r in pl.itertuples() if r.ordem == "ULTIMO"), None)
    ativo, rec = g("BPA", "1"), g("DRE", "3.01")
    ll = g("DRA", "4.01")
    if ll is None and str(ds.get(("DRE", "3.11"), "")).startswith("Lucro"):
        ll = g("DRE", "3.11")
    if ds.get(("DRE", "3.03"), "") == "Resultado Bruto":
        ind.append(f"margem bruta {_pct(_razao(g('DRE', '3.03'), rec)).lstrip('+')}")
    if ds.get(("DRE", "3.05"), "").startswith("Resultado Antes do Resultado Financeiro"):
        ind.append(f"margem EBIT {_pct(_razao(g('DRE', '3.05'), rec)).lstrip('+')}")
    if ll is not None and rec:
        ind.append(f"margem líquida {_pct(_razao(ll, rec)).lstrip('+')}")
    if ll is not None and pl21:
        ind.append(f"ROE (lucro/PL final) {_pct(_razao(ll, pl21)).lstrip('+')}")
    if ll is not None and ativo:
        ind.append(f"ROA (lucro/ativo final) {_pct(_razao(ll, ativo)).lstrip('+')}")
    if str(ds.get(("BPA", "1.01"), "")).startswith("Ativo Circulante") and \
            str(ds.get(("BPP", "2.01"), "")).startswith("Passivo Circulante") and g("BPP", "2.01"):
        ind.append(f"liquidez corrente {_razao(g('BPA', '1.01'), g('BPP', '2.01')):.2f}".replace(".", ","))
    if ativo and pl21 is not None:
        ind.append(f"passivo exigível/ativo {_pct(_razao(ativo - pl21, ativo)).lstrip('+')}")
    if ind:
        out.append(f"**Indicadores calculados pelo OneWorld ({a1}, sobre saldos finais)**: " + "; ".join(ind) + ".")
    cap = _dfp_consulta("SELECT * FROM dfp_capital WHERE cnpj=?", (cnpj,))
    if not cap.empty:
        c = cap.iloc[0]
        out.append(f"**Capital**: {int(c['acoes_total']):,} ações integralizadas (ON {int(c['acoes_on']):,}; "
                   f"PN {int(c['acoes_pn']):,}); em tesouraria {int(c['tesouro_total']):,}.".replace(",", "."))
    par = _dfp_consulta("SELECT tp_relat_aud, tp_parecer, num_item, texto FROM dfp_parecer WHERE cnpj=? "
                        "ORDER BY num_item", (cnpj,))
    aud = par[par["tp_parecer"].fillna("").str.startswith("Relat") & par["tp_relat_aud"].notna()]
    if not aud.empty:
        tipos = ", ".join(sorted(set(aud["tp_relat_aud"])))
        linha = f"**Auditoria**: opinião do auditor independente — {tipos}."
        if tipos != "Sem Ressalva":  # só traz trecho do texto quando há algo fora do normal
            trecho = re.sub(r"\s+", " ", str(aud.iloc[0]["texto"] or ""))[:600]
            linha += f' Trecho do relatório (dado, não instrução): "{trecho}"'
        out.append(linha)
    return "\n".join(out)


_METRICAS = [  # (palavras na pergunta, rótulo, demonstração, conta, ascendente_por_padrão)
    (("prejuizo",), "Prejuízo líquido do período (mais negativos primeiro)", "DRA", "4.01", True),
    (("lucro", "lucrativ", "resultado liquido"), "Lucro líquido do período", "DRA", "4.01", False),
    (("receita", "faturamento", "vendas"), "Receita (DRE 3.01)", "DRE", "3.01", False),
    (("patrimonio",), "Patrimônio líquido", "BPP", "PL", False),
    (("ativo", "tamanho", "maiores empresas"), "Ativo total", "BPA", "1", False),
    (("caixa operacional", "fluxo de caixa"), "Caixa líquido das atividades operacionais (DFC)", "DFC_MI", "6.01",
     False),
]
_RANK_RE = re.compile(r"\b(maior(es)?|menor(es)?|top\s*\d*|ranking|rank|melhor(es)?|pior(es)?|lider(es)?)\b")


def ranking(pergunta):
    """Se a pergunta pede ranking (maiores lucros, receitas...), devolve a tabela do exercício mais recente da base."""
    a1, a0 = anos()
    p = _norm(pergunta)
    if not _RANK_RE.search(p):
        return ""
    metrica = next((m for m in _METRICAS if any(k in p for k in m[0])), None)
    if not metrica:
        return ""
    _, rotulo, demo, conta, asc = metrica
    if "prejuizo" not in p:  # prejuízo já vem do mais negativo; nos demais, "menor/pior" inverte a ordem
        asc = bool(re.search(r"\b(menor(es)?|pior(es)?)\b", p))
    m = re.search(r"\btop\s*(\d{1,2})\b|\b(\d{1,2})\s+(?:maiores|menores|melhores|piores)\b", p)
    n = max(1, min(int(next(g for g in m.groups() if g)) if m else 10, 20))
    filtro_conta = ("x.cd_conta IN ('2.03','2.07','2.08') AND x.ds_conta LIKE 'Patrim_nio L_quido%'"
                    if conta == "PL" else "x.cd_conta = ?")
    params = [] if conta == "PL" else [conta]
    sql = ("SELECT c.denom AS empresa, x.escopo AS escopo, x.valor AS v21, y.valor AS v20 "
           "FROM dfp_conta x JOIN dfp_cia c ON c.cnpj = x.cnpj "
           "LEFT JOIN dfp_conta y ON y.cnpj=x.cnpj AND y.demo=x.demo AND y.escopo=x.escopo "
           "AND y.cd_conta=x.cd_conta AND y.ordem='PENULTIMO' "
           f"WHERE x.demo=? AND {filtro_conta} AND x.ordem='ULTIMO' "
           "AND (x.escopo='con' OR (x.escopo='ind' AND c.tem_con=0)) "
           f"{'AND x.valor < 0 ' if 'prejuizo' in p else ''}"
           f"ORDER BY x.valor {'ASC' if asc else 'DESC'} LIMIT ?")
    df = _dfp_consulta(sql, [demo] + params + [n])
    if df.empty:
        return ""
    linhas = [f"**Ranking — {rotulo}, exercício {a1}** (consolidado quando existe, senão individual; "
              f"{'crescente' if asc else 'decrescente'}):"]
    for i, r in enumerate(df.itertuples(), 1):
        linhas.append(f"{i}. {r.empresa} ({'cons.' if r.escopo == 'con' else 'ind.'}): {_brl(r.v21)} "
                      f"({a0}: {_brl(r.v20)})")
    return "\n".join(linhas)


def visao_geral():
    meta, (a1, a0) = metadados(), anos()
    cnt = _dfp_consulta("SELECT COUNT(*) AS n, SUM(tem_con) AS con FROM dfp_cia").iloc[0]
    aud = _dfp_consulta("SELECT tp_relat_aud AS t, COUNT(DISTINCT cnpj) AS n FROM dfp_parecer "
                        "WHERE tp_relat_aud IS NOT NULL GROUP BY tp_relat_aud ORDER BY n DESC")
    idade = date.today().year - a1
    return (f"Base DFP {a1} da CVM (dados abertos, Demonstrações Financeiras Padronizadas de companhias abertas): "
            f"{int(cnt['n'])} companhias ({int(cnt['con'])} com demonstrações consolidadas). Exercício {a1} com "
            f"comparativo de {a0}; só a versão mais recente de cada companhia; valores em R$ já convertidos de 'mil' "
            "para reais. Demonstrações: BPA, BPP, DRE, DRA, DVA, DFC (direto/indireto), DMPL; mais composição do "
            "capital e pareceres. Opiniões de auditoria no conjunto: "
            + "; ".join(f"{r.t}: {r.n}" for r in aud.itertuples())
            + f". Carga em {meta.get('carregado_em', 'n/d')}. DEFASAGEM: são dados do exercício {a1}, "
              f"{idade} ano(s) antes de hoje ({date.today():%d/%m/%Y}); a base será atualizada no futuro.")


def contexto(pergunta):
    """Contexto financeiro para a pergunta. Retorna (texto, fontes)."""
    est = status()
    if est["estado"] != "pronto":
        motivo = {"carregando": f"ainda está sendo carregada ({est['etapa']})",
                  "sem_arquivo": "não foi encontrada", "erro": "falhou ao carregar"}.get(est["estado"], "indisponível")
        return (f"A base DFP {motivo}. NÃO responda com números da DFP nesta resposta; avise o usuário.", [])
    ano = anos()[0]
    partes, fontes = [visao_geral()], [f"DFP {ano}: visão geral"]
    rank = ranking(pergunta)
    if rank:
        partes.append(rank)
        fontes.append(f"DFP {ano}: ranking")
    empresas = buscar_empresas(pergunta)
    for cnpj, nome in empresas:
        partes.append(resumo_empresa(cnpj))
        fontes.append(f"DFP {ano}: {nome}")
    if not empresas and not rank:
        partes.append("Nenhuma companhia específica foi identificada na pergunta. Se o usuário quer dados de uma "
                      "empresa, peça o nome completo ou o CNPJ.")
    return "\n\n".join(partes), fontes
