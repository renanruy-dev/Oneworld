"""Testes do gerenciamento multi-base CVM, persistência e Decision Intelligence."""
import os
import zipfile
from pathlib import Path

import pandas as pd
import pytest

from oneworld import backend as bk
from oneworld import config as app_cfg
from oneworld import cvm_comparacao as cvm_cmp
from oneworld import database as db

try:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PyQt6.QtWidgets import QApplication, QCheckBox, QLineEdit, QPushButton
    _qt_app = QApplication.instance() or QApplication(["-platform", "offscreen"])
    from oneworld import frontend
    TEM_PYQT6 = True
except (ImportError, OSError):
    TEM_PYQT6 = False


def _criar_zip_cvm(
    destino: Path,
    ano: int,
    receita_u: float,
    receita_p: float,
    custo_u: float,
    bruto_u: float,
    lucro_u: float,
    versao: int = 1,
) -> Path:
    """Gera um ZIP sintético no padrão oficial DFP da CVM para testes rápidos."""
    df_cia = pd.DataFrame(
        [
            {
                "CNPJ_CIA": "00.000.000/0001-91",
                "DT_REFER": f"{ano}-12-31",
                "VERSAO": str(versao),
                "DENOM_CIA": f"COMPANHIA EXEMPLO {ano} S.A.",
                "CD_CVM": "001023",
                "CATEG_DOC": "DFP",
            }
        ]
    )
    linhas_dre = []
    for cd, ds, val, ordem, dt_ini, dt_fim in (
        ("3.01", "Receita de Venda de Bens e/ou Serviços", receita_u, "ÚLTIMO", f"{ano}-01-01", f"{ano}-12-31"),
        ("3.01", "Receita de Venda de Bens e/ou Serviços", receita_p, "PENÚLTIMO", f"{ano - 1}-01-01", f"{ano - 1}-12-31"),
        ("3.02", "Custo dos Bens e/ou Serviços Vendidos", custo_u, "ÚLTIMO", f"{ano}-01-01", f"{ano}-12-31"),
        ("3.03", "Resultado Bruto", bruto_u, "ÚLTIMO", f"{ano}-01-01", f"{ano}-12-31"),
        ("3.11", "Lucro/Prejuízo Consolidado do Período", lucro_u, "ÚLTIMO", f"{ano}-01-01", f"{ano}-12-31"),
    ):
        linhas_dre.append(
            {
                "CNPJ_CIA": "00.000.000/0001-91",
                "DT_REFER": f"{ano}-12-31",
                "VERSAO": str(versao),
                "DENOM_CIA": f"COMPANHIA EXEMPLO {ano} S.A.",
                "CD_CVM": "001023",
                "GRUPO_DFP": "DF Consolidado - Demonstração do Resultado",
                "MOEDA": "REAL",
                "ESCALA_MOEDA": "MIL",
                "ORDEM_EXERC": ordem,
                "DT_INI_EXERC": dt_ini,
                "DT_FIM_EXERC": dt_fim,
                "CD_CONTA": cd,
                "DS_CONTA": ds,
                "VL_CONTA": str(val),
            }
        )
    df_dre = pd.DataFrame(linhas_dre)

    with zipfile.ZipFile(destino, "w") as zf:
        zf.writestr(f"dfp_cia_aberta_{ano}.csv", df_cia.to_csv(sep=";", index=False).encode("latin-1"))
        zf.writestr(f"dfp_cia_aberta_DRE_con_{ano}.csv", df_dre.to_csv(sep=";", index=False).encode("latin-1"))
    return destino


def _criar_csv_dre_cvm(destino: Path, ano: int, titulo: str, receita: float, custo: float, lucro: float) -> Path:
    df_dre = pd.DataFrame(
        [
            {
                "CNPJ_CIA": "11.111.111/0001-11",
                "DT_REFER": f"{ano}-12-31",
                "VERSAO": "1",
                "GRUPO_DFP": titulo,
                "ESCALA_MOEDA": "UNIDADE",
                "ORDEM_EXERC": "ÚLTIMO",
                "CD_CONTA": "3.01",
                "VL_CONTA": str(receita),
            },
            {
                "CNPJ_CIA": "11.111.111/0001-11",
                "DT_REFER": f"{ano}-12-31",
                "VERSAO": "1",
                "GRUPO_DFP": titulo,
                "ESCALA_MOEDA": "UNIDADE",
                "ORDEM_EXERC": "ÚLTIMO",
                "CD_CONTA": "3.02",
                "VL_CONTA": str(custo),
            },
            {
                "CNPJ_CIA": "11.111.111/0001-11",
                "DT_REFER": f"{ano}-12-31",
                "VERSAO": "1",
                "GRUPO_DFP": titulo,
                "ESCALA_MOEDA": "UNIDADE",
                "ORDEM_EXERC": "ÚLTIMO",
                "CD_CONTA": "3.11",
                "VL_CONTA": str(lucro),
            },
        ]
    )
    destino.write_bytes(df_dre.to_csv(sep=";", index=False).encode("latin-1"))
    return destino


@pytest.fixture
def ambiente_cvm(tmp_path, monkeypatch):
    raiz = tmp_path / "proj"
    raiz.mkdir()
    _criar_zip_cvm(raiz / "dfp_cia_aberta_2021.zip", 2021, 1000.0, 800.0, -600.0, 400.0, 100.0)
    monkeypatch.setattr(app_cfg, "RAIZ", raiz)
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "oneworld.db")
    monkeypatch.setattr(db, "BACKUP_DIR", tmp_path / "backups")
    if TEM_PYQT6:
        monkeypatch.setattr(frontend, "BACKUP_DIR", tmp_path / "backups")
    db.init_db()
    cvm_cmp._CACHE_RESUMO.clear()
    return raiz


def test_estado_padrao_desabilitado_sem_gravar_no_banco(ambiente_cvm):
    estado = cvm_cmp.carregar_estado_cvm()
    assert estado["ativa"] is False
    assert len(estado["bases"]) == 1
    assert estado["bases"][0]["nome"] == "DFP CVM 2021 (dfp_cia_aberta_2021.zip)"
    assert estado["bases"][0]["ano_referencia"] == 2021
    # Leitura inicial não deve escrever nada na tabela config
    assert db.cfg_ler(cvm_cmp.CHAVE_CONFIG, None) is None


def test_adicionar_multiplas_renomear_atualizar_e_excluir(ambiente_cvm, tmp_path):
    z22 = _criar_zip_cvm(tmp_path / "dfp_cia_aberta_2022.zip", 2022, 2000.0, 1600.0, -1000.0, 1000.0, 400.0)
    csv23 = _criar_csv_dre_cvm(
        tmp_path / "dre_varejo_2023.csv",
        2023,
        "DF Consolidado - Demonstração do Resultado",
        receita=1000.0,
        custo=-550.0,
        lucro=250.0,
    )

    adicionadas = cvm_cmp.adicionar_bases_cvm([z22, csv23])
    assert len(adicionadas) == 2
    assert adicionadas[0]["nome"] == "DFP CVM 2022 (dfp_cia_aberta_2022.zip)"
    assert "DF Consolidado - Demonstração do Resultado" in adicionadas[1]["nome"]

    # Renomeia e restaura padrão ao enviar string vazia
    id_22 = adicionadas[0]["id"]
    cvm_cmp.renomear_base_cvm(id_22, "Setor Alimentos 2022")
    estado = cvm_cmp.carregar_estado_cvm()
    assert next(b for b in estado["bases"] if b["id"] == id_22)["nome"] == "Setor Alimentos 2022"

    cvm_cmp.renomear_base_cvm(id_22, "   ")
    estado = cvm_cmp.carregar_estado_cvm()
    assert next(b for b in estado["bases"] if b["id"] == id_22)["nome"] == "DFP CVM 2022 (dfp_cia_aberta_2022.zip)"

    # Atualiza arquivo substituindo por outro (2024)
    z24 = _criar_zip_cvm(tmp_path / "dfp_cia_aberta_2024.zip", 2024, 5000.0, 4000.0, -3000.0, 2000.0, 1500.0)
    cvm_cmp.atualizar_arquivo_cvm(id_22, z24)
    estado = cvm_cmp.carregar_estado_cvm()
    b_upd = next(b for b in estado["bases"] if b["id"] == id_22)
    assert b_upd["ano_referencia"] == 2024
    assert b_upd["resumo"]["margem_liquida_pct"] == 30.0

    # Exclui a base padrão autodescoberta de 2021 e confirma que não retorna
    id_21 = next(b["id"] for b in estado["bases"] if b["ano_referencia"] == 2021)
    cvm_cmp.excluir_base_cvm(id_21)
    estado_pos = cvm_cmp.carregar_estado_cvm()
    assert all(b["id"] != id_21 for b in estado_pos["bases"])


def test_habilitar_comparacao_seleciona_todas_e_persiste(ambiente_cvm, tmp_path):
    z22 = _criar_zip_cvm(tmp_path / "dfp_cia_aberta_2022.zip", 2022, 2000.0, 1000.0, -1000.0, 1000.0, 400.0)
    cvm_cmp.adicionar_bases_cvm([z22])

    estado_ativo = cvm_cmp.definir_comparacao_ativa(True)
    assert estado_ativo["ativa"] is True
    assert len(estado_ativo["selecionadas"]) == 2

    # Filtra / seleciona apenas uma e recarrega (simulando reabertura)
    id_21 = next(b["id"] for b in estado_ativo["bases"] if b["ano_referencia"] == 2021)
    cvm_cmp.definir_bases_selecionadas([id_21])

    recarregado = cvm_cmp.carregar_estado_cvm()
    assert recarregado["ativa"] is True
    assert recarregado["selecionadas"] == [id_21]


def test_decision_intelligence_prioriza_mais_recente_e_precisao_matematica(ambiente_cvm, tmp_path):
    # Base 2021: margem líquida = 10%
    # Base 2023 (mais recente): margem líquida = 30.0%, custo/receita = 60.0%, var. receita = +25%
    z23 = _criar_zip_cvm(tmp_path / "dfp_cia_aberta_2023.zip", 2023, 1000.0, 800.0, -600.0, 400.0, 300.0)
    ad = cvm_cmp.adicionar_bases_cvm([z23])
    cvm_cmp.renomear_base_cvm(ad[0]["id"], "Mercado 2023")
    estado = cvm_cmp.definir_comparacao_ativa(True)

    # Caso vermelho: margem usuário = 25.02% vs CVM 30.0% -> exatamente -16.6% abaixo
    resumo_verm = {"receita_bruta": 10000.0, "gasto_total": 7498.0, "rendimento_liquido": 2502.0, "margem_pct": 25.02}
    di_v = cvm_cmp.avaliar_decision_intelligence(resumo_verm, estado)
    assert di_v["base_principal"]["nome"] == "Mercado 2023"
    assert di_v["semaforo"]["nivel"] == "vermelho"
    assert "16,6% abaixo" in di_v["semaforo"]["resumo"]
    assert "Mercado 2023" in di_v["semaforo"]["resumo"]
    assert di_v["semaforo"]["ganho_potencial"] == pytest.approx(498.0, abs=0.01)
    assert any("Prioridade temporal" in o["texto"] for o in di_v["orientacoes"])

    # Caso amarelo: margem usuário = 30.9% vs CVM 30.0% (+3.0%)
    resumo_am = {"receita_bruta": 10000.0, "gasto_total": 6910.0, "rendimento_liquido": 3090.0, "margem_pct": 30.9}
    di_a = cvm_cmp.avaliar_decision_intelligence(resumo_am, estado)
    assert di_a["semaforo"]["nivel"] == "amarelo"

    # Caso verde: margem usuário = 36.0% vs CVM 30.0% (+20.0%)
    resumo_vd = {"receita_bruta": 10000.0, "gasto_total": 6400.0, "rendimento_liquido": 3600.0, "margem_pct": 36.0}
    di_vd = cvm_cmp.avaliar_decision_intelligence(resumo_vd, estado)
    assert di_vd["semaforo"]["nivel"] == "verde"
    assert "20,0% acima" in di_vd["semaforo"]["resumo"]


@pytest.mark.skipif(not TEM_PYQT6, reason="PyQt6 indisponível")
def test_ui_dados_externos_e_dashboard_persistem_estado(ambiente_cvm, tmp_path, monkeypatch):
    z22 = _criar_zip_cvm(tmp_path / "dfp_cia_aberta_2022.zip", 2022, 1000.0, 800.0, -600.0, 400.0, 300.0)
    z23 = _criar_zip_cvm(tmp_path / "dfp_cia_aberta_2023.zip", 2023, 1200.0, 1000.0, -600.0, 600.0, 300.0)
    db.inserir_lote(
        "eventos",
        [{"data": "2026-11-10", "cliente": "Operação Teste", "local": "Sede", "convidados": 7498, "valor": 10000.0, "status": "Confirmado"}],
    )

    janela = frontend.OneWorldWindow()
    try:
        # 1. Dashboard inicia com comparação desabilitada
        assert hasattr(janela, "cvm_painel_negocio")
        assert not janela.cvm_painel_negocio.chk_habilitar.isChecked()
        assert janela.cvm_painel_negocio.corpo.isHidden()

        # 2. Vai para Dados Externos, adiciona z22 e z23 de uma vez, edita nome, filtra, atualiza e exclui
        janela.navegar_para("Dados Externos")
        ger = janela.cvm_gerenciador

        monkeypatch.setattr(
            frontend.QFileDialog,
            "getOpenFileNames",
            staticmethod(lambda *a, **k: ([str(z22), str(z23)], "")),
        )
        ger._ao_adicionar_arquivos()

        estado = cvm_cmp.carregar_estado_cvm()
        assert len(estado["bases"]) == 3

        # Filtro visual na tela Dados Externos
        ger.ed_filtro.setText("2023")
        visiveis = [card for card, _ in ger._cards_busca if not card.isHidden()]
        assert len(visiveis) == 1
        ger.ed_filtro.setText("")

        # Renomeia a base 2023 pela UI
        id_23 = next(b["id"] for b in estado["bases"] if b["ano_referencia"] == 2023)
        ger._ao_salvar_nome(id_23, "Mercado Consolidado 2023")
        assert next(b for b in cvm_cmp.carregar_estado_cvm()["bases"] if b["id"] == id_23)["nome"] == "Mercado Consolidado 2023"

        # Atualiza o arquivo da base 2022 substituindo por um arquivo de 2024
        id_22 = next(b["id"] for b in estado["bases"] if b["ano_referencia"] == 2022)
        z24 = _criar_zip_cvm(tmp_path / "dfp_cia_aberta_2024.zip", 2024, 1500.0, 1200.0, -700.0, 800.0, 450.0)
        monkeypatch.setattr(
            frontend.QFileDialog,
            "getOpenFileName",
            staticmethod(lambda *a, **k: (str(z24), "")),
        )
        ger._ao_atualizar_arquivo(id_22)
        assert next(b for b in cvm_cmp.carregar_estado_cvm()["bases"] if b["id"] == id_22)["ano_referencia"] == 2024

        # Exclui a base de 2021 pela UI
        id_21 = next(b["id"] for b in cvm_cmp.carregar_estado_cvm()["bases"] if b["ano_referencia"] == 2021)
        ger._ao_excluir(id_21, "DFP CVM 2021")
        assert len(cvm_cmp.carregar_estado_cvm()["bases"]) == 2

        # Habilita comparação em Dados Externos e volta ao Dashboard
        ger.chk_ativa.setChecked(True)
        janela.navegar_para("Dashboard")
        painel = janela.cvm_painel_negocio
        assert not painel.corpo.isHidden()
        assert painel.lay_di.count() > 0
        # Não deve exibir filtro nem lista de checkboxes de seleção de bases no Dashboard
        assert painel.findChildren(frontend.QCheckBox) == []
        assert painel.findChildren(frontend.QLineEdit) == []

        # Verifica geração do Markdown com bloco CVM ativo
        bloco = cvm_cmp.avaliar_decision_intelligence(
            bk.resumo_financeiro(janela.dados("eventos"), janela.dados("convidados")),
            cvm_cmp.carregar_estado_cvm(),
            janela.cfg,
        )["markdown"]
        md = bk.gerar_markdown(janela.dados("eventos"), janela.dados("convidados"), janela.cfg, bloco_cvm=bloco)
        assert "Mercado Consolidado 2023" in md
    finally:
        janela.close()
        janela.deleteLater()

    # Simula reabrir o programa: o estado habilitado, nomes e bases continuam persistidos
    janela2 = frontend.OneWorldWindow()
    try:
        assert janela2.cvm_painel_negocio.chk_habilitar.isChecked()
        assert not janela2.cvm_painel_negocio.corpo.isHidden()
        nomes = [b["nome"] for b in cvm_cmp.carregar_estado_cvm()["bases"]]
        assert "Mercado Consolidado 2023" in nomes
    finally:
        janela2.close()
        janela2.deleteLater()


def test_cvm_ativado_por_dados_externos_sem_campo_duplicado_no_dashboard(ambiente_cvm, tmp_path):
    z22 = _criar_zip_cvm(tmp_path / "dfp_cia_aberta_2022.zip", 2022, 2000.0, 1000.0, -1000.0, 1000.0, 400.0)
    cvm_cmp.adicionar_bases_cvm([z22])

    janela = frontend.OneWorldWindow()
    try:
        painel = janela.cvm_painel_negocio
        # O checkbox duplicado não é exibido no layout do Dashboard
        assert painel.chk_habilitar.isHidden()
        assert painel.isHidden()

        # Ativa na aba Dados Externos
        janela.navegar_para("Dados Externos")
        janela.cvm_gerenciador.chk_ativa.setChecked(True)

        # Volta ao Dashboard: já está ativo e visível automaticamente
        janela.navegar_para("Dashboard")
        painel = janela.cvm_painel_negocio
        assert not painel.isHidden()
        assert not painel.corpo.isHidden()
        assert painel.chk_habilitar.isChecked()
    finally:
        janela.close()
        janela.deleteLater()
