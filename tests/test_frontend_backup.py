"""Fluxos de exportar/importar backup na tela Configurações > Segurança (PyQt6 offscreen).

Os diálogos modais são substituídos por respostas programadas; o banco é sempre temporário.
"""
import json
import os
from contextlib import closing

import pytest

try:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PyQt6.QtWidgets import QApplication
    _qt_app = QApplication.instance() or QApplication(["-platform", "offscreen"])
    from oneworld import frontend
    TEM_PYQT6 = True
except (ImportError, OSError):
    TEM_PYQT6 = False

from oneworld import backup as bkp
from oneworld import database as db

pytestmark = pytest.mark.skipif(not TEM_PYQT6, reason="PyQt6 ou bibliotecas de display indisponíveis")


def estado_do_banco():
    with closing(bkp._conectar_leitura()) as con:
        return bkp._ler_tabelas(con)


@pytest.fixture
def janela(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "teste.db")
    monkeypatch.setattr(db, "BACKUP_DIR", tmp_path / "backups")
    monkeypatch.setattr(frontend, "BACKUP_DIR", tmp_path / "backups")
    db.init_db()
    db.cfg_gravar("config", {"nome": "Empresa Original", "pagina_inicial": "Configurações"})
    db.cfg_gravar("campos_personalizados", ["Fornecedor"])
    db.executar("INSERT INTO eventos(data,cliente,extras) VALUES(?,?,?)", ("2026-11-10", "Festa Ana", "{}"))
    db.criar_anotacao("Nota", "texto", "2026-11-11")

    w = frontend.OneWorldWindow()
    w.mensagens = []
    w._mostrar_mensagem = lambda tipo, titulo, texto: w.mensagens.append((tipo, titulo, texto))
    yield w
    w.close()
    w.deleteLater()


@pytest.fixture
def arquivo_backup(janela, tmp_path):
    """Backup exportado do estado inicial, com nome e campos diferentes nas configurações."""
    destino = tmp_path / "backup.json"
    bkp.exportar(destino)
    dados = json.loads(destino.read_text(encoding="utf-8"))
    for reg in dados["tabelas"]["config"]:
        if reg["chave"] == "config":
            reg["valor"] = json.dumps({"nome": "Empresa do Backup", "pagina_inicial": "Configurações"})
        if reg["chave"] == "campos_personalizados":
            reg["valor"] = json.dumps(["Fornecedor", "CNPJ"])
    destino.write_text(json.dumps(dados, ensure_ascii=False), encoding="utf-8")
    return destino


def abrir_arquivo(monkeypatch, caminho):
    monkeypatch.setattr(frontend.QFileDialog, "getOpenFileName",
                        staticmethod(lambda *a, **k: (str(caminho) if caminho else "", "")))


def responder(janela, modo, confirmacoes):
    respostas = list(confirmacoes)
    janela.confirmacoes_pedidas = []
    janela._escolher_modo_importacao = lambda texto: modo

    def confirmar(titulo, texto, rotulo):
        janela.confirmacoes_pedidas.append(titulo)
        return respostas.pop(0)

    janela._confirmar = confirmar


def test_tela_seguranca_tem_os_controles(janela):
    from PyQt6.QtWidgets import QPushButton
    textos = {b.text() for b in janela.findChildren(QPushButton)}
    assert {"Fazer backup agora", "Exportar backup...", "Importar backup..."} <= textos


def test_exportar_pela_tela_acrescenta_extensao(janela, tmp_path, monkeypatch):
    monkeypatch.setattr(frontend.QFileDialog, "getSaveFileName",
                        staticmethod(lambda *a, **k: (str(tmp_path / "meu_backup"), "")))
    janela._exportar_backup()
    assert (tmp_path / "meu_backup.json").is_file()
    assert bkp.ler_backup(tmp_path / "meu_backup.json").contagens["eventos"] == 1
    assert janela.mensagens == []


def test_cancelar_escolha_do_arquivo(janela, arquivo_backup, monkeypatch):
    antes = estado_do_banco()
    abrir_arquivo(monkeypatch, None)
    janela._importar_backup()
    assert estado_do_banco() == antes


def test_cancelar_na_escolha_do_modo(janela, arquivo_backup, monkeypatch):
    antes = estado_do_banco()
    abrir_arquivo(monkeypatch, arquivo_backup)
    responder(janela, None, [])
    janela._importar_backup()
    assert estado_do_banco() == antes


def test_cancelar_confirmacao_de_substituir(janela, arquivo_backup, monkeypatch, tmp_path):
    antes = estado_do_banco()
    abrir_arquivo(monkeypatch, arquivo_backup)
    responder(janela, "substituir", [False])
    janela._importar_backup()
    assert janela.confirmacoes_pedidas == ["Substituir dados atuais"]
    assert estado_do_banco() == antes
    assert not (tmp_path / "backups").exists()  # nem a cópia de segurança foi feita


def test_cancelar_confirmacao_de_adicionar(janela, arquivo_backup, monkeypatch):
    antes = estado_do_banco()
    abrir_arquivo(monkeypatch, arquivo_backup)
    responder(janela, "mesclar", [False])
    janela._importar_backup()
    assert estado_do_banco() == antes


def test_cancelar_no_aviso_de_conflito_de_campos(janela, arquivo_backup, monkeypatch):
    dados = json.loads(arquivo_backup.read_text(encoding="utf-8"))
    for reg in dados["tabelas"]["config"]:
        if reg["chave"] == "campos_personalizados":
            reg["valor"] = json.dumps(["fornecedor", "CNPJ"])
    arquivo_backup.write_text(json.dumps(dados), encoding="utf-8")
    antes = estado_do_banco()
    abrir_arquivo(monkeypatch, arquivo_backup)
    responder(janela, "mesclar", [False])
    janela._importar_backup()
    assert janela.confirmacoes_pedidas == ["Campos personalizados em conflito"]
    assert estado_do_banco() == antes


def test_arquivo_invalido_mostra_mensagem(janela, tmp_path, monkeypatch):
    ruim = tmp_path / "ruim.json"
    ruim.write_text('{"formato": "outro"}', encoding="utf-8")
    antes = estado_do_banco()
    abrir_arquivo(monkeypatch, ruim)
    janela._importar_backup()
    assert janela.mensagens[0][1] == "Arquivo de backup inválido"
    assert "Nenhum dado foi alterado" in janela.mensagens[0][2]
    assert estado_do_banco() == antes


def test_erro_inesperado_vira_mensagem_sem_derrubar_o_app(janela, arquivo_backup, monkeypatch):
    antes = estado_do_banco()
    abrir_arquivo(monkeypatch, arquivo_backup)
    responder(janela, "substituir", [])

    def explodir():
        raise RuntimeError("falha imprevista")

    monkeypatch.setattr(bkp, "contagens_atuais", explodir)
    janela._importar_backup()
    assert janela.mensagens[-1][1] == "Erro inesperado na importação"
    assert estado_do_banco() == antes


def test_substituir_recarrega_estado_em_memoria(janela, arquivo_backup, monkeypatch):
    db.executar("INSERT INTO eventos(data,cliente,extras) VALUES(?,?,?)", ("2027-01-01", "Só no atual", "{}"))
    janela.cfg["nome"] = "Edição não salva"
    janela.estado["ev_busca"] = "filtro antigo"

    abrir_arquivo(monkeypatch, arquivo_backup)
    responder(janela, "substituir", [True])
    janela._importar_backup()

    assert janela.mensagens[-1][1] == "Backup restaurado"
    assert janela.cfg["nome"] == "Empresa do Backup"
    assert janela.campos_personalizados == ["Fornecedor", "CNPJ"]
    assert "ev_busca" not in janela.estado
    assert [e["cliente"] for e in estado_do_banco()["eventos"]] == ["Festa Ana"]
    # "Salvar alterações" depois da restauração grava o estado restaurado, não o antigo
    db.cfg_gravar("config", janela.cfg)
    assert db.cfg_ler("config", {})["nome"] == "Empresa do Backup"


def test_adicionar_apenas_o_que_falta_pela_tela(janela, arquivo_backup, monkeypatch):
    db.executar("DELETE FROM anotacoes")
    abrir_arquivo(monkeypatch, arquivo_backup)
    responder(janela, "mesclar", [True])
    janela._importar_backup()

    assert janela.mensagens[-1][1] == "Importação concluída"
    assert len(db.listar_anotacoes()) == 1
    assert len(estado_do_banco()["eventos"]) == 1  # já existia: ignorado
    assert janela.campos_personalizados == ["Fornecedor", "CNPJ"]
    assert janela.cfg["nome"] == "Empresa Original"  # configurações atuais mantidas

    # reimportar: nada a adicionar
    responder(janela, "mesclar", [])
    janela._importar_backup()
    assert janela.mensagens[-1][1] == "Nada a adicionar"
