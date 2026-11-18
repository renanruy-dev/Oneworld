"""Dashboard Desktop (PyQt6) do módulo de BI do OneWorld.
Adaptação da interface analítica mantendo 100% das regras e fluxo puro de BI:
seleção de dados, tipagem de datas, filtros inclusivos, KPIs configuráveis,
gráficos dinâmicos (barras, linhas, histograma) e exportação.
"""
from __future__ import annotations

import math
import sqlite3
from csv import Error as ErroCSV
from hashlib import sha256
from io import BytesIO
from pathlib import Path
from sqlite3 import Error as ErroSQLite
from zipfile import BadZipFile

import pandas as pd
from PyQt6.QtCore import QDate, QPointF, QRectF, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDialog,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from . import backend, database
from .analises import preparar_grafico
from .filtros import aplicar_filtros
from .fontes_sqlite import carregar_tabela, listar_tabelas
from .formatacao import formatar_valor_kpi
from .frontend import (
    AlertBox,
    CVMComparacaoPainel,
    Divider,
    ExpanderWidget,
    MetricCard,
    PaginatedTableWidget,
)
from .indicadores import OPERACOES, calcular_kpi
from .metadados import ErroBI, configurar_datas, inspecionar_colunas
from .tema import paleta_atual

ROTULOS = {
    "contagem": "Contagem de registros",
    "distintos": "Valores distintos",
    "soma": "Soma",
    "media": "Média",
    "minimo": "Mínimo",
    "maximo": "Máximo",
}
EXEMPLOS = Path(__file__).resolve().parent.parent / "exemplos"


class BIChartWidget(QFrame):
    """Gráfico analítico vetorial nativo (PyQt6) desenhado via QPainter.
    Suporta tipos: barras (categórico), linhas (temporal/sequencial) e histograma (intervalos).
    """

    def __init__(
        self,
        tabela: pd.DataFrame,
        tipo: str,
        cor: str,
        cfg: dict,
        formato_moeda: bool = False,
    ):
        super().__init__()
        self.setObjectName("OwCard")
        self._tabela = tabela
        self._tipo = tipo
        self._cor = QColor(cor)
        self._cfg = cfg
        self._moeda = formato_moeda
        self.setMinimumHeight(280)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        self._dados: list[tuple[str, float]] = []
        if not tabela.empty and len(tabela.columns) >= 2:
            c_eixo, c_val = tabela.columns[0], tabela.columns[1]
            for _, r in tabela.iterrows():
                try:
                    v = float(r[c_val]) if pd.notna(r[c_val]) else 0.0
                except (ValueError, TypeError):
                    v = 0.0
                self._dados.append((str(r[c_eixo]), v))

    def paintEvent(self, event):
        super().paintEvent(event)
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        pal = paleta_atual(self._cfg)
        c_texto = QColor(pal.get("text", "#1E1E24"))
        c_muted = QColor(pal.get("muted", "#6C6B7B"))
        c_borda = QColor(pal.get("border", "#D9D8E2"))

        w, h = self.width(), self.height()
        margem_esq, margem_dir, margem_topo, margem_base = 56, 20, 26, 44
        area_w = max(10, w - margem_esq - margem_dir)
        area_h = max(10, h - margem_topo - margem_base)

        if not self._dados:
            p.setPen(c_muted)
            p.drawText(QRectF(0, 0, w, h), Qt.AlignmentFlag.AlignCenter, "Sem dados válidos para o gráfico.")
            p.end()
            return

        valores = [v for _, v in self._dados]
        min_v = min(valores)
        max_v = max(valores)
        if min_v > 0 or self._tipo in ("barras", "histograma"):
            min_v = 0.0
        if max_v <= min_v:
            max_v = min_v + 1.0
        intervalo_v = max_v - min_v

        fonte_peq = QFont("Segoe UI", 8)
        p.setFont(fonte_peq)
        for i in range(5):
            frac = i / 4.0
            y = margem_topo + area_h * (1.0 - frac)
            p.setPen(QPen(c_borda, 1, Qt.PenStyle.DashLine))
            p.drawLine(int(margem_esq), int(y), int(w - margem_dir), int(y))

            val_eixo = min_v + intervalo_v * frac
            if abs(val_eixo) >= 1000:
                txt_eixo = f"{val_eixo / 1000:.1f}k".replace(".0k", "k")
            elif val_eixo == int(val_eixo):
                txt_eixo = str(int(val_eixo))
            else:
                txt_eixo = f"{val_eixo:.1f}"
            p.setPen(c_muted)
            p.drawText(
                QRectF(4, y - 9, margem_esq - 8, 18),
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                txt_eixo,
            )

        n = len(self._dados)
        passo = area_w / max(1, n)

        if self._tipo in ("barras", "histograma"):
            larg_barra = min(56.0, max(8.0, passo * 0.65)) if self._tipo == "barras" else max(4.0, passo * 0.88)
            for idx, (rotulo, valor) in enumerate(self._dados):
                alt_barra = ((valor - min_v) / intervalo_v) * area_h
                x = margem_esq + idx * passo + (passo - larg_barra) / 2.0
                y = margem_topo + area_h - alt_barra

                caminho = QPainterPath()
                caminho.addRoundedRect(QRectF(x, y, larg_barra, max(2.0, alt_barra)), 4, 4)
                p.fillPath(caminho, self._cor)

                txt_val = str(int(valor) if valor == int(valor) else f"{valor:.2f}")
                p.setPen(c_texto)
                p.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
                p.drawText(
                    QRectF(margem_esq + idx * passo, max(2, y - 18), passo, 16),
                    Qt.AlignmentFlag.AlignCenter,
                    txt_val,
                )

                p.setPen(c_muted)
                p.setFont(fonte_peq)
                p.drawText(
                    QRectF(margem_esq + idx * passo, margem_topo + area_h + 6, passo, 32),
                    Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop | Qt.TextFlag.TextWordWrap,
                    rotulo,
                )
        elif self._tipo == "linhas":
            pontos = []
            for idx, (rotulo, valor) in enumerate(self._dados):
                alt_pt = ((valor - min_v) / intervalo_v) * area_h
                x = margem_esq + idx * passo + passo / 2.0
                y = margem_topo + area_h - alt_pt
                pontos.append((x, y, rotulo, valor))

            # Linha contínua
            p.setPen(QPen(self._cor, 2.5))
            for i in range(len(pontos) - 1):
                p.drawLine(
                    QPointF(pontos[i][0], pontos[i][1]),
                    QPointF(pontos[i + 1][0], pontos[i + 1][1]),
                )

            # Pontos e rótulos
            for x, y, rotulo, valor in pontos:
                p.setBrush(self._cor)
                p.setPen(QPen(c_texto, 1))
                p.drawEllipse(QPointF(x, y), 4, 4)

                txt_val = str(int(valor) if valor == int(valor) else f"{valor:.2f}")
                p.setPen(c_texto)
                p.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
                p.drawText(
                    QRectF(x - passo / 2.0, max(2, y - 18), passo, 16),
                    Qt.AlignmentFlag.AlignCenter,
                    txt_val,
                )

                p.setPen(c_muted)
                p.setFont(fonte_peq)
                p.drawText(
                    QRectF(x - passo / 2.0, margem_topo + area_h + 6, passo, 32),
                    Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop | Qt.TextFlag.TextWordWrap,
                    rotulo,
                )

        p.end()


class BIDashboardWidget(QWidget):
    """Componente completo de Dashboard e Business Intelligence para PyQt6."""

    dados_atualizados = pyqtSignal()

    def __init__(self, cfg: dict | None = None, parent=None, carregar_exemplos: bool = True):
        super().__init__(parent)
        self.cfg = cfg or {"cor": "#5B4FC4", "cor2": "#00A86B", "linhas": 10}
        self._carregar_exemplos_iniciais = carregar_exemplos

        self.fontes_disponiveis: dict[str, Path | tuple | pd.DataFrame] = {}
        self.df_bruto: pd.DataFrame | None = None
        self.df_tipado: pd.DataFrame | None = None
        self.df_filtrado: pd.DataFrame = pd.DataFrame()
        self.meta: dict = {}
        self.falhas_datas: dict[str, int] = {}
        self.erro_atual: str | None = None

        # Configurações de estado
        self.num_kpis = 1
        self.kpi_cfgs: list[dict] = [
            {"operacao": "contagem", "coluna": None, "titulo": "KPI 1", "formato": "Número", "simbolo": "R$"}
            for _ in range(4)
        ]
        self.kpi_resultados = []
        self.grafico_cfg: dict = {"tipo": "barras", "intervalos": 10, "periodo": "dia"}
        self.tabela_grafico: pd.DataFrame = pd.DataFrame()
        self.filtros_ativos: list[dict] = []

        self._iniciar_fontes()
        self._construir_ui()
        if self.fontes_disponiveis:
            primeira = list(self.fontes_disponiveis.keys())[0]
            self.selecionar_fonte(primeira)
        else:
            self._atualizar_visibilidade_estado()

    def _iniciar_fontes(self):
        self.fontes_disponiveis.clear()
        if self._carregar_exemplos_iniciais and EXEMPLOS.exists():
            for p in sorted(EXEMPLOS.glob("*.csv")):
                self.fontes_disponiveis[f"Exemplo: {p.stem}"] = p

    def carregar_exemplos_demo(self):
        """Carrega os conjuntos de exemplo sob demanda do usuário."""
        if EXEMPLOS.exists():
            for p in sorted(EXEMPLOS.glob("*.csv")):
                self.fontes_disponiveis[f"Exemplo: {p.stem}"] = p
        self._atualizar_combo_fontes()
        if self.fontes_disponiveis:
            primeira = list(self.fontes_disponiveis.keys())[0]
            self.cb_dataset.setCurrentText(primeira)
            self.selecionar_fonte(primeira)

    def _atualizar_visibilidade_estado(self):
        tem_dados = self.df_tipado is not None
        if hasattr(self, "card_vazio"):
            self.card_vazio.setVisible(not tem_dados)
        if hasattr(self, "conteudo_analise"):
            self.conteudo_analise.setVisible(tem_dados)

    def _construir_ui(self):
        self.lay_principal = QVBoxLayout(self)
        self.lay_principal.setContentsMargins(0, 0, 0, 0)
        self.lay_principal.setSpacing(14)

        # ── 1. Barra Superior: Seleção de Dados (Card Toolbar) ──
        card_fonte = QFrame()
        card_fonte.setObjectName("ToolbarCard")
        lay_card_fonte = QVBoxLayout(card_fonte)
        lay_card_fonte.setContentsMargins(16, 12, 16, 12)
        lay_card_fonte.setSpacing(6)

        barra_dados = QHBoxLayout()
        barra_dados.setSpacing(12)

        lbl_fonte = QLabel("Conjunto de dados:")
        lbl_fonte.setObjectName("MetricLabel")
        barra_dados.addWidget(lbl_fonte)

        self.cb_dataset = QComboBox()
        self.cb_dataset.setPlaceholderText("Selecione ou adicione uma fonte de dados...")
        self.cb_dataset.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._atualizar_combo_fontes()
        self.cb_dataset.currentTextChanged.connect(self._ao_mudar_fonte)
        barra_dados.addWidget(self.cb_dataset, stretch=2)

        self.chk_banco = QCheckBox("Incluir banco local")
        self.chk_banco.toggled.connect(self._ao_alternar_banco_local)
        barra_dados.addWidget(self.chk_banco)

        btn_upload = QPushButton("+ Adicionar arquivo")
        btn_upload.setObjectName("PrimaryBtn")
        btn_upload.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_upload.clicked.connect(self._ao_fazer_upload)
        barra_dados.addWidget(btn_upload)

        lay_card_fonte.addLayout(barra_dados)

        self.lbl_caption = QLabel(
            "Escolha uma tabela do banco local ou importe arquivos (CSV, Excel, JSON) para explorar indicadores e gráficos."
        )
        self.lbl_caption.setObjectName("Caption")
        lay_card_fonte.addWidget(self.lbl_caption)

        self.lay_principal.addWidget(card_fonte)

        self.cvm_painel = CVMComparacaoPainel(
            self.cfg,
            self._obter_resumo_negocio_seguro,
            parent=self,
        )
        self.lay_principal.addWidget(self.cvm_painel)

        self.caixa_alerta = AlertBox("", "warning")
        self.caixa_alerta.setVisible(False)
        self.lay_principal.addWidget(self.caixa_alerta)

        # ── Estado Vazio (quando nenhum dataset foi carregado) ──
        self.card_vazio = QFrame()
        self.card_vazio.setObjectName("EmptyStateCard")
        lay_vazio = QVBoxLayout(self.card_vazio)
        lay_vazio.setContentsMargins(28, 32, 28, 32)
        lay_vazio.setSpacing(10)

        lbl_vt = QLabel("Nenhuma fonte de dados selecionada no Explorador BI")
        lbl_vt.setObjectName("EmptyTitle")
        lbl_vt.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay_vazio.addWidget(lbl_vt)

        lbl_vd = QLabel(
            "O módulo de BI inicia limpo, sem conjuntos fictícios pré-carregados.\n"
            "Adicione uma planilha/arquivo externo ou habilite a leitura das tabelas do banco local."
        )
        lbl_vd.setObjectName("Caption")
        lbl_vd.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_vd.setWordWrap(True)
        lay_vazio.addWidget(lbl_vd)

        linha_bv = QHBoxLayout()
        linha_bv.addStretch(1)

        btn_v_arq = QPushButton("+ Adicionar arquivo (CSV / XLSX / JSON)")
        btn_v_arq.setObjectName("PrimaryBtn")
        btn_v_arq.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_v_arq.clicked.connect(self._ao_fazer_upload)
        linha_bv.addWidget(btn_v_arq)

        btn_v_db = QPushButton("Carregar tabelas do banco local")
        btn_v_db.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_v_db.clicked.connect(lambda: self.chk_banco.setChecked(True))
        linha_bv.addWidget(btn_v_db)

        btn_v_demo = QPushButton("Carregar dados de demonstração")
        btn_v_demo.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_v_demo.clicked.connect(self.carregar_exemplos_demo)
        linha_bv.addWidget(btn_v_demo)

        linha_bv.addStretch(1)
        lay_vazio.addSpacing(6)
        lay_vazio.addLayout(linha_bv)
        self.lay_principal.addWidget(self.card_vazio)

        # ── Container de Análise Ativa (exibido quando há dataset carregado) ──
        self.conteudo_analise = QWidget()
        lay_analise = QVBoxLayout(self.conteudo_analise)
        lay_analise.setContentsMargins(0, 0, 0, 0)
        lay_analise.setSpacing(14)

        # ── 2. Faixa de KPIs em Destaque no Topo ──
        self.lay_kpi_cards = QHBoxLayout()
        self.lay_kpi_cards.setSpacing(12)
        lay_analise.addLayout(self.lay_kpi_cards)

        # ── 3. Palco Principal: Gráfico Configurável em Card Dedicado ──
        card_graf = QFrame()
        card_graf.setObjectName("OwCard")
        lay_card_graf = QVBoxLayout(card_graf)
        lay_card_graf.setContentsMargins(16, 14, 16, 14)
        lay_card_graf.setSpacing(12)

        barra_graf = QHBoxLayout()
        barra_graf.setSpacing(10)
        lbl_tit_graf = QLabel("Gráfico analítico")
        lbl_tit_graf.setObjectName("SectionTitle")
        barra_graf.addWidget(lbl_tit_graf)
        barra_graf.addStretch(1)

        barra_graf.addWidget(QLabel("Tipo:"))
        self.cb_graf_tipo = QComboBox()
        self.cb_graf_tipo.currentTextChanged.connect(self._ao_mudar_grafico_tipo)
        barra_graf.addWidget(self.cb_graf_tipo)

        self.lbl_graf_grupo = QLabel("Agrupar por:")
        barra_graf.addWidget(self.lbl_graf_grupo)
        self.cb_graf_grupo = QComboBox()
        self.cb_graf_grupo.currentTextChanged.connect(lambda v: self._ao_mudar_grafico_campo("grupo", v))
        barra_graf.addWidget(self.cb_graf_grupo)

        self.lbl_graf_op = QLabel("Agregação:")
        barra_graf.addWidget(self.lbl_graf_op)
        self.cb_graf_op = QComboBox()
        for op in ["contagem", "soma", "media", "minimo", "maximo"]:
            self.cb_graf_op.addItem(ROTULOS.get(op, op), userData=op)
        self.cb_graf_op.currentIndexChanged.connect(lambda _: self._ao_mudar_grafico_campo("operacao", self.cb_graf_op.currentData()))
        barra_graf.addWidget(self.cb_graf_op)

        self.lbl_graf_medida = QLabel("Medida:")
        barra_graf.addWidget(self.lbl_graf_medida)
        self.cb_graf_medida = QComboBox()
        self.cb_graf_medida.currentTextChanged.connect(lambda v: self._ao_mudar_grafico_campo("coluna", v))
        barra_graf.addWidget(self.cb_graf_medida)

        self.lbl_graf_periodo = QLabel("Período:")
        barra_graf.addWidget(self.lbl_graf_periodo)
        self.cb_graf_periodo = QComboBox()
        self.cb_graf_periodo.addItems(["dia", "mes"])
        self.cb_graf_periodo.currentTextChanged.connect(lambda v: self._ao_mudar_grafico_campo("periodo", v))
        barra_graf.addWidget(self.cb_graf_periodo)

        self.lbl_graf_bins = QLabel("Intervalos:")
        barra_graf.addWidget(self.lbl_graf_bins)
        self.sp_graf_bins = QSpinBox()
        self.sp_graf_bins.setRange(1, 100)
        self.sp_graf_bins.setValue(10)
        self.sp_graf_bins.valueChanged.connect(lambda v: self._ao_mudar_grafico_campo("intervalos", v))
        barra_graf.addWidget(self.sp_graf_bins)

        lay_card_graf.addLayout(barra_graf)

        self.lay_grafico_container = QVBoxLayout()
        lay_card_graf.addLayout(self.lay_grafico_container)

        self.expander_dados_grafico = ExpanderWidget("Dados agregados do gráfico", aberto=False)
        self.lay_dados_grafico = QVBoxLayout()
        self.expander_dados_grafico.corpo_layout.addLayout(self.lay_dados_grafico)
        lay_card_graf.addWidget(self.expander_dados_grafico)

        lay_analise.addWidget(card_graf)

        # ── 4. Gavetas de Configuração (Filtros, KPIs e Datas recolhidas por padrão) ──
        self.expander_filtros = ExpanderWidget("Filtros configuráveis", aberto=False)
        self.lay_filtros_itens = QGridLayout()
        self.lay_filtros_itens.setHorizontalSpacing(18)
        self.lay_filtros_itens.setVerticalSpacing(8)
        self.expander_filtros.corpo_layout.addLayout(self.lay_filtros_itens)

        linha_rodape_filtros = QHBoxLayout()
        self.lbl_status_filtros = QLabel("0 de 0 registros após os filtros.")
        self.lbl_status_filtros.setObjectName("Caption")
        linha_rodape_filtros.addWidget(self.lbl_status_filtros)
        linha_rodape_filtros.addStretch(1)

        btn_limpar_filtros = QPushButton("Limpar filtros")
        btn_limpar_filtros.clicked.connect(self.limpar_filtros)
        linha_rodape_filtros.addWidget(btn_limpar_filtros)
        self.expander_filtros.corpo_layout.addLayout(linha_rodape_filtros)
        lay_analise.addWidget(self.expander_filtros)

        self.expander_kpi_cfg = ExpanderWidget("Configurar KPIs (1 a 4 indicadores)", aberto=False)
        linha_n_kpis = QHBoxLayout()
        linha_n_kpis.addWidget(QLabel("Quantidade de KPIs visíveis (1 a 4):"))
        self.sp_n_kpis = QSpinBox()
        self.sp_n_kpis.setRange(1, 4)
        self.sp_n_kpis.setValue(1)
        self.sp_n_kpis.valueChanged.connect(self._ao_mudar_qtd_kpis)
        linha_n_kpis.addWidget(self.sp_n_kpis)
        linha_n_kpis.addStretch(1)
        self.expander_kpi_cfg.corpo_layout.addLayout(linha_n_kpis)

        self.kpi_form_widgets: list[dict] = []
        for i in range(4):
            f_frame = QFrame()
            f_lay = QHBoxLayout(f_frame)
            f_lay.setContentsMargins(0, 4, 0, 4)

            ed_tit = QLineEdit(f"KPI {i + 1}")
            ed_tit.setFixedWidth(140)
            cb_op = QComboBox()
            for op in OPERACOES:
                cb_op.addItem(ROTULOS[op], userData=op)
            cb_col = QComboBox()
            cb_fmt = QComboBox()
            cb_fmt.addItems(["Número", "Percentual", "Moeda"])
            ed_simb = QLineEdit("R$")
            ed_simb.setFixedWidth(55)

            idx_k = i
            ed_tit.textChanged.connect(lambda t, k=idx_k: self._ao_mudar_kpi_campo(k, "titulo", t))
            cb_op.currentIndexChanged.connect(lambda _, k=idx_k: self._ao_mudar_kpi_campo(k, "operacao", cb_op.currentData()))
            cb_col.currentIndexChanged.connect(lambda _, k=idx_k: self._ao_mudar_kpi_campo(k, "coluna", cb_col.currentText()))
            cb_fmt.currentTextChanged.connect(lambda f, k=idx_k: self._ao_mudar_kpi_campo(k, "formato", f))
            ed_simb.textChanged.connect(lambda s, k=idx_k: self._ao_mudar_kpi_campo(k, "simbolo", s))

            f_lay.addWidget(QLabel(f"#{i+1}:"))
            f_lay.addWidget(ed_tit)
            f_lay.addWidget(cb_op)
            f_lay.addWidget(cb_col)
            f_lay.addWidget(cb_fmt)
            f_lay.addWidget(ed_simb)

            self.expander_kpi_cfg.corpo_layout.addWidget(f_frame)
            f_frame.setVisible(i == 0)
            self.kpi_form_widgets.append({
                "frame": f_frame, "titulo": ed_tit, "op": cb_op, "col": cb_col, "fmt": cb_fmt, "simb": ed_simb
            })

        lay_analise.addWidget(self.expander_kpi_cfg)

        self.expander_datas = ExpanderWidget("Tipos de colunas e datas", aberto=False)
        self.lbl_info_colunas = QLabel()
        self.lbl_info_colunas.setObjectName("Caption")
        self.expander_datas.corpo_layout.addWidget(self.lbl_info_colunas)

        linha_datas = QHBoxLayout()
        linha_datas.addWidget(QLabel("Coluna para data:"))
        self.cb_col_data = QComboBox()
        linha_datas.addWidget(self.cb_col_data, stretch=1)

        linha_datas.addWidget(QLabel("Formato:"))
        self.ed_formato_data = QLineEdit("%Y-%m-%d")
        self.ed_formato_data.setFixedWidth(110)
        linha_datas.addWidget(self.ed_formato_data)

        btn_aplicar_data = QPushButton("Interpretar como data")
        btn_aplicar_data.clicked.connect(self._ao_aplicar_datas)
        linha_datas.addWidget(btn_aplicar_data)
        self.expander_datas.corpo_layout.addLayout(linha_datas)

        self.lbl_falhas_data = QLabel()
        self.lbl_falhas_data.setObjectName("Caption")
        self.lbl_falhas_data.setStyleSheet("color: #C0392B;")
        self.expander_datas.corpo_layout.addWidget(self.lbl_falhas_data)

        lay_analise.addWidget(self.expander_datas)

        # ── 5. Registros Filtrados e Exportação em Card Dedicado ──
        card_tabela = QFrame()
        card_tabela.setObjectName("OwCard")
        lay_card_tab = QVBoxLayout(card_tabela)
        lay_card_tab.setContentsMargins(16, 14, 16, 14)
        lay_card_tab.setSpacing(10)

        linha_tabela_tit = QHBoxLayout()
        lbl_reg = QLabel("Registros filtrados")
        lbl_reg.setObjectName("SectionTitle")
        linha_tabela_tit.addWidget(lbl_reg)
        linha_tabela_tit.addStretch(1)

        btn_exportar = QPushButton("Exportar dados filtrados (CSV)")
        btn_exportar.setObjectName("PrimaryBtn")
        btn_exportar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_exportar.clicked.connect(self._ao_exportar_csv)
        linha_tabela_tit.addWidget(btn_exportar)
        lay_card_tab.addLayout(linha_tabela_tit)

        self.lay_tabela_container = QVBoxLayout()
        lay_card_tab.addLayout(self.lay_tabela_container)
        lay_analise.addWidget(card_tabela)

        self.lay_principal.addWidget(self.conteudo_analise)

    # ── Métodos de dados e seleção ──
    def _atualizar_combo_fontes(self):
        atual = self.cb_dataset.currentText()
        self.cb_dataset.blockSignals(True)
        self.cb_dataset.clear()
        for k in self.fontes_disponiveis:
            self.cb_dataset.addItem(k)
        if atual in self.fontes_disponiveis:
            self.cb_dataset.setCurrentText(atual)
        self.cb_dataset.blockSignals(False)

    def _ao_mudar_fonte(self, nome: str):
        if not nome or nome not in self.fontes_disponiveis:
            return
        self.selecionar_fonte(nome)

    def _ao_alternar_banco_local(self, checked: bool):
        # Limpa chaves de banco
        chaves_remover = [k for k in self.fontes_disponiveis if k.startswith("Banco local:")]
        for k in chaves_remover:
            del self.fontes_disponiveis[k]

        if checked:
            try:
                tabelas = listar_tabelas(database.DB_PATH)
                for t in tabelas:
                    self.fontes_disponiveis[f"Banco local: {t}"] = ("sqlite", t)
            except (ErroSQLite, OSError, ValueError):
                self._mostrar_aviso("Não foi possível abrir o banco local para leitura.")
        self._atualizar_combo_fontes()
        if checked and self.df_tipado is None and self.fontes_disponiveis:
            primeira = list(self.fontes_disponiveis.keys())[0]
            self.cb_dataset.setCurrentText(primeira)
            self.selecionar_fonte(primeira)
        elif not self.fontes_disponiveis:
            self.df_bruto = None
            self.df_tipado = None
            self.df_filtrado = pd.DataFrame()
            self._atualizar_visibilidade_estado()

    def _ao_fazer_upload(self):
        arquivos, _ = QFileDialog.getOpenFileNames(
            self,
            "Adicionar conjuntos de dados",
            "",
            "Arquivos suportados (*.csv *.xlsx *.json);;CSV (*.csv);;Excel (*.xlsx);;JSON (*.json)",
        )
        for arq in arquivos:
            p = Path(arq)
            try:
                df = backend.ler_arquivo(p)
                inspecionar_colunas(df)
                nome = f"Arquivo {len([k for k in self.fontes_disponiveis if k.startswith('Arquivo ')]) + 1}: {p.name}"
                self.fontes_disponiveis[nome] = df
            except Exception as exc:
                self._mostrar_aviso(f"Não foi possível ler o arquivo {p.name}: {exc}")
        self._atualizar_combo_fontes()
        if arquivos:
            ultimo = list(self.fontes_disponiveis.keys())[-1]
            self.cb_dataset.setCurrentText(ultimo)

    def adicionar_arquivo(self, caminho_ou_bytes, nome: str):
        """Interface programática para carregamento de arquivos."""
        try:
            if isinstance(caminho_ou_bytes, (str, Path)):
                df = backend.ler_arquivo(Path(caminho_ou_bytes))
            else:
                buf = BytesIO(caminho_ou_bytes)
                buf.name = nome
                df = backend.ler_arquivo(buf)
            inspecionar_colunas(df)
            chave = f"Arquivo {len([k for k in self.fontes_disponiveis if k.startswith('Arquivo ')]) + 1}: {nome}"
            self.fontes_disponiveis[chave] = df
            self._atualizar_combo_fontes()
            self.selecionar_fonte(chave)
            return True
        except Exception as exc:
            self._mostrar_aviso(f"Não foi possível ler o arquivo: {exc}")
            return False

    def selecionar_fonte(self, nome: str):
        if nome not in self.fontes_disponiveis:
            return
        fonte = self.fontes_disponiveis[nome]
        try:
            if isinstance(fonte, tuple) and fonte[0] == "sqlite":
                df = carregar_tabela(database.DB_PATH, fonte[1])
            elif isinstance(fonte, Path):
                df = backend.ler_arquivo(fonte)
            elif isinstance(fonte, pd.DataFrame):
                df = fonte.copy()
            else:
                df = backend.ler_arquivo(fonte)
            inspecionar_colunas(df)
            self.df_bruto = df.copy()
            self.df_tipado = df.copy()
            self.erro_atual = None
            self.caixa_alerta.setVisible(False)
        except Exception as exc:
            self.erro_atual = f"Não foi possível ler o conjunto de dados: {exc}"
            self._mostrar_aviso(self.erro_atual)
            self.df_bruto = None
            self.df_tipado = None
            self.df_filtrado = pd.DataFrame()
            self._atualizar_visibilidade_estado()
            return

        self._atualizar_visibilidade_estado()

        # Reseta configurações de filtro e opções de KPI/gráfico para o novo dataset
        self.filtros_ativos.clear()
        self.num_kpis = 1
        self.kpi_cfgs = [
            {"operacao": "contagem", "coluna": None, "titulo": f"KPI {i + 1}", "formato": "Número", "simbolo": "R$"}
            for i in range(4)
        ]
        self.sp_n_kpis.blockSignals(True)
        self.sp_n_kpis.setValue(1)
        self.sp_n_kpis.blockSignals(False)

        self._atualizar_metadados()
        self._reconstruir_controles_filtros()
        self._atualizar_opcoes_kpis()
        self._atualizar_opcoes_grafico()
        self.recalcular()

    def _mostrar_aviso(self, msg: str):
        self.erro_atual = msg if msg else None
        self.caixa_alerta.lbl.setText(msg)
        self.caixa_alerta.setVisible(bool(msg))

    def _atualizar_metadados(self):
        if self.df_tipado is None:
            self.meta = {}
            return
        self.meta = inspecionar_colunas(self.df_tipado)
        info = " | ".join(f"{c.nome} ({c.tipo})" for c in self.meta.values())
        self.lbl_info_colunas.setText(f"Colunas detectadas: {info}")

        candidatas = [n for n, c in self.meta.items() if c.tipo == "categoria"]
        self.cb_col_data.blockSignals(True)
        self.cb_col_data.clear()
        for cand in candidatas:
            self.cb_col_data.addItem(cand)
        self.cb_col_data.blockSignals(False)

    def _ao_aplicar_datas(self):
        coluna = self.cb_col_data.currentText()
        if not coluna or not self.df_bruto is not None:
            return
        formato = self.ed_formato_data.text().strip() or "%Y-%m-%d"
        self.configurar_datas([coluna], formato)

    def configurar_datas(self, colunas: list[str], formato: str = "%Y-%m-%d"):
        if self.df_bruto is None:
            return
        try:
            self.df_tipado, self.falhas_datas = configurar_datas(self.df_bruto, colunas, formato)
            self._mostrar_aviso("")
            txt_falhas = []
            for col, n_falhas in self.falhas_datas.items():
                if n_falhas > 0:
                    txt_falhas.append(f"{n_falhas} valores em {col!r} não correspondem ao formato.")
            self.lbl_falhas_data.setText(" ".join(txt_falhas))
            self._atualizar_metadados()
            self._reconstruir_controles_filtros()
            self._atualizar_opcoes_grafico()
            self.recalcular()
        except (ErroBI, ValueError, TypeError) as exc:
            self._mostrar_aviso(str(exc))

    # ── Filtros ──
    def _reconstruir_controles_filtros(self):
        # Limpa widgets de filtro anteriores
        while self.lay_filtros_itens.count():
            item = self.lay_filtros_itens.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                while item.layout().count():
                    sub = item.layout().takeAt(0)
                    if sub.widget():
                        sub.widget().deleteLater()

        if not self.meta:
            return

        self.filtro_widgets: dict[str, dict] = {}
        idx_grid = 0
        for nome, col in self.meta.items():
            if col.tipo not in ("categoria", "numero", "data"):
                continue

            linha = QHBoxLayout()
            chk_ativo = QCheckBox(nome)
            linha.addWidget(chk_ativo)

            ctrl_info = {"chk": chk_ativo, "tipo": col.tipo}

            if col.tipo == "categoria":
                valores_unicos = sorted(list(self.df_tipado[nome].dropna().astype(str).unique()))
                cb_val = QComboBox()
                cb_val.addItem("Todos", userData=None)
                for v in valores_unicos:
                    cb_val.addItem(v, userData=v)
                cb_val.setEnabled(False)
                linha.addWidget(cb_val, stretch=1)
                ctrl_info["combo"] = cb_val
                cb_val.currentIndexChanged.connect(lambda _: self._ao_filtro_alterado())
            elif col.tipo == "numero":
                sp_min = QDoubleSpinBox()
                sp_min.setRange(-1e12, 1e12)
                sp_min.setValue(-1e12)
                sp_min.setSpecialValueText("Mín")
                sp_min.setEnabled(False)

                sp_max = QDoubleSpinBox()
                sp_max.setRange(-1e12, 1e12)
                sp_max.setValue(-1e12)
                sp_max.setSpecialValueText("Máx")
                sp_max.setEnabled(False)

                linha.addWidget(QLabel("De:"))
                linha.addWidget(sp_min, stretch=1)
                linha.addWidget(QLabel("Até:"))
                linha.addWidget(sp_max, stretch=1)
                ctrl_info["min"] = sp_min
                ctrl_info["max"] = sp_max
                sp_min.valueChanged.connect(lambda _: self._ao_filtro_alterado())
                sp_max.valueChanged.connect(lambda _: self._ao_filtro_alterado())
            elif col.tipo == "data":
                de_min = QDateEdit()
                de_min.setCalendarPopup(True)
                de_min.setDisplayFormat("yyyy-MM-dd")
                de_min.setDate(QDate(2020, 1, 1))
                de_min.setEnabled(False)

                de_max = QDateEdit()
                de_max.setCalendarPopup(True)
                de_max.setDisplayFormat("yyyy-MM-dd")
                de_max.setDate(QDate(2030, 12, 31))
                de_max.setEnabled(False)

                linha.addWidget(QLabel("De:"))
                linha.addWidget(de_min, stretch=1)
                linha.addWidget(QLabel("Até:"))
                linha.addWidget(de_max, stretch=1)
                ctrl_info["min"] = de_min
                ctrl_info["max"] = de_max
                de_min.dateChanged.connect(lambda _: self._ao_filtro_alterado())
                de_max.dateChanged.connect(lambda _: self._ao_filtro_alterado())

            chk_nulos = QCheckBox("Incluir nulos")
            chk_nulos.setEnabled(False)
            linha.addWidget(chk_nulos)
            ctrl_info["nulos"] = chk_nulos
            chk_nulos.toggled.connect(lambda _: self._ao_filtro_alterado())

            def ao_ativar(checked, c=ctrl_info):
                for k, w in c.items():
                    if k != "chk" and k != "tipo":
                        w.setEnabled(checked)
                self._ao_filtro_alterado()

            chk_ativo.toggled.connect(ao_ativar)
            self.filtro_widgets[nome] = ctrl_info
            self.lay_filtros_itens.addLayout(linha, idx_grid // 2, idx_grid % 2)
            idx_grid += 1

    def _ao_filtro_alterado(self):
        self.filtros_ativos.clear()
        for nome, ctrl in getattr(self, "filtro_widgets", {}).items():
            if not ctrl["chk"].isChecked():
                continue
            tipo = ctrl["tipo"]
            cfg: dict = {"coluna": nome, "tipo": tipo, "incluir_nulos": ctrl["nulos"].isChecked()}
            if tipo == "categoria":
                val = ctrl["combo"].currentData()
                cfg["valores"] = [] if ctrl["combo"].currentIndex() == -1 else ([val] if val is not None else sorted(list(self.df_tipado[nome].dropna().astype(str).unique())))
            elif tipo == "numero":
                v_min = ctrl["min"].value()
                v_max = ctrl["max"].value()
                cfg["minimo"] = v_min if v_min != -1e12 else None
                cfg["maximo"] = v_max if v_max not in (-1e12, 1e12) else None
            elif tipo == "data":
                cfg["minimo"] = ctrl["min"].date().toString("yyyy-MM-dd")
                cfg["maximo"] = ctrl["max"].date().toString("yyyy-MM-dd")
            self.filtros_ativos.append(cfg)
        self.recalcular()

    def definir_filtro(
        self,
        coluna: str,
        ativo: bool = True,
        valores=None,
        minimo=None,
        maximo=None,
        incluir_nulos: bool = False,
    ):
        """Interface programática para configuração e teste de filtros."""
        self.filtros_ativos = [f for f in self.filtros_ativos if f.get("coluna") != coluna]
        if ativo and coluna in self.meta:
            tipo = self.meta[coluna].tipo
            cfg = {"coluna": coluna, "tipo": tipo, "incluir_nulos": incluir_nulos}
            if tipo == "categoria":
                cfg["valores"] = valores if valores is not None else []
            elif tipo in ("numero", "data"):
                cfg["minimo"] = minimo
                cfg["maximo"] = maximo
            self.filtros_ativos.append(cfg)
        self.recalcular()

    def limpar_filtros(self):
        self.filtros_ativos.clear()
        for ctrl in getattr(self, "filtro_widgets", {}).values():
            ctrl["chk"].setChecked(False)
            ctrl["nulos"].setChecked(False)
        self.recalcular()

    # ── KPIs ──
    def _ao_mudar_qtd_kpis(self, n: int):
        self.num_kpis = n
        for i, fw in enumerate(self.kpi_form_widgets):
            fw["frame"].setVisible(i < n)
        self.recalcular()

    def _ao_mudar_kpi_campo(self, idx: int, campo: str, valor):
        if idx < len(self.kpi_cfgs):
            self.kpi_cfgs[idx][campo] = valor
            self.recalcular()

    def configurar_kpi(
        self,
        indice: int,
        operacao: str,
        coluna: str | None = None,
        titulo: str | None = None,
        formato: str = "Número",
        simbolo: str = "R$",
    ):
        """Interface programática para teste e ajuste de KPIs."""
        if indice < len(self.kpi_cfgs):
            self.kpi_cfgs[indice] = {
                "operacao": operacao,
                "coluna": coluna,
                "titulo": titulo or f"KPI {indice + 1}",
                "formato": formato,
                "simbolo": simbolo,
            }
        self.recalcular()

    def _atualizar_opcoes_kpis(self):
        colunas_todas = list(self.meta.keys())
        colunas_num = [n for n, c in self.meta.items() if c.tipo == "numero"]

        for idx, fw in enumerate(self.kpi_form_widgets):
            fw["col"].blockSignals(True)
            fw["col"].clear()
            op = self.kpi_cfgs[idx]["operacao"]
            cols = colunas_todas if op == "distintos" else colunas_num
            for c in cols:
                fw["col"].addItem(c)
            if self.kpi_cfgs[idx].get("coluna") in cols:
                fw["col"].setCurrentText(self.kpi_cfgs[idx]["coluna"])
            elif cols:
                self.kpi_cfgs[idx]["coluna"] = cols[0]
            fw["col"].blockSignals(False)

    # ── Gráficos ──
    def _atualizar_opcoes_grafico(self):
        categorias = [n for n, c in self.meta.items() if c.tipo == "categoria"]
        numericas = [n for n, c in self.meta.items() if c.tipo == "numero"]
        datas = [n for n, c in self.meta.items() if c.tipo == "data"]

        tipos = (["barras"] if categorias else []) + (["linhas"] if datas else []) + (["histograma"] if numericas else [])
        self.cb_graf_tipo.blockSignals(True)
        self.cb_graf_tipo.clear()
        for t in tipos:
            self.cb_graf_tipo.addItem(t)
        if self.grafico_cfg.get("tipo") in tipos:
            self.cb_graf_tipo.setCurrentText(self.grafico_cfg["tipo"])
        elif tipos:
            self.grafico_cfg["tipo"] = tipos[0]
        self.cb_graf_tipo.blockSignals(False)
        self._ao_mudar_grafico_tipo(self.grafico_cfg.get("tipo", ""))

    def _ao_mudar_grafico_tipo(self, tipo: str):
        self.grafico_cfg["tipo"] = tipo
        is_hist = tipo == "histograma"
        is_lin = tipo == "linhas"

        self.lbl_graf_grupo.setVisible(not is_hist)
        self.cb_graf_grupo.setVisible(not is_hist)
        self.lbl_graf_op.setVisible(not is_hist)
        self.cb_graf_op.setVisible(not is_hist)
        self.lbl_graf_medida.setVisible(True)
        self.cb_graf_medida.setVisible(True)
        self.lbl_graf_periodo.setVisible(is_lin)
        self.cb_graf_periodo.setVisible(is_lin)
        self.lbl_graf_bins.setVisible(is_hist)
        self.sp_graf_bins.setVisible(is_hist)

        # Preenche grupos e medidas
        categorias = [n for n, c in self.meta.items() if c.tipo == "categoria"]
        numericas = [n for n, c in self.meta.items() if c.tipo == "numero"]
        datas = [n for n, c in self.meta.items() if c.tipo == "data"]

        self.cb_graf_grupo.blockSignals(True)
        self.cb_graf_grupo.clear()
        for g in (datas if is_lin else categorias):
            self.cb_graf_grupo.addItem(g)
        self.cb_graf_grupo.blockSignals(False)

        self.cb_graf_medida.blockSignals(True)
        self.cb_graf_medida.clear()
        for m in numericas:
            self.cb_graf_medida.addItem(m)
        self.cb_graf_medida.blockSignals(False)

        self.recalcular()

    def _ao_mudar_grafico_campo(self, campo: str, valor):
        self.grafico_cfg[campo] = valor
        self.recalcular()

    def configurar_grafico(
        self,
        tipo: str,
        grupo: str | None = None,
        operacao: str = "contagem",
        coluna: str | None = None,
        periodo: str = "dia",
        intervalos: int = 10,
    ):
        """Interface programática para teste e ajuste de gráficos."""
        self.grafico_cfg = {
            "tipo": tipo,
            "grupo": grupo,
            "operacao": operacao,
            "coluna": coluna,
            "periodo": periodo,
            "intervalos": intervalos,
        }
        self.cb_graf_tipo.blockSignals(True)
        if self.cb_graf_tipo.findText(tipo) != -1:
            self.cb_graf_tipo.setCurrentText(tipo)
        self.cb_graf_tipo.blockSignals(False)
        self._ao_mudar_grafico_tipo(tipo)

        if grupo and self.cb_graf_grupo.findText(grupo) != -1:
            self.cb_graf_grupo.setCurrentText(grupo)
        if operacao:
            for i in range(self.cb_graf_op.count()):
                if self.cb_graf_op.itemData(i) == operacao:
                    self.cb_graf_op.setCurrentIndex(i)
                    break
        if coluna and self.cb_graf_medida.findText(coluna) != -1:
            self.cb_graf_medida.setCurrentText(coluna)
        if periodo and self.cb_graf_periodo.findText(periodo) != -1:
            self.cb_graf_periodo.setCurrentText(periodo)
        self.sp_graf_bins.setValue(intervalos)
        self.recalcular()

    # ── Recálculo e renderização reativa ──
    def recalcular(self):
        if self.df_tipado is None:
            self.df_filtrado = pd.DataFrame()
            return

        try:
            self.df_filtrado = aplicar_filtros(self.df_tipado, self.filtros_ativos)
            self._mostrar_aviso("")
        except ErroBI as exc:
            self._mostrar_aviso(str(exc))
            self.df_filtrado = pd.DataFrame()

        total = len(self.df_tipado)
        filtrados = len(self.df_filtrado)
        self.lbl_status_filtros.setText(f"{filtrados} de {total} registros após os filtros.")
        if hasattr(self, "expander_filtros"):
            n_f = len(self.filtros_ativos)
            self.expander_filtros.definir_titulo(
                f"Filtros configuráveis ({n_f} ativo{'s' if n_f != 1 else ''})" if n_f else "Filtros configuráveis"
            )

        self._renderizar_kpis()
        self._renderizar_grafico()
        self._renderizar_tabela()
        self.dados_atualizados.emit()

    def _renderizar_kpis(self):
        # Limpa cartões antigos
        while self.lay_kpi_cards.count():
            item = self.lay_kpi_cards.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.kpi_resultados.clear()
        formatos_map = {"Número": "numero", "Percentual": "percentual", "Moeda": "moeda"}

        for i in range(self.num_kpis):
            cfg = self.kpi_cfgs[i]
            res = calcular_kpi(self.df_filtrado, cfg)
            self.kpi_resultados.append(res)

            tit = res.titulo or cfg.get("titulo") or f"KPI {i+1}"
            if res.erro:
                card = MetricCard(tit, "—")
            elif res.valor is None:
                card = MetricCard(tit, "—")
            else:
                fmt = formatos_map.get(cfg.get("formato", "Número"), "numero")
                val_txt = formatar_valor_kpi(res.valor, fmt, simbolo=cfg.get("simbolo", "R$"))
                card = MetricCard(tit, val_txt)
            self.lay_kpi_cards.addWidget(card)

    def _renderizar_grafico(self):
        while self.lay_grafico_container.count():
            item = self.lay_grafico_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        while self.lay_dados_grafico.count():
            item = self.lay_dados_grafico.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        tipo = self.grafico_cfg.get("tipo")
        if not tipo or self.df_filtrado.empty:
            self.tabela_grafico = pd.DataFrame()
            return

        cfg_final = dict(self.grafico_cfg)
        if tipo == "histograma":
            cfg_final["coluna"] = cfg_final.get("coluna") or self.cb_graf_medida.currentText()
            cfg_final["intervalos"] = cfg_final.get("intervalos", self.sp_graf_bins.value())
        else:
            cfg_final["grupo"] = cfg_final.get("grupo") or self.cb_graf_grupo.currentText()
            cfg_final["operacao"] = cfg_final.get("operacao") or self.cb_graf_op.currentData() or "contagem"
            if cfg_final["operacao"] != "contagem":
                cfg_final["coluna"] = cfg_final.get("coluna") or self.cb_graf_medida.currentText()
            if tipo == "linhas":
                cfg_final["periodo"] = cfg_final.get("periodo") or self.cb_graf_periodo.currentText() or "dia"

        try:
            self.tabela_grafico = preparar_grafico(self.df_filtrado, cfg_final)
        except ErroBI as exc:
            self.tabela_grafico = pd.DataFrame()
            self.lay_grafico_container.addWidget(AlertBox(str(exc), "warning"))
            return

        widget_grafico = BIChartWidget(
            self.tabela_grafico,
            tipo,
            self.cfg.get("cor", "#5B4FC4"),
            self.cfg,
        )
        self.lay_grafico_container.addWidget(widget_grafico)

        if not self.tabela_grafico.empty:
            tabela_w = PaginatedTableWidget(self.tabela_grafico, linhas_por_pagina=10, status_cols=())
            self.lay_dados_grafico.addWidget(tabela_w)

    def _renderizar_tabela(self):
        while self.lay_tabela_container.count():
            item = self.lay_tabela_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if self.df_filtrado.empty:
            self.lay_tabela_container.addWidget(AlertBox("Nenhum registro para a seleção atual.", "info"))
            return

        tabela_w = PaginatedTableWidget(
            self.df_filtrado,
            linhas_por_pagina=self.cfg.get("linhas", 10),
            status_cols=(),
        )
        self.lay_tabela_container.addWidget(tabela_w)

    def _ao_exportar_csv(self):
        if self.df_filtrado.empty:
            QMessageBox.information(self, "Exportar", "Não há registros filtrados para exportar.")
            return
        caminho, _ = QFileDialog.getSaveFileName(
            self,
            "Exportar dados filtrados",
            "analise_filtrada.csv",
            "Arquivo CSV (*.csv)",
        )
        if caminho:
            self.exportar_csv(caminho)
            QMessageBox.information(self, "Exportação Concluída", f"Dados exportados para:\n{caminho}")

    def exportar_csv(self, caminho: str | Path):
        self.df_filtrado.to_csv(caminho, index=False, encoding="utf-8-sig")

    # ── Métodos para suporte a testes e leitura de estado ──
    def _obter_resumo_negocio_seguro(self) -> dict:
        if not database.DB_PATH.exists():
            return {}
        try:
            e = database.carregar("eventos")
            cv = database.carregar("convidados")
            return backend.resumo_financeiro(e, cv)
        except sqlite3.Error:
            return {}

    def atualizar_comparacao_cvm(self):
        if hasattr(self, "cvm_painel"):
            self.cvm_painel.atualizar()

    def obter_df_filtrado(self) -> pd.DataFrame:
        return self.df_filtrado.copy()

    def obter_kpi_resultados(self) -> list:
        return list(self.kpi_resultados)

    def obter_tabela_grafico(self) -> pd.DataFrame:
        return self.tabela_grafico.copy()


def mostrar_dashboard(cor: str = "#5B4FC4"):
    """Função compatível com a API original."""
    pass
