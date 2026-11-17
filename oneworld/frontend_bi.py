"""Dashboard Desktop (PyQt6) do módulo de BI do OneWorld.
Adaptação da interface analítica mantendo 100% das regras e fluxo puro de BI:
seleção de dados, tipagem de datas, filtros inclusivos, KPIs configuráveis,
gráficos dinâmicos (barras, linhas, histograma) e exportação.
"""
from __future__ import annotations

import math
from io import BytesIO
from pathlib import Path
from sqlite3 import Error as ErroSQLite
from unicodedata import normalize

import pandas as pd
from PyQt6.QtCore import QDate, QPointF, QRectF, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen
from PyQt6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDoubleSpinBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from . import backend, database
from .analises import preparar_grafico
from .filtros import aplicar_filtros
from .fontes_sqlite import carregar_tabela, listar_tabelas
from .formatacao import formatar_valor_kpi
from .frontend import AlertBox, ExpanderWidget, PaginatedTableWidget
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
TIPOS_GRAFICO = {"barras": "Barras", "linhas": "Linha", "histograma": "Histograma"}

# Cada perfil define a dimensão inicial e os indicadores que dependem da base.
PERFIS = (
    ("Educação", ("ano", "turma", "escola"), (
        ("Alunos", "soma", ("alunos", "total_alunos", "qtd_alunos")),
        ("Alunos distintos", "distintos", ("aluno", "id_aluno")),
        ("Professores", "soma", ("professores", "total_professores", "qtd_professores")),
        ("Professores distintos", "distintos", ("professor", "id_professor")),
        ("Média das notas", "media", ("nota",)),
        ("Turmas", "distintos", ("turma",)),
    )),
    ("Estoque", ("categoria", "produto"), (
        ("Unidades em estoque", "soma", ("quantidade",)),
        ("Produtos", "distintos", ("produto",)),
        ("Categorias", "distintos", ("categoria",)),
    )),
    ("Vendas", ("categoria", "produto"), (
        ("Valor das vendas", "soma", ("valor",)),
        ("Valor médio por registro", "media", ("valor",)),
        ("Produtos", "distintos", ("produto",)),
    )),
)


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
        self.setMinimumHeight(212)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        self._dados: list[tuple[str, float]] = []
        self._posicoes: list[float] = []
        if not tabela.empty and len(tabela.columns) >= 2:
            eixo, valores = tabela.iloc[:, 0], tabela.iloc[:, 1]
            for rotulo, valor in zip(eixo, valores):
                try:
                    v = float(valor) if pd.notna(valor) else 0.0
                except (ValueError, TypeError):
                    v = 0.0
                if not math.isfinite(v):
                    continue
                if tipo == "linhas":
                    self._posicoes.append(rotulo.timestamp() if isinstance(rotulo, pd.Timestamp) else float(rotulo))
                if isinstance(rotulo, pd.Timestamp):
                    rotulo = rotulo.strftime("%d/%m/%Y")
                self._dados.append((str(rotulo), v))

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
        if self._tipo in ("barras", "histograma"):
            min_v, max_v = min(0.0, min_v), max(0.0, max_v)
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
            larg_barra = min(56.0, passo * 0.65) if self._tipo == "barras" else passo * 0.88
            zero = margem_topo + area_h * (max_v / intervalo_v)
            p.setPen(QPen(c_borda, 1))
            p.drawLine(QPointF(margem_esq, zero), QPointF(w - margem_dir, zero))
            for idx, (rotulo, valor) in enumerate(self._dados):
                x = margem_esq + idx * passo + (passo - larg_barra) / 2.0
                y = margem_topo + area_h * ((max_v - valor) / intervalo_v)

                caminho = QPainterPath()
                caminho.addRoundedRect(QRectF(x, min(y, zero), larg_barra, max(1.0, abs(y - zero))), 4, 4)
                p.fillPath(caminho, self._cor)

                if passo < 48 and idx % math.ceil(65 / passo):
                    continue
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
            inicio, fim = self._posicoes[0], self._posicoes[-1]
            margem_x = min(36, area_w / 4)
            for pos, (rotulo, valor) in zip(self._posicoes, self._dados):
                alt_pt = ((valor - min_v) / intervalo_v) * area_h
                fracao = (pos - inicio) / (fim - inicio) if fim > inicio else 0.5
                x = margem_esq + margem_x + (area_w - 2 * margem_x) * fracao
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
            ultimo_rotulo = -math.inf
            for x, y, rotulo, valor in pontos:
                p.setBrush(self._cor)
                p.setPen(QPen(c_texto, 1))
                p.drawEllipse(QPointF(x, y), 4, 4)

                if x - ultimo_rotulo < 72:
                    continue
                ultimo_rotulo = x
                txt_val = str(int(valor) if valor == int(valor) else f"{valor:.2f}")
                p.setPen(c_texto)
                p.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
                p.drawText(
                    QRectF(x - 35, max(2, y - 18), 70, 16),
                    Qt.AlignmentFlag.AlignCenter,
                    txt_val,
                )

                p.setPen(c_muted)
                p.setFont(fonte_peq)
                p.drawText(
                    QRectF(x - 35, margem_topo + area_h + 6, 70, 32),
                    Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop | Qt.TextFlag.TextWordWrap,
                    rotulo,
                )

        p.end()


class BIDashboardWidget(QWidget):
    """Componente completo de Dashboard e Business Intelligence para PyQt6."""

    dados_atualizados = pyqtSignal()

    def __init__(self, cfg: dict | None = None, parent=None):
        super().__init__(parent)
        self.cfg = cfg or {"cor": "#5B4FC4", "cor2": "#00A86B", "linhas": 10}
        self._linhas_por_pagina = self.cfg.get("linhas", 10)

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
        self.grupos_grafico: dict[str, str | None] = {}
        self.coluna_agrupada: str | None = None
        self.coluna_histograma: str | None = None
        self.coluna_ano: str | None = None
        self.analises_rapidas: list[tuple[str, str, str | None]] = []
        self.tabela_grafico: pd.DataFrame = pd.DataFrame()
        self.filtros_ativos: list[dict] = []

        self._iniciar_fontes()
        self._construir_ui()
        if self.fontes_disponiveis:
            primeira = list(self.fontes_disponiveis.keys())[0]
            self.selecionar_fonte(primeira)

    def _iniciar_fontes(self):
        self.fontes_disponiveis.clear()
        if EXEMPLOS.exists():
            for p in sorted(EXEMPLOS.glob("*.csv")):
                self.fontes_disponiveis[f"Exemplo: {p.stem}"] = p

    def aplicar_tema(self):
        pal = paleta_atual(self.cfg)
        self.setStyleSheet(f"""
            QFrame#BiPainel, QFrame#BiIndicador {{
                background: {pal['surface']};
                border: 1px solid {pal['border']};
                border-radius: 14px;
            }}
            QFrame#BiIndicadorPrincipal {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #102B24, stop:1 #156A50);
                border-radius: 14px;
            }}
            QLabel#BiValor {{ font-size: 27px; font-weight: 800; }}
            QFrame#BiIndicadorPrincipal QLabel {{ color: #FFFFFF; }}
            QPushButton#BiOpcao {{
                padding: 6px 11px;
                border: 1px solid {pal['border']};
                border-radius: 8px;
                background: {pal['bg']};
                color: {pal['text']};
            }}
            QPushButton#BiOpcao:checked {{ background: #156A50; color: white; border-color: #156A50; }}
            QPushButton#BiOpcao:focus, QPushButton#BiOpcao:hover {{ border-color: #2E9A78; }}
            QPushButton#BiOpcao:disabled {{ color: {pal['muted']}; background: {pal['surface']}; }}
            QCheckBox#BiBancoLocal::indicator {{ width: 15px; height: 15px; }}
        """)
        linhas = self.cfg.get("linhas", 10)
        if linhas != self._linhas_por_pagina:
            self._linhas_por_pagina = linhas
            self._renderizar_tabela()

    def _construir_ui(self):
        self.lay_principal = QVBoxLayout(self)
        self.lay_principal.setContentsMargins(0, 0, 0, 0)
        self.lay_principal.setSpacing(14)
        self.aplicar_tema()

        cabecalho = QFrame()
        cabecalho.setObjectName("BiPainel")
        lay_cabecalho = QVBoxLayout(cabecalho)
        lay_cabecalho.setContentsMargins(16, 10, 16, 12)
        self.lbl_perfil = QLabel("Análise de dados")
        self.lbl_perfil.setObjectName("SectionTitle")
        lay_cabecalho.addWidget(self.lbl_perfil)
        barra_dados = QHBoxLayout()
        barra_dados.setSpacing(12)

        lbl_fonte = QLabel("Conjunto de dados:")
        lbl_fonte.setObjectName("MetricLabel")
        barra_dados.addWidget(lbl_fonte)

        self.cb_dataset = QComboBox()
        self.cb_dataset.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        self.cb_dataset.setMinimumContentsLength(12)
        self.cb_dataset.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._atualizar_combo_fontes()
        self.cb_dataset.currentTextChanged.connect(self._ao_mudar_fonte)
        barra_dados.addWidget(self.cb_dataset, stretch=2)

        self.chk_banco = QCheckBox("Incluir banco local")
        self.chk_banco.setObjectName("BiBancoLocal")
        self.chk_banco.toggled.connect(self._ao_alternar_banco_local)
        barra_dados.addWidget(self.chk_banco)

        btn_upload = QPushButton("+ Adicionar arquivo")
        btn_upload.setObjectName("PrimaryBtn")
        btn_upload.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_upload.clicked.connect(self._ao_fazer_upload)
        barra_dados.addWidget(btn_upload)

        lay_cabecalho.addLayout(barra_dados)
        self.lay_principal.addWidget(cabecalho)

        self.caixa_alerta = AlertBox("", "warning")
        self.caixa_alerta.setVisible(False)
        self.lay_principal.addWidget(self.caixa_alerta)

        # ── 2. Tipagem de datas ──
        self.expander_datas = ExpanderWidget("Tipos de colunas e datas", aberto=False)
        self.lbl_info_colunas = QLabel()
        self.lbl_info_colunas.setWordWrap(True)
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

        # ── 3. Filtros Dinâmicos ──
        self.expander_filtros = ExpanderWidget("Filtros", aberto=False)
        self.lay_filtros_itens = QVBoxLayout()
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

        # ── 4. KPIs ──
        self.lay_kpi_cards = QHBoxLayout()
        self.lay_kpi_cards.setSpacing(12)
        self.lay_principal.addLayout(self.lay_kpi_cards)

        self.expander_kpi_cfg = ExpanderWidget("Configurar indicadores", aberto=False)
        linha_n_kpis = QHBoxLayout()
        linha_n_kpis.addWidget(QLabel("Quantidade de KPIs (1 a 4):"))
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
            ed_tit.setFixedWidth(130)
            cb_op = QComboBox()
            for op in OPERACOES:
                cb_op.addItem(ROTULOS[op], userData=op)
            cb_col = QComboBox()
            cb_fmt = QComboBox()
            cb_fmt.addItems(["Número", "Percentual", "Moeda"])
            ed_simb = QLineEdit("R$")
            ed_simb.setFixedWidth(50)

            idx_k = i
            ed_tit.textChanged.connect(lambda t, k=idx_k: self._ao_mudar_kpi_campo(k, "titulo", t))
            cb_op.currentIndexChanged.connect(lambda _, k=idx_k, cb=cb_op: self._ao_mudar_kpi_campo(k, "operacao", cb.currentData()))
            cb_col.currentTextChanged.connect(lambda texto, k=idx_k: self._ao_mudar_kpi_campo(k, "coluna", texto))
            cb_fmt.currentTextChanged.connect(lambda f, k=idx_k: self._ao_mudar_kpi_campo(k, "formato", f))
            ed_simb.textChanged.connect(lambda s, k=idx_k: self._ao_mudar_kpi_campo(k, "simbolo", s))

            f_lay.addWidget(QLabel(f"#{i+1}:"))
            f_lay.addWidget(ed_tit)
            f_lay.addWidget(cb_op)
            f_lay.addWidget(cb_col)
            f_lay.addWidget(cb_fmt)
            f_lay.addWidget(ed_simb)

            self.expander_kpi_cfg.corpo_layout.addWidget(f_frame)
            f_frame.setVisible(i < self.num_kpis)
            self.kpi_form_widgets.append({
                "frame": f_frame, "titulo": ed_tit, "op": cb_op, "col": cb_col, "fmt": cb_fmt, "simb": ed_simb
            })

        painel_grafico = QFrame()
        painel_grafico.setObjectName("BiPainel")
        lay_painel = QVBoxLayout(painel_grafico)
        lay_painel.setContentsMargins(16, 12, 16, 14)
        topo_grafico = QHBoxLayout()
        self.lbl_titulo_grafico = QLabel("Gráfico")
        self.lbl_titulo_grafico.setObjectName("SectionTitle")
        self.lbl_titulo_grafico.setWordWrap(True)
        topo_grafico.addWidget(self.lbl_titulo_grafico, 1)
        self.botoes_tipo = {}
        self.grupo_tipo = QButtonGroup(self)
        for tipo, rotulo in TIPOS_GRAFICO.items():
            botao = self._botao_opcao(rotulo)
            self.grupo_tipo.addButton(botao)
            botao.clicked.connect(lambda _, t=tipo: self._selecionar_tipo_grafico(t))
            self.botoes_tipo[tipo] = botao
            topo_grafico.addWidget(botao)
        lay_painel.addLayout(topo_grafico)

        self.grupo_medida = QButtonGroup(self)
        self.lay_analises_rapidas = QGridLayout()
        lay_painel.addLayout(self.lay_analises_rapidas)

        barra_graf = QHBoxLayout()

        self.lbl_graf_grupo = QLabel("Agrupar por:")
        barra_graf.addWidget(self.lbl_graf_grupo)
        self.cb_graf_grupo = QComboBox()
        self.cb_graf_grupo.currentTextChanged.connect(lambda v: self._ao_mudar_grafico_campo("grupo", v))
        barra_graf.addWidget(self.cb_graf_grupo)

        self.lbl_graf_op = QLabel("Agregação:")
        barra_graf.addWidget(self.lbl_graf_op)
        self.cb_graf_op = QComboBox()
        for op in OPERACOES:
            self.cb_graf_op.addItem(ROTULOS.get(op, op), userData=op)
        self.cb_graf_op.currentIndexChanged.connect(lambda _: self._selecionar_medida(self.cb_graf_op.currentData(), self.grafico_cfg.get("coluna")))
        barra_graf.addWidget(self.cb_graf_op)

        self.lbl_graf_medida = QLabel("Medida:")
        barra_graf.addWidget(self.lbl_graf_medida)
        self.cb_graf_medida = QComboBox()
        self.cb_graf_medida.currentTextChanged.connect(lambda v: self._ao_mudar_grafico_campo("coluna", v))
        barra_graf.addWidget(self.cb_graf_medida)

        self.lbl_graf_periodo = QLabel("Período:")
        barra_graf.addWidget(self.lbl_graf_periodo)
        self.cb_graf_periodo = QComboBox()
        self.cb_graf_periodo.addItem("Dia", "dia")
        self.cb_graf_periodo.addItem("Mês", "mes")
        self.cb_graf_periodo.currentIndexChanged.connect(
            lambda _: self._ao_mudar_grafico_campo("periodo", self.cb_graf_periodo.currentData()))
        barra_graf.addWidget(self.cb_graf_periodo)

        self.lbl_graf_bins = QLabel("Intervalos:")
        barra_graf.addWidget(self.lbl_graf_bins)
        self.sp_graf_bins = QSpinBox()
        self.sp_graf_bins.setRange(1, 100)
        self.sp_graf_bins.setValue(10)
        self.sp_graf_bins.valueChanged.connect(lambda v: self._ao_mudar_grafico_campo("intervalos", v))
        barra_graf.addWidget(self.sp_graf_bins)
        barra_graf.addStretch(1)
        for combo in (self.cb_graf_grupo, self.cb_graf_op, self.cb_graf_medida):
            combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
            combo.setMinimumContentsLength(9)

        lay_painel.addLayout(barra_graf)

        self.lay_grafico_container = QVBoxLayout()
        lay_painel.addLayout(self.lay_grafico_container)
        self.lay_principal.addWidget(painel_grafico)

        self.expander_dados_grafico = ExpanderWidget("Dados do gráfico", aberto=False)
        self.lay_dados_grafico = QVBoxLayout()
        self.expander_dados_grafico.corpo_layout.addLayout(self.lay_dados_grafico)
        self.lay_principal.addWidget(self.expander_dados_grafico)
        self.lay_principal.addWidget(self.expander_filtros)
        self.lay_principal.addWidget(self.expander_kpi_cfg)
        self.lay_principal.addWidget(self.expander_datas)

        # ── 6. Registros Filtrados e Exportação ──
        linha_tabela_tit = QHBoxLayout()
        linha_tabela_tit.addWidget(QLabel("Registros filtrados"))
        linha_tabela_tit.addStretch(1)

        btn_exportar = QPushButton("Exportar dados filtrados (CSV)")
        btn_exportar.setObjectName("PrimaryBtn")
        btn_exportar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_exportar.clicked.connect(self._ao_exportar_csv)
        linha_tabela_tit.addWidget(btn_exportar)
        self.lay_principal.addLayout(linha_tabela_tit)

        self.lay_tabela_container = QVBoxLayout()
        self.lay_principal.addLayout(self.lay_tabela_container)

    @staticmethod
    def _botao_opcao(rotulo):
        botao = QPushButton(rotulo)
        botao.setObjectName("BiOpcao")
        botao.setCheckable(True)
        botao.setCursor(Qt.CursorShape.PointingHandCursor)
        return botao

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
            return

        self.cb_dataset.blockSignals(True)
        self.cb_dataset.setCurrentText(nome)
        self.cb_dataset.blockSignals(False)
        self.filtros_ativos.clear()
        self.falhas_datas.clear()
        self.lbl_falhas_data.clear()
        self._atualizar_metadados()
        self._aplicar_perfil()
        self._reconstruir_controles_filtros()
        self._atualizar_opcoes_kpis()
        self._atualizar_opcoes_grafico()
        self.recalcular()

    def _aplicar_perfil(self):
        colunas = {
            normalize("NFKD", nome.strip().casefold()).encode("ascii", "ignore").decode().replace(" ", "_"): nome
            for nome in self.meta
        }
        perfil, dimensoes, indicadores = "Análise de dados", (), ()
        if colunas.keys() & {"aluno", "id_aluno", "alunos", "total_alunos", "qtd_alunos",
                             "professor", "id_professor", "professores", "total_professores",
                             "qtd_professores", "turma"}:
            perfil, dimensoes, indicadores = PERFIS[0]
        elif {"produto", "quantidade"} <= colunas.keys():
            perfil, dimensoes, indicadores = PERFIS[1]
        elif {"produto", "valor"} <= colunas.keys():
            perfil, dimensoes, indicadores = PERFIS[2]
        self.lbl_perfil.setText(perfil)

        self.analises_rapidas = [("Registros", "contagem", None)]
        for titulo, op, aliases in indicadores:
            for alias in aliases:
                coluna = colunas.get(alias)
                if coluna is not None and (
                    self.meta[coluna].tipo == "numero"
                    or op == "distintos" and self.meta[coluna].tipo == "categoria"
                ):
                    self.analises_rapidas.append((titulo, op, coluna))
                    break
        principais = self.analises_rapidas[1:5] or self.analises_rapidas
        self.num_kpis = len(principais)
        self.kpi_cfgs = [
            {"operacao": "contagem", "coluna": None, "titulo": f"KPI {i + 1}", "formato": "Número", "simbolo": "R$"}
            for i in range(4)
        ]
        for cfg, (titulo, op, coluna) in zip(self.kpi_cfgs, principais):
            cfg.update(titulo=titulo, operacao=op, coluna=coluna)
            if perfil == "Vendas" and op in ("soma", "media") and self.cb_dataset.currentText() == "Exemplo: vendas":
                cfg["formato"] = "Moeda"
        self.sp_n_kpis.blockSignals(True)
        self.sp_n_kpis.setValue(self.num_kpis)
        self.sp_n_kpis.blockSignals(False)

        grupos = self._grupos_barras()
        grupo = next((colunas[d] for d in dimensoes if colunas.get(d) in grupos), None)
        self.coluna_ano = colunas.get("ano")
        self.grupos_grafico.clear()
        _, op, coluna = principais[0]
        self.coluna_agrupada = coluna
        self.coluna_histograma = None
        self.grafico_cfg = dict(tipo="barras", grupo=grupo, operacao=op, coluna=coluna,
                                periodo="dia", intervalos=10)
        while self.lay_analises_rapidas.count():
            botao = self.lay_analises_rapidas.takeAt(0).widget()
            self.grupo_medida.removeButton(botao)
            botao.hide()
            botao.deleteLater()
        for i, (titulo, op, coluna) in enumerate(self.analises_rapidas):
            botao = self._botao_opcao(titulo)
            self.grupo_medida.addButton(botao, i)
            botao.clicked.connect(lambda _, o=op, c=coluna: self._selecionar_medida(o, c))
            self.lay_analises_rapidas.addWidget(botao, i // 5, i % 5)

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
        falhas = self.df_tipado.attrs.get("falhas_campos", {})
        if falhas:
            detalhes = ", ".join(f"{nome}: {n}" for nome, n in falhas.items())
            info += f"\nValores incompatíveis tratados como nulos ({detalhes})."
        self.lbl_info_colunas.setText(f"Colunas detectadas: {info}")

        tipos_campos = self.df_tipado.attrs.get("tipos_campos", {})
        candidatas = [n for n, c in self.meta.items() if c.tipo == "categoria" and n not in tipos_campos]
        self.cb_col_data.blockSignals(True)
        self.cb_col_data.clear()
        for cand in candidatas:
            self.cb_col_data.addItem(cand)
        self.cb_col_data.blockSignals(False)

    def _ao_aplicar_datas(self):
        coluna = self.cb_col_data.currentText()
        if not coluna or self.df_bruto is None:
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
        tipos_campos = self.df_tipado.attrs.get("tipos_campos", {})
        for nome, col in self.meta.items():
            if col.tipo not in ("categoria", "numero", "data"):
                continue

            linha = QHBoxLayout()
            chk_ativo = QCheckBox(nome)
            linha.addWidget(chk_ativo)

            ctrl_info = {"chk": chk_ativo, "tipo": col.tipo}

            if col.tipo == "categoria":
                valores_unicos = sorted(self.df_tipado[nome].dropna().unique().tolist(), key=str)
                cb_val = QComboBox()
                cb_val.addItem("Todos", userData=None)
                for v in valores_unicos:
                    if tipos_campos.get(nome) == "booleano":
                        cb_val.addItem("Sim" if v else "Não", userData=bool(v))
                    else:
                        cb_val.addItem(str(v), userData=v)
                cb_val.setEnabled(False)
                linha.addWidget(cb_val, stretch=1)
                ctrl_info["combo"] = cb_val
                cb_val.currentIndexChanged.connect(lambda _: self._ao_filtro_alterado())
            elif tipos_campos.get(nome) in ("inteiro", "decimal"):
                for chave, rotulo in (("min", "De"), ("max", "Até")):
                    limite = QLineEdit()
                    limite.setPlaceholderText("Sem limite")
                    limite.setAccessibleName(f"{nome} · {rotulo}")
                    limite.setEnabled(False)
                    limite.editingFinished.connect(self._ao_filtro_alterado)
                    linha.addWidget(QLabel(f"{rotulo}:"))
                    linha.addWidget(limite)
                    ctrl_info[chave] = limite
            elif col.tipo == "numero":
                sp_min = QDoubleSpinBox()
                sp_min.setRange(-1e12, 1e12)
                sp_min.setValue(-1e12)
                sp_min.setSpecialValueText("Mín")
                sp_min.setEnabled(False)

                sp_max = QDoubleSpinBox()
                sp_max.setRange(-1e12, 1e12)
                sp_max.setValue(1e12)
                sp_max.setSpecialValueText("Máx")
                sp_max.setEnabled(False)

                linha.addWidget(QLabel("De:"))
                linha.addWidget(sp_min)
                linha.addWidget(QLabel("Até:"))
                linha.addWidget(sp_max)
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
                if tipos_campos.get(nome) == "data":
                    datas = self.df_tipado[nome].dropna()
                    for controle, extremo in ((de_min, datas.min()), (de_max, datas.max())):
                        controle.setDateRange(QDate(1, 1, 1), QDate(9999, 12, 31))
                        if pd.notna(extremo):
                            controle.setDate(QDate(extremo.year, extremo.month, extremo.day))

                linha.addWidget(QLabel("De:"))
                linha.addWidget(de_min)
                linha.addWidget(QLabel("Até:"))
                linha.addWidget(de_max)
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
            self.lay_filtros_itens.addLayout(linha)

    def _ao_filtro_alterado(self):
        self.filtros_ativos.clear()
        for nome, ctrl in getattr(self, "filtro_widgets", {}).items():
            if not ctrl["chk"].isChecked():
                continue
            tipo = ctrl["tipo"]
            cfg: dict = {"coluna": nome, "tipo": tipo, "incluir_nulos": ctrl["nulos"].isChecked()}
            if tipo == "categoria":
                combo = ctrl["combo"]
                ativos = range(1, combo.count()) if combo.currentIndex() == 0 else [combo.currentIndex()]
                cfg["valores"] = [combo.itemData(i) for i in ativos if i >= 1]
            elif isinstance(ctrl["min"], QLineEdit):
                cfg["minimo"] = ctrl["min"].text().strip() or None
                cfg["maximo"] = ctrl["max"].text().strip() or None
            elif tipo == "numero":
                v_min = ctrl["min"].value()
                v_max = ctrl["max"].value()
                cfg["minimo"] = v_min if v_min != -1e12 else None
                cfg["maximo"] = v_max if v_max != 1e12 else None
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
            for chave, controle in ctrl.items():
                if chave == "tipo":
                    continue
                if chave in ("chk", "nulos"):
                    controle.blockSignals(True)
                    controle.setChecked(False)
                    controle.blockSignals(False)
                if chave != "chk":
                    controle.setEnabled(False)
        self.recalcular()

    # ── KPIs ──
    def _ao_mudar_qtd_kpis(self, n: int):
        self.num_kpis = n
        self._atualizar_opcoes_kpis()
        self.recalcular()

    def _ao_mudar_kpi_campo(self, idx: int, campo: str, valor):
        if idx < len(self.kpi_cfgs):
            self.kpi_cfgs[idx][campo] = valor
            if campo == "operacao":
                self._atualizar_opcoes_kpis()
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
        self._atualizar_opcoes_kpis()
        self.recalcular()

    def _atualizar_opcoes_kpis(self):
        colunas_todas = [n for n, c in self.meta.items() if c.tipo not in ("texto", "incompativel")]
        colunas_num = [n for n, c in self.meta.items() if c.tipo == "numero"]

        for idx, fw in enumerate(self.kpi_form_widgets):
            cfg = self.kpi_cfgs[idx]
            fw["frame"].setVisible(idx < self.num_kpis)
            controles = [fw[c] for c in ("titulo", "op", "col", "fmt", "simb")]
            for controle in controles:
                controle.blockSignals(True)
            fw["titulo"].setText(cfg["titulo"])
            fw["op"].setCurrentIndex(fw["op"].findData(cfg["operacao"]))
            fw["fmt"].setCurrentText(cfg["formato"])
            fw["simb"].setText(cfg["simbolo"])
            fw["col"].clear()
            op = cfg["operacao"]
            cols = colunas_todas if op == "distintos" else colunas_num
            fw["col"].addItems(cols)
            if cfg["coluna"] not in cols and op != "contagem":
                cfg["coluna"] = fw["col"].currentText() or None
            fw["col"].setCurrentIndex(fw["col"].findText(cfg["coluna"] or ""))
            fw["col"].setEnabled(op != "contagem")
            for controle in controles:
                controle.blockSignals(False)

    # ── Gráficos ──
    def _grupos_barras(self):
        return [n for n, c in self.meta.items() if c.tipo in ("categoria", "numero")]

    def _atualizar_opcoes_grafico(self):
        grupos_barras = self._grupos_barras()
        numericas = [n for n, c in self.meta.items() if c.tipo == "numero"]
        datas = [n for n, c in self.meta.items() if c.tipo == "data"]
        if self.coluna_ano in numericas:
            datas.append(self.coluna_ano)
        tipos = {"barras": grupos_barras, "linhas": datas, "histograma": numericas}
        disponiveis = [tipo for tipo, colunas in tipos.items() if colunas]
        tipo = self.grafico_cfg.get("tipo")
        if tipo not in disponiveis:
            tipo = next(iter(disponiveis), "")
        self.grafico_cfg["tipo"] = tipo
        self.grupo_tipo.setExclusive(False)
        for chave, botao in self.botoes_tipo.items():
            botao.setEnabled(chave in disponiveis)
            botao.setChecked(chave == tipo)
            botao.setToolTip("" if chave in disponiveis else {
                "barras": "Requer uma coluna de categorias ou números",
                "linhas": "Requer uma coluna de data ou ano numérico",
                "histograma": "Requer uma coluna numérica",
            }[chave])
        self.grupo_tipo.setExclusive(True)

        agrupado = tipo in ("barras", "linhas")
        histograma = tipo == "histograma"
        grupos = tipos.get(tipo, []) if agrupado else []
        grupo = self.grafico_cfg.get("grupo")
        if agrupado and grupo not in grupos:
            grupo = next(iter(grupos), None)
        por_data = tipo == "linhas" and grupo in self.meta and self.meta[grupo].tipo == "data"
        op = self.grafico_cfg.get("operacao", "contagem")
        medidas = numericas
        if agrupado and op == "distintos":
            medidas = [n for n, c in self.meta.items() if c.tipo not in ("texto", "incompativel")]
        elif agrupado and op == "contagem":
            medidas = []

        controles = (
            (self.lbl_graf_grupo, self.cb_graf_grupo, agrupado),
            (self.lbl_graf_op, self.cb_graf_op, agrupado),
            (self.lbl_graf_medida, self.cb_graf_medida, histograma or (agrupado and op != "contagem")),
            (self.lbl_graf_periodo, self.cb_graf_periodo, por_data),
            (self.lbl_graf_bins, self.sp_graf_bins, histograma),
        )
        for rotulo, controle, visivel in controles:
            rotulo.setVisible(visivel)
            controle.setVisible(visivel)
            controle.blockSignals(True)
        for campo, combo, opcoes in (
            ("grupo", self.cb_graf_grupo, grupos),
            ("coluna", self.cb_graf_medida, medidas),
        ):
            combo.clear()
            combo.addItems(opcoes)
            if self.grafico_cfg.get(campo) in opcoes:
                combo.setCurrentText(self.grafico_cfg[campo])
            if campo != "grupo" or agrupado:
                self.grafico_cfg[campo] = combo.currentText() or None
        self.cb_graf_op.setCurrentIndex(self.cb_graf_op.findData(op))
        self.cb_graf_periodo.setCurrentIndex(self.cb_graf_periodo.findData(self.grafico_cfg["periodo"]))
        self.sp_graf_bins.setValue(self.grafico_cfg["intervalos"])
        for _, controle, _ in controles:
            controle.blockSignals(False)
        self._sincronizar_analises_rapidas()

    def _sincronizar_analises_rapidas(self):
        tipo = self.grafico_cfg["tipo"]
        op = self.grafico_cfg.get("operacao", "contagem")
        coluna = self.grafico_cfg.get("coluna")
        self.grupo_medida.setExclusive(False)
        for indice, (_, operacao, medida) in enumerate(self.analises_rapidas):
            botao = self.grupo_medida.button(indice)
            botao.setVisible(tipo in ("barras", "linhas"))
            botao.setChecked(tipo in ("barras", "linhas") and operacao == op and medida == coluna)
        self.grupo_medida.setExclusive(True)

    def _selecionar_tipo_grafico(self, tipo):
        anterior = self.grafico_cfg["tipo"]
        if tipo != anterior:
            if anterior in ("barras", "linhas"):
                self.grupos_grafico[anterior] = self.grafico_cfg.get("grupo")
                self.coluna_agrupada = self.grafico_cfg.get("coluna")
            elif anterior == "histograma":
                self.coluna_histograma = self.grafico_cfg.get("coluna")
            if tipo == "histograma":
                self.grafico_cfg["coluna"] = self.coluna_histograma or self.coluna_agrupada
            else:
                self.grafico_cfg["grupo"] = self.grupos_grafico.get(tipo) or self.grafico_cfg.get("grupo")
                self.grafico_cfg["coluna"] = self.coluna_agrupada
            self.grafico_cfg["tipo"] = tipo
        self._atualizar_opcoes_grafico()
        self._renderizar_grafico()

    def _selecionar_medida(self, operacao, coluna):
        self.grafico_cfg.update(operacao=operacao, coluna=coluna)
        self._atualizar_opcoes_grafico()
        self._renderizar_grafico()

    def _ao_mudar_grafico_campo(self, campo: str, valor):
        self.grafico_cfg[campo] = valor
        if campo == "grupo":
            self._atualizar_opcoes_grafico()
        else:
            self._sincronizar_analises_rapidas()
        self._renderizar_grafico()

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
        self._atualizar_opcoes_grafico()
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

        self._renderizar_kpis()
        self._renderizar_grafico()
        self._renderizar_tabela()
        self.dados_atualizados.emit()

    def _renderizar_kpis(self):
        # Limpa cartões antigos
        while self.lay_kpi_cards.count():
            item = self.lay_kpi_cards.takeAt(0)
            if item.widget():
                item.widget().hide()
                item.widget().deleteLater()

        self.kpi_resultados.clear()
        formatos_map = {"Número": "numero", "Percentual": "percentual", "Moeda": "moeda"}

        for i in range(self.num_kpis):
            cfg = self.kpi_cfgs[i]
            res = calcular_kpi(self.df_filtrado, cfg)
            self.kpi_resultados.append(res)

            tit = res.titulo or cfg.get("titulo") or f"KPI {i+1}"
            fmt = formatos_map.get(cfg["formato"], "numero")
            valor = "—" if res.valor is None or res.erro else formatar_valor_kpi(
                res.valor, fmt, simbolo=cfg["simbolo"])
            card = QFrame()
            card.setObjectName("BiIndicadorPrincipal" if i == 0 else "BiIndicador")
            lay = QVBoxLayout(card)
            lay.setContentsMargins(14, 12, 14, 12)
            titulo = QLabel(tit)
            titulo.setObjectName("MetricLabel")
            titulo.setTextFormat(Qt.TextFormat.PlainText)
            titulo.setWordWrap(True)
            lay.addWidget(titulo)
            lay.addStretch(1)
            numero = QLabel(valor)
            numero.setObjectName("BiValor")
            numero.setWordWrap(True)
            lay.addWidget(numero)
            card.setMinimumHeight(96)
            operacao = ROTULOS.get(cfg["operacao"], cfg["operacao"])
            detalhe = f"{operacao} • {cfg['coluna']}" if cfg["coluna"] else operacao
            card.setToolTip(res.erro or res.mensagem or detalhe)
            self.lay_kpi_cards.addWidget(card, 1)

    def _renderizar_grafico(self):
        while self.lay_grafico_container.count():
            item = self.lay_grafico_container.takeAt(0)
            if item.widget():
                item.widget().hide()
                item.widget().deleteLater()

        while self.lay_dados_grafico.count():
            item = self.lay_dados_grafico.takeAt(0)
            if item.widget():
                item.widget().hide()
                item.widget().deleteLater()

        tipo = self.grafico_cfg.get("tipo")
        coluna = self.grafico_cfg.get("coluna")
        grupo = self.grafico_cfg.get("grupo")
        op = self.grafico_cfg.get("operacao", "contagem")
        nome_medida = next((titulo for titulo, operacao, medida in self.analises_rapidas
                            if (operacao, medida) == (op, coluna)), None)
        if tipo == "histograma":
            titulo = f"Distribuição de {coluna}"
        elif grupo:
            medida = nome_medida or f"{ROTULOS.get(op, op)} de {coluna}"
            titulo = f"{medida} por {grupo}"
        else:
            titulo = "Gráfico"
        self.lbl_titulo_grafico.setTextFormat(Qt.TextFormat.PlainText)
        self.lbl_titulo_grafico.setText(titulo)
        if not tipo or self.df_filtrado.empty:
            self.tabela_grafico = pd.DataFrame()
            self.lay_grafico_container.addWidget(AlertBox("Sem dados para o gráfico na seleção atual.", "info"))
            return

        try:
            self.tabela_grafico = preparar_grafico(self.df_filtrado, self.grafico_cfg)
        except ErroBI as exc:
            self.tabela_grafico = pd.DataFrame()
            self.lay_grafico_container.addWidget(AlertBox(str(exc), "warning"))
            return

        widget_grafico = BIChartWidget(
            self.tabela_grafico,
            tipo,
            "#2E9A78",
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
                item.widget().hide()
                item.widget().deleteLater()

        if self.df_filtrado.empty:
            self.lay_tabela_container.addWidget(AlertBox("Nenhum registro para a seleção atual.", "info"))
            return

        tabela_w = PaginatedTableWidget(
            self.df_filtrado,
            linhas_por_pagina=self._linhas_por_pagina,
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
    def obter_df_filtrado(self) -> pd.DataFrame:
        return self.df_filtrado.copy()

    def obter_kpi_resultados(self) -> list:
        return list(self.kpi_resultados)

    def obter_tabela_grafico(self) -> pd.DataFrame:
        return self.tabela_grafico.copy()


def mostrar_dashboard(cor: str = "#5B4FC4"):
    """Função compatível com a API original."""
    pass
