"""KPIs puros: recebem dados filtrados e escolhas explícitas do usuário."""
from dataclasses import dataclass
from collections.abc import Mapping
import math

import pandas as pd

from .metadados import ErroBI, exigir_coluna, numeros_validos, validar_dataframe

OPERACOES = ("contagem", "distintos", "soma", "media", "minimo", "maximo")
AGREGACOES = {"soma": "sum", "media": "mean", "minimo": "min", "maximo": "max"}


@dataclass(frozen=True)
class ResultadoKPI:
    titulo: str
    valor: int | float | None
    erro: str | None = None
    mensagem: str | None = None

    @property
    def disponivel(self) -> bool:
        """Zero é um resultado disponível; erro e ausência de dados não são."""
        return self.erro is None and self.valor is not None


def calcular_kpi(df: pd.DataFrame, configuracao: Mapping) -> ResultadoKPI:
    """Nulos são ignorados; soma sem valores é indisponível (contagens = 0).

    Erros de configuração são resultados estruturados para exibição na UI.
    Configuração: operacao, coluna (exceto contagem) e titulo opcional.
    Contagem conta linhas, inclusive linhas inteiramente nulas; distintos
    ignora nulos. As demais operações exigem coluna numérica real conforme
    metadados.py. O DataFrame e a configuração não são modificados.
    Campos de apresentação, como formato, não alteram o valor bruto.
    """
    titulo = "KPI"
    try:
        validar_dataframe(df)
        if not isinstance(configuracao, Mapping):
            raise ErroBI("A configuração de KPI deve ser um mapeamento.")
        rotulo = configuracao.get("titulo")
        if rotulo is not None and not isinstance(rotulo, str):
            raise ErroBI("O título do KPI deve ser textual.")
        operacao = configuracao.get("operacao")
        titulo = rotulo or (operacao if isinstance(operacao, str) else "KPI")
        if not isinstance(operacao, str) or operacao not in OPERACOES:
            raise ErroBI("Operação de KPI desconhecida.")
        coluna = configuracao.get("coluna")
        if operacao != "contagem" and not isinstance(coluna, str):
            raise ErroBI("Informe o nome textual da coluna do KPI.")
        if operacao == "contagem":
            valor = len(df)
        elif operacao == "distintos":
            valor = int(exigir_coluna(df, coluna).nunique(dropna=True))
        else:
            s = numeros_validos(df, coluna).dropna()
            if s.empty:
                return ResultadoKPI(titulo, None, mensagem="Sem valores numéricos válidos.")
            # Inteiros Python evitam overflow silencioso em somas int64.
            if operacao == "soma" and s.dtype.kind in "iu":
                valor = sum(int(v) for v in s)
            else:
                valor = getattr(s, AGREGACOES[operacao])()
                valor = valor.item() if hasattr(valor, "item") else valor
            if not isinstance(valor, int) and not math.isfinite(valor):
                raise ErroBI("O resultado numérico excede o intervalo suportado.")
        return ResultadoKPI(titulo, valor)
    except ErroBI as exc:
        return ResultadoKPI(titulo, None, erro=str(exc))
