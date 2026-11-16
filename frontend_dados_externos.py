"""Tela Dados Externos (PyQt6): central das bases públicas do OneWorld.

Abas:
  • Bases públicas — a base DFP da CVM (estado, instalar/atualizar) e as bases adicionadas pelo usuário
    (adicionar com prévia e confirmação, ver, usar no Dashboard BI, liberar para a IA, excluir).
  • Explorar CVM — busca de companhias, demonstrações e ranking, com envio ao Dashboard e exportação.
  • Importar planilha do negócio — o fluxo já existente (planilha → eventos/convidados).
  • Histórico — tudo que já foi recebido.
Regras de dados ficam em bases_publicas.py e dfp.py; aqui só se desenha e se coletam ações.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from . import bases_publicas as bp
from . import database as db
from . import dfp
from .frontend import AlertBox, Divider, ImportarPlanilhaWidget, MetricCard, PaginatedTableWidget
from .util import brl

FILTRO_ARQUIVOS = "Dados abertos (*.csv *.tsv *.txt *.xlsx *.json *.zip);;Todos os arquivos (*)"
_MAX_BASES_EXTRAS_BI = 5  # demonstrações enviadas ao Dashboard nesta sessão (limita memória)


def _botao(texto: str, ao_clicar, primario: bool = False) -> QPushButton:
    b = QPushButton(texto)
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    if primario:
        b.setObjectName("PrimaryBtn")
    b.clicked.connect(lambda _=False: ao_clicar())
    return b


def _legenda(texto: str) -> QLabel:
    c = QLabel(texto)
    c.setObjectName("Caption")
    c.setWordWrap(True)
    return c


def _card() -> tuple[QFrame, QVBoxLayout]:
    f = QFrame()
    f.setObjectName("OwCard")
    lay = QVBoxLayout(f)
    lay.setContentsMargins(16, 14, 16, 14)
    lay.setSpacing(10)
    return f, lay


def _num(v) -> str:
    return "" if pd.isna(v) else f"{v:,.0f}".replace(",", ".")


def _pct(v) -> str:
    return "" if pd.isna(v) else f"{v * 100:.1f}%".replace(".", ",")


class DadosExternosWidget(QWidget):
    """Conteúdo completo da página Dados Externos."""

    def __init__(self, janela):
        super().__init__()
        self.janela = janela
        self.estado = janela.estado
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(12)

        # A base DFP só era carregada na primeira pergunta à IA; abrir esta tela já a prepara (2º plano).
        dfp.iniciar()
        self._dfp_ativo = self._dfp_carregando()

        erro = self.estado.pop("dx_erro", None)
        if erro:
            lay.addWidget(AlertBox(erro, "error"))

        self.abas = QTabWidget()
        self.abas.addTab(self._aba_bases(), "🗂️ Bases públicas")
        self.abas.addTab(self._aba_cvm(), "🏛️ Explorar CVM")
        self.abas.addTab(self._aba_planilha(), "📥 Importar planilha do negócio")
        self.abas.addTab(self._aba_historico(), "🕘 Histórico")
        self.abas.setCurrentIndex(min(self.estado.get("dx_aba", 0), self.abas.count() - 1))
        self.abas.currentChanged.connect(lambda i: self.estado.__setitem__("dx_aba", i))
        lay.addWidget(self.abas)

        # Acompanha cargas em segundo plano (DFP e importação) sem travar a tela.
        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._tick)
        if self._dfp_ativo or bp.estado_importacao()["estado"] != "ocioso":
            self._timer.start()

    # ── Estado em segundo plano ──
    @staticmethod
    def _dfp_carregando() -> bool:
        s = dfp.status()
        return bool(s.get("atualizando")) or s["estado"] == "carregando"

    def _tick(self):
        imp = bp.estado_importacao()
        if imp["estado"] in ("ok", "erro"):
            self._concluir_importacao(imp)
            return
        carregando = self._dfp_carregando()
        if self._dfp_ativo and not carregando:
            s = dfp.status()
            if s.get("erro") and s.get("falhou_em"):
                self.estado["dx_erro"] = f"A carga da base DFP falhou: {s['erro']}"
            else:
                self.janela.flash(f"Base DFP {s.get('ano', '')} carregada e pronta para uso.")
            self.janela.reconstruir_pagina()
            return
        if carregando and hasattr(self, "lbl_progresso"):
            self.lbl_progresso.setText(f"Carregando a base DFP… {dfp.status().get('etapa') or ''}")
        if not carregando and imp["estado"] == "ocioso":
            self._timer.stop()

    def _concluir_importacao(self, imp: dict):
        bp.limpar_estado_importacao()
        if imp["estado"] == "ok":
            r = imp["resultado"]
            try:
                db.registrar_arquivo(imp["arquivo"] or r["nome"], f"Base pública: {r['nome']}",
                                     r["linhas"], "Importado", origem="Base pública")
            except Exception:  # noqa: BLE001 — o histórico é acessório; a base já está gravada
                pass
            extra = (" " + " ".join(r["avisos"])) if r["avisos"] else ""
            linhas = f"{r['linhas']:,}".replace(",", ".")
            self.janela.flash(f"Base '{r['nome']}' adicionada: {linhas} linhas, {r['colunas']} colunas.{extra}")
        else:
            self.estado["dx_erro"] = f"Não foi possível adicionar a base: {imp['erro']}"
        self.janela.reconstruir_pagina()

    # ══════════════════════ ABA 1 — BASES PÚBLICAS ══════════════════════
    def _aba_bases(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(12, 12, 12, 12)
        lay.setSpacing(14)
        lay.addWidget(_legenda(
            "Dados abertos entram aqui e passam a valer no resto do OneWorld: aparecem como conjuntos de dados "
            "no Dashboard BI e, se você liberar, servem de contexto para a Orientação IA. Nada é gravado antes "
            "da sua confirmação."))
        lay.addWidget(self._card_cvm())

        imp = bp.estado_importacao()
        if imp["estado"] == "importando":
            lay.addWidget(AlertBox(f"Importando a base '{imp['nome']}'… você pode continuar usando o OneWorld.",
                                   "info"))

        lay.addWidget(self._subtitulo("Bases adicionadas por você"))
        bases = bp.listar()
        if bases.empty:
            lay.addWidget(_legenda("Nenhuma base adicionada ainda. Use o formulário abaixo."))
        for b in bases.itertuples():
            lay.addWidget(self._card_base(b))
        ver = self.estado.get("dx_ver")
        if ver in set(bases["id"]):
            lay.addWidget(self._previa_base(int(ver)))

        lay.addWidget(Divider())
        lay.addWidget(self._subtitulo("Adicionar nova base"))
        lay.addWidget(self._form_adicionar())
        lay.addStretch(1)
        return w

    def _subtitulo(self, txt: str) -> QLabel:
        return self.janela._subtitulo(txt)

    # ── Card da CVM ──
    def _card_cvm(self) -> QFrame:
        card, lay = _card()
        t = QLabel("<b>CVM — Demonstrações Financeiras Padronizadas (DFP)</b>")
        lay.addWidget(t)
        lay.addWidget(_legenda("Balanços, resultados, fluxos de caixa e demais demonstrações anuais das companhias "
                               "abertas brasileiras, em dados abertos da CVM."))
        s = dfp.status()
        if s["estado"] == "pronto":
            r = dfp.resumo_base()
            linha = QHBoxLayout()
            linha.setSpacing(12)
            linha.addWidget(MetricCard("Exercício", r.get("ano", "—")))
            linha.addWidget(MetricCard("Companhias", r.get("companhias", 0)))
            linha.addWidget(MetricCard("Com consolidado", r.get("consolidadas", 0)))
            linha.addWidget(MetricCard("Carregada em", r.get("carregado_em", "—")))
            lay.addLayout(linha)
            lay.addWidget(_legenda(f"Fonte: {r.get('fonte', '—')}."))
            if s.get("atualizando"):
                self.lbl_progresso = QLabel(f"Atualizando a base… {s.get('etapa') or ''}")
                lay.addWidget(self.lbl_progresso)
            elif s.get("erro") and s.get("falhou_em"):
                lay.addWidget(AlertBox(f"A última atualização falhou e a base anterior foi mantida: {s['erro']}",
                                       "warning"))
        elif s["estado"] == "carregando":
            self.lbl_progresso = QLabel(f"Carregando a base DFP… {s.get('etapa') or ''}")
            lay.addWidget(AlertBox("Preparando a base da CVM pela primeira vez (leva alguns segundos). "
                                   "Você pode continuar usando o OneWorld.", "info"))
            lay.addWidget(self.lbl_progresso)
        elif s["estado"] == "erro":
            lay.addWidget(AlertBox(f"A carga da base falhou: {s.get('erro', '')}", "error"))
        else:
            lay.addWidget(AlertBox("Nenhuma base DFP instalada. Baixe o pacote dfp_cia_aberta_AAAA.zip no portal "
                                   "de dados abertos da CVM e instale-o aqui.", "warning"))
        barra = QHBoxLayout()
        barra.addWidget(_botao("Instalar / atualizar base DFP (ZIP)…", self._escolher_dfp, primario=True))
        if s["estado"] in ("pronto", "erro") and not s.get("atualizando"):
            barra.addWidget(_botao("Recarregar base", self._recarregar_dfp))
        if s["estado"] == "pronto":
            barra.addWidget(_botao("Explorar companhias", lambda: self.abas.setCurrentIndex(1)))
            barra.addWidget(_botao("Abrir indicadores no Dashboard",
                                   lambda: self._abrir_no_dashboard_chave("cvm:indicadores")))
        barra.addStretch(1)
        lay.addLayout(barra)
        return card

    def _escolher_dfp(self):
        caminho, _ = QFileDialog.getOpenFileName(self, "Pacote DFP da CVM (dfp_cia_aberta_AAAA.zip)", "",
                                                 "Pacote ZIP (*.zip)")
        if caminho:
            self._instalar_dfp(Path(caminho))

    def _instalar_dfp(self, caminho: Path):
        r = bp.instalar_dfp(caminho)
        if r["ok"]:
            self.janela.flash(r["mensagem"])
        else:
            self.estado["dx_erro"] = r["mensagem"]
        self.estado["dx_aba"] = 0
        self.janela.reconstruir_pagina()

    def _recarregar_dfp(self):
        dfp.iniciar(forcar=True)
        self.janela.flash("Recarregando a base DFP em segundo plano.")
        self.janela.reconstruir_pagina()

    # ── Cards das bases do usuário ──
    def _card_base(self, b) -> QFrame:
        card, lay = _card()
        lay.addWidget(QLabel(f"<b>{b.nome}</b>"))
        meta = (f"{b.origem or 'origem não informada'} · arquivo {b.arquivo} · {int(b.linhas):,} linhas · "
                f"{int(b.colunas)} colunas · adicionada em {b.adicionada_em}").replace(",", ".")
        lay.addWidget(_legenda(meta))
        if b.descricao:
            lay.addWidget(_legenda(b.descricao))
        barra = QHBoxLayout()
        barra.addWidget(_botao("Ver dados", lambda i=int(b.id): self._alternar_ver(i)))
        barra.addWidget(_botao("Usar no Dashboard", lambda i=int(b.id): self._abrir_no_dashboard_chave(f"base:{i}"),
                               primario=True))
        chk = QCheckBox("Usar na Orientação IA")
        chk.setToolTip("Ao perguntar à IA externa, a estrutura e 5 linhas de amostra desta base são enviadas "
                       "ao provedor do modelo.")
        chk.setChecked(bool(b.usar_na_ia))
        chk.toggled.connect(lambda marcado, i=int(b.id): self._definir_ia(i, marcado))
        barra.addWidget(chk)
        barra.addStretch(1)
        barra.addWidget(_botao("Excluir", lambda i=int(b.id), n=b.nome: self._excluir(i, n)))
        lay.addLayout(barra)
        return card

    def _alternar_ver(self, id_: int):
        self.estado["dx_ver"] = None if self.estado.get("dx_ver") == id_ else id_
        self.janela.reconstruir_pagina()

    def _previa_base(self, id_: int) -> QWidget:
        card, lay = _card()
        try:
            df = bp.carregar(id_, limite=500)
            lay.addWidget(_legenda("Primeiras 500 linhas. Para analisar a base inteira, use o Dashboard."))
            lay.addWidget(PaginatedTableWidget(df, linhas_por_pagina=self.janela.cfg["linhas"], status_cols=()))
        except (bp.ErroBase, OSError) as ex:
            lay.addWidget(AlertBox(f"Não foi possível abrir a base: {ex}", "error"))
        return card

    def _definir_ia(self, id_: int, marcado: bool):
        bp.definir_uso_ia(id_, marcado)

    def _excluir(self, id_: int, nome: str):
        r = QMessageBox.question(self, "Excluir base", f"Excluir a base '{nome}'? O arquivo original não é afetado.")
        if r == QMessageBox.StandardButton.Yes:
            bp.remover(id_)
            if self.estado.get("dx_ver") == id_:
                self.estado["dx_ver"] = None
            self.janela.flash(f"Base '{nome}' excluída.")
            self.janela.reconstruir_pagina()

    # ── Formulário de adição (arquivo → prévia → confirmação) ──
    def _form_adicionar(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(10)
        barra = QHBoxLayout()
        barra.addWidget(_botao("Selecionar arquivo (CSV, TSV, TXT, XLSX, JSON ou ZIP)…", self._escolher_arquivo))
        arq: Path | None = self.estado.get("dx_arq")
        if arq:
            barra.addWidget(QLabel(f"Arquivo: <b>{arq.name}</b>"))
            barra.addWidget(_botao("Limpar", self._limpar_form))
        barra.addStretch(1)
        lay.addLayout(barra)
        if not arq:
            lay.addWidget(_legenda(
                "Aceita arquivos de dados abertos (CVM, dados.gov.br, IBGE…): detecta sozinho a codificação "
                "(UTF-8 ou Latin-1), o separador (; , tab) e números no formato brasileiro (1.234,56)."))
            return w
        try:
            pre = bp.pre_visualizar(arq, self.estado.get("dx_membro"))
        except (bp.ErroBase, OSError, ValueError) as ex:
            lay.addWidget(AlertBox(f"Não foi possível ler o arquivo: {ex}", "error"))
            return w
        if pre["dfp_ano"]:
            lay.addWidget(AlertBox(f"Este ZIP é o pacote DFP da CVM de {pre['dfp_ano']}. Ele é instalado como a "
                                   "base DFP (e não como uma base genérica).", "info"))
            lay.addWidget(_botao(f"Instalar como base DFP {pre['dfp_ano']}", lambda: self._instalar_dfp(arq),
                                 primario=True), alignment=Qt.AlignmentFlag.AlignLeft)
            return w
        if len(pre["membros"]) > 1:
            cb = QComboBox()
            for nome, tam in pre["membros"]:
                cb.addItem(f"{nome} ({tam / 1024:,.0f} KB)".replace(",", "."), nome)
            idx = cb.findData(pre.get("membro"))
            cb.setCurrentIndex(max(idx, 0))
            cb.currentIndexChanged.connect(self._mudar_membro_factory(cb))
            lay.addWidget(QLabel("O ZIP tem mais de um arquivo; escolha qual importar:"))
            lay.addWidget(cb)
        df = pre["df"]
        tecnico = []
        if pre["codificacao"]:
            tecnico.append(f"codificação {pre['codificacao']}")
        if pre["separador"]:
            tecnico.append(f"separador {pre['separador']!r}".replace("'\\t'", "tab"))
        numeros = sum(1 for t in pre["colunas"].values() if t == "numero")
        lay.addWidget(_legenda(f"Prévia (primeiras linhas) — {len(df.columns)} colunas, {numeros} numéricas"
                               + (f" · {', '.join(tecnico)}" if tecnico else "")
                               + ". Colunas de código (CNPJ, CD_*, ID) e números com zero à esquerda ficam como texto."))
        lay.addWidget(PaginatedTableWidget(df.head(10), linhas_por_pagina=10, status_cols=()))

        form = QFormLayout()
        ed_nome = QLineEdit(self.estado.setdefault("dx_nome", bp.nome_sugerido(pre.get("membro") or arq)))
        ed_nome.textChanged.connect(lambda t: self.estado.__setitem__("dx_nome", t))
        cb_origem = QComboBox()
        cb_origem.setEditable(True)
        cb_origem.addItems(bp.ORIGENS_SUGERIDAS)
        cb_origem.setCurrentText(self.estado.get("dx_origem", "CVM" if "cvm" in arq.name.lower() else "dados.gov.br"))
        cb_origem.currentTextChanged.connect(lambda t: self.estado.__setitem__("dx_origem", t))
        ed_desc = QPlainTextEdit(self.estado.get("dx_desc", ""))
        ed_desc.setMaximumHeight(70)
        ed_desc.setPlaceholderText("Opcional: o que é esta base, período, como foi obtida.")
        ed_desc.textChanged.connect(lambda: self.estado.__setitem__("dx_desc", ed_desc.toPlainText()))
        form.addRow("Nome da base *", ed_nome)
        form.addRow("Origem", cb_origem)
        form.addRow("Descrição", ed_desc)
        lay.addLayout(form)
        chk_ia = QCheckBox("Liberar para a Orientação IA (envia estrutura e 5 linhas de amostra ao provedor)")
        chk_ia.setChecked(bool(self.estado.get("dx_ia", False)))
        chk_ia.toggled.connect(lambda v: self.estado.__setitem__("dx_ia", v))
        lay.addWidget(chk_ia)

        def confirmar():
            ok = bp.adicionar_em_segundo_plano(
                arq, ed_nome.text(), ed_desc.toPlainText(), cb_origem.currentText(),
                membro=pre.get("membro") if pre["membros"] else None, usar_na_ia=chk_ia.isChecked())
            if not ok:
                self.estado["dx_erro"] = "Já há uma importação em andamento. Aguarde terminar."
            else:
                self._limpar_form(reconstruir=False)
            self.janela.reconstruir_pagina()

        lay.addWidget(_botao("Confirmar e adicionar base", confirmar, primario=True),
                      alignment=Qt.AlignmentFlag.AlignLeft)
        return w

    def _mudar_membro_factory(self, cb: QComboBox):
        def mudar(_):
            self.estado["dx_membro"] = cb.currentData()
            self.estado.pop("dx_nome", None)
            self.janela.reconstruir_pagina()
        return mudar

    def _escolher_arquivo(self):
        caminho, _ = QFileDialog.getOpenFileName(self, "Adicionar base pública", "", FILTRO_ARQUIVOS)
        if caminho:
            self.estado.update(dx_arq=Path(caminho), dx_aba=0)
            for k in ("dx_membro", "dx_nome", "dx_desc"):
                self.estado.pop(k, None)
            self.janela.reconstruir_pagina()

    def _limpar_form(self, reconstruir: bool = True):
        for k in ("dx_arq", "dx_membro", "dx_nome", "dx_desc", "dx_ia", "dx_origem"):
            self.estado.pop(k, None)
        if reconstruir:
            self.janela.reconstruir_pagina()

    # ── Envio ao Dashboard ──
    def _abrir_no_dashboard(self, rotulo: str, df: pd.DataFrame | None = None):
        if df is not None:
            extras = self.estado.setdefault("bi_fontes_extras", {})
            extras.pop(rotulo, None)
            extras[rotulo] = df
            while len(extras) > _MAX_BASES_EXTRAS_BI:
                extras.pop(next(iter(extras)))
        self.estado["bi_fonte_inicial"] = rotulo
        self.estado["dash_aba_ativa"] = 0
        self.janela.navegar_para("Dashboard")

    def _abrir_no_dashboard_chave(self, chave: str):
        rotulo = next((r for r, f in bp.fontes_bi().items() if f[1] == chave), None)
        if rotulo is None:
            self.estado["dx_erro"] = "Esta base não está disponível para o Dashboard."
            self.janela.reconstruir_pagina()
            return
        self._abrir_no_dashboard(rotulo)

    # ══════════════════════ ABA 2 — EXPLORAR CVM ══════════════════════
    def _aba_cvm(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(12, 12, 12, 12)
        lay.setSpacing(12)
        if not dfp.pronta():
            lay.addWidget(AlertBox("A base DFP ainda não está pronta. Instale ou aguarde o carregamento na aba "
                                   "“Bases públicas”.", "warning"))
            lay.addStretch(1)
            return w
        ano = dfp.metadados().get("ano", "")
        lay.addWidget(_legenda(f"Demonstrações do exercício {ano} comparadas ao ano anterior. Valores em R$ "
                               "(já convertidos de “mil” para reais). Consolidado quando a companhia tem; "
                               "senão, individual."))
        lay.addWidget(self._subtitulo("Companhia"))
        self._ed_busca = QLineEdit(self.estado.get("dx_q", ""))
        self._ed_busca.setPlaceholderText("Nome, CNPJ ou código CVM — ex.: Petrobras, 33.000.167/0001-01")
        self._cb_emp = QComboBox()
        self._cb_demo = QComboBox()
        self._sp_nivel = QSpinBox()
        self._sp_nivel.setRange(1, 4)
        self._sp_nivel.setValue(self.estado.get("dx_nivel", 2))
        self._sp_nivel.setToolTip("Nível de detalhe do plano de contas (1 = totais; 4 = mais detalhado)")
        self.area_demo = QWidget()
        self.lay_demo = QVBoxLayout(self.area_demo)
        self.lay_demo.setContentsMargins(0, 0, 0, 0)
        self.lay_demo.setSpacing(8)

        lay.addWidget(self._ed_busca)
        lay.addWidget(self._cb_emp)
        linha = QHBoxLayout()
        linha.addWidget(QLabel("Demonstração:"))
        linha.addWidget(self._cb_demo, stretch=1)
        linha.addWidget(QLabel("Detalhe:"))
        linha.addWidget(self._sp_nivel)
        lay.addLayout(linha)
        lay.addWidget(self.area_demo)

        self._ed_busca.textChanged.connect(self._ao_buscar)
        self._cb_emp.currentIndexChanged.connect(self._ao_mudar_companhia)
        self._cb_demo.currentIndexChanged.connect(self._desenhar_demo)
        self._sp_nivel.valueChanged.connect(self._desenhar_demo)
        self._preencher_companhias(self.estado.get("dx_cnpj"))

        lay.addWidget(Divider())
        lay.addWidget(self._secao_ranking())
        lay.addStretch(1)
        return w

    def _preencher_companhias(self, manter_cnpj: str | None = None):
        res = dfp.buscar_companhias(self._ed_busca.text(), limite=50)
        self._cb_emp.blockSignals(True)
        self._cb_emp.clear()
        for r in res.itertuples(index=False):
            self._cb_emp.addItem(f"{r[0]} — {r[1]}", r[1])
        i = self._cb_emp.findData(manter_cnpj) if manter_cnpj else -1
        if res.empty:
            self._cb_emp.addItem("Nenhuma companhia encontrada")
        self._cb_emp.setCurrentIndex(max(i, 0))
        self._cb_emp.blockSignals(False)
        self._ao_mudar_companhia()

    def _ao_buscar(self, texto: str):
        self.estado["dx_q"] = texto
        self._preencher_companhias()

    def _ao_mudar_companhia(self, *_):
        cnpj = self._cb_emp.currentData()
        self.estado["dx_cnpj"] = cnpj
        self._cb_demo.blockSignals(True)
        self._cb_demo.clear()
        if cnpj:
            for d in dfp.demonstracoes_da_companhia(cnpj):
                self._cb_demo.addItem(f"{dfp.rotulo_demonstracao(d)} ({d})", d)
            i = self._cb_demo.findData(self.estado.get("dx_demo", "DRE"))
            self._cb_demo.setCurrentIndex(max(i, 0))
        self._cb_demo.blockSignals(False)
        self._desenhar_demo()

    def _desenhar_demo(self, *_):
        while self.lay_demo.count():
            item = self.lay_demo.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        cnpj, demo = self._cb_emp.currentData(), self._cb_demo.currentData()
        self.estado["dx_demo"], self.estado["dx_nivel"] = demo, self._sp_nivel.value()
        if not cnpj or not demo:
            self.lay_demo.addWidget(AlertBox("Nenhuma demonstração para exibir. Refine a busca.", "info"))
            return
        df = dfp.demonstracao(cnpj, demo, self._sp_nivel.value())
        if df.empty:
            self.lay_demo.addWidget(AlertBox("Esta demonstração não tem linhas neste nível de detalhe.", "info"))
            return
        nome = self._cb_emp.currentText().split(" — ")[0]
        a1, a0 = dfp.anos()
        exibir = df.copy()
        for c in (str(a1), str(a0)):
            exibir[c] = exibir[c].map(_num)
        self.lay_demo.addWidget(PaginatedTableWidget(exibir, linhas_por_pagina=self.janela.cfg["linhas"],
                                                     status_cols=()))
        self.lay_demo.addWidget(_legenda("Variação = ano atual sobre o anterior. Custos e despesas são negativos: "
                                         "+X% significa que cresceram em módulo."))
        barra = QHBoxLayout()
        rotulo = f"Base pública: CVM DFP {a1} — {nome} — {dfp.rotulo_demonstracao(demo)}"
        barra.addWidget(_botao("Abrir no Dashboard", lambda: self._abrir_no_dashboard(rotulo, self._para_bi(df)),
                               primario=True))
        barra.addWidget(_botao("Exportar CSV", lambda: self.janela._exportar_csv_dialogo(
            df, f"dfp_{a1}_{demo}_{cnpj.replace('/', '').replace('.', '').replace('-', '')}.csv")))
        barra.addStretch(1)
        self.lay_demo.addLayout(barra)

    @staticmethod
    def _para_bi(df: pd.DataFrame) -> pd.DataFrame:
        """Variação ('+66,4%') é texto de exibição; no Dashboard ela só atrapalha."""
        return df.drop(columns=["Variação"], errors="ignore")

    def _secao_ranking(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)
        lay.addWidget(self._subtitulo("Ranking de companhias"))
        metricas = ["Receita", "Lucro líquido", "Ativo total", "Patrimônio líquido", "Caixa operacional",
                    "Margem líquida", "ROE", "ROA"]
        cb_m, cb_o, sp_n = QComboBox(), QComboBox(), QSpinBox()
        cb_m.addItems(metricas)
        cb_m.setCurrentText(self.estado.get("dx_rk_m", "Receita"))
        cb_o.addItems(["Maiores", "Menores"])
        cb_o.setCurrentText(self.estado.get("dx_rk_o", "Maiores"))
        sp_n.setRange(3, 50)
        sp_n.setValue(self.estado.get("dx_rk_n", 10))
        barra = QHBoxLayout()
        for rot, ctrl in (("Métrica:", cb_m), ("Ordem:", cb_o), ("Quantidade:", sp_n)):
            barra.addWidget(QLabel(rot))
            barra.addWidget(ctrl)
        barra.addStretch(1)
        lay.addLayout(barra)
        area = QVBoxLayout()
        lay.addLayout(area)

        def desenhar(*_):
            self.estado.update(dx_rk_m=cb_m.currentText(), dx_rk_o=cb_o.currentText(), dx_rk_n=sp_n.value())
            while area.count():
                it = area.takeAt(0)
                if it.widget():
                    it.widget().deleteLater()
            ind = dfp.indicadores_companhias()
            m = cb_m.currentText()
            ind = ind.dropna(subset=[m]).sort_values(m, ascending=cb_o.currentText() == "Menores")
            top = ind.head(sp_n.value())
            cols = ["Companhia", "Escopo", "Receita", "Lucro líquido", "Ativo total", "Patrimônio líquido",
                    "Margem líquida", "ROE"]
            tab = top[cols].copy()
            for c in ("Receita", "Lucro líquido", "Ativo total", "Patrimônio líquido"):
                tab[c] = tab[c].map(lambda v: "" if pd.isna(v) else brl(v))
            for c in ("Margem líquida", "ROE"):
                tab[c] = tab[c].map(_pct)
            tab.insert(0, "#", range(1, len(tab) + 1))
            area.addWidget(PaginatedTableWidget(tab, linhas_por_pagina=max(10, sp_n.value()), status_cols=()))
            area.addWidget(_legenda("Exercício mais recente da base; consolidado quando existe. Bancos e seguradoras "
                                    "têm plano de contas próprio: Receita e margens podem não ser comparáveis."))
            btns = QHBoxLayout()
            btns.addWidget(_botao("Abrir todas as companhias no Dashboard",
                                  lambda: self._abrir_no_dashboard_chave("cvm:indicadores"), primario=True))
            btns.addWidget(_botao("Exportar ranking (CSV)", lambda: self.janela._exportar_csv_dialogo(
                top, f"ranking_dfp_{m.lower().replace(' ', '_')}.csv")))
            btns.addStretch(1)
            area.addLayout(btns)

        for c in (cb_m, cb_o):
            c.currentIndexChanged.connect(desenhar)
        sp_n.valueChanged.connect(desenhar)
        desenhar()
        return w

    # ══════════════════════ ABAS 3 e 4 ══════════════════════
    def _aba_planilha(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(12, 12, 12, 12)
        lay.setSpacing(12)
        lay.addWidget(_legenda("Para planilhas do seu próprio negócio (operações e cadastros). Para dados abertos "
                               "de referência, use a aba “Bases públicas”."))
        lay.addWidget(ImportarPlanilhaWidget(self.janela, destino_fixo=None, chave_estado="impex"))
        lay.addStretch(1)
        return w

    def _aba_historico(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(12, 12, 12, 12)
        h = db.historico_arquivos()
        if h.empty:
            lay.addWidget(AlertBox("Nenhum arquivo recebido.", "info"))
        else:
            lay.addWidget(PaginatedTableWidget(h, linhas_por_pagina=self.janela.cfg["linhas"], status_cols=()))
        lay.addStretch(1)
        return w
