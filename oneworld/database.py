"""Camada de banco de dados (SQLite). Não conhece Streamlit nem regras de tela."""
import json
import sqlite3
from datetime import datetime

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
    """Cria as tabelas (se não existirem) e insere os dados demonstrativos na primeira execução."""
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
        CREATE TABLE IF NOT EXISTS config(chave TEXT PRIMARY KEY, valor TEXT);
        """)
        if not con.execute("SELECT 1 FROM config WHERE chave='seed'").fetchone():
            con.executemany(
                "INSERT INTO eventos(data,cliente,local,convidados,valor,status) VALUES(?,?,?,?,?,?)",
                [("2026-10-10", "Cliente exemplo", "Espaço 01", 120, 15000.0, "Confirmado"),
                 ("2026-10-18", "Organização exemplo", "Espaço 02", 80, 9200.0, "Em planejamento"),
                 ("2026-10-25", "Cliente demonstrativo", "Espaço 03", 200, 24000.0, "Confirmado")])
            con.executemany(
                "INSERT INTO convidados(evento,nome,mesa,acompanhantes,contato,restricao,confirmacao)"
                " VALUES(?,?,?,?,?,?,?)",
                [("Cliente exemplo", "Pessoa exemplo", "01", 1, "contato@exemplo.com", "—", "Confirmado"),
                 ("Cliente exemplo", "Outro convidado", "01", 2, "(00) 00000-0000", "Vegetariana", "Pendente")])
            con.execute("INSERT INTO config VALUES('seed','1')")
        con.commit()
    finally:
        con.close()


# ── Configurações persistidas ──
def cfg_ler(chave, padrao):
    df = consulta("SELECT valor FROM config WHERE chave=?", (chave,))
    return json.loads(df.iloc[0, 0]) if not df.empty else padrao


def cfg_gravar(chave, valor):
    executar("INSERT INTO config(chave,valor) VALUES(?,?) "
             "ON CONFLICT(chave) DO UPDATE SET valor=excluded.valor",
             (chave, json.dumps(valor, ensure_ascii=False)))


# ── Eventos e convidados (CRUD genérico) ──
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
    con = sqlite3.connect(DB_PATH)
    try:
        con.executemany(sql, [[r.get(c) for c in cols] + [json.dumps(extras or {}, ensure_ascii=False)]
                              for r in registros])
        con.commit()
    finally:
        con.close()


def atualizar(tab, id_, dados, extras):
    cols = CAMPOS[tab]
    sql = f"UPDATE {tab} SET {','.join(c + '=?' for c in cols)}, extras=? WHERE id=?"
    executar(sql, [dados.get(c) for c in cols] + [json.dumps(extras, ensure_ascii=False), int(id_)])


def excluir(tab, id_):
    executar(f"DELETE FROM {tab} WHERE id=?", (int(id_),))


def renomear_evento_nos_convidados(novo, antigo):
    executar("UPDATE convidados SET evento=? WHERE evento=?", (novo, antigo))


def contar_convidados_do_evento(nome_evento):
    df = consulta("SELECT COUNT(*) AS n FROM convidados WHERE evento=?", (nome_evento,))
    return int(df.iloc[0, 0])


# ── Histórico de arquivos importados ──
def registrar_arquivo(arquivo, destino, registros, status, origem="Upload manual"):
    executar("INSERT INTO arquivos(arquivo,origem,recebido_em,destino,registros,status) VALUES(?,?,?,?,?,?)",
             (arquivo, origem, datetime.now().strftime("%d/%m/%Y %H:%M"), destino, registros, status))


def historico_arquivos():
    return consulta("SELECT arquivo AS Arquivo, origem AS Origem, recebido_em AS 'Recebido em', "
                    "destino AS Destino, registros AS Registros, status AS Status "
                    "FROM arquivos ORDER BY id DESC")


# ── Anotações ──
def listar_anotacoes():
    return consulta("SELECT * FROM anotacoes ORDER BY data, id")


def criar_anotacao(titulo, descricao, data_iso):
    executar("INSERT INTO anotacoes(titulo,descricao,data) VALUES(?,?,?)", (titulo, descricao, data_iso))


def excluir_anotacao(id_):
    executar("DELETE FROM anotacoes WHERE id=?", (int(id_),))


# ── Relatórios da Orientação IA ──
def salvar_relatorio(pergunta, resposta):
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
