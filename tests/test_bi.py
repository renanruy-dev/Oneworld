"""Contratos do BI e regressões com dados de domínios diferentes."""
from pathlib import Path
import unittest

import pandas as pd
from pandas.testing import assert_frame_equal

from oneworld.analises import preparar_grafico
from oneworld.filtros import aplicar_filtros
from oneworld.indicadores import calcular_kpi
from oneworld.metadados import ErroBI, configurar_datas, inspecionar_colunas

RAIZ = Path(__file__).resolve().parents[1]


class TestKPIs(unittest.TestCase):
    def setUp(self):
        self.df = pd.DataFrame({"dimensao": ["A", "A", "B", None],
                                "medida": pd.Series([2, 4, None, 6], dtype="Float64")})

    def test_operacoes(self):
        for op, esperado in {"contagem": 4, "distintos": 2, "soma": 12,
                             "media": 4, "minimo": 2, "maximo": 6}.items():
            with self.subTest(op=op):
                coluna = "dimensao" if op == "distintos" else "medida"
                r = calcular_kpi(self.df, {"operacao": op, "coluna": coluna})
                self.assertIsNone(r.erro)
                self.assertEqual(r.valor, esperado)

    def test_configuracoes_invalidas(self):
        for cfg in ({"operacao": "desconhecida"}, {"operacao": "soma", "coluna": "ausente"},
                    {"operacao": "media", "coluna": "dimensao"}):
            with self.subTest(cfg=cfg):
                r = calcular_kpi(self.df, cfg)
                self.assertIsNone(r.valor)
                self.assertTrue(r.erro)

    def test_vazios_e_nulos(self):
        for df in (self.df.iloc[:0], self.df.assign(medida=float("nan"))):
            for op in ("soma", "media", "minimo", "maximo"):
                with self.subTest(op=op, tamanho=len(df)):
                    r = calcular_kpi(df, {"operacao": op, "coluna": "medida"})
                    self.assertIsNone(r.valor)
                    self.assertIsNone(r.erro)
                    self.assertTrue(r.mensagem)
        self.assertEqual(calcular_kpi(pd.DataFrame(), {"operacao": "contagem"}).valor, 0)
        self.assertEqual(calcular_kpi(self.df.iloc[:0], {"operacao": "distintos", "coluna": "dimensao"}).valor, 0)

    def test_sem_conversao_silenciosa(self):
        df = pd.DataFrame({"x": ["1", "2"]})
        self.assertTrue(calcular_kpi(df, {"operacao": "soma", "coluna": "x"}).erro)

    def test_infinitos_e_overflow(self):
        df = pd.DataFrame({"x": [1, float("inf"), float("-inf"), None]})
        self.assertEqual(calcular_kpi(df, {"operacao": "soma", "coluna": "x"}).valor, 1)
        df = pd.DataFrame({"x": [2**62, 2**62]})
        self.assertEqual(calcular_kpi(df, {"operacao": "soma", "coluna": "x"}).valor, 2**63)

    def test_booleanos_nao_sao_medidas(self):
        self.assertTrue(calcular_kpi(pd.DataFrame({"x": [True, False]}),
                                    {"operacao": "soma", "coluna": "x"}).erro)

    def test_complexos_nao_sao_medidas(self):
        self.assertTrue(calcular_kpi(pd.DataFrame({"x": [1 + 2j]}),
                                    {"operacao": "media", "coluna": "x"}).erro)


class TestMetadados(unittest.TestCase):
    def test_formato_data_invalido_retorna_erro_bi(self):
        df = pd.DataFrame({"data": ["2026-10-01"]})
        with self.assertRaisesRegex(ErroBI, "formato"):
            configurar_datas(df, ["data"], "%Q")
        self.assertEqual(df.iloc[0, 0], "2026-10-01")

    def test_tipos_e_datas_explicitas(self):
        df = pd.DataFrame({"a": ["2026-10-01", "invalida"], "b": [1, 2], "c": [True, False],
                           "d": [[1], [2]]})
        self.assertEqual([m.tipo for m in inspecionar_colunas(df).values()],
                         ["categoria", "numero", "categoria", "incompativel"])
        out, falhas = configurar_datas(df, ["a"])
        self.assertEqual(falhas, {"a": 1})
        self.assertEqual(inspecionar_colunas(out)["a"].tipo, "data")
        self.assertEqual(df.loc[0, "a"], "2026-10-01")

    def test_colunas_invalidas(self):
        for df in (pd.DataFrame([[1, 2]], columns=["a", "a"]), pd.DataFrame({1: [2]})):
            with self.assertRaises(ErroBI):
                inspecionar_colunas(df)


class TestFiltros(unittest.TestCase):
    def setUp(self):
        self.df = pd.DataFrame({"grupo": ["A", "B", "A", None], "x": [1, 2, 3, None],
                                "tempo": pd.to_datetime(["2026-10-01 00:00:00", "2026-10-02 23:59:59",
                                                         "2026-10-03 00:00:00", None])})

    def test_and_inclusivo_sem_mutacao(self):
        antes = self.df.copy(deep=True)
        out = aplicar_filtros(self.df, [{"coluna": "grupo", "tipo": "categoria", "valores": ["A"]},
                                       {"coluna": "x", "tipo": "numero", "minimo": 2, "maximo": 3}])
        self.assertEqual(out.index.tolist(), [2])
        out.loc[2, "x"] = 100
        assert_frame_equal(self.df, antes)

    def test_selecao_vazia_e_nulos(self):
        cfg = {"coluna": "grupo", "tipo": "categoria", "valores": []}
        self.assertTrue(aplicar_filtros(self.df, [cfg]).empty)
        cfg["incluir_nulos"] = True
        self.assertEqual(aplicar_filtros(self.df, [cfg]).index.tolist(), [3])

    def test_dia_final_completo_e_fuso(self):
        for tz in (None, "America/Sao_Paulo"):
            df = self.df.copy()
            if tz:
                df["tempo"] = df["tempo"].dt.tz_localize(tz)
            out = aplicar_filtros(df, [{"coluna": "tempo", "tipo": "data", "minimo": "2026-10-01",
                                        "maximo": "2026-10-02"}])
            self.assertEqual(out.index.tolist(), [0, 1])

    def test_erros_de_configuracao(self):
        for cfg in ({"coluna": "x", "tipo": "numero", "minimo": 3, "maximo": 1},
                    {"coluna": "x", "tipo": "numero", "minimo": "abc"},
                    {"coluna": "x", "tipo": "numero", "minimo": float("nan")},
                    {"coluna": "tempo", "tipo": "data", "maximo": "xxx"},
                    {"coluna": "ausente", "tipo": "categoria"},
                    {"coluna": "grupo", "tipo": "numero"},
                    {"coluna": "x", "tipo": "outro"}):
            with self.subTest(cfg=cfg), self.assertRaises(ErroBI):
                aplicar_filtros(self.df, [cfg])

    def test_limpar_filtros(self):
        out = aplicar_filtros(self.df, [])
        assert_frame_equal(out, self.df)
        self.assertIsNot(out, self.df)

    def test_indices_duplicados(self):
        df = self.df.copy()
        df.index = [0, 0, 1, 1]
        self.assertEqual(len(aplicar_filtros(df, [{"coluna": "x", "tipo": "numero", "maximo": 2}])), 2)


class TestGraficos(unittest.TestCase):
    def test_categorias_textuais_e_booleanas_no_mesmo_grupo(self):
        df = pd.DataFrame({"grupo": ["A", True, "B", False, True],
                           "valor": [1, 2, 3, 4, 5]})
        for op, esperado in (("contagem", {"A": 1, "B": 1, False: 1, True: 2}),
                             ("soma", {"A": 1, "B": 3, False: 4, True: 7})):
            with self.subTest(op=op):
                tabela = preparar_grafico(df, {"tipo": "barras", "grupo": "grupo",
                                              "operacao": op, "coluna": "valor"})
                self.assertEqual(tabela.set_index("grupo")["valor"].to_dict(), esperado)
                self.assertEqual(tabela["grupo"].tolist(), ["A", "B", False, True])

    def setUp(self):
        self.df = pd.DataFrame({"grupo": ["A", "A", "B", None], "valor": [1, 3, None, 5],
                                "tempo": pd.to_datetime(["2026-02-01", "2026-01-02", "2026-01-03", None])})

    def test_barras(self):
        for op, esperado in {"contagem": [2, 1], "soma": [4], "media": [2],
                             "minimo": [1], "maximo": [3]}.items():
            with self.subTest(op=op):
                tabela = preparar_grafico(self.df, {"tipo": "barras", "grupo": "grupo",
                                                    "operacao": op, "coluna": "valor"})
                self.assertEqual(tabela["valor"].tolist(), esperado)

    def test_temporal_ordenado(self):
        tabela = preparar_grafico(self.df, {"tipo": "linhas", "grupo": "tempo", "periodo": "mes"})
        self.assertEqual(tabela["grupo"].dt.month.tolist(), [1, 2])
        self.assertEqual(tabela["valor"].tolist(), [2, 1])

    def test_histograma_inclui_extremos(self):
        tabela = preparar_grafico(self.df, {"tipo": "histograma", "coluna": "valor", "intervalos": 2})
        self.assertEqual(tabela["frequencia"].tolist(), [2, 1])

    def test_histograma_constante(self):
        tabela = preparar_grafico(pd.DataFrame({"x": [2, 2]}), {"tipo": "histograma", "coluna": "x"})
        self.assertEqual(tabela["frequencia"].sum(), 2)

    def test_vazios(self):
        for cfg in ({"tipo": "barras", "grupo": "grupo"}, {"tipo": "linhas", "grupo": "tempo"},
                    {"tipo": "histograma", "coluna": "valor"}):
            self.assertTrue(preparar_grafico(self.df.iloc[:0], cfg).empty)

    def test_erros(self):
        for cfg in ({"tipo": "pizza"}, {"tipo": "linhas", "grupo": "grupo"},
                    {"tipo": "linhas", "grupo": "tempo", "periodo": "ano"},
                    {"tipo": "barras", "grupo": "grupo", "operacao": "distintos"},
                    {"tipo": "histograma", "coluna": "valor", "intervalos": 0},
                    {"tipo": "histograma", "coluna": "grupo"}):
            with self.subTest(cfg=cfg), self.assertRaises(ErroBI):
                preparar_grafico(self.df, cfg)

    def test_entrada_preservada(self):
        antes = self.df.copy(deep=True)
        preparar_grafico(self.df, {"tipo": "barras", "grupo": "grupo", "operacao": "soma", "coluna": "valor"})
        assert_frame_equal(self.df, antes)

    def test_soma_preserva_inteiros_nullable_grandes(self):
        df = pd.DataFrame({"a": ["X", "X", "X"],
                           "b": pd.Series([2**62 + 1, 2**62 + 1, None], dtype="Int64")})
        tabela = preparar_grafico(df, {"tipo": "barras", "grupo": "a", "operacao": "soma", "coluna": "b"})
        self.assertEqual(tabela["valor"].iloc[0], 2**63 + 2)

    def test_intervalo_preserva_inteiros_grandes(self):
        df = pd.DataFrame({"x": [2**62, 2**62 + 1]})
        out = aplicar_filtros(df, [{"coluna": "x", "tipo": "numero", "minimo": 2**62 + 1}])
        self.assertEqual(out.index.tolist(), [1])


class TestIndependenciaDominio(unittest.TestCase):
    def test_mesmo_fluxo_em_tres_dominios(self):
        for arquivo, grupo, medida, soma, media in (
            ("vendas", "produto", "valor", 450, 112.5),
            ("educacao", "turma", "nota", 24, 8),
            ("estoque", "categoria", "quantidade", 47, 47 / 3),
        ):
            with self.subTest(dataset=arquivo):
                df = pd.read_csv(RAIZ / "exemplos" / f"{arquivo}.csv")
                self.assertAlmostEqual(calcular_kpi(df, {"operacao": "media", "coluna": medida}).valor, media)
                self.assertEqual(calcular_kpi(df, {"operacao": "soma", "coluna": medida}).valor, soma)
                # Uma seleção de categoria alimenta KPI e gráfico com o mesmo DataFrame.
                filtrado = aplicar_filtros(df, [{"coluna": grupo, "tipo": "categoria",
                                                 "valores": [df[grupo].iloc[0]]}])
                kpi = calcular_kpi(filtrado, {"operacao": "soma", "coluna": medida})
                grafico = preparar_grafico(filtrado, {"tipo": "barras", "grupo": grupo,
                                                     "operacao": "soma", "coluna": medida})
                self.assertEqual(kpi.valor, grafico["valor"].sum())
                self.assertFalse(kpi.erro)


if __name__ == "__main__":
    unittest.main()
