"""Catálogo multi-base da CVM, persistência de comparação e motor simples de Decision Intelligence."""
from __future__ import annotations

import re
import sqlite3
import uuid
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any, Sequence

import pandas as pd

from . import backend as bk
from . import config as app_cfg
from . import database as db

CHAVE_CONFIG = "cvm_comparacao"
_CACHE_RESUMO: dict[str, tuple[str, dict[str, Any]]] = {}
_CONTA_DRE = {"3.01", "3.02", "3.03", "3.09", "3.11"}
_COLUNAS_DRE = {
    "CNPJ_CIA",
    "DT_REFER",
    "VERSAO",
    "GRUPO_DFP",
    "ESCALA_MOEDA",
    "ORDEM_EXERC",
    "CD_CONTA",
    "VL_CONTA",
}
_COLUNAS_CIA = {"CNPJ_CIA", "DT_REFER", "VERSAO", "CATEG_DOC"}


def _dirs_descoberta() -> tuple[Path, ...]:
    raiz = app_cfg.RAIZ
    return (raiz, raiz / "dados", raiz / "data", raiz / "dfp")


def _fmt_pct(valor: float, com_sinal: bool = False) -> str:
    txt = f"{valor:+.1f}%" if com_sinal else f"{valor:.1f}%"
    return txt.replace(".", ",")


def _norm_caminho(caminho: str | Path) -> str:
    try:
        return str(Path(caminho).expanduser().resolve())
    except OSError:
        return str(caminho)


def _assinatura_caminho(caminho: Path) -> str:
    if caminho.is_file():
        st = caminho.stat()
        return f"f|{caminho.resolve()}|{st.st_size}|{st.st_mtime_ns}"
    if caminho.is_dir():
        arqs = sorted(
            (p.name, p.stat().st_size, p.stat().st_mtime_ns)
            for p in caminho.iterdir()
            if p.is_file() and p.suffix.lower() in (".csv", ".xlsx")
        )
        return f"d|{caminho.resolve()}|{hash(tuple(arqs))}"
    raise FileNotFoundError(f"Caminho CVM não encontrado: {caminho}")


def _ler_tabela_cvm(nome: str, abrir, usecols_alvo: set[str]) -> pd.DataFrame:
    if nome.lower().endswith(".xlsx"):
        from . import planilha as excel

        with abrir() as fh:
            df = excel.ler_planilha(fh.read(), texto_obrigatorio=("CD_CONTA", "CNPJ_CIA"))
        cols = [c for c in df.columns if c in usecols_alvo]
        return df[cols] if cols else df
    with abrir() as fh:
        return pd.read_csv(
            fh,
            sep=";",
            encoding="latin-1",
            dtype=str,
            usecols=lambda c: c in usecols_alvo,
        )


def _para_numero(serie: pd.Series) -> pd.Series:
    if pd.api.types.is_numeric_dtype(serie):
        return pd.to_numeric(serie, errors="coerce")
    s = serie.astype(str).str.strip()
    tem_virgula = s.str.contains(",", regex=False, na=False)
    if tem_virgula.any():
        s = s.where(~tem_virgula, s.str.replace(".", "", regex=False).str.replace(",", ".", regex=False))
    return pd.to_numeric(s, errors="coerce")


def _ultima_versao(df: pd.DataFrame) -> pd.DataFrame:
    if "VERSAO" not in df.columns or "CNPJ_CIA" not in df.columns or df.empty:
        return df
    v = pd.to_numeric(df["VERSAO"], errors="coerce").fillna(0)
    return df[v == v.groupby(df["CNPJ_CIA"]).transform("max")]


def _ano_de_texto(texto: Any) -> int:
    if texto is None or (not isinstance(texto, str) and pd.isna(texto)):
        return 0
    m = re.search(r"((?:19|20)\d{2})", str(texto))
    return int(m.group(1)) if m else 0


def _localizar_membros_cvm(caminho: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    """Localiza fonte principal (cadastro) e DRE (consolidada ou individual) em ZIP, pasta ou arquivo."""
    if not caminho.exists():
        raise FileNotFoundError(f"Arquivo ou pasta da CVM não encontrado: {caminho}")

    def eh_dre(nome: str) -> tuple[int, str] | None:
        base = nome.rsplit("/", 1)[-1].lower()
        if not base.endswith((".csv", ".xlsx")):
            return None
        if "_dre_con_" in base or base.startswith("dre_con"):
            return (0 if base.endswith(".csv") else 1, nome)
        if "_dre_ind_" in base or base.startswith("dre_ind") or "_dre_" in base:
            return (2 if base.endswith(".csv") else 3, nome)
        return None

    def eh_principal(nome: str) -> tuple[int, str] | None:
        base = nome.rsplit("/", 1)[-1].lower()
        if not base.endswith((".csv", ".xlsx")):
            return None
        if re.fullmatch(r"dfp_cia_aberta_\d{4}\.(csv|xlsx)", base):
            return (0 if base.endswith(".csv") else 1, nome)
        return None

    if caminho.is_file() and caminho.suffix.lower() == ".zip":
        with zipfile.ZipFile(caminho) as zf:
            nomes = zf.namelist()
        dre = sorted((res for n in nomes if (res := eh_dre(n)) is not None), key=lambda x: x)
        cia = sorted((res for n in nomes if (res := eh_principal(n)) is not None), key=lambda x: x)
        if not dre and not cia:
            raise ValueError(f"O ZIP '{caminho.name}' não contém arquivos reconhecidos da base DFP da CVM.")
        info_cia = {"tipo": "zip", "zip": caminho, "membro": cia[0][1]} if cia else {}
        info_dre = {"tipo": "zip", "zip": caminho, "membro": dre[0][1]} if dre else {}
        return info_cia, info_dre

    if caminho.is_dir():
        arquivos = [p.name for p in caminho.iterdir() if p.is_file()]
        dre = sorted((res for n in arquivos if (res := eh_dre(n)) is not None), key=lambda x: x)
        cia = sorted((res for n in arquivos if (res := eh_principal(n)) is not None), key=lambda x: x)
        if not dre and not cia:
            raise ValueError(f"A pasta '{caminho.name}' não contém arquivos reconhecidos da base DFP da CVM.")
        info_cia = {"tipo": "arq", "path": caminho / cia[0][1]} if cia else {}
        info_dre = {"tipo": "arq", "path": caminho / dre[0][1]} if dre else {}
        return info_cia, info_dre

    suf = caminho.suffix.lower()
    if suf not in (".csv", ".xlsx"):
        raise ValueError(f"Formato não suportado para base CVM: '{caminho.name}'. Use .zip, .csv ou .xlsx.")

    # Arquivo individual (.csv ou .xlsx)
    nome_l = caminho.name.lower()
    pasta = caminho.parent
    arquivos_irmao = [p.name for p in pasta.iterdir() if p.is_file()]

    # Verifica rapidamente se o arquivo é DRE ou cadastro principal pelas colunas/nome
    if "dre" in nome_l:
        cia_irmaos = sorted((res for n in arquivos_irmao if (res := eh_principal(n)) is not None), key=lambda x: x)
        info_cia = {"tipo": "arq", "path": pasta / cia_irmaos[0][1]} if cia_irmaos else {}
        return info_cia, {"tipo": "arq", "path": caminho}

    # Inspeciona cabeçalho para confirmar se é DRE (CD_CONTA) ou índice (CNPJ_CIA)
    df_head = _ler_tabela_cvm(
        caminho.name,
        lambda: open(caminho, "rb"),
        _COLUNAS_DRE | _COLUNAS_CIA,
    )
    cols = set(df_head.columns)
    if {"CD_CONTA", "VL_CONTA"}.issubset(cols):
        cia_irmaos = sorted((res for n in arquivos_irmao if (res := eh_principal(n)) is not None), key=lambda x: x)
        info_cia = {"tipo": "arq", "path": pasta / cia_irmaos[0][1]} if cia_irmaos else {}
        return info_cia, {"tipo": "arq", "path": caminho}

    if "CNPJ_CIA" in cols:
        ano_arq = _ano_de_texto(caminho.name)
        candidatos_dre = sorted(
            (res for n in arquivos_irmao if (res := eh_dre(n)) is not None and (not ano_arq or str(ano_arq) in n)),
            key=lambda x: x,
        )
        if not candidatos_dre:
            candidatos_dre = sorted((res for n in arquivos_irmao if (res := eh_dre(n)) is not None), key=lambda x: x)
        info_dre = {"tipo": "arq", "path": pasta / candidatos_dre[0][1]} if candidatos_dre else {}
        return {"tipo": "arq", "path": caminho}, info_dre

    raise ValueError(f"O arquivo '{caminho.name}' não possui colunas reconhecidas da CVM (CNPJ_CIA / CD_CONTA).")


def _carregar_membro(info: dict[str, Any], cols: set[str]) -> pd.DataFrame:
    if not info:
        return pd.DataFrame()
    if info["tipo"] == "zip":
        zp: Path = info["zip"]
        membro: str = info["membro"]
        with zipfile.ZipFile(zp) as zf:
            return _ler_tabela_cvm(membro, lambda: zf.open(membro), cols)
    p: Path = info["path"]
    return _ler_tabela_cvm(p.name, lambda: open(p, "rb"), cols)


def _calcular_metricas_dre(df_dre: pd.DataFrame) -> dict[str, Any]:
    if df_dre.empty or not {"CNPJ_CIA", "CD_CONTA", "VL_CONTA"}.issubset(df_dre.columns):
        return {
            "companhias_analisadas": 0,
            "margem_bruta_pct": None,
            "margem_liquida_pct": None,
            "custo_sobre_receita_pct": None,
            "variacao_receita_pct": None,
            "receita_mediana": None,
        }

    df = _ultima_versao(df_dre).copy()
    df["CD_CONTA"] = df["CD_CONTA"].astype(str).str.strip()
    df = df[df["CD_CONTA"].isin(_CONTA_DRE)].copy()
    if df.empty:
        return {
            "companhias_analisadas": 0,
            "margem_bruta_pct": None,
            "margem_liquida_pct": None,
            "custo_sobre_receita_pct": None,
            "variacao_receita_pct": None,
            "receita_mediana": None,
        }

    escala = df["ESCALA_MOEDA"] if "ESCALA_MOEDA" in df.columns else pd.Series("", index=df.index)
    mult = escala.fillna("").astype(str).str.upper().map({"MIL": 1000.0}).fillna(1.0)
    df["valor"] = _para_numero(df["VL_CONTA"]) * mult
    df = df.dropna(subset=["valor"])

    if "ORDEM_EXERC" in df.columns:
        eh_pen = df["ORDEM_EXERC"].fillna("").astype(str).str.upper().str.contains("PEN", regex=False)
    else:
        eh_pen = pd.Series(False, index=df.index)

    ult = df[~eh_pen]
    pen = df[eh_pen]

    rec_u = ult[ult["CD_CONTA"] == "3.01"].groupby("CNPJ_CIA")["valor"].first()
    rec_p = pen[pen["CD_CONTA"] == "3.01"].groupby("CNPJ_CIA")["valor"].first()
    custo_u = ult[ult["CD_CONTA"] == "3.02"].groupby("CNPJ_CIA")["valor"].first()
    bruto_u = ult[ult["CD_CONTA"] == "3.03"].groupby("CNPJ_CIA")["valor"].first()
    lucro_u = ult[ult["CD_CONTA"] == "3.11"].groupby("CNPJ_CIA")["valor"].first()
    if lucro_u.empty:
        lucro_u = ult[ult["CD_CONTA"] == "3.09"].groupby("CNPJ_CIA")["valor"].first()

    tab = pd.DataFrame(
        {
            "rec_u": rec_u,
            "rec_p": rec_p,
            "custo_u": custo_u,
            "bruto_u": bruto_u,
            "lucro_u": lucro_u,
        }
    )
    tab = tab[tab["rec_u"] > 0].copy()
    if tab.empty:
        return {
            "companhias_analisadas": 0,
            "margem_bruta_pct": None,
            "margem_liquida_pct": None,
            "custo_sobre_receita_pct": None,
            "variacao_receita_pct": None,
            "receita_mediana": None,
        }

    # Caso 3.03 (Resultado Bruto) não esteja preenchido, usa Receita - |Custo| quando disponível
    bruto_efetivo = tab["bruto_u"].where(tab["bruto_u"].notna(), tab["rec_u"] - tab["custo_u"].abs())
    mb = (bruto_efetivo / tab["rec_u"]) * 100.0
    ml = (tab["lucro_u"] / tab["rec_u"]) * 100.0
    cr = (tab["custo_u"].abs() / tab["rec_u"]) * 100.0

    valid_var = tab[tab["rec_p"] > 0]
    if not valid_var.empty:
        var_rec = ((valid_var["rec_u"] - valid_var["rec_p"]) / valid_var["rec_p"]) * 100.0
        var_med = round(float(var_rec.median()), 2)
    else:
        var_med = None

    def _med_round(s: pd.Series) -> float | None:
        s_ok = s.dropna()
        return round(float(s_ok.median()), 2) if not s_ok.empty else None

    return {
        "companhias_analisadas": int(len(tab)),
        "margem_bruta_pct": _med_round(mb),
        "margem_liquida_pct": _med_round(ml),
        "custo_sobre_receita_pct": _med_round(cr),
        "variacao_receita_pct": var_med,
        "receita_mediana": round(float(tab["rec_u"].median()), 2),
    }


def _gerar_nome_padrao(caminho: Path, ano: int, titulo_arquivo: str, categ_doc: str) -> str:
    if titulo_arquivo:
        suf_ano = f" {ano}" if ano and str(ano) not in titulo_arquivo else ""
        return f"{titulo_arquivo}{suf_ano} ({caminho.name})"
    if categ_doc:
        suf_ano = f" {ano}" if ano else ""
        return f"{categ_doc} CVM{suf_ano} ({caminho.name})"
    if ano:
        return f"DFP CVM {ano} ({caminho.name})"
    return caminho.name


def extrair_resumo_cvm(caminho: str | Path) -> dict[str, Any]:
    """Extrai metadados e indicadores medianos precisos de uma fonte CVM (ZIP, pasta, CSV ou XLSX)."""
    p = Path(caminho).expanduser()
    assinatura = _assinatura_caminho(p)
    if assinatura in _CACHE_RESUMO and _CACHE_RESUMO[assinatura][0] == assinatura:
        return dict(_CACHE_RESUMO[assinatura][1])

    info_cia, info_dre = _localizar_membros_cvm(p)
    df_cia = _carregar_membro(info_cia, _COLUNAS_CIA)
    df_dre = _carregar_membro(info_dre, _COLUNAS_DRE)

    total_cias = 0
    datas_ref: list[str] = []
    categ_doc = ""
    titulo_arquivo = ""

    if not df_cia.empty:
        df_cia_u = _ultima_versao(df_cia)
        if "CNPJ_CIA" in df_cia_u.columns:
            total_cias = int(df_cia_u["CNPJ_CIA"].dropna().nunique())
        else:
            total_cias = int(len(df_cia_u))
        if "DT_REFER" in df_cia_u.columns:
            datas_ref.extend(str(x).strip() for x in df_cia_u["DT_REFER"].dropna() if str(x).strip())
        if "CATEG_DOC" in df_cia_u.columns:
            vals = [str(x).strip() for x in df_cia_u["CATEG_DOC"].dropna() if str(x).strip()]
            if vals:
                categ_doc = vals[0]

    if not df_dre.empty:
        if not total_cias and "CNPJ_CIA" in df_dre.columns:
            total_cias = int(df_dre["CNPJ_CIA"].dropna().nunique())
        if "DT_REFER" in df_dre.columns:
            datas_ref.extend(str(x).strip() for x in df_dre["DT_REFER"].dropna() if str(x).strip())
        if "GRUPO_DFP" in df_dre.columns and info_dre.get("path") == p:
            vals = [str(x).strip() for x in df_dre["GRUPO_DFP"].dropna() if str(x).strip()]
            if vals:
                titulo_arquivo = vals[0]

    data_ref = max(datas_ref) if datas_ref else ""
    ano_ref = _ano_de_texto(data_ref) or _ano_de_texto(p.name)
    ano_ant = ano_ref - 1 if ano_ref else 0
    if not data_ref and ano_ref:
        data_ref = f"{ano_ref}-12-31"

    metricas = _calcular_metricas_dre(df_dre)
    nome_padrao = _gerar_nome_padrao(p, ano_ref, titulo_arquivo, categ_doc)

    resumo = {
        "nome_padrao": nome_padrao,
        "arquivo_padrao": p.name,
        "ano_referencia": ano_ref,
        "ano_anterior": ano_ant,
        "data_referencia": data_ref,
        "total_companhias": total_cias,
        **metricas,
    }
    _CACHE_RESUMO[assinatura] = (assinatura, dict(resumo))
    return resumo


def _criar_item_base(caminho: str | Path, nome_custom: str | None = None, base_id: str | None = None) -> dict[str, Any]:
    p = Path(caminho).expanduser()
    resumo = extrair_resumo_cvm(p)
    nome_padrao = resumo["nome_padrao"]
    nome_final = (nome_custom or "").strip() or nome_padrao
    return {
        "id": base_id or uuid.uuid4().hex[:12],
        "nome": nome_final,
        "nome_padrao": nome_padrao,
        "caminho": _norm_caminho(p),
        "arquivo_padrao": resumo["arquivo_padrao"],
        "ano_referencia": resumo["ano_referencia"],
        "ano_anterior": resumo["ano_anterior"],
        "data_referencia": resumo["data_referencia"],
        "atualizado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "resumo": resumo,
    }


def _descobrir_zips_cvm() -> list[Path]:
    achados: list[Path] = []
    vistos: set[str] = set()
    for base in _dirs_descoberta():
        if not base.is_dir():
            continue
        for z in sorted(base.glob("dfp_cia_aberta_*.zip")):
            if re.fullmatch(r"dfp_cia_aberta_\d{4}\.zip", z.name):
                res = _norm_caminho(z)
                if res not in vistos:
                    vistos.add(res)
                    achados.append(z)
    return achados


def _normalizar_estado(raw: Any) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raw = {}
    bases_raw = raw.get("bases") if isinstance(raw.get("bases"), list) else []
    bases: list[dict[str, Any]] = []
    for b in bases_raw:
        if isinstance(b, dict) and b.get("id"):
            bases.append(dict(b))
    ids_validos = {b["id"] for b in bases}
    sel_raw = raw.get("selecionadas") if isinstance(raw.get("selecionadas"), list) else []
    selecionadas = [sid for sid in sel_raw if sid in ids_validos]
    exc_raw = raw.get("excluidas") if isinstance(raw.get("excluidas"), list) else []
    excluidas = [str(x) for x in exc_raw if x]
    return {
        "ativa": bool(raw.get("ativa", False)),
        "bases": bases,
        "selecionadas": selecionadas,
        "excluidas": excluidas,
    }


def carregar_estado_cvm() -> dict[str, Any]:
    """Lê o estado persistido da comparação CVM (sem gravar no banco durante leitura)."""
    bruto = None
    if db.DB_PATH.exists():
        try:
            bruto = db.cfg_ler(CHAVE_CONFIG, None)
        except sqlite3.Error:
            bruto = None
    estado = _normalizar_estado(bruto)

    caminhos_existentes = {_norm_caminho(b.get("caminho", "")) for b in estado["bases"]}
    nomes_existentes = {str(b.get("arquivo_padrao", "")) for b in estado["bases"]}
    excluidas = set(estado["excluidas"])

    for zp in _descobrir_zips_cvm():
        norm_p = _norm_caminho(zp)
        if norm_p in caminhos_existentes or norm_p in excluidas or zp.name in excluidas:
            continue
        if zp.name in nomes_existentes:
            continue
        try:
            item = _criar_item_base(zp, base_id=f"cvm_{zp.stem}")
        except (OSError, ValueError, zipfile.BadZipFile):
            continue
        estado["bases"].append(item)
        caminhos_existentes.add(norm_p)
        nomes_existentes.add(zp.name)

    return estado


def _salvar_estado_cvm(estado: dict[str, Any]) -> dict[str, Any]:
    limpo = _normalizar_estado(estado)
    try:
        db.cfg_gravar(CHAVE_CONFIG, limpo)
    except sqlite3.OperationalError:
        db.init_db()
        db.cfg_gravar(CHAVE_CONFIG, limpo)
    return limpo


def ordenar_bases_recentes(bases: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    """Ordena bases da mais recente para a mais antiga (ano, data de referência e atualização)."""
    return sorted(
        bases,
        key=lambda b: (
            int(b.get("ano_referencia") or 0),
            str(b.get("data_referencia") or ""),
            str(b.get("atualizado_em") or ""),
        ),
        reverse=True,
    )


def adicionar_bases_cvm(
    caminhos: Sequence[str | Path] | str | Path,
    nome_custom: str | None = None,
) -> list[dict[str, Any]]:
    """Adiciona uma ou várias fontes CVM ao catálogo e persiste no SQLite."""
    lista_caminhos = [caminhos] if isinstance(caminhos, (str, Path)) else list(caminhos)
    if not lista_caminhos:
        return []

    estado = carregar_estado_cvm()
    excluidas = set(estado["excluidas"])
    adicionadas: list[dict[str, Any]] = []

    for idx, c in enumerate(lista_caminhos):
        nome_item = nome_custom if (nome_custom and len(lista_caminhos) == 1 and idx == 0) else None
        item = _criar_item_base(c, nome_custom=nome_item)
        norm_p = item["caminho"]
        excluidas.discard(norm_p)
        excluidas.discard(item["arquivo_padrao"])

        # Evita duplicar exatamente o mesmo arquivo já cadastrado; atualiza-o se já existir
        existente = next((b for b in estado["bases"] if _norm_caminho(b.get("caminho", "")) == norm_p), None)
        if existente is not None:
            existente.update(
                {
                    "nome_padrao": item["nome_padrao"],
                    "arquivo_padrao": item["arquivo_padrao"],
                    "ano_referencia": item["ano_referencia"],
                    "ano_anterior": item["ano_anterior"],
                    "data_referencia": item["data_referencia"],
                    "atualizado_em": item["atualizado_em"],
                    "resumo": item["resumo"],
                }
            )
            if nome_item:
                existente["nome"] = nome_item.strip()
            adicionadas.append(dict(existente))
        else:
            estado["bases"].append(item)
            if estado["ativa"] and item["id"] not in estado["selecionadas"]:
                estado["selecionadas"].append(item["id"])
            adicionadas.append(dict(item))

    estado["excluidas"] = sorted(excluidas)
    _salvar_estado_cvm(estado)
    return adicionadas


def renomear_base_cvm(base_id: str, novo_nome: str) -> dict[str, Any]:
    """Renomeia uma base CVM (se vazio, restaura o nome padrão do arquivo) e persiste."""
    estado = carregar_estado_cvm()
    alvo = next((b for b in estado["bases"] if b["id"] == base_id), None)
    if alvo is None:
        raise KeyError(f"Base CVM '{base_id}' não encontrada.")
    nome_limpo = str(novo_nome or "").strip()
    padrao = alvo.get("nome_padrao") or alvo.get("arquivo_padrao") or "Base CVM"
    alvo["nome"] = nome_limpo or padrao
    alvo["atualizado_em"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return _salvar_estado_cvm(estado)


def atualizar_arquivo_cvm(base_id: str, novo_caminho: str | Path) -> dict[str, Any]:
    """Substitui o arquivo de uma base CVM existente, recalcula os indicadores e persiste."""
    estado = carregar_estado_cvm()
    alvo = next((b for b in estado["bases"] if b["id"] == base_id), None)
    if alvo is None:
        raise KeyError(f"Base CVM '{base_id}' não encontrada.")

    antigo_caminho = _norm_caminho(alvo.get("caminho", ""))
    antigo_arq = str(alvo.get("arquivo_padrao", ""))
    antigo_padrao = str(alvo.get("nome_padrao", ""))
    usava_nome_padrao = alvo.get("nome") in ("", antigo_padrao, antigo_arq)

    novo_item = _criar_item_base(novo_caminho, base_id=base_id)
    excluidas = set(estado["excluidas"])
    if antigo_caminho and antigo_caminho != novo_item["caminho"]:
        excluidas.add(antigo_caminho)
    if antigo_arq and antigo_arq != novo_item["arquivo_padrao"]:
        excluidas.add(antigo_arq)
    excluidas.discard(novo_item["caminho"])
    excluidas.discard(novo_item["arquivo_padrao"])

    alvo["nome_padrao"] = novo_item["nome_padrao"]
    if usava_nome_padrao:
        alvo["nome"] = novo_item["nome_padrao"]
    alvo["caminho"] = novo_item["caminho"]
    alvo["arquivo_padrao"] = novo_item["arquivo_padrao"]
    alvo["ano_referencia"] = novo_item["ano_referencia"]
    alvo["ano_anterior"] = novo_item["ano_anterior"]
    alvo["data_referencia"] = novo_item["data_referencia"]
    alvo["atualizado_em"] = novo_item["atualizado_em"]
    alvo["resumo"] = novo_item["resumo"]

    estado["excluidas"] = sorted(excluidas)
    return _salvar_estado_cvm(estado)


def excluir_base_cvm(base_id: str) -> dict[str, Any]:
    """Exclui uma base CVM do catálogo e persiste a remoção no SQLite."""
    estado = carregar_estado_cvm()
    alvo = next((b for b in estado["bases"] if b["id"] == base_id), None)
    if alvo is None:
        return estado
    estado["bases"] = [b for b in estado["bases"] if b["id"] != base_id]
    estado["selecionadas"] = [sid for sid in estado["selecionadas"] if sid != base_id]
    excluidas = set(estado["excluidas"])
    if alvo.get("caminho"):
        excluidas.add(_norm_caminho(alvo["caminho"]))
    if alvo.get("arquivo_padrao"):
        excluidas.add(str(alvo["arquivo_padrao"]))
    estado["excluidas"] = sorted(excluidas)
    return _salvar_estado_cvm(estado)


def definir_comparacao_ativa(ativa: bool) -> dict[str, Any]:
    """Habilita ou desabilita a comparação CVM. Ao ativar sem seleção prévia, seleciona todas as bases."""
    estado = carregar_estado_cvm()
    estado["ativa"] = bool(ativa)
    if estado["ativa"] and not estado["selecionadas"]:
        estado["selecionadas"] = [b["id"] for b in estado["bases"]]
    return _salvar_estado_cvm(estado)


def definir_bases_selecionadas(ids: Sequence[str]) -> dict[str, Any]:
    """Persiste quais bases CVM específicas foram marcadas pelo usuário."""
    estado = carregar_estado_cvm()
    ids_validos = {b["id"] for b in estado["bases"]}
    vistos: set[str] = set()
    limpos: list[str] = []
    for sid in ids:
        if sid in ids_validos and sid not in vistos:
            vistos.add(sid)
            limpos.append(sid)
    estado["selecionadas"] = limpos
    return _salvar_estado_cvm(estado)


def avaliar_decision_intelligence(
    resumo_negocio: dict[str, Any] | None,
    estado_cvm: dict[str, Any],
    cfg: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Compara o negócio com as bases CVM selecionadas (priorizando a mais recente) com precisão matemática."""
    cfg_efetivo = cfg or {"moeda": "BRL", "idioma": "Português"}
    if not estado_cvm.get("ativa"):
        return {
            "ativa": False,
            "sem_bases": False,
            "bases_usadas": [],
            "base_principal": None,
            "semaforo": None,
            "orientacoes": [],
            "markdown": "",
        }

    sel = set(estado_cvm.get("selecionadas") or [])
    bases_sel = [b for b in estado_cvm.get("bases", []) if b.get("id") in sel]
    bases_ord = ordenar_bases_recentes(bases_sel)

    if not bases_ord:
        return {
            "ativa": True,
            "sem_bases": True,
            "bases_usadas": [],
            "base_principal": None,
            "semaforo": {
                "nivel": "neutro",
                "tipo_alerta": "warning",
                "titulo": "Nenhuma base CVM selecionada para comparação",
                "resumo": "Marque pelo menos uma base CVM no filtro de seleção para gerar comparações e orientações.",
                "recomendacao": "Selecione uma ou mais bases CVM acima ou adicione um novo arquivo em Dados Externos.",
                "delta_rel_pct": None,
                "ganho_potencial": None,
            },
            "orientacoes": [],
            "markdown": "",
        }

    principal = bases_ord[0]
    res = principal.get("resumo") or {}
    nome_base = principal.get("nome") or principal.get("arquivo_padrao") or "CVM"
    ano_ref = int(principal.get("ano_referencia") or res.get("ano_referencia") or 0)
    ano_ant = int(principal.get("ano_anterior") or res.get("ano_anterior") or (ano_ref - 1 if ano_ref else 0))

    neg = resumo_negocio or {}
    rec = float(neg.get("receita_bruta") or 0.0)
    gasto = float(neg.get("gasto_total") or 0.0)
    margem_usu = float(neg.get("margem_pct") or 0.0)

    margem_cvm = res.get("margem_liquida_pct")
    custo_cvm = res.get("custo_sobre_receita_pct")
    var_cvm = res.get("variacao_receita_pct")
    n_cias = int(res.get("companhias_analisadas") or res.get("total_companhias") or 0)

    orientacoes: list[dict[str, str]] = []
    delta_rel: float | None = None
    ganho_potencial: float | None = None

    if rec > 0 and margem_cvm is not None and abs(float(margem_cvm)) > 1e-9:
        ref_m = float(margem_cvm)
        delta_rel = ((margem_usu - ref_m) / abs(ref_m)) * 100.0
        if delta_rel > 5.0:
            semaforo = {
                "nivel": "verde",
                "tipo_alerta": "success",
                "titulo": f"Vantagem competitiva frente à base '{nome_base}'",
                "resumo": (
                    f"Sua margem de rendimento ({_fmt_pct(margem_usu)}) está {_fmt_pct(delta_rel)} acima "
                    f"em relação ao setor na base '{nome_base}' (referência mediana: {_fmt_pct(ref_m)})."
                ),
                "recomendacao": (
                    "Orientação: manter o controle de gastos atual e avaliar ampliação de volume com segurança de margem."
                ),
                "delta_rel_pct": round(delta_rel, 2),
                "ganho_potencial": 0.0,
            }
        elif delta_rel >= -5.0:
            semaforo = {
                "nivel": "amarelo",
                "tipo_alerta": "warning",
                "titulo": f"Equilíbrio com a referência '{nome_base}'",
                "resumo": (
                    f"Sua margem de rendimento ({_fmt_pct(margem_usu)}) está alinhada "
                    f"({_fmt_pct(delta_rel, com_sinal=True)}) com a mediana da base '{nome_base}' ({_fmt_pct(ref_m)})."
                ),
                "recomendacao": (
                    "Orientação: acompanhar despesas operacionais recorrentes para evitar recuo abaixo da referência."
                ),
                "delta_rel_pct": round(delta_rel, 2),
                "ganho_potencial": 0.0,
            }
        else:
            queda = abs(delta_rel)
            ganho_potencial = max(0.0, ((ref_m - margem_usu) / 100.0) * rec)
            semaforo = {
                "nivel": "vermelho",
                "tipo_alerta": "error",
                "titulo": f"Alerta de defasagem frente ao setor ('{nome_base}')",
                "resumo": (
                    f"Sua margem de rendimento ({_fmt_pct(margem_usu)}) está {_fmt_pct(queda)} abaixo "
                    f"em relação ao setor na base '{nome_base}' (referência mediana: {_fmt_pct(ref_m)}). "
                    f"Impacto estimado: equiparar a margem representaria +{bk.moeda(ganho_potencial, cfg_efetivo)} "
                    "sobre a receita analisada."
                ),
                "recomendacao": (
                    "Orientação: revisar precificação ou renegociar os principais centros de custo e despesas."
                ),
                "delta_rel_pct": round(delta_rel, 2),
                "ganho_potencial": round(ganho_potencial, 2),
            }
        orientacoes.append({"tipo": semaforo["tipo_alerta"], "texto": semaforo["resumo"]})
        orientacoes.append({"tipo": "info", "texto": semaforo["recomendacao"]})
    elif rec > 0:
        semaforo = {
            "nivel": "neutro",
            "tipo_alerta": "info",
            "titulo": f"Referência ativa: {nome_base}",
            "resumo": (
                f"A base '{nome_base}' está ativa como referência, mas não possui margem líquida da DRE para cruzamento direto."
            ),
            "recomendacao": "Selecione uma base CVM com DRE completa ou acompanhe o cadastro de companhias.",
            "delta_rel_pct": None,
            "ganho_potencial": None,
        }
        orientacoes.append({"tipo": "info", "texto": semaforo["resumo"]})
    else:
        detalhe_ref = (
            f"A base mais recente ('{nome_base}', exercício {ano_ref}) registra margem líquida mediana de "
            f"{_fmt_pct(float(margem_cvm))}."
            if margem_cvm is not None
            else f"A base mais recente ('{nome_base}', exercício {ano_ref}) contém {n_cias} companhias."
        )
        semaforo = {
            "nivel": "neutro",
            "tipo_alerta": "info",
            "titulo": f"Comparação CVM habilitada — aguardando lançamentos do negócio",
            "resumo": (
                f"{detalhe_ref} Cadastre receitas e gastos operacionais para que o sistema calcule sua variação "
                "percentual exata (Δ%) frente ao mercado."
            ),
            "recomendacao": "Orientação: lance suas primeiras receitas e gastos para liberar o semáforo comparativo.",
            "delta_rel_pct": None,
            "ganho_potencial": None,
        }
        orientacoes.append({"tipo": "info", "texto": semaforo["resumo"]})

    # Diagnóstico preciso de comprometimento de custos/gastos
    if rec > 0 and custo_cvm is not None and abs(float(custo_cvm)) > 1e-9:
        custo_usu_pct = (gasto / rec) * 100.0
        ref_c = float(custo_cvm)
        delta_custo = ((custo_usu_pct - ref_c) / abs(ref_c)) * 100.0
        if delta_custo > 5.0:
            orientacoes.append(
                {
                    "tipo": "warning",
                    "texto": (
                        f"Pressão de gastos: suas despesas consomem {_fmt_pct(custo_usu_pct)} da receita, "
                        f"{_fmt_pct(delta_custo)} acima do custo/receita mediano da base '{nome_base}' "
                        f"({_fmt_pct(ref_c)})."
                    ),
                }
            )
        elif delta_custo < -5.0:
            orientacoes.append(
                {
                    "tipo": "success",
                    "texto": (
                        f"Eficiência de custos: seus gastos consomem {_fmt_pct(custo_usu_pct)} da receita, "
                        f"{_fmt_pct(abs(delta_custo))} abaixo do custo/receita mediano da base '{nome_base}' "
                        f"({_fmt_pct(ref_c)})."
                    ),
                }
            )
        else:
            orientacoes.append(
                {
                    "tipo": "info",
                    "texto": (
                        f"Estrutura de custos alinhada: seus gastos consomem {_fmt_pct(custo_usu_pct)} da receita "
                        f"frente a {_fmt_pct(ref_c)} na base '{nome_base}'."
                    ),
                }
            )

    # Tendência exata observada na base CVM mais recente
    if var_cvm is not None and ano_ref:
        v_cvm = float(var_cvm)
        direcao = "crescimento" if v_cvm >= 0 else "retração"
        orientacoes.append(
            {
                "tipo": "info",
                "texto": (
                    f"Tendência observada na base mais recente ('{nome_base}', exercício {ano_ant}→{ano_ref}): "
                    f"{direcao} mediano de {_fmt_pct(abs(v_cvm))} na receita das {n_cias} companhias analisadas."
                ),
            }
        )

    # Preferência explícita pela base mais recente quando há múltiplas selecionadas
    if len(bases_ord) > 1:
        outras = ", ".join(str(b.get("nome") or b.get("arquivo_padrao")) for b in bases_ord[1:])
        orientacoes.append(
            {
                "tipo": "info",
                "texto": (
                    f"Prioridade temporal ativa: orientações principais guiadas pela base mais recente "
                    f"('{nome_base}', exercício {ano_ref}); também em comparação: {outras}."
                ),
            }
        )

    linhas_md = [
        "## Comparação de Mercado (CVM) & Decision Intelligence",
        f"- Base de referência principal (mais recente): **{nome_base}** (exercício {ano_ref or 'n/d'})",
        f"- Bases selecionadas ({len(bases_ord)}): "
        + ", ".join(str(b.get("nome") or b.get("arquivo_padrao")) for b in bases_ord),
        f"- Diagnóstico: **{semaforo['titulo']}**",
    ]
    for item in orientacoes:
        linhas_md.append(f"- {item['texto']}")

    return {
        "ativa": True,
        "sem_bases": False,
        "bases_usadas": bases_ord,
        "base_principal": principal,
        "semaforo": semaforo,
        "orientacoes": orientacoes,
        "markdown": "\n".join(linhas_md) + "\n",
    }
