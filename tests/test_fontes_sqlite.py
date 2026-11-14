"""Integração real SQLite → filtros → KPIs, com banco temporário."""
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from contextlib import closing

import pandas as pd

from oneworld import database
from oneworld.fontes_sqlite import carregar_tabela, listar_tabelas, _conectar
from oneworld.indicadores import calcular_kpi
from oneworld.filtros import aplicar_filtros


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
        with patch.object(database, "DB_PATH", self.caminho):
            antes = self.caminho.read_bytes()
            df = carregar_tabela(self.caminho, "amostra")
            self.assertEqual(len(df), 1)
            self.assertEqual(calcular_kpi(df, {"operacao": "contagem"}).valor, 1)
            self.assertEqual(df.iloc[0]["conteudo"], b'\xff\x00')
            self.assertEqual(self.caminho.read_bytes(), antes)

            with closing(sqlite3.connect(self.caminho)) as con:
                con.execute('UPDATE amostra SET medida=?', (1.00000000002,))
                con.commit()
            df_atualizado = carregar_tabela(self.caminho, "amostra")
            self.assertEqual(df_atualizado.iloc[0]["medida"], 1.00000000002)

    def test_dashboard_reflete_banco_filtros_e_retorno_a_exemplos(self):
        with patch.object(database, "DB_PATH", self.caminho):
            df = carregar_tabela(self.caminho, "notas livres")
            self.assertEqual(calcular_kpi(df, {"operacao": "media", "coluna": "nota"}).valor, 8)
            filtrado = aplicar_filtros(df, [{"coluna": "turma", "tipo": "categoria", "valores": ["A"]}])
            self.assertEqual(calcular_kpi(filtrado, {"operacao": "media", "coluna": "nota"}).valor, 7)
            with closing(sqlite3.connect(self.caminho)) as con:
                con.execute('INSERT INTO "notas livres" VALUES ("C", 12)')
                con.commit()
            df_novo = carregar_tabela(self.caminho, "notas livres")
            self.assertEqual(calcular_kpi(df_novo, {"operacao": "contagem"}).valor, 4)


if __name__ == "__main__":
    unittest.main()
