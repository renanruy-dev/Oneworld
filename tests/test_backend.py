"""Testes unitários das regras de negócio do OneWorld (backend e config)."""
from datetime import date
import pandas as pd
import pytest
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


@pytest.mark.parametrize("texto, esperado", [
    ("1.500", 1500.0),             # ponto de milhar (padrão brasileiro)
    ("R$ 1.500", 1500.0),
    ("12.345", 12345.0),
    ("-1.500", -1500.0),
    ("1.500.000", 1500000.0),
    ("1.500,50", 1500.50),         # formato completo continua igual
    ("0.500", 0.5),                # zero à esquerda: decimal
    ("25000.00", 25000.0),         # duas casas: decimal
    ("1,5", 1.5),                  # vírgula: decimal
])
def test_parse_valor_ponto_de_milhar(texto, esperado):
    assert bk.parse_valor(texto) == esperado


@pytest.mark.parametrize("texto", ["abc", "R$", "-"])
def test_parse_valor_invalido_tem_mensagem_clara(texto):
    with pytest.raises(ValueError, match="número inválido"):
        bk.parse_valor(texto)


def test_validar_valor_invalido_gera_erro_legivel():
    df = pd.DataFrame([{"d": "2026-11-01", "c": "Alfa", "v": "abc"}])
    mapa = {"data": "d", "cliente": "c", "local": None, "convidados": None, "valor": "v", "status": None}
    existentes = pd.DataFrame(columns=["data", "cliente", "local", "convidados", "valor", "status"])
    res = bk.validar(df, "eventos", mapa, existentes)
    assert res["ok"] == []
    assert len(res["erros"]) == 1
    assert "número inválido" in res["erros"][0]["Motivo"]
    assert res["erros"][0]["Linha no arquivo"] == 2


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
    assert res["ok"][0]["valor"] == 5000.



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


def test_comparativo_receita_aumento_perda_e_estabilidade():
    # Mês recente 2026-11 = 15000 vs 2026-10 = 10000 (+50%), 2026-05 = 15000 (0%), 2025-11 = 20000 (-25%)
    e = pd.DataFrame([
        {"data": "2025-11-10", "cliente": "Ano Ant", "valor": 20000.0},
        {"data": "2026-05-12", "cliente": "Seis M", "valor": 15000.0},
        {"data": "2026-10-15", "cliente": "Mes Ant", "valor": 10000.0},
        {"data": "2026-11-15", "cliente": "Mes Atual", "valor": 15000.0},
    ])
    res = bk.comparativo_receita_empresa(e, cfg.PADROES, hoje=date(2026, 11, 18))
    assert res["ativo"] is True
    assert res["nivel"] == "verde"
    mapa = {c["chave"]: c for c in res["comparacoes"]}
    assert set(mapa.keys()) == {"mes", "30d", "6m", "ano"}

    assert mapa["mes"]["delta_pct"] == 50.0
    assert mapa["mes"]["delta_valor"] == 5000.0
    assert mapa["mes"]["nivel"] == "verde"

    assert mapa["6m"]["delta_pct"] == 0.0
    assert mapa["6m"]["nivel"] == "amarelo"

    assert mapa["ano"]["delta_pct"] == -25.0
    assert mapa["ano"]["delta_valor"] == -5000.0
    assert mapa["ano"]["nivel"] == "vermelho"

    assert mapa["30d"]["disponivel"] is True
    assert mapa["30d"]["rec_atual"] == 15000.0
    assert mapa["30d"]["rec_anterior"] == 10000.0


def test_comparativo_receita_respeita_config_e_alcance():
    e = pd.DataFrame([
        {"data": "2025-11-10", "cliente": "Ano Ant", "valor": 20000.0},
        {"data": "2026-05-12", "cliente": "Seis M", "valor": 12000.0},
        {"data": "2026-10-15", "cliente": "Mes Ant", "valor": 10000.0},
        {"data": "2026-11-15", "cliente": "Mes Atual", "valor": 8000.0},
    ])
    # Limita alcance a 3 meses -> bloqueia 6 meses e Ano passado
    c1 = {**cfg.PADROES, "rec_cmp_max_meses": 3}
    r1 = bk.comparativo_receita_empresa(e, c1, hoje=date(2026, 11, 18))
    chaves1 = [c["chave"] for c in r1["comparacoes"]]
    assert chaves1 == ["mes", "30d"]
    assert r1["nivel"] == "vermelho"
    assert r1["principal"]["delta_pct"] == -20.0

    # Alcance 12 meses, mas desabilitando ano passado e 30 dias
    c2 = {**cfg.PADROES, "rec_cmp_max_meses": 12, "rec_cmp_ano": False, "rec_cmp_30d": False}
    r2 = bk.comparativo_receita_empresa(e, c2, hoje=date(2026, 11, 18))
    assert [c["chave"] for c in r2["comparacoes"]] == ["mes", "6m"]

    # Comparativo totalmente desativado
    c3 = {**cfg.PADROES, "rec_cmp_ativo": False}
    r3 = bk.comparativo_receita_empresa(e, c3, hoje=date(2026, 11, 18))
    assert r3["ativo"] is False
    assert r3["comparacoes"] == []


def test_comparativo_receita_sem_historico_suficiente_e_base_zero():
    # Apenas 1 lançamento recente -> não inventa variação percentual para mês anterior
    e_curto = pd.DataFrame([{"data": "2026-11-10", "cliente": "Unico", "valor": 5000.0}])
    res = bk.comparativo_receita_empresa(e_curto, cfg.PADROES, hoje=date(2026, 11, 18))
    assert res["ativo"] is True
    assert all(not c["disponivel"] for c in res["comparacoes"])

    # Mês anterior com 0, mas existe histórico anterior (2026-09 teve receita)
    e_zero = pd.DataFrame([
        {"data": "2026-09-05", "cliente": "Antigo", "valor": 1000.0},
        {"data": "2026-11-10", "cliente": "Atual", "valor": 3000.0},
    ])
    res_z = bk.comparativo_receita_empresa(e_zero, cfg.PADROES, hoje=date(2026, 11, 18))
    mes_cmp = next(c for c in res_z["comparacoes"] if c["chave"] == "mes")
    assert mes_cmp["disponivel"] is True
    assert mes_cmp["delta_pct"] is None
    assert mes_cmp["delta_valor"] == 3000.0
    assert mes_cmp["nivel"] == "verde"
