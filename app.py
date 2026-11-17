"""OneWorld — Protótipo 02 · ponto de entrada Desktop (PyQt6).
Rodar:  python app.py

Estrutura:
  app.py                  → este arquivo (inicialização da janela desktop PyQt6)
  oneworld/config.py      → constantes, paleta, listas e estrutura das tabelas
  oneworld/database.py    → banco SQLite (tabelas, CRUD, backup)
  oneworld/backend.py     → regras de negócio (importação, validação, IA simulada, Markdown)
  oneworld/tema.py        → temas Claro/Escuro e folha de estilo QSS
  oneworld/frontend.py    → telas, componentes e navegação (PyQt6)
"""
from oneworld import frontend

if __name__ == "__main__":
    frontend.main()
