"""Testes unitários da camada SQLite (database.py) do OneWorld."""
import sqlite3
from pathlib import Path
import pytest
from oneworld import database as db


@pytest.fixture(autouse=True)
def banco_temporario(tmp_path, monkeypatch):
    temp_db = tmp_path / "teste_oneworld.db"
    temp_bkp = tmp_path / "backups"
    monkeypatch.setattr(db, "DB_PATH", temp_db)
    monkeypatch.setattr(db, "BACKUP_DIR", temp_bkp)
    db.init_db()
    yield temp_db


def test_init_db_cria_tabelas(banco_temporario):
    con = sqlite3.connect(banco_temporario)
    tabelas = {t[0] for t in con.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
    con.close()
    assert {"eventos", "convidados", "arquivos", "anotacoes", "relatorios_ia", "config"}.issubset(tabelas)


def test_inserir_e_carregar_eventos():
    registros = [
        {"data": "2026-11-10", "cliente": "Cliente Teste", "local": "Sede", "convidados": 10, "valor": 1200.0, "status": "Confirmado"}
    ]
    db.inserir_lote("eventos", registros)
    df = db.carregar("eventos")
    assert len(df) == 1
    assert df.iloc[0]["cliente"] == "Cliente Teste"
    assert df.iloc[0]["valor"] == 1200.0


def test_atualizar_e_excluir_evento():
    db.inserir_lote("eventos", [{"data": "2026-11-10", "cliente": "Original", "local": "A", "convidados": 5, "valor": 500.0, "status": "Pendente"}])
    df = db.carregar("eventos")
    id_criado = int(df.iloc[0]["id"])

    # Atualiza
    db.atualizar("eventos", id_criado, {"data": "2026-11-10", "cliente": "Modificado", "local": "B", "convidados": 8, "valor": 800.0, "status": "Confirmado"}, {})
    df_mod = db.carregar("eventos")
    assert df_mod.iloc[0]["cliente"] == "Modificado"

    # Exclui
    db.excluir("eventos", id_criado)
    df_pos = db.carregar("eventos")
    assert len(df_pos) == 0


def test_anotacoes():
    db.criar_anotacao("Nota 1", "Detalhes da nota", "2026-11-10")
    notas = db.listar_anotacoes()
    assert len(notas) == 1
    assert notas.iloc[0]["titulo"] == "Nota 1"

    id_nota = int(notas.iloc[0]["id"])
    db.excluir_anotacao(id_nota)
    assert len(db.listar_anotacoes()) == 0


def test_config_persistida():
    db.cfg_gravar("teste_chave", {"ativo": True, "limite": 50})
    lido = db.cfg_ler("teste_chave", {})
    assert lido == {"ativo": True, "limite": 50}
