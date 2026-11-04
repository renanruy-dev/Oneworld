"""Interface gráfica desktop nativa (PyQt6) do OneWorld: telas, formulários e navegação.
Só desenha e coleta ações do usuário; regras ficam em backend.py e SQL em database.py."""
from __future__ import annotations

import math
import sys
from datetime import date
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
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
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
from . import database as db
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
        lbl = QLabel(texto)
        lbl.setWordWrap(True)
        if tipo in cores_txt:
            lbl.setStyleSheet(f"color: {cores_txt[tipo]}; font-weight: 600;")
        lay.addWidget(lbl)


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
            self.df_lido = bk.ler_arquivo(p)
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

        lbl_map = QLabel("<b>Mapeamento de colunas</b> — sugerido automaticamente por nome; ajuste se precisar")
        self.lay_din.addWidget(lbl_map)

        sug = bk.sugerir(list(data.columns), self.destino_atual, self.janela.cfg)
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
        cfg = {**PADROES, **db.cfg_ler("config", {})}
        if cfg.get("texto") not in ("P", "M", "G"):
            cfg["texto"] = "M"
        if cfg.get("perfil_negocio") not in PERFIS_NEGOCIO:
            cfg["perfil_negocio"] = PERFIL_PADRAO
        if not isinstance(cfg.get("rotulos_custom"), dict):
            cfg["rotulos_custom"] = {}
        self.cfg: dict = cfg
        self.campos_personalizados: list[str] = db.cfg_ler("campos_personalizados", [])
        self.notificacoes: list[str] = ["Sistema inicializado.", "Dados carregados do SQLite."]
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
            pix = pixmap_arredondado(logo, 210, raio=14)
            if not pix.isNull():
                lbl_logo.setPixmap(pix)
                self.lay_sidebar.addWidget(lbl_logo, alignment=Qt.AlignmentFlag.AlignCenter)
            if bk.sem_acento(self.cfg["nome"]) != "oneworld":
                lbl_nm = QLabel(f"<b>{self.cfg['nome']}</b>")
                self.lay_sidebar.addWidget(lbl_nm)
        else:
            lbl_nm = QLabel(self.cfg["nome"])
            lbl_nm.setObjectName("MainTitle")
            self.lay_sidebar.addWidget(lbl_nm)

        cap_sub = QLabel("Gerência e análise em um só mundo")
        cap_sub.setObjectName("Caption")
        cap_sub.setWordWrap(True)
        self.lay_sidebar.addWidget(cap_sub)
        self.lay_sidebar.addSpacing(8)

        lbl_nav = QLabel("Navegação")
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
        self.lay_sidebar.addWidget(Divider())

        lbl_amb = QLabel("Ambiente")
        lbl_amb.setObjectName("Caption")
        self.lay_sidebar.addWidget(lbl_amb)
        perfil_txt = self.cfg.get("perfil_negocio", PERFIL_PADRAO)
        for info in (f"Perfil: {perfil_txt}", "Modo: local", "Banco: SQLite", "Status: operacional"):
            lbl_i = QLabel(info)
            lbl_i.setWordWrap(True)
            self.lay_sidebar.addWidget(lbl_i)

        self.sidebar_frame.style().unpolish(self.sidebar_frame)
        self.sidebar_frame.style().polish(self.sidebar_frame)

    def navegar_para(self, nova_pagina: str):
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
            "Anotações": self.pagina_anotacoes,
            "Configurações": self.pagina_config,
        }
        rotas[self.pagina_atual]()

        self.lay_pagina.addStretch(1)
        self.lay_pagina.addWidget(Divider())
        rodape = QLabel("OneWorld — BI & Gestão · dados em SQLite local · estrutura adaptável por perfil de negócio.")
        rodape.setObjectName("Caption")
        self.lay_pagina.addWidget(rodape)

    # ── PÁGINA 1: DASHBOARD ──
    def pagina_dashboard(self):
        v = self.vocab()
        self._cabecalho("Dashboard", "Visão geral dos dados e indicadores do negócio")
        e, cv = self.dados("eventos"), self.dados("convidados")

        barra_f = QHBoxLayout()
        barra_f.setSpacing(16)

        col_f1 = QVBoxLayout()
        col_f1.addWidget(QLabel("Período"))
        cb_mes = QComboBox()
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
        barra_f.addLayout(col_f1, stretch=1)

        col_f2 = QVBoxLayout()
        col_f2.addWidget(QLabel(v["rotulos"]["status"]))
        stat_atual = self.estado.get("dash_status", [])
        ms_status = MultiSelectChips(STATUS_EVENTO, stat_atual, self.cfg["cor"])
        ms_status.changed.connect(lambda vals: self._definir_filtro("dash_status", vals))
        col_f2.addWidget(ms_status)
        barra_f.addLayout(col_f2, stretch=2)

        self.lay_pagina.addLayout(barra_f)

        f = bk.filtrar_eventos(e, mes_atual, stat_atual)
        conf = int((cv["confirmacao"] == "Confirmado").sum()) if not cv.empty else 0

        linha_m = QHBoxLayout()
        linha_m.setSpacing(12)
        linha_m.addWidget(MetricCard(v["metric_ent1"], len(f)))
        linha_m.addWidget(MetricCard(v["metric_qtd"], int(f["convidados"].sum())))
        linha_m.addWidget(MetricCard(v["metric_valor"], self.moeda(f["valor"].sum())))
        linha_m.addWidget(MetricCard(v["metric_pend"], int(f["status"].isin(["Pendente", "Em planejamento"]).sum())))
        linha_m.addWidget(MetricCard(v["metric_ent2_conf"], f"{conf} de {len(cv)}"))
        self.lay_pagina.addLayout(linha_m)

        cap = QLabel(v["legenda_valor"])
        cap.setObjectName("Caption")
        self.lay_pagina.addWidget(cap)
        self.lay_pagina.addWidget(Divider())

        linha_g = QHBoxLayout()
        linha_g.setSpacing(16)

        col_g1 = QVBoxLayout()
        col_g2 = QVBoxLayout()
        col_g3 = QVBoxLayout()

        if not f.empty:
            t = f.assign(mes=pd.to_datetime(f["data"]).dt.strftime("%Y-%m"))
            col_g1.addWidget(self._subtitulo(f"{v['metric_valor']} por mês"))
            col_g1.addWidget(BarChartWidget(t.groupby("mes")["valor"].sum(), self.cfg["cor"], self.cfg, True))

            col_g2.addWidget(self._subtitulo(v["grafico_status"]))
            col_g2.addWidget(BarChartWidget(f.groupby("status").size(), self.cfg["cor2"], self.cfg, False))
        else:
            col_g1.addWidget(AlertBox("Nenhum registro para os filtros escolhidos.", "info"))

        col_g3.addWidget(self._subtitulo("Notificações"))
        if self.cfg.get("lembretes", True):
            for msg in bk.lembretes(e):
                col_g3.addWidget(AlertBox(msg, "warning"))
        for n in self.notificacoes[:5]:
            col_g3.addWidget(AlertBox(n, "info"))
        col_g3.addStretch(1)

        linha_g.addLayout(col_g1, stretch=20)
        linha_g.addLayout(col_g2, stretch=20)
        linha_g.addLayout(col_g3, stretch=13)
        self.lay_pagina.addLayout(linha_g)

        self.lay_pagina.addWidget(self._subtitulo(v["proximos_titulo"]))
        prox = f[pd.to_datetime(f["data"]).dt.date >= date.today()] if not f.empty else f
        df_exibir = (prox if not prox.empty else f).drop(columns=["id"], errors="ignore")
        self.lay_pagina.addWidget(
            PaginatedTableWidget(
                self.formatar(df_exibir, "eventos"),
                linhas_por_pagina=self.cfg["linhas"],
                pagina_inicial=self.estado.get("pg_dash", 1),
                ao_mudar_pagina=lambda pg: self.estado.__setitem__("pg_dash", pg),
            )
        )

    def _definir_filtro(self, chave: str, valor):
        self.estado[chave] = valor
        self.reconstruir_pagina()

    # ── PÁGINA 2: ENTIDADE PRINCIPAL (OPERAÇÕES / VENDAS / PROJETOS / EVENTOS) ──
    def pagina_eventos(self):
        v = self.vocab()
        self._cabecalho(v["menu_ent1"], v["ent1_subtitulo"])
        abas = QTabWidget()

        # Aba 1: Listagem
        w_lista = QWidget()
        l_lista = QVBoxLayout(w_lista)
        l_lista.setContentsMargins(16, 16, 16, 16)
        l_lista.setSpacing(12)

        e = self.dados("eventos")
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
            l_ed.addStretch(1)

        abas.addTab(w_ed, "Editar / excluir")
        abas.setCurrentIndex(self.estado.get("tab_eventos", 0))
        abas.currentChanged.connect(lambda idx: self.estado.__setitem__("tab_eventos", idx))
        self.lay_pagina.addWidget(abas)

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

    # ── PÁGINA 3: ENTIDADE SECUNDÁRIA (CADASTROS / CLIENTES / ATIVIDADES / CONVIDADOS) ──
    def pagina_convidados(self):
        v = self.vocab()
        rot = v["rotulos"]
        self._cabecalho(v["menu_ent2"], v["ent2_subtitulo"])
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
        card_conf = MetricCard("Confirmados", 0)
        card_pend = MetricCard("Pendentes", 0)
        card_rec = MetricCard("Recusaram / Inativos", 0)
        linha_m.addWidget(card_conf)
        linha_m.addWidget(card_pend)
        linha_m.addWidget(card_rec)
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

            card_conf.atualizar(int((df_f["confirmacao"] == "Confirmado").sum()) if not df_f.empty else 0)
            card_pend.atualizar(int((df_f["confirmacao"] == "Pendente").sum()) if not df_f.empty else 0)
            card_rec.atualizar(int((df_f["confirmacao"] == "Recusou").sum()) if not df_f.empty else 0)

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

        self.lay_pagina.addWidget(abas)

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
        sp_ac.setRange(0, 1000)
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
        self._cabecalho("Dados Externos", "Recebimento, validação e tratamento")
        self.lay_pagina.addWidget(ImportarPlanilhaWidget(self, destino_fixo=None, chave_estado="impex"))
        self.lay_pagina.addWidget(Divider())
        self.lay_pagina.addWidget(self._subtitulo("Histórico"))
        h = db.historico_arquivos()
        if h.empty:
            self.lay_pagina.addWidget(AlertBox("Nenhum arquivo recebido.", "info"))
        else:
            self.lay_pagina.addWidget(
                PaginatedTableWidget(h, linhas_por_pagina=self.cfg["linhas"], status_cols=())
            )

    # ── PÁGINA 5: ORIENTAÇÃO IA ──
    def pagina_ia(self):
        self._cabecalho("Orientação IA", "Perguntas e análises baseadas nos dados")
        self.lay_pagina.addWidget(
            AlertBox(
                "Resposta SIMULADA por regras locais. A IA externa (BYOK) ainda é uma decisão pendente do "
                "projeto; quando existir, ela orienta e sugere, sem alterar registros.",
                "info",
            )
        )

        self.lay_pagina.addWidget(QLabel("Pergunte sobre seus dados"))
        ed_perg = QPlainTextEdit()
        ed_perg.setPlaceholderText("Ex.: Qual é o valor/receita previsto por mês?")
        ed_perg.setMaximumHeight(95)
        self.lay_pagina.addWidget(ed_perg)

        btn_perg = QPushButton("Perguntar")
        btn_perg.setObjectName("PrimaryBtn")
        btn_perg.setCursor(Qt.CursorShape.PointingHandCursor)
        self.lay_pagina.addWidget(btn_perg, alignment=Qt.AlignmentFlag.AlignLeft)

        ult_resp = self.estado.get("ia_ultima_resposta")
        if ult_resp:
            self.lay_pagina.addWidget(self._subtitulo("Resposta"))
            self.lay_pagina.addWidget(AlertBox(ult_resp, "info"))

        def fazer_pergunta():
            p = ed_perg.toPlainText().strip()
            if not p:
                return
            resp = bk.responder_ia(p, self.dados("eventos"), self.dados("convidados"), self.cfg)
            db.salvar_relatorio(p, resp)
            self.estado["ia_ultima_resposta"] = resp
            self.reconstruir_pagina()

        btn_perg.clicked.connect(fazer_pergunta)

        self.lay_pagina.addWidget(self._subtitulo("Relatórios recentes"))
        rels = db.listar_relatorios()
        if rels.empty:
            cap_v = QLabel("Nenhuma pergunta registrada ainda.")
            cap_v.setObjectName("Caption")
            self.lay_pagina.addWidget(cap_v)
        else:
            for r in rels.itertuples():
                exp = ExpanderWidget(f"{r.data} — {r.pergunta}")
                lbl_r = QLabel(str(r.resposta))
                lbl_r.setWordWrap(True)
                exp.corpo_layout.addWidget(lbl_r)
                self.lay_pagina.addWidget(exp)

        self.lay_pagina.addWidget(Divider())
        self.lay_pagina.addWidget(self._subtitulo("Exportar para análise externa"))
        cap_ex = QLabel(
            "Gera um Markdown com resumo, tabelas e um prompt sugerido para colar em um chat de IA externo. "
            "Ao colar, os dados saem do seu computador."
        )
        cap_ex.setObjectName("Caption")
        cap_ex.setWordWrap(True)
        self.lay_pagina.addWidget(cap_ex)

        md = bk.gerar_markdown(self.dados("eventos"), self.dados("convidados"), self.cfg)
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
        self.lay_pagina.addWidget(btn_md, alignment=Qt.AlignmentFlag.AlignLeft)

        exp_prev = ExpanderWidget("Pré-visualizar")
        ed_code = QPlainTextEdit(md)
        ed_code.setReadOnly(True)
        ed_code.setMinimumHeight(220)
        ed_code.setFont(QFont("Consolas", 10))
        exp_prev.corpo_layout.addWidget(ed_code)
        self.lay_pagina.addWidget(exp_prev)

    # ── PÁGINA 6: ANOTAÇÕES ──
    def pagina_anotacoes(self):
        self._cabecalho("Anotações", "Notas, relatórios e datas previstas")

        card_form = QFrame()
        card_form.setObjectName("OwCard")
        lay_f = QVBoxLayout(card_form)
        lay_f.setContentsMargins(16, 16, 16, 16)
        lay_f.setSpacing(10)

        form = QFormLayout()
        ed_tit = QLineEdit()
        ed_desc = QPlainTextEdit()
        ed_desc.setMaximumHeight(90)
        hoje = date.today()
        ed_dp = QDateEdit(QDate(hoje.year, hoje.month, hoje.day))
        ed_dp.setCalendarPopup(True)
        ed_dp.setDisplayFormat("dd/MM/yyyy")

        form.addRow("Título", ed_tit)
        form.addRow("Descrição", ed_desc)
        form.addRow("Data prevista", ed_dp)
        lay_f.addLayout(form)

        lbl_err = QLabel()
        lbl_err.setStyleSheet("color: #8F2412; font-weight: 600;")
        lbl_err.setVisible(False)
        lay_f.addWidget(lbl_err)

        btn_salvar = QPushButton("Salvar anotação")
        btn_salvar.setObjectName("PrimaryBtn")
        btn_salvar.setCursor(Qt.CursorShape.PointingHandCursor)

        def criar_nota():
            t = ed_tit.text().strip()
            if not t:
                lbl_err.setText("Informe um título.")
                lbl_err.setVisible(True)
                return
            qdt = ed_dp.date()
            iso = date(qdt.year(), qdt.month(), qdt.day()).isoformat()
            db.criar_anotacao(t, ed_desc.toPlainText().strip(), iso)
            self.flash("Anotação salva.")
            self.reconstruir_pagina()

        btn_salvar.clicked.connect(criar_nota)
        lay_f.addWidget(btn_salvar, alignment=Qt.AlignmentFlag.AlignLeft)
        self.lay_pagina.addWidget(card_form)

        notas = db.listar_anotacoes()
        if notas.empty:
            self.lay_pagina.addWidget(AlertBox("Nenhuma anotação cadastrada.", "info"))
        else:
            for r in notas.itertuples():
                exp = ExpanderWidget(f"{bk.fmt_data(r.data)} — {r.titulo}")
                lbl_d = QLabel(r.descricao or "—")
                lbl_d.setWordWrap(True)
                exp.corpo_layout.addWidget(lbl_d)
                btn_del = QPushButton("Excluir anotação")
                btn_del.setCursor(Qt.CursorShape.PointingHandCursor)
                btn_del.clicked.connect(lambda _, id_=r.id: self._excluir_nota(id_))
                exp.corpo_layout.addWidget(btn_del, alignment=Qt.AlignmentFlag.AlignLeft)
                self.lay_pagina.addWidget(exp)

    def _excluir_nota(self, id_: int):
        db.excluir_anotacao(id_)
        self.flash("Anotação excluída.")
        self.reconstruir_pagina()

    # ── PÁGINA 7: CONFIGURAÇÕES ──
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
            f"{db.contar_backups()} backup(s) na pasta {BACKUP_DIR}. "
            "A restauração ainda é um requisito pendente."
        )
        cap_bkp.setObjectName("Caption")
        l_seg.addWidget(cap_bkp)
        l_seg.addWidget(AlertBox("Chaves de API (BYOK) devem ficar no arquivo .env, nunca no código.", "warning"))
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


def main():
    """Ponto de entrada da aplicação desktop PyQt6."""
    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName("OneWorld")
    if LOGO_PADRAO.exists():
        app.setWindowIcon(QIcon(str(LOGO_PADRAO)))
    janela = OneWorldWindow()
    janela.show()
    sys.exit(app.exec())
