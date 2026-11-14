# Guia do dashboard OneWorld

Este guia explica o uso da Parte 4, responsável pelos indicadores, filtros e
gráficos. As operações funcionam localmente, sem chave de inteligência artificial.

## Abrir o sistema

Na pasta do projeto, execute no PowerShell:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Abra o endereço mostrado e escolha Dashboard. A instalação precisa das
bibliotecas de `requirements.txt`. A pasta `.venv` existente contém o ambiente
usado na validação de 27/10/2026.

## Escolher os dados

Use um exemplo ou envie CSV, XLSX ou JSON e selecione o arquivo em Conjunto de
dados. O leitor atual usa a primeira aba do Excel.

Para analisar dados já gravados pelo aplicativo, marque Incluir tabelas do banco
local e escolha uma opção Banco local. Essa consulta não modifica as tabelas.
Os nomes vêm do banco existente: não são campos obrigatórios do mecanismo de BI.
Tabelas administrativas também podem aparecer; escolha a tabela que contém os
registros a analisar. Tabelas vazias exibem ausência de dados normalmente.

Cada interação consulta novamente a tabela selecionada. Se seu conteúdo mudar,
as configurações de análise são reiniciadas, assim como ao trocar de dataset.
Para buscar alterações sem outra interação, atualize a página.

## Configurar a análise

1. Em Tipos de colunas e datas, confira as colunas. Datas em texto precisam de
   escolha explícita e formato, por exemplo `%Y-%m-%d` ou `%d/%m/%Y`.
2. Em Filtros dinâmicos, ative as colunas desejadas. Escolha categorias ou
   intervalos. Filtros de colunas diferentes são combinados com E.
3. Escolha de um a seis KPIs. Em Configurar KPI, defina operação, coluna,
   título e apresentação. Contagem conta linhas; distintos conta valores únicos
   não nulos; soma, média, mínimo e máximo exigem colunas numéricas.
4. Escolha barras para categorias, linhas para datas ou histograma para números.
   Defina agrupamento, medida e agregação conforme os controles disponíveis.
5. Confira Registros filtrados e use Exportar dados filtrados para obter CSV.

O mesmo conjunto filtrado alimenta tabela, KPIs, gráfico e exportação. Limpar
filtros restaura a visão completa. Ausência de média ou de outra agregação
numérica é exibida como traço. Contagem sem registros é zero. Percentual apenas
formata uma fração: 0,25 vira 25%; não calcula uma taxa automaticamente.

## Roteiro de demonstração

| Conjunto | Configuração | Resultado esperado |
| --- | --- | --- |
| Exemplo: vendas | Soma de valor | 450 |
| Exemplo: vendas | Média de valor | 112,5 |
| Exemplo: vendas | Distintos de produto | 3 |
| Exemplo: educacao | Média de nota | 8 |
| Exemplo: educacao | Filtro turma A e média de nota | 7 |
| Exemplo: estoque | Soma de quantidade | 47 |

Demonstre também barras, datas convertidas em linhas, histograma, limpeza de
filtros e exportação. Depois selecione uma tabela do banco local e repita uma
análise compatível com suas colunas. Os resultados do banco dependem dos dados
gravados, portanto não devem ser apresentados como números fixos do produto.

## Limites atuais

Arquivos enviados e configurações dos painéis ficam na sessão, sem salvamento
para reabertura futura. Há um gráfico por vez. A escrita e o catálogo genérico
de datasets dependem dos módulos da equipe. A IA externa ainda não está
implementada nesta cópia e não é necessária para usar este dashboard.
