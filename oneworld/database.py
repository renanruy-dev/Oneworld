"""Camada de banco de dados (SQLite). Não conhece UI nem regras de tela."""
import json
import sqlite3
from datetime import datetime
from typing import cast

import pandas as pd

from .config import BACKUP_DIR, CAMPOS, DB_PATH


# ── Acesso básico ──
def executar(sql, params=()):
    con = sqlite3.connect(DB_PATH)
    try:
        cur = con.execute(sql, params)
        con.commit()
        return cur.lastrowid
    finally:
        con.close()


def consulta(sql, params=()):
    con = sqlite3.connect(DB_PATH)
    try:
        return pd.read_sql_query(sql, con, params=params)
    finally:
        con.close()


def init_db():
    """Cria as tabelas do banco de dados (se não existirem)."""
    con = sqlite3.connect(DB_PATH)
    try:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS eventos(
            id INTEGER PRIMARY KEY AUTOINCREMENT, data TEXT, cliente TEXT, local TEXT,
            convidados INTEGER DEFAULT 0, valor REAL DEFAULT 0, status TEXT,
            extras TEXT DEFAULT '{}');
        CREATE TABLE IF NOT EXISTS convidados(
            id INTEGER PRIMARY KEY AUTOINCREMENT, evento TEXT, nome TEXT, mesa TEXT,
            acompanhantes INTEGER DEFAULT 0, contato TEXT, restricao TEXT,
            confirmacao TEXT, extras TEXT DEFAULT '{}');
        CREATE TABLE IF NOT EXISTS arquivos(
            id INTEGER PRIMARY KEY AUTOINCREMENT, arquivo TEXT, origem TEXT,
            recebido_em TEXT, destino TEXT, registros INTEGER, status TEXT);
        CREATE TABLE IF NOT EXISTS anotacoes(
            id INTEGER PRIMARY KEY AUTOINCREMENT, titulo TEXT, descricao TEXT, data TEXT);
        CREATE TABLE IF NOT EXISTS relatorios_ia(
            id INTEGER PRIMARY KEY AUTOINCREMENT, data TEXT, pergunta TEXT, resposta TEXT);
        CREATE TABLE IF NOT EXISTS dados_gerais(
            id INTEGER PRIMARY KEY AUTOINCREMENT, titulo TEXT, categoria TEXT,
            valor TEXT, data TEXT, descricao TEXT);
        CREATE TABLE IF NOT EXISTS config(chave TEXT PRIMARY KEY, valor TEXT);
        """)
        con.commit()
    finally:
        con.close()


# ── Configurações persistidas ──
def cfg_ler(chave, padrao):
    df = consulta("SELECT valor FROM config WHERE chave=?", (chave,))
    return json.loads(cast(str, df.iloc[0, 0])) if not df.empty else padrao


def cfg_gravar(chave, valor):
    executar("INSERT INTO config(chave,valor) VALUES(?,?) "
             "ON CONFLICT(chave) DO UPDATE SET valor=excluded.valor",
             (chave, json.dumps(valor, ensure_ascii=False)))


# ── Operações (eventos) e Cadastros (convidados) — CRUD genérico ──
def carregar(tab, campos_extras=()):
    """Lê uma tabela; campos personalizados (guardados em JSON) viram colunas."""
    ordem = "data, id" if tab == "eventos" else "id"
    df = consulta(f"SELECT * FROM {tab} ORDER BY {ordem}")
    ex = df.pop("extras").apply(lambda s: json.loads(s) if s else {})
    for campo in campos_extras:
        df[campo] = ex.apply(lambda d, c=campo: d.get(c, ""))
    return df


def inserir_lote(tab, registros, extras=None):
    cols = CAMPOS[tab]
    sql = (f"INSERT INTO {tab}({','.join(cols)},extras) "
           f"VALUES({','.join('?' * (len(cols) + 1))})")
    ex_json = json.dumps(extras or {}, ensure_ascii=False)
    linhas = [[r.get(c) for c in cols] + [ex_json] for r in registros]
    con = sqlite3.connect(DB_PATH)
    try:
        if len(linhas) == 1:
            cur = con.execute(sql, linhas[0])
            con.commit()
            return cur.lastrowid
        con.executemany(sql, linhas)
        con.commit()
        return None
    finally:
        con.close()


def atualizar(tab, id_, dados, extras):
    cols = CAMPOS[tab]
    sql = f"UPDATE {tab} SET {','.join(c + '=?' for c in cols)}, extras=? WHERE id=?"
    executar(sql, [dados.get(c) for c in cols] + [json.dumps(extras, ensure_ascii=False), int(id_)])


def excluir(tab, id_):
    executar(f"DELETE FROM {tab} WHERE id=?", (int(id_),))
    remover_meta_campo(tab, int(id_))


def excluir_lote(tab, ids):
    """Exclui vários registros de uma tabela em uma única transação."""
    lista = [(int(i),) for i in ids]
    if not lista:
        return 0
    con = sqlite3.connect(DB_PATH)
    try:
        cur = con.executemany(f"DELETE FROM {tab} WHERE id=?", lista)
        con.commit()
        removidos = cur.rowcount
    finally:
        con.close()
    _remover_metas_campos(tab, [i for (i,) in lista])
    return removidos


def renomear_evento_nos_convidados(novo, antigo):
    executar("UPDATE convidados SET evento=? WHERE evento=?", (novo, antigo))


def contar_convidados_do_evento(nome_evento):
    df = consulta("SELECT COUNT(*) AS n FROM convidados WHERE evento=?", (nome_evento,))
    return int(cast(int, df.iloc[0, 0]))


# ── Histórico de arquivos importados ──
def registrar_arquivo(arquivo, destino, registros, status, origem="Upload manual"):
    executar("INSERT INTO arquivos(arquivo,origem,recebido_em,destino,registros,status) VALUES(?,?,?,?,?,?)",
             (arquivo, origem, datetime.now().strftime("%d/%m/%Y %H:%M"), destino, registros, status))


def historico_arquivos():
    return consulta("SELECT arquivo AS Arquivo, origem AS Origem, recebido_em AS 'Recebido em', "
                    "destino AS Destino, registros AS Registros, status AS Status "
                    "FROM arquivos ORDER BY id DESC")


# ── Dados Gerais (alimentados livremente pelo usuário) ──
def carregar_dados_gerais() -> pd.DataFrame:
    return consulta("SELECT * FROM dados_gerais ORDER BY id")


def inserir_dado_geral(dados: dict) -> int | None:
    return executar(
        "INSERT INTO dados_gerais(titulo, categoria, valor, data, descricao) VALUES(?,?,?,?,?)",
        (
            dados.get("titulo", ""),
            dados.get("categoria", ""),
            dados.get("valor", ""),
            dados.get("data", ""),
            dados.get("descricao", ""),
        ),
    )


def atualizar_dado_geral(id_: int, dados: dict) -> None:
    executar(
        "UPDATE dados_gerais SET titulo=?, categoria=?, valor=?, data=?, descricao=? WHERE id=?",
        (
            dados.get("titulo", ""),
            dados.get("categoria", ""),
            dados.get("valor", ""),
            dados.get("data", ""),
            dados.get("descricao", ""),
            int(id_),
        ),
    )


def excluir_dado_geral(id_: int) -> None:
    executar("DELETE FROM dados_gerais WHERE id=?", (int(id_),))
    remover_meta_campo("dados_gerais", int(id_))


# ── Metadados de Campos para Dashboard e Lista de Lançamentos ──
CHAVE_CAMPOS_DASH = "campos_dashboard"
TIPOS_DASHBOARD = ("kpi", "grafico", "kpi_grafico", "lista", "nenhum")
TIPOS_VALOR_CAMPO = ("dinheiro", "numero", "texto")


def _meta_padrao_campo(origem: str) -> dict:
    if origem == "eventos":
        return {"tipo_dashboard": "kpi", "nome_info": "Receita lançada", "tipo_valor": "dinheiro", "itens": []}
    if origem == "convidados":
        return {"tipo_dashboard": "kpi", "nome_info": "Despesa lançada", "tipo_valor": "dinheiro", "itens": []}
    return {"tipo_dashboard": "kpi", "nome_info": "Valor", "tipo_valor": "numero", "itens": []}


def _normalizar_meta_campo(origem: str, meta: dict | None) -> dict:
    base = _meta_padrao_campo(origem)
    if not isinstance(meta, dict):
        return base
    td = str(meta.get("tipo_dashboard", "")).strip()
    if td in TIPOS_DASHBOARD:
        base["tipo_dashboard"] = td
    ni = str(meta.get("nome_info", "")).strip()
    if ni:
        base["nome_info"] = ni
    tv = str(meta.get("tipo_valor", "")).strip()
    if tv in TIPOS_VALOR_CAMPO:
        base["tipo_valor"] = tv
    itens_brutos = meta.get("itens", [])
    if isinstance(itens_brutos, list):
        itens = []
        for it in itens_brutos:
            if isinstance(it, dict):
                itens.append({
                    "rotulo": str(it.get("rotulo") or ""),
                    "valor": it.get("valor", ""),
                    "data": str(it.get("data") or ""),
                })
        base["itens"] = itens
    return base


def carregar_metas_campos() -> dict[str, dict]:
    """Carrega todos os metadados dos campos configurados para o Dashboard."""
    dados = cfg_ler(CHAVE_CAMPOS_DASH, {})
    return dados if isinstance(dados, dict) else {}


def obter_meta_campo(origem: str, id_: int) -> dict:
    """Retorna a configuração normalizada de um campo (dados_gerais, eventos ou convidados)."""
    metas = carregar_metas_campos()
    return _normalizar_meta_campo(origem, metas.get(f"{origem}:{int(id_)}"))


def salvar_meta_campo(origem: str, id_: int, meta: dict) -> dict:
    """Persiste tipo no Dashboard, categoria de informação, formato e itens do campo."""
    metas = carregar_metas_campos()
    chave = f"{origem}:{int(id_)}"
    existente = _normalizar_meta_campo(origem, metas.get(chave))
    combinado = dict(existente)
    combinado.update(meta or {})
    if "itens" not in (meta or {}):
        combinado["itens"] = existente["itens"]
    norm = _normalizar_meta_campo(origem, combinado)
    metas[chave] = norm
    cfg_gravar(CHAVE_CAMPOS_DASH, metas)
    return norm


def adicionar_item_campo(origem: str, id_: int, item: dict) -> dict:
    """Adiciona um novo lançamento à lista de dados de um campo e salva."""
    meta = obter_meta_campo(origem, int(id_))
    novo = {
        "rotulo": str(item.get("rotulo") or ""),
        "valor": item.get("valor", ""),
        "data": str(item.get("data") or ""),
    }
    meta["itens"].append(novo)
    return salvar_meta_campo(origem, int(id_), meta)


def remover_item_campo(origem: str, id_: int, indice: int) -> dict:
    """Remove um lançamento da lista de um campo pelo índice."""
    meta = obter_meta_campo(origem, int(id_))
    if 0 <= indice < len(meta["itens"]):
        meta["itens"].pop(indice)
    return salvar_meta_campo(origem, int(id_), meta)


def remover_meta_campo(origem: str, id_: int) -> None:
    """Remove os metadados de um campo excluído, se existirem."""
    _remover_metas_campos(origem, [id_])


def _remover_metas_campos(origem: str, ids) -> None:
    metas = carregar_metas_campos()
    alterou = False
    for id_ in ids:
        chave = f"{origem}:{int(id_)}"
        if chave in metas:
            del metas[chave]
            alterou = True
    if alterou:
        cfg_gravar(CHAVE_CAMPOS_DASH, metas)


def sincronizar_meta_com_valor_registro(
    origem: str,
    id_: int,
    valor_registro,
    data_registro: str,
    meta_form: dict | None = None,
) -> dict:
    """Mantém tipo_dashboard, tipo_valor e a lista de itens coerentes quando um registro é criado ou editado."""
    from . import backend as bk

    meta_atual = obter_meta_campo(origem, int(id_))
    meta_comb = _normalizar_meta_campo(origem, {**meta_atual, **(meta_form or {})})
    itens = list(meta_atual["itens"])
    tv = meta_comb["tipo_valor"]
    dt = str(data_registro or "")

    if tv in ("dinheiro", "numero"):
        bruto = "" if valor_registro is None else str(valor_registro).strip()
        val_num: float | None = None
        if bruto:
            try:
                val_num = float(bk.parse_valor(valor_registro))
            except ValueError:
                val_num = None
        if val_num is None or (val_num == 0.0 and origem in ("eventos", "convidados")):
            itens = []
        elif not itens:
            rot = "Valor inicial" if origem == "dados_gerais" else "Lançamento inicial"
            itens = [{"rotulo": rot, "valor": val_num, "data": dt}]
        elif len(itens) == 1:
            itens[0] = {**itens[0], "valor": val_num, "data": dt or itens[0].get("data", "")}
        else:
            soma_atual = 0.0
            for it in itens:
                try:
                    soma_atual += float(bk.parse_valor(it.get("valor")))
                except ValueError:
                    pass
            if abs(soma_atual - val_num) > 1e-6:
                itens = [{"rotulo": "Valor atualizado", "valor": val_num, "data": dt}]
    else:
        txt = str(valor_registro or "").strip()
        if not txt:
            itens = []
        elif not itens:
            itens = [{"rotulo": "Valor inicial", "valor": txt, "data": dt}]
        elif len(itens) == 1:
            itens[0] = {**itens[0], "valor": txt, "data": dt or itens[0].get("data", "")}
        else:
            ultimo = str(itens[-1].get("valor") or "").strip()
            resumo_esperado = f"{ultimo} ({len(itens)} itens)"
            if txt not in (ultimo, resumo_esperado):
                itens = [{"rotulo": "Valor atualizado", "valor": txt, "data": dt}]

    return salvar_meta_campo(origem, int(id_), {**meta_comb, "itens": itens})


# ── Anotações ──
def listar_anotacoes():
    return consulta("SELECT * FROM anotacoes ORDER BY data, id")


def criar_anotacao(titulo, descricao, data_iso):
    executar("INSERT INTO anotacoes(titulo,descricao,data) VALUES(?,?,?)", (titulo, descricao, data_iso))


def excluir_anotacao(id_):
    executar("DELETE FROM anotacoes WHERE id=?", (int(id_),))


# ── Relatórios da Orientação IA ──
def salvar_relatorio(pergunta, resposta):
    from . import ia  # IA externa (BYOK) se houver chave configurada; senão a resposta segue inalterada
    resposta = ia.resposta_com_llm(pergunta, resposta)
    executar("INSERT INTO relatorios_ia(data,pergunta,resposta) VALUES(?,?,?)",
             (datetime.now().strftime("%d/%m/%Y %H:%M"), pergunta, resposta))


def listar_relatorios(limite=10):
    return consulta("SELECT * FROM relatorios_ia ORDER BY id DESC LIMIT ?", (limite,))


# ── Backup manual ──
def fazer_backup():
    """Copia o banco para backups/ e devolve o caminho do arquivo gerado."""
    BACKUP_DIR.mkdir(exist_ok=True)
    dest = BACKUP_DIR / f"oneworld_backup_{datetime.now():%Y%m%d_%H%M%S}.db"
    src, dst = sqlite3.connect(DB_PATH), sqlite3.connect(dest)
    try:
        src.backup(dst)
    finally:
        dst.close()
        src.close()
    return dest


def contar_backups():
    return len(list(BACKUP_DIR.glob("*.db"))) if BACKUP_DIR.exists() else 0
