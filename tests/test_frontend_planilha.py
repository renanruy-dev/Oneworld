"""Seção "Planilha padrão e IA externa" (página Orientação IA), em PyQt6 offscreen.
Diálogos modais são substituídos por respostas programadas; banco e arquivos são temporários."""
import os
import sqlite3
from contextlib import closing

import pytest
from openpyxl import load_workbook

try:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PyQt6.QtWidgets import QApplication, QPushButton
    _qt_app = QApplication.instance() or QApplication(["-platform", "offscreen"])
    from oneworld import frontend
    TEM_PYQT6 = True
except (ImportError, OSError):
    TEM_PYQT6 = False

from oneworld import database as db
from oneworld import planilha_padrao as pp

pytestmark = pytest.mark.skipif(not TEM_PYQT6, reason="PyQt6 ou bibliotecas de display indisponíveis")


def estado():
    with closing(sqlite3.connect(db.DB_PATH)) as con:
        return {t: con.execute(f"SELECT * FROM {t} ORDER BY 1").fetchall()
                for t in ("eventos", "convidados", "anotacoes", "arquivos")}


@pytest.fixture
def janela(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "teste.db")
    monkeypatch.setattr(db, "BACKUP_DIR", tmp_path / "backups")
    monkeypatch.setattr(frontend, "BACKUP_DIR", tmp_path / "backups")
    db.init_db()
    db.cfg_gravar("config", {"pagina_inicial": "Orientação IA"})
    db.executar("INSERT INTO eventos(data,cliente,local,convidados,valor,status,extras) VALUES(?,?,?,?,?,?,?)",
                ("2026-11-10", "Festa Ana", "Salão", 50, 1500, "Confirmado", "{}"))
    db.executar("INSERT INTO convidados(evento,nome,acompanhantes,confirmacao,extras) VALUES(?,?,?,?,?)",
                ("Festa Ana", "Bia", 0, "Confirmado", "{}"))
    w = frontend.OneWorldWindow()
    w.mensagens, w.confirmacoes = [], []
    w._mostrar_mensagem = lambda tipo, titulo, texto: w.mensagens.append((tipo, titulo, texto))
    yield w
    w.close()
    w.deleteLater()


def salvar_em(monkeypatch, caminho):
    monkeypatch.setattr(frontend.QFileDialog, "getSaveFileName", staticmethod(lambda *a, **k: (str(caminho), "")))


def abrir(monkeypatch, caminho):
    monkeypatch.setattr(frontend.QFileDialog, "getOpenFileName",
                        staticmethod(lambda *a, **k: (str(caminho) if caminho else "", "")))


def confirmar_sempre(janela, resposta=True):
    def confirmar(titulo, texto, rotulo):
        janela.confirmacoes.append(titulo)
        return resposta
    janela._confirmar = confirmar


def planilha_editada(janela, tmp_path, monkeypatch):
    confirmar_sempre(janela)
    salvar_em(monkeypatch, tmp_path / "edicao")
    janela._exportar_planilha_padrao(pp.TIPO_EDICAO)
    p = tmp_path / "edicao.xlsx"
    wb = load_workbook(p)
    ws = wb["Operacoes"]
    cols = {c.value: c.column for c in ws[1]}
    ws.cell(row=2, column=cols["local"]).value = "Salão novo"
    ws.cell(row=3, column=cols["data"]).value = "2027-01-01"
    ws.cell(row=3, column=cols["cliente"]).value = "Evento novo"
    ws.cell(row=3, column=cols["status"]).value = "Pendente"
    wb.save(p)
    return p


def _aba_ia(janela, titulo):
    from PyQt6.QtWidgets import QTabWidget
    abas = next(a for a in janela.findChildren(QTabWidget) if a.count() == 4)
    i = next(i for i in range(abas.count()) if abas.tabText(i) == titulo)
    return abas, abas.widget(i)


def test_pagina_organizada_em_abas(janela):
    from PyQt6.QtWidgets import QTabWidget
    abas = next(a for a in janela.findChildren(QTabWidget) if a.count() == 4)
    assert [abas.tabText(i) for i in range(4)] == [
        "Perguntar aos dados", "Atualizar dados com IA externa", "Pedir análise à IA externa", "Exportar Markdown"]
    assert "Baixar Markdown" in {b.text() for b in abas.widget(3).findChildren(QPushButton)}
    assert "Perguntar" in {b.text() for b in abas.widget(0).findChildren(QPushButton)}


def test_aba_atualizar_tem_passo_a_passo_e_botoes(janela):
    from PyQt6.QtWidgets import QLabel
    _, aba = _aba_ia(janela, "Atualizar dados com IA externa")
    textos = " ".join(lbl.text() for lbl in aba.findChildren(QLabel))
    for trecho in ("Escolha o que vai na planilha", "Baixe a planilha para edição", "Copie o prompt de preenchimento",
                   "Envie à IA e baixe o arquivo devolvido", "Importe o arquivo devolvido", ".xlsx", "download"):
        assert trecho in textos, trecho
    botoes = [b.text() for b in aba.findChildren(QPushButton)]
    assert botoes == ["Exportar planilha para edição...", "Baixar modelo vazio...", "Copiar prompt de preenchimento",
                      "Importar planilha preenchida..."]


def test_aba_analise_tem_passos_e_botoes(janela):
    _, aba = _aba_ia(janela, "Pedir análise à IA externa")
    assert [b.text() for b in aba.findChildren(QPushButton)] == [
        "Exportar planilha para análise...", "Copiar prompt de análise"]


def test_aba_continua_selecionada_apos_acao(janela):
    abas, _ = _aba_ia(janela, "Atualizar dados com IA externa")
    abas.setCurrentIndex(1)
    janela._copiar_prompt_preenchimento()  # copia, mostra aviso e reconstrói a página
    abas2, _ = _aba_ia(janela, "Atualizar dados com IA externa")
    assert abas2.currentIndex() == 1


def test_selecao_de_tabelas_independente_por_aba(janela):
    janela._estado_planilha(pp.TIPO_EDICAO)["tabelas"] = ["eventos"]
    assert janela._estado_planilha(pp.TIPO_ANALISE)["tabelas"] == ["eventos", "convidados"]


def test_exportar_para_analise_sem_confirmacao(janela, tmp_path, monkeypatch):
    salvar_em(monkeypatch, tmp_path / "analise")
    janela._exportar_planilha_padrao(pp.TIPO_ANALISE)
    assert (tmp_path / "analise.xlsx").is_file() and janela.confirmacoes == []
    with pytest.raises(pp.PlanilhaInvalida):
        pp.ler_planilha_padrao(tmp_path / "analise.xlsx")


def test_exportar_para_edicao_pede_confirmacao_e_cancelar_nao_gera_arquivo(janela, tmp_path, monkeypatch):
    confirmar_sempre(janela, False)
    salvar_em(monkeypatch, tmp_path / "edicao.xlsx")
    janela._exportar_planilha_padrao(pp.TIPO_EDICAO)
    assert janela.confirmacoes == ["Exportar planilha para edição"]
    assert not (tmp_path / "edicao.xlsx").exists()


def test_modelo_vazio(janela, tmp_path, monkeypatch):
    salvar_em(monkeypatch, tmp_path / "modelo.xlsx")
    janela._exportar_modelo_vazio()
    wb = load_workbook(tmp_path / "modelo.xlsx")
    assert wb["Operacoes"]["A2"].value is None and "Dicionario" in wb.sheetnames


def test_copiar_prompts_conforme_tabelas(janela):
    janela._estado_planilha(pp.TIPO_ANALISE)["tabelas"] = ["eventos"]
    janela._estado_planilha(pp.TIPO_EDICAO)["tabelas"] = ["eventos"]
    janela._copiar_prompt_analise()
    texto = QApplication.clipboard().text()
    assert "Operacoes" in texto and "Cadastros" not in texto
    janela._copiar_prompt_preenchimento()
    assert "id_oneworld" in QApplication.clipboard().text()


def test_cancelar_na_previa_nao_altera(janela, tmp_path, monkeypatch):
    p = planilha_editada(janela, tmp_path, monkeypatch)
    antes = estado()
    abrir(monkeypatch, p)
    janela.planos = []
    janela._revisar_importacao_planilha = lambda plano: janela.planos.append(plano) or False
    janela._importar_planilha_padrao()
    assert len(janela.planos[0].inclusoes) == 1 and len(janela.planos[0].alteracoes) == 1
    assert estado() == antes


def test_confirmar_grava_e_informa(janela, tmp_path, monkeypatch):
    p = planilha_editada(janela, tmp_path, monkeypatch)
    abrir(monkeypatch, p)
    janela._revisar_importacao_planilha = lambda plano: True
    janela._importar_planilha_padrao()
    assert janela.mensagens[-1][1] == "Planilha importada"
    ev = estado()["eventos"]
    assert ev[0][3] == "Salão novo" and ev[1][2] == "Evento novo"
    assert estado()["arquivos"][-1][2] == "Planilha padrão (IA externa)"


def test_arquivo_invalido_mostra_problemas(janela, tmp_path, monkeypatch):
    salvar_em(monkeypatch, tmp_path / "analise.xlsx")
    janela._exportar_planilha_padrao(pp.TIPO_ANALISE)
    abrir(monkeypatch, tmp_path / "analise.xlsx")
    janela._importar_planilha_padrao()
    assert janela.mensagens[-1][1] == "Planilha não pode ser importada"
    assert "Nenhum dado foi alterado" in janela.mensagens[-1][2]


def test_dialogo_de_previa_bloqueia_confirmacao_com_erro(janela, tmp_path, monkeypatch):
    p = planilha_editada(janela, tmp_path, monkeypatch)
    wb = load_workbook(p)
    ws = wb["Operacoes"]
    cols = {c.value: c.column for c in ws[1]}
    ws.cell(row=3, column=cols["status"]).value = "pendente"  # valor fora da lista
    wb.save(p)
    plano = pp.planejar_importacao(pp.ler_planilha_padrao(p))
    dlg = janela._criar_dialogo_previa(plano)
    assert not dlg.botao_confirmar.isEnabled()
    plano_ok = pp.planejar_importacao(pp.ler_planilha_padrao(planilha_editada(janela, tmp_path, monkeypatch)))
    assert janela._criar_dialogo_previa(plano_ok).botao_confirmar.isEnabled()
