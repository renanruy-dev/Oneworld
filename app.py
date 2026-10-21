"""OneWorld — Protótipo 02 · ponto de entrada.
Rodar:  streamlit run app.py

Estrutura:
  app.py                  → este arquivo (configuração da página e início)
  oneworld/config.py      → constantes, paleta, listas e estrutura das tabelas
  oneworld/database.py    → banco SQLite (tabelas, CRUD, backup)
  oneworld/backend.py     → regras de negócio (importação, validação, IA simulada, Markdown)
  oneworld/tema.py        → temas Claro/Escuro e CSS
  oneworld/frontend.py    → telas e navegação (Streamlit)
"""
import streamlit as st

from oneworld.config import LOGO_PADRAO

st.set_page_config(
    page_title="OneWorld",
    page_icon=str(LOGO_PADRAO) if LOGO_PADRAO.exists() else "🌐",
    layout="wide",
)

from oneworld import frontend  # noqa: E402  (precisa vir depois do set_page_config)

frontend.main()
