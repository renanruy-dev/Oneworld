"""Tema visual: paletas Claro/Escuro e CSS (roxo + verde OneWorld). Sem Streamlit."""
from string import Template

CLARO = dict(bg="#F6F6FB", surface="#FFFFFF", text="#1E2140", muted="#646B86",
             border="#E2E3EF", side="#FFFFFF")
ESCURO = dict(bg="#12121D", surface="#1C1C2C", text="#ECECF7", muted="#A0A3BC",
              border="#2F2F46", side="#171725")

_GAP = {"Compacta": "0.5rem", "Confortável": "1rem", "Ampla": "1.6rem"}
_PAD = {"Compacta": "1.2rem", "Confortável": "2rem", "Ampla": "3rem"}
_FS = {"P": "14px", "M": "16px", "G": "18px"}

_CSS = Template("""
html, .stApp, .stApp p, .stApp label, .stApp li {font-size:$fs;}
.stApp {background:var(--bg); color:var(--text);}
.stApp h1,.stApp h2,.stApp h3,.stApp h4,.stApp p,.stApp label,.stApp li,
.stApp [data-testid="stMarkdownContainer"] {color:var(--text);}
.stApp .stCaption, .stApp [data-testid="stCaptionContainer"],
[data-testid="stMetricLabel"] {color:var(--muted) !important;}
[data-testid="stHeader"] {background:transparent;}
.block-container {padding-top:$pad; max-width:1300px;}
[data-testid="stVerticalBlock"] {gap:$gap;}
[data-testid="stSidebar"] {background:var(--side); border-right:1px solid var(--border);}
[data-testid="stSidebar"] img {border-radius:14px;}
.main-title {font-size:2rem; font-weight:800; line-height:1.15; margin:0; color:var(--text);}
.brand-bar {height:4px; width:84px; border-radius:4px; margin:8px 0 10px;
            background:linear-gradient(90deg,$cor2,$cor);}
.sub-title {color:var(--muted); margin-bottom:1.2rem;}
[data-testid="stMetric"] {background:var(--surface); border:1px solid var(--border);
    border-left:5px solid $cor2; border-radius:12px; padding:14px 16px;}
[data-testid="stMetricValue"] {color:$cor;}
button[data-baseweb="tab"][aria-selected="true"] {color:$cor;}
[data-baseweb="tab-highlight"] {background-color:$cor !important;}
div.stButton > button[kind="primary"], div.stFormSubmitButton > button[kind="primary"] {
    background:$cor; border:1px solid $cor; color:#fff; font-weight:600;}
div.stButton > button[kind="primary"]:hover, div.stFormSubmitButton > button[kind="primary"]:hover {
    filter:brightness(1.12); border-color:$cor2;}
div.stButton > button:not([kind="primary"]), div.stDownloadButton > button {
    background:var(--surface); color:var(--text); border:1px solid var(--border);}
.stTextInput input,.stTextArea textarea,.stNumberInput input,.stDateInput input,
[data-baseweb="select"] > div, [data-baseweb="input"] {
    background:var(--surface) !important; color:var(--text) !important;
    border-color:var(--border) !important;}
ul[role="listbox"] {background:var(--surface) !important;}
ul[role="listbox"] li {color:var(--text) !important;}
[data-testid="stExpander"] {background:var(--surface); border:1px solid var(--border); border-radius:10px;}
[data-testid="stAlert"] {border-radius:10px;}
hr {border-color:var(--border);}
.ow-card {background:var(--surface); border:1px solid var(--border); border-radius:12px; padding:14px 16px;}
.ow-chip {display:inline-block; padding:2px 10px; border-radius:999px; font-size:.8rem; font-weight:600;}
""")


def _vars(p):
    return "".join(f"--{k}:{v};" for k, v in p.items())


def gerar_css(cfg):
    """Devolve o bloco <style> completo para a configuração atual."""
    if cfg["tema"] == "Claro":
        raiz = f":root{{{_vars(CLARO)}}}"
    elif cfg["tema"] == "Escuro":
        raiz = f":root{{{_vars(ESCURO)}}}"
    else:  # Automático: segue o sistema operacional
        raiz = (f":root{{{_vars(CLARO)}}}"
                f"@media (prefers-color-scheme: dark){{:root{{{_vars(ESCURO)}}}}}")
    css = _CSS.substitute(cor=cfg["cor"], cor2=cfg["cor2"], gap=_GAP[cfg["densidade"]],
                          pad=_PAD[cfg["densidade"]], fs=_FS[cfg["texto"]])
    return f"<style>{raiz}{css}</style>"
