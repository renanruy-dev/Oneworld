"""Dashboard Streamlit; todas as operações analíticas ficam nos módulos puros."""
from hashlib import sha256
from csv import Error as ErroCSV
from io import BytesIO
from pathlib import Path
from zipfile import BadZipFile
from sqlite3 import Error as ErroSQLite

import pandas as pd
import streamlit as st

from . import backend
from . import database
from .fontes_sqlite import carregar_tabela, listar_tabelas
from .analises import preparar_grafico
from .filtros import aplicar_filtros
from .formatacao import formatar_valor_kpi
from .indicadores import OPERACOES, calcular_kpi
from .metadados import ErroBI, configurar_datas, inspecionar_colunas, numeros_validos

ROTULOS = {"contagem": "Contagem de registros", "distintos": "Valores distintos",
           "soma": "Soma", "media": "Média", "minimo": "Mínimo", "maximo": "Máximo"}
EXEMPLOS = Path(__file__).resolve().parent.parent / "exemplos"


def _chave(base):
    """Separa a identidade dos controles de cada versão do dataset."""
    chave = base + "::" + st.session_state["bi_fonte"][0]
    if base.startswith("bi_cfg_filtro_"):
        chave += "::" + str(st.session_state.get("bi_filtros_revisao", 0))
    return chave


def _selecionar_dados():
    arquivos = st.file_uploader("Adicionar conjuntos de dados (CSV, XLSX ou JSON)",
                                type=["csv", "xlsx", "json"], accept_multiple_files=True,
                                key="bi_uploads")
    fontes = {f"Exemplo: {p.stem}": p for p in sorted(EXEMPLOS.glob("*.csv"))}
    if st.checkbox("Incluir tabelas do banco local", key="bi_banco_local"):
        try:
            fontes.update({f"Banco local: {nome}": ("sqlite", nome)
                           for nome in listar_tabelas(database.DB_PATH)})
        except (ErroSQLite, OSError, ValueError):
            st.warning("Não foi possível abrir o banco local para leitura.")
    fontes.update({f"Arquivo {i + 1}: {a.name}": a for i, a in enumerate(arquivos)})
    if not fontes:
        st.info("Adicione um arquivo para iniciar sua análise.")
        return None
    escolha = st.selectbox("Conjunto de dados", list(fontes), key="bi_dataset")
    fonte = fontes[escolha]
    if isinstance(fonte, tuple):
        try:
            dados_banco = carregar_tabela(database.DB_PATH, fonte[1])
        except (ErroSQLite, OSError, ValueError):
            st.error("Não foi possível ler a tabela. Verifique se o banco está disponível.")
            return None
        # JSON exige UTF-8 em BLOBs e arredonda reais, ocultando atualizações.
        # A identidade inclui esquema e valores sem converter os dados lidos.
        esquema = repr([(c, str(t)) for c, t in dados_banco.dtypes.items()]).encode()
        conteudo = esquema + pd.util.hash_pandas_object(dados_banco, index=True).values.tobytes()
        st.caption("Tabela consultada somente para leitura. Alterações no banco aparecem ao atualizar a análise.")
    else:
        conteudo = fonte.read_bytes() if isinstance(fonte, Path) else fonte.getvalue()
    identificador = sha256(escolha.encode() + conteudo).hexdigest()[:16]
    memoria = st.session_state.get("bi_fonte")
    if not memoria or memoria[0] != identificador:
        try:
            if isinstance(fonte, tuple):
                df = dados_banco
            else:
                arquivo = BytesIO(conteudo)
                arquivo.name = fonte.name
                df = backend.ler_arquivo(arquivo)
            inspecionar_colunas(df)
        except (ValueError, TypeError, OSError, ImportError, UnicodeError,
                BadZipFile, EOFError, NotImplementedError, ErroCSV) as exc:
            st.error(f"Não foi possível ler o arquivo: {exc}")
            return None
        st.session_state["bi_fonte"] = (identificador, df)
        # O novo conteúdo deve começar sem configurações de outro dataset.
        for chave in list(st.session_state):
            if chave.startswith("bi_cfg_"):
                del st.session_state[chave]
        # Encerra o ciclo antigo antes de reconstruir controles de outras colunas.
        # Sem isso, o navegador pode conservar rótulos do dataset anterior.
        st.rerun()
    return st.session_state["bi_fonte"][1].copy()


def _tipar_datas(df):
    with st.expander("Tipos de colunas e datas"):
        meta = inspecionar_colunas(df)
        st.dataframe(pd.DataFrame([vars(c) for c in meta.values()]), hide_index=True)
        candidatas = [n for n, c in meta.items() if c.tipo == "categoria"]
        colunas = st.multiselect("Interpretar colunas como data", candidatas, key=_chave("bi_cfg_datas"))
        if colunas:
            formato = st.text_input("Formato das datas", "%Y-%m-%d", key=_chave("bi_cfg_formato_data"),
                                    help="Exemplos: %Y-%m-%d ou %d/%m/%Y.")
            df, falhas = configurar_datas(df, colunas, formato)
            for nome, quantidade in falhas.items():
                if quantidade:
                    st.warning(f"{nome}: {quantidade} valor(es) não seguem o formato e foram "
                               "considerados nulos apenas nesta análise.")
    return df


def _configurar_filtros(df, meta):
    filtros = []
    with st.expander("Filtros dinâmicos"):
        if st.button("Limpar filtros", key="bi_limpar"):
            for chave in list(st.session_state):
                if chave.startswith("bi_cfg_filtro_"):
                    del st.session_state[chave]
            # Reconstrói também o estado visual dos widgets no navegador.
            st.session_state["bi_filtros_revisao"] = st.session_state.get("bi_filtros_revisao", 0) + 1
            st.rerun()
        for i, (nome, coluna) in enumerate(meta.items()):
            k = f"bi_cfg_filtro_{i}"
            if coluna.tipo == "incompativel":
                st.caption(f"{nome}: tipo incompatível com filtros automáticos.")
                continue
            if not st.checkbox(f"Filtrar {nome}", key=_chave(k)):
                continue
            cfg = {"coluna": nome, "tipo": coluna.tipo}
            cfg["incluir_nulos"] = st.checkbox("Incluir nulos / valores não finitos", key=_chave(k + "_null"))
            if coluna.tipo == "categoria":
                opcoes = df[nome].dropna().unique().tolist()
                cfg["valores"] = st.multiselect(f"Valores de {nome}", opcoes, default=opcoes,
                                                key=_chave(k + "_valores"))
            else:
                s = numeros_validos(df, nome) if coluna.tipo == "numero" else df[nome]
                validos = s.dropna()
                if validos.empty:
                    st.caption(f"{nome}: sem valores válidos para definir um intervalo.")
                elif coluna.tipo == "numero":
                    converter = int if validos.dtype.kind in "iu" else float
                    lo, hi = converter(validos.min()), converter(validos.max())
                    if converter is int and max(abs(lo), abs(hi)) > 2**53 - 1:
                        # Widgets numéricos usam a precisão de Number no navegador.
                        # Texto mantém limites inteiros grandes exatos.
                        minimo = st.text_input(f"Mínimo de {nome}", str(lo), key=_chave(k + "_min"))
                        maximo = st.text_input(f"Máximo de {nome}", str(hi), key=_chave(k + "_max"))
                        try:
                            cfg["minimo"], cfg["maximo"] = int(minimo), int(maximo)
                        except ValueError as exc:
                            raise ErroBI(f"Informe limites inteiros válidos para {nome!r}.") from exc
                    else:
                        cfg["minimo"] = st.number_input(f"Mínimo de {nome}", value=lo, key=_chave(k + "_min"))
                        cfg["maximo"] = st.number_input(f"Máximo de {nome}", value=hi, key=_chave(k + "_max"))
                else:
                    cfg["minimo"] = st.date_input(f"Data inicial de {nome}", validos.min().date(),
                                                   key=_chave(k + "_min"), format="DD/MM/YYYY")
                    cfg["maximo"] = st.date_input(f"Data final de {nome}", validos.max().date(),
                                                   key=_chave(k + "_max"), format="DD/MM/YYYY")
            filtros.append(cfg)
    return filtros


def _mostrar_kpis(df, meta):
    st.subheader("KPIs configuráveis")
    quantidade = st.number_input("Quantidade de KPIs", 1, 6, 1, key=_chave("bi_cfg_n_kpis"))
    numericas = [n for n, c in meta.items() if c.tipo == "numero"]
    compativeis = [n for n, c in meta.items() if c.tipo != "incompativel"]
    for i in range(quantidade):
        k = f"bi_cfg_kpi_{i}"
        with st.expander(f"Configurar KPI {i + 1}"):
            operacoes = [o for o in OPERACOES if o == "contagem" or
                         (o == "distintos" and compativeis) or (o not in ("contagem", "distintos") and numericas)]
            op = st.selectbox("Operação", operacoes, format_func=ROTULOS.get, key=_chave(k + "_op"))
            coluna = None
            if op != "contagem":
                coluna = st.selectbox("Coluna do KPI", compativeis if op == "distintos" else numericas,
                                      key=_chave(k + "_col_" + op))
            titulo = st.text_input("Título do KPI", f"KPI {i + 1}", key=_chave(k + "_titulo"))
            formato = st.selectbox("Apresentação", ["Número", "Percentual", "Moeda"], key=_chave(k + "_fmt"))
            simbolo = st.text_input("Símbolo da moeda", "R$", key=_chave(k + "_simbolo")) if formato == "Moeda" else ""
            if formato == "Percentual":
                st.caption("Apresentação: 0,25 corresponde a 25%. Nenhuma taxa é calculada.")
        resultado = calcular_kpi(df, {"operacao": op, "coluna": coluna, "titulo": titulo})
        if resultado.erro:
            st.error(resultado.erro)
        elif resultado.valor is None:
            st.metric(resultado.titulo, formatar_valor_kpi(resultado.valor))
            st.caption(resultado.mensagem)
        else:
            formatos = {"Número": "numero", "Percentual": "percentual", "Moeda": "moeda"}
            texto = formatar_valor_kpi(resultado.valor, formatos[formato], simbolo=simbolo)
            st.metric(resultado.titulo, texto)


def _mostrar_grafico(df, meta, cor):
    st.subheader("Gráfico configurável")
    categorias = [n for n, c in meta.items() if c.tipo == "categoria"]
    numericas = [n for n, c in meta.items() if c.tipo == "numero"]
    datas = [n for n, c in meta.items() if c.tipo == "data"]
    tipos = (["barras"] if categorias else []) + (["linhas"] if datas else []) + (["histograma"] if numericas else [])
    if not tipos:
        st.info("Sem colunas compatíveis com gráficos. Verifique os tipos do conjunto.")
        return
    cfg = {"tipo": st.selectbox("Tipo de gráfico", tipos, key=_chave("bi_cfg_grafico"))}
    if cfg["tipo"] == "histograma":
        cfg["coluna"] = st.selectbox("Coluna numérica", numericas, key=_chave("bi_cfg_hist_col"))
        cfg["intervalos"] = st.number_input("Intervalos", 1, 100, 10, key=_chave("bi_cfg_hist_bins"))
    else:
        tipo = cfg["tipo"]
        cfg["grupo"] = st.selectbox("Agrupar por", datas if tipo == "linhas" else categorias,
                                    key=_chave(f"bi_cfg_grupo_{tipo}"))
        cfg["operacao"] = st.selectbox("Agregação", ["contagem"] + (["soma", "media", "minimo", "maximo"] if numericas else []),
                                       format_func=ROTULOS.get, key=_chave("bi_cfg_agregacao"))
        if cfg["operacao"] != "contagem":
            cfg["coluna"] = st.selectbox("Medida", numericas, key=_chave("bi_cfg_medida"))
        if tipo == "linhas":
            cfg["periodo"] = st.selectbox("Período", ["dia", "mes"], key=_chave("bi_cfg_periodo"))
    tabela = preparar_grafico(df, cfg)
    if tabela.empty:
        st.info("Sem dados válidos para o gráfico e os filtros selecionados.")
        return
    eixo, medida = tabela.columns
    if cfg["tipo"] == "linhas":
        st.line_chart(tabela, x=eixo, y=medida, color=cor)
    elif cfg["tipo"] == "histograma":
        # Os rótulos são intervalos textuais já ordenados numericamente.
        # Ordenação alfabética deslocaria, por exemplo, (7.5, 10.0] ao final.
        st.bar_chart(tabela, x=eixo, y=medida, color=cor, sort=False)
    else:
        st.bar_chart(tabela, x=eixo, y=medida, color=cor)
    with st.expander("Dados do gráfico"):
        st.dataframe(tabela, hide_index=True)


def mostrar_dashboard(cor):
    """Um único DataFrame filtrado alimenta tabela, KPIs e gráfico."""
    st.caption("Escolha os dados e configure a análise. Arquivos e configurações da análise ficam nesta sessão local.")
    try:
        df = _selecionar_dados()
        if df is None:
            return
        with st.container(key=_chave("bi_painel")):
            df = _tipar_datas(df)
            meta = inspecionar_colunas(df)
            if not meta:
                st.info("O conjunto não possui colunas.")
                return
            filtros = _configurar_filtros(df, meta)
            filtrado = aplicar_filtros(df, filtros)
            st.caption(f"{len(filtrado)} de {len(df)} registros após os filtros.")
            if filtrado.empty:
                st.info("Nenhum registro para a seleção atual. Ajuste ou limpe os filtros.")
            _mostrar_kpis(filtrado, meta)
            _mostrar_grafico(filtrado, meta, cor)
            st.subheader("Registros filtrados")
            st.dataframe(filtrado, hide_index=True)
            st.download_button("Exportar dados filtrados", filtrado.to_csv(index=False).encode("utf-8-sig"),
                               "analise_filtrada.csv", "text/csv", key="bi_download")
    except ErroBI as exc:
        st.error(str(exc))
