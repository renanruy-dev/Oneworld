"""Interface (Streamlit) do OneWorld: telas, formulários e navegação.
Só desenha e coleta ações do usuário; regras ficam em backend.py e SQL em database.py."""
import math
from datetime import date

import pandas as pd
import streamlit as st

from . import backend as bk
from . import database as db
from .config import (CAMPOS, CAMPOS_DESTINO, FILTROS, NAO_USAR, OBRIGATORIOS, PADROES, PAGINAS,
                     ROXO, STATUS_CONV, STATUS_CORES, STATUS_EVENTO, VERDE, BACKUP_DIR)
from .tema import gerar_css

_VER = tuple(int(x) for x in __import__("re").findall(r"\d+", st.__version__)[:2])
# Streamlit novo usa width="stretch"; versões antigas ainda usam use_container_width
LARGURA = {"width": "stretch"} if _VER >= (1, 50) else {"use_container_width": True}


# ── Estado da sessão ──
def C():
    """Configurações atuais (dict guardado na sessão)."""
    return st.session_state.config


def extras_cfg():
    return st.session_state.campos_personalizados


def dados(tab):
    return db.carregar(tab, extras_cfg())


def init_state():
    if "db_ok" not in st.session_state:
        db.init_db()
        cfg = {**PADROES, **db.cfg_ler("config", {})}
        if cfg["texto"] not in ("P", "M", "G"):
            cfg["texto"] = "M"
        st.session_state.config = cfg
        st.session_state.campos_personalizados = db.cfg_ler("campos_personalizados", [])
        st.session_state.notificacoes = ["Sistema inicializado.", "Dados carregados do SQLite."]
        st.session_state.db_ok = True
    if "pagina" not in st.session_state:
        st.session_state.pagina = C()["pagina_inicial"]


def aviso(texto):
    st.session_state.notificacoes.insert(0, texto)
    st.session_state.notificacoes = st.session_state.notificacoes[:20]


def flash(msg):
    st.session_state["_flash"] = msg


def mostrar_flash():
    msg = st.session_state.pop("_flash", None)
    if msg:
        st.success(msg)


# ── Peças visuais reutilizáveis ──
def moeda(v):
    return bk.moeda(v, C())


def formatar(df, tab):
    return bk.formatar(df, tab, C())


def csv_bytes(df):
    return df.to_csv(index=False).encode("utf-8-sig")


def titulo(t, sub):
    st.markdown(f'<div class="main-title">{t}</div><div class="brand-bar"></div>'
                f'<div class="sub-title">{sub}</div>', unsafe_allow_html=True)
    mostrar_flash()


def estilizar(df, cols):
    cols = [c for c in cols if c in df.columns]
    if not cols:
        return df

    def cor(v):
        par = STATUS_CORES.get(v)
        return f"background-color:{par[0]};color:{par[1]};font-weight:600" if par else ""

    fn = getattr(df.style, "map", None) or df.style.applymap
    return fn(cor, subset=cols)


def mostrar_tabela(df, chave_tab, status_cols=("Status", "Confirmação")):
    if df.empty:
        st.info("Nenhum registro para exibir.")
        return
    n = int(C()["linhas"])
    paginas = max(1, math.ceil(len(df) / n))
    k = f"pg_{chave_tab}"
    if st.session_state.get(k, 1) > paginas:
        st.session_state[k] = 1
    pag = st.number_input("Página", 1, paginas, key=k) if paginas > 1 else 1
    ini, fim = (pag - 1) * n, pag * n
    st.dataframe(estilizar(df.iloc[ini:fim], status_cols), **LARGURA, hide_index=True)
    st.caption(f"Exibindo {ini + 1}–{min(fim, len(df))} de {len(df)} registros")


# ── Formulários reutilizáveis ──
def extras_inputs(v, k):
    return {c: st.text_input(c, bk.texto(v.get(c, "")), key=f"{k}_x_{c}") for c in extras_cfg()}


def campos_evento(v, k):
    v = {} if v is None else v
    cliente = st.text_input("Nome / identificação", v.get("cliente", ""), key=f"{k}_cli")
    data = st.date_input("Data", bk.parse_date(v.get("data")) or date.today(), key=f"{k}_dt",
                         format="DD/MM/YYYY")
    local = st.text_input("Local / espaço", v.get("local", ""), key=f"{k}_loc")
    conv = st.number_input("Convidados previstos", min_value=0,
                           value=int(v.get("convidados", 0) or 0), key=f"{k}_cv")
    valor = st.number_input("Valor previsto", min_value=0.0, step=100.0,
                            value=float(v.get("valor", 0.0) or 0.0), key=f"{k}_vl")
    atual = v.get("status")
    status = st.selectbox("Status", STATUS_EVENTO,
                          index=STATUS_EVENTO.index(atual) if atual in STATUS_EVENTO else 0, key=f"{k}_st")
    extras = extras_inputs(v, k)
    return ({"data": data.isoformat(), "cliente": cliente.strip(), "local": local.strip(),
             "convidados": int(conv), "valor": float(valor), "status": status}, extras)


def campos_convidado(v, k):
    v = {} if v is None else v
    clientes = list(dict.fromkeys(dados("eventos")["cliente"].tolist()))
    atual = v.get("evento", "")
    if atual and atual not in clientes:
        clientes.append(atual)
    if clientes:
        evento = st.selectbox("Evento", clientes,
                              index=clientes.index(atual) if atual in clientes else 0, key=f"{k}_ev")
    else:
        evento = st.text_input("Evento", atual, key=f"{k}_ev")
    nome = st.text_input("Nome", v.get("nome", ""), key=f"{k}_nm")
    mesa = st.text_input("Mesa", bk.texto(v.get("mesa", "")), key=f"{k}_ms")
    acomp = st.number_input("Acompanhantes", min_value=0,
                            value=int(v.get("acompanhantes", 0) or 0), key=f"{k}_ac")
    contato = st.text_input("Contato", v.get("contato", ""), key=f"{k}_ct")
    restr = st.text_input("Restrição alimentar",
                          "" if v.get("restricao", "—") == "—" else v.get("restricao", ""), key=f"{k}_rs")
    c_atual = v.get("confirmacao")
    conf = st.selectbox("Confirmação", STATUS_CONV,
                        index=STATUS_CONV.index(c_atual) if c_atual in STATUS_CONV else 0, key=f"{k}_cf")
    extras = extras_inputs(v, k)
    return ({"evento": evento, "nome": nome.strip(), "mesa": mesa.strip(), "acompanhantes": int(acomp),
             "contato": contato.strip(), "restricao": restr.strip() or "—", "confirmacao": conf}, extras)


def bloco_excluir(tab, id_, descricao, aviso_extra=""):
    st.subheader("Excluir")
    if aviso_extra:
        st.warning(aviso_extra)
    ok = st.checkbox(f"Confirmo a exclusão de: {descricao}", key=f"del_ok_{tab}_{id_}")
    if st.button("Excluir registro", disabled=not ok, key=f"del_bt_{tab}_{id_}"):
        db.excluir(tab, id_)
        aviso(f"Registro excluído: {descricao}")
        flash("Registro excluído.")
        st.rerun()


# ── Importação de planilhas (fluxo de tela) ──
def importar_planilha(destino_fixo=None, ch="imp"):
    n = st.session_state.setdefault(f"{ch}_n", 0)
    arq = st.file_uploader("Enviar arquivo (CSV, XLSX ou JSON)", type=["csv", "xlsx", "json"],
                           key=f"{ch}_up_{n}")
    if not arq:
        st.caption("Fluxo: leitura → mapeamento → validação → prévia → confirmação. "
                   "Nada é gravado antes do seu clique em confirmar.")
        return
    try:
        data = bk.ler_arquivo(arq)
    except Exception as ex:  # noqa: BLE001 — mostrar o motivo ao usuário
        st.error(f"Não foi possível ler o arquivo: {ex}")
        return
    if data.empty:
        st.warning("O arquivo não tem linhas de dados.")
        return
    st.markdown("**Prévia do arquivo**")
    st.dataframe(data.head(10), **LARGURA)
    destino = destino_fixo or st.radio(
        "Destino dos dados", ["eventos", "convidados"], horizontal=True, key=f"{ch}_dest",
        format_func=lambda x: {"eventos": "Eventos", "convidados": "Convidados"}[x])
    st.markdown("**Mapeamento de colunas** — sugerido automaticamente por nome; ajuste se precisar")
    sug = bk.sugerir(list(data.columns), destino)
    opcoes = [NAO_USAR] + list(data.columns)
    mapa, cols = {}, st.columns(2)
    for i, (campo, rotulo) in enumerate(CAMPOS_DESTINO[destino].items()):
        padrao = sug.get(campo)
        idx = opcoes.index(padrao) if padrao in opcoes else 0
        obrig = " *" if campo in OBRIGATORIOS[destino] else ""
        with cols[i % 2]:
            esc = st.selectbox(f"{rotulo}{obrig}", opcoes, index=idx,
                               key=f"{ch}_{destino}_{campo}_{arq.name}_{arq.size}")
        mapa[campo] = None if esc == NAO_USAR else esc
    faltando = [CAMPOS_DESTINO[destino][c] for c in OBRIGATORIOS[destino] if not mapa[c]]
    if faltando:
        st.error("Mapeie os campos obrigatórios: " + ", ".join(faltando))
        return
    res = bk.validar(data, destino, mapa, dados(destino))
    a, b, c = st.columns(3)
    a.metric("Prontos para gravar", len(res["ok"]))
    b.metric("Com erro", len(res["erros"]))
    c.metric("Duplicados ignorados", res["duplicados"])
    if res["padrao"]:
        st.caption(f"{res['padrao']} linha(s) com status/confirmação não reconhecido receberam o valor padrão.")
    if res["erros"]:
        with st.expander(f"Ver {len(res['erros'])} linha(s) com erro (não serão importadas)"):
            st.dataframe(pd.DataFrame(res["erros"]), **LARGURA, hide_index=True)
    if res["ok"]:
        st.markdown("**Prévia do que será gravado**")
        prev = pd.DataFrame(res["ok"]).head(10)
        st.dataframe(estilizar(formatar(prev, destino), ("Status", "Confirmação")),
                     **LARGURA, hide_index=True)
    if st.button(f"Confirmar importação de {len(res['ok'])} registro(s)", type="primary",
                 disabled=not res["ok"], key=f"{ch}_go"):
        db.inserir_lote(destino, res["ok"])
        db.registrar_arquivo(arq.name, destino, len(res["ok"]),
                             "Processado" if not res["erros"] else "Processado com erros")
        aviso(f"Importação: {len(res['ok'])} registro(s) de {arq.name} em {destino}")
        flash(f"{len(res['ok'])} registro(s) gravados em {destino}.")
        st.session_state[f"{ch}_n"] = n + 1
        st.rerun()


# ── Páginas ──
def pagina_dashboard():
    cfg = C()
    titulo("Dashboard", "Visão geral dos dados e indicadores")
    e, cv = dados("eventos"), dados("convidados")
    f1, f2 = st.columns(2)
    mes = f1.selectbox("Período", ["Todos"] + bk.meses_disponiveis(e), key="dash_mes",
                       format_func=lambda m: m if m == "Todos" else f"{m[5:]}/{m[:4]}")
    stat = f2.multiselect("Status", STATUS_EVENTO, key="dash_status")
    f = bk.filtrar_eventos(e, mes, stat)

    conf = int((cv["confirmacao"] == "Confirmado").sum()) if not cv.empty else 0
    a, b, c, d, x = st.columns(5)
    a.metric("Eventos", len(f))
    b.metric("Convidados previstos", int(f["convidados"].sum()))
    c.metric("Receita prevista", moeda(f["valor"].sum()))
    d.metric("Pendências", int(f["status"].isin(["Pendente", "Em planejamento"]).sum()))
    x.metric("Convidados confirmados", f"{conf} de {len(cv)}")
    st.caption("Receita prevista = valores cadastrados nas reservas; não representa pagamentos recebidos.")
    st.divider()

    g1, g2, g3 = st.columns([2, 2, 1.3])
    if not f.empty:
        t = f.assign(mês=pd.to_datetime(f["data"]).dt.strftime("%Y-%m"))
        with g1:
            st.subheader("Receita prevista por mês")
            st.bar_chart(t.groupby("mês")["valor"].sum(), color=cfg["cor"])
        with g2:
            st.subheader("Eventos por status")
            st.bar_chart(f.groupby("status").size(), color=cfg["cor2"])
    else:
        g1.info("Nenhum evento para os filtros escolhidos.")
    with g3:
        st.subheader("Notificações")
        if cfg["lembretes"]:
            for msg in bk.lembretes(e):
                st.warning(msg)
        for n in st.session_state.notificacoes[:5]:
            st.info(n)

    st.subheader("Próximos eventos")
    prox = f[pd.to_datetime(f["data"]).dt.date >= date.today()] if not f.empty else f
    mostrar_tabela(formatar((prox if not prox.empty else f).drop(columns=["id"]), "eventos"), "dash")


def pagina_eventos():
    titulo("Eventos", "Cadastro e gerenciamento")
    lista, novo, editar = st.tabs(["Todos os eventos", "+ Novo evento", "Editar / excluir"])
    with lista:
        e = dados("eventos")
        c1, c2 = st.columns(2)
        busca = c1.text_input("Buscar evento", key="ev_busca")
        status = c2.multiselect("Filtrar status", STATUS_EVENTO, key="ev_status")
        if busca:
            e = e[e.astype(str).apply(lambda col: col.str.contains(busca, case=False, na=False)).any(axis=1)]
        if status:
            e = e[e["status"].isin(status)]
        mostrar_tabela(formatar(e, "eventos"), "eventos")
        st.download_button("Exportar CSV", csv_bytes(e), "eventos.csv", "text/csv")
    with novo:
        with st.form("novo_evento", clear_on_submit=True):
            dd, extras = campos_evento(None, "ne")
            salvar = st.form_submit_button("Cadastrar", type="primary")
        if salvar:
            if not dd["cliente"]:
                st.error("Informe uma identificação.")
            else:
                db.inserir_lote("eventos", [dd], extras)
                aviso(f"Novo evento: {dd['cliente']}")
                flash("Evento cadastrado.")
                st.rerun()
    with editar:
        e = dados("eventos")
        if e.empty:
            st.info("Nenhum evento cadastrado.")
            return
        ops = {int(r.id): f"#{r.id} · {bk.fmt_data(r.data)} · {r.cliente}" for r in e.itertuples()}
        sel = st.selectbox("Escolha o evento", list(ops), format_func=ops.get, key="ev_sel")
        row = e[e["id"] == sel].iloc[0]
        with st.form(f"edit_evento_{sel}"):
            dd, extras = campos_evento(row, f"ee{sel}")
            salvar = st.form_submit_button("Salvar alterações", type="primary")
        if salvar:
            if not dd["cliente"]:
                st.error("Informe uma identificação.")
            else:
                db.atualizar("eventos", sel, dd, extras)
                if dd["cliente"] != row["cliente"]:
                    db.renomear_evento_nos_convidados(dd["cliente"], row["cliente"])
                aviso(f"Evento atualizado: {dd['cliente']}")
                flash("Evento atualizado.")
                st.rerun()
        st.divider()
        vinc = db.contar_convidados_do_evento(row["cliente"])
        bloco_excluir("eventos", sel, row["cliente"],
                      f"{vinc} convidado(s) estão ligados a este evento e continuarão cadastrados."
                      if vinc else "")


def pagina_convidados():
    titulo("Convidados & Planilhas", "Registros tabulares e campos personalizáveis")
    lista, novo, editar, imp = st.tabs(["Convidados", "+ Adicionar", "Editar / excluir", "Importar planilha"])
    with lista:
        g = dados("convidados")
        c1, c2, c3 = st.columns(3)
        busca = c1.text_input("Buscar convidado", key="cv_busca")
        evs = c2.multiselect("Evento", sorted(g["evento"].unique()), key="cv_evento")
        conf = c3.multiselect("Confirmação", STATUS_CONV, key="cv_conf")
        if busca:
            g = g[g.astype(str).apply(lambda col: col.str.contains(busca, case=False, na=False)).any(axis=1)]
        if evs:
            g = g[g["evento"].isin(evs)]
        if conf:
            g = g[g["confirmacao"].isin(conf)]
        m1, m2, m3 = st.columns(3)
        m1.metric("Confirmados", int((g["confirmacao"] == "Confirmado").sum()))
        m2.metric("Pendentes", int((g["confirmacao"] == "Pendente").sum()))
        m3.metric("Recusaram", int((g["confirmacao"] == "Recusou").sum()))
        mostrar_tabela(formatar(g, "convidados"), "convidados")
        st.download_button("Exportar CSV", csv_bytes(g), "convidados.csv", "text/csv")
    with novo:
        with st.form("novo_convidado", clear_on_submit=True):
            dd, extras = campos_convidado(None, "nc")
            salvar = st.form_submit_button("Adicionar", type="primary")
        if salvar:
            if not dd["nome"]:
                st.error("Informe o nome do convidado.")
            else:
                db.inserir_lote("convidados", [dd], extras)
                aviso(f"Convidado adicionado: {dd['nome']}")
                flash("Convidado adicionado.")
                st.rerun()
    with editar:
        g = dados("convidados")
        if g.empty:
            st.info("Nenhum convidado cadastrado.")
        else:
            ops = {int(r.id): f"#{r.id} · {r.nome} · {r.evento}" for r in g.itertuples()}
            sel = st.selectbox("Escolha o convidado", list(ops), format_func=ops.get, key="cv_sel")
            row = g[g["id"] == sel].iloc[0]
            with st.form(f"edit_conv_{sel}"):
                dd, extras = campos_convidado(row, f"ec{sel}")
                salvar = st.form_submit_button("Salvar alterações", type="primary")
            if salvar:
                if not dd["nome"]:
                    st.error("Informe o nome do convidado.")
                else:
                    db.atualizar("convidados", sel, dd, extras)
                    aviso(f"Convidado atualizado: {dd['nome']}")
                    flash("Convidado atualizado.")
                    st.rerun()
            st.divider()
            bloco_excluir("convidados", sel, row["nome"])
    with imp:
        importar_planilha("convidados", "impcv")


def pagina_dados_externos():
    titulo("Dados Externos", "Recebimento, validação e tratamento")
    importar_planilha(None, "impex")
    st.subheader("Histórico")
    h = db.historico_arquivos()
    if h.empty:
        st.info("Nenhum arquivo recebido.")
    else:
        st.dataframe(h, **LARGURA, hide_index=True)


def pagina_ia():
    titulo("Orientação IA", "Perguntas e análises baseadas nos dados")
    st.info("Resposta SIMULADA por regras locais. A IA externa (BYOK) ainda é uma decisão pendente do "
            "projeto; quando existir, ela orienta e sugere, sem alterar registros.")
    pergunta = st.text_area("Pergunte sobre seus dados", placeholder="Ex.: Qual é a receita prevista?")
    if st.button("Perguntar", type="primary") and pergunta.strip():
        resp = bk.responder_ia(pergunta, dados("eventos"), dados("convidados"), C())
        st.subheader("Resposta")
        st.write(resp)
        db.salvar_relatorio(pergunta, resp)
    st.subheader("Relatórios recentes")
    for r in db.listar_relatorios().itertuples():
        with st.expander(f"{r.data} — {r.pergunta}"):
            st.write(r.resposta)
    st.divider()
    st.subheader("Exportar para análise externa")
    st.caption("Gera um Markdown com resumo, tabelas e um prompt sugerido para colar em um chat de IA externo. "
               "Ao colar, os dados saem do seu computador.")
    md = bk.gerar_markdown(dados("eventos"), dados("convidados"), C())
    st.download_button("Baixar Markdown", md.encode("utf-8"), "oneworld_export.md", "text/markdown")
    with st.expander("Pré-visualizar"):
        st.code(md, language="markdown")


def pagina_anotacoes():
    titulo("Anotações", "Notas, relatórios e datas previstas")
    with st.form("nova_anotacao", clear_on_submit=True):
        t = st.text_input("Título")
        d = st.text_area("Descrição")
        dp = st.date_input("Data prevista", value=date.today(), format="DD/MM/YYYY")
        salvar = st.form_submit_button("Salvar anotação", type="primary")
    if salvar:
        if not t.strip():
            st.error("Informe um título.")
        else:
            db.criar_anotacao(t.strip(), d, dp.isoformat())
            flash("Anotação salva.")
            st.rerun()
    notas = db.listar_anotacoes()
    if notas.empty:
        st.info("Nenhuma anotação cadastrada.")
    for r in notas.itertuples():
        with st.expander(f"{bk.fmt_data(r.data)} — {r.titulo}"):
            st.write(r.descricao or "—")
            if st.button("Excluir anotação", key=f"del_nota_{r.id}"):
                db.excluir_anotacao(r.id)
                st.rerun()


def pagina_config():
    cfg = C()
    titulo("Configurações", "Personalização da interface e eficiência")
    visual, efic, dds, seg, campos = st.tabs(
        ["Personalização visual", "Eficiência", "Dados & integrações", "Segurança", "Modelos & campos"])
    with visual:
        cfg["nome"] = st.text_input("Nome do sistema", cfg["nome"])
        c1, c2 = st.columns(2)
        cfg["cor"] = c1.color_picker("Cor principal (botões, destaques)", cfg["cor"])
        cfg["cor2"] = c2.color_picker("Cor de apoio (gráficos, detalhes)", cfg["cor2"])
        if st.button("Voltar às cores OneWorld (roxo e verde)"):
            cfg["cor"], cfg["cor2"] = ROXO, VERDE
            st.rerun()
        cfg["tema"] = st.selectbox("Tema", ["Claro", "Escuro", "Automático"],
                                   index=["Claro", "Escuro", "Automático"].index(cfg["tema"]))
        cfg["densidade"] = st.select_slider("Densidade", ["Compacta", "Confortável", "Ampla"],
                                            value=cfg["densidade"])
        cfg["texto"] = st.select_slider("Tamanho do texto", ["P", "M", "G"], value=cfg["texto"])
        st.markdown(f'<div class="ow-card"><b>Prévia</b><br>{cfg["nome"]} '
                    f'<span class="ow-chip" style="background:{STATUS_CORES["Confirmado"][0]};'
                    f'color:{STATUS_CORES["Confirmado"][1]}">Confirmado</span> '
                    f'<span class="ow-chip" style="background:{cfg["cor"]};color:#fff">Botão</span> '
                    f'<span class="ow-chip" style="background:{cfg["cor2"]};color:#1E2140">Apoio</span></div>',
                    unsafe_allow_html=True)
        up = st.file_uploader("Logotipo (PNG, JPG ou SVG)", type=["png", "jpg", "jpeg", "svg"])
        if up and st.button("Usar este logotipo"):
            bk.salvar_logo(up.name, up.getvalue())
            st.rerun()
        if bk.logo_personalizado() and st.button("Remover logotipo personalizado"):
            bk.remover_logo()
            st.rerun()
    with efic:
        pgs = PAGINAS[:-1]
        cfg["pagina_inicial"] = st.selectbox("Página inicial", pgs, index=pgs.index(cfg["pagina_inicial"]))
        cfg["linhas"] = st.number_input("Linhas por página", 5, 100, int(cfg["linhas"]))
        cfg["auto_refresh"] = st.toggle("Atualização automática do Dashboard (30 s)", cfg["auto_refresh"])
        cfg["lembrar_filtros"] = st.toggle("Lembrar filtros ao trocar de página", cfg["lembrar_filtros"])
        cfg["lembretes"] = st.toggle("Lembretes de eventos nos próximos 7 dias", cfg["lembretes"])
        st.caption("Atalhos de teclado (N, /, D) estão planejados e ainda não funcionam nesta versão.")
    with dds:
        cfg["idioma"] = st.selectbox("Idioma (formato de números)", ["Português", "English", "Español"],
                                     index=["Português", "English", "Español"].index(cfg["idioma"]))
        cfg["moeda"] = st.selectbox("Moeda (símbolo; não converte valores)", ["BRL", "USD", "EUR"],
                                    index=["BRL", "USD", "EUR"].index(cfg["moeda"]))
        st.write("Integrações externas (pagamentos, calendário, API): fora do escopo confirmado do MVP.")
        st.write("Exportação: CSV por tabela e Markdown na tela Orientação IA.")
    with seg:
        st.write("Operação local, sem login próprio (conforme escopo do MVP).")
        if st.button("Fazer backup agora", type="primary"):
            dest = db.fazer_backup()
            aviso(f"Backup criado: {dest.name}")
            st.success(f"Backup salvo em: {dest}")
        st.caption(f"{db.contar_backups()} backup(s) na pasta {BACKUP_DIR}. "
                   "A restauração ainda é um requisito pendente.")
        st.warning("Chaves de API (BYOK) devem ficar no arquivo .env, nunca no código.")
    with campos:
        novo = st.text_input("Nome do novo campo", placeholder="Ex.: Categoria")
        if st.button("Adicionar campo") and novo.strip():
            lista = st.session_state.campos_personalizados
            reservados = {bk.chave(x) for x in sum(CAMPOS.values(), [])}
            if novo.strip() in lista or bk.chave(novo) in reservados:
                st.error("Esse nome já existe.")
            else:
                lista.append(novo.strip())
                db.cfg_gravar("campos_personalizados", lista)
                st.rerun()
        for cp in list(st.session_state.campos_personalizados):
            c1, c2 = st.columns([4, 1])
            c1.write(f"• {cp}")
            if c2.button("Remover", key=f"rm_{cp}"):
                st.session_state.campos_personalizados.remove(cp)
                db.cfg_gravar("campos_personalizados", st.session_state.campos_personalizados)
                st.rerun()
        if not st.session_state.campos_personalizados:
            st.info("Nenhum campo personalizado.")
        else:
            st.caption("Os campos aparecem nos formulários e tabelas de Eventos e Convidados. "
                       "Os valores já gravados ficam guardados mesmo se o campo for removido.")
        st.subheader("Modelos")
        st.write("Área reservada para modelos de eventos, formulários, dashboards e estruturas de dados.")
    st.divider()
    a, b = st.columns(2)
    if a.button("Salvar alterações", type="primary"):
        db.cfg_gravar("config", cfg)
        st.success("Configurações salvas no banco.")
    if b.button("Restaurar padrões"):
        cfg.update(PADROES)
        db.cfg_gravar("config", cfg)
        st.rerun()


ROTAS = {"Dashboard": pagina_dashboard, "Eventos": pagina_eventos,
         "Convidados & Planilhas": pagina_convidados, "Dados Externos": pagina_dados_externos,
         "Orientação IA": pagina_ia, "Anotações": pagina_anotacoes, "Configurações": pagina_config}


def sidebar():
    cfg = C()
    with st.sidebar:
        logo = bk.logo_atual()
        if logo:
            st.image(str(logo), **LARGURA)
            if bk.sem_acento(cfg["nome"]) != "oneworld":
                st.markdown(f"**{cfg['nome']}**")
        else:
            st.markdown(f"## {cfg['nome']}")
        st.caption("Gerência e análise em um só mundo")
        st.radio("Navegação", PAGINAS, key="pagina")
        st.divider()
        st.caption("Ambiente")
        st.write("Modo: local")
        st.write("Banco: SQLite")
        st.write("Status: operacional")


def main():
    """Ponto de entrada chamado por app.py (depois do st.set_page_config)."""
    init_state()
    cfg = C()
    st.markdown(gerar_css(cfg), unsafe_allow_html=True)
    sidebar()
    pagina = st.session_state.pagina
    if st.session_state.get("_ultima_pagina") not in (None, pagina) and not cfg["lembrar_filtros"]:
        for k in FILTROS:
            st.session_state.pop(k, None)
    st.session_state["_ultima_pagina"] = pagina

    if pagina == "Dashboard" and cfg["auto_refresh"]:
        st.fragment(run_every=30)(pagina_dashboard)()
    else:
        ROTAS[pagina]()

    st.divider()
    st.caption("OneWorld — Protótipo 02 · dados em SQLite local · IA simulada nesta versão.")
