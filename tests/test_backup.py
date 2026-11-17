"""Testes do backup completo em JSON (oneworld/backup.py). Usam somente bancos temporários."""
import copy
import json
import sqlite3
from contextlib import closing

import pytest

from oneworld import backup as bkp
from oneworld import database as db


@pytest.fixture(autouse=True)
def banco_temporario(tmp_path, monkeypatch):
    temp_db = tmp_path / "teste_oneworld.db"
    monkeypatch.setattr(db, "DB_PATH", temp_db)
    monkeypatch.setattr(db, "BACKUP_DIR", tmp_path / "backups")
    db.init_db()
    yield temp_db


# ── Auxiliares ──
def estado_do_banco():
    """Conteúdo completo das seis tabelas, com IDs, exatamente como gravado."""
    with closing(bkp._conectar_leitura()) as con:
        return bkp._ler_tabelas(con)


def inserir(tab, **valores):
    cols = list(valores)
    return db.executar(f"INSERT INTO {tab}({','.join(cols)}) VALUES({','.join('?' * len(cols))})",
                       [valores[c] for c in cols])


def popular():
    inserir("eventos", data="2026-11-10", cliente="Festa Ana", local="Salão A", convidados=50,
            valor=1500.5, status="Confirmado", extras=json.dumps({"Fornecedor": "Buffet X"}, ensure_ascii=False))
    inserir("eventos", data="2026-12-01", cliente="Pedido 42", local="Loja", convidados=3,
            valor=99, status="Pendente", extras="{}")
    inserir("convidados", evento="Festa Ana", nome="Bia", mesa="1", acompanhantes=2, contato="bia@x",
            restricao="", confirmacao="Confirmado", extras=json.dumps({"Fornecedor": ""}))
    inserir("convidados", evento="Festa Ana", nome="Caio", mesa=None, acompanhantes=0, contato=None,
            restricao="Vegano", confirmacao="Pendente", extras="{}")
    inserir("convidados", evento="Pedido 42", nome="Item avulso", mesa="B", acompanhantes=1, contato="",
            restricao=None, confirmacao="Recusou", extras="{}")
    db.criar_anotacao("Ligar fornecedor", "Confirmar cardápio", "2026-11-05")
    db.executar("INSERT INTO relatorios_ia(data,pergunta,resposta) VALUES(?,?,?)",
                ("17/11/2026 10:00", "Qual o total?", "R$ 1.599,50"))
    db.registrar_arquivo("vendas.csv", "convidados", 3, "Importado")
    db.cfg_gravar("config", {"nome": "Minha Empresa", "tema": "Escuro", "linhas": 20})
    db.cfg_gravar("campos_personalizados", ["Fornecedor"])
    db.cfg_gravar("llm", {"modelo": "anthropic/claude", "max_tokens": 900})


def exportar_dict(tmp_path, nome="bkp.json"):
    destino = tmp_path / nome
    bkp.exportar(destino)
    return json.loads(destino.read_text(encoding="utf-8"))


def gravar_dict(tmp_path, dados, nome="editado.json"):
    p = tmp_path / nome
    p.write_text(json.dumps(dados, ensure_ascii=False), encoding="utf-8")
    return p


# ── Exportação ──
def test_exportar_gera_json_completo(tmp_path):
    popular()
    antes = estado_do_banco()
    destino = tmp_path / "saida" / "meu_backup.json"
    destino.parent.mkdir()
    res = bkp.exportar(destino)

    dados = json.loads(destino.read_text(encoding="utf-8"))
    assert dados["formato"] == "oneworld-backup"
    assert dados["aplicativo"] == "OneWorld"
    assert dados["versao_formato"] == 1
    assert dados["gerado_em"]
    assert set(dados["tabelas"]) == {"eventos", "convidados", "anotacoes", "relatorios_ia", "arquivos", "config"}
    assert dados["contagens"] == {t: len(antes[t]) for t in bkp.TABELAS} == res.contagens
    # valores e extras preservados exatamente (texto original do banco)
    assert dados["tabelas"]["eventos"] == antes["eventos"]
    assert dados["tabelas"]["convidados"] == antes["convidados"]
    assert dados["tabelas"]["eventos"][0]["extras"] == '{"Fornecedor": "Buffet X"}'
    assert dados["tabelas"]["eventos"][1]["valor"] == 99
    # nenhum arquivo temporário restante
    assert [p.name for p in destino.parent.iterdir()] == ["meu_backup.json"]


def test_exportar_omite_segredos_mas_mantem_preferencias(tmp_path):
    popular()
    db.cfg_gravar("llm", {"modelo": "openai/gpt", "max_tokens": 500, "api_key": "sk-SEGREDO", "chave": "x"})
    db.cfg_gravar("openai_api_key", "sk-OUTRO")
    destino = tmp_path / "b.json"
    res = bkp.exportar(destino)
    texto = destino.read_text(encoding="utf-8")
    assert "sk-SEGREDO" not in texto and "sk-OUTRO" not in texto
    assert res.segredos_removidos == 3
    llm = next(json.loads(r["valor"]) for r in json.loads(texto)["tabelas"]["config"] if r["chave"] == "llm")
    assert llm == {"modelo": "openai/gpt", "max_tokens": 500}


def test_exportar_falha_na_gravacao_nao_deixa_arquivo_incompleto(tmp_path, monkeypatch):
    popular()
    destino = tmp_path / "existente.json"
    destino.write_text("conteúdo anterior", encoding="utf-8")

    def falhar(*_a, **_k):
        raise OSError(28, "Sem espaço em disco")

    monkeypatch.setattr(bkp.os, "replace", falhar)
    with pytest.raises(bkp.BackupErro, match="Nenhum arquivo foi criado ou alterado"):
        bkp.exportar(destino)
    assert destino.read_text(encoding="utf-8") == "conteúdo anterior"
    assert not list(tmp_path.glob("*.tmp"))


def test_exportar_pasta_inexistente(tmp_path):
    with pytest.raises(bkp.BackupErro, match="pasta de destino não existe"):
        bkp.exportar(tmp_path / "nao_existe" / "b.json")


def test_exportar_e_importar_registros_com_extras_nulos(tmp_path):
    inserir("eventos", data="2026-01-01", cliente="Sem extras", extras=None)
    dados = exportar_dict(tmp_path)
    assert dados["tabelas"]["eventos"][0]["extras"] is None
    backup = bkp.ler_backup(tmp_path / "bkp.json")
    bkp.substituir(backup)
    assert estado_do_banco()["eventos"][0]["extras"] is None


# ── Substituir ──
def test_substituir_restaura_tudo_exatamente(tmp_path):
    popular()
    original = estado_do_banco()
    bkp.exportar(tmp_path / "b.json")

    # banco muda depois do backup
    db.excluir("eventos", 1)
    inserir("eventos", data="2027-01-01", cliente="Novo", extras="{}")
    db.cfg_gravar("config", {"nome": "Outro nome"})
    db.cfg_gravar("campos_personalizados", ["CNPJ"])
    mudado = estado_do_banco()

    backup = bkp.ler_backup(tmp_path / "b.json")
    res = bkp.substituir(backup)

    assert estado_do_banco() == original  # IDs, valores, extras e configurações idênticos
    assert res.modo == "substituir"
    # a cópia de segurança contém o estado anterior à restauração
    assert res.copia_seguranca.is_file()
    with closing(sqlite3.connect(res.copia_seguranca)) as con:
        clientes = [r[0] for r in con.execute("SELECT cliente FROM eventos ORDER BY id")]
    assert clientes == [e["cliente"] for e in mudado["eventos"]]


def test_substituir_preserva_ids_e_vinculos(tmp_path):
    popular()
    dados = exportar_dict(tmp_path)
    # IDs esparsos no backup
    for novo_id, ev in zip((10, 25), dados["tabelas"]["eventos"]):
        ev["id"] = novo_id
    for novo_id, cv in zip((7, 8, 99), dados["tabelas"]["convidados"]):
        cv["id"] = novo_id
    backup = bkp.ler_backup(gravar_dict(tmp_path, dados))
    bkp.substituir(backup)

    estado = estado_do_banco()
    assert [e["id"] for e in estado["eventos"]] == [10, 25]
    assert [c["id"] for c in estado["convidados"]] == [7, 8, 99]
    nomes_eventos = {e["cliente"] for e in estado["eventos"]}
    assert all(c["evento"] in nomes_eventos for c in estado["convidados"])
    assert db.contar_convidados_do_evento("Festa Ana") == 2


def test_substituir_atualiza_configuracoes_lidas_pelo_app(tmp_path):
    popular()
    bkp.exportar(tmp_path / "b.json")
    db.cfg_gravar("config", {"nome": "Alterado"})
    db.cfg_gravar("campos_personalizados", [])
    bkp.substituir(bkp.ler_backup(tmp_path / "b.json"))
    assert db.cfg_ler("config", {})["nome"] == "Minha Empresa"
    assert db.cfg_ler("campos_personalizados", []) == ["Fornecedor"]
    assert db.cfg_ler("llm", {}) == {"modelo": "anthropic/claude", "max_tokens": 900}


def test_falha_na_copia_de_seguranca_interrompe_sem_alterar(tmp_path, monkeypatch):
    popular()
    bkp.exportar(tmp_path / "b.json")
    backup = bkp.ler_backup(tmp_path / "b.json")
    db.cfg_gravar("config", {"nome": "Estado atual"})
    antes = estado_do_banco()

    bloqueio = tmp_path / "um_arquivo"
    bloqueio.write_text("não é pasta", encoding="utf-8")
    monkeypatch.setattr(db, "BACKUP_DIR", bloqueio)  # mkdir falha: o caminho é um arquivo
    with pytest.raises(bkp.CopiaSegurancaFalhou, match="nenhum dado foi alterado"):
        bkp.substituir(backup)
    assert estado_do_banco() == antes


def test_erro_durante_substituicao_desfaz_tudo(tmp_path, monkeypatch):
    popular()
    bkp.exportar(tmp_path / "b.json")
    backup = bkp.ler_backup(tmp_path / "b.json")
    inserir("eventos", data="2027-02-02", cliente="Só no banco atual", extras="{}")
    antes = estado_do_banco()

    original = bkp._gravar_tabela

    def gravar_com_falha(con, tab, regs, com_id):
        if tab == "arquivos":  # eventos, convidados, anotações e relatórios já foram apagados e regravados
            raise sqlite3.OperationalError("disco cheio (simulado)")
        original(con, tab, regs, com_id)

    monkeypatch.setattr(bkp, "_gravar_tabela", gravar_com_falha)
    with pytest.raises(bkp.BackupErro, match="foi desfeita"):
        bkp.substituir(backup)
    assert estado_do_banco() == antes


# ── Adicionar apenas o que falta ──
def test_reimportar_o_mesmo_backup_nao_duplica(tmp_path):
    popular()
    bkp.exportar(tmp_path / "b.json")
    backup = bkp.ler_backup(tmp_path / "b.json")
    antes = estado_do_banco()

    res = bkp.aplicar_mesclagem(backup)
    assert sum(res.adicionados.values()) == 0
    assert res.ignorados == {t: len(antes[t]) for t in bkp.TABELAS_DADOS}
    assert estado_do_banco() == antes

    # e de novo: continua sem duplicar
    res2 = bkp.aplicar_mesclagem(backup)
    assert sum(res2.adicionados.values()) == 0
    assert estado_do_banco() == antes


def test_mesclar_em_banco_vazio_e_reimportar(tmp_path):
    popular()
    bkp.exportar(tmp_path / "b.json")
    original = estado_do_banco()
    for tab in bkp.TABELAS_DADOS:
        db.executar(f"DELETE FROM {tab}")

    backup = bkp.ler_backup(tmp_path / "b.json")
    res = bkp.aplicar_mesclagem(backup)
    assert res.adicionados == {t: len(original[t]) for t in bkp.TABELAS_DADOS}

    res2 = bkp.aplicar_mesclagem(backup)
    assert sum(res2.adicionados.values()) == 0
    assert sum(res2.ignorados.values()) == sum(len(original[t]) for t in bkp.TABELAS_DADOS)


def test_mesclar_com_colisao_de_ids_gera_novos_ids(tmp_path):
    popular()
    dados = exportar_dict(tmp_path)
    for tab in bkp.TABELAS_DADOS:
        db.executar(f"DELETE FROM {tab}")
    # banco atual com registros DIFERENTES usando os mesmos IDs do backup
    inserir("eventos", id=1, data="2030-01-01", cliente="Atual 1", extras="{}")
    inserir("eventos", id=2, data="2030-01-02", cliente="Atual 2", extras="{}")
    antes = estado_do_banco()

    res = bkp.aplicar_mesclagem(bkp.ler_backup(gravar_dict(tmp_path, dados)))
    depois = estado_do_banco()
    assert res.adicionados["eventos"] == 2
    assert depois["eventos"][:2] == antes["eventos"]  # registros atuais intactos
    novos = depois["eventos"][2:]
    assert [e["id"] for e in novos] == [3, 4]
    assert [e["cliente"] for e in novos] == ["Festa Ana", "Pedido 42"]
    assert novos[0]["extras"] == dados["tabelas"]["eventos"][0]["extras"]


def test_mesclar_respeita_quantidade_de_ocorrencias(tmp_path):
    nota = {"titulo": "Repetida", "descricao": "igual", "data": "2026-01-01"}
    db.criar_anotacao(**{"titulo": nota["titulo"], "descricao": nota["descricao"], "data_iso": nota["data"]})
    dados = exportar_dict(tmp_path)
    dados["tabelas"]["anotacoes"] = [{"id": i, **nota} for i in (1, 2, 3)]
    dados["contagens"]["anotacoes"] = 3
    backup = bkp.ler_backup(gravar_dict(tmp_path, dados))

    plano = bkp.planejar_mesclagem(backup)
    assert plano.contagem_adicionar["anotacoes"] == 2 and plano.ignorados["anotacoes"] == 1

    res = bkp.aplicar_mesclagem(backup)
    assert res.adicionados["anotacoes"] == 2
    assert len(db.listar_anotacoes()) == 3
    assert bkp.aplicar_mesclagem(backup).adicionados["anotacoes"] == 0


@pytest.mark.parametrize("alteracao, ja_existe", [
    ({"valor": 1200.0, "convidados": 10.0}, True),                  # números equivalentes
    ({"extras": '{"a":"x","b":1.0}'}, True),                        # ordem das chaves, formatação e 1 == 1.0
    ({"cliente": "Ana "}, False),                                   # espaço no fim conta
    ({"cliente": " Ana"}, False),                                   # espaço no início conta
    ({"cliente": "ANA"}, False),                                    # maiúsculas contam
    ({"local": ""}, False),                                         # texto vazio não é NULL
    ({"extras": '{"a": "x", "b": 2}'}, False),                      # extras diferentes
    ({"extras": '{"a": "x"}'}, False),                              # extras com menos chaves
], ids=["numeros", "extras_reordenados", "espaco_fim", "espaco_inicio", "maiusculas", "vazio_vs_null",
        "extras_diferentes", "extras_incompletos"])
def test_mesclar_normaliza_apenas_equivalencias_seguras(tmp_path, alteracao, ja_existe):
    inserir("eventos", data="2026-05-05", cliente="Ana", local=None, convidados=10, valor=1200,
            status="Confirmado", extras='{"b": 1, "a": "x"}')
    dados = exportar_dict(tmp_path)
    variante = {**dados["tabelas"]["eventos"][0], "id": 50, **alteracao}
    dados["tabelas"]["eventos"] = [variante]
    backup = bkp.ler_backup(gravar_dict(tmp_path, dados))

    res = bkp.aplicar_mesclagem(backup)
    assert res.ignorados["eventos"] == (1 if ja_existe else 0)
    assert res.adicionados["eventos"] == (0 if ja_existe else 1)
    if not ja_existe:  # o registro novo é gravado exatamente como no backup
        novo = estado_do_banco()["eventos"][-1]
        assert {k: novo[k] for k in alteracao} == alteracao


def test_mesclar_preserva_texto_exato_dos_vinculos(tmp_path):
    dados = exportar_dict(tmp_path)
    dados["tabelas"]["eventos"] = [{"id": 1, "data": "2026-01-01", "cliente": "  Festa  da Ana ", "local": None,
                                    "convidados": 0, "valor": 0, "status": None, "extras": "{}"}]
    dados["tabelas"]["convidados"] = [{"id": 1, "evento": "  Festa  da Ana ", "nome": "Bia", "mesa": None,
                                       "acompanhantes": 0, "contato": None, "restricao": None,
                                       "confirmacao": None, "extras": "{}"}]
    dados["contagens"].update(eventos=1, convidados=1)
    bkp.aplicar_mesclagem(bkp.ler_backup(gravar_dict(tmp_path, dados)))
    estado = estado_do_banco()
    assert estado["convidados"][0]["evento"] == estado["eventos"][0]["cliente"] == "  Festa  da Ana "
    assert db.contar_convidados_do_evento("  Festa  da Ana ") == 1


def test_mesclar_mantem_configuracoes_e_une_campos(tmp_path):
    popular()
    dados = exportar_dict(tmp_path)
    for reg in dados["tabelas"]["config"]:
        if reg["chave"] == "config":
            reg["valor"] = json.dumps({"nome": "Nome do backup", "tema": "Claro"})
        if reg["chave"] == "campos_personalizados":
            reg["valor"] = json.dumps(["Fornecedor", "CNPJ", "Centro de Custo"])
    db.cfg_gravar("campos_personalizados", ["Fornecedor", "Prazo"])

    res = bkp.aplicar_mesclagem(bkp.ler_backup(gravar_dict(tmp_path, dados)))
    assert res.campos_adicionados == ["CNPJ", "Centro de Custo"]
    assert db.cfg_ler("campos_personalizados", []) == ["Fornecedor", "Prazo", "CNPJ", "Centro de Custo"]
    cfg = db.cfg_ler("config", {})
    assert cfg["nome"] == "Minha Empresa" and cfg["tema"] == "Escuro"  # configurações atuais mantidas


def test_mesclar_aponta_conflitos_de_campos_sem_descartar_dados(tmp_path):
    db.cfg_gravar("campos_personalizados", ["Fornecedor"])
    dados = exportar_dict(tmp_path)
    for reg in dados["tabelas"]["config"]:
        if reg["chave"] == "campos_personalizados":
            reg["valor"] = json.dumps(["fornecedor ", "Valor", "CNPJ"])
    extras = json.dumps({"fornecedor ": "Buffet Y", "Valor": "abc", "CNPJ": "123"}, ensure_ascii=False)
    dados["tabelas"]["eventos"] = [{"id": 1, "data": "2026-01-01", "cliente": "X", "local": None,
                                    "convidados": 0, "valor": 0, "status": None, "extras": extras}]
    dados["contagens"]["eventos"] = 1
    backup = bkp.ler_backup(gravar_dict(tmp_path, dados))

    plano = bkp.planejar_mesclagem(backup)
    assert [c.nome for c in plano.conflitos] == ["fornecedor ", "Valor"]
    assert "Fornecedor" in plano.conflitos[0].motivo
    assert "coluna padrão" in plano.conflitos[1].motivo
    assert plano.campos_novos == ["CNPJ"]

    res = bkp.aplicar_mesclagem(backup)
    assert db.cfg_ler("campos_personalizados", []) == ["Fornecedor", "CNPJ"]
    assert [c.nome for c in res.conflitos] == ["fornecedor ", "Valor"]
    assert estado_do_banco()["eventos"][0]["extras"] == extras  # valores gravados exatamente


def test_erro_durante_mesclagem_desfaz_tudo(tmp_path, monkeypatch):
    popular()
    bkp.exportar(tmp_path / "b.json")
    for tab in bkp.TABELAS_DADOS:
        db.executar(f"DELETE FROM {tab}")
    db.cfg_gravar("campos_personalizados", [])
    backup = bkp.ler_backup(tmp_path / "b.json")
    antes = estado_do_banco()

    original = bkp._gravar_tabela

    def gravar_com_falha(con, tab, regs, com_id):
        if tab == "anotacoes":  # eventos e convidados já inseridos nesta transação
            raise sqlite3.OperationalError("falha simulada")
        original(con, tab, regs, com_id)

    monkeypatch.setattr(bkp, "_gravar_tabela", gravar_com_falha)
    with pytest.raises(bkp.BackupErro, match="nenhum dado foi alterado"):
        bkp.aplicar_mesclagem(backup)
    assert estado_do_banco() == antes


def test_previa_e_leitura_nao_alteram_o_banco(tmp_path):
    """Equivale a cancelar depois de ver o resumo: nada pode ter sido gravado."""
    popular()
    bkp.exportar(tmp_path / "b.json")
    inserir("eventos", data="2027-03-03", cliente="Extra", extras="{}")
    antes = estado_do_banco()
    conteudo_db = db.DB_PATH.read_bytes()

    backup = bkp.ler_backup(tmp_path / "b.json")
    bkp.planejar_mesclagem(backup)
    bkp.contagens_atuais()
    assert estado_do_banco() == antes
    assert db.DB_PATH.read_bytes() == conteudo_db
    assert not db.BACKUP_DIR.exists()


# ── Arquivos inválidos ──
def _mutacoes():
    def tabela(t):
        return lambda d: d["tabelas"][t]

    def m(nome, func):
        return pytest.param(func, id=nome)

    return [
        m("formato_errado", lambda d: d.update(formato="outro-app")),
        m("aplicativo_errado", lambda d: d.update(aplicativo="Outro")),
        m("versao_futura", lambda d: d.update(versao_formato=2)),
        m("versao_texto", lambda d: d.update(versao_formato="1")),
        m("data_invalida", lambda d: d.update(gerado_em="ontem")),
        m("chave_desconhecida", lambda d: d.update(extra=1)),
        m("sem_contagens", lambda d: d.pop("contagens")),
        m("contagem_divergente", lambda d: d["contagens"].update(eventos=99)),
        m("tabela_faltando", lambda d: d["tabelas"].pop("anotacoes")),
        m("tabela_desconhecida", lambda d: d["tabelas"].update(usuarios=[])),
        m("tabela_nao_lista", lambda d: d["tabelas"].update(eventos={})),
        m("coluna_faltando", lambda d: tabela("eventos")(d)[0].pop("valor")),
        m("coluna_desconhecida", lambda d: tabela("eventos")(d)[0].update(senha="x")),
        m("numero_como_texto", lambda d: tabela("eventos")(d)[0].update(valor="mil")),
        m("texto_como_numero", lambda d: tabela("convidados")(d)[0].update(nome=123)),
        m("id_booleano", lambda d: tabela("eventos")(d)[0].update(id=True)),
        m("id_negativo", lambda d: tabela("eventos")(d)[0].update(id=-1)),
        m("id_repetido", lambda d: tabela("eventos")(d)[1].update(id=tabela("eventos")(d)[0]["id"])),
        m("extras_json_invalido", lambda d: tabela("eventos")(d)[0].update(extras="{quebrado")),
        m("extras_nao_objeto", lambda d: tabela("eventos")(d)[0].update(extras="[1, 2]")),
        m("config_valor_invalido", lambda d: tabela("config")(d)[0].update(valor="{nao json")),
        m("config_chave_repetida", lambda d: tabela("config")(d).append(dict(tabela("config")(d)[0]))),
        m("campos_nao_lista", lambda d: [r.update(valor='"Fornecedor"') for r in tabela("config")(d)
                                         if r["chave"] == "campos_personalizados"]),
        m("campos_repetidos", lambda d: [r.update(valor='["A", "A"]') for r in tabela("config")(d)
                                         if r["chave"] == "campos_personalizados"]),
        m("opcao_com_tipo_errado", lambda d: [r.update(valor='{"linhas": "dez"}') for r in tabela("config")(d)
                                              if r["chave"] == "config"]),
    ]


@pytest.mark.parametrize("mutar", _mutacoes())
def test_arquivo_invalido_e_rejeitado_sem_alterar_banco(tmp_path, mutar):
    popular()
    dados = exportar_dict(tmp_path)
    antes = estado_do_banco()
    ruim = copy.deepcopy(dados)
    mutar(ruim)
    with pytest.raises(bkp.BackupInvalido):
        bkp.ler_backup(gravar_dict(tmp_path, ruim))
    assert estado_do_banco() == antes


@pytest.mark.parametrize("conteudo", [
    b"",
    b"isto nao e json",
    b"[1, 2, 3]",
    b'{"formato": "oneworld-backup", "formato": "oneworld-backup"}',
    b'{"formato": "oneworld-backup", "valor": NaN}',
    "{\"formato\": \"oneworld-backup\"}".encode("utf-16"),
], ids=["vazio", "texto", "lista", "chave_duplicada", "nan", "utf16"])
def test_conteudo_bruto_invalido(tmp_path, conteudo):
    p = tmp_path / "ruim.json"
    p.write_bytes(conteudo)
    with pytest.raises(bkp.BackupInvalido):
        bkp.ler_backup(p)


def test_arquivo_inexistente(tmp_path):
    with pytest.raises(bkp.BackupInvalido, match="não encontrado"):
        bkp.ler_backup(tmp_path / "nao_existe.json")
