# Relato individual — Felipe — OneWorld

Versão para revisão, atualizada em 14/11/2026. Texto elaborado com base nas conversas sobre a Parte 4, no histórico Git e nas evidências locais. As informações ainda necessárias estão reunidas ao final.

## Participação no projeto

Minha contribuição no OneWorld está concentrada na Parte 4, dedicada ao Business Intelligence e à visualização de dados. Essa parte reúne indicadores, filtros, gráficos e a interface de análise. Na retomada do projeto, procurei identificar o que já estava implementado e concluir as pendências da minha contribuição. Solicitei a organização do trabalho em etapas e estabeleci que necessidades relacionadas aos módulos de outros integrantes fossem registradas para a equipe.

Utilizei assistência de IA no desenvolvimento e na preparação dos materiais. Nas conversas com o Codex, solicitei verificações técnicas, conclusão das tarefas possíveis localmente e organização das evidências e dos documentos. Em 14/11/2026, também autorizei commits na minha branch. A contribuição técnica está registrada no commit `23a35be`, associado à conta `felipecarreira07` e com crédito de coautoria ao Copilot. A organização dos materiais e a demonstração reproduzível foram registradas no commit `a049209`, na branch `felipe/parte-oneworld`.

## Solução e resultados

O dashboard permite analisar dados de diferentes áreas escolhendo colunas e operações. A implementação utiliza Python, pandas e Streamlit, com leitura de arquivos CSV, XLSX e JSON e consulta a tabelas do SQLite local. Os indicadores disponíveis incluem contagem, contagem de valores distintos, soma, média, mínimo e máximo. Os filtros podem combinar categorias, números e datas. A visualização oferece barras, linhas temporais e histogramas, além da tabela de dados e da exportação em CSV.

Uma decisão técnica central foi manter os cálculos separados da apresentação e utilizar o mesmo conjunto filtrado nos indicadores, gráficos, tabela e exportação. Os exemplos de vendas, educação e estoque demonstram a aplicação do mecanismo a conjuntos de dados com colunas distintas. As funções básicas de BI funcionam sem chave de um serviço externo de IA.

A verificação do código atual em 14/11/2026 terminou com 60 testes aprovados. Os exemplos registrados apresentam soma de vendas igual a 450, média geral de notas igual a 8, média da turma A igual a 7 e soma de estoque igual a 47. Foi também verificada a criação de uma demonstração temporária com três tabelas sintéticas e a inicialização da aplicação Streamlit.

## Desafios técnicos e organização da entrega

Minha principal dificuldade foi decidir quais KPIs utilizar no dashboard. A escolha dos indicadores foi o ponto em que encontrei mais dificuldade durante minha participação. Minha atuação ficou concentrada na Parte 4, sem interação com as outras partes do projeto.

Os registros do desenvolvimento documentam problemas relacionados à troca de datasets, à limpeza de filtros, à interpretação de datas, à ordenação do histograma e à identificação de alterações em dados SQLite. Essas situações foram tratadas na implementação e nos testes da Parte 4. Elas mostram a importância de verificar entradas diferentes e de conferir a coerência entre os controles da interface e os resultados apresentados.

Na etapa de fechamento, solicitei que fossem concluídas as tarefas possíveis com as informações disponíveis. Foram organizados o manual do dashboard, os roteiros de apresentação, capacitação e validação, o questionário de avaliação e os textos técnicos para incorporação ao relatório da equipe. A demonstração passou a ser gerada a partir dos CSVs do projeto, facilitando sua reprodução em uma pasta temporária.

A integração da minha contribuição aproveita componentes compartilhados de navegação, tema, leitura de arquivos e banco. O fechamento coletivo envolve combinar a versão utilizada pela equipe, incorporar os materiais aos documentos oficiais e confirmar as atividades de apresentação e entrega.

## Alcance e relação com o parceiro

O projeto prevê a Casa Grande Eventos como parceira de validação. O dashboard oferece recursos para explorar dados, comparar grupos e exportar recortes, que podem apoiar a interpretação das informações pelo usuário. A utilidade efetiva para o parceiro precisa ser sustentada por sua experiência de uso e pelo retorno registrado.

Os materiais consultados contêm testes técnicos, exemplos sintéticos e instrumentos preparados para as atividades com o parceiro. A participação pessoal em demonstração, capacitação ou coleta de avaliação ainda precisa ser confirmada. O estado atual também mantém limitações como configurações restritas à sessão, um gráfico por vez e leitura da primeira aba de arquivos XLSX.

## Complementos para fechar a versão pessoal

1. **Identificação e período.** Informar nome completo, curso, turma, disciplina e matrícula conforme o modelo exigido, além do período efetivo de participação. Os registros técnicos consultados abrangem outubro e novembro de 2026.
2. **Aprendizado pessoal.** Informar, em uma frase, o que aprendeu ao decidir os KPIs. A dificuldade e a ausência de interação com outras partes já foram incorporadas conforme seu relato.
3. **Atividade com o parceiro.** Confirmar se participou de demonstração, capacitação ou conversa com o parceiro. Se participou, informar quando, seu papel e o retorno recebido. Se ainda não participou, basta registrar essa situação.

Após esses complementos, revisar o texto conforme o modelo da disciplina e confirmar que a descrição corresponde à sua participação.

## Fontes de preparação

- Conversa “Identifique pendências do OneWorld”, consultada em 14/11/2026, e conversa atual sobre a conclusão da contribuição.
- [Histórico de alterações](historico_alteracoes.md) e commits `23a35be` e `a049209`.
- [Status da entrega](status_entrega.md), [validação técnica](validacao_tecnica.md) e [evidências de outubro](evidencias/validacao_20261027/README.md).
- [Contribuição técnica](contribuicao_entrega4.md) e [dependências da equipe](dependencias_equipe.md).
