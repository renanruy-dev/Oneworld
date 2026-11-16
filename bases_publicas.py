"""Bases públicas (dados abertos: CVM, dados.gov.br, IBGE...) usadas no OneWorld. Não conhece PyQt.

Duas portas de entrada, ambas acionadas pela tela Dados Externos:
  1. A base DFP da CVM (dfp.py): `instalar_dfp()` valida e instala um novo dfp_cia_aberta_AAAA.zip.
  2. Bases genéricas (CSV, TSV, TXT, XLSX, JSON ou ZIP com um desses): `pre_visualizar()` + `adicionar_base()`
     gravam a tabela em um SQLite próprio (bases_publicas.db), separado do oneworld.db e dos backups.

Depois de entrar, as bases ficam disponíveis (a) no Dashboard BI, via `fontes_bi()`, e (b) como contexto
opcional da IA externa, via `contexto_ia()` — só para as bases que o usuário marcar explicitamente.
"""
import csv
import os
import re
import shutil
import sqlite3
import threading
import zipfile
from contextlib import closing, contextmanager
from datetime import datetime
from pathlib import Path

import pandas as pd

from . import dfp
from .config import RAIZ

BP_DB_PATH = RAIZ / "bases_publicas.db"
LIMITE_LINHAS = 5_000_000      # teto de linhas por base (protege memória/disco)
TAMANHO_BLOCO = 100_000        # linhas lidas por vez na importação
EXTENSOES = (".csv", ".tsv", ".txt", ".xlsx", ".json")
MAX_CONTEXTO_IA = 6000         # caracteres por execução, somando todas as bases marcadas
ORIGENS_SUGERIDAS = ["CVM", "dados.gov.br", "IBGE", "Banco Central", "Receita Federal", "Outra"]


class ErroBase(ValueError):
    """Arquivo ou operação inválida; a mensagem é segura para mostrar ao usuário."""


# ══════════════════════════════ 1. LEITURA ══════════════════════════════
def _nome(origem):
    return Path(str(origem)).name


@contextmanager
def _abrir(origem, membro=None):
    """Abre o arquivo (ou o membro de um ZIP) em binário."""
    if membro:
        with zipfile.ZipFile(origem) as zf, zf.open(membro) as fh:
            yield fh
    else:
        with open(origem, "rb") as fh:
            yield fh


def membros_zip(origem):
    """Arquivos tabulares dentro de um ZIP, do menor para o maior: [(nome, tamanho_bytes)]."""
    try:
        with zipfile.ZipFile(origem) as zf:
            itens = [(i.filename, i.file_size) for i in zf.infolist()
                     if not i.is_dir() and i.filename.lower().endswith(EXTENSOES)
                     and not Path(i.filename).name.startswith(("._", "~$"))]
    except zipfile.BadZipFile as ex:
        raise ErroBase("O arquivo ZIP está corrompido ou incompleto.") from ex
    return sorted(itens, key=lambda m: m[1])


def _detectar_csv(amostra):
    """(codificação, separador) a partir dos primeiros bytes. Dados abertos brasileiros costumam vir em
    latin-1 com ';'; planilhas exportadas hoje costumam vir em UTF-8 com ','."""
    corte = amostra[:-4] if len(amostra) > 4096 else amostra  # evita cortar um caractere multibyte ao meio
    try:
        texto, cod = corte.decode("utf-8-sig"), "utf-8-sig"
    except UnicodeDecodeError:
        texto, cod = amostra.decode("latin-1"), "latin-1"
    linhas = [ln for ln in texto.splitlines() if ln.strip()][:30]
    if not linhas:
        raise ErroBase("O arquivo está vazio.")
    try:
        sep = csv.Sniffer().sniff("\n".join(linhas), delimiters=";,\t|").delimiter
    except csv.Error:
        sep = max(";,\t|", key=linhas[0].count)
        if not linhas[0].count(sep):
            sep = ","
    return cod, sep


def _ler_json(fh):
    import json
    dados = json.loads(fh.read().decode("utf-8-sig"))
    if isinstance(dados, dict):
        dados = next((v for v in dados.values() if isinstance(v, list)), [dados])
    df = pd.json_normalize(dados)
    df.columns = [str(c) for c in df.columns]
    return df.astype(object).where(df.notna(), None).map(lambda v: None if v is None else str(v))


def _blocos(origem, membro=None, bloco=None):
    """Gera (DataFrame_de_texto, info) em blocos. info = {'codificacao', 'separador'} (None se não se aplica).
    Tudo é lido como texto; o tipo é decidido depois por `inferir_tipos`."""
    bloco = bloco or TAMANHO_BLOCO
    nome = (membro or _nome(origem)).lower()
    if nome.endswith(".xlsx"):
        from . import planilha as excel  # import tardio: só quem usa XLSX precisa do openpyxl
        with _abrir(origem, membro) as fh:
            df = excel.ler_planilha(fh.read())
        yield df, {"codificacao": None, "separador": None}
    elif nome.endswith(".json"):
        with _abrir(origem, membro) as fh:
            yield _ler_json(fh), {"codificacao": None, "separador": None}
    else:
        with _abrir(origem, membro) as fh:
            cod, sep = _detectar_csv(fh.read(1 << 20))
        info = {"codificacao": cod, "separador": sep}
        with _abrir(origem, membro) as fh:
            try:
                for df in pd.read_csv(fh, sep=sep, encoding=cod, dtype=str, chunksize=bloco,
                                      on_bad_lines="skip", skipinitialspace=True):
                    yield df, info
            except (pd.errors.ParserError, pd.errors.EmptyDataError) as ex:
                raise ErroBase(f"Não foi possível interpretar o arquivo como tabela: {ex}") from ex


def _limpar_nomes(colunas):
    """Nomes de coluna textuais, sem vazios nem repetidos (exigência do BI)."""
    vistos, out = {}, []
    for i, c in enumerate(colunas, 1):
        n = re.sub(r"\s+", " ", str(c)).strip() or f"coluna_{i}"
        vistos[n] = vistos.get(n, 0) + 1
        out.append(n if vistos[n] == 1 else f"{n}_{vistos[n]}")
    return out


# ── Tipos ──
_RE_INT = re.compile(r"-?\d+")
_RE_PONTO = re.compile(r"-?\d+(\.\d+)?")
_RE_VIRG = re.compile(r"-?(\d{1,3}(\.\d{3})+|\d+)(,\d+)?")
_RE_CODIGO = re.compile(r"(^|[^a-z])(cd|cod|codigo|cnpj|cpf|cep|id|ibge|uf|ddd|ncm|cnae|isin|matricula)([^a-z]|$)")


def _sem_acento(s):
    import unicodedata
    return unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower()


def _para_numero(vals, nome_coluna):
    """Série numérica se TODOS os valores não vazios forem números sem ambiguidade; senão None.
    Colunas de código/identificador e números com zeros à esquerda ('007', '3.10' em plano de contas)
    ficam como texto: converter corromperia o dado."""
    if _RE_CODIGO.search(_sem_acento(nome_coluna)):
        return None
    v = vals.str.strip()
    if v.map(lambda x: bool(_RE_INT.fullmatch(x)) and (len(x.lstrip("-")) > 1 and x.lstrip("-")[0] == "0")).any():
        return None  # zeros à esquerda
    if v.str.contains(",", regex=False).any():
        if not v.map(lambda x: bool(_RE_VIRG.fullmatch(x))).all():
            return None
        return pd.to_numeric(v.str.replace(".", "", regex=False).str.replace(",", ".", regex=False), errors="coerce")
    if not v.map(lambda x: bool(_RE_PONTO.fullmatch(x))).all():
        return None
    if v.str.contains(r"^-?0\d", regex=True).any():
        return None
    return pd.to_numeric(v, errors="coerce")


def inferir_tipos(df, tipos=None):
    """Converte colunas de texto que são claramente numéricas. Datas ficam como texto (o BI converte sob
    comando do usuário). Retorna (df, tipos) onde tipos = {coluna: 'numero'|'texto'}; passe `tipos` de um
    bloco anterior para manter a mesma decisão nos blocos seguintes (valores que não convertem viram vazio)."""
    df = df.copy()
    df.columns = _limpar_nomes(df.columns)
    df = df.astype(object).map(lambda v: None if isinstance(v, str) and not v.strip() else v)
    decididos = {}
    for c in df.columns:
        s = df[c].dropna().astype(str)
        if tipos is not None:
            num = tipos.get(c) == "numero"
            if num:
                df[c] = _forcar_numero(df[c])
            decididos[c] = tipos.get(c, "texto")
            continue
        n = _para_numero(s, c) if len(s) else None
        if n is not None:
            df[c] = n.reindex(df.index)
            decididos[c] = "numero"
        else:
            decididos[c] = "texto"
    return df, decididos


def _forcar_numero(serie):
    s = serie.dropna().astype(str).str.strip()
    if s.str.contains(",", regex=False).any():
        s = s.str.replace(".", "", regex=False).str.replace(",", ".", regex=False)
    return pd.to_numeric(s, errors="coerce").reindex(serie.index)


def pre_visualizar(origem, membro=None, linhas=200):
    """Lê só o começo do arquivo para o usuário conferir antes de gravar. Não grava nada.
    Retorna dict(df, codificacao, separador, colunas, membros, dfp_ano)."""
    origem = Path(origem)
    if not origem.is_file():
        raise ErroBase("Arquivo não encontrado.")
    nome = origem.name.lower()
    res = {"df": pd.DataFrame(), "codificacao": None, "separador": None, "colunas": {}, "membros": [],
           "dfp_ano": None}
    if nome.endswith(".zip"):
        ano = detectar_dfp(origem)
        if ano:
            res["dfp_ano"] = ano
            return res
        res["membros"] = membros_zip(origem)
        if not res["membros"]:
            raise ErroBase("O ZIP não contém CSV, TSV, TXT, XLSX ou JSON.")
        membro = membro or res["membros"][0][0]
    elif not nome.endswith(EXTENSOES):
        raise ErroBase("Formato não suportado. Use CSV, TSV, TXT, XLSX, JSON ou um ZIP com um desses.")
    try:
        df, info = next(_blocos(origem, membro, bloco=max(linhas, 1)))
    except StopIteration:
        raise ErroBase("O arquivo não tem linhas de dados.") from None
    df, tipos = inferir_tipos(df.head(linhas))
    if df.empty or not len(df.columns):
        raise ErroBase("O arquivo não tem linhas de dados.")
    res.update(df=df, colunas=tipos, codificacao=info["codificacao"], separador=info["separador"],
               membro=membro)
    return res


# ══════════════════════════════ 2. CATÁLOGO ══════════════════════════════
def _con(criar=True):
    if not criar and not BP_DB_PATH.is_file():
        return None
    con = sqlite3.connect(BP_DB_PATH)
    con.execute("""CREATE TABLE IF NOT EXISTS bp_catalogo(
        id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT UNIQUE NOT NULL, descricao TEXT, origem TEXT,
        arquivo TEXT, linhas INTEGER, colunas INTEGER, adicionada_em TEXT, usar_na_ia INTEGER DEFAULT 0,
        tipos TEXT)""")
    return con


def listar():
    """Bases adicionadas pelo usuário (DataFrame; vazio se não houver)."""
    cols = ["id", "nome", "descricao", "origem", "arquivo", "linhas", "colunas", "adicionada_em", "usar_na_ia"]
    con = _con(criar=False)
    if con is None:
        return pd.DataFrame(columns=cols)
    with closing(con):
        return pd.read_sql_query(f"SELECT {','.join(cols)} FROM bp_catalogo ORDER BY id DESC", con)


def _tabela(id_):
    return f"bp_{int(id_)}"


def carregar(id_, limite=None):
    """DataFrame de uma base adicionada (opcionalmente só as primeiras `limite` linhas)."""
    con = _con(criar=False)
    if con is None:
        raise ErroBase("Base não encontrada.")
    with closing(con):
        if not con.execute("SELECT 1 FROM bp_catalogo WHERE id=?", (int(id_),)).fetchone():
            raise ErroBase("Base não encontrada.")
        sql = f'SELECT * FROM "{_tabela(id_)}"' + (f" LIMIT {int(limite)}" if limite else "")
        return pd.read_sql_query(sql, con)


def remover(id_):
    con = _con(criar=False)
    if con is None:
        return
    with closing(con):
        con.execute(f'DROP TABLE IF EXISTS "{_tabela(id_)}"')
        con.execute("DELETE FROM bp_catalogo WHERE id=?", (int(id_),))
        con.commit()


def definir_uso_ia(id_, usar):
    with closing(_con()) as con:
        con.execute("UPDATE bp_catalogo SET usar_na_ia=? WHERE id=?", (1 if usar else 0, int(id_)))
        con.commit()


def nome_sugerido(origem):
    base = re.sub(r"[_\-]+", " ", Path(str(origem)).stem).strip()
    return base[:80] or "Base pública"


# ══════════════════════════════ 3. IMPORTAÇÃO ══════════════════════════════
def adicionar_base(origem, nome, descricao="", origem_dados="", membro=None, usar_na_ia=False):
    """Importa o arquivo para uma tabela própria e registra no catálogo. Síncrono (use
    `adicionar_em_segundo_plano` na interface). Retorna dict(id, nome, linhas, colunas, avisos)."""
    origem = Path(origem)
    nome = re.sub(r"\s+", " ", (nome or "").strip())
    if not nome:
        raise ErroBase("Informe um nome para a base.")
    if not origem.is_file():
        raise ErroBase("Arquivo não encontrado.")
    if origem.name.lower().endswith(".zip"):
        if detectar_dfp(origem):
            raise ErroBase("Este ZIP é a base DFP da CVM: use 'Instalar/atualizar base DFP'.")
        if membro is None:
            ms = membros_zip(origem)
            if not ms:
                raise ErroBase("O ZIP não contém CSV, TSV, TXT, XLSX ou JSON.")
            membro = ms[0][0]
    with closing(_con()) as con:
        if con.execute("SELECT 1 FROM bp_catalogo WHERE nome=? COLLATE NOCASE", (nome,)).fetchone():
            raise ErroBase(f"Já existe uma base chamada '{nome}'. Escolha outro nome.")
        id_ = con.execute(
            "INSERT INTO bp_catalogo(nome,descricao,origem,arquivo,linhas,colunas,adicionada_em,usar_na_ia) "
            "VALUES(?,?,?,?,0,0,?,?)",
            (nome, descricao.strip(), (origem_dados or "").strip(), origem.name,
             datetime.now().strftime("%d/%m/%Y %H:%M"), 1 if usar_na_ia else 0)).lastrowid
        con.commit()
        tabela, total, tipos, perdidos, truncou, colunas = _tabela(id_), 0, None, 0, False, 0
        try:
            for bloco, _ in _blocos(origem, membro):
                if tipos is None:
                    bloco, tipos = inferir_tipos(bloco)
                    colunas = len(bloco.columns)
                else:
                    bloco.columns = _limpar_nomes(bloco.columns)
                    antes = {c: bloco[c].notna().sum() for c in tipos if tipos[c] == "numero" and c in bloco}
                    bloco, _ = inferir_tipos(bloco, tipos)
                    perdidos += sum(antes[c] - bloco[c].notna().sum() for c in antes)
                if total + len(bloco) > LIMITE_LINHAS:
                    bloco, truncou = bloco.head(LIMITE_LINHAS - total), True
                if len(bloco):
                    bloco.to_sql(tabela, con, if_exists="append", index=False)
                    total += len(bloco)
                if truncou:
                    break
            if not total:
                raise ErroBase("O arquivo não tem linhas de dados.")
            con.execute("UPDATE bp_catalogo SET linhas=?, colunas=?, tipos=? WHERE id=?",
                        (total, colunas, repr(tipos), id_))
            con.commit()
        except BaseException:
            con.rollback()
            con.execute(f'DROP TABLE IF EXISTS "{tabela}"')
            con.execute("DELETE FROM bp_catalogo WHERE id=?", (id_,))
            con.commit()
            raise
    avisos = []
    if truncou:
        avisos.append(f"A base tinha mais de {LIMITE_LINHAS:,} linhas; só as primeiras foram importadas."
                      .replace(",", "."))
    if perdidos:
        avisos.append(f"{perdidos} valor(es) não numérico(s) em colunas numéricas ficaram vazios.")
    return {"id": id_, "nome": nome, "linhas": total, "colunas": colunas, "avisos": avisos}


_imp_lock = threading.Lock()
_imp_estado = {"estado": "ocioso", "nome": "", "arquivo": "", "resultado": None, "erro": ""}


def estado_importacao():
    with _imp_lock:
        return dict(_imp_estado)


def limpar_estado_importacao():
    with _imp_lock:
        _imp_estado.update(estado="ocioso", nome="", arquivo="", resultado=None, erro="")


def adicionar_em_segundo_plano(*args, **kwargs):
    """Mesma assinatura de `adicionar_base`, mas sem travar a interface. Acompanhe por `estado_importacao()`:
    ocioso | importando | ok | erro. Retorna False se já houver uma importação em andamento."""
    with _imp_lock:
        if _imp_estado["estado"] == "importando":
            return False
        _imp_estado.update(estado="importando", nome=(args[1] if len(args) > 1 else kwargs.get("nome", "")),
                           arquivo=_nome(args[0] if args else kwargs.get("origem", "")), resultado=None, erro="")

    def trabalho():
        try:
            r = adicionar_base(*args, **kwargs)
            with _imp_lock:
                _imp_estado.update(estado="ok", resultado=r)
        except ErroBase as ex:
            with _imp_lock:
                _imp_estado.update(estado="erro", erro=str(ex))
        except Exception as ex:  # noqa: BLE001 — nunca derruba a interface
            with _imp_lock:
                _imp_estado.update(estado="erro", erro=f"{type(ex).__name__}: {ex}"[:300])

    threading.Thread(target=trabalho, name="oneworld-importacao", daemon=True).start()
    return True


# ══════════════════════════════ 4. BASE DFP (CVM) ══════════════════════════════
_RE_DFP_PRINCIPAL = re.compile(r"dfp_cia_aberta_(\d{4})\.(csv|xlsx)")


def detectar_dfp(caminho):
    """Ano (str) se o ZIP é um pacote DFP da CVM (cadastro + demonstrações); senão None."""
    try:
        with zipfile.ZipFile(caminho) as zf:
            nomes = [n.rsplit("/", 1)[-1] for n in zf.namelist()]
    except (zipfile.BadZipFile, OSError):
        return None
    for n in nomes:
        m = _RE_DFP_PRINCIPAL.fullmatch(n)
        if m and any(re.fullmatch(rf"dfp_cia_aberta_(BPA|BPP|DRE)_(con|ind)_{m.group(1)}\.(csv|xlsx)", x)
                     for x in nomes):
            return m.group(1)
    return None


def instalar_dfp(caminho):
    """Valida e instala um novo pacote DFP da CVM (dfp_cia_aberta_AAAA.zip) e dispara a reconstrução da base
    em segundo plano. Retorna dict(ok, mensagem, ano). Nunca levanta exceção."""
    def falha(msg):
        return {"ok": False, "mensagem": msg, "ano": None}

    caminho = Path(caminho)
    if not caminho.is_file():
        return falha("Arquivo não encontrado.")
    ano = detectar_dfp(caminho)
    if not ano:
        return falha("Este ZIP não parece o pacote DFP da CVM. Ele precisa conter dfp_cia_aberta_AAAA.csv e as "
                     "demonstrações (BPA, BPP, DRE). Baixe em dados.cvm.gov.br → Cia. Abertas: Documentos → DFP.")
    if os.environ.get("ONEWORLD_DFP_ZIP") or dfp._env().get("ONEWORLD_DFP_ZIP"):
        return falha("A variável ONEWORLD_DFP_ZIP está definida e fixa a fonte da DFP; remova-a (ou aponte para "
                     "este arquivo) para instalar por aqui.")
    if dfp.status().get("atualizando"):
        return falha("A base DFP está sendo carregada agora. Aguarde terminar e tente de novo.")
    fontes = dfp.listar_fontes()
    if fontes and fontes[0][0] > ano:
        return falha(f"Já existe a DFP de {fontes[0][0]}, mais recente que a deste arquivo ({ano}). "
                     "A OneWorld usa sempre o exercício mais recente.")
    mesmo_ano = next((p for a, p in fontes if a == ano and p.is_file()), None)
    destino = mesmo_ano or (RAIZ / "dados" / f"dfp_cia_aberta_{ano}.zip")
    try:
        if destino.resolve() != caminho.resolve():
            destino.parent.mkdir(parents=True, exist_ok=True)
            tmp = destino.with_name(destino.name + ".tmp")
            shutil.copyfile(caminho, tmp)
            os.replace(tmp, destino)
        dfp.iniciar(forcar=True)
    except OSError as ex:
        return falha(f"Não foi possível copiar o arquivo: {ex}")
    return {"ok": True, "ano": ano,
            "mensagem": f"DFP {ano} instalada. A base está sendo carregada em segundo plano."}


# ══════════════════════════════ 5. USO: BI e IA ══════════════════════════════
def _rotulo_cvm():
    return f"CVM DFP {dfp.metadados().get('ano', '')}".strip()


def fontes_bi():
    """Fontes públicas oferecidas ao Dashboard BI: {rótulo: ('publica', chave)}. Leitura sob demanda."""
    out = {}
    try:
        if dfp.pronta():
            r = _rotulo_cvm()
            out[f"Base pública: {r} — Indicadores por companhia"] = ("publica", "cvm:indicadores")
            out[f"Base pública: {r} — Cadastro de companhias"] = ("publica", "cvm:cadastro")
    except (sqlite3.Error, OSError):
        pass
    try:
        for b in listar().itertuples():
            out[f"Base pública: {b.nome}"] = ("publica", f"base:{b.id}")
    except (sqlite3.Error, OSError):
        pass
    return out


def carregar_fonte(chave):
    """Resolve uma chave de `fontes_bi()` em DataFrame."""
    if chave == "cvm:indicadores":
        return dfp.indicadores_companhias()
    if chave == "cvm:cadastro":
        return dfp.companhias()
    if chave.startswith("base:"):
        return carregar(int(chave.split(":", 1)[1]))
    raise ErroBase("Fonte pública desconhecida.")


def contexto_ia():
    """Texto para a IA externa com as bases que o usuário marcou como 'usar na IA' (estrutura + amostra).
    Retorna (texto, fontes); ('', []) se não houver nenhuma marcada. O texto é DADO, nunca instrução."""
    try:
        marcadas = listar()
        marcadas = marcadas[marcadas["usar_na_ia"] == 1]
    except (sqlite3.Error, OSError):
        return "", []
    partes, fontes, restante = [], [], MAX_CONTEXTO_IA
    for b in marcadas.itertuples():
        try:
            df = carregar(b.id, limite=2000)
        except (ErroBase, sqlite3.Error):
            continue
        cab = (f"### {b.nome} (origem: {b.origem or 'não informada'}; arquivo {b.arquivo}; "
               f"{b.linhas} linhas, {b.colunas} colunas; adicionada em {b.adicionada_em})")
        if b.descricao:
            cab += f"\nDescrição do usuário: {b.descricao}"
        cols = ", ".join(f"{c} ({'número' if pd.api.types.is_numeric_dtype(df[c]) else 'texto'})"
                         for c in df.columns)
        amostra = df.head(5).map(lambda v: str(v)[:60]).to_csv(index=False, sep=";")
        bloco = f"{cab}\nColunas: {cols}\nPrimeiras linhas:\n{amostra}"[:max(restante, 0)]
        if not bloco:
            break
        restante -= len(bloco)
        partes.append(bloco)
        fontes.append(f"Base pública: {b.nome}")
    return "\n\n".join(partes), fontes
