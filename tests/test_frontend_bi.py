"""Fluxos reais de BI e testes do BIDashboardWidget em PyQt6 isolado."""
from datetime import date
from io import BytesIO
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import pandas as pd
from pandas.testing import assert_frame_equal

os.environ["QT_QPA_PLATFORM"] = "offscreen"
from PyQt6.QtWidgets import QApplication
_qt_app = QApplication.instance() or QApplication(["-platform", "offscreen"])

from oneworld import database
from oneworld.frontend_bi import BIDashboardWidget

RAIZ = Path(__file__).resolve().parents[1]


class TestDashboard(unittest.TestCase):
    def setUp(self):
        self.temporario = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporario.cleanup)
        self.banco = patch.object(database, "DB_PATH", Path(self.temporario.name) / "teste.db")
        self.banco.start()
        self.addCleanup(self.banco.stop)
        self.widget = BIDashboardWidget()

    def verificar_sem_erros(self):
        self.assertIsNone(self.widget.erro_atual)

    def test_inicializacao_e_troca_dataset(self):
        self.verificar_sem_erros()
        # Primeiro dataset padrão em ordem alfabética: educacao (3 registros)
        self.assertEqual(self.widget.obter_kpi_resultados()[0].valor, 3)
        self.widget.selecionar_fonte("Exemplo: vendas")
        self.verificar_sem_erros()
        self.assertEqual(self.widget.obter_kpi_resultados()[0].valor, 4)
        self.widget.selecionar_fonte("Exemplo: estoque")
        self.verificar_sem_erros()
        self.assertEqual(self.widget.obter_kpi_resultados()[0].valor, 3)

    def test_kpi_grafico_e_filtro_atualizados(self):
        self.widget.configurar_kpi(0, operacao="media", coluna="nota")
        self.verificar_sem_erros()
        self.assertEqual(self.widget.obter_kpi_resultados()[0].valor, 8.0)

        self.widget.configurar_grafico(tipo="barras", grupo="turma", operacao="media", coluna="nota")
        self.widget.definir_filtro("turma", ativo=True, valores=[])
        self.verificar_sem_erros()
        # Seleção vazia: nenhum registro
        self.assertIsNone(self.widget.obter_kpi_resultados()[0].valor)

        self.widget.definir_filtro("turma", ativo=True, valores=["A"])
        self.verificar_sem_erros()
        self.assertEqual(self.widget.obter_kpi_resultados()[0].valor, 7.0)

        tabela_graf = self.widget.obter_tabela_grafico()
        self.assertEqual(tabela_graf["valor"].tolist(), [7.0])

        self.widget.limpar_filtros()
        self.verificar_sem_erros()
        self.assertEqual(self.widget.obter_kpi_resultados()[0].valor, 8.0)

    def test_datas_histograma_e_multiplos_kpis(self):
        self.widget.selecionar_fonte("Exemplo: vendas")
        self.widget.configurar_datas(["data"], formato="%Y-%m-%d")
        self.widget.configurar_grafico("linhas", grupo="data", operacao="soma", coluna="valor", periodo="dia")
        self.verificar_sem_erros()
        self.assertEqual(self.widget.obter_tabela_grafico()["valor"].sum(), 450)

        self.widget.definir_filtro("data", ativo=True, maximo="2026-10-02")
        self.verificar_sem_erros()
        # Vendas até 2026-10-02: 2 registros
        self.assertEqual(self.widget.obter_kpi_resultados()[0].valor, 2)

        self.widget.configurar_grafico("histograma", coluna="valor", intervalos=10)
        self.verificar_sem_erros()
        self.assertEqual(self.widget.obter_tabela_grafico()["frequencia"].sum(), 2)

        self.widget._ao_mudar_qtd_kpis(2)
        self.assertEqual(len(self.widget.obter_kpi_resultados()), 2)

        self.widget.selecionar_fonte("Exemplo: educacao")
        self.verificar_sem_erros()
        self.assertEqual(len(self.widget.obter_kpi_resultados()), 1)
        tipos_disponiveis = [self.widget.cb_graf_tipo.itemText(i) for i in range(self.widget.cb_graf_tipo.count())]
        self.assertNotIn("linhas", tipos_disponiveis)

    def test_histograma_preserva_ordem_numerica_no_eixo(self):
        self.widget.selecionar_fonte("Exemplo: estoque")
        self.widget.configurar_grafico("histograma", coluna="quantidade", intervalos=10)
        self.verificar_sem_erros()
        tabela = self.widget.obter_tabela_grafico()
        self.assertNotEqual(tabela["intervalo"].tolist(), sorted(tabela["intervalo"]))
        self.assertEqual(tabela["frequencia"].sum(), 3)

    def test_limites_invertidos_mostram_mensagem(self):
        self.widget.definir_filtro("nota", ativo=True, minimo=11.0, maximo=2.0)
        self.assertIsNotNone(self.widget.erro_atual)
        self.assertIn("invertidos", self.widget.erro_atual)

    def test_formato_data_invalido_e_recuperacao(self):
        self.widget.selecionar_fonte("Exemplo: vendas")
        self.widget.configurar_datas(["data"], formato="%Q")
        self.assertIsNotNone(self.widget.erro_atual)
        self.assertIn("formato", self.widget.erro_atual)
        self.widget.configurar_datas(["data"], formato="%Y-%m-%d")
        self.verificar_sem_erros()
        self.assertEqual(self.widget.obter_kpi_resultados()[0].valor, 4)

    def test_troca_descarta_todas_as_configuracoes_antigas(self):
        self.widget.selecionar_fonte("Exemplo: vendas")
        self.widget.configurar_datas(["data"], formato="%Y-%m-%d")
        self.widget.definir_filtro("produto", ativo=True, valores=[])
        self.widget._ao_mudar_qtd_kpis(3)
        self.widget.configurar_kpi(0, operacao="media", titulo="Título antigo", formato="Moeda")
        self.widget.configurar_grafico("linhas", grupo="data", periodo="mes")

        for nome in ("educacao", "estoque", "vendas"):
            self.widget.selecionar_fonte("Exemplo: " + nome)
            self.verificar_sem_erros()
            self.assertEqual(len(self.widget.obter_kpi_resultados()), 1)
            self.assertEqual(self.widget.kpi_cfgs[0]["titulo"], "KPI 1")
            self.assertEqual(self.widget.kpi_cfgs[0]["formato"], "Número")
            self.assertEqual(len(self.widget.filtros_ativos), 0)

    def test_filtros_combinados_exportacao_e_limpeza_sem_ia(self):
        with patch.dict(os.environ, {}, clear=True), patch(
            "oneworld.backend.responder_ia", side_effect=AssertionError("BI chamou IA")
        ) as ia:
            self.widget.selecionar_fonte("Exemplo: vendas")
            self.widget.configurar_datas(["data"], formato="%Y-%m-%d")
            self.widget.configurar_kpi(0, operacao="soma", coluna="valor")
            self.widget.definir_filtro("categoria", ativo=True, valores=["Papelaria"])
            self.widget.definir_filtro("valor", ativo=True, minimo=100)
            self.widget.definir_filtro("data", ativo=True, maximo="2026-10-02")

            for tipo in ("barras", "linhas", "histograma"):
                with self.subTest(tipo=tipo):
                    self.widget.configurar_grafico(
                        tipo,
                        grupo="data" if tipo == "linhas" else "produto",
                        operacao="soma",
                        coluna="valor",
                    )
                    self.verificar_sem_erros()
                    self.assertEqual(self.widget.obter_kpi_resultados()[0].valor, 100)
                    tabela = self.widget.obter_df_filtrado()
                    self.assertEqual(tabela["produto"].tolist(), ["Caneta"])
                    self.assertEqual(tabela["valor"].tolist(), [100])

                    arquivo_exportado = Path(self.temporario.name) / f"export_{tipo}.csv"
                    self.widget.exportar_csv(arquivo_exportado)
                    csv = pd.read_csv(arquivo_exportado, parse_dates=["data"])
                    assert_frame_equal(csv, tabela.reset_index(drop=True), check_dtype=False)

            self.widget.definir_filtro("produto", ativo=True, valores=[])
            self.verificar_sem_erros()
            self.assertIsNone(self.widget.obter_kpi_resultados()[0].valor)
            self.assertTrue(self.widget.obter_df_filtrado().empty)

            self.widget.limpar_filtros()
            self.verificar_sem_erros()
            self.assertEqual(self.widget.obter_kpi_resultados()[0].valor, 450)
            self.assertEqual(len(self.widget.obter_df_filtrado()), 4)
            ia.assert_not_called()

    def test_titulo_e_apresentacao_explicitos(self):
        self.widget.configurar_kpi(0, operacao="media", coluna="nota", titulo="Nota escolhida")
        self.assertEqual(self.widget.obter_kpi_resultados()[0].titulo, "Nota escolhida")
        self.assertEqual(self.widget.obter_kpi_resultados()[0].valor, 8.0)

        self.widget.configurar_kpi(0, operacao="media", coluna="nota", formato="Percentual")
        self.widget.configurar_kpi(0, operacao="media", coluna="nota", formato="Moeda", simbolo="US$")
        self.widget.configurar_kpi(0, operacao="media", coluna="nota", formato="Número")
        self.verificar_sem_erros()
        self.assertEqual(self.widget.obter_kpi_resultados()[0].valor, 8.0)


class TestUploads(unittest.TestCase):
    def setUp(self):
        self.widget = BIDashboardWidget()

    def test_arquivos_validos(self):
        df = pd.DataFrame({"rotulo": ["A", "B"], "medida": [2, 4]})
        excel = BytesIO()
        df.to_excel(excel, index=False)
        arquivos = [
            ("teste.csv", df.to_csv(index=False).encode()),
            ("teste.json", df.to_json(orient="records").encode()),
            ("teste.xlsx", excel.getvalue()),
        ]
        for nome, conteudo in arquivos:
            with self.subTest(nome=nome):
                ok = self.widget.adicionar_arquivo(conteudo, nome)
                self.assertTrue(ok)
                self.assertIsNone(self.widget.erro_atual)
                self.assertEqual(self.widget.obter_kpi_resultados()[0].valor, 2)

    def test_arquivos_invalidos(self):
        for nome, conteudo in [
            ("vazio.csv", b""),
            ("invalido.json", b"1"),
            ("invalido.xlsx", b"nao e um arquivo Excel"),
        ]:
            with self.subTest(nome=nome):
                ok = self.widget.adicionar_arquivo(conteudo, nome)
                self.assertFalse(ok)
                self.assertIsNotNone(self.widget.erro_atual)

    def test_filtro_de_inteiros_grandes(self):
        conteudo = f"rotulo,medida\nA,{2**62}\nB,{2**62 + 1}\n".encode()
        ok = self.widget.adicionar_arquivo(conteudo, "inteiros.csv")
        self.assertTrue(ok)
        self.widget.definir_filtro("medida", ativo=True, minimo=2**62 + 1)
        self.assertIsNone(self.widget.erro_atual)
        self.assertEqual(self.widget.obter_kpi_resultados()[0].valor, 1)


if __name__ == "__main__":
    unittest.main()
