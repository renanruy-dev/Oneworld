"""Constantes e configurações fixas do OneWorld (sem lógica e sem Streamlit)."""
from pathlib import Path

# ── Caminhos (a raiz do projeto é a pasta que contém app.py) ──
RAIZ = Path(__file__).resolve().parent.parent
DB_PATH = RAIZ / "oneworld.db"
BACKUP_DIR = RAIZ / "backups"
ASSETS_DIR = RAIZ / "assets"
LOGO_PADRAO = RAIZ / "OneWorld-logo.jpg"

# ── Identidade visual ──
ROXO = "#5B4FC4"
VERDE = "#9BC53D"

PADROES = {
    "nome": "OneWorld", "cor": ROXO, "cor2": VERDE, "tema": "Claro",
    "densidade": "Confortável", "texto": "M", "pagina_inicial": "Dashboard",
    "linhas": 10, "auto_refresh": False, "lembrar_filtros": True,
    "lembretes": True, "idioma": "Português", "moeda": "BRL",
}

PAGINAS = ["Dashboard", "Eventos", "Convidados & Planilhas", "Dados Externos",
           "Orientação IA", "Anotações", "Configurações"]

STATUS_EVENTO = ["Em planejamento", "Confirmado", "Concluído", "Pendente"]
STATUS_CONV = ["Confirmado", "Pendente", "Recusou"]

STATUS_CORES = {  # (fundo, texto) — legíveis em tema claro e escuro
    "Confirmado": ("#DDF2C2", "#2F5A06"),
    "Em planejamento": ("#FFEBB8", "#7A4B00"),
    "Pendente": ("#FFD9D2", "#8F2412"),
    "Concluído": ("#DCD8F8", "#352A99"),
    "Recusou": ("#E6E6EC", "#44465A"),
}

# ── Estrutura das tabelas ──
CAMPOS = {
    "eventos": ["data", "cliente", "local", "convidados", "valor", "status"],
    "convidados": ["evento", "nome", "mesa", "acompanhantes", "contato",
                   "restricao", "confirmacao"],
}
CAMPOS_DESTINO = {
    "eventos": {"data": "Data", "cliente": "Nome / identificação", "local": "Local / espaço",
                "convidados": "Convidados previstos", "valor": "Valor previsto",
                "status": "Status"},
    "convidados": {"evento": "Evento", "nome": "Nome", "mesa": "Mesa",
                   "acompanhantes": "Acompanhantes", "contato": "Contato",
                   "restricao": "Restrição alimentar", "confirmacao": "Confirmação"},
}
OBRIGATORIOS = {"eventos": ["data", "cliente"], "convidados": ["nome"]}
ROTULOS = {"id": "ID", "data": "Data", "cliente": "Cliente", "local": "Local",
           "convidados": "Convidados", "valor": "Valor", "status": "Status",
           "evento": "Evento", "nome": "Nome", "mesa": "Mesa",
           "acompanhantes": "Acompanhantes", "contato": "Contato",
           "restricao": "Restrição alimentar", "confirmacao": "Confirmação"}

# ── Importação: sugestão de mapeamento por nome de coluna ──
NAO_USAR = "— não importar —"
SINONIMOS = {
    "eventos": {"data": ["data", "dia", "date"],
                "cliente": ["cliente", "identificacao", "organizacao", "evento", "nome"],
                "local": ["local", "salao", "espaco", "lugar"],
                "convidados": ["convidados", "pessoas", "quantidade", "qtd", "lotacao"],
                "valor": ["valor", "preco", "receita", "total", "reserva"],
                "status": ["status", "situacao"]},
    "convidados": {"evento": ["evento", "cliente"],
                   "nome": ["nome", "convidado", "pessoa"],
                   "mesa": ["mesa"],
                   "acompanhantes": ["acompanhantes", "acomp", "extras"],
                   "contato": ["contato", "email", "telefone", "celular", "whatsapp"],
                   "restricao": ["restricao", "alimentar", "dieta"],
                   "confirmacao": ["confirmacao", "confirmado", "rsvp", "presenca", "status"]},
}
ALIAS_OPCAO = {"sim": "Confirmado", "confirmada": "Confirmado", "ok": "Confirmado",
               "nao": "Recusou", "recusado": "Recusou", "recusada": "Recusou",
               "aguardando": "Pendente", "planejamento": "Em planejamento",
               "concluido": "Concluído", "realizado": "Concluído"}

# Chaves de filtros da interface (limpas ao trocar de página se "lembrar filtros" estiver off)
FILTROS = ["dash_mes", "dash_status", "ev_busca", "ev_status",
           "cv_busca", "cv_evento", "cv_conf"]
