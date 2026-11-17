"""Testes da planilha padrão e do fluxo manual com IA externa (oneworld/planilha_padrao.py).
Usam somente bancos e arquivos temporários."""
import json
import sqlite3
from contextlib import closing
from datetime import date, datetime

import pytest
from openpyxl import Workbook, load_workbook

from oneworld import database as db
from oneworld import planilha_padrao as pp


@pytest.fixture(autouse=True)
def banco_temporario(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "teste.db")
    monkeypatch.setattr(db, "BACKUP_DIR", tmp_path / "backups")
    db.init_db()
    yield


# ── Auxiliares ──
def inserir(tab, **valores):
    cols = list(valores)
    return db.executar(f"INSERT INTO {tab}({','.join(cols)}) VALUES({','.join('?' * len(cols))})",
                       [valores[c] for c in cols])


def popular():
    db.cfg_gravar("campos_personalizados", ["Fornecedor"])
    inserir("eventos", data="2026-11-10", cliente="Festa Ana", local="Salão A", convidados=50, valor=1500.0,
            status="Confirmado", extras=json.dumps({"Fornecedor": "Buffet X", "Antigo": "valor órfão"}))
    inserir("eventos", data="2026-12-05", cliente="Pedido 42", local="Loja", convidados=3, valor=99.9,
            status="Pendente", extras="{}")
    inserir("eventos", data="2027-01-15", cliente="Reunião", local=None, convidados=0, valor=0,
            status="Em planejamento", extras="{}")
    inserir("convidados", evento="Festa Ana", nome="Bia", mesa="007", acompanhantes=1, contato="011999990000",
            restricao="Vegana", confirmacao="Confirmado", extras="{}")
    inserir("convidados", evento="Festa Ana", nome="Caio", mesa="2", acompanhantes=0, contato=None,
            restricao=None, confirmacao="Pendente", extras="{}")
    inserir("convidados", evento="Pedido 42", nome="Item avulso", mesa=None, acompanhantes=0, contato="",
            restricao="—", confirmacao="Recusou", extras="{}")
    db.criar_anotacao("Ligar fornecedor", "Confirmar cardápio", "2026-11-20")


def estado():
    with closing(sqlite3.connect(db.DB_PATH)) as con:
        return {t: con.execute(f"SELECT * FROM {t} ORDER BY 1").fetchall()
                for t in ("eventos", "convidados", "anotacoes", "arquivos", "config")}


def exportar(tmp_path, nome="p.xlsx", **op):
    destino = tmp_path / nome
    pp.exportar_planilha(destino, pp.OpcoesExportacao(**op))
    return destino


def cab(ws):
    return {c.value: c.column for c in ws[1] if c.value}


def linha_do_id(ws, id_):
    col = cab(ws)["id_oneworld"]
    return next(r for r in range(2, ws.max_row + 1) if ws.cell(row=r, column=col).value == id_)


def definir(caminho, aba, id_, **valores):
    wb = load_workbook(caminho)
    ws = wb[aba]
    r, h = linha_do_id(ws, id_), cab(ws)
    for col, v in valores.items():
        ws.cell(row=r, column=h[col]).value = v
    wb.save(caminho)


def adicionar(caminho, aba, **valores):
    wb = load_workbook(caminho)
    ws = wb[aba]
    h = cab(ws)
    r = max([1] + [c.row for col in ws.iter_cols() for c in col if c.value not in (None, "")]) + 1
    for col, v in valores.items():
        ws.cell(row=r, column=h[col]).value = v
    wb.save(caminho)
    return r


def apagar_coluna(caminho, aba, nome):
    wb = load_workbook(caminho)
    ws = wb[aba]
    ws.delete_cols(cab(ws)[nome])
    wb.save(caminho)


def plano_de(caminho):
    return pp.planejar_importacao(pp.ler_planilha_padrao(caminho))


def importar(caminho):
    arq = pp.ler_planilha_padrao(caminho)
    plano = pp.planejar_importacao(arq)
    return plano, pp.aplicar_importacao(arq, plano)


# ── Exportação ──
def test_exportar_para_edicao_estrutura_e_controles(tmp_path):
    popular()
    p = exportar(tmp_path, tipo=pp.TIPO_EDICAO)
    wb = load_workbook(p)
    assert wb.sheetnames == ["LEIA-ME", "OneWorld", "Dicionario", "Resumo_Periodos", "Operacoes", "Cadastros"]
    meta = {r[0].value: r[1].value for r in wb["OneWorld"].iter_rows(min_row=2)}
    assert meta["formato"] == "oneworld-planilha" and meta["versao_formato"] == "1"
    assert meta["tipo_arquivo"] == "edicao" and meta["abas"] == "Operacoes,Cadastros"
    assert meta["base_id"] == db.cfg_ler(pp.CHAVE_BASE, None)  # criado na exportação para edição
    ws = wb["Operacoes"]
    assert list(cab(ws)) == ["id_oneworld", "data", "periodo", "cliente", "local", "convidados", "valor", "status",
                             "campo:Fornecedor", "controle"]
    h = cab(ws)
    ev1 = dict(zip(["id", "data", "cliente", "local", "convidados", "valor", "status", "extras"],
                   estado()["eventos"][0][:1] + estado()["eventos"][0][1:]))
    assert ws.cell(row=2, column=h["controle"]).value == pp.controle_do_registro("eventos", ev1)
    assert len(ws.cell(row=2, column=h["controle"]).value) == 64  # SHA-256 completo
    cs = wb["Cadastros"]
    hc = cab(cs)
    mesa, contato = cs.cell(row=2, column=hc["mesa"]), cs.cell(row=2, column=hc["contato"])
    assert (mesa.value, mesa.data_type) == ("007", "s")
    assert (contato.value, contato.data_type) == ("011999990000", "s")


def test_textos_que_comecam_com_igual_nao_viram_formula(tmp_path):
    db.cfg_gravar("campos_personalizados", [])
    inserir("eventos", data="2026-01-01", cliente="=SOMA(A1:A9)", status="Pendente", extras="{}")
    p = exportar(tmp_path, tipo=pp.TIPO_EDICAO)
    c = load_workbook(p)["Operacoes"]["D2"]
    assert c.value == "=SOMA(A1:A9)" and c.data_type == "s"
    plano = plano_de(p)  # reimporta sem acusar fórmula e sem mudanças
    assert not plano.erros and len(plano.sem_mudanca) == 1


def test_exportar_para_analise_sem_dados_pessoais_e_sem_reimportacao(tmp_path):
    popular()
    p = exportar(tmp_path, tipo=pp.TIPO_ANALISE, tabelas=("eventos", "convidados", "anotacoes"))
    wb = load_workbook(p)
    assert list(cab(wb["Operacoes"])) == ["data", "periodo", "cliente", "local", "convidados", "valor", "status"]
    assert list(cab(wb["Cadastros"])) == ["evento", "mesa", "acompanhantes", "confirmacao"]
    assert "Anotacoes" in wb.sheetnames
    meta = {r[0].value: r[1].value for r in wb["OneWorld"].iter_rows(min_row=2)}
    assert meta["tipo_arquivo"] == "analise" and "omitidos" in meta["dados_pessoais"]
    assert db.cfg_ler(pp.CHAVE_BASE, None) is None  # análise não cria identificação da base
    with pytest.raises(pp.PlanilhaInvalida, match="SOMENTE PARA ANÁLISE"):
        pp.ler_planilha_padrao(p)

    p2 = exportar(tmp_path, "p2.xlsx", tipo=pp.TIPO_ANALISE, incluir_dados_pessoais=True)
    assert "nome" in cab(load_workbook(p2)["Cadastros"])
    assert "campo:Fornecedor" in cab(load_workbook(p2)["Operacoes"])


def test_resumo_por_periodo_usa_valor_previsto(tmp_path):
    popular()
    wb = load_workbook(exportar(tmp_path, tipo=pp.TIPO_ANALISE))
    ws = wb["Resumo_Periodos"]
    linhas = {r[0].value: [c.value for c in r] for r in ws.iter_rows(min_row=2)}
    assert list(cab(ws))[:3] == ["periodo", "operacoes", "valor_previsto_total"]
    assert linhas["2026-11"][1:3] == [1, 1500.0]


def test_filtro_de_periodo_e_vinculo_ambiguo(tmp_path):
    popular()
    # segunda operação "Festa Ana" fora do período: cadastros de "Festa Ana" ficam ambíguos
    inserir("eventos", data="2030-01-01", cliente="Festa Ana", status="Pendente", extras="{}")
    res = pp.exportar_planilha(tmp_path / "p.xlsx", pp.OpcoesExportacao(
        tabelas=("eventos", "convidados", "anotacoes"), data_inicio=date(2026, 11, 1), data_fim=date(2026, 12, 31)))
    assert res.contagens == {"eventos": 2, "convidados": 1, "anotacoes": 1}
    assert res.excluidos["Cadastros com vínculo ambíguo (operações com o mesmo nome dentro e fora do período)"] == 2
    assert res.excluidos["Operações fora do período ou sem data válida"] == 2
    meta = {r[0].value: r[1].value for r in load_workbook(res.caminho)["OneWorld"].iter_rows(min_row=2)}
    assert meta["periodo_inicio"] == "2026-11-01" and meta["contagem_exportada:Cadastros"] == "1"


def test_modelo_vazio_e_preenchimento(tmp_path):
    popular()
    p = exportar(tmp_path, tipo=pp.TIPO_EDICAO, vazio=True, tabelas=("eventos", "convidados", "anotacoes"))
    wb = load_workbook(p)
    assert wb["Operacoes"].cell(row=2, column=1).value is None
    adicionar(p, "Operacoes", data="2027-03-01", cliente="Novo cliente", valor="1.234,56", status="Confirmado",
              convidados=10)
    adicionar(p, "Cadastros", evento="Novo cliente", nome="Dani", confirmacao="Pendente", mesa="0012")
    adicionar(p, "Anotacoes", titulo="Retornar ligação", data="05/03/2027")
    plano, res = importar(p)
    assert res.inclusoes == {"eventos": 1, "convidados": 1, "anotacoes": 1}
    ev = db.carregar("eventos").set_index("cliente").loc["Novo cliente"]
    assert ev["valor"] == 1234.56 and ev["data"] == "2027-03-01"
    cv = db.carregar("convidados").set_index("nome").loc["Dani"]
    assert cv["mesa"] == "0012" and cv["evento"] == "Novo cliente"
    assert db.listar_anotacoes().iloc[-1]["data"] == "2027-03-05"


def test_prompts_correspondem_as_abas_exportadas():
    pa = pp.prompt_analise(["Operacoes"])
    assert "Operacoes" in pa and "Cadastros" not in pa and "PREVISTO" in pa
    assert "gastos, impostos, recebimentos" in pa and "evidência" in pa
    pf = pp.prompt_preenchimento(["Cadastros"], ["CPF"])
    assert "Operacoes" not in pf.split("Regras de estrutura")[0]
    assert "id_oneworld" in pf and "controle" in pf and "NÃO invente" in pf and "CPF" in pf
    assert "Recusou" in pf and "Em planejamento" not in pf


# ── Reimportação: identidade, alterações e reimportação idempotente ──
def test_reimportar_sem_mudancas_nao_grava_nada(tmp_path):
    popular()
    p = exportar(tmp_path, tabelas=("eventos", "convidados", "anotacoes"))
    plano = plano_de(p)
    assert len(plano.sem_mudanca) == 7 and not plano.tem_gravacao and not plano.pode_confirmar
    assert not plano.erros and not plano.conflitos


def test_alteracao_e_reimportacao_do_mesmo_resultado(tmp_path):
    popular()
    p = exportar(tmp_path)
    definir(p, "Operacoes", 2, valor=250, status="Confirmado", **{"campo:Fornecedor": "Gráfica Y"})
    plano, res = importar(p)
    assert res.alteracoes == {"eventos": 1}
    ev = db.carregar("eventos", ["Fornecedor"]).set_index("id").loc[2]
    assert ev["valor"] == 250 and ev["status"] == "Confirmado" and ev["Fornecedor"] == "Gráfica Y"
    # reimportar o mesmo arquivo: nada se repete
    plano2 = plano_de(p)
    assert not plano2.tem_gravacao
    assert [o.id for o in plano2.ja_aplicadas] == [2]


def test_alteracao_preserva_extras_de_campos_fora_da_planilha(tmp_path):
    popular()
    p = exportar(tmp_path)
    definir(p, "Operacoes", 1, **{"campo:Fornecedor": "Outro buffet"})
    importar(p)
    extras = json.loads(estado()["eventos"][0][7])
    assert extras == {"Fornecedor": "Outro buffet", "Antigo": "valor órfão"}


def test_inclusao_reimportada_vira_duplicada(tmp_path):
    popular()
    p = exportar(tmp_path)
    adicionar(p, "Cadastros", evento="Pedido 42", nome="Novo item", confirmacao="Pendente")
    _, res = importar(p)
    assert res.inclusoes == {"convidados": 1}
    plano2 = plano_de(p)
    assert not plano2.inclusoes and len(plano2.duplicados) == 1
    assert "idêntica ao registro existente" in plano2.duplicados[0].motivo


def test_duplicados_no_proprio_arquivo_e_com_existentes(tmp_path):
    popular()
    p = exportar(tmp_path)
    adicionar(p, "Cadastros", evento="Pedido 42", nome="Repetido", confirmacao="Pendente")
    adicionar(p, "Cadastros", evento="Pedido 42", nome="Repetido", confirmacao="Pendente")
    # mesma informação de um registro existente (Caio), como linha nova
    adicionar(p, "Cadastros", evento="Festa Ana", nome="Caio", mesa="2", acompanhantes=0, confirmacao="Pendente")
    plano = plano_de(p)
    assert len(plano.inclusoes) == 1
    motivos = sorted(o.motivo for o in plano.duplicados)
    assert len(motivos) == 2 and "linha" in motivos[1] and "registro existente" in motivos[0]


def test_limpeza_destacada_e_coluna_omitida_nao_apaga(tmp_path):
    popular()
    p = exportar(tmp_path)
    definir(p, "Cadastros", 1, contato=None, acompanhantes=None, mesa="007")
    apagar_coluna(p, "Cadastros", "restricao")
    plano, _ = importar(p)
    alt = plano.alteracoes[0]
    assert {(m.coluna, m.limpeza) for m in alt.mudancas} == {("contato", True), ("acompanhantes", True)}
    assert len(plano.limpezas) == 2
    cv = estado()["convidados"][0]
    assert cv[5] == "" and cv[4] == 0  # contato limpo; acompanhantes vazio = 0
    assert cv[6] == "Vegana"  # coluna omitida: valor preservado


def test_zero_digitado_nao_e_marcado_como_limpeza(tmp_path):
    popular()
    p = exportar(tmp_path)
    definir(p, "Operacoes", 1, convidados=0)
    plano = plano_de(p)
    assert [(m.coluna, m.limpeza) for m in plano.alteracoes[0].mudancas] == [("convidados", False)]


def test_campo_obrigatorio_vazio_e_erro(tmp_path):
    popular()
    p = exportar(tmp_path)
    definir(p, "Operacoes", 1, cliente=None)
    plano = plano_de(p)
    assert plano.erros and plano.erros[0].coluna == "cliente" and not plano.pode_confirmar


def test_status_exige_valor_exato(tmp_path):
    popular()
    p = exportar(tmp_path)
    definir(p, "Operacoes", 1, status="confirmado")
    plano = plano_de(p)
    assert "não permitido" in plano.erros[0].mensagem and not plano.pode_confirmar


@pytest.mark.parametrize("coluna, valor, trecho", [
    ("data", "2026-13-01", "inexistente"),
    ("data", "10-11-2026", "data inválida"),
    ("data", datetime(2026, 1, 1, 10, 30), "horário"),
    ("valor", "abc", "não é um número"),
    ("valor", -5, "menor que 0"),
    ("convidados", 2.5, "inteiro"),
    ("convidados", True, "esperado número"),
    ("local", 123, "esperado texto"),
])
def test_tipos_invalidos(tmp_path, coluna, valor, trecho):
    popular()
    p = exportar(tmp_path)
    definir(p, "Operacoes", 1, **{coluna: valor})
    plano = plano_de(p)
    assert any(trecho in e.mensagem for e in plano.erros), [e.mensagem for e in plano.erros]


def test_formatos_aceitos(tmp_path):
    popular()
    p = exportar(tmp_path)
    definir(p, "Operacoes", 1, data=datetime(2026, 11, 12), valor="2.500,75")
    definir(p, "Operacoes", 2, data="06/12/2026", valor=100)
    _, res = importar(p)
    evs = {r[0]: r for r in estado()["eventos"]}
    assert evs[1][1] == "2026-11-12" and evs[1][5] == 2500.75 and evs[2][1] == "2026-12-06"


def test_numero_em_coluna_de_texto_e_rejeitado(tmp_path):
    popular()
    p = exportar(tmp_path)
    definir(p, "Cadastros", 1, contato=11999990000)  # perderia o zero à esquerda
    plano = plano_de(p)
    assert plano.erros[0].coluna == "contato" and "zeros" in plano.erros[0].mensagem


# ── Identidade, conflitos e outra base ──
def test_conflito_quando_registro_muda_no_sistema_e_na_planilha(tmp_path):
    popular()
    p = exportar(tmp_path)
    definir(p, "Operacoes", 1, local="Planilha")
    db.executar("UPDATE eventos SET local='Sistema' WHERE id=1")
    plano = plano_de(p)
    assert len(plano.conflitos) == 1 and not plano.pode_confirmar
    arq = pp.ler_planilha_padrao(p)
    with pytest.raises(pp.ImportacaoErro):
        pp.aplicar_importacao(arq, plano)


def test_linha_nao_editada_de_registro_alterado_no_sistema_e_mantida(tmp_path):
    popular()
    p = exportar(tmp_path)
    db.executar("UPDATE eventos SET local='Mudou no sistema' WHERE id=1")
    definir(p, "Operacoes", 2, local="Loja nova")
    plano, res = importar(p)
    assert [o.id for o in plano.mantidas] == [1] and res.alteracoes == {"eventos": 1}
    assert estado()["eventos"][0][3] == "Mudou no sistema"


def test_registro_excluido_no_sistema_gera_conflito(tmp_path):
    popular()
    p = exportar(tmp_path)
    db.excluir("convidados", 3)
    plano = plano_de(p)
    assert "não existe mais" in plano.conflitos[0].mensagem


def test_id_repetido_e_controle_ausente_sao_erros(tmp_path):
    popular()
    p = exportar(tmp_path)
    wb = load_workbook(p)
    ws = wb["Operacoes"]
    h = cab(ws)
    ws.cell(row=3, column=h["id_oneworld"]).value = 1       # ID repetido
    ws.cell(row=4, column=h["controle"]).value = None        # ID sem controle
    wb.save(p)
    msgs = [e.mensagem for e in plano_de(p).erros]
    assert any("repetido" in m for m in msgs) and any("ambos" in m for m in msgs)


def test_controle_editado_gera_conflito_e_nao_sobrescreve(tmp_path):
    popular()
    p = exportar(tmp_path)
    definir(p, "Operacoes", 1, local="X", controle="0" * 64)
    plano = plano_de(p)
    assert len(plano.conflitos) == 1 and not plano.alteracoes


def test_planilha_de_outra_base_nunca_atualiza_por_id(tmp_path):
    popular()
    p = exportar(tmp_path)
    definir(p, "Operacoes", 1, local="Editado na outra base")
    db.cfg_gravar(pp.CHAVE_BASE, "f" * 32)  # este banco passa a ser "outra" base
    plano = plano_de(p)
    assert plano.outra_base and not plano.alteracoes
    assert [i.valores["local"] for i in plano.inclusoes] == ["Editado na outra base"]
    assert len(plano.duplicados) == 5  # as linhas não editadas (2 operações e 3 cadastros) são duplicadas


def test_importar_em_outro_banco_com_ids_coincidentes(tmp_path, monkeypatch):
    popular()
    p = exportar(tmp_path)
    # outro banco, com registros diferentes nos mesmos IDs
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "outro.db")
    db.init_db()
    db.cfg_gravar("campos_personalizados", ["Fornecedor"])
    inserir("eventos", data="2020-01-01", cliente="Outro 1", status="Pendente", extras="{}")
    antes = estado()["eventos"]
    plano = plano_de(p)
    assert plano.outra_base and not plano.alteracoes and not plano.conflitos
    assert len([i for i in plano.inclusoes if i.tabela == "eventos"]) == 3
    pp.aplicar_importacao(pp.ler_planilha_padrao(p), plano)
    depois = estado()["eventos"]
    assert depois[0] == antes[0] and len(depois) == 4


# ── Vínculos por texto ──
def test_renomear_operacao_propaga_para_todos_os_cadastros(tmp_path):
    popular()
    p = exportar(tmp_path, tabelas=("eventos",))  # cadastros nem estão na planilha
    definir(p, "Operacoes", 1, cliente="Festa da Ana")
    plano, res = importar(p)
    assert res.propagacoes == 2 and {x.cadastro_id for x in plano.propagacoes} == {1, 2}
    assert db.contar_convidados_do_evento("Festa da Ana") == 2


def test_renomear_com_nome_duplicado_e_bloqueado(tmp_path):
    popular()
    inserir("eventos", data="2026-11-11", cliente="Festa Ana", status="Pendente", extras="{}")
    p = exportar(tmp_path)
    definir(p, "Operacoes", 1, cliente="Festa da Ana")
    plano = plano_de(p)
    assert any("não dá para saber" in e.mensagem for e in plano.erros) and not plano.propagacoes


def test_nova_operacao_com_nome_ja_vinculado_e_bloqueada(tmp_path):
    popular()
    p = exportar(tmp_path)
    adicionar(p, "Operacoes", data="2027-05-05", cliente="Festa Ana", status="Pendente")
    plano = plano_de(p)
    assert any("ambíguos" in e.mensagem for e in plano.erros)


def test_vinculos_validados_no_estado_final(tmp_path):
    popular()
    p = exportar(tmp_path)
    adicionar(p, "Operacoes", data="2027-02-02", cliente="Evento novo", status="Confirmado")
    adicionar(p, "Cadastros", evento="Evento novo", nome="Edu", confirmacao="Confirmado")
    adicionar(p, "Cadastros", evento="Não existe", nome="Fabi", confirmacao="Confirmado")
    plano = plano_de(p)
    assert [e.mensagem for e in plano.erros if e.coluna == "evento"] == [
        "a operação vinculada 'Não existe' não existe e não será criada por esta importação."]
    assert not plano.pode_confirmar


def test_cadastro_vinculado_a_nome_ambiguo_e_bloqueado(tmp_path):
    popular()
    inserir("eventos", data="2026-11-11", cliente="Pedido 42", status="Pendente", extras="{}")
    p = exportar(tmp_path)
    adicionar(p, "Cadastros", evento="Pedido 42", nome="Gabi", confirmacao="Pendente")
    assert any("ambíguo" in e.mensagem for e in plano_de(p).erros)


# ── Estrutura incompatível ──
def _mudar_meta(p, chave, valor):
    wb = load_workbook(p)
    ws = wb["OneWorld"]
    for r in ws.iter_rows(min_row=2):
        if r[0].value == chave:
            r[1].value = valor
    wb.save(p)


@pytest.mark.parametrize("mutar, trecho", [
    (lambda p: _mudar_meta(p, "formato", "outro"), "não identifica"),
    (lambda p: _mudar_meta(p, "versao_formato", "2"), "mais nova"),
    (lambda p: _mudar_meta(p, "base_id", "abc"), "base_id"),
    (lambda p: _mudar_meta(p, "abas", "Operacoes,Gastos"), "lista de abas"),
], ids=["formato", "versao", "base_id", "abas"])
def test_metadados_imutaveis_invalidos(tmp_path, mutar, trecho):
    popular()
    p = exportar(tmp_path)
    mutar(p)
    with pytest.raises(pp.PlanilhaInvalida, match=trecho):
        pp.ler_planilha_padrao(p)


def test_metadados_informativos_podem_mudar(tmp_path):
    popular()
    p = exportar(tmp_path)
    _mudar_meta(p, "contagem_exportada:Operacoes", "999")
    adicionar(p, "Operacoes", data="2027-04-04", cliente="Mais uma", status="Pendente")
    plano = plano_de(p)
    assert len(plano.inclusoes) == 1 and plano.pode_confirmar


def test_aba_desconhecida_e_rejeitada(tmp_path):
    popular()
    p = exportar(tmp_path)
    wb = load_workbook(p)
    wb.create_sheet("Gastos")["A1"] = "valor"
    wb.save(p)
    with pytest.raises(pp.PlanilhaInvalida, match="não cria tabelas"):
        pp.ler_planilha_padrao(p)
    with sqlite3.connect(db.DB_PATH) as con:
        assert "Gastos" not in {r[0] for r in con.execute("SELECT name FROM sqlite_master")}


def test_aba_suportada_fora_da_exportacao_e_rejeitada(tmp_path):
    popular()
    p = exportar(tmp_path, tabelas=("eventos",))
    wb = load_workbook(p)
    wb.create_sheet("Cadastros")["A1"] = "id_oneworld"
    wb.save(p)
    with pytest.raises(pp.PlanilhaInvalida, match="não fazia parte"):
        pp.ler_planilha_padrao(p)


def test_coluna_desconhecida_e_campo_inexistente(tmp_path):
    popular()
    p = exportar(tmp_path)
    wb = load_workbook(p)
    wb["Operacoes"].cell(row=1, column=12).value = "imposto"
    wb.save(p)
    with pytest.raises(pp.PlanilhaInvalida, match="coluna desconhecida 'imposto'"):
        pp.ler_planilha_padrao(p)

    p2 = exportar(tmp_path, "p2.xlsx")
    wb = load_workbook(p2)
    wb["Operacoes"].cell(row=1, column=12).value = "campo:CNPJ"
    wb.save(p2)
    plano = plano_de(p2)
    assert any("não cria campos" in e.mensagem for e in plano.erros)
    assert db.cfg_ler("campos_personalizados", []) == ["Fornecedor"]


def test_formula_em_aba_de_dados_e_rejeitada(tmp_path):
    popular()
    p = exportar(tmp_path)
    definir(p, "Operacoes", 1, valor="=1+1")  # openpyxl grava como fórmula
    with pytest.raises(pp.PlanilhaInvalida, match="fórmula"):
        pp.ler_planilha_padrao(p)


@pytest.mark.parametrize("nome, conteudo", [
    ("dados.csv", b"a;b\n1;2"),
    ("corrompido.xlsx", b"isto nao e um zip"),
])
def test_arquivos_nao_suportados(tmp_path, nome, conteudo):
    p = tmp_path / nome
    p.write_bytes(conteudo)
    with pytest.raises(pp.PlanilhaInvalida):
        pp.ler_planilha_padrao(p)


def test_xlsx_qualquer_sem_aba_oneworld(tmp_path):
    p = tmp_path / "qualquer.xlsx"
    wb = Workbook()
    wb.active["A1"] = "cliente"
    wb.save(p)
    with pytest.raises(pp.PlanilhaInvalida, match="OneWorld"):
        pp.ler_planilha_padrao(p)


# ── Gravação: prévia sem efeitos, transação, cópia de segurança e histórico ──
def test_previa_e_cancelamento_nao_alteram_o_banco(tmp_path):
    popular()
    p = exportar(tmp_path)
    adicionar(p, "Operacoes", data="2027-04-04", cliente="Nova", status="Pendente")
    antes = estado()
    conteudo = db.DB_PATH.read_bytes()
    plano_de(p)  # abrir a prévia e "cancelar"
    assert estado() == antes and db.DB_PATH.read_bytes() == conteudo
    assert not db.BACKUP_DIR.exists()


def test_previa_nao_cria_base_id(tmp_path):
    popular()
    p = exportar(tmp_path)
    db.executar("DELETE FROM config WHERE chave=?", (pp.CHAVE_BASE,))
    plano_de(p)
    assert db.cfg_ler(pp.CHAVE_BASE, None) is None


def test_sucesso_cria_copia_e_registra_historico_na_mesma_transacao(tmp_path):
    popular()
    p = exportar(tmp_path)
    adicionar(p, "Operacoes", data="2027-04-04", cliente="Nova", status="Pendente")
    definir(p, "Operacoes", 2, local="Loja 2")
    _, res = importar(p)
    assert res.copia_seguranca.is_file()
    hist = estado()["arquivos"]
    assert hist[-1][1:3] == ("p.xlsx", "Planilha padrão (IA externa)") and hist[-1][5] == 2


def test_falha_na_copia_de_seguranca_interrompe(tmp_path, monkeypatch):
    popular()
    p = exportar(tmp_path)
    adicionar(p, "Operacoes", data="2027-04-04", cliente="Nova", status="Pendente")
    arq = pp.ler_planilha_padrao(p)
    plano = pp.planejar_importacao(arq)
    antes = estado()
    bloqueio = tmp_path / "arquivo_no_lugar_da_pasta"
    bloqueio.write_text("x")
    monkeypatch.setattr(db, "BACKUP_DIR", bloqueio)
    with pytest.raises(pp.ImportacaoErro, match="cópia de segurança"):
        pp.aplicar_importacao(arq, plano)
    assert estado() == antes


def test_erro_durante_a_gravacao_desfaz_tudo(tmp_path, monkeypatch):
    popular()
    p = exportar(tmp_path)
    adicionar(p, "Operacoes", data="2027-04-04", cliente="Nova", status="Pendente")
    definir(p, "Operacoes", 1, local="Alterado")
    arq = pp.ler_planilha_padrao(p)
    plano = pp.planejar_importacao(arq)
    antes = estado()

    def falhar(con, plano):
        raise sqlite3.OperationalError("disco cheio (simulado)")

    monkeypatch.setattr(pp, "_registrar_no_historico", falhar)  # inclusões e alterações já executadas
    with pytest.raises(pp.ImportacaoErro, match="desfeita"):
        pp.aplicar_importacao(arq, plano)
    assert estado() == antes


def test_dados_mudaram_desde_a_previa(tmp_path):
    popular()
    p = exportar(tmp_path)
    definir(p, "Operacoes", 1, local="Planilha")
    adicionar(p, "Operacoes", data="2027-04-04", cliente="Nova", status="Pendente")
    arq = pp.ler_planilha_padrao(p)
    plano = pp.planejar_importacao(arq)
    db.executar("UPDATE eventos SET local='Mudou' WHERE id=1")  # mudança após a prévia
    antes = estado()
    with pytest.raises(pp.PlanoDesatualizado):
        pp.aplicar_importacao(arq, plano)
    assert estado() == antes


def test_importacao_nao_usa_o_importador_antigo(tmp_path, monkeypatch):
    from oneworld import backend
    popular()
    p = exportar(tmp_path)
    adicionar(p, "Operacoes", data="2027-04-04", cliente="Nova", status="Pendente")

    def proibido(*a, **k):
        raise AssertionError("importação antiga não deve ser usada")

    monkeypatch.setattr(backend, "validar", proibido)
    monkeypatch.setattr(db, "inserir_lote", proibido)
    _, res = importar(p)
    assert res.inclusoes == {"eventos": 1}
