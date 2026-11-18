"""Testes da tela 'Adicionar dados' em formato de cards (2 por linha)."""
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

try:
    os.environ["QT_QPA_PLATFORM"] = "offscreen"
    from PyQt6.QtCore import QEvent
    from PyQt6.QtWidgets import (
        QApplication,
        QCheckBox,
        QComboBox,
        QFrame,
        QGridLayout,
        QLabel,
        QLineEdit,
        QMessageBox,
        QPushButton,
        QTabWidget,
    )
    _qt_app = QApplication.instance() or QApplication(["-platform", "offscreen"])
    from oneworld import database as db
    from oneworld.frontend import BarChartWidget, MetricCard, MultiSelectChips, OneWorldWindow
    TEM_PYQT6 = True
except (ImportError, OSError):
    TEM_PYQT6 = False
    OneWorldWindow = None


@unittest.skipUnless(TEM_PYQT6, "PyQt6 ou bibliotecas de display não disponíveis no ambiente")
class TestTelaAdicionarDadosCards(unittest.TestCase):
    def setUp(self):
        self.temporario = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporario.cleanup)
        self.banco = patch.object(db, "DB_PATH", Path(self.temporario.name) / "teste_cards.db")
        self.banco.start()
        self.addCleanup(self.banco.stop)
        db.init_db()
        self.win = OneWorldWindow()
        self.addCleanup(self.win.close)
        self.win.pagina_atual = "Eventos"
        self._reconstruir()

    def _flush(self):
        _qt_app.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        _qt_app.processEvents()

    def _reconstruir(self):
        self.win.reconstruir_pagina()
        self._flush()

    def _pagina(self):
        return self.win.scroll.widget()

    def _aba_modulo(self) -> QTabWidget:
        tabs = self._pagina().findChildren(QTabWidget)
        self.assertTrue(tabs, "QTabWidget principal de 'Adicionar dados' não encontrado")
        return tabs[0]

    def test_sem_exportar_csv_e_sem_filtros_chips(self):
        botoes = [b.text() for b in self._pagina().findChildren(QPushButton)]
        self.assertNotIn("Exportar CSV", botoes)
        chips = self._pagina().findChildren(MultiSelectChips)
        self.assertEqual(chips, [])

    def test_cards_receitas_duas_colunas_e_busca(self):
        # 1 receita -> ocupa metade (0, 0) e placeholder em (0, 1)
        db.inserir_lote(
            "eventos",
            [{
                "data": "2026-11-18",
                "cliente": "Venda Alpha",
                "local": "Online",
                "convidados": 100,
                "valor": 1500.0,
                "status": "Confirmado",
            }],
        )
        self.win.estado["tab_modulo_fin"] = 1
        self._reconstruir()
        aba_fin = self._aba_modulo().widget(1)
        grade = aba_fin.findChild(QGridLayout)
        self.assertIsNotNone(grade)
        cards = [c for c in aba_fin.findChildren(QFrame) if c.objectName() == "OwCard"]
        self.assertEqual(len(cards), 1)
        self.assertIs(grade.itemAtPosition(0, 0).widget(), cards[0])
        self.assertIsNotNone(grade.itemAtPosition(0, 1))

        # +2 receitas (total 3) -> 2 na linha 0 e 3º vai para linha 1 coluna 0
        db.inserir_lote(
            "eventos",
            [
                {
                    "data": "2026-11-19",
                    "cliente": "Venda Beta",
                    "local": "Loja",
                    "convidados": 200,
                    "valor": 2500.0,
                    "status": "Concluído",
                },
                {
                    "data": "2026-11-20",
                    "cliente": "Consultoria Gama",
                    "local": "Matriz",
                    "convidados": 0,
                    "valor": 4000.0,
                    "status": "Em planejamento",
                },
            ],
        )
        self._reconstruir()
        aba_fin = self._aba_modulo().widget(1)
        grade = aba_fin.findChild(QGridLayout)
        cards = [c for c in aba_fin.findChildren(QFrame) if c.objectName() == "OwCard"]
        self.assertEqual(len(cards), 3)
        self.assertIsNotNone(grade.itemAtPosition(0, 0))
        self.assertIsNotNone(grade.itemAtPosition(0, 1))
        self.assertIsNotNone(grade.itemAtPosition(1, 0))
        self.assertIsNone(grade.itemAtPosition(1, 1))

        # Busca filtra os cards
        busca = aba_fin.findChild(QLineEdit)
        self.assertIsNotNone(busca)
        busca.setText("Consultoria")
        self._flush()
        cards_filtrados = [c for c in aba_fin.findChildren(QFrame) if c.objectName() == "OwCard"]
        self.assertEqual(len(cards_filtrados), 1)

    def test_cards_gastos_duas_colunas_e_exclusao(self):
        db.inserir_lote(
            "convidados",
            [
                {
                    "evento": "Venda Alpha",
                    "nome": "Servidor Cloud",
                    "mesa": "Infraestrutura",
                    "acompanhantes": 350,
                    "contato": "NF-101",
                    "restricao": "Fixo",
                    "confirmacao": "Confirmado",
                },
                {
                    "evento": "Venda Alpha",
                    "nome": "Anúncios",
                    "mesa": "Marketing",
                    "acompanhantes": 500,
                    "contato": "Pix",
                    "restricao": "Variável",
                    "confirmacao": "Pendente",
                },
                {
                    "evento": "Venda Beta",
                    "nome": "Frete",
                    "mesa": "Logística",
                    "acompanhantes": 120,
                    "contato": "CT-e 9",
                    "restricao": "—",
                    "confirmacao": "Confirmado",
                },
            ],
        )
        self.win.estado["tab_modulo_fin"] = 1
        self._reconstruir()
        aba_fin = self._aba_modulo().widget(1)
        grade = aba_fin.findChild(QGridLayout)
        cards = [c for c in aba_fin.findChildren(QFrame) if c.objectName() == "OwCard"]
        self.assertEqual(len(cards), 3)
        self.assertIsNotNone(grade.itemAtPosition(0, 0))
        self.assertIsNotNone(grade.itemAtPosition(0, 1))
        self.assertIsNotNone(grade.itemAtPosition(1, 0))

        # Excluir primeiro card via botão Excluir com confirmação
        btn_excluir = [b for b in cards[0].findChildren(QPushButton) if b.text() == "Excluir"][0]
        with patch.object(QMessageBox, "question", return_value=QMessageBox.StandardButton.Yes):
            btn_excluir.click()
        self._flush()

        aba_fin = self._aba_modulo().widget(1)
        cards_restantes = [c for c in aba_fin.findChildren(QFrame) if c.objectName() == "OwCard"]
        self.assertEqual(len(cards_restantes), 2)

    def test_aba_dados_gerais_cards_busca_e_exclusao(self):
        abas = self._aba_modulo()
        self.assertEqual(abas.count(), 2)
        self.assertIn("Dados Gerais", abas.tabText(0))
        self.assertIn("Dados Financeiros", abas.tabText(1))

        db.inserir_dado_geral({
            "titulo": "Meta Q4",
            "categoria": "Comercial",
            "valor": "R$ 100.000",
            "data": "2026-11-18",
            "descricao": "Meta de vendas",
        })
        db.inserir_dado_geral({
            "titulo": "Clientes Ativos",
            "categoria": "Operacional",
            "valor": "240",
            "data": "2026-11-18",
            "descricao": "",
        })
        db.inserir_dado_geral({
            "titulo": "Estoque Base",
            "categoria": "Logística",
            "valor": "850 un.",
            "data": "2026-11-18",
            "descricao": "Depósito central",
        })

        self.win.estado["tab_modulo_fin"] = 0
        self._reconstruir()
        aba_dg = self._aba_modulo().widget(0)
        grade = aba_dg.findChild(QGridLayout)
        cards = [c for c in aba_dg.findChildren(QFrame) if c.objectName() == "OwCard"]
        self.assertEqual(len(cards), 3)
        self.assertIsNotNone(grade.itemAtPosition(0, 0))
        self.assertIsNotNone(grade.itemAtPosition(0, 1))
        self.assertIsNotNone(grade.itemAtPosition(1, 0))

        # Busca
        busca = aba_dg.findChild(QLineEdit)
        busca.setText("Estoque")
        self._flush()
        self.assertEqual(len([c for c in aba_dg.findChildren(QFrame) if c.objectName() == "OwCard"]), 1)

        # Limpa busca e exclui
        busca.setText("")
        self._flush()
        cards = [c for c in aba_dg.findChildren(QFrame) if c.objectName() == "OwCard"]
        btn_excluir = [b for b in cards[0].findChildren(QPushButton) if b.text() == "Excluir"][0]
        with patch.object(QMessageBox, "question", return_value=QMessageBox.StandardButton.Yes):
            btn_excluir.click()
        self._flush()

        aba_dg = self._aba_modulo().widget(0)
        self.assertEqual(len([c for c in aba_dg.findChildren(QFrame) if c.objectName() == "OwCard"]), 2)

    def test_dados_financeiros_categorias_e_botoes_separados(self):
        db.inserir_lote(
            "eventos",
            [{
                "data": "2026-11-18",
                "cliente": "Receita Teste",
                "local": "Online",
                "convidados": 10,
                "valor": 1000.0,
                "status": "Confirmado",
            }],
        )
        db.inserir_lote(
            "convidados",
            [{
                "evento": "Receita Teste",
                "nome": "Despesa Teste",
                "mesa": "Operacional",
                "acompanhantes": 200,
                "contato": "NF-1",
                "restricao": "Fixo",
                "confirmacao": "Confirmado",
            }],
        )
        self.win.estado["tab_modulo_fin"] = 1
        self._reconstruir()
        aba_fin = self._aba_modulo().widget(1)

        botoes = [b.text() for b in aba_fin.findChildren(QPushButton)]
        self.assertIn("+ Adicionar Receita", botoes)
        self.assertIn("+ Adicionar Despesa", botoes)

        cards = [c for c in aba_fin.findChildren(QFrame) if c.objectName() == "OwCard"]
        self.assertEqual(len(cards), 2)

        cb_cat = aba_fin.findChild(QComboBox)
        self.assertIsNotNone(cb_cat)

        cb_cat.setCurrentIndex(cb_cat.findData("Receitas"))
        self._flush()
        self.assertEqual(len([c for c in aba_fin.findChildren(QFrame) if c.objectName() == "OwCard"]), 1)

        cb_cat.setCurrentIndex(cb_cat.findData("Despesas"))
        self._flush()
        self.assertEqual(len([c for c in aba_fin.findChildren(QFrame) if c.objectName() == "OwCard"]), 1)

        cb_cat.setCurrentIndex(cb_cat.findData("Todas"))
        self._flush()
        self.assertEqual(len([c for c in aba_fin.findChildren(QFrame) if c.objectName() == "OwCard"]), 2)

    def test_configuracao_campo_dashboard_e_tipo_informacao(self):
        id_dg = db.inserir_dado_geral({
            "titulo": "Vendas Balcão",
            "categoria": "Comercial",
            "valor": "1500",
            "data": "2026-11-18",
            "descricao": "Faturamento diário",
        })
        id_ev = db.inserir_lote(
            "eventos",
            [{
                "data": "2026-11-18",
                "cliente": "Contrato Y",
                "local": "Online",
                "convidados": 100,
                "valor": 2000.0,
                "status": "Confirmado",
            }],
        )
        db.salvar_meta_campo("dados_gerais", id_dg, {
            "tipo_dashboard": "kpi_grafico",
            "nome_info": "Vendas Loja",
            "tipo_valor": "dinheiro",
            "itens": [{"rotulo": "Dia 1", "valor": 1500.0, "data": "2026-11-18"}],
        })
        db.salvar_meta_campo("eventos", id_ev, {
            "tipo_dashboard": "lista",
            "nome_info": "Parcela",
            "tipo_valor": "dinheiro",
        })

        # Dados Gerais (aba 0) exibe botão '+ Adicionar dados' no card
        self.win.estado["tab_modulo_fin"] = 0
        self._reconstruir()
        aba_dg = self._aba_modulo().widget(0)
        cards_dg = [c for c in aba_dg.findChildren(QFrame) if c.objectName() == "OwCard"]
        self.assertEqual(len(cards_dg), 1)
        botoes_dg = [b.text() for b in cards_dg[0].findChildren(QPushButton)]
        self.assertIn("+ Adicionar dados", botoes_dg)
        self.assertIn("Editar", botoes_dg)
        self.assertIn("Excluir", botoes_dg)
        textos_dg = " ".join(lbl.text() for lbl in cards_dg[0].findChildren(QLabel))
        self.assertIn("Vendas Loja", textos_dg)
        self.assertIn("Dia 1", textos_dg)

        # Dados Financeiros (aba 1) também exibe botão '+ Adicionar dados' no card
        self.win.estado["tab_modulo_fin"] = 1
        self._reconstruir()
        aba_fin = self._aba_modulo().widget(1)
        cards_fin = [c for c in aba_fin.findChildren(QFrame) if c.objectName() == "OwCard"]
        self.assertEqual(len(cards_fin), 1)
        self.assertIn("+ Adicionar dados", [b.text() for b in cards_fin[0].findChildren(QPushButton)])

    def test_adicionar_dados_no_card_atualiza_lista_e_dashboard(self):
        id_dg = db.inserir_dado_geral({
            "titulo": "Faturamento Filial",
            "categoria": "Financeiro",
            "valor": "1000",
            "data": "2026-11-18",
            "descricao": "",
        })
        db.salvar_meta_campo("dados_gerais", id_dg, {
            "tipo_dashboard": "kpi_grafico",
            "nome_info": "Venda Lote",
            "tipo_valor": "dinheiro",
            "itens": [{"rotulo": "Lote 1", "valor": 1000.0, "data": "2026-11-18"}],
        })
        id_ev = db.inserir_lote(
            "eventos",
            [{
                "data": "2026-11-18",
                "cliente": "Serviço Principal",
                "local": "Matriz",
                "convidados": 200,
                "valor": 5000.0,
                "status": "Confirmado",
            }],
        )
        db.salvar_meta_campo("eventos", id_ev, {
            "tipo_dashboard": "kpi",
            "nome_info": "Receita Contrato",
            "tipo_valor": "dinheiro",
            "itens": [{"rotulo": "Parcela 1", "valor": 5000.0, "data": "2026-11-18"}],
        })

        # Adiciona segundo dado ao campo de Dados Gerais
        meta_dg = db.adicionar_item_campo("dados_gerais", id_dg, {
            "rotulo": "Lote 2",
            "valor": 2500.0,
            "data": "2026-11-19",
        })
        dg_row = db.carregar_dados_gerais().iloc[0].to_dict()
        self.win._sincronizar_valor_campo_com_itens("dados_gerais", dg_row, meta_dg)

        # Verifica atualização no card em Adicionar dados
        self.win.estado["tab_modulo_fin"] = 0
        self._reconstruir()
        aba_dg = self._aba_modulo().widget(0)
        card = [c for c in aba_dg.findChildren(QFrame) if c.objectName() == "OwCard"][0]
        textos_card = " ".join(lbl.text() for lbl in card.findChildren(QLabel))
        self.assertIn("Lote 2", textos_card)
        self.assertIn("3.500,00", textos_card)

        # Navega para o Dashboard inicial e valida KPIs principais, painel CVM e campos configurados
        self.win.navegar_para("Dashboard")
        self._flush()
        pagina_dash = self._pagina()
        self.assertTrue(hasattr(self.win, "cvm_painel_negocio"))

        kpis = pagina_dash.findChildren(MetricCard)
        titulos_kpi = [k.lbl_titulo.text() for k in kpis]
        # KPIs financeiros padrão continuam presentes
        self.assertIn("Total de Gastos", titulos_kpi)
        self.assertIn("Rendimento Líquido", titulos_kpi)
        # Novos campos configurados aparecem como KPIs e Gráfico
        self.assertTrue(any("Faturamento Filial" in t for t in titulos_kpi))
        self.assertTrue(any("Serviço Principal" in t for t in titulos_kpi))
        graficos = pagina_dash.findChildren(BarChartWidget)
        self.assertGreaterEqual(len(graficos), 2)

    def _mapa_kpis_dashboard(self) -> dict[str, str]:
        return {k.lbl_titulo.text(): k.lbl_valor.text() for k in self._pagina().findChildren(MetricCard)}

    def test_insercao_edicao_e_remocao_atualizam_dashboard(self):
        # 1. Inserção
        id_dg = db.inserir_dado_geral({
            "titulo": "Estoque Central",
            "categoria": "Operacional",
            "valor": "100",
            "data": "2026-11-18",
            "descricao": "",
        })
        db.sincronizar_meta_com_valor_registro(
            "dados_gerais",
            id_dg,
            "100",
            "2026-11-18",
            {"tipo_dashboard": "kpi", "nome_info": "Unidades", "tipo_valor": "numero"},
        )

        id_ev = db.inserir_lote(
            "eventos",
            [{
                "data": "2026-11-18",
                "cliente": "Venda Mês",
                "local": "Online",
                "convidados": 0,
                "valor": 1000.0,
                "status": "Confirmado",
            }],
        )
        db.sincronizar_meta_com_valor_registro(
            "eventos",
            id_ev,
            1000.0,
            "2026-11-18",
            {"tipo_dashboard": "kpi", "nome_info": "Receita lançada", "tipo_valor": "dinheiro"},
        )

        id_cv = db.inserir_lote(
            "convidados",
            [{
                "evento": "Venda Mês",
                "nome": "Aluguel",
                "mesa": "Fixo",
                "acompanhantes": 400,
                "contato": "Boleto",
                "restricao": "—",
                "confirmacao": "Confirmado",
            }],
        )
        db.sincronizar_meta_com_valor_registro(
            "convidados",
            id_cv,
            400,
            "2026-11-18",
            {"tipo_dashboard": "kpi", "nome_info": "Despesa lançada", "tipo_valor": "dinheiro"},
        )

        self.win.navegar_para("Dashboard")
        self._flush()
        kpis = self._mapa_kpis_dashboard()
        self.assertEqual(kpis["Total de Gastos"], "R$ 400,00")
        self.assertEqual(kpis["Rendimento Líquido"], "R$ 600,00")
        self.assertEqual(kpis["Estoque Central · Unidades"], "100")
        self.assertEqual(kpis["Venda Mês · Receita lançada"], "R$ 1.000,00")
        self.assertEqual(kpis["Aluguel · Despesa lançada"], "R$ 400,00")

        # 2. Edição de todos os registros e atualização automática do Dashboard
        db.atualizar_dado_geral(id_dg, {
            "titulo": "Estoque Central",
            "categoria": "Operacional",
            "valor": "250",
            "data": "2026-11-18",
            "descricao": "",
        })
        db.sincronizar_meta_com_valor_registro(
            "dados_gerais",
            id_dg,
            "250",
            "2026-11-18",
            {"tipo_dashboard": "kpi", "nome_info": "Unidades", "tipo_valor": "numero"},
        )

        db.atualizar("eventos", id_ev, {
            "data": "2026-11-18",
            "cliente": "Venda Mês",
            "local": "Online",
            "convidados": 0,
            "valor": 3000.0,
            "status": "Confirmado",
        }, {})
        db.sincronizar_meta_com_valor_registro(
            "eventos",
            id_ev,
            3000.0,
            "2026-11-18",
            {"tipo_dashboard": "kpi", "nome_info": "Receita lançada", "tipo_valor": "dinheiro"},
        )

        db.atualizar("convidados", id_cv, {
            "evento": "Venda Mês",
            "nome": "Aluguel",
            "mesa": "Fixo",
            "acompanhantes": 500,
            "contato": "Boleto",
            "restricao": "—",
            "confirmacao": "Confirmado",
        }, {})
        db.sincronizar_meta_com_valor_registro(
            "convidados",
            id_cv,
            500,
            "2026-11-18",
            {"tipo_dashboard": "kpi", "nome_info": "Despesa lançada", "tipo_valor": "dinheiro"},
        )

        self.win.notificar_alteracao_dados()
        self._flush()
        kpis = self._mapa_kpis_dashboard()
        self.assertEqual(kpis["Total de Gastos"], "R$ 500,00")
        self.assertEqual(kpis["Rendimento Líquido"], "R$ 2.500,00")
        self.assertEqual(kpis["Estoque Central · Unidades"], "250")
        self.assertEqual(kpis["Venda Mês · Receita lançada"], "R$ 3.000,00")
        self.assertEqual(kpis["Aluguel · Despesa lançada"], "R$ 500,00")

        # 3. Remoção e atualização automática do Dashboard
        db.excluir_dado_geral(id_dg)
        db.excluir("convidados", id_cv)
        self.win.notificar_alteracao_dados()
        self._flush()
        kpis = self._mapa_kpis_dashboard()
        self.assertEqual(kpis["Total de Gastos"], "R$ 0,00")
        self.assertEqual(kpis["Rendimento Líquido"], "R$ 3.000,00")
        self.assertNotIn("Estoque Central · Unidades", kpis)
        self.assertNotIn("Aluguel · Despesa lançada", kpis)

    def test_configuracoes_e_comparativo_proprio_receita_dashboard(self):
        db.inserir_lote(
            "eventos",
            [
                {"data": "2025-11-10", "cliente": "Ano Ant", "local": "M", "convidados": 0, "valor": 2000.0, "status": "Confirmado"},
                {"data": "2026-05-10", "cliente": "Seis M", "local": "M", "convidados": 0, "valor": 1000.0, "status": "Confirmado"},
                {"data": "2026-10-15", "cliente": "Mes Ant", "local": "M", "convidados": 0, "valor": 1000.0, "status": "Confirmado"},
                {"data": "2026-11-15", "cliente": "Mes Atual", "local": "M", "convidados": 0, "valor": 1500.0, "status": "Confirmado"},
            ],
        )
        self.win.navegar_para("Dashboard")
        self._flush()
        kpis = self._mapa_kpis_dashboard()
        self.assertIn("Mês passado", kpis)
        self.assertIn("Últimos 30 dias", kpis)
        self.assertIn("6 meses atrás", kpis)
        self.assertIn("Ano passado", kpis)
        self.assertIn("+50,0%", kpis["Mês passado"])
        self.assertIn("-25,0%", kpis["Ano passado"])

        # Abre Configurações > Eficiência e ajusta alcance e checkboxes
        self.win.estado["tab_config"] = 1
        self.win.navegar_para("Configurações")
        self._flush()
        aba_efic = self._pagina().findChild(QTabWidget).widget(1)

        chks = {c.text(): c for c in aba_efic.findChildren(QCheckBox)}
        chk_ativo = chks["Ativar comparativo próprio de aumento/perda de receita no Dashboard"]
        chk_6m = chks["Mês recente vs. 6 meses atrás"]
        chk_ano = chks["Mês recente vs. Ano passado (12 meses atrás)"]
        self.assertTrue(chk_ativo.isChecked())
        self.assertTrue(chk_6m.isChecked())
        self.assertTrue(chk_ano.isChecked())

        # Desmarca Ano passado e limita alcance para 3 meses
        chk_ano.setChecked(False)
        combos = aba_efic.findChildren(QComboBox)
        cb_max = next(c for c in combos if c.findData(3) >= 0 and c.findData(12) >= 0)
        cb_max.setCurrentIndex(cb_max.findData(3))
        self._flush()
        self.assertFalse(chk_6m.isEnabled())
        self.assertFalse(chk_ano.isEnabled())

        btn_salvar = next(b for b in self._pagina().findChildren(QPushButton) if b.text() == "Salvar alterações")
        btn_salvar.click()
        self._flush()

        # Volta ao Dashboard e confirma que apenas Mês passado e Últimos 30 dias aparecem
        self.win.navegar_para("Dashboard")
        self._flush()
        kpis2 = self._mapa_kpis_dashboard()
        self.assertIn("Mês passado", kpis2)
        self.assertIn("Últimos 30 dias", kpis2)
        self.assertNotIn("6 meses atrás", kpis2)
        self.assertNotIn("Ano passado", kpis2)

        # Desativa comparativo próprio completamente
        self.win.estado["tab_config"] = 1
        self.win.navegar_para("Configurações")
        self._flush()
        aba_efic = self._pagina().findChild(QTabWidget).widget(1)
        chks = {c.text(): c for c in aba_efic.findChildren(QCheckBox)}
        chks["Ativar comparativo próprio de aumento/perda de receita no Dashboard"].setChecked(False)
        next(b for b in self._pagina().findChildren(QPushButton) if b.text() == "Salvar alterações").click()
        self._flush()

        self.win.navegar_para("Dashboard")
        self._flush()
        kpis3 = self._mapa_kpis_dashboard()
        self.assertNotIn("Mês passado", kpis3)
        self.assertNotIn("Últimos 30 dias", kpis3)

