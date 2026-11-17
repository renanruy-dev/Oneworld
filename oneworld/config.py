"""Constantes, perfis de negócio (domínios) e configurações do OneWorld."""
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

# ── Perfis de Negócio (Domínios Pré-configurados + Personalizáveis) ──
PERFIS_NEGOCIO = {
    "Gestão Empresarial (Geral)": {
        "menu_ent1": "Operações",
        "menu_ent2": "Cadastros & Planilhas",
        "ent1_singular": "Operação",
        "ent1_plural": "Operações",
        "ent1_subtitulo": "Registro e gerenciamento de operações, contratos e lançamentos",
        "ent2_singular": "Cadastro",
        "ent2_plural": "Cadastros",
        "ent2_subtitulo": "Clientes, itens vinculados, registros tabulares e campos personalizáveis",
        "metric_ent1": "Operações",
        "metric_qtd": "Volume / Quantidade",
        "metric_valor": "Receita / Valor previsto",
        "metric_pend": "Pendências",
        "metric_ent2_conf": "Cadastros confirmados",
        "legenda_valor": "Receita / Valor previsto = valores registrados nas operações; não representa liquidação bancária.",
        "grafico_status": "Operações por status",
        "proximos_titulo": "Próximas operações / lançamentos",
        "rotulos": {
            "id": "ID",
            "data": "Data",
            "cliente": "Cliente / Identificação",
            "local": "Categoria / Unidade",
            "convidados": "Quantidade / Volume",
            "valor": "Valor (R$)",
            "status": "Status",
            "evento": "Operação vinculada",
            "nome": "Nome / Registro",
            "mesa": "Grupo / Código",
            "acompanhantes": "Qtd. adicional",
            "contato": "Contato / Ref.",
            "restricao": "Observações",
            "confirmacao": "Situação",
        },
    },
    "Comércio & Vendas": {
        "menu_ent1": "Vendas & Pedidos",
        "menu_ent2": "Clientes & Planilhas",
        "ent1_singular": "Pedido",
        "ent1_plural": "Vendas / Pedidos",
        "ent1_subtitulo": "Controle de pedidos, faturamento previsto e canais de venda",
        "ent2_singular": "Cliente / Item",
        "ent2_plural": "Clientes & Itens",
        "ent2_subtitulo": "Carteira de clientes, itens de pedidos e importação de planilhas",
        "metric_ent1": "Pedidos",
        "metric_qtd": "Itens vendidos",
        "metric_valor": "Faturamento previsto",
        "metric_pend": "Pedidos pendentes",
        "metric_ent2_conf": "Clientes ativos / confirmados",
        "legenda_valor": "Faturamento previsto = soma dos pedidos cadastrados no período selecionado.",
        "grafico_status": "Pedidos por status",
        "proximos_titulo": "Pedidos recentes e entregas futuras",
        "rotulos": {
            "id": "ID",
            "data": "Data do pedido",
            "cliente": "Cliente / Pedido",
            "local": "Canal / Filial",
            "convidados": "Qtd. de itens",
            "valor": "Valor do pedido",
            "status": "Status",
            "evento": "Pedido / Origem",
            "nome": "Nome do cliente",
            "mesa": "Segmento / Código",
            "acompanhantes": "Itens extras",
            "contato": "Telefone / E-mail",
            "restricao": "Preferência / Obs.",
            "confirmacao": "Situação",
        },
    },
    "Serviços & Projetos": {
        "menu_ent1": "Projetos & Ordens",
        "menu_ent2": "Atividades & Planilhas",
        "ent1_singular": "Projeto / OS",
        "ent1_plural": "Projetos / Ordens",
        "ent1_subtitulo": "Gerenciamento de projetos, ordens de serviço, prazos e orçamentos",
        "ent2_singular": "Atividade / Alocação",
        "ent2_plural": "Atividades & Equipe",
        "ent2_subtitulo": "Tarefas, profissionais alocados, entregáveis e planilhas",
        "metric_ent1": "Projetos / OS",
        "metric_qtd": "Horas / Alocações",
        "metric_valor": "Orçamento previsto",
        "metric_pend": "Em aberto / planejamento",
        "metric_ent2_conf": "Atividades confirmadas",
        "legenda_valor": "Orçamento previsto = valores estimados nos projetos e ordens de serviço.",
        "grafico_status": "Projetos por status",
        "proximos_titulo": "Próximos prazos e entregas",
        "rotulos": {
            "id": "ID",
            "data": "Data / Prazo",
            "cliente": "Cliente / Projeto",
            "local": "Escopo / Unidade",
            "convidados": "Horas / Equipe",
            "valor": "Valor orçado",
            "status": "Status",
            "evento": "Projeto vinculado",
            "nome": "Responsável / Tarefa",
            "mesa": "Setor / Etapa",
            "acompanhantes": "Subtarefas",
            "contato": "Contato",
            "restricao": "Especificação técnica",
            "confirmacao": "Situação",
        },
    },
    "Eventos & Recepção": {
        "menu_ent1": "Eventos",
        "menu_ent2": "Convidados & Planilhas",
        "ent1_singular": "Evento",
        "ent1_plural": "Eventos",
        "ent1_subtitulo": "Cadastro e gerenciamento de eventos e reservas",
        "ent2_singular": "Convidado",
        "ent2_plural": "Convidados",
        "ent2_subtitulo": "Registros tabulares, lista de presença e campos personalizáveis",
        "metric_ent1": "Eventos",
        "metric_qtd": "Convidados previstos",
        "metric_valor": "Receita prevista",
        "metric_pend": "Pendências",
        "metric_ent2_conf": "Convidados confirmados",
        "legenda_valor": "Receita prevista = valores cadastrados nas reservas; não representa pagamentos recebidos.",
        "grafico_status": "Eventos por status",
        "proximos_titulo": "Próximos eventos",
        "rotulos": {
            "id": "ID",
            "data": "Data",
            "cliente": "Nome / identificação",
            "local": "Local / espaço",
            "convidados": "Convidados previstos",
            "valor": "Valor previsto",
            "status": "Status",
            "evento": "Evento",
            "nome": "Nome",
            "mesa": "Mesa",
            "acompanhantes": "Acompanhantes",
            "contato": "Contato",
            "restricao": "Restrição alimentar",
            "confirmacao": "Confirmação",
        },
    },
}

PERFIL_PADRAO = "Gestão Empresarial (Geral)"

PADROES = {
    "nome": "OneWorld",
    "cor": ROXO,
    "cor2": VERDE,
    "tema": "Claro",
    "densidade": "Confortável",
    "texto": "M",
    "pagina_inicial": "Dashboard",
    "linhas": 10,
    "auto_refresh": False,
    "lembrar_filtros": True,
    "lembretes": True,
    "idioma": "Português",
    "moeda": "BRL",
    "perfil_negocio": PERFIL_PADRAO,
    "rotulos_custom": {},
}

# Chaves internas fixas de rota (garantem navegação estável independentemente do nome exibido no menu)
PAGINAS = [
    "Dashboard",
    "Eventos",
    "Convidados & Planilhas",
    "Dados Externos",
    "Orientação IA",
    "Anotações",
    "Configurações",
]

STATUS_EVENTO = ["Em planejamento", "Confirmado", "Concluído", "Pendente"]
STATUS_CONV = ["Confirmado", "Pendente", "Recusou"]

STATUS_CORES = {  # (fundo, texto) — legíveis em tema claro e escuro
    "Confirmado": ("#DDF2C2", "#2F5A06"),
    "Em planejamento": ("#FFEBB8", "#7A4B00"),
    "Pendente": ("#FFD9D2", "#8F2412"),
    "Concluído": ("#DCD8F8", "#352A99"),
    "Recusou": ("#E6E6EC", "#44465A"),
}

# ── Estrutura interna das tabelas SQLite (estável) ──
CAMPOS = {
    "eventos": ["data", "cliente", "local", "convidados", "valor", "status"],
    "convidados": ["evento", "nome", "mesa", "acompanhantes", "contato", "restricao", "confirmacao"],
}

CAMPOS_DESTINO = {
    "eventos": {c: PERFIS_NEGOCIO[PERFIL_PADRAO]["rotulos"][c] for c in CAMPOS["eventos"]},
    "convidados": {c: PERFIS_NEGOCIO[PERFIL_PADRAO]["rotulos"][c] for c in CAMPOS["convidados"]},
}
OBRIGATORIOS = {"eventos": ["data", "cliente"], "convidados": ["nome"]}
ROTULOS = dict(PERFIS_NEGOCIO[PERFIL_PADRAO]["rotulos"])


def obter_vocabulario(cfg: dict | None = None) -> dict:
    """Retorna o vocabulário ativo combinando o Perfil de Negócio escolhido e ajustes manuais do empresário."""
    cfg = cfg or PADROES
    nome_perfil = cfg.get("perfil_negocio", PERFIL_PADRAO)
    if nome_perfil not in PERFIS_NEGOCIO:
        nome_perfil = PERFIL_PADRAO
    base = PERFIS_NEGOCIO[nome_perfil]
    custom = cfg.get("rotulos_custom") or {}

    rotulos = {**base["rotulos"], **custom.get("rotulos", {})}
    vocab = {
        **base,
        **{k: v for k, v in custom.items() if k != "rotulos" and v},
        "rotulos": rotulos,
        "campos_destino": {
            "eventos": {c: rotulos[c] for c in CAMPOS["eventos"]},
            "convidados": {c: rotulos[c] for c in CAMPOS["convidados"]},
        },
    }
    return vocab


def rotulo_pagina(chave_pg: str, cfg: dict | None = None) -> str:
    """Devolve o título visível no menu para uma chave de página."""
    v = obter_vocabulario(cfg)
    if chave_pg == "Eventos":
        return v["menu_ent1"]
    if chave_pg == "Convidados & Planilhas":
        return v["menu_ent2"]
    return chave_pg


# ── Importação: sugestão de mapeamento por nome de coluna (ampliado para qualquer negócio) ──
NAO_USAR = "— não importar —"
SINONIMOS = {
    "eventos": {
        "data": ["data", "dia", "date", "prazo", "vencimento", "emissao"],
        "cliente": ["cliente", "identificacao", "organizacao", "evento", "nome", "pedido", "projeto", "descricao"],
        "local": ["local", "salao", "espaco", "lugar", "categoria", "unidade", "filial", "canal", "escopo", "setor"],
        "convidados": ["convidados", "pessoas", "quantidade", "qtd", "lotacao", "volume", "itens", "horas", "equipe"],
        "valor": ["valor", "preco", "receita", "total", "reserva", "orcamento", "faturamento"],
        "status": ["status", "situacao", "etapa", "estado"],
    },
    "convidados": {
        "evento": ["evento", "cliente", "operacao", "pedido", "projeto", "origem", "vinculo"],
        "nome": ["nome", "convidado", "pessoa", "item", "responsavel", "tarefa", "registro"],
        "mesa": ["mesa", "grupo", "codigo", "categoria", "setor", "segmento", "etapa"],
        "acompanhantes": ["acompanhantes", "acomp", "extras", "adicional", "subtarefas", "dependentes"],
        "contato": ["contato", "email", "telefone", "celular", "whatsapp", "referencia"],
        "restricao": ["restricao", "alimentar", "dieta", "observacao", "observacoes", "obs", "nota", "especificacao"],
        "confirmacao": ["confirmacao", "confirmado", "rsvp", "presenca", "status", "situacao"],
    },
}
ALIAS_OPCAO = {
    "sim": "Confirmado",
    "confirmada": "Confirmado",
    "ativo": "Confirmado",
    "aprovado": "Confirmado",
    "ok": "Confirmado",
    "nao": "Recusou",
    "recusado": "Recusou",
    "recusada": "Recusou",
    "cancelado": "Recusou",
    "inativo": "Recusou",
    "aguardando": "Pendente",
    "emaberto": "Pendente",
    "planejamento": "Em planejamento",
    "concluido": "Concluído",
    "realizado": "Concluído",
    "entregue": "Concluído",
    "finalizado": "Concluído",
}

# Chaves de filtros da interface (limpas ao trocar de página se "lembrar filtros" estiver off)
FILTROS = ["dash_mes", "dash_status", "ev_busca", "ev_status", "cv_busca", "cv_evento", "cv_conf"]
