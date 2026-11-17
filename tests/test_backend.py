"""Testes unitários das regras de negócio do OneWorld (backend e config)."""
from datetime import date
import pandas as pd
from oneworld import backend as bk
from oneworld import config as cfg


def test_moeda_brl():
    config = {"moeda": "BRL", "idioma": "Português"}
    assert bk.moeda(15000.5, config) == "R$ 15.000,50"
    assert bk.moeda(0, config) == "R$ 0,00"
    assert bk.moeda("invalid", config) == "R$ 0,00"


def test_parse_date_and_fmt():
    assert bk.parse_date("2026-10-10") == date(2026, 10, 10)
    assert bk.parse_date("10/10/2026") == date(2026, 10, 10)
    assert bk.parse_date("") is None
    assert bk.fmt_data("2026-10-10") == "10/10/2026"


def test_parse_valor():
    assert bk.parse_valor("R$ 1.500,50") == 1500.50
    assert bk.parse_valor("25000.00") == 25000.00
    assert bk.parse_valor(120) == 120.0
    assert bk.parse_valor("") == 0.0


def test_norm_opcao():
    opcoes = ["Confirmado", "Pendente", "Recusou"]
    val, usou_padrao = bk.norm_opcao("sim", opcoes, "Pendente")
    assert val == "Confirmado"
    assert not usou_padrao

    val2, usou_padrao2 = bk.norm_opcao("desconhecido", opcoes, "Pendente")
    assert val2 == "Pendente"
    assert usou_padrao2


def test_obter_vocabulario_perfis():
    for perfil in cfg.PERFIS_NEGOCIO:
        v = cfg.obter_vocabulario({"perfil_negocio": perfil})
        assert "menu_ent1" in v
        assert "menu_ent2" in v
        assert "rotulos" in v
        assert "campos_destino" in v
        assert len(v["rotulos"]) >= 12


def test_sugerir_colunas():
    cols_eventos = ["Data da Operação", "Nome do Cliente", "Local", "Volume", "Valor Total", "Status"]
    sug = bk.sugerir(cols_eventos, "eventos")
    assert "data" in sug
    assert "cliente" in sug
    assert "valor" in sug


def test_validar_planilha():
    df = pd.DataFrame([
        {"data_col": "2026-11-01", "cli_col": "Empresa Alfa", "val_col": "5000", "status_col": "Confirmado"},
        {"data_col": "2026-11-05", "cli_col": "Empresa Beta", "val_col": "3200", "status_col": "Em planejamento"},
    ])
    mapa = {
        "data": "data_col",
        "cliente": "cli_col",
        "local": None,
        "convidados": None,
        "valor": "val_col",
        "status": "status_col",
    }
    existentes = pd.DataFrame(columns=["data", "cliente", "local", "convidados", "valor", "status"])
    res = bk.validar(df, "eventos", mapa, existentes)
    assert len(res["ok"]) == 2
    assert len(res["erros"]) == 0
    assert res["ok"][0]["cliente"] == "Empresa Alfa"
    assert res["ok"][0]["valor"] == 5000.0


def test_responder_ia():
    e = pd.DataFrame([
        {"id": 1, "data": "2026-11-01", "cliente": "Empresa Alfa", "local": "Matriz", "convidados": 50, "valor": 10000.0, "status": "Confirmado"}
    ])
    cv = pd.DataFrame([
        {"id": 1, "evento": "Empresa Alfa", "nome": "Item 1", "mesa": "01", "acompanhantes": 0, "contato": "", "restricao": "—", "confirmacao": "Confirmado"}
    ])
    config = cfg.PADROES
    resp = bk.responder_ia("Qual é o valor total?", e, cv, config)
    assert "R$" in resp
    assert "10.000,00" in resp


def test_gerar_markdown():
    e = pd.DataFrame([
        {"id": 1, "data": "2026-11-01", "cliente": "Empresa Alfa", "local": "Matriz", "convidados": 50, "valor": 10000.0, "status": "Confirmado"}
    ])
    cv = pd.DataFrame([
        {"id": 1, "evento": "Empresa Alfa", "nome": "Item 1", "mesa": "01", "acompanhantes": 0, "contato": "", "restricao": "—", "confirmacao": "Confirmado"}
    ])
    config = cfg.PADROES
    md = bk.gerar_markdown(e, cv, config)
    assert "# OneWorld" in md
    assert "Empresa Alfa" in md
