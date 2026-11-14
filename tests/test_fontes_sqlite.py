"""Integração real SQLite → filtros → KPIs, com banco temporário."""
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from contextlib import closing

from streamlit.testing.v1 import AppTest

from oneworld import database
from oneworld.fontes_sqlite import carregar_tabela, listar_tabelas
from oneworld.fontes_sqlite import _conectar
from oneworld.indicadores import calcular_kpi


def widget(app, tipo, base):
    """Localiza um controle da fonte ativa por seu nome funcional."""
    return next(w for w in getattr(app, tipo)
                if w.key and w.key.split("::")[0] == base)


class TestFontesSQLite(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.caminho = Path(self.temp.name) / "dados.db"
        with closing(sqlite3.connect(self.caminho)) as con:
            con.execute('CREATE TABLE "notas livres" (turma TEXT, nota REAL)')
            con.executemany('INSERT INTO "notas livres" VALUES (?, ?)',
                            [("A", 8), ("A", 6), ("B", 10)])
            con.commit()

    def test_leitura_sem_alterar_banco_e_sem_criar_arquivo(self):
        antes = self.caminho.read_bytes()
        self.assertEqual(listar_tabelas(self.caminho), ["notas livres"])
        df = carregar_tabela(self.caminho, "notas livres")
        self.assertEqual(calcular_kpi(df, {"operacao": "media", "coluna": "nota"}).valor, 8)
        self.assertEqual(self.caminho.read_bytes(), antes)
        ausente = self.caminho.with_name("ausente.db")
        with self.assertRaises(sqlite3.Error):
            listar_tabelas(ausente)
        self.assertFalse(ausente.exists())

    def test_nomes_de_tabela_sao_identificadores(self):
        with self.assertRaises(ValueError):
            carregar_tabela(self.caminho, 'notas livres"; DROP TABLE "notas livres')
        with closing(sqlite3.connect(self.caminho)) as con:
            con.execute('CREATE TABLE "nome""especial" (valor INTEGER)')
            con.execute('INSERT INTO "nome""especial" VALUES (42)')
            con.commit()
        self.assertEqual(carregar_tabela(self.caminho, 'nome"especial').iloc[0, 0], 42)

    def test_conexao_bi_recusa_escrita(self):
        antes = self.caminho.read_bytes()
        with closing(_conectar(self.caminho)) as con:
            with self.assertRaises(sqlite3.OperationalError):
                con.execute('INSERT INTO "notas livres" VALUES ("C", 12)')
        self.assertEqual(self.caminho.read_bytes(), antes)

    def test_dashboard_blob_e_atualizacao_real_pequena(self):
        with closing(sqlite3.connect(self.caminho)) as con:
            con.execute('CREATE TABLE amostra (conteudo BLOB, medida REAL)')
            con.execute('INSERT INTO amostra VALUES (?, ?)', (b'\xff\x00', 1.00000000001))
            con.commit()
        script = '''
from oneworld.frontend_bi import mostrar_dashboard
mostrar_dashboard("#5B4FC4")
'''
        with patch.object(database, "DB_PATH", self.caminho):
            antes = self.caminho.read_bytes()
            app = AppTest.from_string(script, default_timeout=20).run()
            widget(app, "checkbox", "bi_banco_local").check().run()
            widget(app, "selectbox", "bi_dataset").select("Banco local: amostra").run()
            self.assertFalse(app.exception)
            self.assertFalse(app.error)
            self.assertEqual(app.metric[0].value, "1")
            self.assertEqual(app.dataframe[-1].value.iloc[0]["conteudo"], b'\xff\x00')
            self.assertEqual(self.caminho.read_bytes(), antes)
            identidade = app.session_state["bi_fonte"][0]
            with closing(sqlite3.connect(self.caminho)) as con:
                con.execute('UPDATE amostra SET medida=?', (1.00000000002,))
                con.commit()
            app.run()
            self.assertFalse(app.exception)
            self.assertNotEqual(app.session_state["bi_fonte"][0], identidade)
            self.assertEqual(app.dataframe[-1].value.iloc[0]["medida"], 1.00000000002)

    def test_dashboard_reflete_banco_filtros_e_retorno_a_exemplos(self):
        with patch.object(database, "DB_PATH", self.caminho):
            app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py"),
                                    default_timeout=20).run()
            widget(app, "checkbox", "bi_banco_local").check().run()
            widget(app, "selectbox", "bi_dataset").select("Banco local: notas livres").run()
            widget(app, "selectbox", "bi_cfg_kpi_0_op").select("media").run()
            self.assertEqual(app.metric[0].value, "8.00")
            widget(app, "checkbox", "bi_cfg_filtro_0").check().run()
            widget(app, "multiselect", "bi_cfg_filtro_0_valores").set_value(["A"]).run()
            self.assertEqual(app.metric[0].value, "7.00")
            with closing(sqlite3.connect(self.caminho)) as con:
                con.execute('INSERT INTO "notas livres" VALUES ("C", 12)')
                con.commit()
            app.run()
            self.assertEqual(app.metric[0].value, "4")  # nova origem reinicia configurações
            widget(app, "checkbox", "bi_banco_local").uncheck().run()
            self.assertFalse(app.exception)
            self.assertFalse(app.error)
            self.assertTrue(widget(app, "selectbox", "bi_dataset").value.startswith("Exemplo:"))


if __name__ == "__main__":
    unittest.main()
