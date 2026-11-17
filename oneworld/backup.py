"""Backup completo do OneWorld em arquivo JSON: exportar, validar e importar.

Modos de importação:
  • substituir(...)        → troca todos os dados pelos do backup, preservando IDs e vínculos.
                             Antes, cria uma cópia de segurança do banco atual; tudo em uma única transação.
  • aplicar_mesclagem(...) → "Adicionar apenas o que falta": insere somente as ocorrências ausentes,
                             comparando o conteúdo completo de cada registro (sem o ID). Mantém as
                             configurações atuais e só une os campos personalizados compatíveis.

Este módulo não conhece a interface. Ele lê database.DB_PATH e database.BACKUP_DIR no momento de
cada chamada, para que os testes possam apontar para bancos temporários.

Ficam fora do backup: o arquivo .env, chaves de API e o banco público DFP (dfp_cia_aberta.db).
"""
from __future__ import annotations

import json
import math
import os
import re
import sqlite3
import tempfile
from collections import Counter
from contextlib import closing
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from . import backend as bk
from . import database as db
from .config import CAMPOS, PADROES

FORMATO = "oneworld-backup"
APLICATIVO = "OneWorld"
VERSAO_FORMATO = 1

# Tipos de coluna aceitos no arquivo
ID, TEXTO, NUMERO, EXTRAS, CHAVE_CFG, JSON_CFG = "id", "texto", "numero", "extras", "chave", "json"

# Estrutura das seis tabelas (deve acompanhar database.init_db)
ESQUEMA: dict[str, dict[str, str]] = {
    "eventos": {"id": ID, "data": TEXTO, "cliente": TEXTO, "local": TEXTO, "convidados": NUMERO,
                "valor": NUMERO, "status": TEXTO, "extras": EXTRAS},
    "convidados": {"id": ID, "evento": TEXTO, "nome": TEXTO, "mesa": TEXTO, "acompanhantes": NUMERO,
                   "contato": TEXTO, "restricao": TEXTO, "confirmacao": TEXTO, "extras": EXTRAS},
    "anotacoes": {"id": ID, "titulo": TEXTO, "descricao": TEXTO, "data": TEXTO},
    "relatorios_ia": {"id": ID, "data": TEXTO, "pergunta": TEXTO, "resposta": TEXTO},
    "arquivos": {"id": ID, "arquivo": TEXTO, "origem": TEXTO, "recebido_em": TEXTO, "destino": TEXTO,
                 "registros": NUMERO, "status": TEXTO},
    "config": {"chave": CHAVE_CFG, "valor": JSON_CFG},
}
TABELAS = tuple(ESQUEMA)
TABELAS_DADOS = tuple(t for t in TABELAS if t != "config")

NOMES_TABELAS = {
    "eventos": "Operações (eventos)",
    "convidados": "Cadastros (convidados)",
    "anotacoes": "Anotações",
    "relatorios_ia": "Relatórios de IA",
    "arquivos": "Histórico de arquivos importados",
    "config": "Configurações",
}

_CHAVES_TOPO = {"formato", "aplicativo", "versao_formato", "gerado_em", "contagens", "tabelas"}
_INT_MIN, _INT_MAX = -(2 ** 63), 2 ** 63 - 1
# Nomes que indicam segredo (nunca vão para o backup). "max_tokens" não casa: termina em "tokens".
_SEGREDO = re.compile(r"(^|_)(api_?key|apikey|key|chave|secret|segredo|senha|password|token)$", re.IGNORECASE)
# Nomes que um campo personalizado não pode ter (colidiriam com colunas nativas ao carregar a tabela)
_RESERVADOS = {bk.chave(c) for c in sum(CAMPOS.values(), [])} | {"id", "extras"}


# ── Erros (mensagens prontas para o usuário) ──
class BackupErro(Exception):
    """Falha de backup com mensagem compreensível."""


class BackupInvalido(BackupErro):
    """O arquivo não é um backup válido do OneWorld. Nada foi alterado."""


class CopiaSegurancaFalhou(BackupErro):
    """A cópia de segurança anterior à substituição falhou. Nada foi alterado."""


# ── Estruturas de resultado ──
@dataclass
class Backup:
    gerado_em: str
    tabelas: dict[str, list[dict]]
    caminho: Path | None = None

    @property
    def contagens(self) -> dict[str, int]:
        return {t: len(self.tabelas[t]) for t in TABELAS}

    @property
    def campos_personalizados(self) -> list[str]:
        for reg in self.tabelas["config"]:
            if reg["chave"] == "campos_personalizados":
                return list(json.loads(reg["valor"]))
        return []


@dataclass
class ResultadoExportacao:
    caminho: Path
    contagens: dict[str, int]
    segredos_removidos: int = 0


@dataclass
class ConflitoCampo:
    nome: str
    motivo: str


@dataclass
class PlanoMesclagem:
    adicionar: dict[str, list[dict]]
    ignorados: dict[str, int]
    campos_atuais: list[str]
    campos_novos: list[str]
    campos_existentes: list[str]
    conflitos: list[ConflitoCampo]

    @property
    def contagem_adicionar(self) -> dict[str, int]:
        return {t: len(r) for t, r in self.adicionar.items()}

    @property
    def total_adicionar(self) -> int:
        return sum(self.contagem_adicionar.values())

    @property
    def tem_algo_a_fazer(self) -> bool:
        return self.total_adicionar > 0 or bool(self.campos_novos)


@dataclass
class ResultadoImportacao:
    modo: str  # "substituir" ou "mesclar"
    adicionados: dict[str, int]
    ignorados: dict[str, int] = field(default_factory=dict)
    campos_adicionados: list[str] = field(default_factory=list)
    conflitos: list[ConflitoCampo] = field(default_factory=list)
    copia_seguranca: Path | None = None


# ── Conexões ──
def _caminho_banco() -> Path:
    caminho = Path(db.DB_PATH)
    if not caminho.is_file():
        raise BackupErro(f"O banco de dados do OneWorld não foi encontrado em: {caminho}")
    return caminho


def _conectar_leitura() -> sqlite3.Connection:
    # mode=ro: a leitura nunca cria nem altera o banco
    uri = _caminho_banco().resolve().as_uri() + "?mode=ro"
    return sqlite3.connect(uri, uri=True, isolation_level=None)


def _conectar_escrita() -> sqlite3.Connection:
    # isolation_level=None: a transação é controlada explicitamente (BEGIN IMMEDIATE / COMMIT / ROLLBACK)
    return sqlite3.connect(_caminho_banco(), isolation_level=None, timeout=10)


def _q(nome: str) -> str:
    return '"' + nome.replace('"', '""') + '"'


def _conferir_estrutura(con: sqlite3.Connection):
    """Garante que o banco tem exatamente as colunas conhecidas (evita backup que perca colunas novas)."""
    for tab, cols in ESQUEMA.items():
        reais = [r[1] for r in con.execute(f"PRAGMA table_info({_q(tab)})")]
        if not reais:
            raise BackupErro(f"A tabela '{tab}' não existe no banco atual.")
        if set(reais) != set(cols):
            raise BackupErro(
                f"A estrutura da tabela '{tab}' é diferente da esperada pelo backup "
                f"(colunas no banco: {', '.join(reais)}). Atualize oneworld/backup.py antes de continuar."
            )


def _ler_tabelas(con: sqlite3.Connection) -> dict[str, list[dict]]:
    saida: dict[str, list[dict]] = {}
    for tab, cols in ESQUEMA.items():
        ordem = "chave" if tab == "config" else "id"
        sql = f"SELECT {', '.join(_q(c) for c in cols)} FROM {_q(tab)} ORDER BY {_q(ordem)}"
        regs = []
        for linha in con.execute(sql):
            reg = dict(zip(cols, linha))
            for col, valor in reg.items():
                if isinstance(valor, (bytes, memoryview)):
                    raise BackupErro(f"{NOMES_TABELAS[tab]}: o campo '{col}' contém dados binários, "
                                     "que não podem ser salvos no backup.")
            regs.append(reg)
        saida[tab] = regs
    return saida


# ── Validação ──
def _carregar_json(texto: str):
    def sem_duplicadas(pares):
        obj = {}
        for k, v in pares:
            if k in obj:
                raise BackupInvalido(f"O arquivo contém a chave '{k}' repetida no mesmo objeto.")
            obj[k] = v
        return obj

    def sem_constantes(nome):
        raise BackupInvalido(f"O arquivo contém o valor numérico inválido '{nome}'.")

    try:
        return json.loads(texto, object_pairs_hook=sem_duplicadas, parse_constant=sem_constantes)
    except json.JSONDecodeError as e:
        raise BackupInvalido(f"O arquivo não é um JSON válido (linha {e.lineno}, coluna {e.colno}).") from e
    except RecursionError as e:
        raise BackupInvalido("O arquivo tem uma estrutura aninhada demais para ser um backup.") from e


def _tipo(v) -> str:
    if v is None:
        return "vazio (null)"
    if isinstance(v, bool):
        return "verdadeiro/falso"
    if isinstance(v, (int, float)):
        return "número"
    if isinstance(v, str):
        return "texto"
    if isinstance(v, list):
        return "lista"
    if isinstance(v, dict):
        return "objeto"
    return type(v).__name__


def _texto_valido(v, onde: str):
    if not isinstance(v, str):
        raise BackupInvalido(f"{onde}: esperado texto, encontrado {_tipo(v)}.")
    try:
        v.encode("utf-8")
    except UnicodeEncodeError as e:
        raise BackupInvalido(f"{onde}: o texto contém caracteres inválidos.") from e


def _validar_valor(tipo: str, v, onde: str):
    if tipo == ID:
        if isinstance(v, bool) or not isinstance(v, int) or not 1 <= v <= _INT_MAX:
            raise BackupInvalido(f"{onde}: o ID deve ser um número inteiro positivo (encontrado {_tipo(v)}).")
    elif tipo == TEXTO:
        if v is not None:
            _texto_valido(v, onde)
    elif tipo == NUMERO:
        if v is None:
            return
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            raise BackupInvalido(f"{onde}: esperado número, encontrado {_tipo(v)}.")
        if isinstance(v, int) and not _INT_MIN <= v <= _INT_MAX:
            raise BackupInvalido(f"{onde}: número inteiro fora do intervalo suportado.")
        if isinstance(v, float) and not math.isfinite(v):
            raise BackupInvalido(f"{onde}: número inválido.")
    elif tipo == EXTRAS:
        if v is None or v == "":  # o sistema trata ambos como "sem campos extras" ao carregar
            return
        _texto_valido(v, onde)
        try:
            obj = json.loads(v)
        except (json.JSONDecodeError, RecursionError) as e:
            raise BackupInvalido(f"{onde}: os campos extras não são um JSON válido.") from e
        if not isinstance(obj, dict):
            raise BackupInvalido(f"{onde}: os campos extras devem ser um objeto JSON.")
    elif tipo == CHAVE_CFG:
        _texto_valido(v, onde)
        if not v:
            raise BackupInvalido(f"{onde}: a chave de configuração está vazia.")
    elif tipo == JSON_CFG:
        _texto_valido(v, onde)
        try:
            json.loads(v)
        except (json.JSONDecodeError, RecursionError) as e:
            raise BackupInvalido(f"{onde}: o valor da configuração não é um JSON válido.") from e


def _validar_tabela(tab: str, regs) -> list[dict]:
    nome = NOMES_TABELAS[tab]
    if not isinstance(regs, list):
        raise BackupInvalido(f"{nome}: esperada uma lista de registros, encontrado {_tipo(regs)}.")
    cols = ESQUEMA[tab]
    esperadas = set(cols)
    unicos = set()
    col_unica = "chave" if tab == "config" else "id"
    for i, reg in enumerate(regs, 1):
        onde = f"{nome}, registro {i}"
        if not isinstance(reg, dict):
            raise BackupInvalido(f"{onde}: esperado um objeto, encontrado {_tipo(reg)}.")
        faltando = sorted(esperadas - reg.keys())
        sobrando = sorted(reg.keys() - esperadas)
        if faltando:
            raise BackupInvalido(f"{onde}: faltam as colunas {', '.join(faltando)}.")
        if sobrando:
            raise BackupInvalido(f"{onde}: colunas desconhecidas: {', '.join(sobrando)}.")
        for col, tipo in cols.items():
            _validar_valor(tipo, reg[col], f"{onde}, campo '{col}'")
        if reg[col_unica] in unicos:
            raise BackupInvalido(f"{onde}: '{col_unica}' repetido ({reg[col_unica]}).")
        unicos.add(reg[col_unica])
    return regs


def _mesmo_tipo(v, padrao) -> bool:
    """bool e int são distintos aqui (em Python, True também é int)."""
    if isinstance(padrao, bool):
        return isinstance(v, bool)
    if isinstance(padrao, int):
        return isinstance(v, int) and not isinstance(v, bool)
    return isinstance(v, type(padrao))


def _validar_configuracoes(regs: list[dict]):
    """Confere o formato das configurações conhecidas, para não restaurar algo que quebre as telas."""
    for reg in regs:
        chave, valor = reg["chave"], json.loads(reg["valor"])
        onde = f"Configurações, chave '{chave}'"
        if chave == "campos_personalizados":
            if not isinstance(valor, list):
                raise BackupInvalido(f"{onde}: esperada uma lista de nomes.")
            for nome in valor:
                if not isinstance(nome, str) or not nome.strip():
                    raise BackupInvalido(f"{onde}: todo campo personalizado deve ter um nome em texto.")
            if len(set(valor)) != len(valor):
                raise BackupInvalido(f"{onde}: há nomes de campo repetidos.")
        elif chave == "llm":
            if not isinstance(valor, dict):
                raise BackupInvalido(f"{onde}: esperado um objeto.")
        elif chave == "config":
            if not isinstance(valor, dict):
                raise BackupInvalido(f"{onde}: esperado um objeto.")
            for k, padrao in PADROES.items():
                if k not in valor:
                    continue
                if not _mesmo_tipo(valor[k], padrao):
                    v = valor[k]
                    raise BackupInvalido(f"{onde}: a opção '{k}' tem tipo inválido ({_tipo(v)}).")


def validar(dados) -> Backup:
    """Valida integralmente o conteúdo de um backup já lido do JSON. Não acessa o banco."""
    if not isinstance(dados, dict) or dados.get("formato") != FORMATO:
        raise BackupInvalido("Este arquivo não é um backup do OneWorld (identificação ausente ou diferente).")
    faltando = sorted(_CHAVES_TOPO - dados.keys())
    sobrando = sorted(dados.keys() - _CHAVES_TOPO)
    if faltando:
        raise BackupInvalido(f"O backup está incompleto: faltam {', '.join(faltando)}.")
    if sobrando:
        raise BackupInvalido(f"O backup contém itens desconhecidos: {', '.join(sobrando)}.")
    if dados["aplicativo"] != APLICATIVO:
        raise BackupInvalido("Este arquivo não é um backup do OneWorld (aplicativo diferente).")

    versao = dados["versao_formato"]
    if isinstance(versao, bool) or not isinstance(versao, int):
        raise BackupInvalido("A versão do formato do backup é inválida.")
    if versao > VERSAO_FORMATO:
        raise BackupInvalido(f"Este backup foi gerado por uma versão mais nova do OneWorld (formato {versao}). "
                             f"Esta versão lê até o formato {VERSAO_FORMATO}.")
    if versao != VERSAO_FORMATO:
        raise BackupInvalido(f"Versão de formato do backup não suportada: {versao}.")

    gerado_em = dados["gerado_em"]
    try:
        datetime.fromisoformat(gerado_em)
    except (TypeError, ValueError) as e:
        raise BackupInvalido("A data de geração do backup é inválida.") from e

    tabelas = dados["tabelas"]
    if not isinstance(tabelas, dict):
        raise BackupInvalido("O backup não contém a seção de tabelas no formato esperado.")
    faltando = [t for t in TABELAS if t not in tabelas]
    sobrando = sorted(set(tabelas) - set(TABELAS))
    if faltando:
        raise BackupInvalido(f"O backup não contém as tabelas: {', '.join(faltando)}.")
    if sobrando:
        raise BackupInvalido(f"O backup contém tabelas desconhecidas: {', '.join(sobrando)}.")
    for tab in TABELAS:
        _validar_tabela(tab, tabelas[tab])
    _validar_configuracoes(tabelas["config"])

    contagens = dados["contagens"]
    if not isinstance(contagens, dict) or set(contagens) != set(TABELAS):
        raise BackupInvalido("As contagens do backup estão ausentes ou incompletas.")
    for tab in TABELAS:
        n = contagens[tab]
        if isinstance(n, bool) or not isinstance(n, int) or n != len(tabelas[tab]):
            raise BackupInvalido(f"{NOMES_TABELAS[tab]}: a quantidade de registros não confere com a "
                                 "informada no arquivo (o arquivo pode estar incompleto ou ter sido editado).")

    return Backup(gerado_em=gerado_em, tabelas={t: tabelas[t] for t in TABELAS})


def ler_backup(caminho) -> Backup:
    """Lê e valida um arquivo de backup. Somente leitura: não altera o banco."""
    p = Path(caminho)
    try:
        bruto = p.read_bytes()
    except FileNotFoundError as e:
        raise BackupInvalido(f"Arquivo não encontrado: {p}") from e
    except OSError as e:
        raise BackupInvalido(f"Não foi possível ler o arquivo: {e.strerror or e}") from e
    try:
        texto = bruto.decode("utf-8-sig")
    except UnicodeDecodeError as e:
        raise BackupInvalido("O arquivo não está em UTF-8; não parece um backup do OneWorld.") from e
    backup = validar(_carregar_json(texto))
    backup.caminho = p
    return backup


# ── Exportação ──
def _limpar_segredos(valor):
    if isinstance(valor, dict):
        limpo, removidos = {}, 0
        for k, v in valor.items():
            if _SEGREDO.search(str(k)):
                removidos += 1
                continue
            limpo[k], n = _limpar_segredos(v)
            removidos += n
        return limpo, removidos
    if isinstance(valor, list):
        itens = [_limpar_segredos(v) for v in valor]
        return [v for v, _ in itens], sum(n for _, n in itens)
    return valor, 0


def _config_sem_segredos(regs: list[dict]) -> tuple[list[dict], int]:
    """Remove das configurações qualquer item com nome de segredo. O texto dos demais fica intacto."""
    saida, removidos = [], 0
    for reg in regs:
        if _SEGREDO.search(reg["chave"]):
            removidos += 1
            continue
        try:
            valor = json.loads(reg["valor"])
        except (TypeError, ValueError):
            saida.append(reg)  # a validação da exportação apontará o problema
            continue
        limpo, n = _limpar_segredos(valor)
        if n:
            removidos += n
            reg = {**reg, "valor": json.dumps(limpo, ensure_ascii=False)}
        saida.append(reg)
    return saida, removidos


def _gravar_atomico(destino: Path, texto: str):
    """Grava em arquivo temporário na mesma pasta e só então renomeia: nunca deixa arquivo pela metade."""
    fd, tmp = tempfile.mkstemp(prefix=".oneworld_backup_", suffix=".tmp", dir=destino.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            f.write(texto)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, destino)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def exportar(caminho) -> ResultadoExportacao:
    """Exporta as seis tabelas para um arquivo JSON, com leitura consistente (uma única transação)."""
    destino = Path(caminho)
    if not destino.parent.is_dir():
        raise BackupErro(f"A pasta de destino não existe: {destino.parent}")

    with closing(_conectar_leitura()) as con:
        con.execute("BEGIN")  # todas as leituras abaixo enxergam o mesmo instante do banco
        try:
            _conferir_estrutura(con)
            tabelas = _ler_tabelas(con)
        finally:
            con.execute("ROLLBACK")

    tabelas["config"], removidos = _config_sem_segredos(tabelas["config"])
    dados = {
        "formato": FORMATO,
        "aplicativo": APLICATIVO,
        "versao_formato": VERSAO_FORMATO,
        "gerado_em": datetime.now().isoformat(timespec="seconds"),
        "contagens": {t: len(tabelas[t]) for t in TABELAS},
        "tabelas": tabelas,
    }
    try:
        validar(dados)  # garante que o arquivo gerado será aceito na importação
        texto = json.dumps(dados, ensure_ascii=False, indent=2, allow_nan=False)
    except (BackupInvalido, ValueError) as e:
        raise BackupErro(f"O banco contém um dado que não pode ser salvo no backup: {e}") from e

    try:
        _gravar_atomico(destino, texto)
    except OSError as e:
        raise BackupErro(f"Não foi possível gravar o arquivo de backup ({e.strerror or e}). "
                         "Nenhum arquivo foi criado ou alterado.") from e
    return ResultadoExportacao(caminho=destino, contagens=dados["contagens"], segredos_removidos=removidos)


# ── Comparação por conteúdo (modo "Adicionar apenas o que falta") ──
def _norm(v):
    """Forma canônica de um valor. Só equipara o que é seguramente igual (ex.: 10 e 10.0)."""
    if v is None:
        return ("null",)
    if isinstance(v, bool):
        return ("bool", v)
    if isinstance(v, int):
        return ("num", v)
    if isinstance(v, float):
        if math.isnan(v):
            return ("nan",)
        if math.isinf(v):
            return ("inf", v > 0)
        return ("num", int(v)) if v.is_integer() else ("num", v)
    if isinstance(v, str):
        return ("txt", v)  # texto exato: espaços e maiúsculas contam
    if isinstance(v, dict):
        return ("obj", tuple(sorted((str(k), _norm(x)) for k, x in v.items())))
    if isinstance(v, list):
        return ("lista", tuple(_norm(x) for x in v))
    return ("outro", repr(v))


def _norm_extras(v):
    """Campos extras: compara o conteúdo JSON, ignorando ordem das chaves e formatação."""
    if isinstance(v, str):
        try:
            return ("json", _norm(json.loads(v)))
        except (ValueError, RecursionError):
            return ("txt", v)
    return _norm(v)


def _impressao(tab: str, reg: dict) -> tuple:
    return tuple(_norm_extras(reg[c]) if t == EXTRAS else _norm(reg[c])
                 for c, t in ESQUEMA[tab].items() if t != ID)


def _campos_atuais(regs_config: list[dict]) -> list[str]:
    for reg in regs_config:
        if reg["chave"] == "campos_personalizados":
            try:
                valor = json.loads(reg["valor"])
            except (TypeError, ValueError) as e:
                raise BackupErro("A lista atual de campos personalizados está corrompida.") from e
            if not isinstance(valor, list) or not all(isinstance(x, str) for x in valor):
                raise BackupErro("A lista atual de campos personalizados está corrompida.")
            return valor
    return []


def _analisar_campos(atuais: list[str], do_backup: list[str]):
    """Separa os campos do backup em: já existentes, novos compatíveis e conflitos."""
    por_chave = {bk.chave(c): c for c in atuais}
    novos, existentes, conflitos = [], [], []
    for nome in do_backup:
        if nome in atuais:
            existentes.append(nome)
            continue
        k = bk.chave(nome)
        if not k:
            conflitos.append(ConflitoCampo(nome, "o nome não tem letras nem números que o identifiquem"))
        elif k in _RESERVADOS:
            conflitos.append(ConflitoCampo(nome, "tem o mesmo nome de uma coluna padrão do sistema"))
        elif k in por_chave:
            conflitos.append(ConflitoCampo(
                nome, f"é parecido com o campo '{por_chave[k]}', mas não idêntico (difere em maiúsculas, "
                      "acentos, espaços ou pontuação); unir os dois poderia misturar valores diferentes"))
        else:
            novos.append(nome)
            por_chave[k] = nome
    return novos, existentes, conflitos


def _montar_plano(backup: Backup, atuais: dict[str, list[dict]]) -> PlanoMesclagem:
    adicionar, ignorados = {}, {}
    for tab in TABELAS_DADOS:
        # Conta ocorrências: se o banco tem 1 cópia e o backup tem 3 idênticas, faltam 2.
        restantes = Counter(_impressao(tab, r) for r in atuais[tab])
        add, ign = [], 0
        for reg in backup.tabelas[tab]:
            fp = _impressao(tab, reg)
            if restantes[fp] > 0:
                restantes[fp] -= 1
                ign += 1
            else:
                add.append(reg)
        adicionar[tab], ignorados[tab] = add, ign
    campos_atuais = _campos_atuais(atuais["config"])
    novos, existentes, conflitos = _analisar_campos(campos_atuais, backup.campos_personalizados)
    return PlanoMesclagem(adicionar, ignorados, campos_atuais, novos, existentes, conflitos)


def planejar_mesclagem(backup: Backup) -> PlanoMesclagem:
    """Prévia do modo "Adicionar apenas o que falta". Somente leitura."""
    with closing(_conectar_leitura()) as con:
        con.execute("BEGIN")
        try:
            _conferir_estrutura(con)
            atuais = _ler_tabelas(con)
        finally:
            con.execute("ROLLBACK")
    return _montar_plano(backup, atuais)


def contagens_atuais() -> dict[str, int]:
    """Quantidade de registros atualmente no banco, por tabela. Somente leitura."""
    with closing(_conectar_leitura()) as con:
        return {t: con.execute(f"SELECT COUNT(*) FROM {_q(t)}").fetchone()[0] for t in TABELAS}


# ── Gravação ──
def _gravar_tabela(con: sqlite3.Connection, tab: str, regs: list[dict], com_id: bool):
    cols = [c for c, t in ESQUEMA[tab].items() if com_id or t != ID]
    sql = (f"INSERT INTO {_q(tab)}({', '.join(_q(c) for c in cols)}) "
           f"VALUES({', '.join('?' * len(cols))})")
    con.executemany(sql, [[r[c] for c in cols] for r in regs])


def _em_transacao(acao, mensagem_falha: str):
    """Executa acao(con) em uma única transação; qualquer erro desfaz tudo."""
    with closing(_conectar_escrita()) as con:
        try:
            con.execute("BEGIN IMMEDIATE")
        except sqlite3.Error as e:
            raise BackupErro(f"O banco está em uso e não pôde ser bloqueado para gravação ({e}). "
                             "Nenhum dado foi alterado.") from e
        try:
            resultado = acao(con)
            con.execute("COMMIT")
            return resultado
        except BaseException as e:
            if con.in_transaction:  # o SQLite pode já ter desfeito a transação sozinho
                con.execute("ROLLBACK")
            if isinstance(e, BackupErro) or not isinstance(e, Exception):
                raise
            raise BackupErro(f"{mensagem_falha} Detalhe técnico: {e}") from e


def criar_copia_seguranca() -> Path:
    """Copia o banco atual para backups/ e confere a integridade da cópia."""
    pasta = Path(db.BACKUP_DIR)
    destino = pasta / f"oneworld_antes_da_restauracao_{datetime.now():%Y%m%d_%H%M%S_%f}.db"
    try:
        pasta.mkdir(parents=True, exist_ok=True)
        if destino.exists():
            raise FileExistsError(f"já existe um arquivo com o nome {destino.name}")
        with closing(_conectar_leitura()) as origem, closing(sqlite3.connect(destino)) as copia:
            origem.backup(copia)
        uri = destino.resolve().as_uri() + "?mode=ro"
        with closing(sqlite3.connect(uri, uri=True)) as conferir:
            situacao = conferir.execute("PRAGMA integrity_check").fetchone()[0]
        if situacao != "ok":
            raise sqlite3.DatabaseError("a verificação de integridade da cópia falhou")
    except (OSError, sqlite3.Error, BackupErro) as e:
        try:
            destino.unlink(missing_ok=True)
        except OSError:
            pass
        raise CopiaSegurancaFalhou(
            f"Não foi possível criar a cópia de segurança do banco atual ({e}). "
            "A restauração foi interrompida e nenhum dado foi alterado."
        ) from e
    return destino


def substituir(backup: Backup) -> ResultadoImportacao:
    """Troca todos os dados (inclusive configurações) pelos do backup, preservando IDs."""
    copia = criar_copia_seguranca()

    def acao(con):
        _conferir_estrutura(con)
        for tab in TABELAS:
            con.execute(f"DELETE FROM {_q(tab)}")
            _gravar_tabela(con, tab, backup.tabelas[tab], com_id=True)

    _em_transacao(acao, "A restauração falhou e foi desfeita; os dados atuais continuam como estavam.")
    return ResultadoImportacao(modo="substituir", adicionados=backup.contagens, copia_seguranca=copia)


def aplicar_mesclagem(backup: Backup) -> ResultadoImportacao:
    """Insere somente as ocorrências que faltam (novos IDs) e une os campos personalizados compatíveis.

    A comparação é refeita dentro da transação, sobre o estado real do banco naquele momento.
    Campos em conflito NÃO entram na lista de campos; os valores deles nos registros inseridos são
    gravados exatamente como estão no backup (dentro dos campos extras).
    """
    def acao(con):
        _conferir_estrutura(con)
        plano = _montar_plano(backup, _ler_tabelas(con))
        for tab in TABELAS_DADOS:
            _gravar_tabela(con, tab, plano.adicionar[tab], com_id=False)
        if plano.campos_novos:
            con.execute(
                "INSERT INTO config(chave,valor) VALUES(?,?) "
                "ON CONFLICT(chave) DO UPDATE SET valor=excluded.valor",
                ("campos_personalizados",
                 json.dumps(plano.campos_atuais + plano.campos_novos, ensure_ascii=False)),
            )
        return plano

    plano = _em_transacao(acao, "A importação falhou e foi desfeita; nenhum dado foi alterado.")
    return ResultadoImportacao(
        modo="mesclar",
        adicionados=plano.contagem_adicionar,
        ignorados=dict(plano.ignorados),
        campos_adicionados=list(plano.campos_novos),
        conflitos=list(plano.conflitos),
    )
