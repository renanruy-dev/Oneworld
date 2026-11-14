# Indicadores genéricos

A implementação reaproveita `oneworld/indicadores.py` e os validadores da
auditoria em `oneworld/metadados.py`. Não depende de nomes de colunas ou de
regras de negócio. As funções de cálculo não acessam Streamlit, SQLite ou IA.

## Uso e contrato

```python
from oneworld.indicadores import calcular_kpi
from oneworld.formatacao import formatar_valor_kpi

configuracao = {
    "titulo": "Média das notas selecionadas",
    "operacao": "media",
    "coluna": "nota",
    "formato": "numero",
}
resultado = calcular_kpi(df_filtrado, configuracao)
if resultado.erro:
    print(resultado.erro)
else:
    print(resultado.titulo, formatar_valor_kpi(
        resultado.valor, configuracao["formato"],
    ))
```

- Entrada: `pandas.DataFrame` com nomes de colunas textuais únicos e um
  mapeamento de configuração. Dados e configuração são preservados.
- `operacao`: `contagem`, `distintos`, `soma`, `media`, `minimo` ou `maximo`.
- `coluna`: obrigatória para todas as operações exceto `contagem`, que conta
  linhas, inclusive as inteiramente nulas, sem depender do índice.
- `titulo`: texto opcional escolhido pelo usuário; sem título, usa a operação.
- Saída preservada: `ResultadoKPI(titulo, valor, erro, mensagem)`. O valor é
  `int`, `float` ou `None`. A propriedade `disponivel` distingue um resultado
  válido (inclusive zero) de ausência de dados ou erro.
- Erros de configuração, DataFrame inválido, coluna ausente e tipo incompatível
  retornam `valor=None` e `erro` descritivo.
- Distintos aceita números, categorias e datas compatíveis com o contrato,
  ignorando nulos e categorias sem ocorrências. Booleanos são categorias.
- Soma, média, mínimo e máximo exigem números reais. Texto numérico, booleanos,
  datas, objetos aninhados e complexos não são medidas; não há coerção automática.
- Agregações numéricas ignoram nulos e infinitos. Sem valores válidos, inclusive
  após filtros, retornam `valor=None`, `erro=None` e uma `mensagem`. Contagem e
  distintos em colunas compatíveis vazias retornam zero. A validação de coluna
  e tipo permanece ativa nos conjuntos vazios.
- Somas inteiras usam inteiros Python para evitar overflow de `int64`. Resultados
  de ponto flutuante não finitos são sinalizados como erro.

## Apresentação independente

`formatar_valor_kpi(valor, formato="numero", simbolo="R$")` é uma função pura
separada, usada também pelo dashboard. `simbolo` deve ser passado por nome.

| Valor bruto | Formato explícito | Apresentação |
| ---: | --- | --- |
| 0.25 | `numero` (padrão) | `0.25` |
| 0.25 | `percentual` | `25.00%` |
| 0.25 | `moeda`, símbolo `€` | `€ 0.25` |
| `None` | qualquer formato válido | `—` |

Mantém os separadores usados pela interface existente e duas casas decimais
para floats, moeda e percentual. Inteiros em formato número mantêm todos os
dígitos; moeda também preserva inteiros grandes sem convertê-los para float.
Formatos inválidos levantam `ErroBI` na apresentação.

O campo `formato` da configuração não afeta o cálculo. Uma coluna `valor` não
recebe significado financeiro nem formatação monetária automaticamente.
Percentual apresenta uma fração; não calcula taxas.

## Demonstração reproduzível

Na raiz do projeto:

```powershell
.\.venv\Scripts\python.exe -m exemplos.demonstrar_indicadores
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

A mesma função, alterando apenas a configuração, produziu:

| Arquivo | Coluna numérica | Coluna distinta | Registros | Distintos | Soma | Média | Mínimo | Máximo |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `vendas.csv` | `valor` | `produto` | 4 | 3 | 450 | 112,5 | 50 | 200 |
| `educacao.csv` | `nota` | `turma` | 3 | 2 | 24 | 8 | 6 | 10 |
| `estoque.csv` | `quantidade` | `categoria` | 3 | 2 | 47 | 15,666667 | 5 | 30 |

Verificação desta etapa: **49 testes aprovados**, incluindo os testes anteriores.
`tests/test_indicadores.py` cobre também leitura real de duas abas XLSX com
estruturas diferentes, filtros sem registros, tipos pandas nullable, precisão
inteira, configurações malformadas, serialização e preservação dos dados.
`tests/test_frontend_bi.py` verifica título e troca explícita de apresentação.
Compilação de `oneworld`, `exemplos` e `tests` verificada com `compileall`.
