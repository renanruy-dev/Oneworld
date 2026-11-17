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

try:
    os.environ["QT_QPA_PLATFORM"] = "offscreen"
    from PyQt6.QtWidgets import QApplication
    _qt_app = QApplication.instance() or QApplication(["-platform", "offscreen"])
    from oneworld.frontend_bi import BIDashboardWidget
    TEM_PYQT6 = True
except (ImportError, OSError):
    TEM_PYQT6 = False
    BIDashboardWidget = None

from oneworld import database

RAIZ = Path(__file__).resolve().parents[1]


@unittest.skipUnless(TEM_PYQT6, "PyQt6 ou bibliotecas de display não disponíveis no ambiente")
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

    def test_campos_personalizados_do_banco_usam_tipo_e_escopo(self):
        database.init_db()
        database.cfg_gravar("campos_personalizados", [
            "Observação",
            {"nome": "Quantidade", "tipo": "inteiro", "tabelas": ["eventos"]},
            {"nome": "Vencimento", "tipo": "data", "tabelas": ["eventos"]},
            {"nome": "Entregue", "tipo": "booleano", "tabelas": ["eventos"]},
        ])
        for cliente, quantidade, vencimento, entregue in [
            ("A", 12, "2026-11-17", True),
            ("B", 3, "2026-12-01", False),
            ("C", None, None, None),
        ]:
            database.inserir_lote("eventos", [{"cliente": cliente}], {
                "Observação": "00123", "Quantidade": quantidade,
                "Vencimento": vencimento, "Entregue": entregue,
            })

        widget = self.widget
        widget._ao_alternar_banco_local(True)
        widget.selecionar_fonte("Banco local: eventos")
        self.verificar_sem_erros()
        self.assertNotIn("extras", widget.meta)
        self.assertNotIn("Observação", widget.filtro_widgets)
        self.assertEqual(widget.df_tipado["Observação"].tolist(), ["00123"] * 3)

        widget.configurar_kpi(0, operacao="soma", coluna="Quantidade")
        self.assertEqual(widget.obter_kpi_resultados()[0].valor, 15)
        widget.configurar_grafico("linhas", grupo="Vencimento", operacao="soma",
                                  coluna="Quantidade", periodo="mes")
        self.assertEqual(widget.obter_tabela_grafico()["valor"].tolist(), [12, 3])

        controle = widget.filtro_widgets["Entregue"]
        controle["chk"].setChecked(True)
        controle["combo"].setCurrentText("Não")
        self.assertEqual(widget.obter_kpi_resultados()[0].valor, 3)
        self.assertEqual(widget.obter_df_filtrado()["cliente"].tolist(), ["B"])

        widget.selecionar_fonte("Banco local: convidados")
        self.assertIn("Observação", widget.meta)
        self.assertNotIn("Quantidade", widget.meta)

    def test_inicializacao_e_troca_dataset(self):
        self.verificar_sem_erros()
        self.assertEqual(self.widget.lbl_perfil.text(), "Educação")
        self.assertEqual([k.valor for k in self.widget.obter_kpi_resultados()], [3, 8, 2])
        self.widget.selecionar_fonte("Exemplo: vendas")
        self.verificar_sem_erros()
        self.assertEqual(self.widget.lbl_perfil.text(), "Vendas")
        self.assertEqual([k.valor for k in self.widget.obter_kpi_resultados()], [450, 112.5, 3])
        self.widget.selecionar_fonte("Exemplo: estoque")
        self.verificar_sem_erros()
        self.assertEqual(self.widget.lbl_perfil.text(), "Estoque")
        self.assertEqual([k.valor for k in self.widget.obter_kpi_resultados()], [47, 3, 2])

    def test_atalhos_alteram_grafico_escolar_por_ano(self):
        base = b"ano,alunos,professores,turma\n2025,12,3,A\n2024,15,2,B\n2025,19,1,B\n"
        self.assertTrue(self.widget.adicionar_arquivo(base, "escola.csv"))
        self.assertEqual(self.widget.lbl_titulo_grafico.text(), "Alunos por ano")
        tabela = self.widget.obter_tabela_grafico()
        self.assertEqual(tabela["grupo"].tolist(), [2024, 2025])
        self.assertEqual(tabela["valor"].tolist(), [15, 31])

        professores = next(b for b in self.widget.grupo_medida.buttons() if b.text() == "Professores")
        professores.click()
        self.assertTrue(professores.isChecked())
        self.assertEqual(self.widget.obter_tabela_grafico()["valor"].tolist(), [2, 4])
        self.widget.botoes_tipo["linhas"].click()
        self.assertTrue(self.widget.botoes_tipo["linhas"].isChecked())
        self.assertEqual(self.widget.obter_tabela_grafico()["valor"].tolist(), [2, 4])

        self.widget.botoes_tipo["histograma"].click()
        self.widget.cb_graf_medida.setCurrentText("alunos")
        self.assertEqual(self.widget.obter_tabela_grafico()["frequencia"].sum(), 3)
        self.widget.botoes_tipo["barras"].click()
        self.assertEqual(self.widget.lbl_titulo_grafico.text(), "Professores por ano")
        self.widget.cb_graf_grupo.setCurrentText("turma")
        self.assertEqual(self.widget.obter_tabela_grafico()["valor"].tolist(), [3, 3])

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
        self.assertEqual(self.widget.obter_kpi_resultados()[0].valor, 300)

        self.widget.configurar_grafico("histograma", coluna="valor", intervalos=10)
        self.verificar_sem_erros()
        self.assertEqual(self.widget.obter_tabela_grafico()["frequencia"].sum(), 2)

        self.widget._ao_mudar_qtd_kpis(2)
        self.assertEqual(len(self.widget.obter_kpi_resultados()), 2)

        self.widget.selecionar_fonte("Exemplo: educacao")
        self.verificar_sem_erros()
        self.assertEqual(len(self.widget.obter_kpi_resultados()), 3)
        self.assertFalse(self.widget.botoes_tipo["linhas"].isEnabled())

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
        self.assertEqual(self.widget.obter_kpi_resultados()[0].valor, 450)

    def test_troca_descarta_todas_as_configuracoes_antigas(self):
        self.widget.selecionar_fonte("Exemplo: vendas")
        self.widget.configurar_datas(["data"], formato="%Y-%m-%d")
        self.widget.definir_filtro("produto", ativo=True, valores=[])
        self.widget._ao_mudar_qtd_kpis(3)
        self.widget.configurar_kpi(0, operacao="media", titulo="Título antigo", formato="Moeda")
        self.widget.configurar_grafico("linhas", grupo="data", periodo="mes")

        for nome, titulo, formato in (
            ("educacao", "Alunos distintos", "Número"),
            ("estoque", "Unidades em estoque", "Número"),
            ("vendas", "Valor das vendas", "Moeda"),
        ):
            self.widget.selecionar_fonte("Exemplo: " + nome)
            self.verificar_sem_erros()
            self.assertEqual(len(self.widget.obter_kpi_resultados()), 3)
            self.assertEqual(self.widget.kpi_cfgs[0]["titulo"], titulo)
            self.assertEqual(self.widget.kpi_cfgs[0]["formato"], formato)
            self.assertEqual(len(self.widget.filtros_ativos), 0)
            self.assertTrue(self.widget.botoes_tipo["barras"].isChecked())

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


@unittest.skipUnless(TEM_PYQT6, "PyQt6 ou bibliotecas de display não disponíveis no ambiente")
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
