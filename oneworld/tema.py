"""Tema visual: paletas Claro/Escuro e estilos QSS (PyQt6) + CSS legado (roxo + verde OneWorld)."""
from string import Template

CLARO = dict(bg="#F6F6FB", surface="#FFFFFF", text="#1E2140", muted="#646B86",
             border="#E2E3EF", side="#FFFFFF")
ESCURO = dict(bg="#12121D", surface="#1C1C2C", text="#ECECF7", muted="#A0A3BC",
              border="#2F2F46", side="#171725")

_GAP = {"Compacta": "0.5rem", "Confortável": "1rem", "Ampla": "1.6rem"}
_PAD = {"Compacta": "1.2rem", "Confortável": "2rem", "Ampla": "3rem"}
_FS = {"P": "14px", "M": "16px", "G": "18px"}

_GAP_PX = {"Compacta": 8, "Confortável": 14, "Ampla": 22}
_PAD_PX = {"Compacta": 16, "Confortável": 26, "Ampla": 36}
_FS_PX = {"P": 13, "M": 14, "G": 16}


def paleta_atual(cfg):
    """Devolve o dicionário de cores (CLARO ou ESCURO) conforme a configuração atual."""
    tema = cfg.get("tema", "Claro")
    if tema == "Claro":
        return CLARO
    if tema == "Escuro":
        return ESCURO
    try:
        from PyQt6.QtCore import Qt
        from PyQt6.QtGui import QGuiApplication
        hints = QGuiApplication.styleHints()
        if hints and hints.colorScheme() == Qt.ColorScheme.Dark:
            return ESCURO
    except Exception:
        pass
    return CLARO


def metricas_layout(cfg):
    """Retorna (gap_px, pad_px, font_px) de acordo com densidade e tamanho de texto."""
    dens = cfg.get("densidade", "Confortável")
    txt = cfg.get("texto", "M")
    return (_GAP_PX.get(dens, 14), _PAD_PX.get(dens, 26), _FS_PX.get(txt, 14))


def gerar_qss(cfg):
    """Gera a folha de estilo Qt (QSS) fiel ao design original do OneWorld."""
    p = paleta_atual(cfg)
    _, _, fs = metricas_layout(cfg)
    cor = cfg.get("cor", "#5B4FC4")
    cor2 = cfg.get("cor2", "#9BC53D")
    fs_title = fs + 14
    fs_sub = fs + 3
    fs_small = max(11, fs - 1)
    fs_metric = fs + 10

    return f"""
    QMainWindow, QWidget#MainContent, QScrollArea#PageScroll, QWidget#PageContainer {{
        background-color: {p['bg']};
        color: {p['text']};
        font-family: "Segoe UI", "Inter", "Ubuntu", sans-serif;
        font-size: {fs}px;
    }}
    QLabel {{
        color: {p['text']};
        background: transparent;
        font-size: {fs}px;
    }}
    QLabel#MainTitle {{
        font-size: {fs_title}px;
        font-weight: 800;
        color: {p['text']};
    }}
    QLabel#SubTitle {{
        font-size: {fs}px;
        color: {p['muted']};
        margin-bottom: 6px;
    }}
    QLabel#SectionTitle {{
        font-size: {fs_sub}px;
        font-weight: 700;
        color: {p['text']};
        margin-top: 6px;
        margin-bottom: 2px;
    }}
    QLabel#Caption {{
        font-size: {fs_small}px;
        color: {p['muted']};
    }}
    QFrame#BrandBar {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {cor2}, stop:1 {cor});
        border-radius: 2px;
        min-height: 4px;
        max-height: 4px;
        min-width: 84px;
        max-width: 84px;
    }}
    QFrame#Divider {{
        background-color: {p['border']};
        min-height: 1px;
        max-height: 1px;
        border: none;
    }}
    /* Sidebar */
    QFrame#Sidebar {{
        background-color: {p['side']};
        border-right: 1px solid {p['border']};
    }}
    QPushButton#NavBtn {{
        text-align: left;
        padding: 9px 14px;
        border-radius: 8px;
        border: 1px solid transparent;
        background-color: transparent;
        color: {p['text']};
        font-size: {fs}px;
        font-weight: 500;
    }}
    QPushButton#NavBtn:hover {{
        background-color: {p['bg']};
        border-color: {p['border']};
    }}
    QPushButton#NavBtn[active="true"] {{
        background-color: {cor};
        color: #FFFFFF;
        font-weight: 700;
        border-color: {cor};
    }}
    /* Cards e Métricas */
    QFrame#MetricCard {{
        background-color: {p['surface']};
        border: 1px solid {p['border']};
        border-left: 5px solid {cor2};
        border-radius: 12px;
    }}
    QLabel#MetricLabel {{
        color: {p['muted']};
        font-size: {fs_small}px;
        font-weight: 600;
    }}
    QLabel#MetricValue {{
        color: {cor};
        font-size: {fs_metric}px;
        font-weight: 800;
    }}
    QFrame#OwCard {{
        background-color: {p['surface']};
        border: 1px solid {p['border']};
        border-radius: 12px;
    }}
    /* Alertas / Banners */
    QFrame#AlertInfo {{
        background-color: {p['surface']};
        border: 1px solid {p['border']};
        border-left: 4px solid {cor};
        border-radius: 10px;
    }}
    QFrame#AlertSuccess {{
        background-color: #DDF2C2;
        border: 1px solid #9BC53D;
        border-left: 4px solid #2F5A06;
        border-radius: 10px;
    }}
    QFrame#AlertWarning {{
        background-color: #FFEBB8;
        border: 1px solid #E0A800;
        border-left: 4px solid #7A4B00;
        border-radius: 10px;
    }}
    QFrame#AlertError {{
        background-color: #FFD9D2;
        border: 1px solid #D9534F;
        border-left: 4px solid #8F2412;
        border-radius: 10px;
    }}
    /* Botões */
    QPushButton {{
        background-color: {p['surface']};
        color: {p['text']};
        border: 1px solid {p['border']};
        border-radius: 8px;
        padding: 7px 14px;
        font-size: {fs}px;
        font-weight: 500;
    }}
    QPushButton:hover {{
        border-color: {cor};
    }}
    QPushButton:disabled {{
        color: {p['muted']};
        background-color: {p['bg']};
        border-color: {p['border']};
    }}
    QPushButton#PrimaryBtn {{
        background-color: {cor};
        color: #FFFFFF;
        border: 1px solid {cor};
        font-weight: 600;
    }}
    QPushButton#PrimaryBtn:hover {{
        border: 1px solid {cor2};
    }}
    QPushButton#PrimaryBtn:disabled {{
        background-color: {p['border']};
        color: {p['muted']};
        border-color: {p['border']};
    }}
    /* Entradas de formulário */
    QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox, QDateEdit, QComboBox {{
        background-color: {p['surface']};
        color: {p['text']};
        border: 1px solid {p['border']};
        border-radius: 8px;
        padding: 6px 10px;
        font-size: {fs}px;
        selection-background-color: {cor};
        selection-color: #FFFFFF;
    }}
    QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus,
    QSpinBox:focus, QDoubleSpinBox:focus, QDateEdit:focus, QComboBox:focus {{
        border: 1px solid {cor};
    }}
    QComboBox::drop-down {{
        border: none;
        width: 24px;
    }}
    QComboBox QAbstractItemView {{
        background-color: {p['surface']};
        color: {p['text']};
        border: 1px solid {p['border']};
        selection-background-color: {cor};
        selection-color: #FFFFFF;
        outline: 0;
    }}
    QCheckBox, QRadioButton {{
        color: {p['text']};
        font-size: {fs}px;
        spacing: 8px;
    }}
    /* Abas */
    QTabWidget::pane {{
        border: 1px solid {p['border']};
        background-color: {p['surface']};
        border-radius: 10px;
        top: -1px;
    }}
    QTabBar::tab {{
        background: transparent;
        color: {p['muted']};
        padding: 9px 16px;
        border: none;
        border-bottom: 3px solid transparent;
        font-size: {fs}px;
        font-weight: 600;
    }}
    QTabBar::tab:selected {{
        color: {cor};
        border-bottom: 3px solid {cor};
    }}
    QTabBar::tab:hover {{
        color: {p['text']};
    }}
    /* Tabelas */
    QTableWidget {{
        background-color: {p['surface']};
        alternate-background-color: {p['bg']};
        color: {p['text']};
        gridline-color: {p['border']};
        border: 1px solid {p['border']};
        border-radius: 10px;
        font-size: {fs}px;
        selection-background-color: {cor};
        selection-color: #FFFFFF;
    }}
    QHeaderView::section {{
        background-color: {p['bg']};
        color: {p['muted']};
        font-weight: 700;
        font-size: {fs_small}px;
        padding: 7px 10px;
        border: none;
        border-bottom: 1px solid {p['border']};
        border-right: 1px solid {p['border']};
    }}
    /* Scrollbars */
    QScrollBar:vertical {{
        background: transparent;
        width: 10px;
        margin: 0px;
    }}
    QScrollBar::handle:vertical {{
        background: {p['border']};
        min-height: 24px;
        border-radius: 5px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {p['muted']};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}
    QScrollBar:horizontal {{
        background: transparent;
        height: 10px;
        margin: 0px;
    }}
    QScrollBar::handle:horizontal {{
        background: {p['border']};
        min-width: 24px;
        border-radius: 5px;
    }}
    """


# ── Compatibilidade CSS legado ──
_CSS = Template("""
html, .stApp, .stApp p, .stApp label, .stApp li {font-size:$fs;}
.stApp {background:var(--bg); color:var(--text);}
""")


def _vars(p):
    return "".join(f"--{k}:{v};" for k, v in p.items())


def gerar_css(cfg):
    """Mantido por compatibilidade caso algum teste importe gerar_css."""
    if cfg["tema"] == "Claro":
        raiz = f":root{{{_vars(CLARO)}}}"
    elif cfg["tema"] == "Escuro":
        raiz = f":root{{{_vars(ESCURO)}}}"
    else:
        raiz = (f":root{{{_vars(CLARO)}}}"
                f"@media (prefers-color-scheme: dark){{:root{{{_vars(ESCURO)}}}}}")
    css = _CSS.substitute(cor=cfg["cor"], cor2=cfg["cor2"], gap=_GAP[cfg["densidade"]],
                          pad=_PAD[cfg["densidade"]], fs=_FS[cfg["texto"]])
    return f"<style>{raiz}{css}</style>"
