"""Interface gráfica desktop nativa (PyQt6) do OneWorld: telas, formulários e navegação.
Só desenha e coleta ações do usuário; regras ficam em backend.py e SQL em database.py."""
from __future__ import annotations

import html
import math
import sqlite3
import sys
import zipfile
from datetime import date, datetime
from pathlib import Path

import pandas as pd
from PyQt6.QtCore import QDate, QRectF, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QIcon, QPainter, QPainterPath, QPen, QPixmap
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QButtonGroup,
    QCheckBox,
    QColorDialog,
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
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from . import backend as bk
from . import backup as bkp
from . import cvm_comparacao as cvm_cmp
from . import database as db
from . import ia
from . import mapeamento as mp
from . import planilha_padrao as pp
from .config import (
    BACKUP_DIR,
    CAMPOS,
    FILTROS,
    LOGO_PADRAO,
    NAO_USAR,
    OBRIGATORIOS,
    PADROES,
    PAGINAS,
    PERFIL_PADRAO,
    PERFIS_NEGOCIO,
    ROXO,
    STATUS_CONV,
    STATUS_CORES,
    STATUS_EVENTO,
    VERDE,
    obter_vocabulario,
    rotulo_pagina,
)
from .tema import gerar_qss, metricas_layout, paleta_atual


# ── Utilitários de Imagem / Componentes Visuais Leves ──
def pixmap_arredondado(caminho: Path, largura: int, raio: int = 14) -> QPixmap:
    src = QPixmap(str(caminho))
    if src.isNull():
        return QPixmap()
    esc = src.scaledToWidth(largura, Qt.TransformationMode.SmoothTransformation)
    out = QPixmap(esc.size())
    out.fill(Qt.GlobalColor.transparent)
    p = QPainter(out)
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    path = QPainterPath()
    path.addRoundedRect(QRectF(0, 0, esc.width(), esc.height()), raio, raio)
    p.setClipPath(path)
    p.drawPixmap(0, 0, esc)
    p.end()
    return out


class Divider(QFrame):
    def __init__(self):
        super().__init__()
        self.setObjectName("Divider")
        self.setFrameShape(QFrame.Shape.HLine)


class AlertBox(QFrame):
    """Caixa de aviso estilizada."""

    def __init__(self, texto: str, tipo: str = "info"):
        super().__init__()
        nomes = {
            "info": "AlertInfo",
            "success": "AlertSuccess",
            "warning": "AlertWarning",
            "error": "AlertError",
        }
        cores_txt = {
            "success": "#2F5A06",
            "warning": "#7A4B00",
            "error": "#8F2412",
        }
        self.setObjectName(nomes.get(tipo, "AlertInfo"))
        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 10, 14, 10)
        self.lbl = QLabel(texto)
        self.lbl.setWordWrap(True)
        if tipo in cores_txt:
            self.lbl.setStyleSheet(f"color: {cores_txt[tipo]}; font-weight: 600;")
        lay.addWidget(self.lbl)

    def definir_texto(self, texto: str):
        self.lbl.setText(texto)


class MetricCard(QFrame):
    """Cartão de indicador com barra lateral verde."""

    def __init__(self, rotulo: str, valor: str | int):
        super().__init__()
        self.setObjectName("MetricCard")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 12, 16, 12)
        lay.setSpacing(4)
        self.lbl_titulo = QLabel(str(rotulo))
        self.lbl_titulo.setObjectName("MetricLabel")
        self.lbl_titulo.setWordWrap(True)
        self.lbl_valor = QLabel(str(valor))
        self.lbl_valor.setObjectName("MetricValue")
        lay.addWidget(self.lbl_titulo)
        lay.addWidget(self.lbl_valor)

    def atualizar(self, valor: str | int):
        self.lbl_valor.setText(str(valor))


class ExpanderWidget(QFrame):
    """Componente recolhível leve."""

    def __init__(self, titulo_txt: str, aberto: bool = False):
        super().__init__()
        self.setObjectName("OwCard")
        self._aberto = aberto
        self._titulo = titulo_txt

        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 8, 12, 8)
        lay.setSpacing(8)

        self.btn = QPushButton()
        self.btn.setFlat(True)
        self.btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn.setStyleSheet("text-align: left; font-weight: 600; border: none; padding: 4px 2px;")
        self.btn.clicked.connect(self.alternar)
        lay.addWidget(self.btn)

        self.corpo = QWidget()
        self.corpo_layout = QVBoxLayout(self.corpo)
        self.corpo_layout.setContentsMargins(4, 4, 4, 4)
        self.corpo_layout.setSpacing(8)
        lay.addWidget(self.corpo)

        self._atualizar_estado()

    def alternar(self):
        self._aberto = not self._aberto
        self._atualizar_estado()

    def definir_titulo(self, novo_titulo: str):
        self._titulo = novo_titulo
        self._atualizar_estado()

    def _atualizar_estado(self):
        seta = "▼" if self._aberto else "▶"
        self.btn.setText(f"{seta}  {self._titulo}")
        self.corpo.setVisible(self._aberto)


class MultiSelectChips(QWidget):
    """Seletor múltiplo leve usando botões de alternância (chips)."""

    changed = pyqtSignal(list)

    def __init__(self, opcoes: list[str], selecionados: list[str] | None = None, cor_ativa: str = ROXO):
        super().__init__()
        self._selecionados = list(selecionados or [])
        self._cor = cor_ativa
        self._botoes: dict[str, QPushButton] = {}

        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(6)

        if not opcoes:
            vazio = QLabel("—")
            vazio.setObjectName("Caption")
            lay.addWidget(vazio)
        for op in opcoes:
            btn = QPushButton(str(op))
            btn.setCheckable(True)
            btn.setChecked(op in self._selecionados)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.toggled.connect(lambda checked, o=op: self._ao_alternar(o, checked))
            self._botoes[op] = btn
            lay.addWidget(btn)
        lay.addStretch(1)
        self._estilizar()

    def _estilizar(self):
        for _, btn in self._botoes.items():
            if btn.isChecked():
                btn.setStyleSheet(
                    f"background-color: {self._cor}; color: #FFFFFF; border: 1px solid {self._cor}; "
                    "border-radius: 14px; padding: 4px 12px; font-weight: 600;"
                )
            else:
                btn.setStyleSheet("border-radius: 14px; padding: 4px 12px;")

    def _ao_alternar(self, opcao: str, marcado: bool):
        if marcado and opcao not in self._selecionados:
            self._selecionados.append(opcao)
        elif not marcado and opcao in self._selecionados:
            self._selecionados.remove(opcao)
        self._estilizar()
        self.changed.emit(list(self._selecionados))

    def valores(self) -> list[str]:
        return list(self._selecionados)


class BarChartWidget(QFrame):
    """Gráfico de barras nativo e ultraleve desenhado via QPainter (sem peso de matplotlib)."""

    def __init__(self, serie: pd.Series, cor: str, cfg: dict, formato_moeda: bool = False):
        super().__init__()
        self.setObjectName("OwCard")
        self._dados = [(str(k), float(v)) for k, v in serie.items()]
        self._cor = QColor(cor)
        self._cfg = cfg
        self._moeda = formato_moeda
        self.setMinimumHeight(230)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

    def paintEvent(self, event):
        super().paintEvent(event)
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        pal = paleta_atual(self._cfg)
        c_texto = QColor(pal["text"])
        c_muted = QColor(pal["muted"])
        c_borda = QColor(pal["border"])

        w, h = self.width(), self.height()
        margem_esq, margem_dir, margem_topo, margem_base = 54, 18, 26, 42
        area_w = max(10, w - margem_esq - margem_dir)
        area_h = max(10, h - margem_topo - margem_base)

        if not self._dados:
            p.setPen(c_muted)
            p.drawText(QRectF(0, 0, w, h), Qt.AlignmentFlag.AlignCenter, "Sem dados")
            p.end()
            return

        max_v = max((v for _, v in self._dados), default=1.0)
        if max_v <= 0:
            max_v = 1.0

        fonte_peq = QFont("Segoe UI", 8)
        p.setFont(fonte_peq)
        for i in range(5):
            frac = i / 4.0
            y = margem_topo + area_h * (1.0 - frac)
            p.setPen(QPen(c_borda, 1, Qt.PenStyle.DashLine))
            p.drawLine(int(margem_esq), int(y), int(w - margem_dir), int(y))

            val_eixo = max_v * frac
            if val_eixo >= 1000:
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
        passo = area_w / n
        larg_barra = min(56.0, max(16.0, passo * 0.58))

        for idx, (rotulo, valor) in enumerate(self._dados):
            alt_barra = (valor / max_v) * area_h
            x = margem_esq + idx * passo + (passo - larg_barra) / 2.0
            y = margem_topo + area_h - alt_barra

            caminho = QPainterPath()
            caminho.addRoundedRect(QRectF(x, y, larg_barra, max(3.0, alt_barra)), 5, 5)
            p.fillPath(caminho, self._cor)

            txt_val = bk.moeda(valor, self._cfg) if self._moeda else str(int(valor) if valor == int(valor) else valor)
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
                QRectF(margem_esq + idx * passo, margem_topo + area_h + 6, passo, 30),
                Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop | Qt.TextFlag.TextWordWrap,
                rotulo,
            )

        p.end()


class PaginatedTableWidget(QWidget):
    """Tabela paginada com estilização de células de Status/Situação/Confirmação."""

    def __init__(
        self,
        df: pd.DataFrame,
        linhas_por_pagina: int = 10,
        status_cols: tuple[str, ...] = ("Status", "Confirmação", "Situação"),
        pagina_inicial: int = 1,
        ao_mudar_pagina=None,
    ):
        super().__init__()
        self._df = df
        self._n = max(1, int(linhas_por_pagina))
        self._status_cols = status_cols
        self._ao_mudar_pagina = ao_mudar_pagina

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(6)

        if df.empty:
            lay.addWidget(AlertBox("Nenhum registro para exibir.", "info"))
            return

        self._paginas = max(1, math.ceil(len(df) / self._n))
        self._pagina = min(max(1, pagina_inicial), self._paginas)

        if self._paginas > 1:
            barra_pg = QHBoxLayout()
            lbl_pg = QLabel("Página")
            lbl_pg.setObjectName("Caption")
            self.spin_pg = QSpinBox()
            self.spin_pg.setRange(1, self._paginas)
            self.spin_pg.setValue(self._pagina)
            self.spin_pg.valueChanged.connect(self._ir_para_pagina)
            lbl_tot = QLabel(f"de {self._paginas}")
            lbl_tot.setObjectName("Caption")
            barra_pg.addWidget(lbl_pg)
            barra_pg.addWidget(self.spin_pg)
            barra_pg.addWidget(lbl_tot)
            barra_pg.addStretch(1)
            lay.addLayout(barra_pg)

        self.tabela = QTableWidget()
        self.tabela.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabela.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabela.setAlternatingRowColors(True)
        self.tabela.verticalHeader().setVisible(False)
        self.tabela.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabela.horizontalHeader().setMinimumSectionSize(90)
        lay.addWidget(self.tabela)

        self.lbl_info = QLabel()
        self.lbl_info.setObjectName("Caption")
        lay.addWidget(self.lbl_info)

        self._preencher()

    def _ir_para_pagina(self, pg: int):
        self._pagina = pg
        if self._ao_mudar_pagina:
            self._ao_mudar_pagina(pg)
        self._preencher()

    def _preencher(self):
        ini = (self._pagina - 1) * self._n
        fim = min(self._pagina * self._n, len(self._df))
        fatia = self._df.iloc[ini:fim]

        cols = [str(c) for c in fatia.columns]
        self.tabela.setColumnCount(len(cols))
        self.tabela.setHorizontalHeaderLabels(cols)
        self.tabela.setRowCount(len(fatia))

        for r_idx, (_, row) in enumerate(fatia.iterrows()):
            self.tabela.setRowHeight(r_idx, 36)
            for c_idx, col_name in enumerate(cols):
                val = "" if pd.isna(row.iloc[c_idx]) else str(row.iloc[c_idx])
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
                if (col_name in self._status_cols or val in STATUS_CORES) and val in STATUS_CORES:
                    fundo, texto_cor = STATUS_CORES[val]
                    item.setBackground(QColor(fundo))
                    item.setForeground(QColor(texto_cor))
                    f = item.font()
                    f.setBold(True)
                    item.setFont(f)
                self.tabela.setItem(r_idx, c_idx, item)

        altura_ideal = min(460, 42 + len(fatia) * 36)
        self.tabela.setMinimumHeight(altura_ideal)
        self.lbl_info.setText(f"Exibindo {ini + 1}–{fim} de {len(self._df)} registros")


def _limpar_layout_widgets(layout) -> None:
    """Remove widgets e sublayouts de um layout Qt sem depender da janela principal."""
    while layout.count():
        item = layout.takeAt(0)
        w = item.widget()
        if w:
            w.deleteLater()
        elif item.layout():
            _limpar_layout_widgets(item.layout())


def _fmt_pct_cvm(valor) -> str:
    if valor is None:
        return "n/d"
    try:
        return f"{float(valor):.1f}%".replace(".", ",")
    except (TypeError, ValueError):
        return "n/d"


class CVMComparacaoPainel(QFrame):
    """Painel de controle multi-base CVM (habilitar, filtrar/selecionar) e Decision Intelligence."""

    estado_alterado = pyqtSignal()

    def __init__(self, cfg: dict, obter_resumo_negocio, parent=None):
        super().__init__(parent)
        self.setObjectName("OwCard")
        self.cfg = cfg
        self._obter_resumo = obter_resumo_negocio
        self._checks_bases: dict[str, QCheckBox] = {}
        self._nomes_busca: dict[str, str] = {}

        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 12, 16, 12)
        lay.setSpacing(10)

        topo = QHBoxLayout()
        topo.setSpacing(12)
        self.chk_habilitar = QCheckBox(
            "Habilitar comparação com base(s) pública(s) CVM (Decision Intelligence)"
        )
        self.chk_habilitar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.chk_habilitar.toggled.connect(self._ao_alternar_ativa)
        topo.addWidget(self.chk_habilitar)
        topo.addStretch(1)

        self.lbl_status = QLabel()
        self.lbl_status.setObjectName("Caption")
        topo.addWidget(self.lbl_status)
        lay.addLayout(topo)

        self.corpo = QWidget()
        self.lay_corpo = QVBoxLayout(self.corpo)
        self.lay_corpo.setContentsMargins(0, 4, 0, 0)
        self.lay_corpo.setSpacing(10)

        barra_filtro = QHBoxLayout()
        barra_filtro.setSpacing(8)
        self.ed_filtro = QLineEdit()
        self.ed_filtro.setPlaceholderText("Filtrar bases CVM por nome ou ano...")
        self.ed_filtro.textChanged.connect(self._aplicar_filtro_visual)
        barra_filtro.addWidget(self.ed_filtro, stretch=1)

        self.btn_todas = QPushButton("Selecionar todas")
        self.btn_todas.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_todas.clicked.connect(self._selecionar_todas)
        barra_filtro.addWidget(self.btn_todas)

        self.btn_recente = QPushButton("Apenas mais recente")
        self.btn_recente.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_recente.clicked.connect(self._selecionar_mais_recente)
        barra_filtro.addWidget(self.btn_recente)
        self.lay_corpo.addLayout(barra_filtro)

        self.lay_checks = QVBoxLayout()
        self.lay_checks.setContentsMargins(2, 2, 2, 2)
        self.lay_checks.setSpacing(4)
        self.lay_corpo.addLayout(self.lay_checks)

        self.lay_di = QVBoxLayout()
        self.lay_di.setContentsMargins(0, 4, 0, 0)
        self.lay_di.setSpacing(8)
        self.lay_corpo.addLayout(self.lay_di)

        lay.addWidget(self.corpo)
        self.atualizar()

    def _ao_alternar_ativa(self, checked: bool):
        cvm_cmp.definir_comparacao_ativa(bool(checked))
        self.atualizar()
        self.estado_alterado.emit()

    def _ao_mudar_selecao(self):
        ids = [bid for bid, chk in self._checks_bases.items() if chk.isChecked()]
        cvm_cmp.definir_bases_selecionadas(ids)
        self._renderizar_di(cvm_cmp.carregar_estado_cvm())
        self.estado_alterado.emit()

    def _selecionar_todas(self):
        estado = cvm_cmp.carregar_estado_cvm()
        ids = [b["id"] for b in estado.get("bases", [])]
        cvm_cmp.definir_bases_selecionadas(ids)
        self.atualizar()
        self.estado_alterado.emit()

    def _selecionar_mais_recente(self):
        estado = cvm_cmp.carregar_estado_cvm()
        ord_bases = cvm_cmp.ordenar_bases_recentes(estado.get("bases", []))
        ids = [ord_bases[0]["id"]] if ord_bases else []
        cvm_cmp.definir_bases_selecionadas(ids)
        self.atualizar()
        self.estado_alterado.emit()

    def _aplicar_filtro_visual(self):
        termo = bk.sem_acento(self.ed_filtro.text())
        for bid, chk in self._checks_bases.items():
            alvo = self._nomes_busca.get(bid, "")
            chk.setVisible(not termo or termo in alvo)

    def atualizar(self):
        """Recarrega o estado persistido do SQLite e atualiza seletores e Decision Intelligence."""
        estado = cvm_cmp.carregar_estado_cvm()
        ativa = bool(estado.get("ativa"))

        self.chk_habilitar.blockSignals(True)
        self.chk_habilitar.setChecked(ativa)
        self.chk_habilitar.blockSignals(False)

        self.corpo.setVisible(ativa)
        _limpar_layout_widgets(self.lay_checks)
        self._checks_bases.clear()
        self._nomes_busca.clear()

        bases_ord = cvm_cmp.ordenar_bases_recentes(estado.get("bases", []))
        sel = set(estado.get("selecionadas") or [])

        if not bases_ord:
            lbl_vazio = QLabel("Nenhuma base CVM cadastrada. Adicione na página 'Dados Externos'.")
            lbl_vazio.setObjectName("Caption")
            self.lay_checks.addWidget(lbl_vazio)
        else:
            for idx, base in enumerate(bases_ord):
                res = base.get("resumo") or {}
                ano = base.get("ano_referencia") or res.get("ano_referencia") or "n/d"
                cias = int(res.get("companhias_analisadas") or res.get("total_companhias") or 0)
                tag_rec = "  ·  Mais recente (Referência principal)" if idx == 0 else ""
                nome = base.get("nome") or base.get("arquivo_padrao") or "CVM"
                chk = QCheckBox(f"{nome} — Exercício {ano} ({cias} cias){tag_rec}")
                chk.setCursor(Qt.CursorShape.PointingHandCursor)
                chk.setChecked(base["id"] in sel)
                chk.toggled.connect(lambda _c: self._ao_mudar_selecao())
                self._checks_bases[base["id"]] = chk
                self._nomes_busca[base["id"]] = bk.sem_acento(
                    f"{nome} {base.get('arquivo_padrao', '')} {ano}"
                )
                self.lay_checks.addWidget(chk)

        self._aplicar_filtro_visual()
        self._renderizar_di(estado)

    def _renderizar_di(self, estado: dict):
        _limpar_layout_widgets(self.lay_di)
        if not estado.get("ativa"):
            n_disp = len(estado.get("bases", []))
            self.lbl_status.setText(f"Desativada ({n_disp} base(s) disponível(is))")
            return

        resumo_neg = self._obter_resumo() or {}
        di = cvm_cmp.avaliar_decision_intelligence(resumo_neg, estado, self.cfg)
        bases_usadas = di["bases_usadas"]
        principal = di["base_principal"]

        if principal:
            ano_p = principal.get("ano_referencia") or "n/d"
            self.lbl_status.setText(
                f"Ativa · {len(bases_usadas)} base(s) · Principal: {principal.get('nome')} ({ano_p})"
            )
        else:
            self.lbl_status.setText("Ativa · Nenhuma base selecionada")

        sem = di.get("semaforo")
        if sem:
            self.lay_di.addWidget(AlertBox(f"{sem['titulo']}\n{sem['resumo']}", sem["tipo_alerta"]))

        orientacoes = di.get("orientacoes") or []
        inicio_extra = 1 if (not di.get("sem_bases") and orientacoes and sem and orientacoes[0]["texto"] == sem["resumo"]) else 0
        for item in orientacoes[inicio_extra:]:
            self.lay_di.addWidget(AlertBox(item["texto"], item["tipo"]))

        if bases_usadas:
            lbl_tab = QLabel("Bases CVM em comparação (ordenadas da mais recente para a mais antiga):")
            lbl_tab.setObjectName("MetricLabel")
            self.lay_di.addWidget(lbl_tab)
            linhas = []
            for b in bases_usadas:
                r = b.get("resumo") or {}
                linhas.append(
                    {
                        "Base CVM": b.get("nome") or b.get("arquivo_padrao") or "CVM",
                        "Exercício": str(b.get("ano_referencia") or "n/d"),
                        "Empresas": int(r.get("companhias_analisadas") or r.get("total_companhias") or 0),
                        "Margem Líquida": _fmt_pct_cvm(r.get("margem_liquida_pct")),
                        "Margem Bruta": _fmt_pct_cvm(r.get("margem_bruta_pct")),
                        "Custo / Receita": _fmt_pct_cvm(r.get("custo_sobre_receita_pct")),
                        "Var. Receita Anual": _fmt_pct_cvm(r.get("variacao_receita_pct")),
                    }
                )
            df_cmp = pd.DataFrame(linhas)
            self.lay_di.addWidget(
                PaginatedTableWidget(df_cmp, linhas_por_pagina=max(5, len(df_cmp)), status_cols=())
            )


class CVMGerenciadorWidget(QWidget):
    """Gerenciador completo de bases públicas CVM na página Dados Externos."""

    def __init__(self, janela: "OneWorldWindow"):
        super().__init__()
        self.janela = janela
        self._cards_busca: list[tuple[QFrame, str]] = []

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(12)

        # Barra de ações e ativação
        card_topo = QFrame()
        card_topo.setObjectName("ToolbarCard")
        lay_topo = QVBoxLayout(card_topo)
        lay_topo.setContentsMargins(16, 12, 16, 12)
        lay_topo.setSpacing(8)

        lbl_tit = QLabel("Bases Públicas de Comparação (CVM) & Decision Intelligence")
        lbl_tit.setObjectName("SectionTitle")
        lay_topo.addWidget(lbl_tit)

        lbl_desc = QLabel(
            "As bases da CVM funcionam como referências de mercado separadas dos seus lançamentos operacionais. "
            "Adicione uma ou mais bases, edite os nomes, atualize ou exclua arquivos e habilite a comparação no Dashboard/BI."
        )
        lbl_desc.setObjectName("Caption")
        lbl_desc.setWordWrap(True)
        lay_topo.addWidget(lbl_desc)

        barra_btns = QHBoxLayout()
        barra_btns.setSpacing(10)

        self.btn_add_cvm = QPushButton("+ Adicionar Base(s) CVM...")
        self.btn_add_cvm.setObjectName("PrimaryBtn")
        self.btn_add_cvm.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_add_cvm.clicked.connect(self._ao_adicionar_arquivos)
        barra_btns.addWidget(self.btn_add_cvm)

        self.btn_add_pasta = QPushButton("+ Pasta CVM...")
        self.btn_add_pasta.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_add_pasta.clicked.connect(self._ao_adicionar_pasta)
        barra_btns.addWidget(self.btn_add_pasta)

        self.chk_ativa = QCheckBox("Habilitar comparação no Dashboard / BI")
        self.chk_ativa.setCursor(Qt.CursorShape.PointingHandCursor)
        self.chk_ativa.toggled.connect(self._ao_alternar_ativa)
        barra_btns.addWidget(self.chk_ativa)
        barra_btns.addStretch(1)
        lay_topo.addLayout(barra_btns)

        barra_filtro = QHBoxLayout()
        barra_filtro.setSpacing(8)
        self.ed_filtro = QLineEdit()
        self.ed_filtro.setPlaceholderText("Filtrar bases CVM cadastradas por nome, arquivo ou ano...")
        self.ed_filtro.textChanged.connect(self._aplicar_filtro)
        barra_filtro.addWidget(self.ed_filtro, stretch=1)

        btn_todas = QPushButton("Selecionar todas")
        btn_todas.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_todas.clicked.connect(self._selecionar_todas)
        barra_filtro.addWidget(btn_todas)

        btn_recente = QPushButton("Apenas mais recente")
        btn_recente.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_recente.clicked.connect(self._selecionar_mais_recente)
        barra_filtro.addWidget(btn_recente)

        btn_nenhuma = QPushButton("Desmarcar todas")
        btn_nenhuma.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_nenhuma.clicked.connect(self._desmarcar_todas)
        barra_filtro.addWidget(btn_nenhuma)
        lay_topo.addLayout(barra_filtro)

        lay.addWidget(card_topo)

        self.alerta_erro = AlertBox("", "error")
        self.alerta_erro.setVisible(False)
        lay.addWidget(self.alerta_erro)

        self.alerta_sucesso = AlertBox("", "success")
        self.alerta_sucesso.setVisible(False)
        lay.addWidget(self.alerta_sucesso)

        self.lay_lista = QVBoxLayout()
        self.lay_lista.setSpacing(10)
        lay.addLayout(self.lay_lista)

        self.recarregar()

    def _mostrar_erro(self, msg: str | None):
        if msg:
            self.alerta_sucesso.setVisible(False)
            self.alerta_erro.definir_texto(msg)
            self.alerta_erro.setVisible(True)
        else:
            self.alerta_erro.setVisible(False)

    def _mostrar_sucesso(self, msg: str | None):
        if msg:
            self.alerta_erro.setVisible(False)
            self.alerta_sucesso.definir_texto(msg)
            self.alerta_sucesso.setVisible(True)
        else:
            self.alerta_sucesso.setVisible(False)

    def _ao_alternar_ativa(self, checked: bool):
        self._mostrar_sucesso(None)
        cvm_cmp.definir_comparacao_ativa(bool(checked))
        self.janela.aviso(
            "Comparação CVM habilitada." if checked else "Comparação CVM desabilitada."
        )
        self.recarregar()

    def _ao_adicionar_arquivos(self):
        caminhos, _ = QFileDialog.getOpenFileNames(
            self,
            "Selecionar base(s) pública(s) CVM",
            "",
            "Bases CVM (*.zip *.csv *.xlsx);;ZIP (*.zip);;CSV (*.csv);;Excel (*.xlsx)",
        )
        if not caminhos:
            return
        self.adicionar_caminhos(caminhos)

    def _ao_adicionar_pasta(self):
        pasta = QFileDialog.getExistingDirectory(self, "Selecionar pasta da base CVM", "")
        if not pasta:
            return
        self.adicionar_caminhos([pasta])

    def adicionar_caminhos(self, caminhos: list[str | Path]):
        """Adiciona uma ou várias fontes CVM ao catálogo e atualiza a lista."""
        self._mostrar_erro(None)
        try:
            adicionadas = cvm_cmp.adicionar_bases_cvm(caminhos)
        except (OSError, ValueError, zipfile.BadZipFile) as exc:
            self._mostrar_erro(f"Não foi possível adicionar a base CVM: {exc}")
            return
        if adicionadas:
            self.janela.aviso(f"{len(adicionadas)} base(s) CVM carregada(s) no catálogo.")
            self._mostrar_sucesso(f"{len(adicionadas)} base(s) CVM salva(s) com sucesso.")
            self.recarregar()

    def _ao_salvar_nome(self, base_id: str, novo_nome: str):
        self._mostrar_erro(None)
        try:
            cvm_cmp.renomear_base_cvm(base_id, novo_nome)
        except (KeyError, ValueError) as exc:
            self._mostrar_erro(str(exc))
            return
        self._mostrar_sucesso("Nome da base CVM atualizado.")
        self.recarregar()

    def _ao_atualizar_arquivo(self, base_id: str):
        caminho, _ = QFileDialog.getOpenFileName(
            self,
            "Substituir arquivo da base CVM",
            "",
            "Bases CVM (*.zip *.csv *.xlsx);;ZIP (*.zip);;CSV (*.csv);;Excel (*.xlsx)",
        )
        if not caminho:
            return
        self.atualizar_arquivo(base_id, caminho)

    def atualizar_arquivo(self, base_id: str, caminho: str | Path):
        """Substitui o arquivo vinculado a uma base CVM existente."""
        self._mostrar_erro(None)
        try:
            cvm_cmp.atualizar_arquivo_cvm(base_id, caminho)
        except (KeyError, OSError, ValueError, zipfile.BadZipFile) as exc:
            self._mostrar_erro(f"Não foi possível atualizar a base CVM: {exc}")
            return
        self.janela.aviso("Base CVM atualizada com novo arquivo.")
        self._mostrar_sucesso("Arquivo da base CVM atualizado com sucesso.")
        self.recarregar()

    def _ao_excluir(self, base_id: str, nome: str):
        self._mostrar_erro(None)
        cvm_cmp.excluir_base_cvm(base_id)
        self.janela.aviso(f"Base CVM removida: {nome}")
        self._mostrar_sucesso(f"Base '{nome}' excluída do catálogo.")
        self.recarregar()

    def _ao_alternar_selecao(self, base_id: str, marcado: bool):
        estado = cvm_cmp.carregar_estado_cvm()
        sel = list(estado.get("selecionadas") or [])
        if marcado and base_id not in sel:
            sel.append(base_id)
        elif not marcado and base_id in sel:
            sel.remove(base_id)
        cvm_cmp.definir_bases_selecionadas(sel)

    def _selecionar_todas(self):
        estado = cvm_cmp.carregar_estado_cvm()
        cvm_cmp.definir_bases_selecionadas([b["id"] for b in estado.get("bases", [])])
        self.recarregar()

    def _selecionar_mais_recente(self):
        estado = cvm_cmp.carregar_estado_cvm()
        ord_bases = cvm_cmp.ordenar_bases_recentes(estado.get("bases", []))
        cvm_cmp.definir_bases_selecionadas([ord_bases[0]["id"]] if ord_bases else [])
        self.recarregar()

    def _desmarcar_todas(self):
        cvm_cmp.definir_bases_selecionadas([])
        self.recarregar()

    def _aplicar_filtro(self):
        termo = bk.sem_acento(self.ed_filtro.text())
        for card, chave_busca in self._cards_busca:
            card.setVisible(not termo or termo in chave_busca)

    def recarregar(self):
        """Reconstrói a listagem de bases CVM mantendo o estado persistido."""
        estado = cvm_cmp.carregar_estado_cvm()
        self.chk_ativa.blockSignals(True)
        self.chk_ativa.setChecked(bool(estado.get("ativa")))
        self.chk_ativa.blockSignals(False)

        _limpar_layout_widgets(self.lay_lista)
        self._cards_busca.clear()

        bases_ord = cvm_cmp.ordenar_bases_recentes(estado.get("bases", []))
        sel = set(estado.get("selecionadas") or [])
        cor = self.janela.cfg.get("cor", ROXO)

        if not bases_ord:
            self.lay_lista.addWidget(
                AlertBox(
                    "Nenhuma base CVM cadastrada. Clique em '+ Adicionar Base(s) CVM...' para incluir arquivos.",
                    "info",
                )
            )
            return

        for idx, base in enumerate(bases_ord):
            res = base.get("resumo") or {}
            bid = base["id"]
            card = QFrame()
            card.setObjectName("OwCard")
            lay_c = QVBoxLayout(card)
            lay_c.setContentsMargins(14, 12, 14, 12)
            lay_c.setSpacing(8)

            # Linha 1: seleção para comparação + campo de nome editável + ações
            l1 = QHBoxLayout()
            l1.setSpacing(8)
            chk_sel = QCheckBox("Usar na comparação")
            chk_sel.setCursor(Qt.CursorShape.PointingHandCursor)
            chk_sel.setChecked(bid in sel)
            chk_sel.toggled.connect(lambda m, b_id=bid: self._ao_alternar_selecao(b_id, m))
            l1.addWidget(chk_sel)

            if idx == 0:
                badge = QLabel("Mais recente · Prioridade")
                badge.setStyleSheet(
                    f"background:{cor}; color:#FFFFFF; padding: 3px 10px; "
                    "border-radius: 10px; font-weight: 600;"
                )
                l1.addWidget(badge)

            ed_nome = QLineEdit(str(base.get("nome") or ""))
            ed_nome.setPlaceholderText(str(base.get("nome_padrao") or base.get("arquivo_padrao") or ""))
            ed_nome.returnPressed.connect(lambda b_id=bid, ed=ed_nome: self._ao_salvar_nome(b_id, ed.text()))
            l1.addWidget(ed_nome, stretch=1)

            btn_salvar = QPushButton("Salvar nome")
            btn_salvar.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_salvar.clicked.connect(lambda _, b_id=bid, ed=ed_nome: self._ao_salvar_nome(b_id, ed.text()))
            l1.addWidget(btn_salvar)

            btn_atualizar = QPushButton("Atualizar arquivo...")
            btn_atualizar.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_atualizar.clicked.connect(lambda _, b_id=bid: self._ao_atualizar_arquivo(b_id))
            l1.addWidget(btn_atualizar)

            btn_excluir = QPushButton("Excluir")
            btn_excluir.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_excluir.clicked.connect(
                lambda _, b_id=bid, nm=base.get("nome", "CVM"): self._ao_excluir(b_id, nm)
            )
            l1.addWidget(btn_excluir)
            lay_c.addLayout(l1)

            # Linha 2: metadados e indicadores extraídos
            ano = base.get("ano_referencia") or res.get("ano_referencia") or "n/d"
            dt_ref = base.get("data_referencia") or res.get("data_referencia") or "n/d"
            cias_an = int(res.get("companhias_analisadas") or 0)
            cias_tot = int(res.get("total_companhias") or 0)
            info1 = QLabel(
                f"Arquivo: {base.get('arquivo_padrao', 'n/d')}  ·  "
                f"Exercício: {ano} (Ref.: {dt_ref})  ·  "
                f"Companhias analisadas: {cias_an}/{cias_tot}  ·  "
                f"Atualizado em: {base.get('atualizado_em', 'n/d')}"
            )
            info1.setObjectName("Caption")
            info1.setWordWrap(True)
            lay_c.addWidget(info1)

            info2 = QLabel(
                f"Indicadores medianos (DRE):  "
                f"Margem Líquida {_fmt_pct_cvm(res.get('margem_liquida_pct'))}  ·  "
                f"Margem Bruta {_fmt_pct_cvm(res.get('margem_bruta_pct'))}  ·  "
                f"Custo/Receita {_fmt_pct_cvm(res.get('custo_sobre_receita_pct'))}  ·  "
                f"Var. Receita Anual {_fmt_pct_cvm(res.get('variacao_receita_pct'))}"
            )
            info2.setObjectName("Caption")
            info2.setWordWrap(True)
            lay_c.addWidget(info2)

            self.lay_lista.addWidget(card)
            chave_busca = bk.sem_acento(
                f"{base.get('nome', '')} {base.get('arquivo_padrao', '')} {ano}"
            )
            self._cards_busca.append((card, chave_busca))

        self._aplicar_filtro()


# ── Widget de Importação de Planilhas ──
class ImportarPlanilhaWidget(QWidget):
    """Fluxo interativo completo: leitura → mapeamento → validação → prévia → confirmação."""

    def __init__(self, janela: "OneWorldWindow", destino_fixo: str | None = None, chave_estado: str = "imp"):
        super().__init__()
        self.janela = janela
        self.destino_fixo = destino_fixo
        self.chave = chave_estado
        self.caminho_arq: Path | None = self.janela.estado.get(f"{chave_estado}_arq")
        self.df_lido: pd.DataFrame | None = self.janela.estado.get(f"{chave_estado}_df")
        self.destino_atual: str = destino_fixo or self.janela.estado.get(f"{chave_estado}_dest", "eventos")

        self.lay = QVBoxLayout(self)
        self.lay.setContentsMargins(0, 0, 0, 0)
        self.lay.setSpacing(12)

        barra_arq = QHBoxLayout()
        btn_up = QPushButton("Selecionar arquivo (CSV, XLSX ou JSON)...")
        btn_up.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_up.clicked.connect(self._escolher_arquivo)
        barra_arq.addWidget(btn_up)

        if self.caminho_arq:
            lbl_nome = QLabel(f"Arquivo selecionado: <b>{self.caminho_arq.name}</b>")
            barra_arq.addWidget(lbl_nome)
            btn_limpar = QPushButton("Limpar")
            btn_limpar.clicked.connect(self._limpar_arquivo)
            barra_arq.addWidget(btn_limpar)
        barra_arq.addStretch(1)
        self.lay.addLayout(barra_arq)

        self.area_dinamica = QWidget()
        self.lay_din = QVBoxLayout(self.area_dinamica)
        self.lay_din.setContentsMargins(0, 0, 0, 0)
        self.lay_din.setSpacing(12)
        self.lay.addWidget(self.area_dinamica)

        self._renderizar_fluxo()

    def _escolher_arquivo(self):
        caminho, _ = QFileDialog.getOpenFileName(
            self,
            "Enviar arquivo (CSV, XLSX ou JSON)",
            "",
            "Planilhas e Dados (*.csv *.xlsx *.json)",
        )
        if not caminho:
            return
        p = Path(caminho)
        self.caminho_arq = p
        self.janela.estado[f"{self.chave}_arq"] = p
        try:
            self.df_lido = mp.ler_arquivo(p)
            self.janela.estado[f"{self.chave}_df"] = self.df_lido
            self.janela.estado.pop(f"{self.chave}_erro", None)
        except Exception as ex:  # noqa: BLE001
            self.df_lido = None
            self.janela.estado[f"{self.chave}_erro"] = str(ex)
        self.janela.reconstruir_pagina()

    def _limpar_arquivo(self):
        self.janela.estado.pop(f"{self.chave}_arq", None)
        self.janela.estado.pop(f"{self.chave}_df", None)
        self.janela.estado.pop(f"{self.chave}_erro", None)
        self.janela.reconstruir_pagina()

    def _limpar_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
            elif item.layout():
                self._limpar_layout(item.layout())

    def _renderizar_fluxo(self):
        self._limpar_layout(self.lay_din)
        v = self.janela.vocab()

        erro_leitura = self.janela.estado.get(f"{self.chave}_erro")
        if erro_leitura:
            self.lay_din.addWidget(AlertBox(f"Não foi possível ler o arquivo: {erro_leitura}", "error"))
            return

        if not self.caminho_arq or self.df_lido is None:
            cap = QLabel(
                "Fluxo: leitura → mapeamento → validação → prévia → confirmação. "
                "Nada é gravado antes do seu clique em confirmar."
            )
            cap.setObjectName("Caption")
            self.lay_din.addWidget(cap)
            return

        data = self.df_lido
        if data.empty:
            self.lay_din.addWidget(AlertBox("O arquivo não tem linhas de dados.", "warning"))
            return

        lbl_prev = QLabel("<b>Prévia do arquivo</b>")
        self.lay_din.addWidget(lbl_prev)
        self.lay_din.addWidget(PaginatedTableWidget(data.head(10), linhas_por_pagina=10, status_cols=()))

        if not self.destino_fixo:
            box_dest = QHBoxLayout()
            box_dest.addWidget(QLabel("<b>Destino dos dados:</b>"))
            grp = QButtonGroup(self.area_dinamica)
            rb_ev = QRadioButton(v["ent1_plural"])
            rb_cv = QRadioButton(v["ent2_plural"])
            rb_ev.setChecked(self.destino_atual == "eventos")
            rb_cv.setChecked(self.destino_atual == "convidados")
            grp.addButton(rb_ev)
            grp.addButton(rb_cv)
            rb_ev.toggled.connect(lambda checked: self._mudar_destino("eventos") if checked else None)
            rb_cv.toggled.connect(lambda checked: self._mudar_destino("convidados") if checked else None)
            box_dest.addWidget(rb_ev)
            box_dest.addWidget(rb_cv)
            box_dest.addStretch(1)
            self.lay_din.addLayout(box_dest)

        lbl_map = QLabel(
            "<b>Mapeamento de colunas</b> — sugerido automaticamente por nome e conteúdo; ajuste se precisar"
        )
        self.lay_din.addWidget(lbl_map)

        sug = mp.sugerir(data, self.destino_atual)
        sug_cfg = bk.sugerir(list(data.columns), self.destino_atual, self.janela.cfg)
        usadas = set(sug.values())
        for campo, col in sug_cfg.items():
            if campo not in sug and col not in usadas:
                sug[campo] = col
                usadas.add(col)
        opcoes = [NAO_USAR] + list(data.columns)
        grade = QGridLayout()
        grade.setHorizontalSpacing(16)
        grade.setVerticalSpacing(10)

        campos_dest = v["campos_destino"][self.destino_atual]
        self._combos_mapa: dict[str, QComboBox] = {}
        for i, (campo, rotulo) in enumerate(campos_dest.items()):
            padrao = sug.get(campo)
            obrig = " *" if campo in OBRIGATORIOS[self.destino_atual] else ""
            celula = QWidget()
            v_cel = QVBoxLayout(celula)
            v_cel.setContentsMargins(0, 0, 0, 0)
            v_cel.setSpacing(4)
            v_cel.addWidget(QLabel(f"{rotulo}{obrig}"))
            cb = QComboBox()
            cb.addItems(opcoes)
            if padrao in opcoes:
                cb.setCurrentIndex(opcoes.index(padrao))
            cb.currentTextChanged.connect(self._atualizar_validacao)
            v_cel.addWidget(cb)
            self._combos_mapa[campo] = cb
            grade.addWidget(celula, i // 2, i % 2)

        self.lay_din.addLayout(grade)

        self.container_validacao = QWidget()
        self.lay_val = QVBoxLayout(self.container_validacao)
        self.lay_val.setContentsMargins(0, 0, 0, 0)
        self.lay_val.setSpacing(10)
        self.lay_din.addWidget(self.container_validacao)

        self._atualizar_validacao()

    def _mudar_destino(self, novo_dest: str):
        self.destino_atual = novo_dest
        self.janela.estado[f"{self.chave}_dest"] = novo_dest
        self._renderizar_fluxo()

    def _atualizar_validacao(self):
        self._limpar_layout(self.lay_val)
        if self.df_lido is None:
            return
        v = self.janela.vocab()
        campos_dest = v["campos_destino"][self.destino_atual]

        mapa = {
            campo: (None if cb.currentText() == NAO_USAR else cb.currentText())
            for campo, cb in self._combos_mapa.items()
        }
        faltando = [campos_dest[c] for c in OBRIGATORIOS[self.destino_atual] if not mapa.get(c)]
        if faltando:
            self.lay_val.addWidget(AlertBox("Mapeie os campos obrigatórios: " + ", ".join(faltando), "error"))
            return

        res = bk.validar(self.df_lido, self.destino_atual, mapa, self.janela.dados(self.destino_atual))

        linha_m = QHBoxLayout()
        linha_m.setSpacing(12)
        linha_m.addWidget(MetricCard("Prontos para gravar", len(res["ok"])))
        linha_m.addWidget(MetricCard("Com erro", len(res["erros"])))
        linha_m.addWidget(MetricCard("Duplicados ignorados", res["duplicados"]))
        self.lay_val.addLayout(linha_m)

        if res["padrao"]:
            cap = QLabel(f"{res['padrao']} linha(s) com status/situação não reconhecido receberam o valor padrão.")
            cap.setObjectName("Caption")
            self.lay_val.addWidget(cap)

        if res["erros"]:
            exp = ExpanderWidget(f"Ver {len(res['erros'])} linha(s) com erro (não serão importadas)")
            exp.corpo_layout.addWidget(
                PaginatedTableWidget(pd.DataFrame(res["erros"]), linhas_por_pagina=10, status_cols=())
            )
            self.lay_val.addWidget(exp)

        if res["ok"]:
            self.lay_val.addWidget(QLabel("<b>Prévia do que será gravado</b>"))
            prev = pd.DataFrame(res["ok"]).head(10)
            self.lay_val.addWidget(
                PaginatedTableWidget(
                    self.janela.formatar(prev, self.destino_atual),
                    linhas_por_pagina=10,
                )
            )

        btn_conf = QPushButton(f"Confirmar importação de {len(res['ok'])} registro(s)")
        btn_conf.setObjectName("PrimaryBtn")
        btn_conf.setEnabled(bool(res["ok"]))
        btn_conf.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_conf.clicked.connect(lambda: self._confirmar_importacao(res))
        self.lay_val.addWidget(btn_conf, alignment=Qt.AlignmentFlag.AlignLeft)

    def _confirmar_importacao(self, res: dict):
        v = self.janela.vocab()
        nome_dest = v["ent1_plural"] if self.destino_atual == "eventos" else v["ent2_plural"]
        nome_arq = self.caminho_arq.name if self.caminho_arq else "arquivo"
        db.inserir_lote(self.destino_atual, res["ok"])
        db.registrar_arquivo(
            nome_arq,
            nome_dest,
            len(res["ok"]),
            "Processado" if not res["erros"] else "Processado com erros",
        )
        self.janela.aviso(f"Importação: {len(res['ok'])} registro(s) de {nome_arq} em {nome_dest}")
        self.janela.flash(f"{len(res['ok'])} registro(s) gravados em {nome_dest}.")
        self._limpar_arquivo()


# ── Janela Principal Desktop ──
class OneWorldWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        db.init_db()
        self.cfg: dict = self._ler_configuracoes()
        self.campos_personalizados: list[str] = db.cfg_ler("campos_personalizados", [])
        self.notificacoes: list[str] = []
        self.pagina_atual: str = self.cfg.get("pagina_inicial", "Dashboard")
        if self.pagina_atual not in PAGINAS:
            self.pagina_atual = "Dashboard"
        self.estado: dict = {}
        self._flash_msg: str | None = None

        self.setWindowTitle(self.cfg["nome"])
        logo = bk.logo_atual()
        if logo and logo.exists():
            self.setWindowIcon(QIcon(str(logo)))
        self.resize(1340, 840)

        raiz = QWidget()
        raiz.setObjectName("MainContent")
        self.setCentralWidget(raiz)
        lay_raiz = QHBoxLayout(raiz)
        lay_raiz.setContentsMargins(0, 0, 0, 0)
        lay_raiz.setSpacing(0)

        self.sidebar_frame = QFrame()
        self.sidebar_frame.setObjectName("Sidebar")
        self.sidebar_frame.setFixedWidth(255)
        self.lay_sidebar = QVBoxLayout(self.sidebar_frame)
        self.lay_sidebar.setContentsMargins(18, 22, 18, 18)
        self.lay_sidebar.setSpacing(8)
        lay_raiz.addWidget(self.sidebar_frame)

        self.scroll = QScrollArea()
        self.scroll.setObjectName("PageScroll")
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        lay_raiz.addWidget(self.scroll, stretch=1)

        self.page_container = QWidget()
        self.page_container.setObjectName("PageContainer")
        self.lay_pagina = QVBoxLayout(self.page_container)
        self.scroll.setWidget(self.page_container)

        self.timer_refresh = QTimer(self)
        self.timer_refresh.setInterval(30_000)
        self.timer_refresh.timeout.connect(self._ao_disparar_timer)

        self.aplicar_tema()
        self.reconstruir_sidebar()
        self.reconstruir_pagina()

    # ── Helpers de estado, vocabulário e dados ──
    @staticmethod
    def _ler_configuracoes() -> dict:
        """Lê as configurações do banco, completando com os padrões e corrigindo valores inválidos."""
        cfg = {**PADROES, **db.cfg_ler("config", {})}
        if cfg.get("texto") not in ("P", "M", "G"):
            cfg["texto"] = "M"
        if cfg.get("perfil_negocio") not in PERFIS_NEGOCIO:
            cfg["perfil_negocio"] = PERFIL_PADRAO
        if not isinstance(cfg.get("rotulos_custom"), dict):
            cfg["rotulos_custom"] = {}
        return cfg

    def vocab(self) -> dict:
        return obter_vocabulario(self.cfg)

    def dados(self, tab: str) -> pd.DataFrame:
        return db.carregar(tab, self.campos_personalizados)

    def moeda(self, v) -> str:
        return bk.moeda(v, self.cfg)

    def formatar(self, df: pd.DataFrame, tab: str) -> pd.DataFrame:
        return bk.formatar(df, tab, self.cfg)

    def aviso(self, txt: str):
        self.notificacoes.insert(0, txt)
        self.notificacoes = self.notificacoes[:20]

    def flash(self, msg: str):
        self._flash_msg = msg

    def aplicar_tema(self):
        self.setWindowTitle(self.cfg["nome"])
        self.setStyleSheet(gerar_qss(self.cfg))
        gap, pad, _ = metricas_layout(self.cfg)
        self.lay_pagina.setContentsMargins(pad, pad, pad, pad)
        self.lay_pagina.setSpacing(gap)
        if self.cfg.get("auto_refresh"):
            if not self.timer_refresh.isActive():
                self.timer_refresh.start()
        else:
            self.timer_refresh.stop()

    def _ao_disparar_timer(self):
        if self.pagina_atual == "Dashboard" and self.cfg.get("auto_refresh"):
            self.reconstruir_pagina()

    def _limpar_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
            elif item.layout():
                self._limpar_layout(item.layout())

    # ── Sidebar ──
    def reconstruir_sidebar(self):
        self._limpar_layout(self.lay_sidebar)

        logo = bk.logo_atual()
        if logo and logo.exists():
            lbl_logo = QLabel()
            pix = pixmap_arredondado(logo, 136, raio=12)
            if not pix.isNull():
                lbl_logo.setPixmap(pix)
                self.lay_sidebar.addWidget(lbl_logo, alignment=Qt.AlignmentFlag.AlignCenter)
            if bk.sem_acento(self.cfg["nome"]) != "oneworld":
                lbl_nm = QLabel(f"<b>{self.cfg['nome']}</b>")
                lbl_nm.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.lay_sidebar.addWidget(lbl_nm)
        else:
            lbl_nm = QLabel(self.cfg["nome"])
            lbl_nm.setObjectName("MainTitle")
            self.lay_sidebar.addWidget(lbl_nm)

        cap_sub = QLabel("Gerência e análise em um só mundo")
        cap_sub.setObjectName("Caption")
        cap_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cap_sub.setWordWrap(True)
        self.lay_sidebar.addWidget(cap_sub)
        self.lay_sidebar.addSpacing(10)

        lbl_nav = QLabel("NAVEGAÇÃO")
        lbl_nav.setObjectName("Caption")
        self.lay_sidebar.addWidget(lbl_nav)

        self._botoes_nav: dict[str, QPushButton] = {}
        for pg in PAGINAS:
            rot_visivel = rotulo_pagina(pg, self.cfg)
            btn = QPushButton(rot_visivel.replace("&", "&&"))
            btn.setObjectName("NavBtn")
            btn.setProperty("active", "true" if pg == self.pagina_atual else "false")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _, p=pg: self.navegar_para(p))
            self._botoes_nav[pg] = btn
            self.lay_sidebar.addWidget(btn)

        self.lay_sidebar.addStretch(1)

        card_amb = QFrame()
        card_amb.setObjectName("SidebarEnvCard")
        lay_amb = QVBoxLayout(card_amb)
        lay_amb.setContentsMargins(12, 10, 12, 10)
        lay_amb.setSpacing(3)
        lbl_amb = QLabel("AMBIENTE")
        lbl_amb.setObjectName("MetricLabel")
        lay_amb.addWidget(lbl_amb)
        perfil_txt = self.cfg.get("perfil_negocio", PERFIL_PADRAO)
        for info in (f"Perfil: {perfil_txt}", "Banco: SQLite local + Base CVM", "Status: Operacional"):
            lbl_i = QLabel(info)
            lbl_i.setObjectName("Caption")
            lbl_i.setWordWrap(True)
            lay_amb.addWidget(lbl_i)
        self.lay_sidebar.addWidget(card_amb)

        self.sidebar_frame.style().unpolish(self.sidebar_frame)
        self.sidebar_frame.style().polish(self.sidebar_frame)

    def navegar_para(self, nova_pagina: str):
        if nova_pagina not in PAGINAS:
            nova_pagina = "Dashboard"
        if nova_pagina != self.pagina_atual and not self.cfg.get("lembrar_filtros", True):
            for k in FILTROS:
                self.estado.pop(k, None)
        self.pagina_atual = nova_pagina
        self.reconstruir_sidebar()
        self.reconstruir_pagina()

    # ── Peças de Página ──
    def _cabecalho(self, titulo_txt: str, subtitulo_txt: str):
        lbl_t = QLabel(titulo_txt)
        lbl_t.setObjectName("MainTitle")
        self.lay_pagina.addWidget(lbl_t)

        barra = QFrame()
        barra.setObjectName("BrandBar")
        self.lay_pagina.addWidget(barra, alignment=Qt.AlignmentFlag.AlignLeft)

        lbl_s = QLabel(subtitulo_txt)
        lbl_s.setObjectName("SubTitle")
        self.lay_pagina.addWidget(lbl_s)

        if self._flash_msg:
            self.lay_pagina.addWidget(AlertBox(self._flash_msg, "success"))
            self._flash_msg = None

    def _subtitulo(self, txt: str) -> QLabel:
        lbl = QLabel(txt)
        lbl.setObjectName("SectionTitle")
        return lbl

    def _exportar_csv_dialogo(self, df: pd.DataFrame, nome_padrao: str):
        caminho, _ = QFileDialog.getSaveFileName(
            self,
            "Exportar CSV",
            nome_padrao,
            "Arquivo CSV (*.csv)",
        )
        if caminho:
            Path(caminho).write_bytes(df.to_csv(index=False).encode("utf-8-sig"))
            self.flash(f"Arquivo exportado com sucesso: {Path(caminho).name}")
            self.reconstruir_pagina()

    def reconstruir_pagina(self):
        self._limpar_layout(self.lay_pagina)
        rotas = {
            "Dashboard": self.pagina_dashboard,
            "Eventos": self.pagina_eventos,
            "Convidados & Planilhas": self.pagina_convidados,
            "Dados Externos": self.pagina_dados_externos,
            "Orientação IA": self.pagina_ia,
            "Configurações": self.pagina_config,
        }
        if self.pagina_atual not in rotas:
            self.pagina_atual = "Dashboard"
        rotas[self.pagina_atual]()

        self.lay_pagina.addStretch(1)
        self.lay_pagina.addWidget(Divider())
        rodape = QLabel("OneWorld — BI & Gestão · dados em SQLite local · estrutura adaptável por perfil de negócio.")
        rodape.setObjectName("Caption")
        self.lay_pagina.addWidget(rodape)

    # ── PÁGINA 1: DASHBOARD ──
    def pagina_dashboard(self):
        self._cabecalho("Dashboard", "Visão consolidada dos dados, finanças e indicadores do negócio")
        self._montar_dashboard_negocio(self.lay_pagina)

    def _montar_dashboard_negocio(self, container_lay: QVBoxLayout):
        v = self.vocab()
        e, cv = self.dados("eventos"), self.dados("convidados")

        # ── 1. Barra Superior: Filtros + Ações Rápidas ──
        card_topo = QFrame()
        card_topo.setObjectName("ToolbarCard")
        lay_topo = QHBoxLayout(card_topo)
        lay_topo.setContentsMargins(16, 12, 16, 12)
        lay_topo.setSpacing(18)

        col_f1 = QVBoxLayout()
        col_f1.setSpacing(4)
        lbl_per = QLabel("Período")
        lbl_per.setObjectName("MetricLabel")
        col_f1.addWidget(lbl_per)
        cb_mes = QComboBox()
        cb_mes.setMinimumWidth(150)
        meses = ["Todos"] + bk.meses_disponiveis(e)
        for m in meses:
            rot = m if m == "Todos" else f"{m[5:]}/{m[:4]}"
            cb_mes.addItem(rot, userData=m)
        mes_atual = self.estado.get("dash_mes", "Todos")
        if mes_atual not in meses:
            mes_atual = "Todos"
        cb_mes.setCurrentIndex(meses.index(mes_atual))
        cb_mes.currentIndexChanged.connect(
            lambda _: self._definir_filtro("dash_mes", cb_mes.currentData())
        )
        col_f1.addWidget(cb_mes)
        lay_topo.addLayout(col_f1)

        col_f2 = QVBoxLayout()
        col_f2.setSpacing(4)
        lbl_st = QLabel(v["rotulos"]["status"])
        lbl_st.setObjectName("MetricLabel")
        col_f2.addWidget(lbl_st)
        stat_atual = self.estado.get("dash_status", [])
        ms_status = MultiSelectChips(STATUS_EVENTO, stat_atual, self.cfg["cor"])
        ms_status.changed.connect(lambda vals: self._definir_filtro("dash_status", vals))
        col_f2.addWidget(ms_status)
        lay_topo.addLayout(col_f2, stretch=1)

        col_acoes = QVBoxLayout()
        col_acoes.setSpacing(4)
        lbl_ac = QLabel("Ações rápidas")
        lbl_ac.setObjectName("MetricLabel")
        col_acoes.addWidget(lbl_ac)
        linha_ac = QHBoxLayout()
        linha_ac.setSpacing(8)

        btn_nova_op = QPushButton(f"+ {v['ent1_singular']}")
        btn_nova_op.setObjectName("PrimaryBtn")
        btn_nova_op.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_nova_op.clicked.connect(lambda: self._abrir_modulo_financeiro(0))
        linha_ac.addWidget(btn_nova_op)

        btn_novo_gasto = QPushButton(f"+ {v['ent2_singular']}")
        btn_novo_gasto.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_novo_gasto.clicked.connect(lambda: self._abrir_modulo_financeiro(1))
        linha_ac.addWidget(btn_novo_gasto)

        btn_imp = QPushButton("Importar Planilha")
        btn_imp.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_imp.clicked.connect(lambda: self.navegar_para("Dados Externos"))
        linha_ac.addWidget(btn_imp)

        btn_ia = QPushButton("Orientação IA (CVM)")
        btn_ia.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_ia.clicked.connect(lambda: self.navegar_para("Orientação IA"))
        linha_ac.addWidget(btn_ia)

        col_acoes.addLayout(linha_ac)
        lay_topo.addLayout(col_acoes)

        container_lay.addWidget(card_topo)

        # ── 2. Faixa de Indicadores (KPIs Financeiros) ──
        f = bk.filtrar_eventos(e, mes_atual, stat_atual)
        fin = bk.resumo_financeiro(f, cv)
        pend_rec = int(f["status"].isin(["Pendente", "Em planejamento"]).sum()) if not f.empty else 0

        linha_m = QHBoxLayout()
        linha_m.setSpacing(12)
        for rot, val in (
            (v["metric_valor"], self.moeda(fin["receita_bruta"])),
            ("Total de Gastos", self.moeda(fin["gasto_total"])),
            ("Rendimento Líquido", self.moeda(fin["rendimento_liquido"])),
            ("Margem / Rendimento", f"{fin['margem_pct']:.1f}%"),
            (v["metric_pend"], pend_rec),
        ):
            mc = MetricCard(rot, val)
            mc.setMinimumHeight(84)
            linha_m.addWidget(mc)
        container_lay.addLayout(linha_m)

        cap = QLabel(v["legenda_valor"])
        cap.setObjectName("Caption")
        container_lay.addWidget(cap)

        # ── 2b. Comparação CVM & Decision Intelligence ──
        self.cvm_painel_negocio = CVMComparacaoPainel(
            self.cfg,
            lambda resumo=fin: resumo,
            parent=self,
        )
        container_lay.addWidget(self.cvm_painel_negocio)

        # ── 3. Estado Vazio Limpo (quando o banco local está sem registros) ──
        if e.empty and cv.empty:
            card_vazio = QFrame()
            card_vazio.setObjectName("EmptyStateCard")
            lay_vazio = QVBoxLayout(card_vazio)
            lay_vazio.setContentsMargins(28, 28, 28, 28)
            lay_vazio.setSpacing(10)

            lbl_vt = QLabel("Base financeira limpa e pronta para uso")
            lbl_vt.setObjectName("EmptyTitle")
            lbl_vt.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lay_vazio.addWidget(lbl_vt)

            lbl_vd = QLabel(
                f"Nenhum registro de {v['ent1_plural'].lower()} ou {v['ent2_plural'].lower()} foi inserido ainda.\n"
                "A base pública DFP da CVM já está disponível para consulta comparativa em 'Orientação IA'."
            )
            lbl_vd.setObjectName("Caption")
            lbl_vd.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl_vd.setWordWrap(True)
            lay_vazio.addWidget(lbl_vd)

            linha_bv = QHBoxLayout()
            linha_bv.addStretch(1)

            b1 = QPushButton(f"Cadastrar {v['ent1_singular'].lower()}")
            b1.setObjectName("PrimaryBtn")
            b1.setCursor(Qt.CursorShape.PointingHandCursor)
            b1.clicked.connect(lambda: self._abrir_modulo_financeiro(0))
            linha_bv.addWidget(b1)

            b_gasto = QPushButton(f"Lançar {v['ent2_singular'].lower()}")
            b_gasto.setCursor(Qt.CursorShape.PointingHandCursor)
            b_gasto.clicked.connect(lambda: self._abrir_modulo_financeiro(1))
            linha_bv.addWidget(b_gasto)

            b2 = QPushButton("Importar planilha externa")
            b2.setCursor(Qt.CursorShape.PointingHandCursor)
            b2.clicked.connect(lambda: self.navegar_para("Dados Externos"))
            linha_bv.addWidget(b2)

            b3 = QPushButton("Consultar CVM / Orientação IA")
            b3.setCursor(Qt.CursorShape.PointingHandCursor)
            b3.clicked.connect(lambda: self.navegar_para("Orientação IA"))
            linha_bv.addWidget(b3)

            linha_bv.addStretch(1)
            lay_vazio.addSpacing(6)
            lay_vazio.addLayout(linha_bv)
            container_lay.addWidget(card_vazio)
            container_lay.addStretch(1)
            return

        # ── 4. Gráficos e Painel de Notificações (quando há dados) ──
        linha_g = QHBoxLayout()
        linha_g.setSpacing(16)

        card_g1 = QFrame()
        card_g1.setObjectName("OwCard")
        col_g1 = QVBoxLayout(card_g1)
        col_g1.setContentsMargins(16, 14, 16, 14)

        card_g2 = QFrame()
        card_g2.setObjectName("OwCard")
        col_g2 = QVBoxLayout(card_g2)
        col_g2.setContentsMargins(16, 14, 16, 14)

        card_g3 = QFrame()
        card_g3.setObjectName("OwCard")
        col_g3 = QVBoxLayout(card_g3)
        col_g3.setContentsMargins(16, 14, 16, 14)

        if not f.empty:
            t = f.assign(mes=pd.to_datetime(f["data"]).dt.strftime("%Y-%m"))
            col_g1.addWidget(self._subtitulo(f"{v['metric_valor']} por mês"))
            col_g1.addWidget(BarChartWidget(t.groupby("mes")["valor"].sum(), self.cfg["cor"], self.cfg, True))
        else:
            col_g1.addWidget(self._subtitulo(f"{v['metric_valor']} por mês"))
            col_g1.addWidget(AlertBox("Nenhum registro de receita corresponde aos filtros selecionados.", "info"))

        if not fin["gastos_por_categoria"].empty:
            col_g2.addWidget(self._subtitulo("Gastos por categoria (R$)"))
            col_g2.addWidget(BarChartWidget(fin["gastos_por_categoria"], self.cfg["cor2"], self.cfg, True))
        elif not f.empty:
            col_g2.addWidget(self._subtitulo(v["grafico_status"]))
            col_g2.addWidget(BarChartWidget(f.groupby("status").size(), self.cfg["cor2"], self.cfg, False))
        else:
            col_g2.addWidget(self._subtitulo("Gastos por categoria (R$)"))
            col_g2.addWidget(AlertBox("Nenhum gasto registrado para exibir no gráfico.", "info"))

        col_g3.addWidget(self._subtitulo("Notificações & Alertas"))
        tem_notif = False
        if self.cfg.get("lembretes", True):
            for msg in bk.lembretes(e):
                col_g3.addWidget(AlertBox(msg, "warning"))
                tem_notif = True
        for n in self.notificacoes[:5]:
            col_g3.addWidget(AlertBox(n, "info"))
            tem_notif = True
        if not tem_notif:
            lbl_sem = QLabel("Nenhuma notificação ou pendência no momento.")
            lbl_sem.setObjectName("Caption")
            col_g3.addWidget(lbl_sem)
        col_g3.addStretch(1)

        linha_g.addWidget(card_g1, stretch=20)
        linha_g.addWidget(card_g2, stretch=20)
        linha_g.addWidget(card_g3, stretch=14)
        container_lay.addLayout(linha_g)

        # ── 5. Tabela de Próximas Operações ──
        card_tab = QFrame()
        card_tab.setObjectName("OwCard")
        lay_tab = QVBoxLayout(card_tab)
        lay_tab.setContentsMargins(16, 14, 16, 14)
        lay_tab.addWidget(self._subtitulo(v["proximos_titulo"]))
        prox = f[pd.to_datetime(f["data"]).dt.date >= date.today()] if not f.empty else f
        df_exibir = (prox if not prox.empty else f).drop(columns=["id"], errors="ignore")
        lay_tab.addWidget(
            PaginatedTableWidget(
                self.formatar(df_exibir, "eventos"),
                linhas_por_pagina=self.cfg["linhas"],
                pagina_inicial=self.estado.get("pg_dash", 1),
                ao_mudar_pagina=lambda pg: self.estado.__setitem__("pg_dash", pg),
            )
        )
        container_lay.addWidget(card_tab)

    def _definir_filtro(self, chave: str, valor):
        self.estado[chave] = valor
        self.reconstruir_pagina()

    def _abrir_modulo_financeiro(self, aba_idx: int):
        self.estado["tab_modulo_fin"] = aba_idx
        self.navegar_para("Eventos")

    # ── PÁGINA 2: MÓDULO UNIFICADO (RECEITAS/OPERAÇÕES + GASTOS/DESPESAS) ──
    def pagina_eventos(self):
        v = self.vocab()
        self._cabecalho(v["menu_ent1"], v["ent1_subtitulo"])

        e = self.dados("eventos")

        abas_mod = QTabWidget()

        w_ev = QWidget()
        lay_ev = QVBoxLayout(w_ev)
        lay_ev.setContentsMargins(12, 12, 12, 12)
        lay_ev.setSpacing(10)
        self._montar_aba_eventos(lay_ev, e)
        abas_mod.addTab(w_ev, f"💰 {v['ent1_plural']} (Entradas)")

        w_cv = QWidget()
        lay_cv = QVBoxLayout(w_cv)
        lay_cv.setContentsMargins(12, 12, 12, 12)
        lay_cv.setSpacing(10)
        self._montar_aba_convidados(lay_cv)
        abas_mod.addTab(w_cv, f"📉 {v['ent2_plural']} (Saídas & Custos)")

        idx_mod = self.estado.get("tab_modulo_fin", 0)
        if idx_mod not in (0, 1):
            idx_mod = 0
        abas_mod.setCurrentIndex(idx_mod)
        abas_mod.currentChanged.connect(lambda idx: self.estado.__setitem__("tab_modulo_fin", idx))
        self.lay_pagina.addWidget(abas_mod)

    def _montar_aba_eventos(self, container_lay: QVBoxLayout, e: pd.DataFrame):
        v = self.vocab()
        abas = QTabWidget()

        # Aba 1: Listagem
        w_lista = QWidget()
        l_lista = QVBoxLayout(w_lista)
        l_lista.setContentsMargins(16, 16, 16, 16)
        l_lista.setSpacing(12)

        barra_f = QHBoxLayout()
        barra_f.setSpacing(16)

        c1 = QVBoxLayout()
        c1.addWidget(QLabel(f"Buscar em {v['ent1_plural'].lower()}"))
        ed_busca = QLineEdit(self.estado.get("ev_busca", ""))
        ed_busca.setPlaceholderText("Digite para filtrar...")
        c1.addWidget(ed_busca)
        barra_f.addLayout(c1, stretch=1)

        c2 = QVBoxLayout()
        c2.addWidget(QLabel(f"Filtrar {v['rotulos']['status'].lower()}"))
        ms_stat = MultiSelectChips(STATUS_EVENTO, self.estado.get("ev_status", []), self.cfg["cor"])
        c2.addWidget(ms_stat)
        barra_f.addLayout(c2, stretch=2)
        l_lista.addLayout(barra_f)

        container_tab = QWidget()
        lay_tab = QVBoxLayout(container_tab)
        lay_tab.setContentsMargins(0, 0, 0, 0)
        l_lista.addWidget(container_tab)

        btn_csv = QPushButton("Exportar CSV")
        btn_csv.setCursor(Qt.CursorShape.PointingHandCursor)
        l_lista.addWidget(btn_csv, alignment=Qt.AlignmentFlag.AlignLeft)
        l_lista.addStretch(1)

        def atualizar_lista_eventos():
            self._limpar_layout(lay_tab)
            busca = ed_busca.text().strip()
            status = ms_stat.valores()
            self.estado["ev_busca"] = busca
            self.estado["ev_status"] = status
            df_f = e.copy()
            if busca:
                df_f = df_f[
                    df_f.astype(str).apply(lambda col: col.str.contains(busca, case=False, na=False)).any(axis=1)
                ]
            if status:
                df_f = df_f[df_f["status"].isin(status)]
            lay_tab.addWidget(
                PaginatedTableWidget(
                    self.formatar(df_f, "eventos"),
                    linhas_por_pagina=self.cfg["linhas"],
                    pagina_inicial=self.estado.get("pg_eventos", 1),
                    ao_mudar_pagina=lambda pg: self.estado.__setitem__("pg_eventos", pg),
                )
            )
            try:
                btn_csv.clicked.disconnect()
            except Exception:
                pass
            nome_csv = f"{bk.chave(v['ent1_plural']) or 'operacoes'}.csv"
            btn_csv.clicked.connect(lambda: self._exportar_csv_dialogo(df_f, nome_csv))

        ed_busca.textChanged.connect(lambda _: atualizar_lista_eventos())
        ms_stat.changed.connect(lambda _: atualizar_lista_eventos())
        atualizar_lista_eventos()
        abas.addTab(w_lista, v["ent1_plural"])

        # Aba 2: + Novo registro
        w_novo = QWidget()
        l_novo = QVBoxLayout(w_novo)
        l_novo.setContentsMargins(16, 16, 16, 16)
        l_novo.setSpacing(12)

        form_ne, ler_ne = self._montar_form_evento(None)
        l_novo.addLayout(form_ne)
        lbl_erro_ne = QLabel()
        lbl_erro_ne.setStyleSheet("color: #8F2412; font-weight: 600;")
        lbl_erro_ne.setVisible(False)
        l_novo.addWidget(lbl_erro_ne)

        btn_cad = QPushButton("Cadastrar")
        btn_cad.setObjectName("PrimaryBtn")
        btn_cad.setCursor(Qt.CursorShape.PointingHandCursor)

        def salvar_novo_evento():
            dd, extras = ler_ne()
            if not dd["cliente"]:
                lbl_erro_ne.setText(f"Informe o campo '{v['rotulos']['cliente']}'.")
                lbl_erro_ne.setVisible(True)
                return
            db.inserir_lote("eventos", [dd], extras)
            self.aviso(f"Novo registro ({v['ent1_singular']}): {dd['cliente']}")
            self.flash(f"{v['ent1_singular']} cadastrado(a) com sucesso.")
            self.reconstruir_pagina()

        btn_cad.clicked.connect(salvar_novo_evento)
        l_novo.addWidget(btn_cad, alignment=Qt.AlignmentFlag.AlignLeft)
        l_novo.addStretch(1)
        abas.addTab(w_novo, f"+ Adicionar {v['ent1_singular']}")

        # Aba 3: Editar / excluir
        w_ed = QWidget()
        l_ed = QVBoxLayout(w_ed)
        l_ed.setContentsMargins(16, 16, 16, 16)
        l_ed.setSpacing(12)

        if e.empty:
            l_ed.addWidget(AlertBox(f"Nenhum registro em {v['ent1_plural'].lower()}.", "info"))
        else:
            l_ed.addWidget(QLabel(f"Escolha o registro ({v['ent1_singular']})"))
            cb_sel = QComboBox()
            ids = []
            for r in e.itertuples():
                ids.append(int(r.id))
                cb_sel.addItem(f"#{r.id} · {bk.fmt_data(r.data)} · {r.cliente}", userData=int(r.id))
            sel_atual = self.estado.get("ev_sel", ids[0])
            if sel_atual in ids:
                cb_sel.setCurrentIndex(ids.index(sel_atual))
            l_ed.addWidget(cb_sel)

            area_ed = QWidget()
            lay_area_ed = QVBoxLayout(area_ed)
            lay_area_ed.setContentsMargins(0, 0, 0, 0)
            lay_area_ed.setSpacing(10)
            l_ed.addWidget(area_ed)

            def montar_edicao_evento():
                self._limpar_layout(lay_area_ed)
                id_sel = cb_sel.currentData()
                self.estado["ev_sel"] = id_sel
                row = e[e["id"] == id_sel].iloc[0].to_dict()
                form_ee, ler_ee = self._montar_form_evento(row)
                lay_area_ed.addLayout(form_ee)

                lbl_err = QLabel()
                lbl_err.setStyleSheet("color: #8F2412; font-weight: 600;")
                lbl_err.setVisible(False)
                lay_area_ed.addWidget(lbl_err)

                btn_salvar = QPushButton("Salvar alterações")
                btn_salvar.setObjectName("PrimaryBtn")
                btn_salvar.setCursor(Qt.CursorShape.PointingHandCursor)

                def confirmar_edicao():
                    dd, extras = ler_ee()
                    if not dd["cliente"]:
                        lbl_err.setText(f"Informe o campo '{v['rotulos']['cliente']}'.")
                        lbl_err.setVisible(True)
                        return
                    db.atualizar("eventos", id_sel, dd, extras)
                    if dd["cliente"] != row["cliente"]:
                        db.renomear_evento_nos_convidados(dd["cliente"], row["cliente"])
                    self.aviso(f"{v['ent1_singular']} atualizado(a): {dd['cliente']}")
                    self.flash("Registro atualizado.")
                    self.reconstruir_pagina()

                btn_salvar.clicked.connect(confirmar_edicao)
                lay_area_ed.addWidget(btn_salvar, alignment=Qt.AlignmentFlag.AlignLeft)
                lay_area_ed.addWidget(Divider())

                vinc = db.contar_convidados_do_evento(row["cliente"])
                aviso_vinc = (
                    f"{vinc} registro(s) em '{v['ent2_plural']}' estão vinculados a este item e continuarão cadastrados."
                    if vinc
                    else ""
                )
                lay_area_ed.addWidget(self._bloco_excluir("eventos", id_sel, row["cliente"], aviso_vinc))

            cb_sel.currentIndexChanged.connect(lambda _: montar_edicao_evento())
            montar_edicao_evento()
            l_ed.addWidget(Divider())
            l_ed.addWidget(
                self._bloco_excluir_lote(
                    "eventos",
                    e,
                    lambda r: f"#{r.id} · {bk.fmt_data(r.data)} · {r.cliente}",
                )
            )
            l_ed.addStretch(1)

        abas.addTab(w_ed, "Editar / excluir")
        abas.setCurrentIndex(self.estado.get("tab_eventos", 0))
        abas.currentChanged.connect(lambda idx: self.estado.__setitem__("tab_eventos", idx))
        container_lay.addWidget(abas)

    def _montar_form_evento(self, v_row: dict | None):
        v_row = {} if v_row is None else v_row
        rot = self.vocab()["rotulos"]
        form = QFormLayout()
        form.setSpacing(10)

        ed_cli = QLineEdit(str(v_row.get("cliente", "")))
        dt_val = bk.parse_date(v_row.get("data")) or date.today()
        ed_dt = QDateEdit(QDate(dt_val.year, dt_val.month, dt_val.day))
        ed_dt.setCalendarPopup(True)
        ed_dt.setDisplayFormat("dd/MM/yyyy")

        ed_loc = QLineEdit(str(v_row.get("local", "")))
        sp_cv = QSpinBox()
        sp_cv.setRange(0, 1_000_000)
        sp_cv.setValue(int(v_row.get("convidados", 0) or 0))

        sp_vl = QDoubleSpinBox()
        sp_vl.setRange(0.0, 1_000_000_000.0)
        sp_vl.setDecimals(2)
        sp_vl.setSingleStep(100.0)
        sp_vl.setValue(float(v_row.get("valor", 0.0) or 0.0))

        cb_st = QComboBox()
        cb_st.addItems(STATUS_EVENTO)
        atual_st = v_row.get("status")
        if atual_st in STATUS_EVENTO:
            cb_st.setCurrentIndex(STATUS_EVENTO.index(atual_st))

        form.addRow(rot["cliente"], ed_cli)
        form.addRow(rot["data"], ed_dt)
        form.addRow(rot["local"], ed_loc)
        form.addRow(rot["convidados"], sp_cv)
        form.addRow(rot["valor"], sp_vl)
        form.addRow(rot["status"], cb_st)

        campos_ex: dict[str, QLineEdit] = {}
        for c in self.campos_personalizados:
            ed_x = QLineEdit(bk.texto(v_row.get(c, "")))
            campos_ex[c] = ed_x
            form.addRow(c, ed_x)

        def ler():
            qdt = ed_dt.date()
            iso = date(qdt.year(), qdt.month(), qdt.day()).isoformat()
            dados_ev = {
                "data": iso,
                "cliente": ed_cli.text().strip(),
                "local": ed_loc.text().strip(),
                "convidados": int(sp_cv.value()),
                "valor": float(sp_vl.value()),
                "status": cb_st.currentText(),
            }
            extras = {c: ed.text().strip() for c, ed in campos_ex.items()}
            return dados_ev, extras

        return form, ler

    def _bloco_excluir(self, tab: str, id_: int, descricao: str, aviso_extra: str = "") -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 4, 0, 0)
        lay.setSpacing(8)
        lay.addWidget(self._subtitulo("Excluir"))
        if aviso_extra:
            lay.addWidget(AlertBox(aviso_extra, "warning"))
        chk = QCheckBox(f"Confirmo a exclusão de: {descricao}")
        btn = QPushButton("Excluir registro")
        btn.setEnabled(False)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        chk.toggled.connect(btn.setEnabled)

        def confirmar():
            db.excluir(tab, id_)
            self.aviso(f"Registro excluído: {descricao}")
            self.flash("Registro excluído.")
            self.reconstruir_pagina()

        btn.clicked.connect(confirmar)
        lay.addWidget(chk)
        lay.addWidget(btn, alignment=Qt.AlignmentFlag.AlignLeft)
        return w

    def _bloco_excluir_lote(self, tab: str, df: pd.DataFrame, rotulo_fn) -> QWidget:
        """Exclusão em lote com filtro, seleção múltipla e botão 'Selecionar todos'."""
        card = QFrame()
        card.setObjectName("OwCard")
        lay = QVBoxLayout(card)
        lay.setContentsMargins(14, 12, 14, 12)
        lay.setSpacing(8)
        lay.addWidget(self._subtitulo("Exclusão em lote (selecionar vários ou todos)"))

        barra = QHBoxLayout()
        barra.setSpacing(8)
        ed_filtro = QLineEdit()
        ed_filtro.setPlaceholderText("Filtrar registros para seleção em lote...")
        barra.addWidget(ed_filtro, stretch=1)

        btn_todos = QPushButton("Selecionar todos")
        btn_todos.setCursor(Qt.CursorShape.PointingHandCursor)
        barra.addWidget(btn_todos)

        btn_nenhum = QPushButton("Desmarcar todos")
        btn_nenhum.setCursor(Qt.CursorShape.PointingHandCursor)
        barra.addWidget(btn_nenhum)
        lay.addLayout(barra)

        lista = QListWidget()
        lista.setMaximumHeight(190)
        for r in df.itertuples():
            item = QListWidgetItem(rotulo_fn(r))
            item.setData(Qt.ItemDataRole.UserRole, int(r.id))
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Unchecked)
            lista.addItem(item)
        lay.addWidget(lista)

        chk_conf = QCheckBox("Confirmo a exclusão dos 0 registro(s) selecionado(s)")
        btn_exc = QPushButton("Excluir selecionados")
        btn_exc.setEnabled(False)
        btn_exc.setCursor(Qt.CursorShape.PointingHandCursor)

        def ids_marcados() -> list[int]:
            return [
                int(lista.item(i).data(Qt.ItemDataRole.UserRole))
                for i in range(lista.count())
                if lista.item(i).checkState() == Qt.CheckState.Checked
            ]

        def atualizar_estado_lote():
            n = len(ids_marcados())
            chk_conf.setText(f"Confirmo a exclusão dos {n} registro(s) selecionado(s)")
            btn_exc.setEnabled(n > 0 and chk_conf.isChecked())

        def filtrar_itens():
            termo = bk.sem_acento(ed_filtro.text())
            for i in range(lista.count()):
                it = lista.item(i)
                it.setHidden(bool(termo) and termo not in bk.sem_acento(it.text()))

        def marcar_visiveis(marcar: bool):
            lista.blockSignals(True)
            estado = Qt.CheckState.Checked if marcar else Qt.CheckState.Unchecked
            for i in range(lista.count()):
                it = lista.item(i)
                if not it.isHidden():
                    it.setCheckState(estado)
            lista.blockSignals(False)
            atualizar_estado_lote()

        def confirmar_lote():
            ids = ids_marcados()
            if not ids:
                return
            db.excluir_lote(tab, ids)
            self.aviso(f"{len(ids)} registro(s) excluído(s) em lote ({tab}).")
            self.flash(f"{len(ids)} registro(s) excluído(s).")
            self.reconstruir_pagina()

        ed_filtro.textChanged.connect(filtrar_itens)
        btn_todos.clicked.connect(lambda: marcar_visiveis(True))
        btn_nenhum.clicked.connect(lambda: marcar_visiveis(False))
        lista.itemChanged.connect(lambda _: atualizar_estado_lote())
        chk_conf.toggled.connect(lambda _: atualizar_estado_lote())
        btn_exc.clicked.connect(confirmar_lote)

        lay.addWidget(chk_conf)
        lay.addWidget(btn_exc, alignment=Qt.AlignmentFlag.AlignLeft)
        return card

    # ── ABA SECUNDÁRIA UNIFICADA (GASTOS / DESPESAS / CADASTROS) ──
    def pagina_convidados(self):
        self.estado["tab_modulo_fin"] = 1
        self.pagina_eventos()

    def _montar_aba_convidados(self, container_lay: QVBoxLayout):
        v = self.vocab()
        rot = v["rotulos"]
        abas = QTabWidget()

        # Aba 1: Listagem
        w_lista = QWidget()
        l_lista = QVBoxLayout(w_lista)
        l_lista.setContentsMargins(16, 16, 16, 16)
        l_lista.setSpacing(12)

        g = self.dados("convidados")
        barra_f = QHBoxLayout()
        barra_f.setSpacing(14)

        c1 = QVBoxLayout()
        c1.addWidget(QLabel(f"Buscar em {v['ent2_plural'].lower()}"))
        ed_busca = QLineEdit(self.estado.get("cv_busca", ""))
        ed_busca.setPlaceholderText("Digite para filtrar...")
        c1.addWidget(ed_busca)
        barra_f.addLayout(c1, stretch=1)

        c2 = QVBoxLayout()
        c2.addWidget(QLabel(rot["evento"]))
        evs_disp = sorted(str(x) for x in g["evento"].unique() if str(x).strip()) if not g.empty else []
        ms_ev = MultiSelectChips(evs_disp, self.estado.get("cv_evento", []), self.cfg["cor"])
        c2.addWidget(ms_ev)
        barra_f.addLayout(c2, stretch=1)

        c3 = QVBoxLayout()
        c3.addWidget(QLabel(rot["confirmacao"]))
        ms_cf = MultiSelectChips(STATUS_CONV, self.estado.get("cv_conf", []), self.cfg["cor"])
        c3.addWidget(ms_cf)
        barra_f.addLayout(c3, stretch=1)
        l_lista.addLayout(barra_f)

        linha_m = QHBoxLayout()
        linha_m.setSpacing(12)
        card_total_gasto = MetricCard("Total de Gastos Filtrados", self.moeda(0))
        card_conf = MetricCard("Quitados / Confirmados", 0)
        card_pend = MetricCard("A pagar / Pendentes", 0)
        linha_m.addWidget(card_total_gasto)
        linha_m.addWidget(card_conf)
        linha_m.addWidget(card_pend)
        l_lista.addLayout(linha_m)

        container_tab = QWidget()
        lay_tab = QVBoxLayout(container_tab)
        lay_tab.setContentsMargins(0, 0, 0, 0)
        l_lista.addWidget(container_tab)

        btn_csv = QPushButton("Exportar CSV")
        btn_csv.setCursor(Qt.CursorShape.PointingHandCursor)
        l_lista.addWidget(btn_csv, alignment=Qt.AlignmentFlag.AlignLeft)
        l_lista.addStretch(1)

        def atualizar_lista_conv():
            self._limpar_layout(lay_tab)
            busca = ed_busca.text().strip()
            evs = ms_ev.valores()
            conf = ms_cf.valores()
            self.estado["cv_busca"] = busca
            self.estado["cv_evento"] = evs
            self.estado["cv_conf"] = conf

            df_f = g.copy()
            if busca:
                df_f = df_f[
                    df_f.astype(str).apply(lambda col: col.str.contains(busca, case=False, na=False)).any(axis=1)
                ]
            if evs:
                df_f = df_f[df_f["evento"].isin(evs)]
            if conf:
                df_f = df_f[df_f["confirmacao"].isin(conf)]

            total_g = (
                df_f[df_f["confirmacao"] != "Recusou"]["acompanhantes"].sum()
                if not df_f.empty
                else 0
            )
            card_total_gasto.atualizar(self.moeda(total_g))
            card_conf.atualizar(int((df_f["confirmacao"] == "Confirmado").sum()) if not df_f.empty else 0)
            card_pend.atualizar(int((df_f["confirmacao"] == "Pendente").sum()) if not df_f.empty else 0)

            lay_tab.addWidget(
                PaginatedTableWidget(
                    self.formatar(df_f, "convidados"),
                    linhas_por_pagina=self.cfg["linhas"],
                    pagina_inicial=self.estado.get("pg_convidados", 1),
                    ao_mudar_pagina=lambda pg: self.estado.__setitem__("pg_convidados", pg),
                )
            )
            try:
                btn_csv.clicked.disconnect()
            except Exception:
                pass
            nome_csv = f"{bk.chave(v['ent2_plural']) or 'cadastros'}.csv"
            btn_csv.clicked.connect(lambda: self._exportar_csv_dialogo(df_f, nome_csv))

        ed_busca.textChanged.connect(lambda _: atualizar_lista_conv())
        ms_ev.changed.connect(lambda _: atualizar_lista_conv())
        ms_cf.changed.connect(lambda _: atualizar_lista_conv())
        atualizar_lista_conv()
        abas.addTab(w_lista, v["ent2_plural"])

        # Aba 2: + Adicionar
        w_novo = QWidget()
        l_novo = QVBoxLayout(w_novo)
        l_novo.setContentsMargins(16, 16, 16, 16)
        l_novo.setSpacing(12)

        form_nc, ler_nc = self._montar_form_convidado(None)
        l_novo.addLayout(form_nc)
        lbl_erro_nc = QLabel()
        lbl_erro_nc.setStyleSheet("color: #8F2412; font-weight: 600;")
        lbl_erro_nc.setVisible(False)
        l_novo.addWidget(lbl_erro_nc)

        btn_add = QPushButton("Adicionar")
        btn_add.setObjectName("PrimaryBtn")
        btn_add.setCursor(Qt.CursorShape.PointingHandCursor)

        def salvar_novo_conv():
            dd, extras = ler_nc()
            if not dd["nome"]:
                lbl_erro_nc.setText(f"Informe o campo '{rot['nome']}'.")
                lbl_erro_nc.setVisible(True)
                return
            db.inserir_lote("convidados", [dd], extras)
            self.aviso(f"Novo registro ({v['ent2_singular']}): {dd['nome']}")
            self.flash(f"{v['ent2_singular']} adicionado(a).")
            self.reconstruir_pagina()

        btn_add.clicked.connect(salvar_novo_conv)
        l_novo.addWidget(btn_add, alignment=Qt.AlignmentFlag.AlignLeft)
        l_novo.addStretch(1)
        abas.addTab(w_novo, f"+ Adicionar {v['ent2_singular']}")

        # Aba 3: Editar / excluir
        w_ed = QWidget()
        l_ed = QVBoxLayout(w_ed)
        l_ed.setContentsMargins(16, 16, 16, 16)
        l_ed.setSpacing(12)

        if g.empty:
            l_ed.addWidget(AlertBox(f"Nenhum registro em {v['ent2_plural'].lower()}.", "info"))
        else:
            l_ed.addWidget(QLabel(f"Escolha o registro ({v['ent2_singular']})"))
            cb_sel = QComboBox()
            ids = []
            for r in g.itertuples():
                ids.append(int(r.id))
                cb_sel.addItem(f"#{r.id} · {r.nome} · {r.evento}", userData=int(r.id))
            sel_atual = self.estado.get("cv_sel", ids[0])
            if sel_atual in ids:
                cb_sel.setCurrentIndex(ids.index(sel_atual))
            l_ed.addWidget(cb_sel)

            area_ed = QWidget()
            lay_area_ed = QVBoxLayout(area_ed)
            lay_area_ed.setContentsMargins(0, 0, 0, 0)
            lay_area_ed.setSpacing(10)
            l_ed.addWidget(area_ed)

            def montar_edicao_conv():
                self._limpar_layout(lay_area_ed)
                id_sel = cb_sel.currentData()
                self.estado["cv_sel"] = id_sel
                row = g[g["id"] == id_sel].iloc[0].to_dict()
                form_ec, ler_ec = self._montar_form_convidado(row)
                lay_area_ed.addLayout(form_ec)

                lbl_err = QLabel()
                lbl_err.setStyleSheet("color: #8F2412; font-weight: 600;")
                lbl_err.setVisible(False)
                lay_area_ed.addWidget(lbl_err)

                btn_salvar = QPushButton("Salvar alterações")
                btn_salvar.setObjectName("PrimaryBtn")
                btn_salvar.setCursor(Qt.CursorShape.PointingHandCursor)

                def confirmar_edicao():
                    dd, extras = ler_ec()
                    if not dd["nome"]:
                        lbl_err.setText(f"Informe o campo '{rot['nome']}'.")
                        lbl_err.setVisible(True)
                        return
                    db.atualizar("convidados", id_sel, dd, extras)
                    self.aviso(f"{v['ent2_singular']} atualizado(a): {dd['nome']}")
                    self.flash("Registro atualizado.")
                    self.reconstruir_pagina()

                btn_salvar.clicked.connect(confirmar_edicao)
                lay_area_ed.addWidget(btn_salvar, alignment=Qt.AlignmentFlag.AlignLeft)
                lay_area_ed.addWidget(Divider())
                lay_area_ed.addWidget(self._bloco_excluir("convidados", id_sel, row["nome"]))

            cb_sel.currentIndexChanged.connect(lambda _: montar_edicao_conv())
            montar_edicao_conv()
            l_ed.addWidget(Divider())
            l_ed.addWidget(
                self._bloco_excluir_lote(
                    "convidados",
                    g,
                    lambda r: f"#{r.id} · {r.nome} · {r.evento}",
                )
            )
            l_ed.addStretch(1)

        abas.addTab(w_ed, "Editar / excluir")

        # Aba 4: Importar planilha
        w_imp = QWidget()
        l_imp = QVBoxLayout(w_imp)
        l_imp.setContentsMargins(16, 16, 16, 16)
        l_imp.addWidget(ImportarPlanilhaWidget(self, destino_fixo="convidados", chave_estado="impcv"))
        l_imp.addStretch(1)
        abas.addTab(w_imp, "Importar planilha")
        abas.setCurrentIndex(self.estado.get("tab_convidados", 0))
        abas.currentChanged.connect(lambda idx: self.estado.__setitem__("tab_convidados", idx))

        container_lay.addWidget(abas)

    def _montar_form_convidado(self, v_row: dict | None):
        v_row = {} if v_row is None else v_row
        rot = self.vocab()["rotulos"]
        form = QFormLayout()
        form.setSpacing(10)

        clientes = list(dict.fromkeys(self.dados("eventos")["cliente"].tolist()))
        atual_ev = str(v_row.get("evento", ""))
        if atual_ev and atual_ev not in clientes:
            clientes.append(atual_ev)

        if clientes:
            w_ev = QComboBox()
            w_ev.addItems(clientes)
            if atual_ev in clientes:
                w_ev.setCurrentIndex(clientes.index(atual_ev))
        else:
            w_ev = QLineEdit(atual_ev)

        ed_nm = QLineEdit(str(v_row.get("nome", "")))
        ed_ms = QLineEdit(bk.texto(v_row.get("mesa", "")))
        sp_ac = QSpinBox()
        sp_ac.setRange(0, 1_000_000_000)
        sp_ac.setSingleStep(50)
        sp_ac.setValue(int(v_row.get("acompanhantes", 0) or 0))
        ed_ct = QLineEdit(str(v_row.get("contato", "")))
        restr_val = "" if v_row.get("restricao", "—") == "—" else str(v_row.get("restricao", ""))
        ed_rs = QLineEdit(restr_val)

        cb_cf = QComboBox()
        cb_cf.addItems(STATUS_CONV)
        c_atual = v_row.get("confirmacao")
        if c_atual in STATUS_CONV:
            cb_cf.setCurrentIndex(STATUS_CONV.index(c_atual))

        form.addRow(rot["evento"], w_ev)
        form.addRow(rot["nome"], ed_nm)
        form.addRow(rot["mesa"], ed_ms)
        form.addRow(rot["acompanhantes"], sp_ac)
        form.addRow(rot["contato"], ed_ct)
        form.addRow(rot["restricao"], ed_rs)
        form.addRow(rot["confirmacao"], cb_cf)

        campos_ex: dict[str, QLineEdit] = {}
        for c in self.campos_personalizados:
            ed_x = QLineEdit(bk.texto(v_row.get(c, "")))
            campos_ex[c] = ed_x
            form.addRow(c, ed_x)

        def ler():
            ev_txt = w_ev.currentText() if isinstance(w_ev, QComboBox) else w_ev.text().strip()
            dados_cv = {
                "evento": ev_txt,
                "nome": ed_nm.text().strip(),
                "mesa": ed_ms.text().strip(),
                "acompanhantes": int(sp_ac.value()),
                "contato": ed_ct.text().strip(),
                "restricao": ed_rs.text().strip() or "—",
                "confirmacao": cb_cf.currentText(),
            }
            extras = {c: ed.text().strip() for c, ed in campos_ex.items()}
            return dados_cv, extras

        return form, ler

    # ── PÁGINA 4: DADOS EXTERNOS ──
    def pagina_dados_externos(self):
        self._cabecalho(
            "Dados Externos",
            "Gerenciamento de bases públicas de comparação (CVM) e importação de planilhas",
        )
        abas = QTabWidget()

        # Aba 1: Bases Públicas CVM (Comparação & Decision Intelligence)
        w_cvm = QWidget()
        lay_cvm = QVBoxLayout(w_cvm)
        lay_cvm.setContentsMargins(16, 16, 16, 16)
        lay_cvm.setSpacing(12)
        self.cvm_gerenciador = CVMGerenciadorWidget(self)
        lay_cvm.addWidget(self.cvm_gerenciador)
        lay_cvm.addStretch(1)
        abas.addTab(w_cvm, "📊 Bases CVM (Comparação)")

        # Aba 2: Importar Planilhas para Lançamentos do Negócio
        w_imp = QWidget()
        lay_imp = QVBoxLayout(w_imp)
        lay_imp.setContentsMargins(16, 16, 16, 16)
        lay_imp.setSpacing(12)
        lay_imp.addWidget(self._subtitulo("Importação de planilhas para lançamentos do negócio"))
        lay_imp.addWidget(ImportarPlanilhaWidget(self, destino_fixo=None, chave_estado="impex"))
        lay_imp.addStretch(1)
        abas.addTab(w_imp, "📥 Importar Planilhas (Negócio)")

        # Aba 3: Histórico de Importações
        w_hist = QWidget()
        lay_hist = QVBoxLayout(w_hist)
        lay_hist.setContentsMargins(16, 16, 16, 16)
        lay_hist.setSpacing(12)
        lay_hist.addWidget(self._subtitulo("Histórico de importações"))
        h = db.historico_arquivos()
        if h.empty:
            lay_hist.addWidget(AlertBox("Nenhum arquivo recebido.", "info"))
        else:
            lay_hist.addWidget(
                PaginatedTableWidget(h, linhas_por_pagina=self.cfg["linhas"], status_cols=())
            )
        lay_hist.addStretch(1)
        abas.addTab(w_hist, "🕒 Histórico")

        aba_idx = self.estado.get("tab_dados_externos", 0)
        if not 0 <= aba_idx < abas.count():
            aba_idx = 0
        abas.setCurrentIndex(aba_idx)
        abas.currentChanged.connect(lambda idx: self.estado.__setitem__("tab_dados_externos", idx))

        self.lay_pagina.addWidget(abas)

    # ── PÁGINA 5: ORIENTAÇÃO IA ──
    def pagina_ia(self):
        self._cabecalho("Orientação IA", "Perguntas, análises e troca de dados com IA externa")
        abas = QTabWidget()
        construtores = [
            ("Perguntar aos dados", self._aba_ia_perguntar),
            ("Atualizar dados com IA externa", self._aba_ia_atualizar),
            ("Pedir análise à IA externa", self._aba_ia_analise),
            ("Exportar Markdown", self._aba_ia_markdown),
        ]
        for titulo, construir in construtores:
            w = QWidget()
            lay = QVBoxLayout(w)
            lay.setContentsMargins(18, 18, 18, 18)
            lay.setSpacing(14)
            construir(lay)
            lay.addStretch(1)
            abas.addTab(w, titulo)
        abas.setCurrentIndex(self.estado.get("tab_ia", 0))
        abas.currentChanged.connect(lambda idx: self.estado.__setitem__("tab_ia", idx))
        self.lay_pagina.addWidget(abas)

    def _aba_ia_perguntar(self, lay: QVBoxLayout):
        st_llm = ia.llm_status()
        aviso_ia = (
            f"IA externa (BYOK) ativa: {st_llm['modelo']}. Ela orienta e sugere, sem alterar registros."
            if st_llm.get("pronto")
            else f"Resposta por regras locais ({st_llm.get('motivo', 'LLM não configurado')}). "
            "Configure a chave em .env para usar IA externa (BYOK); ela orienta e sugere, sem alterar registros."
        )
        lay.addWidget(AlertBox(aviso_ia, "info"))

        lay.addWidget(self._subtitulo("Pergunte sobre seus dados"))
        ed_perg = QPlainTextEdit()
        ed_perg.setPlaceholderText("Ex.: Qual é o valor/receita previsto por mês?")
        ed_perg.setMaximumHeight(95)
        lay.addWidget(ed_perg)

        btn_perg = QPushButton("Perguntar")
        btn_perg.setObjectName("PrimaryBtn")
        btn_perg.setCursor(Qt.CursorShape.PointingHandCursor)
        lay.addWidget(btn_perg, alignment=Qt.AlignmentFlag.AlignLeft)

        ult_resp = self.estado.get("ia_ultima_resposta")
        if ult_resp:
            lay.addWidget(self._subtitulo("Resposta"))
            lay.addWidget(AlertBox(ult_resp, "info"))

        def fazer_pergunta():
            p = ed_perg.toPlainText().strip()
            if not p:
                return
            resp_local = bk.responder_ia(p, self.dados("eventos"), self.dados("convidados"), self.cfg)
            resp = ia.resposta_com_llm(p, resp_local)
            db.salvar_relatorio(p, resp)
            self.estado["ia_ultima_resposta"] = resp
            self.reconstruir_pagina()

        btn_perg.clicked.connect(fazer_pergunta)

        lay.addWidget(self._subtitulo("Relatórios recentes"))
        rels = db.listar_relatorios()
        if rels.empty:
            cap_v = QLabel("Nenhuma pergunta registrada ainda.")
            cap_v.setObjectName("Caption")
            lay.addWidget(cap_v)
        else:
            for r in rels.itertuples():
                exp = ExpanderWidget(f"{r.data} — {r.pergunta}")
                lbl_r = QLabel(str(r.resposta))
                lbl_r.setWordWrap(True)
                exp.corpo_layout.addWidget(lbl_r)
                lay.addWidget(exp)

    def _aba_ia_markdown(self, lay: QVBoxLayout):
        cap_ex = QLabel(
            "Gera um Markdown com resumo, tabelas e um prompt sugerido para colar em um chat de IA externo. "
            "Ao colar, os dados saem do seu computador."
        )
        cap_ex.setObjectName("Caption")
        cap_ex.setWordWrap(True)
        lay.addWidget(cap_ex)

        e_df, cv_df = self.dados("eventos"), self.dados("convidados")
        estado_cvm = cvm_cmp.carregar_estado_cvm()
        bloco_cvm = ""
        if estado_cvm.get("ativa"):
            di = cvm_cmp.avaliar_decision_intelligence(
                bk.resumo_financeiro(e_df, cv_df), estado_cvm, self.cfg
            )
            bloco_cvm = di.get("markdown", "")
        md = bk.gerar_markdown(e_df, cv_df, self.cfg, bloco_cvm=bloco_cvm)
        btn_md = QPushButton("Baixar Markdown")
        btn_md.setCursor(Qt.CursorShape.PointingHandCursor)

        def salvar_md():
            caminho, _ = QFileDialog.getSaveFileName(
                self,
                "Baixar Markdown",
                "oneworld_export.md",
                "Markdown (*.md)",
            )
            if caminho:
                Path(caminho).write_text(md, encoding="utf-8")
                self.flash(f"Markdown salvo em: {Path(caminho).name}")
                self.reconstruir_pagina()

        btn_md.clicked.connect(salvar_md)
        lay.addWidget(btn_md, alignment=Qt.AlignmentFlag.AlignLeft)

        exp_prev = ExpanderWidget("Pré-visualizar")
        ed_code = QPlainTextEdit(md)
        ed_code.setReadOnly(True)
        ed_code.setMinimumHeight(220)
        ed_code.setFont(QFont("Consolas", 10))
        exp_prev.corpo_layout.addWidget(ed_code)
        lay.addWidget(exp_prev)

    # ── PÁGINA 6: CONFIGURAÇÕES ──
    def pagina_config(self):
        cfg = self.cfg
        v = self.vocab()
        self._cabecalho("Configurações", "Personalização do negócio, interface e eficiência")

        abas = QTabWidget()

        # Aba 1: Personalização visual
        w_vis = QWidget()
        l_vis = QVBoxLayout(w_vis)
        l_vis.setContentsMargins(16, 16, 16, 16)
        l_vis.setSpacing(12)

        l_vis.addWidget(QLabel("Nome do sistema / empresa"))
        ed_nome = QLineEdit(cfg["nome"])
        ed_nome.textChanged.connect(lambda txt: cfg.__setitem__("nome", txt))
        l_vis.addWidget(ed_nome)

        linha_cores = QHBoxLayout()
        btn_cor1 = QPushButton(f"Cor principal: {cfg['cor']}")
        btn_cor1.setStyleSheet(
            f"background-color: {cfg['cor']}; color: #FFFFFF; font-weight: 600; padding: 8px 14px;"
        )
        btn_cor2 = QPushButton(f"Cor de apoio: {cfg['cor2']}")
        btn_cor2.setStyleSheet(
            f"background-color: {cfg['cor2']}; color: #1E2140; font-weight: 600; padding: 8px 14px;"
        )

        def escolher_cor(chave_cor: str):
            c = QColorDialog.getColor(QColor(cfg[chave_cor]), self, "Escolher cor")
            if c.isValid():
                cfg[chave_cor] = c.name()
                self.aplicar_tema()
                self.reconstruir_sidebar()
                self.reconstruir_pagina()

        btn_cor1.clicked.connect(lambda: escolher_cor("cor"))
        btn_cor2.clicked.connect(lambda: escolher_cor("cor2"))
        linha_cores.addWidget(btn_cor1)
        linha_cores.addWidget(btn_cor2)

        btn_reset_cor = QPushButton("Voltar às cores OneWorld (roxo e verde)")

        def resetar_cores():
            cfg["cor"], cfg["cor2"] = ROXO, VERDE
            self.aplicar_tema()
            self.reconstruir_sidebar()
            self.reconstruir_pagina()

        btn_reset_cor.clicked.connect(resetar_cores)
        linha_cores.addWidget(btn_reset_cor)
        linha_cores.addStretch(1)
        l_vis.addLayout(linha_cores)

        form_vis = QFormLayout()
        cb_tema = QComboBox()
        temas = ["Claro", "Escuro", "Automático"]
        cb_tema.addItems(temas)
        cb_tema.setCurrentIndex(temas.index(cfg["tema"]) if cfg["tema"] in temas else 0)

        cb_dens = QComboBox()
        densidades = ["Compacta", "Confortável", "Ampla"]
        cb_dens.addItems(densidades)
        cb_dens.setCurrentIndex(densidades.index(cfg["densidade"]) if cfg["densidade"] in densidades else 1)

        cb_txt = QComboBox()
        tamanhos = ["P", "M", "G"]
        cb_txt.addItems(tamanhos)
        cb_txt.setCurrentIndex(tamanhos.index(cfg["texto"]) if cfg["texto"] in tamanhos else 1)

        def aplicar_mudanca_visual():
            cfg["tema"] = cb_tema.currentText()
            cfg["densidade"] = cb_dens.currentText()
            cfg["texto"] = cb_txt.currentText()
            self.aplicar_tema()
            self.reconstruir_sidebar()
            self.reconstruir_pagina()

        cb_tema.currentTextChanged.connect(lambda _: aplicar_mudanca_visual())
        cb_dens.currentTextChanged.connect(lambda _: aplicar_mudanca_visual())
        cb_txt.currentTextChanged.connect(lambda _: aplicar_mudanca_visual())

        form_vis.addRow("Tema", cb_tema)
        form_vis.addRow("Densidade", cb_dens)
        form_vis.addRow("Tamanho do texto", cb_txt)
        l_vis.addLayout(form_vis)

        card_prev = QFrame()
        card_prev.setObjectName("OwCard")
        lay_prev = QHBoxLayout(card_prev)
        lay_prev.setContentsMargins(16, 12, 16, 12)
        lay_prev.setSpacing(10)
        lay_prev.addWidget(QLabel(f"<b>Prévia:</b>  {cfg['nome']}"))

        chip1 = QLabel("Confirmado")
        chip1.setStyleSheet(
            f"background:{STATUS_CORES['Confirmado'][0]}; color:{STATUS_CORES['Confirmado'][1]}; "
            "padding: 3px 10px; border-radius: 10px; font-weight: 600;"
        )
        chip2 = QLabel("Botão")
        chip2.setStyleSheet(
            f"background:{cfg['cor']}; color:#FFFFFF; padding: 3px 10px; border-radius: 10px; font-weight: 600;"
        )
        chip3 = QLabel("Apoio")
        chip3.setStyleSheet(
            f"background:{cfg['cor2']}; color:#1E2140; padding: 3px 10px; border-radius: 10px; font-weight: 600;"
        )
        lay_prev.addWidget(chip1)
        lay_prev.addWidget(chip2)
        lay_prev.addWidget(chip3)
        lay_prev.addStretch(1)
        l_vis.addWidget(card_prev)

        linha_logo = QHBoxLayout()
        btn_up_logo = QPushButton("Alterar logotipo (PNG, JPG ou SVG)...")

        def enviar_logo():
            cam, _ = QFileDialog.getOpenFileName(
                self, "Selecionar logotipo", "", "Imagens (*.png *.jpg *.jpeg *.svg)"
            )
            if cam:
                p = Path(cam)
                bk.salvar_logo(p.name, p.read_bytes())
                self.flash("Logotipo personalizado atualizado.")
                self.reconstruir_sidebar()
                self.reconstruir_pagina()

        btn_up_logo.clicked.connect(enviar_logo)
        linha_logo.addWidget(btn_up_logo)

        if bk.logo_personalizado():
            btn_rm_logo = QPushButton("Remover logotipo personalizado")

            def rm_logo():
                bk.remover_logo()
                self.flash("Logotipo personalizado removido.")
                self.reconstruir_sidebar()
                self.reconstruir_pagina()

            btn_rm_logo.clicked.connect(rm_logo)
            linha_logo.addWidget(btn_rm_logo)

        linha_logo.addStretch(1)
        l_vis.addLayout(linha_logo)
        l_vis.addStretch(1)
        abas.addTab(w_vis, "Personalização visual")

        # Aba 2: Eficiência
        w_efic = QWidget()
        l_efic = QVBoxLayout(w_efic)
        l_efic.setContentsMargins(16, 16, 16, 16)
        l_efic.setSpacing(12)

        form_ef = QFormLayout()
        pgs = PAGINAS[:-1]
        cb_pginic = QComboBox()
        for p_key in pgs:
            cb_pginic.addItem(rotulo_pagina(p_key, cfg), userData=p_key)
        if cfg["pagina_inicial"] in pgs:
            cb_pginic.setCurrentIndex(pgs.index(cfg["pagina_inicial"]))
        cb_pginic.currentIndexChanged.connect(
            lambda _: cfg.__setitem__("pagina_inicial", cb_pginic.currentData())
        )

        sp_linhas = QSpinBox()
        sp_linhas.setRange(5, 100)
        sp_linhas.setValue(int(cfg["linhas"]))
        sp_linhas.valueChanged.connect(lambda val: cfg.__setitem__("linhas", int(val)))

        form_ef.addRow("Página inicial", cb_pginic)
        form_ef.addRow("Linhas por página", sp_linhas)
        l_efic.addLayout(form_ef)

        chk_auto = QCheckBox("Atualização automática do Dashboard (30 s)")
        chk_auto.setChecked(bool(cfg.get("auto_refresh", False)))
        chk_auto.toggled.connect(lambda val: (cfg.__setitem__("auto_refresh", val), self.aplicar_tema()))

        chk_filt = QCheckBox("Lembrar filtros ao trocar de página")
        chk_filt.setChecked(bool(cfg.get("lembrar_filtros", True)))
        chk_filt.toggled.connect(lambda val: cfg.__setitem__("lembrar_filtros", val))

        chk_lemb = QCheckBox("Lembretes de prazos/operações nos próximos 7 dias")
        chk_lemb.setChecked(bool(cfg.get("lembretes", True)))
        chk_lemb.toggled.connect(lambda val: cfg.__setitem__("lembretes", val))

        l_efic.addWidget(chk_auto)
        l_efic.addWidget(chk_filt)
        l_efic.addWidget(chk_lemb)

        cap_at = QLabel("Atalhos de teclado (N, /, D) estão planejados e ainda não funcionam nesta versão.")
        cap_at.setObjectName("Caption")
        l_efic.addWidget(cap_at)
        l_efic.addStretch(1)
        abas.addTab(w_efic, "Eficiência")

        # Aba 3: Dados & integrações
        w_dds = QWidget()
        l_dds = QVBoxLayout(w_dds)
        l_dds.setContentsMargins(16, 16, 16, 16)
        l_dds.setSpacing(12)

        form_dd = QFormLayout()
        idiomas = ["Português", "English", "Español"]
        cb_id = QComboBox()
        cb_id.addItems(idiomas)
        if cfg["idioma"] in idiomas:
            cb_id.setCurrentIndex(idiomas.index(cfg["idioma"]))
        cb_id.currentTextChanged.connect(lambda txt: cfg.__setitem__("idioma", txt))

        moedas = ["BRL", "USD", "EUR"]
        cb_mo = QComboBox()
        cb_mo.addItems(moedas)
        if cfg["moeda"] in moedas:
            cb_mo.setCurrentIndex(moedas.index(cfg["moeda"]))
        cb_mo.currentTextChanged.connect(lambda txt: cfg.__setitem__("moeda", txt))

        form_dd.addRow("Idioma (formato de números)", cb_id)
        form_dd.addRow("Moeda (símbolo; não converte valores)", cb_mo)
        l_dds.addLayout(form_dd)
        l_dds.addWidget(QLabel("Integrações externas (pagamentos, calendário, API): fora do escopo confirmado do MVP."))
        l_dds.addWidget(QLabel("Exportação: CSV por tabela e Markdown na tela Orientação IA."))
        l_dds.addWidget(QLabel("Backup completo (exportar/importar JSON): aba Segurança."))
        l_dds.addStretch(1)
        abas.addTab(w_dds, "Dados && integrações")

        # Aba 4: Segurança
        w_seg = QWidget()
        l_seg = QVBoxLayout(w_seg)
        l_seg.setContentsMargins(16, 16, 16, 16)
        l_seg.setSpacing(12)

        l_seg.addWidget(QLabel("Operação local, sem login próprio (conforme escopo do MVP)."))
        btn_bkp = QPushButton("Fazer backup agora")
        btn_bkp.setObjectName("PrimaryBtn")
        btn_bkp.setCursor(Qt.CursorShape.PointingHandCursor)

        def criar_bkp():
            dest = db.fazer_backup()
            self.aviso(f"Backup criado: {dest.name}")
            self.flash(f"Backup salvo em: {dest}")
            self.reconstruir_pagina()

        btn_bkp.clicked.connect(criar_bkp)
        l_seg.addWidget(btn_bkp, alignment=Qt.AlignmentFlag.AlignLeft)

        cap_bkp = QLabel(
            f"Cópia rápida do banco (.db): {db.contar_backups()} arquivo(s) na pasta {BACKUP_DIR}. "
            "Para restaurar ou complementar dados, use o backup completo abaixo."
        )
        cap_bkp.setObjectName("Caption")
        cap_bkp.setWordWrap(True)
        l_seg.addWidget(cap_bkp)

        l_seg.addWidget(Divider())
        l_seg.addWidget(self._subtitulo("Backup completo (arquivo JSON)"))
        cap_json = QLabel(
            f"Inclui {v['ent1_plural']}, {v['ent2_plural']}, anotações, relatórios de IA, histórico de "
            "arquivos importados e configurações. Não inclui o arquivo .env, chaves de API nem o banco "
            "público DFP. Ao importar, você escolhe entre substituir os dados atuais ou adicionar apenas "
            "o que falta."
        )
        cap_json.setObjectName("Caption")
        cap_json.setWordWrap(True)
        l_seg.addWidget(cap_json)

        linha_json = QHBoxLayout()
        btn_exp_json = QPushButton("Exportar backup...")
        btn_exp_json.setObjectName("PrimaryBtn")
        btn_exp_json.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_exp_json.clicked.connect(self._exportar_backup)
        btn_imp_json = QPushButton("Importar backup...")
        btn_imp_json.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_imp_json.clicked.connect(self._importar_backup)
        linha_json.addWidget(btn_exp_json)
        linha_json.addWidget(btn_imp_json)
        linha_json.addStretch(1)
        l_seg.addLayout(linha_json)

        l_seg.addWidget(Divider())
        l_seg.addWidget(AlertBox("Chaves de API (BYOK) devem ficar no arquivo .env, nunca no código.", "warning"))

        btn_testar_ia = QPushButton("Testar conexão com a IA")
        btn_testar_ia.setObjectName("PrimaryBtn")
        btn_testar_ia.setCursor(Qt.CursorShape.PointingHandCursor)

        def testar_ia():
            self.estado["ia_teste_resultado"] = ia.testar_conexao()
            self.reconstruir_pagina()

        btn_testar_ia.clicked.connect(testar_ia)
        l_seg.addWidget(btn_testar_ia, alignment=Qt.AlignmentFlag.AlignLeft)

        res_ia = self.estado.get("ia_teste_resultado")
        if res_ia:
            tipo_res = "success" if res_ia.get("ok") else "danger"
            l_seg.addWidget(AlertBox(res_ia.get("mensagem", ""), tipo_res))
            if res_ia.get("ok"):
                detalhes = (
                    f"Provedor: {res_ia.get('provedor')} | Modelo: {res_ia.get('modelo')} "
                    f"| Latência: {res_ia.get('latencia_ms')} ms"
                )
                if res_ia.get("tokens") is not None:
                    detalhes += f" | Tokens: {res_ia.get('tokens')}"
                lbl_det = QLabel(detalhes)
                lbl_det.setObjectName("Caption")
                l_seg.addWidget(lbl_det)
            icones = {"ok": "✅", "aviso": "⚠️", "erro": "❌"}
            for nivel, texto in res_ia.get("diagnostico", []):
                lbl_diag = QLabel(f"{icones.get(nivel, '•')} {texto}")
                lbl_diag.setWordWrap(True)
                l_seg.addWidget(lbl_diag)

        l_seg.addStretch(1)
        abas.addTab(w_seg, "Segurança")

        # Aba 5: Modelos & campos (Perfis de Negócio + Nomenclatura + Campos Extras)
        w_cp = QWidget()
        l_cp = QVBoxLayout(w_cp)
        l_cp.setContentsMargins(16, 16, 16, 16)
        l_cp.setSpacing(14)

        l_cp.addWidget(self._subtitulo("Modelo / Perfil do Empreendimento"))
        cap_mod = QLabel(
            "Escolha um modelo pronto para adaptar instantaneamente menus, indicadores, formulários e tabelas "
            "ao ramo da empresa, ou personalize cada rótulo logo abaixo."
        )
        cap_mod.setObjectName("Caption")
        cap_mod.setWordWrap(True)
        l_cp.addWidget(cap_mod)

        barra_perfil = QHBoxLayout()
        cb_perfil = QComboBox()
        lista_perfis = list(PERFIS_NEGOCIO.keys())
        cb_perfil.addItems(lista_perfis)
        perfil_atual = cfg.get("perfil_negocio", PERFIL_PADRAO)
        if perfil_atual in lista_perfis:
            cb_perfil.setCurrentIndex(lista_perfis.index(perfil_atual))

        def trocar_perfil(novo_p: str):
            cfg["perfil_negocio"] = novo_p
            cfg["rotulos_custom"] = {}
            db.cfg_gravar("config", cfg)
            self.aviso(f"Perfil de negócio alterado para: {novo_p}")
            self.flash(f"Perfil '{novo_p}' aplicado em todo o sistema.")
            self.reconstruir_sidebar()
            self.reconstruir_pagina()

        cb_perfil.currentTextChanged.connect(trocar_perfil)
        barra_perfil.addWidget(QLabel("<b>Perfil ativo:</b>"))
        barra_perfil.addWidget(cb_perfil, stretch=1)
        l_cp.addLayout(barra_perfil)

        # Editor de Nomenclatura Personalizada
        exp_nom = ExpanderWidget("Personalizar nomenclatura de menus e colunas deste perfil", aberto=False)
        grade_nom = QGridLayout()
        grade_nom.setHorizontalSpacing(16)
        grade_nom.setVerticalSpacing(8)

        ed_m1 = QLineEdit(v["menu_ent1"])
        ed_e1_p = QLineEdit(v["ent1_plural"])
        ed_m2 = QLineEdit(v["menu_ent2"])
        ed_e2_p = QLineEdit(v["ent2_plural"])

        grade_nom.addWidget(QLabel("<b>Menu Principal 1:</b>"), 0, 0)
        grade_nom.addWidget(ed_m1, 0, 1)
        grade_nom.addWidget(QLabel("<b>Título Tabela 1 (plural):</b>"), 0, 2)
        grade_nom.addWidget(ed_e1_p, 0, 3)

        grade_nom.addWidget(QLabel("<b>Menu Principal 2:</b>"), 1, 0)
        grade_nom.addWidget(ed_m2, 1, 1)
        grade_nom.addWidget(QLabel("<b>Título Tabela 2 (plural):</b>"), 1, 2)
        grade_nom.addWidget(ed_e2_p, 1, 3)

        campos_editaveis = [
            ("cliente", "Coluna Identificação (Tab. 1)"),
            ("local", "Coluna Categoria/Local (Tab. 1)"),
            ("convidados", "Coluna Quantidade/Volume (Tab. 1)"),
            ("valor", "Coluna Valor/Receita (Tab. 1)"),
            ("evento", "Coluna Vínculo (Tab. 2)"),
            ("nome", "Coluna Nome/Item (Tab. 2)"),
            ("mesa", "Coluna Grupo/Código (Tab. 2)"),
            ("acompanhantes", "Coluna Qtd. Extra (Tab. 2)"),
            ("contato", "Coluna Contato (Tab. 2)"),
            ("restricao", "Coluna Observações (Tab. 2)"),
        ]
        inputs_rotulos: dict[str, QLineEdit] = {}
        for idx_c, (ch_c, desc_c) in enumerate(campos_editaveis):
            lin = 2 + (idx_c // 2)
            col_base = (idx_c % 2) * 2
            grade_nom.addWidget(QLabel(desc_c), lin, col_base)
            ed_r = QLineEdit(v["rotulos"][ch_c])
            inputs_rotulos[ch_c] = ed_r
            grade_nom.addWidget(ed_r, lin, col_base + 1)

        exp_nom.corpo_layout.addLayout(grade_nom)

        barra_btns_nom = QHBoxLayout()
        btn_aplicar_nom = QPushButton("Aplicar nomenclatura personalizada")
        btn_aplicar_nom.setObjectName("PrimaryBtn")

        def salvar_nomenclatura():
            cfg["rotulos_custom"] = {
                "menu_ent1": ed_m1.text().strip() or v["menu_ent1"],
                "ent1_plural": ed_e1_p.text().strip() or v["ent1_plural"],
                "metric_ent1": ed_e1_p.text().strip() or v["metric_ent1"],
                "menu_ent2": ed_m2.text().strip() or v["menu_ent2"],
                "ent2_plural": ed_e2_p.text().strip() or v["ent2_plural"],
                "metric_qtd": inputs_rotulos["convidados"].text().strip() or v["metric_qtd"],
                "metric_valor": inputs_rotulos["valor"].text().strip() or v["metric_valor"],
                "rotulos": {ch: ed.text().strip() for ch, ed in inputs_rotulos.items() if ed.text().strip()},
            }
            db.cfg_gravar("config", cfg)
            self.flash("Nomenclatura personalizada aplicada e salva.")
            self.reconstruir_sidebar()
            self.reconstruir_pagina()

        btn_aplicar_nom.clicked.connect(salvar_nomenclatura)

        btn_limpar_nom = QPushButton("Restaurar nomes padrão deste perfil")

        def limpar_nomenclatura():
            cfg["rotulos_custom"] = {}
            db.cfg_gravar("config", cfg)
            self.flash("Nomes originais do perfil restaurados.")
            self.reconstruir_sidebar()
            self.reconstruir_pagina()

        btn_limpar_nom.clicked.connect(limpar_nomenclatura)
        barra_btns_nom.addWidget(btn_aplicar_nom)
        barra_btns_nom.addWidget(btn_limpar_nom)
        barra_btns_nom.addStretch(1)
        exp_nom.corpo_layout.addLayout(barra_btns_nom)
        l_cp.addWidget(exp_nom)

        l_cp.addWidget(Divider())
        l_cp.addWidget(self._subtitulo("Campos adicionais personalizados (Colunas Extras)"))

        barra_novo_cp = QHBoxLayout()
        ed_novo_cp = QLineEdit()
        ed_novo_cp.setPlaceholderText("Ex.: Fornecedor, CNPJ, Centro de Custo...")
        btn_add_cp = QPushButton("Adicionar campo")

        lbl_err_cp = QLabel()
        lbl_err_cp.setStyleSheet("color: #8F2412; font-weight: 600;")
        lbl_err_cp.setVisible(False)

        def adicionar_cp():
            novo = ed_novo_cp.text().strip()
            if not novo:
                return
            reservados = {bk.chave(x) for x in sum(CAMPOS.values(), [])}
            if novo in self.campos_personalizados or bk.chave(novo) in reservados:
                lbl_err_cp.setText("Esse nome já existe.")
                lbl_err_cp.setVisible(True)
                return
            self.campos_personalizados.append(novo)
            db.cfg_gravar("campos_personalizados", self.campos_personalizados)
            self.flash(f"Campo personalizado '{novo}' adicionado.")
            self.reconstruir_pagina()

        btn_add_cp.clicked.connect(adicionar_cp)
        barra_novo_cp.addWidget(ed_novo_cp, stretch=1)
        barra_novo_cp.addWidget(btn_add_cp)
        l_cp.addLayout(barra_novo_cp)
        l_cp.addWidget(lbl_err_cp)

        if not self.campos_personalizados:
            l_cp.addWidget(AlertBox("Nenhum campo extra adicionado.", "info"))
        else:
            for cp in list(self.campos_personalizados):
                linha_item = QHBoxLayout()
                linha_item.addWidget(QLabel(f"• {cp}"), stretch=4)
                btn_rm = QPushButton("Remover")
                btn_rm.clicked.connect(lambda _, c=cp: self._remover_campo_personalizado(c))
                linha_item.addWidget(btn_rm, stretch=1)
                l_cp.addLayout(linha_item)
            cap_cp = QLabel(
                f"Os campos aparecem nos formulários e tabelas de {v['ent1_plural']} e {v['ent2_plural']}. "
                "Os valores já gravados ficam guardados mesmo se o campo for removido."
            )
            cap_cp.setObjectName("Caption")
            cap_cp.setWordWrap(True)
            l_cp.addWidget(cap_cp)

        l_cp.addStretch(1)
        abas.addTab(w_cp, "Modelos && campos")
        abas.setCurrentIndex(self.estado.get("tab_config", 0))
        abas.currentChanged.connect(lambda idx: self.estado.__setitem__("tab_config", idx))

        self.lay_pagina.addWidget(abas)
        self.lay_pagina.addWidget(Divider())

        barra_acoes = QHBoxLayout()
        btn_salvar_cfg = QPushButton("Salvar alterações")
        btn_salvar_cfg.setObjectName("PrimaryBtn")
        btn_salvar_cfg.setCursor(Qt.CursorShape.PointingHandCursor)

        def salvar_config():
            db.cfg_gravar("config", self.cfg)
            self.aplicar_tema()
            self.reconstruir_sidebar()
            self.flash("Configurações salvas no banco.")
            self.reconstruir_pagina()

        btn_salvar_cfg.clicked.connect(salvar_config)

        btn_padroes = QPushButton("Restaurar padrões")
        btn_padroes.setCursor(Qt.CursorShape.PointingHandCursor)

        def restaurar_padroes():
            self.cfg.update(PADROES)
            self.cfg["rotulos_custom"] = {}
            db.cfg_gravar("config", self.cfg)
            self.aplicar_tema()
            self.reconstruir_sidebar()
            self.flash("Configurações restauradas para os padrões.")
            self.reconstruir_pagina()

        btn_padroes.clicked.connect(restaurar_padroes)
        barra_acoes.addWidget(btn_salvar_cfg)
        barra_acoes.addWidget(btn_padroes)
        barra_acoes.addStretch(1)
        self.lay_pagina.addLayout(barra_acoes)

    def _remover_campo_personalizado(self, cp: str):
        if cp in self.campos_personalizados:
            self.campos_personalizados.remove(cp)
            db.cfg_gravar("campos_personalizados", self.campos_personalizados)
            self.reconstruir_pagina()

    # ── Backup completo (JSON): exportar e importar ──
    # Todos os diálogos modais passam por _escolher_modo_importacao, _confirmar e _mostrar_mensagem,
    # o que permite testar os fluxos (inclusive cancelamentos) sem abrir janelas.
    def _nomes_tabelas_backup(self) -> dict[str, str]:
        v = self.vocab()
        return {**bkp.NOMES_TABELAS, "eventos": v["ent1_plural"], "convidados": v["ent2_plural"]}

    def _mostrar_mensagem(self, tipo: str, titulo: str, texto: str):
        icones = {
            "info": QMessageBox.Icon.Information,
            "aviso": QMessageBox.Icon.Warning,
            "erro": QMessageBox.Icon.Critical,
        }
        caixa = QMessageBox(icones.get(tipo, QMessageBox.Icon.Information), titulo, texto,
                            QMessageBox.StandardButton.Ok, self)
        caixa.setTextFormat(Qt.TextFormat.RichText)
        caixa.exec()

    def _confirmar(self, titulo: str, texto: str, rotulo_ok: str) -> bool:
        caixa = QMessageBox(QMessageBox.Icon.Warning, titulo, texto, parent=self)
        caixa.setTextFormat(Qt.TextFormat.RichText)
        btn_ok = caixa.addButton(rotulo_ok, QMessageBox.ButtonRole.AcceptRole)
        btn_cancelar = caixa.addButton("Cancelar", QMessageBox.ButtonRole.RejectRole)
        caixa.setDefaultButton(btn_cancelar)
        caixa.setEscapeButton(btn_cancelar)
        caixa.exec()
        return caixa.clickedButton() is btn_ok

    def _escolher_modo_importacao(self, texto: str) -> str | None:
        """Devolve 'substituir', 'mesclar' ou None (cancelado)."""
        caixa = QMessageBox(QMessageBox.Icon.Question, "Importar backup", texto, parent=self)
        caixa.setTextFormat(Qt.TextFormat.RichText)
        btn_sub = caixa.addButton("Substituir dados atuais", QMessageBox.ButtonRole.ActionRole)
        btn_mes = caixa.addButton("Adicionar apenas o que falta", QMessageBox.ButtonRole.ActionRole)
        btn_cancelar = caixa.addButton("Cancelar", QMessageBox.ButtonRole.RejectRole)
        caixa.setDefaultButton(btn_cancelar)
        caixa.setEscapeButton(btn_cancelar)
        caixa.exec()
        clicado = caixa.clickedButton()
        if clicado is btn_sub:
            return "substituir"
        if clicado is btn_mes:
            return "mesclar"
        return None

    @staticmethod
    def _tabela_html(cabecalho: list[str], linhas: list[list]) -> str:
        th = "".join(f"<th align='left' style='padding:2px 10px 2px 0'>{html.escape(str(c))}</th>"
                     for c in cabecalho)
        corpo = "".join(
            "<tr>" + "".join(f"<td style='padding:2px 10px 2px 0'>{html.escape(str(c))}</td>" for c in lin)
            + "</tr>" for lin in linhas
        )
        return f"<table><tr>{th}</tr>{corpo}</table>"

    def _exportar_backup(self):
        nome = f"oneworld_backup_{datetime.now():%Y%m%d_%H%M%S}.json"
        pasta = BACKUP_DIR if BACKUP_DIR.is_dir() else Path.home()
        caminho, _ = QFileDialog.getSaveFileName(
            self, "Exportar backup do OneWorld", str(pasta / nome), "Backup do OneWorld (*.json)"
        )
        if not caminho:
            return
        destino = Path(caminho)
        if destino.suffix.lower() != ".json":
            destino = destino.with_name(destino.name + ".json")
        try:
            res = bkp.exportar(destino)
        except bkp.BackupErro as e:
            self._mostrar_mensagem("erro", "Falha ao exportar backup", html.escape(str(e)))
            return
        except Exception as e:  # noqa: BLE001 — a exportação só lê o banco; nada foi alterado
            self._mostrar_mensagem("erro", "Falha ao exportar backup",
                                   html.escape(f"Erro inesperado ao exportar: {e}"))
            return
        total = sum(n for t, n in res.contagens.items() if t != "config")
        self.aviso(f"Backup exportado: {res.caminho.name}")
        msg = f"Backup exportado ({total} registro(s)) em: {res.caminho}"
        if res.segredos_removidos:
            msg += f" — {res.segredos_removidos} item(ns) com aparência de segredo foram omitidos."
        self.flash(msg)
        self.reconstruir_pagina()

    def _importar_backup(self):
        try:
            self._fluxo_importar_backup()
        except Exception as e:  # noqa: BLE001 — erro imprevisto não pode derrubar o app; gravações são transacionais
            self._mostrar_mensagem(
                "erro", "Erro inesperado na importação",
                html.escape(f"{e}") + "<br><br>Qualquer gravação em andamento foi desfeita.",
            )

    def _fluxo_importar_backup(self):
        pasta = BACKUP_DIR if BACKUP_DIR.is_dir() else Path.home()
        caminho, _ = QFileDialog.getOpenFileName(
            self, "Importar backup do OneWorld", str(pasta), "Backup do OneWorld (*.json)"
        )
        if not caminho:
            return
        try:
            backup = bkp.ler_backup(caminho)
        except bkp.BackupErro as e:
            self._mostrar_mensagem("aviso", "Arquivo de backup inválido",
                                   html.escape(str(e)) + "<br><br>Nenhum dado foi alterado.")
            return

        nomes = self._nomes_tabelas_backup()
        try:
            gerado = datetime.fromisoformat(backup.gerado_em).strftime("%d/%m/%Y %H:%M")
        except ValueError:
            gerado = backup.gerado_em
        resumo = (
            f"<b>Arquivo:</b> {html.escape(Path(caminho).name)}<br>"
            f"<b>Gerado em:</b> {html.escape(gerado)}<br><br>"
            + self._tabela_html(["Conteúdo do backup", "Registros"],
                                [[nomes[t], n] for t, n in backup.contagens.items()])
            + f"<br>Campos personalizados no backup: {len(backup.campos_personalizados)}<br><br>"
            "<b>Substituir dados atuais</b>: apaga todos os dados e configurações atuais e coloca os do "
            "backup (antes, salva uma cópia de segurança do banco).<br>"
            "<b>Adicionar apenas o que falta</b>: mantém tudo o que existe e acrescenta só os registros do "
            "backup que ainda não estão no sistema."
        )
        modo = self._escolher_modo_importacao(resumo)
        if modo == "substituir":
            self._importar_substituindo(backup, nomes)
        elif modo == "mesclar":
            self._importar_mesclando(backup, nomes)

    def _importar_substituindo(self, backup: bkp.Backup, nomes: dict[str, str]):
        try:
            atuais = bkp.contagens_atuais()
        except bkp.BackupErro as e:
            self._mostrar_mensagem("erro", "Não foi possível restaurar", html.escape(str(e)))
            return
        texto = (
            "<b>Todos os dados atuais serão apagados</b> e substituídos pelos do backup:<br><br>"
            + self._tabela_html(["Tabela", "Atual (será apagado)", "Backup (será restaurado)"],
                                [[nomes[t], atuais[t], backup.contagens[t]] for t in bkp.TABELAS])
            + "<br>As configurações também serão substituídas; alterações ainda não salvas nesta tela "
            "serão descartadas.<br>Antes de alterar qualquer dado, uma cópia de segurança do banco atual "
            f"será salva em {html.escape(str(BACKUP_DIR))}.<br><br>Deseja continuar?"
        )
        if not self._confirmar("Substituir dados atuais", texto, "Sim, substituir"):
            return
        try:
            res = bkp.substituir(backup)
        except bkp.BackupErro as e:
            self._mostrar_mensagem("erro", "Restauração não concluída", html.escape(str(e)))
            return
        self._recarregar_apos_importacao(substituiu=True)
        total = sum(n for t, n in res.adicionados.items() if t != "config")
        self.aviso(f"Backup restaurado: {total} registro(s)")
        self._mostrar_mensagem(
            "info", "Backup restaurado",
            f"Dados restaurados a partir do backup ({total} registro(s)).<br>"
            f"Cópia de segurança do banco anterior: {html.escape(str(res.copia_seguranca))}",
        )

    def _importar_mesclando(self, backup: bkp.Backup, nomes: dict[str, str]):
        try:
            plano = bkp.planejar_mesclagem(backup)
        except bkp.BackupErro as e:
            self._mostrar_mensagem("erro", "Não foi possível comparar os dados", html.escape(str(e)))
            return

        if plano.conflitos:
            itens = "".join(f"<li><b>{html.escape(c.nome)}</b>: {html.escape(c.motivo)}</li>"
                            for c in plano.conflitos)
            texto_conf = (
                "Alguns campos personalizados do backup são incompatíveis com os atuais e "
                f"<b>não serão adicionados</b> à lista de campos:<ul>{itens}</ul>"
                "Os valores desses campos nos registros importados serão gravados exatamente como estão no "
                "backup (nos dados extras de cada registro), mas não aparecerão como coluna.<br><br>"
                "Deseja continuar sem adicionar esses campos?"
            )
            if not self._confirmar("Campos personalizados em conflito", texto_conf,
                                   "Continuar sem esses campos"):
                return

        if not plano.tem_algo_a_fazer:
            self._mostrar_mensagem("info", "Nada a adicionar",
                                   "Todos os registros e campos do backup já existem no sistema. "
                                   "Nenhum dado foi alterado.")
            return

        linhas = [[nomes[t], len(backup.tabelas[t]), plano.contagem_adicionar[t], plano.ignorados[t]]
                  for t in bkp.TABELAS_DADOS]
        campos_txt = (", ".join(html.escape(c) for c in plano.campos_novos) if plano.campos_novos
                      else "nenhum")
        texto = (
            self._tabela_html(["Tabela", "No backup", "Serão adicionados", "Já existem (ignorados)"], linhas)
            + f"<br>Campos personalizados que serão adicionados: {campos_txt}<br><br>"
            "Os registros são comparados pelo conteúdo completo (sem o ID). Um registro com qualquer "
            "diferença — inclusive espaços, maiúsculas ou campos extras — é considerado novo. "
            "Este modo <b>não atualiza nem remove</b> registros existentes, e as configurações atuais são "
            "mantidas.<br><br>Deseja adicionar os registros que faltam?"
        )
        if not self._confirmar("Adicionar apenas o que falta", texto, "Adicionar"):
            return
        try:
            res = bkp.aplicar_mesclagem(backup)
        except bkp.BackupErro as e:
            self._mostrar_mensagem("erro", "Importação não concluída", html.escape(str(e)))
            return
        self._recarregar_apos_importacao(substituiu=False)
        total_add = sum(res.adicionados.values())
        total_ign = sum(res.ignorados.values())
        self.aviso(f"Backup importado: {total_add} registro(s) adicionado(s)")
        linhas_res = [[nomes[t], res.adicionados[t], res.ignorados[t]] for t in bkp.TABELAS_DADOS]
        extra = ""
        if res.campos_adicionados:
            extra += "<br>Campos adicionados: " + ", ".join(html.escape(c) for c in res.campos_adicionados)
        if res.conflitos:
            extra += "<br>Campos não adicionados (conflito): " + ", ".join(
                html.escape(c.nome) for c in res.conflitos)
        self._mostrar_mensagem(
            "info", "Importação concluída",
            f"{total_add} registro(s) adicionado(s) e {total_ign} ignorado(s) por já existirem.<br><br>"
            + self._tabela_html(["Tabela", "Adicionados", "Ignorados"], linhas_res) + extra,
        )

    def _recarregar_apos_importacao(self, substituiu: bool):
        """Relê do banco o que a tela guarda em memória, para que o estado antigo não sobrescreva o novo."""
        self.campos_personalizados = db.cfg_ler("campos_personalizados", [])
        if substituiu:
            self.cfg = self._ler_configuracoes()
            aba = self.estado.get("tab_config")
            self.estado = {} if aba is None else {"tab_config": aba}
            self.aplicar_tema()
        self.reconstruir_sidebar()
        self.reconstruir_pagina()

    # ── Planilha padrão e IA externa (fluxo manual, sem chamadas de IA) ──
    # Diálogos modais passam por _confirmar, _mostrar_mensagem e _revisar_importacao_planilha (testáveis).
    def _estado_planilha(self, tipo: str) -> dict:
        """Escolhas da aba (tabelas, período, dados pessoais). Cada aba — edição ou análise — tem as suas."""
        return self.estado.setdefault(f"planilha_{tipo}", {
            "tabelas": ["eventos", "convidados"], "periodo": False, "ini": None, "fim": None, "pessoais": False,
        })

    def _opcoes_planilha(self, tipo: str, vazio: bool = False) -> pp.OpcoesExportacao:
        st = self._estado_planilha(tipo)
        ini = fim = None
        if st["periodo"] and not vazio:
            ini = st["ini"] or date.today().replace(day=1)
            fim = st["fim"] or date.today()
        return pp.OpcoesExportacao(
            tipo=tipo,
            tabelas=tuple(t for t in pp.TABELAS if t in st["tabelas"]),
            data_inicio=ini, data_fim=fim,
            incluir_dados_pessoais=bool(st["pessoais"]) and tipo == pp.TIPO_ANALISE, vazio=vazio,
        )

    def _nomes_tabelas_planilha(self) -> dict[str, str]:
        v = self.vocab()
        return {"eventos": v["ent1_plural"], "convidados": v["ent2_plural"], "anotacoes": "Anotações"}

    def _passo(self, lay: QVBoxLayout, numero: int, titulo: str, texto: str = "") -> QVBoxLayout:
        """Cartão numerado de um passo; devolve o layout interno para receber botões e opções."""
        card = QFrame()
        card.setObjectName("OwCard")
        corpo = QVBoxLayout(card)
        corpo.setContentsMargins(18, 14, 18, 16)
        corpo.setSpacing(10)
        topo = QHBoxLayout()
        topo.setSpacing(12)
        selo = QLabel(str(numero))
        selo.setFixedSize(30, 30)
        selo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        selo.setStyleSheet(f"background:{self.cfg['cor']}; color:#FFFFFF; border-radius:15px; font-weight:800;")
        lbl = QLabel(titulo)
        lbl.setObjectName("SectionTitle")
        topo.addWidget(selo)
        topo.addWidget(lbl, stretch=1)
        corpo.addLayout(topo)
        if texto:
            t = QLabel(texto)
            t.setObjectName("PassoTexto")
            t.setWordWrap(True)
            t.setTextFormat(Qt.TextFormat.RichText)
            corpo.addWidget(t)
        lay.addWidget(card)
        return corpo

    @staticmethod
    def _legenda(texto: str) -> QLabel:
        lbl = QLabel(texto)
        lbl.setObjectName("Caption")
        lbl.setWordWrap(True)
        return lbl

    def _linha_botoes(self, lay: QVBoxLayout, botoes: list[tuple[str, object, bool]]):
        linha = QHBoxLayout()
        linha.setSpacing(10)
        for rotulo, acao, primario in botoes:
            b = QPushButton(rotulo)
            if primario:
                b.setObjectName("PrimaryBtn")
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.clicked.connect(lambda *_, a=acao: a())
            linha.addWidget(b)
        linha.addStretch(1)
        lay.addLayout(linha)

    def _opcoes_dados_planilha(self, lay: QVBoxLayout, tipo: str):
        """Tabelas e período (cada aba guarda a própria escolha)."""
        st = self._estado_planilha(tipo)
        nomes = self._nomes_tabelas_planilha()
        form = QFormLayout()
        form.setHorizontalSpacing(16)
        form.setVerticalSpacing(10)

        w_tab = QWidget()
        h_tab = QHBoxLayout(w_tab)
        h_tab.setContentsMargins(0, 0, 0, 0)
        h_tab.setSpacing(18)
        for tab in pp.TABELAS:
            chk = QCheckBox(nomes[tab].replace("&", "&&"))
            chk.setChecked(tab in st["tabelas"])

            def alternar(marcado, t=tab):
                if marcado and t not in st["tabelas"]:
                    st["tabelas"].append(t)
                elif not marcado and t in st["tabelas"]:
                    st["tabelas"].remove(t)

            chk.toggled.connect(alternar)
            h_tab.addWidget(chk)
        h_tab.addStretch(1)
        form.addRow("Tabelas:", w_tab)

        w_per = QWidget()
        h_per = QHBoxLayout(w_per)
        h_per.setContentsMargins(0, 0, 0, 0)
        h_per.setSpacing(10)
        chk_per = QCheckBox("Somente de")
        chk_per.setChecked(bool(st["periodo"]))
        hoje = date.today()
        ini = st["ini"] or hoje.replace(day=1)
        fim = st["fim"] or hoje
        de_ini = QDateEdit(QDate(ini.year, ini.month, ini.day))
        de_fim = QDateEdit(QDate(fim.year, fim.month, fim.day))
        pal = paleta_atual(self.cfg)
        for de in (de_ini, de_fim):
            de.setCalendarPopup(True)
            de.setDisplayFormat("dd/MM/yyyy")
            de.setMinimumWidth(150)
            de.setEnabled(bool(st["periodo"]))
            # fica visivelmente apagado enquanto o período não está marcado
            de.setStyleSheet(f"QDateEdit:disabled {{ color: {pal['muted']}; background-color: {pal['bg']}; }}")

        def alternar_periodo(marcado):
            st["periodo"] = marcado
            de_ini.setEnabled(marcado)
            de_fim.setEnabled(marcado)

        chk_per.toggled.connect(alternar_periodo)
        de_ini.dateChanged.connect(lambda q: st.__setitem__("ini", date(q.year(), q.month(), q.day())))
        de_fim.dateChanged.connect(lambda q: st.__setitem__("fim", date(q.year(), q.month(), q.day())))
        h_per.addWidget(chk_per)
        h_per.addWidget(de_ini)
        h_per.addWidget(QLabel("até"))
        h_per.addWidget(de_fim)
        h_per.addStretch(1)
        form.addRow("Período:", w_per)
        lay.addLayout(form)
        lay.addWidget(self._legenda(
            f"Sem marcar o período, vão todos os registros. {nomes['convidados']} não têm data própria: entram "
            f"quando a operação vinculada está no período. Se houver operações com o mesmo nome dentro e fora "
            "do período, esses cadastros ficam de fora e o arquivo informa quantos."
        ))

    def _aba_ia_atualizar(self, lay: QVBoxLayout):
        lay.addWidget(self._legenda(
            "Use quando quiser que uma IA externa (ChatGPT, Gemini, Claude...) inclua ou atualize registros por "
            "você. O OneWorld não envia nada sozinho: você leva a planilha e o prompt ao chat e depois importa o "
            "arquivo que a IA devolver."
        ))
        lay.addWidget(AlertBox(
            "Esta planilha leva todos os campos, inclusive nomes, contatos e observações. Ao enviá-la a uma IA "
            "externa, esses dados saem do seu computador.", "warning"))

        p1 = self._passo(lay, 1, "Escolha o que vai na planilha")
        self._opcoes_dados_planilha(p1, pp.TIPO_EDICAO)

        p2 = self._passo(lay, 2, "Baixe a planilha para edição",
                         "Gera o arquivo <b>.xlsx</b> com seus registros e os controles que permitem importar de "
                         "volta com segurança.")
        self._linha_botoes(p2, [
            ("Exportar planilha para edição...", lambda: self._exportar_planilha_padrao(pp.TIPO_EDICAO), True),
            ("Baixar modelo vazio...", self._exportar_modelo_vazio, False),
        ])
        p2.addWidget(self._legenda("Ainda não tem registros? Use o modelo vazio: mesma estrutura, sem dados."))

        p3 = self._passo(lay, 3, "Copie o prompt de preenchimento",
                         "O prompt explica à IA como preencher a planilha sem quebrar a estrutura e pede o arquivo "
                         "<b>.xlsx para download</b>.")
        self._linha_botoes(p3, [("Copiar prompt de preenchimento", self._copiar_prompt_preenchimento, False)])

        self._passo(lay, 4, "Envie à IA e baixe o arquivo devolvido",
                    "Em um chat de IA que aceite anexos e gere arquivos: <b>anexe a planilha</b>, <b>cole o "
                    "prompt</b> e troque o texto entre &lt;novos_dados&gt; pelos dados novos ou pelas alterações "
                    "que você quer. Depois, <b>baixe o .xlsx</b> que a IA devolver. Se ela mostrar só uma tabela "
                    "no chat, peça o arquivo para download.")

        p5 = self._passo(lay, 5, "Importe o arquivo devolvido",
                         "Você verá uma prévia com o que será incluído, alterado ou limpo. Nada é gravado sem a sua "
                         "confirmação, e o sistema faz uma cópia de segurança antes.")
        self._linha_botoes(p5, [("Importar planilha preenchida...", self._importar_planilha_padrao, True)])

    def _aba_ia_analise(self, lay: QVBoxLayout):
        lay.addWidget(self._legenda(
            "Use quando quiser que uma IA externa analise seus dados e sugira caminhos para o negócio. Este arquivo "
            "é só para leitura: não pode ser importado de volta."
        ))
        st = self._estado_planilha(pp.TIPO_ANALISE)

        p1 = self._passo(lay, 1, "Escolha o que vai na planilha")
        self._opcoes_dados_planilha(p1, pp.TIPO_ANALISE)
        chk_pes = QCheckBox("Incluir nomes, contatos, observações e campos personalizados")
        chk_pes.setChecked(bool(st["pessoais"]))
        chk_pes.toggled.connect(lambda m: st.__setitem__("pessoais", m))
        p1.addWidget(chk_pes)
        p1.addWidget(self._legenda(
            "Desmarcado, o arquivo sai sem essas colunas. Ainda assim, textos livres (como o nome da operação) podem "
            "conter informações pessoais: revise antes de enviar."
        ))

        p2 = self._passo(lay, 2, "Baixe a planilha para análise",
                         "Gera o arquivo <b>.xlsx</b> com um resumo por mês e os dados escolhidos.")
        self._linha_botoes(p2, [
            ("Exportar planilha para análise...", lambda: self._exportar_planilha_padrao(pp.TIPO_ANALISE), True),
        ])

        p3 = self._passo(lay, 3, "Copie o prompt e envie à IA",
                         "Anexe a planilha no chat e cole o prompt. Ele pede sugestões baseadas nos dados, lembra que "
                         "o valor é <b>previsto</b> e proíbe inventar números. A IA sugere; quem decide é você.")
        self._linha_botoes(p3, [("Copiar prompt de análise", self._copiar_prompt_analise, False)])

    def _abas_selecionadas(self, tipo: str) -> list[str]:
        return [pp.ABA_DA_TABELA[t] for t in pp.TABELAS if t in self._estado_planilha(tipo)["tabelas"]]

    def _salvar_xlsx_dialogo(self, titulo: str, nome: str) -> Path | None:
        pasta = BACKUP_DIR if BACKUP_DIR.is_dir() else Path.home()
        caminho, _ = QFileDialog.getSaveFileName(self, titulo, str(pasta / nome), "Planilha Excel (*.xlsx)")
        if not caminho:
            return None
        destino = Path(caminho)
        return destino if destino.suffix.lower() == ".xlsx" else destino.with_name(destino.name + ".xlsx")

    def _exportar_planilha_padrao(self, tipo: str, vazio: bool = False):
        opcoes = self._opcoes_planilha(tipo, vazio=vazio)
        nomes = self._nomes_tabelas_planilha()
        if not opcoes.tabelas:
            self._mostrar_mensagem("aviso", "Planilha padrão", "Marque ao menos uma tabela para exportar.")
            return
        try:
            if opcoes.tipo == pp.TIPO_EDICAO and not vazio:
                contagens, excluidos = pp.contar_para_exportacao(opcoes)
                linhas = [[nomes[t], n] for t, n in contagens.items()]
                fora = "".join(f"<li>{html.escape(k)}: {n}</li>" for k, n in excluidos.items())
                texto = (
                    "O arquivo <b>para edição e reimportação</b> terá todos os campos das tabelas escolhidas, "
                    "<b>inclusive nomes, contatos, observações e campos personalizados</b>:<br><br>"
                    + self._tabela_html(["Tabela", "Registros"], linhas)
                    + (f"<br>Ficarão fora do arquivo:<ul>{fora}</ul>" if fora else "<br>")
                    + "Se você enviar este arquivo a uma IA externa, esses dados sairão do seu computador.<br><br>"
                    "Confirma as tabelas escolhidas?"
                )
                if not self._confirmar("Exportar planilha para edição", texto, "Exportar"):
                    return
            sufixo = "modelo_vazio" if vazio else ("edicao" if opcoes.tipo == pp.TIPO_EDICAO else "analise")
            destino = self._salvar_xlsx_dialogo("Salvar planilha padrão",
                                                f"oneworld_planilha_{sufixo}_{datetime.now():%Y%m%d_%H%M}.xlsx")
            if destino is None:
                return
            res = pp.exportar_planilha(destino, opcoes)
        except pp.PlanilhaErro as e:
            self._mostrar_mensagem("erro", "Falha ao exportar a planilha", html.escape(str(e)))
            return
        except Exception as e:  # noqa: BLE001 — exportação não altera dados; mostra o erro sem derrubar o app
            self._mostrar_mensagem("erro", "Falha ao exportar a planilha", html.escape(f"Erro inesperado: {e}"))
            return
        resumo = ", ".join(f"{nomes[t]}: {n}" for t, n in res.contagens.items())
        tipo_txt = ("modelo vazio" if vazio else
                    "para edição e reimportação" if res.tipo == pp.TIPO_EDICAO else "somente para análise")
        self.aviso(f"Planilha padrão exportada ({tipo_txt}): {res.caminho.name}")
        msg = f"Planilha {tipo_txt} salva em: {res.caminho}"
        if not vazio:
            msg += f" ({resumo})"
        if res.excluidos:
            msg += " — fora do arquivo: " + "; ".join(f"{k}: {n}" for k, n in res.excluidos.items())
        self.flash(msg)
        self.reconstruir_pagina()

    def _exportar_modelo_vazio(self):
        self._exportar_planilha_padrao(pp.TIPO_EDICAO, vazio=True)

    def _copiar_texto(self, texto: str, aviso: str):
        QApplication.clipboard().setText(texto)
        self.flash(aviso)
        self.reconstruir_pagina()

    def _copiar_prompt_analise(self):
        abas = self._abas_selecionadas(pp.TIPO_ANALISE)
        if not abas:
            self._mostrar_mensagem("aviso", "Planilha padrão", "Marque ao menos uma tabela no passo 1.")
            return
        self._copiar_texto(pp.prompt_analise(abas),
                           f"Prompt de análise copiado (abas: {', '.join(abas)}). Cole no chat junto com a planilha.")

    def _copiar_prompt_preenchimento(self):
        abas = self._abas_selecionadas(pp.TIPO_EDICAO)
        if not abas:
            self._mostrar_mensagem("aviso", "Planilha padrão", "Marque ao menos uma tabela no passo 1.")
            return
        self._copiar_texto(pp.prompt_preenchimento(abas, self.campos_personalizados),
                           f"Prompt de preenchimento copiado (abas: {', '.join(abas)}). Cole no chat junto com a "
                           "planilha exportada para edição (ou o modelo vazio).")

    def _importar_planilha_padrao(self):
        try:
            self._fluxo_importar_planilha()
        except Exception as e:  # noqa: BLE001 — erro imprevisto não pode derrubar o app; gravação é transacional
            self._mostrar_mensagem("erro", "Erro inesperado na importação",
                                   html.escape(f"{e}") + "<br><br>Qualquer gravação em andamento foi desfeita.")

    def _fluxo_importar_planilha(self):
        pasta = BACKUP_DIR if BACKUP_DIR.is_dir() else Path.home()
        caminho, _ = QFileDialog.getOpenFileName(self, "Importar planilha padrão", str(pasta),
                                                 "Planilha padrão do OneWorld (*.xlsx)")
        if not caminho:
            return
        try:
            arquivo = pp.ler_planilha_padrao(caminho)
        except pp.PlanilhaInvalida as e:
            itens = "".join(f"<li>{html.escape(p)}</li>" for p in e.problemas[:30])
            extra = f"<br>(+{len(e.problemas) - 30} problema(s))" if len(e.problemas) > 30 else ""
            self._mostrar_mensagem("aviso", "Planilha não pode ser importada",
                                   f"<ul>{itens}</ul>{extra}<br>Nenhum dado foi alterado.")
            return
        try:
            plano = pp.planejar_importacao(arquivo)
        except pp.PlanilhaErro as e:
            self._mostrar_mensagem("erro", "Não foi possível preparar a prévia", html.escape(str(e)))
            return
        if not self._revisar_importacao_planilha(plano) or not plano.pode_confirmar:
            return
        try:
            res = pp.aplicar_importacao(arquivo, plano)
        except pp.PlanoDesatualizado as e:
            self._mostrar_mensagem("aviso", "Revise a importação novamente", html.escape(str(e)))
            return
        except pp.ImportacaoErro as e:
            self._mostrar_mensagem("erro", "Importação não concluída", html.escape(str(e)))
            return
        nomes = self._nomes_tabelas_planilha()
        linhas = [[nomes[t], res.inclusoes.get(t, 0), res.alteracoes.get(t, 0)] for t in pp.TABELAS
                  if res.inclusoes.get(t) or res.alteracoes.get(t)]
        total = sum(res.inclusoes.values()) + sum(res.alteracoes.values())
        self.aviso(f"Planilha padrão importada: {total} registro(s) gravado(s)")
        self.reconstruir_pagina()
        self._mostrar_mensagem(
            "info", "Planilha importada",
            self._tabela_html(["Tabela", "Incluídos", "Alterados"], linhas)
            + (f"<br>Vínculos de cadastros atualizados: {res.propagacoes}" if res.propagacoes else "")
            + (f"<br>Linhas duplicadas ignoradas: {res.duplicados}" if res.duplicados else "")
            + f"<br><br>Cópia de segurança do banco anterior: {html.escape(str(res.copia_seguranca))}",
        )

    def _revisar_importacao_planilha(self, plano: pp.Plano) -> bool:
        return self._criar_dialogo_previa(plano).exec() == QDialog.DialogCode.Accepted

    def _criar_dialogo_previa(self, plano: pp.Plano) -> QDialog:
        rot = self.vocab()["rotulos"]
        nomes = self._nomes_tabelas_planilha()

        def nome_col(col):
            if col is None:
                return ""
            if col.startswith(pp.PREFIXO_CAMPO):
                return col[len(pp.PREFIXO_CAMPO):]
            return rot.get(col, col)

        def fmt(v):
            return "(vazio)" if v is None or v == "" else str(v)

        dlg = QDialog(self)
        dlg.setWindowTitle(f"Prévia da importação — {plano.arquivo}")
        dlg.resize(1050, 720)
        lay = QVBoxLayout(dlg)
        if plano.erros or plano.conflitos:
            lay.addWidget(AlertBox("Há erros ou conflitos: nada será gravado. Corrija a planilha (ou exporte "
                                   "novamente) e importe de novo.", "error"))
        elif not plano.tem_gravacao:
            lay.addWidget(AlertBox("Nada a gravar: o conteúdo da planilha já está no sistema.", "info"))
        else:
            lay.addWidget(AlertBox("Revise as inclusões, alterações e limpezas. A gravação é feita de uma vez, "
                                   "com cópia de segurança antes.", "success"))
        for aviso in plano.avisos:
            lbl = QLabel("⚠️ " + aviso)
            lbl.setWordWrap(True)
            lay.addWidget(lbl)

        grade = QGridLayout()
        cards = [("Inclusões", len(plano.inclusoes)), ("Alterações", len(plano.alteracoes)),
                 ("Limpezas", len(plano.limpezas)), ("Vínculos atualizados", len(plano.propagacoes)),
                 ("Duplicados ignorados", len(plano.duplicados)),
                 ("Sem gravação", len(plano.sem_mudanca) + len(plano.ja_aplicadas) + len(plano.mantidas)),
                 ("Conflitos", len(plano.conflitos)), ("Erros", len(plano.erros))]
        for i, (r, n) in enumerate(cards):
            grade.addWidget(MetricCard(r, n), i // 4, i % 4)
        lay.addLayout(grade)

        def conteudo(tab, valores, extras):
            partes = [f"{nome_col(c)}: {fmt(valores.get(c))}" for c in [x.nome for x in pp.CAMPOS[tab]]
                      if valores.get(c) not in (None, "")]
            partes += [f"{k}: {v}" for k, v in (extras or {}).items() if v not in (None, "")]
            return "; ".join(partes)

        abas = QTabWidget()
        tabelas = [
            ("Erros", pd.DataFrame([{"Aba": p.aba, "Linha": p.linha or "", "Coluna": nome_col(p.coluna),
                                     "Problema": p.mensagem} for p in plano.erros])),
            ("Conflitos", pd.DataFrame([{"Aba": p.aba, "Linha": p.linha or "", "Coluna": nome_col(p.coluna),
                                         "Problema": p.mensagem} for p in plano.conflitos])),
            ("Inclusões", pd.DataFrame([{"Tabela": nomes[i.tabela], "Linha": i.linha,
                                         "Conteúdo": conteudo(i.tabela, i.valores, i.extras)}
                                        for i in plano.inclusoes])),
            ("Alterações", pd.DataFrame([{"Tabela": nomes[a.tabela], "Linha": a.linha, "ID": a.id,
                                          "Campo": nome_col(m.coluna), "Antes": fmt(m.antes), "Depois": fmt(m.depois),
                                          "Limpeza": "LIMPA O VALOR" if m.limpeza else ""}
                                         for a in plano.alteracoes for m in a.mudancas])),
            ("Limpezas", pd.DataFrame([{"Tabela": nomes[a.tabela], "Linha": a.linha, "ID": a.id,
                                        "Campo": nome_col(m.coluna), "Valor atual (será limpo)": fmt(m.antes),
                                        "Fica": fmt(m.depois)} for a, m in plano.limpezas])),
            ("Vínculos", pd.DataFrame([{"Cadastro (ID)": p.cadastro_id, "Nome": p.nome, "Vínculo atual": p.de,
                                        "Novo vínculo": p.para} for p in plano.propagacoes])),
            ("Duplicados", pd.DataFrame([{"Tabela": nomes[o.tabela], "Linha": o.linha, "Motivo": o.motivo}
                                         for o in plano.duplicados])),
            ("Sem gravação", pd.DataFrame([{"Tabela": nomes[o.tabela], "Linha": o.linha, "ID": o.id or "",
                                            "Situação": o.motivo}
                                           for o in plano.sem_mudanca + plano.ja_aplicadas + plano.mantidas])),
        ]
        for titulo, df in tabelas:
            if df.empty:
                continue
            w = QWidget()
            lw = QVBoxLayout(w)
            lw.addWidget(PaginatedTableWidget(df, linhas_por_pagina=12, status_cols=()))
            abas.addTab(w, f"{titulo} ({len(df)})")
        if abas.count():
            lay.addWidget(abas, stretch=1)
        else:
            lay.addStretch(1)

        barra = QHBoxLayout()
        barra.addStretch(1)
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.clicked.connect(dlg.reject)
        btn_ok = QPushButton("Confirmar importação")
        btn_ok.setObjectName("PrimaryBtn")
        btn_ok.setEnabled(plano.pode_confirmar)
        btn_ok.clicked.connect(dlg.accept)
        barra.addWidget(btn_cancelar)
        barra.addWidget(btn_ok)
        lay.addLayout(barra)
        dlg.botao_confirmar = btn_ok  # usado nos testes
        return dlg


def main():
    """Ponto de entrada da aplicação desktop PyQt6."""
    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName("OneWorld")
    if LOGO_PADRAO.exists():
        app.setWindowIcon(QIcon(str(LOGO_PADRAO)))
    janela = OneWorldWindow()
    janela.show()
    sys.exit(app.exec())
