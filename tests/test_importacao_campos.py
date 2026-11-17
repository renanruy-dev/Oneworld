"""Importação real de campos personalizados, da planilha ao BI."""
import json
from datetime import datetime

import pandas as pd
import pytest
from PyQt6.QtWidgets import QApplication, QPushButton

from oneworld import backend, database, mapeamento
from oneworld.campos import converter_valor
from oneworld.frontend import ImportarPlanilhaWidget, OneWorldWindow, PaginatedTableWidget
from oneworld.frontend_bi import BIDashboardWidget


@pytest.mark.parametrize("extensao", ["csv", "xlsx", "json"])
def test_importacao_tipagem_previa_confirmacao_e_bi(tmp_path, monkeypatch, extensao):
    app = QApplication.instance() or QApplication([])
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "oneworld.db")
    database.init_db()
    database.cfg_gravar("config", {"pagina_inicial": "Configurações"})
    database.cfg_gravar("campos_personalizados", [
        {"nome": "Quantidade", "tipo": "inteiro", "tabelas": ["eventos"]},
        {"nome": "Peso", "tipo": "decimal", "tabelas": ["eventos"]},
        {"nome": "Vencimento", "tipo": "data", "tabelas": ["eventos"]},
        {"nome": "Entregue", "tipo": "booleano", "tabelas": ["eventos"]},
        {"nome": "Código", "tipo": "texto", "tabelas": ["eventos"]},
        {"nome": "Preferência", "tipo": "texto", "tabelas": ["convidados"]},
    ])
    dados = [
        {"data": "2026-11-17", "cliente": "A", "Quantidade": 12, "Peso": "12,55",
         "Vencimento": "17/11/2026", "Entregue": "sim", "Código": "00123"},
        {"data": "2026-11-17", "cliente": "B", "Quantidade": 3, "Peso": 3.125,
         "Vencimento": "2026-12-01", "Entregue": "não", "Código": "00456"},
        {"data": "2026-11-17", "cliente": "C", "Quantidade": None, "Peso": None,
         "Vencimento": None, "Entregue": None, "Código": None},
        {"data": "2026-11-17", "cliente": "D", "Quantidade": "doze", "Peso": "inválido",
         "Vencimento": "31/02/2026", "Entregue": "talvez", "Código": "00789"},
    ]
    caminho = tmp_path / f"dados.{extensao}"
    if extensao == "json":
        caminho.write_text(json.dumps(dados, ensure_ascii=False), encoding="utf-8")
    elif extensao == "xlsx":
        dados[0]["Vencimento"] = datetime(2026, 11, 17)
        pd.DataFrame(dados).to_excel(caminho, index=False)
    else:
        pd.DataFrame(dados).to_csv(caminho, index=False)

    janela = OneWorldWindow()
    janela.estado["teste_arq"] = caminho
    janela.estado["teste_df"] = mapeamento.ler_arquivo(caminho)
    widget = ImportarPlanilhaWidget(janela, destino_fixo="eventos", chave_estado="teste")
    try:
        assert "Preferência" not in widget._combos_mapa
        for nome in ("Quantidade", "Peso", "Vencimento", "Entregue", "Código"):
            assert widget._combos_mapa[nome].currentText() == nome

        erros = next(t._df for t in widget.findChildren(PaginatedTableWidget)
                     if "Motivo" in t._df)
        assert set(erros["Campo"]) == {"Quantidade", "Peso", "Vencimento", "Entregue"}
        assert erros["Linha no arquivo"].tolist() == [5, 5, 5, 5]
        previa = next(t._df for t in widget.findChildren(PaginatedTableWidget)
                      if "Quantidade" in t._df and len(t._df) == 3)
        assert previa["Quantidade"].tolist()[:2] == [12, 3]
        assert previa["Código"].tolist()[:2] == ["00123", "00456"]
        assert database.carregar("eventos").empty

        confirmar = next(b for b in widget.findChildren(QPushButton)
                         if b.text() == "Confirmar importação de 3 registro(s)")
        confirmar.click()
        salvo = database.carregar("eventos", ["Quantidade", "Código"])
        assert salvo["Quantidade"].tolist() == [12, 3, None]
        assert salvo["Código"].tolist() == ["00123", "00456", None]

        bi = BIDashboardWidget()
        bi._ao_alternar_banco_local(True)
        bi.selecionar_fonte("Banco local: eventos")
        bi.configurar_kpi(0, operacao="soma", coluna="Quantidade")
        assert bi.obter_kpi_resultados()[0].valor == 15
        bi.configurar_kpi(0, operacao="soma", coluna="Peso")
        assert bi.obter_kpi_resultados()[0].valor == pytest.approx(15.675)
        bi.configurar_kpi(0, operacao="media", coluna="Peso")
        assert bi.obter_kpi_resultados()[0].valor == pytest.approx(7.8375)
        controle = bi.filtro_widgets["Peso"]
        controle["min"].setText("12,55")
        controle["chk"].setChecked(True)
        assert bi.obter_df_filtrado()["cliente"].tolist() == ["A"]
        bi.limpar_filtros()
        bi.configurar_kpi(0, operacao="soma", coluna="Quantidade")
        bi.configurar_grafico("linhas", grupo="Vencimento", operacao="soma",
                              coluna="Quantidade", periodo="mes")
        assert bi.obter_tabela_grafico()["valor"].tolist() == [12, 3]
        bi.definir_filtro("Entregue", valores=[False])
        assert bi.obter_kpi_resultados()[0].valor == 3

        # Repetir o arquivo mantém o comportamento de ignorar duplicados.
        mapa = {nome: combo.currentText() for nome, combo in widget._combos_mapa.items()
                if combo.currentIndex() > 0}
        resultado = backend.validar(widget.df_lido, "eventos", mapa,
                                   janela.dados("eventos"), janela.campos_personalizados)
        assert resultado["duplicados"] == 3
        assert resultado["ok"] == []
        bi.close()
    finally:
        widget.close()
        janela.close()


def test_linhas_do_arquivo_apos_cabecalho_e_linhas_descartadas():
    df, _, _ = mapeamento._tabela([
        ["Relatório", None],
        ["data", "cliente", "Quantidade"],
        ["2026-11-17", "A", "12"],
        [None, None, None],
        ["Total", None, "12"],
        ["2026-11-17", "B", "doze"],
    ], "eventos")
    existentes = pd.DataFrame(columns=["data", "cliente"])
    campos = [{"nome": "Quantidade", "tipo": "inteiro", "tabelas": ["eventos"]}]
    res = backend.validar(df, "eventos",
                          {"data": "data", "cliente": "cliente", "Quantidade": "Quantidade"},
                          existentes, campos)
    assert len(res["ok"]) == 1
    assert res["erros"][0]["Linha no arquivo"] == 6


@pytest.mark.parametrize("valor,esperado", [(12.0, 12), (None, None), (float("nan"), None)])
def test_inteiro_lido_da_planilha(valor, esperado):
    assert converter_valor(valor, "inteiro") == esperado


@pytest.mark.parametrize("valor", [12.5, True, float("inf"), "12,5", "doze"])
def test_inteiro_rejeita_entrada_invalida(valor):
    with pytest.raises(ValueError):
        converter_valor(valor, "inteiro")


@pytest.mark.parametrize("valor,esperado", [
    ("12,55", 12.55), ("-0.125", -0.125), (0, 0.0), (3.125, 3.125),
    ("1e-7", 1e-7), (None, None), ("", None),
])
def test_decimal_aceita_formatos_e_nulos(valor, esperado):
    assert converter_valor(valor, "decimal") == esperado


@pytest.mark.parametrize("valor", [True, "doze", "1.234,56", "NaN", "inf", float("inf"), "1e999"])
def test_decimal_rejeita_valores_invalidos(valor):
    with pytest.raises(ValueError):
        converter_valor(valor, "decimal")
