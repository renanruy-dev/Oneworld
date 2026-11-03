"""Fluxos reais de rerun Streamlit com SQLite isolado em diretório temporário."""
from pathlib import Path
from io import BytesIO
import json
import os
import tempfile
import unittest
from unittest.mock import patch

import pandas as pd
from pandas.testing import assert_frame_equal
import streamlit as st

from streamlit.testing.v1 import AppTest

from oneworld import database

RAIZ = Path(__file__).resolve().parents[1]


def widget(app, tipo, base):
    """Localiza um controle da fonte ativa por seu nome funcional."""
    return next(w for w in getattr(app, tipo)
                if w.key and w.key.split("::")[0] == base)


class TestDashboard(unittest.TestCase):
    def setUp(self):
        self.temporario = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporario.cleanup)
        self.banco = patch.object(database, "DB_PATH", Path(self.temporario.name) / "teste.db")
        self.banco.start()
        self.addCleanup(self.banco.stop)
        self.app = AppTest.from_file(str(RAIZ / "app.py"), default_timeout=20).run()

    def verificar_sem_erros(self):
        self.assertFalse(self.app.exception, [e.message for e in self.app.exception])
        self.assertFalse(self.app.error, [e.value for e in self.app.error])

    def test_inicializacao_e_troca_dataset(self):
        self.verificar_sem_erros()
        self.assertEqual(self.app.metric[0].value, "3")
        widget(self.app, "selectbox", "bi_dataset").select("Exemplo: vendas").run()
        self.verificar_sem_erros()
        self.assertEqual(self.app.metric[0].value, "4")
        widget(self.app, "selectbox", "bi_dataset").select("Exemplo: estoque").run()
        self.verificar_sem_erros()
        self.assertEqual(self.app.metric[0].value, "3")

    def test_kpi_grafico_e_filtro_atualizados(self):
        widget(self.app, "selectbox", "bi_cfg_kpi_0_op").select("media").run()
        self.verificar_sem_erros()
        self.assertEqual(self.app.metric[0].value, "8.00")
        widget(self.app, "selectbox", "bi_cfg_agregacao").select("media").run()
        widget(self.app, "selectbox", "bi_cfg_grupo_barras").select("turma").run()
        widget(self.app, "checkbox", "bi_cfg_filtro_1").check().run()
        widget(self.app, "multiselect", "bi_cfg_filtro_1_valores").set_value([]).run()
        self.verificar_sem_erros()
        self.assertEqual(self.app.metric[0].value, "—")
        widget(self.app, "multiselect", "bi_cfg_filtro_1_valores").set_value(["A"]).run()
        self.verificar_sem_erros()
        self.assertEqual(self.app.metric[0].value, "7.00")
        grafico = self.app.dataframe[1].value
        self.assertEqual(grafico["valor"].tolist(), [7])
        identidade_filtro = widget(self.app, "checkbox", "bi_cfg_filtro_1").key
        widget(self.app, "button", "bi_limpar").click().run()
        self.verificar_sem_erros()
        self.assertNotEqual(widget(self.app, "checkbox", "bi_cfg_filtro_1").key, identidade_filtro)
        self.assertFalse(widget(self.app, "checkbox", "bi_cfg_filtro_1").value)
        self.assertEqual(self.app.metric[0].value, "8.00")

    def test_datas_histograma_e_multiplos_kpis(self):
        widget(self.app, "selectbox", "bi_dataset").select("Exemplo: vendas").run()
        widget(self.app, "multiselect", "bi_cfg_datas").set_value(["data"]).run()
        widget(self.app, "selectbox", "bi_cfg_grafico").select("linhas").run()
        self.verificar_sem_erros()
        self.assertEqual(self.app.dataframe[1].value["valor"].sum(), 4)
        widget(self.app, "checkbox", "bi_cfg_filtro_3").check().run()
        from datetime import date
        widget(self.app, "date_input", "bi_cfg_filtro_3_max").set_value(date(2026, 10, 2)).run()
        self.verificar_sem_erros()
        self.assertEqual(self.app.metric[0].value, "2")
        widget(self.app, "selectbox", "bi_cfg_grafico").select("histograma").run()
        self.verificar_sem_erros()
        self.assertEqual(self.app.dataframe[1].value["frequencia"].sum(), 2)
        widget(self.app, "number_input", "bi_cfg_n_kpis").set_value(2).run()
        self.assertEqual(len(self.app.metric), 2)
        widget(self.app, "selectbox", "bi_dataset").select("Exemplo: educacao").run()
        self.verificar_sem_erros()
        self.assertEqual(len(self.app.metric), 1)
        self.assertNotIn("linhas", widget(self.app, "selectbox", "bi_cfg_grafico").options)

    def test_histograma_preserva_ordem_numerica_no_eixo(self):
        widget(self.app, "selectbox", "bi_dataset").select("Exemplo: estoque").run()
        widget(self.app, "selectbox", "bi_cfg_grafico").select("histograma").run()
        self.verificar_sem_erros()
        tabela = self.app.dataframe[1].value
        self.assertNotEqual(tabela["intervalo"].tolist(), sorted(tabela["intervalo"]))
        especificacao = json.loads(self.app.get("vega_lite_chart")[0].proto.spec)
        self.assertIn("sort", especificacao["encoding"]["x"])
        self.assertIsNone(especificacao["encoding"]["x"]["sort"])
        self.assertEqual(tabela["frequencia"].sum(), 3)

    def test_limites_invertidos_mostram_mensagem(self):
        widget(self.app, "checkbox", "bi_cfg_filtro_2").check().run()
        widget(self.app, "number_input", "bi_cfg_filtro_2_min").set_value(11.0).run()
        self.assertFalse(self.app.exception)
        self.assertTrue(self.app.error)
        self.assertIn("invertidos", self.app.error[0].value)

    def test_formato_data_invalido_e_recuperacao(self):
        widget(self.app, "selectbox", "bi_dataset").select("Exemplo: vendas").run()
        widget(self.app, "multiselect", "bi_cfg_datas").set_value(["data"]).run()
        widget(self.app, "text_input", "bi_cfg_formato_data").set_value("%Q").run()
        self.assertFalse(self.app.exception)
        self.assertTrue(self.app.error)
        self.assertIn("formato", self.app.error[0].value)
        widget(self.app, "text_input", "bi_cfg_formato_data").set_value("%Y-%m-%d").run()
        self.verificar_sem_erros()
        self.assertEqual(self.app.metric[0].value, "4")

    def test_troca_descarta_todas_as_configuracoes_antigas(self):
        widget(self.app, "selectbox", "bi_dataset").select("Exemplo: vendas").run()
        widget(self.app, "multiselect", "bi_cfg_datas").set_value(["data"]).run()
        widget(self.app, "checkbox", "bi_cfg_filtro_1").check().run()
        widget(self.app, "multiselect", "bi_cfg_filtro_1_valores").set_value([]).run()
        widget(self.app, "number_input", "bi_cfg_n_kpis").set_value(6).run()
        widget(self.app, "text_input", "bi_cfg_kpi_0_titulo").set_value("Título antigo").run()
        widget(self.app, "selectbox", "bi_cfg_kpi_0_fmt").select("Moeda").run()
        widget(self.app, "selectbox", "bi_cfg_grafico").select("linhas").run()
        widget(self.app, "selectbox", "bi_cfg_periodo").select("mes").run()
        identidade = widget(self.app, "selectbox", "bi_cfg_grafico").key
        for nome, grupos in (("educacao", ["aluno", "turma"]),
                             ("estoque", ["produto", "categoria"]),
                             ("vendas", ["produto", "categoria", "data"])):
            widget(self.app, "selectbox", "bi_dataset").select("Exemplo: " + nome).run()
            self.verificar_sem_erros()
            self.assertEqual(len(self.app.metric), 1)
            self.assertEqual(self.app.metric[0].label, "KPI 1")
            self.assertEqual(widget(self.app, "selectbox", "bi_cfg_kpi_0_fmt").value, "Número")
            self.assertEqual(widget(self.app, "multiselect", "bi_cfg_datas").value, [])
            self.assertFalse(any(w.value for w in self.app.checkbox
                                 if w.key.startswith("bi_cfg_filtro_")))
            self.assertEqual(widget(self.app, "selectbox", "bi_cfg_grupo_barras").options, grupos)
            self.assertNotEqual(widget(self.app, "selectbox", "bi_cfg_grafico").key, identidade)
            identidade = widget(self.app, "selectbox", "bi_cfg_grafico").key
            self.assertNotIn("linhas", widget(self.app, "selectbox", "bi_cfg_grafico").options)

    def test_filtros_combinados_exportacao_e_limpeza_sem_ia(self):
        # Risco de integração: CSV pode divergir da tabela mesmo com KPIs corretos.
        # Captura os bytes enviados ao botão real; AppTest não clica downloads.
        from datetime import date
        with patch.dict(os.environ, {}, clear=True), patch(
            "oneworld.backend.responder_ia", side_effect=AssertionError("BI chamou IA")
        ) as ia, patch("oneworld.frontend_bi.st.download_button", wraps=st.download_button) as download:
            widget(self.app, "selectbox", "bi_dataset").select("Exemplo: vendas").run()
            widget(self.app, "multiselect", "bi_cfg_datas").set_value(["data"]).run()
            widget(self.app, "selectbox", "bi_cfg_kpi_0_op").select("soma").run()
            widget(self.app, "selectbox", "bi_cfg_grupo_barras").select("categoria").run()
            widget(self.app, "selectbox", "bi_cfg_agregacao").select("soma").run()
            widget(self.app, "checkbox", "bi_cfg_filtro_1").check().run()
            widget(self.app, "multiselect", "bi_cfg_filtro_1_valores").set_value(["Papelaria"]).run()
            widget(self.app, "checkbox", "bi_cfg_filtro_2").check().run()
            widget(self.app, "number_input", "bi_cfg_filtro_2_min").set_value(100).run()
            widget(self.app, "checkbox", "bi_cfg_filtro_3").check().run()
            widget(self.app, "date_input", "bi_cfg_filtro_3_max").set_value(date(2026, 10, 2)).run()
            for tipo in ("barras", "linhas", "histograma"):
                with self.subTest(tipo=tipo):
                    widget(self.app, "selectbox", "bi_cfg_grafico").select(tipo).run()
                    self.verificar_sem_erros()
                    self.assertEqual(self.app.metric[0].value, "100")
                    tabela = self.app.dataframe[-1].value
                    self.assertEqual(tabela["produto"].tolist(), ["Caneta"])
                    self.assertEqual(tabela["valor"].tolist(), [100])
                    grafico = self.app.dataframe[1].value
                    self.assertEqual(grafico.iloc[:, 1].sum(), 1 if tipo == "histograma" else 100)
                    csv = pd.read_csv(BytesIO(download.call_args.args[1]), parse_dates=["data"])
                    assert_frame_equal(csv, tabela.reset_index(drop=True), check_dtype=False)
            widget(self.app, "multiselect", "bi_cfg_filtro_1_valores").set_value([]).run()
            self.verificar_sem_erros()
            self.assertEqual(self.app.metric[0].value, "—")
            self.assertTrue(self.app.dataframe[-1].value.empty)
            csv = pd.read_csv(BytesIO(download.call_args.args[1]))
            self.assertTrue(csv.empty)
            self.assertEqual(csv.columns.tolist(), ["produto", "categoria", "valor", "data"])
            widget(self.app, "button", "bi_limpar").click().run()
            self.verificar_sem_erros()
            self.assertEqual(self.app.metric[0].value, "450")
            self.assertEqual(len(pd.read_csv(BytesIO(download.call_args.args[1]))), 4)
            self.assertFalse(any(w.value for w in self.app.checkbox if w.key.startswith("bi_cfg_filtro_")))
            ia.assert_not_called()

    def test_titulo_e_apresentacao_explicitos(self):
        widget(self.app, "selectbox", "bi_cfg_kpi_0_op").select("media").run()
        widget(self.app, "text_input", "bi_cfg_kpi_0_titulo").set_value("Nota escolhida").run()
        self.assertEqual(self.app.metric[0].label, "Nota escolhida")
        self.assertEqual(self.app.metric[0].value, "8.00")
        widget(self.app, "selectbox", "bi_cfg_kpi_0_fmt").select("Percentual").run()
        self.assertEqual(self.app.metric[0].value, "800.00%")
        widget(self.app, "selectbox", "bi_cfg_kpi_0_fmt").select("Moeda").run()
        widget(self.app, "text_input", "bi_cfg_kpi_0_simbolo").set_value("US$").run()
        self.assertEqual(self.app.metric[0].value, "US$ 8.00")
        widget(self.app, "selectbox", "bi_cfg_kpi_0_fmt").select("Número").run()
        self.verificar_sem_erros()
        self.assertEqual(self.app.metric[0].value, "8.00")


class TestUploads(unittest.TestCase):
    def carregar_upload(self, nome, conteudo):
        # AppTest não fornece API de upload. Injeta somente o arquivo, mantendo
        # seleção, leitura, tratamento de erros e renderização reais.
        script = f'''
from io import BytesIO
from unittest.mock import patch
from oneworld.frontend_bi import mostrar_dashboard
arquivo = BytesIO({conteudo!r})
arquivo.name = {nome!r}
with patch("oneworld.frontend_bi.st.file_uploader", return_value=[arquivo]):
    mostrar_dashboard("#5B4FC4")
'''
        app = AppTest.from_string(script, default_timeout=20).run()
        widget(app, "selectbox", "bi_dataset").select(widget(app, "selectbox", "bi_dataset").options[-1]).run()
        return app

    def test_arquivos_validos(self):
        df = pd.DataFrame({"rotulo": ["A", "B"], "medida": [2, 4]})
        excel = BytesIO()
        df.to_excel(excel, index=False)
        arquivos = [("teste.csv", df.to_csv(index=False).encode()),
                    ("teste.json", df.to_json(orient="records").encode()),
                    ("teste.xlsx", excel.getvalue())]
        for nome, conteudo in arquivos:
            with self.subTest(nome=nome):
                app = self.carregar_upload(nome, conteudo)
                self.assertFalse(app.exception)
                self.assertFalse(app.error)
                self.assertEqual(app.metric[0].value, "2")

    def test_arquivos_invalidos(self):
        for nome, conteudo in [("vazio.csv", b""), ("invalido.json", b"1"),
                               ("invalido.xlsx", b"nao e um arquivo Excel")]:
            with self.subTest(nome=nome):
                app = self.carregar_upload(nome, conteudo)
                self.assertFalse(app.exception)
                self.assertTrue(app.error)
                self.assertIn("ler o arquivo", app.error[0].value)

    def test_filtro_de_inteiros_grandes(self):
        conteudo = f"rotulo,medida\nA,{2**62}\nB,{2**62 + 1}\n".encode()
        app = self.carregar_upload("inteiros.csv", conteudo)
        widget(app, "checkbox", "bi_cfg_filtro_1").check().run()
        widget(app, "text_input", "bi_cfg_filtro_1_min").set_value(str(2**62 + 1)).run()
        self.assertFalse(app.exception)
        self.assertFalse(app.error)
        self.assertEqual(app.metric[0].value, "1")


if __name__ == "__main__":
    unittest.main()
