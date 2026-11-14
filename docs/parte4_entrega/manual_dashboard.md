# Manual do dashboard — Parte 4 / Entrega 5

Atualizado em 27/10/2026 (Prompt 2) a partir do [guia existente](../guia_dashboard.md) e dos controles de `oneworld/frontend_bi.py`. Este manual cobre a análise de dados da Parte 4. A revisão e incorporação ao manual coletivo estão pendentes; sua existência não comprova disponibilização nem capacitação.

Prazos do [planejamento](../oneworld_planejamento_execucao_v2.md): **04/11/2026** (Entrega 4), **18/11/2026** (Entrega 5) e **25/11/2026** (Entrega 6), **datas previstas nos documentos, ainda sujeitas à confirmação da disciplina**.

## 1. Abrir e escolher os dados

O OneWorld permite analisar dados de diferentes áreas. Você escolhe as colunas e o significado dos indicadores. Não é preciso cadastrar uma chave de IA para usar o dashboard.

Em um ambiente local já preparado pela equipe, abra o sistema e escolha **Dashboard**. Para treinamento, use a cópia isolada existente e os comandos do [roteiro de apresentação](roteiro_apresentacao.md#preparação-local). A inicialização do aplicativo completo pode gravar tabelas legadas: a demonstração deve usar o banco sintético dessa cópia. O ambiente de uso definitivo e sua preparação dependem da equipe (D07).

Abra o endereço informado no terminal. Se o comando não funcionar, solicite à equipe a preparação do ambiente e das bibliotecas de `requirements.txt`. Este material não inclui instalador nem hospedagem. A equipe ainda precisa confirmar abertura na máquina do usuário responsável.

Em **Conjunto de dados**, escolha um exemplo: vendas, educacao ou estoque. Para usar seu arquivo, clique em **Adicionar conjuntos de dados (CSV, XLSX ou JSON)** e depois selecione-o em **Conjunto de dados**. Enviar o arquivo não o seleciona automaticamente. Em Excel, somente a primeira aba é lida. Confira as colunas e a tabela antes de interpretar os resultados; use nomes de colunas únicos.

## 2. Reconhecer tipos e datas

Abra **Tipos de colunas e datas**. A lista mostra o nome, o tipo reconhecido e a quantidade de valores vazios (nulos):

| Tipo | Significado e uso |
| --- | --- |
| categoria | Texto ou opções como turma e produto; permite selecionar valores e comparar grupos. Valores verdadeiro/falso também são categorias. |
| numero | Valores reconhecidos como números; permite intervalos e cálculos. Um número armazenado como texto não vira medida automaticamente. |
| data | Datas já reconhecidas; permite período e gráfico de linhas. |
| incompativel | Conteúdo sem operação automática compatível, como estruturas aninhadas; revise o arquivo com a equipe. |

Datas escritas como texto precisam de escolha explícita. Em **Interpretar colunas como data**, selecione a coluna e informe **Formato das datas**: `%Y-%m-%d` para `2026-10-01` ou `%d/%m/%Y` para `01/10/2026`. O formato informado vale para as colunas selecionadas. Não marque identificadores ou valores numéricos como datas.

No exemplo de vendas, selecione `data` e mantenha `%Y-%m-%d`. Valores que não seguem o formato são tratados como vazios somente nesta análise, com aviso da quantidade. Corrija o formato ou o arquivo de origem se necessário. A conversão não reescreve o arquivo ou o banco. Se o formato for inválido, por exemplo `%Q`, aparece uma mensagem de erro pedindo conferência do formato. Volte a `%Y-%m-%d` no exemplo. Após um erro que interrompe a tela, configurações de controles posteriores podem voltar aos padrões; confira KPIs e gráfico novamente.

## 3. Aplicar e limpar filtros

Abra **Filtros dinâmicos** e marque **Filtrar** na coluna desejada. Para categorias, selecione os valores; para números, informe mínimo e máximo; para datas, escolha início e fim. Os limites são inclusivos. Mínimo/início não pode superar máximo/fim.

Filtros em colunas diferentes precisam ser atendidos ao mesmo tempo (regra E). Por exemplo, turma A e nota de 7 a 10 deixam apenas Ana no exemplo de educação. Quando um filtro está ativo, a opção **Incluir nulos / valores não finitos** permite manter esses valores nessa coluna; os demais filtros continuam valendo. Sem filtro nessa coluna, os registros não são excluídos por esse motivo.

Confira a mensagem de quantidade de registros após os filtros. **Limpar filtros** desativa os filtros e volta à visão completa, mantendo as demais escolhas de análise. Nenhum registro é apagado. Uma seleção sem resultados é válida: ajuste os critérios ou limpe-os.

## 4. Configurar KPIs

KPI é um indicador resumido dos dados selecionados. Em **KPIs configuráveis**, escolha de um a seis indicadores. Abra **Configurar KPI** e defina operação, coluna quando solicitada, título e apresentação.

| Operação | O que informa |
| --- | --- |
| Contagem de registros | Número de linhas, mesmo que algumas células estejam vazias. Não exige coluna. |
| Valores distintos | Quantidade de valores diferentes e não vazios na coluna escolhida. |
| Soma / Média | Total ou média dos números válidos da coluna. |
| Mínimo / Máximo | Menor ou maior número válido da coluna. |

Soma, média, mínimo e máximo exigem coluna numérica; vazios e infinitos são ignorados nesses cálculos. Sem valores válidos, as agregações numéricas, inclusive soma, mostram um traço e uma explicação. Contagem e distintos sem valores retornam zero.

Escolha **Número**, **Percentual** ou **Moeda** conscientemente. Percentual apenas apresenta uma fração: `0,25` aparece como `25%`; não calcula uma taxa. Moeda acrescenta o símbolo escolhido, sem converter valores ou concluir que a coluna representa receita. Exemplo: vendas, Soma de `valor`, apresentação Número → 450.

## 5. Configurar e interpretar gráficos

Há um gráfico por vez em **Gráfico configurável**. As opções dependem dos tipos disponíveis:

| Tipo | Como configurar | Como ler |
| --- | --- | --- |
| barras | Escolha categoria em **Agrupar por**; defina agregação e medida numérica quando solicitada. | Compare o resultado entre categorias. Contagem conta linhas por grupo. |
| linhas | Converta a data se necessário; escolha a data em **Agrupar por**, agregação, medida e **Período** dia ou mes. | Observe o resultado ao longo do tempo. Soma e média têm significados diferentes. |
| histograma | Escolha **Coluna numérica** e quantidade de **Intervalos**. | Cada barra conta valores em uma faixa; não representa uma categoria de negócio. |

Abra **Dados do gráfico** para conferir os números usados. No histograma, escolha de 1 a 100 intervalos. Em telas estreitas, rótulos podem ficar cortados; consulte os intervalos nessa tabela. Nem toda linha aparece no gráfico: faltas na coluna de agrupamento ou na medida podem impedir sua representação. Os KPIs, o gráfico, a tabela e a exportação partem do mesmo conjunto filtrado, mas cada cálculo trata os valores ausentes conforme sua operação. Não conclua causa ou previsão apenas pela forma do gráfico.

## 6. Exportar os resultados

Confira **Registros filtrados** e clique em **Exportar dados filtrados**. O download gera `analise_filtrada.csv`, com as colunas e linhas da tabela filtrada, sem uma coluna extra de índice. O CSV usa vírgula como separador e UTF-8 com marca de codificação para facilitar a abertura de acentos.

O arquivo contém os dados após a conversão de datas da análise. Não inclui o desenho do gráfico, os cartões dos KPIs nem as configurações do painel. Abra-o em uma planilha e confira cabeçalhos e linhas. Se tudo aparecer em uma coluna, use a importação de texto/CSV e selecione vírgula e UTF-8. Escolha onde guardar o arquivo baixado.

## 7. Ler tabelas do banco local

Marque **Incluir tabelas do banco local** e escolha **Banco local: nome da tabela** em **Conjunto de dados**. Escolha a tabela pelos registros e colunas que deseja analisar; tabelas administrativas também podem aparecer. Nenhum nome de tabela é obrigatório para o mecanismo de BI.

Essa consulta do dashboard é somente de leitura: não grava nem altera a tabela. Isso não se estende às outras telas do aplicativo, que podem realizar gravações. Tabelas vazias são exibidas como ausência de dados. Os totais dependem do conteúdo real do banco e não têm um valor fixo garantido.

A tabela selecionada é consultada novamente a cada interação. Para buscar alterações sem outra interação, atualize a página e confira a seleção. Se o conteúdo consultado mudar, as configurações da análise são reiniciadas. O banco não substitui o salvamento do painel.

## 8. Entender mensagens e resolver dificuldades

| Mensagem ou situação | Ação sugerida |
| --- | --- |
| “Não foi possível ler o arquivo: …” | Confira formato, extensão e conteúdo; tente um exemplo para comparar. Peça apoio se o arquivo válido continuar falhando. |
| Valores não seguem o formato de data | Confira dia/mês/ano e o formato escolhido; os valores indicados ficaram vazios nesta análise. |
| Coluna ausente ou não compatível com a operação | Confira a fonte e os tipos; escolha coluna compatível. Números textuais precisam ser tratados na origem. |
| Limites inválidos ou invertidos | Informe números válidos e início/mínimo menor ou igual ao fim/máximo. |
| “Nenhum registro para a seleção atual” | Ajuste ou limpe os filtros; não significa que os dados foram apagados. |
| “Sem colunas compatíveis com gráficos” / “Sem dados válidos para o gráfico…” | Confira os tipos, conversão de datas, filtros, agrupamento e medida. |
| Traço no KPI | Não há números válidos para aquela agregação; confira coluna, vazios e filtros. |
| “Não foi possível abrir o banco local para leitura” / “Não foi possível ler a tabela…” | Peça à equipe que confira disponibilidade do banco e da tabela. Não crie nem altere tabelas para contornar o aviso. |
| “O conjunto não possui colunas” | Escolha outra fonte ou revise o arquivo de origem. |

Se precisar de apoio, anote a fonte, a tarefa, as opções selecionadas e a mensagem exibida. Compartilhe uma captura sem dados sensíveis e um exemplo mínimo permitido pela organização.

## 9. Limites e cuidados de persistência

Uploads e configurações ficam na sessão local. Não há função para salvar e reabrir dashboards, e não há garantia de recuperar escolhas após atualizar a página, fechar a sessão ou reiniciar o sistema. Trocar a fonte ou detectar mudança no conteúdo reinicia configurações de datas, filtros, KPIs e gráfico. Limpar filtros, por sua vez, só redefine os filtros.

Guarde o arquivo original, exporte o recorte necessário e anote as configurações importantes para reproduzi-las. Fazer upload não grava um novo dataset genérico no SQLite. Configurações gerais de outras telas não salvam este painel. Leitura de todas as abas Excel, catálogo/escrita genéricos e persistência dos painéis dependem de decisões dos demais responsáveis. Bases grandes ou com muitas categorias podem dificultar o uso; não há garantia de volume nesta documentação.

A preparação do ambiente, a disponibilização e o manual completo da equipe seguem pendentes no [relatório para a equipe](relatorio_equipe.md), em [dependencias_equipe.md](dependencias_equipe.md) (D02–D07/D12–D14) e no [checklist](checklist.md). Este manual foi conferido com o código e as [evidências atuais](evidencias/validacao_20261027/README.md); não houve novo teste da interface nesta preparação documental.
