# Relato individual — Felipe Carreira da Cunha Antunes — OneWorld

Versão para revisão, atualizada em 14/11/2026. Texto elaborado com base nas conversas sobre a Parte 4, no histórico Git e nas evidências locais. As informações ainda necessárias estão reunidas ao final.

## Identificação

- Nome completo — Felipe Carreira da Cunha Antunes
- Curso — Ciência da Computação
- Disciplina — Tópicos de Big Data em Python
- Turma — WYD6399
- Matrícula — 202502579527
- Período letivo de participação — 2026.2

## Participação no projeto

Minha contribuição no OneWorld está concentrada na Parte 4, dedicada ao Business Intelligence e à visualização de dados. Essa parte reúne indicadores, filtros, gráficos e a interface de análise. Na retomada do projeto, procurei identificar o que já estava implementado e concluir as pendências da minha contribuição. Solicitei a organização do trabalho em etapas e estabeleci que necessidades relacionadas aos módulos de outros integrantes fossem registradas para a equipe.

Na preparação da entrega, solicitei verificações técnicas, conclusão das tarefas possíveis localmente e organização das evidências e dos documentos. A contribuição técnica está registrada na branch `felipe/parte-oneworld`, junto aos materiais de demonstração e documentação.

## Solução e resultados

O dashboard permite analisar dados de diferentes áreas escolhendo colunas e operações. A implementação utiliza Python, pandas e Streamlit, com leitura de arquivos CSV, XLSX e JSON e consulta a tabelas do SQLite local. Os indicadores disponíveis incluem contagem, contagem de valores distintos, soma, média, mínimo e máximo. Os filtros podem combinar categorias, números e datas. A visualização oferece barras, linhas temporais e histogramas, além da tabela de dados e da exportação em CSV.

Uma decisão técnica central foi manter os cálculos separados da apresentação e utilizar o mesmo conjunto filtrado nos indicadores, gráficos, tabela e exportação. Os exemplos de vendas, educação e estoque demonstram a aplicação do mecanismo a conjuntos de dados com colunas distintas. As funções básicas de BI funcionam sem chave de um serviço externo de IA.

A verificação do código atual em 14/11/2026 terminou com 60 testes aprovados. Os exemplos registrados apresentam soma de vendas igual a 450, média geral de notas igual a 8, média da turma A igual a 7 e soma de estoque igual a 47. Foi também verificada a criação de uma demonstração temporária com três tabelas sintéticas e a inicialização da aplicação Streamlit.

## Desafios técnicos e organização da entrega

Minha principal dificuldade foi decidir quais KPIs utilizar no dashboard. Tive contato com todos os outros participantes do projeto, mas a parte de código não teve uma entrega conjunta. Minha contribuição técnica ficou concentrada na Parte 4.

A escolha das operações atende à proposta de analisar dados de diferentes áreas. A contagem informa o volume de registros; a contagem de distintos identifica quantos valores diferentes existem em uma coluna; a soma apresenta um total acumulado; a média resume o valor médio; e o mínimo e o máximo mostram os extremos. Nos exemplos do projeto, essas operações permitem apresentar o total de vendas, a média das notas e a quantidade total em estoque.

O princípio técnico é relacionar a pergunta da análise à coluna e à operação adequadas. Para saber quanto foi vendido, utiliza-se a soma dos valores; para conhecer a média das notas, utiliza-se a média; para saber quantos produtos diferentes aparecem, utiliza-se a contagem de distintos. A relevância de cada indicador depende do objetivo de quem analisa os dados. O dashboard deixa essa configuração disponível ao usuário.

Os registros do desenvolvimento documentam problemas relacionados à troca de datasets, à limpeza de filtros, à interpretação de datas, à ordenação do histograma e à identificação de alterações em dados SQLite. Essas situações foram tratadas na implementação e nos testes da Parte 4. Elas mostram a importância de verificar entradas diferentes e de conferir a coerência entre os controles da interface e os resultados apresentados.

Na etapa de fechamento, solicitei que fossem concluídas as tarefas possíveis com as informações disponíveis. Foram organizados o manual do dashboard, os roteiros de apresentação, capacitação e validação, o questionário de avaliação e os textos técnicos para incorporação ao relatório da equipe. A demonstração passou a ser gerada a partir dos CSVs do projeto, facilitando sua reprodução em uma pasta temporária.

A integração da minha contribuição aproveita componentes compartilhados de navegação, tema, leitura de arquivos e banco. O fechamento coletivo envolve combinar a versão utilizada pela equipe, incorporar os materiais aos documentos oficiais e confirmar as atividades de apresentação e entrega.

## Alcance e relação com o parceiro

O projeto prevê a Casa Grande Eventos como parceira de validação. O dashboard oferece recursos para explorar dados, comparar grupos e exportar recortes, que podem apoiar a interpretação das informações pelo usuário. A utilidade efetiva para o parceiro precisa ser sustentada por sua experiência de uso e pelo retorno registrado.

Os materiais consultados contêm testes técnicos, exemplos sintéticos e instrumentos preparados para as atividades com o parceiro. A participação pessoal em demonstração, capacitação ou coleta de avaliação ainda precisa ser confirmada. O estado atual também mantém limitações como configurações restritas à sessão, um gráfico por vez e leitura da primeira aba de arquivos XLSX.

## Complementos para fechar a versão pessoal

A participação específica em demonstração, capacitação ou conversa com o parceiro permanece sem detalhamento nos registros consultados. O contato com os demais participantes foi confirmado pelo integrante. Caso existam atividades com o parceiro a incluir, registrar data aproximada, papel desempenhado e retorno recebido.

Revisar o texto conforme o modelo da disciplina e confirmar que a descrição corresponde à sua participação.

## Fontes de preparação

- Conversa “Identifique pendências do OneWorld”, consultada em 14/11/2026, e conversa atual sobre a conclusão da contribuição.
- [Histórico de alterações](historico_alteracoes.md) e commits `23a35be` e `a049209`.
- [Status da entrega](status_entrega.md), [validação técnica](validacao_tecnica.md) e [evidências de outubro](evidencias/validacao_20261027/README.md).
- [Contribuição técnica](contribuicao_entrega4.md) e [dependências da equipe](dependencias_equipe.md).
