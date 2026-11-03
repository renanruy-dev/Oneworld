"""Contrato público dos KPIs e apresentação explícita em diferentes domínios."""
from dataclasses import asdict
from io import BytesIO
import json
from pathlib import Path
import unittest

import pandas as pd
from pandas.testing import assert_frame_equal

from oneworld.filtros import aplicar_filtros
from oneworld.formatacao import formatar_valor_kpi
from oneworld.indicadores import OPERACOES, calcular_kpi
from oneworld.metadados import ErroBI

RAIZ = Path(__file__).resolve().parents[1]


class TestContratoKPI(unittest.TestCase):
    def test_configuracoes_malformadas_retornam_erro(self):
        df = pd.DataFrame({"x": [1]})
        for cfg in (None, [], "soma", 1, {}, {"operacao": []},
                    {"operacao": {"tipo": "soma"}},
                    {"operacao": "soma"}, {"operacao": "soma", "coluna": []},
                    {"operacao": "distintos", "coluna": {"nome": "x"}},
                    {"operacao": "contagem", "titulo": 42}):
            with self.subTest(cfg=cfg):
                r = calcular_kpi(df, cfg)
                self.assertIsNone(r.valor)
                self.assertTrue(r.erro)
                self.assertFalse(r.disponivel)

    def test_dataframe_invalido_retornado_como_erro(self):
        for df in (None, [{"x": 1}], pd.DataFrame({1: [2]}),
                   pd.DataFrame([[1, 2]], columns=["x", "x"])):
            with self.subTest(df=repr(df)):
                self.assertTrue(calcular_kpi(df, {"operacao": "contagem"}).erro)

    def test_validacao_de_coluna_e_tipo_em_todas_as_operacoes(self):
        df = pd.DataFrame({
            "texto": ["1", None], "logico": pd.Series([True, None], dtype="boolean"),
            "data": pd.to_datetime(["2026-01-01", None]),
            "aninhado": [[1], [2]], "complexo": [1j, 2j],
        })
        for op in OPERACOES:
            if op == "contagem":
                continue
            with self.subTest(op=op, coluna="ausente"):
                self.assertTrue(calcular_kpi(df, {"operacao": op, "coluna": "ausente"}).erro)
            colunas = ("aninhado", "complexo") if op == "distintos" else df.columns
            for coluna in colunas:
                with self.subTest(op=op, coluna=coluna):
                    self.assertTrue(calcular_kpi(df, {"operacao": op, "coluna": coluna}).erro)

    def test_distintos_em_tipos_compativeis_ignora_nulos(self):
        df = pd.DataFrame({
            "categoria": pd.Categorical(["A", "A", None], categories=["A", "B"]),
            "texto": pd.Series(["A", "A", None], dtype="string"),
            "numero": pd.Series([2, 2, None], dtype="Int64"),
            "logico": pd.Series([True, True, None], dtype="boolean"),
            "data": pd.to_datetime(["2026-01-01", "2026-01-01", None], utc=True),
        })
        for coluna in df.columns:
            with self.subTest(coluna=coluna):
                r = calcular_kpi(df, {"operacao": "distintos", "coluna": coluna})
                self.assertIsNone(r.erro)
                self.assertEqual(r.valor, 1)

    def test_contagem_inclui_linhas_nulas_e_indices_duplicados(self):
        df = pd.DataFrame({"qualquer": [None, None]}, index=[7, 7])
        self.assertEqual(calcular_kpi(df, {"operacao": "contagem"}).valor, 2)
        self.assertEqual(calcular_kpi(df, {"operacao": "distintos", "coluna": "qualquer"}).valor, 0)
        self.assertEqual(calcular_kpi(pd.DataFrame(index=[1, 2]), {"operacao": "contagem"}).valor, 2)

    def test_sem_registros_apos_filtros(self):
        df = pd.DataFrame({"grupo": ["A"], "medida": pd.Series([1], dtype="Int64")})
        vazio = aplicar_filtros(df, [{"coluna": "grupo", "tipo": "categoria", "valores": []}])
        for op in OPERACOES:
            with self.subTest(op=op):
                r = calcular_kpi(vazio, {"operacao": op, "coluna": "medida"})
                self.assertIsNone(r.erro)
                if op in ("contagem", "distintos"):
                    self.assertEqual(r.valor, 0)
                    self.assertTrue(r.disponivel)
                else:
                    self.assertIsNone(r.valor)
                    self.assertTrue(r.mensagem)
                    self.assertFalse(r.disponivel)

    def test_nulos_e_infinitos_sem_valores_validos(self):
        for serie in (pd.Series([None, None], dtype="Int64"),
                      pd.Series([None, None], dtype="Float64"),
                      pd.Series([float("inf"), float("-inf"), None])):
            for op in ("soma", "media", "minimo", "maximo"):
                with self.subTest(dtype=serie.dtype, op=op):
                    r = calcular_kpi(pd.DataFrame({"m": serie}), {"operacao": op, "coluna": "m"})
                    self.assertIsNone(r.erro)
                    self.assertIsNone(r.valor)
                    self.assertTrue(r.mensagem)

    def test_dtypes_numericos_e_resultados_serializaveis(self):
        for dtype in ("int32", "uint64", "float32", "Int64", "UInt64", "Float64"):
            df = pd.DataFrame({"m": pd.Series([2, 4], dtype=dtype)})
            for op, esperado in {"soma": 6, "media": 3, "minimo": 2, "maximo": 4}.items():
                with self.subTest(dtype=dtype, op=op):
                    r = calcular_kpi(df, {"operacao": op, "coluna": "m", "titulo": "Minha escolha"})
                    self.assertIsNone(r.erro)
                    self.assertEqual(r.valor, esperado)
                    self.assertEqual(r.titulo, "Minha escolha")
                    self.assertEqual(json.loads(json.dumps(asdict(r)))["valor"], esperado)

    def test_precisao_de_inteiros_nullable(self):
        df = pd.DataFrame({"m": pd.Series([2**62 + 1, 2**62 + 2, None], dtype="Int64")})
        for op, esperado in {"soma": 2**63 + 3, "minimo": 2**62 + 1, "maximo": 2**62 + 2}.items():
            with self.subTest(op=op):
                self.assertEqual(calcular_kpi(df, {"operacao": op, "coluna": "m"}).valor, esperado)

    def test_overflow_float_retorna_erro(self):
        df = pd.DataFrame({"m": [1e308, 1e308]})
        self.assertTrue(calcular_kpi(df, {"operacao": "soma", "coluna": "m"}).erro)

    def test_dados_e_configuracao_preservados_com_nomes_arbitrarios(self):
        df = pd.DataFrame({"Temperatura (°C)": [-5, 0, 8, None], "Local / ID": ["A", "B", "A", None]})
        antes = df.copy(deep=True)
        cfg = {"titulo": "Temperatura média", "operacao": "media", "coluna": "Temperatura (°C)"}
        copia = cfg.copy()
        self.assertEqual(calcular_kpi(df, cfg).valor, 1)
        self.assertEqual(cfg, copia)
        assert_frame_equal(df, antes)
        renomeado = df.rename(columns={"Temperatura (°C)": "outra medida"})
        self.assertEqual(calcular_kpi(renomeado, {**cfg, "coluna": "outra medida"}).valor, 1)


class TestFormatacaoKPI(unittest.TestCase):
    def test_apresentacao_independente_do_calculo(self):
        df = pd.DataFrame({"valor": [0.25]})
        for formato, esperado in (("numero", "0.25"), ("percentual", "25.00%"), ("moeda", "€ 0.25")):
            with self.subTest(formato=formato):
                r = calcular_kpi(df, {"titulo": "Escolha do usuário", "operacao": "soma",
                                      "coluna": "valor", "formato": formato})
                self.assertEqual(r.valor, 0.25)
                self.assertEqual(r.titulo, "Escolha do usuário")
                self.assertEqual(formatar_valor_kpi(r.valor, formato, simbolo="€"), esperado)
        self.assertEqual(formatar_valor_kpi(calcular_kpi(df, {"operacao": "soma", "coluna": "valor"}).valor), "0.25")

    def test_zero_indisponibilidade_e_inteiros_grandes(self):
        self.assertEqual(formatar_valor_kpi(0), "0")
        for formato in ("numero", "percentual", "moeda"):
            with self.subTest(formato=formato):
                self.assertEqual(formatar_valor_kpi(None, formato), "—")
        self.assertEqual(formatar_valor_kpi(2**62 + 1), "4611686018427387905")
        self.assertEqual(formatar_valor_kpi(2**62 + 1, "moeda"), "R$ 4,611,686,018,427,387,905.00")

    def test_erros_de_apresentacao(self):
        for formato in (None, [], "receita"):
            with self.subTest(formato=formato), self.assertRaises(ErroBI):
                formatar_valor_kpi(1, formato)
        for valor in ("1", True, float("inf"), float("nan")):
            with self.subTest(valor=valor), self.assertRaises(ErroBI):
                formatar_valor_kpi(valor)
        for simbolo in (None, "", " "):
            with self.subTest(simbolo=simbolo), self.assertRaises(ErroBI):
                formatar_valor_kpi(1, "moeda", simbolo=simbolo)


class TestPlanilhasDiferentes(unittest.TestCase):
    def test_todas_as_operacoes_nos_tres_csv(self):
        for nome, medida, categoria, esperados in (
            ("vendas", "valor", "produto", (4, 3, 450, 112.5, 50, 200)),
            ("educacao", "nota", "turma", (3, 2, 24, 8, 6, 10)),
            ("estoque", "quantidade", "categoria", (3, 2, 47, 47 / 3, 5, 30)),
        ):
            df = pd.read_csv(RAIZ / "exemplos" / f"{nome}.csv")
            for op, esperado in zip(OPERACOES, esperados):
                with self.subTest(dataset=nome, op=op):
                    r = calcular_kpi(df, {"operacao": op, "coluna": categoria if op == "distintos" else medida})
                    self.assertIsNone(r.erro)
                    self.assertAlmostEqual(r.valor, esperado)

    def test_abas_xlsx_com_estruturas_diferentes(self):
        arquivo = BytesIO()
        with pd.ExcelWriter(arquivo) as writer:
            for nome in ("vendas", "educacao"):
                pd.read_csv(RAIZ / "exemplos" / f"{nome}.csv").to_excel(writer, sheet_name=nome, index=False)
        arquivo.seek(0)
        abas = pd.read_excel(arquivo, sheet_name=None)
        for nome, medida, esperado in (("vendas", "valor", 112.5), ("educacao", "nota", 8)):
            with self.subTest(aba=nome):
                r = calcular_kpi(abas[nome], {"operacao": "media", "coluna": medida})
                self.assertIsNone(r.erro)
                self.assertEqual(r.valor, esperado)


if __name__ == "__main__":
    unittest.main()
