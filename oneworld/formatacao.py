"""Apresentação de valores de KPI, independente do cálculo e da interface."""
from decimal import Decimal
import math

from .metadados import ErroBI


def formatar_valor_kpi(valor, formato="numero", *, simbolo="R$") -> str:
    """Formata o valor bruto sem inferir unidade ou significado da coluna.

    Percentual apenas apresenta uma fração: 0.25 vira 25.00%.
    Mantém a convenção de separadores já usada pelo dashboard.
    Indisponibilidade (None) é exibida como travessão.
    """
    if not isinstance(formato, str) or formato not in ("numero", "percentual", "moeda"):
        raise ErroBI("Formato de KPI desconhecido.")
    if formato == "moeda" and (not isinstance(simbolo, str) or not simbolo.strip()):
        raise ErroBI("Informe um símbolo de moeda textual não vazio.")
    if valor is None:
        return "—"
    if (isinstance(valor, bool) or not isinstance(valor, (int, float))
            or (isinstance(valor, float) and not math.isfinite(valor))):
        raise ErroBI("Informe um valor numérico finito para apresentação.")
    if formato == "numero" and isinstance(valor, int):
        return str(valor)
    # Decimal evita arredondar inteiros grandes pela conversão para float.
    numero = Decimal(valor) if isinstance(valor, int) else valor
    if formato == "percentual":
        return f"{numero:.2%}"
    if formato == "moeda":
        return f"{simbolo} {numero:,.2f}"
    return f"{numero:,.2f}"
