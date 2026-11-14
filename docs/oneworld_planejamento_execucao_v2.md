# OneWorld — Planejamento e Execução Técnica (v2.0)

> **Status:** planejamento técnico revisado — não implica implementação concluída.  
> **Referência de planejamento:** 21/10/2026.  
> **Área principal:** Parte 4 — Business Intelligence e Visualização de Dados.  
> **Prazo da Entrega 4:** 04/11/2026.  
> **Escopo:** aplicação de BI genérica, local, intuitiva e open source, com integração opcional de IA.

## 1. Correção de escopo

O **OneWorld NÃO é um software de BI para casas de eventos** e não deve ser desenvolvido a partir de estruturas, indicadores ou regras específicas desse segmento. É uma aplicação de *Business Intelligence* de **propósito geral**: o usuário fornece seus dados, escolhe o que deseja analisar e o sistema disponibiliza operações analíticas reutilizáveis.

A **Casa Grande Eventos** é uma parceira para levantamento de requisitos, testes e validação, **não o domínio obrigatório ou público exclusivo** do produto.

### 1.1. Princípios inegociáveis

1. **Independência de domínio:** o código de análise não conhece antecipadamente colunas como `evento`, `convidado`, `receita`, `reserva`, `aluno` ou `produto`.
2. **Dados definidos pelo usuário:** a aplicação trabalha com conjuntos de dados e/ou domínios configurados, em vez de impor uma tabela de negócio fixa.
3. **Análise configurável:** KPIs, filtros e gráficos são produzidos a partir das colunas existentes e de escolhas explícitas do usuário.
4. **Usabilidade:** a interface oferece apenas operações compatíveis com os dados e explica indisponibilidades de forma clara.
5. **Separação de responsabilidades:** cálculos e transformações ficam separados dos componentes Streamlit.
6. **Uso local e independente de IA:** todos os recursos básicos de BI funcionam sem chaves externas.
7. **IA opcional e limitada no MVP:** BYOK (*Bring Your Own Key*) para **sugerir mapeamentos** entre colunas importadas e campos de um domínio já configurado; toda sugestão exige confirmação humana.
8. **Reaproveitamento:** preservar funcionalidades genéricas já implementadas; refatorar ou remover apenas pressupostos específicos de negócio.
9. **Sem resultados fictícios:** testes, arquivos alterados e execução devem ser relatados conforme efetivamente realizados.

### 1.2. Correções em relação ao planejamento anterior

| Antes — inadequado | Agora — necessário |
| --- | --- |
| Receita prevista de eventos | Soma de uma coluna numérica escolhida |
| Número de eventos | Contagem de registros de qualquer dataset |
| Convidados confirmados | Contagem condicional ou contagem distinta quando configurada |
| Filtros de status de evento | Filtros construídos a partir dos tipos de colunas disponíveis |
| Eventos por mês | Agregação temporal sobre qualquer campo de data compatível |
| Dashboard fixo para eventos | Dashboard configurável sobre o conjunto de dados ativo |
| Testes centrados em eventos | Testes com vendas, educação, estoque e dados vazios |

**Regra de revisão:** sempre que um exemplo ou uma função mencionar um setor, verificar se é apenas dado de teste ou uma dependência real. Apenas o segundo caso representa erro de arquitetura.

## 2. Visão do produto e escopo do MVP

### 2.1. Fluxo conceitual

```text
Planilha / registros / domínio configurado
                  |
                  v
      Importação e validação
                  |
                  v
    Tratamento (pandas) e persistência (SQLite)
                  |
                  v
        Dataset selecionado
                  |
                  v
           Filtros genéricos
                  |
         +--------+---------+
         |                  |
         v                  v
    KPIs genéricos     Gráficos genéricos
         |                  |
         +--------+---------+
                  |
                  v
          Interface Streamlit

IA opcional (BYOK): sugestões de mapeamento de colunas,
com revisão humana; não executa o fluxo analítico básico.
```

### 2.2. Funcionalidades essenciais do MVP

- Selecionar ou configurar um domínio de dados e seus campos/tipos, conforme o fluxo acordado com a equipe.
- Incluir registros manualmente ou importar planilhas, conforme o módulo de entrada implementado.
- Validar tipos e armazenar informações localmente.
- Selecionar um conjunto de dados e visualizar suas colunas e registros.
- Aplicar filtros compatíveis com colunas categóricas, numéricas e de data.
- Criar KPIs usando contagem, contagem distinta, soma, média, mínimo e máximo.
- Gerar gráficos de barras, linhas temporais e histogramas.
- Atualizar KPIs e gráficos a partir do mesmo conjunto de dados filtrado.
- Funcionar sem acesso à internet e sem configuração de IA nas funcionalidades centrais.

### 2.3. Fora do MVP da Parte 4

- CRM, gestão de eventos, reservas, convidados ou faturamento de um segmento específico.
- Indicadores calculados com regras contábeis ou operacionais fixas (lucro, margem, taxa de conversão, ocupação etc.).
- Fórmulas arbitrárias definidas pelo usuário e cálculos derivados complexos.
- Modelos preditivos, recomendação automática de decisões ou chatbot analítico completo.
- Geração autônoma de banco de dados, esquemas, KPIs ou regras de negócio pela IA.
- Substituir integralmente ferramentas comerciais maduras como o Power BI.

Essas capacidades podem ser avaliadas para versões futuras, sem comprometer a entrega acadêmica.

## 3. Arquitetura e contratos da Parte 4

### 3.1. Organização sugerida

```text
oneworld/
├── app.py
├── config.py
├── database.py
├── backend.py
├── frontend.py
├── tema.py
│
├── indicadores.py       # cálculo genérico de KPIs
├── filtros.py           # aplicação de filtros dinâmicos
├── analises.py          # agregações e dados para gráficos
│
└── tests/
    └── test_bi.py
```

> **Atenção:** os nomes acima são uma **proposta**, não uma confirmação da estrutura existente no repositório. A auditoria inicial deve localizar os módulos atuais e preservar sua organização sempre que possível. Não criar duplicatas nem substituir o trabalho dos demais integrantes sem alinhamento.

### 3.2. Contrato de entrada e saída

**Entrada:** um `pandas.DataFrame` com os dados do conjunto selecionado e, quando necessário, metadados de suas colunas (nome, tipo inferido/configurado e rótulo).

**Processamento:** filtros → DataFrame filtrado → operações de KPIs e agregações para gráficos.

**Saídas:** resultados de KPI estruturados, DataFrames agregados e mensagens de validação, consumidos pelos componentes Streamlit.

**Restrições:** funções puras de BI não devem acessar diretamente SQLite, Streamlit ou serviços externos de IA. O frontend não deve duplicar os cálculos.

### 3.3. Interfaces conceituais

A forma exata das assinaturas deve ser definida **depois de verificar o código atual**. Como referência:

```python
# Assinaturas ilustrativas — não são código já implementado.

def aplicar_filtros(df, configuracoes):
    """Retorna um novo DataFrame filtrado."""


def calcular_kpi(df_filtrado, configuracao):
    """Retorna valor, rótulo e informações sobre erros/ausência de dados."""


def preparar_grafico(df_filtrado, configuracao):
    """Retorna dados agregados adequados ao tipo de gráfico."""
```

A camada de integração deve obter o DataFrame do backend, aplicar os filtros **uma única vez** e repassar o resultado para KPIs e gráficos.

## 4. KPIs genéricos

### 4.1. Operações do MVP

| Operação | Tipo de entrada | Exemplo de utilização |
| --- | --- | --- |
| Contagem de registros | Qualquer dataset | Número de vendas, alunos ou itens |
| Valores distintos | Qualquer coluna compatível | Quantidade de produtos ou turmas diferentes |
| Soma | Numérica | Valor total ou quantidade total |
| Média | Numérica | Média de notas ou preços |
| Mínimo | Numérica | Menor valor registrado |
| Máximo | Numérica | Maior valor registrado |

Nenhuma dessas operações deve usar nomes de colunas fixos nem inferir significados financeiros pela aparência do nome.

### 4.2. Exemplo de configuração genérica

```json
{
  "id": "kpi_1",
  "titulo": "Soma dos valores selecionados",
  "operacao": "soma",
  "coluna": "valor",
  "formato": "numero"
}
```

`valor` é apenas uma coluna de exemplo fornecida pelo usuário, **não um campo obrigatório do sistema**. O formato (`numero`, `moeda`, `percentual`) é escolha de apresentação; não atribuir moeda automaticamente.

### 4.3. Regras e casos extremos

- Validar existência da coluna e compatibilidade da operação com seu tipo.
- Retornar erro de configuração claro para soma/média em texto, em vez de tentar somar strings.
- Em agregações numéricas, considerar apenas valores numéricos válidos, sem converter silenciosamente conteúdo ambíguo.
- Tratar valores nulos: agregações ignoram nulos; contagem distinta ignora nulos por padrão, com semântica documentada.
- A contagem de registros em um DataFrame vazio é `0`; média/mínimo/máximo sem valores válidos devem ser exibidos como indisponíveis, não como `0` inventado.
- Atualizar resultados sempre que o conjunto filtrado for alterado.
- Separar resultado bruto de sua formatação visual (casas decimais, moeda, percentual).
- Não interpretar uma coluna como taxa ou valor monetário sem escolha explícita do usuário.

### 4.4. Exemplo de dados para validação

```text
Dataset A — vendas
produto   valor
Caneta    100
Livro     200
Caneta    100
Borracha   50

Dataset B — notas
aluno     turma    nota
Ana       A        8
Bruno     A        6
Clara     B       10
```

| Dataset | Operação | Resultado correto |
| --- | --- | ---: |
| A | Soma de `valor` | 450 |
| A | Média de `valor` | 112,5 |
| A | Valores distintos de `produto` | 3 |
| B | Média de `nota` | 8 |
| B | Valores distintos de `turma` | 2 |

**Critério essencial:** o código usado para calcular os KPIs do Dataset A deve funcionar com o Dataset B sem nenhuma mudança interna.

## 5. Filtros dinâmicos

| Tipo de coluna | Filtro sugerido | Observações |
| --- | --- | --- |
| Categórica/texto | Seleção de um ou vários valores | Tratar categorias vazias/nulas de forma explícita |
| Numérica | Intervalo mínimo e máximo | Sem aceitar limites invertidos |
| Data/data-hora | Intervalo de datas | Definir limites inclusivos e normalizar datas com segurança |
| Incompatível/complexa | Sem filtro automático | Informar incompatibilidade, sem falha da interface |

Regras:

1. Colunas e controles de filtro são detectados a partir do conjunto ativo, não do nome de um setor.
2. Filtros em colunas diferentes usam lógica **AND** no MVP.
3. O resultado é um **novo DataFrame**, sem modificar o original.
4. O usuário pode limpar os filtros e voltar à visão completa.
5. O resultado vazio é válido e deve ser tratado normalmente.
6. KPIs e gráficos recebem **exatamente o mesmo DataFrame filtrado**.

## 6. Gráficos genéricos

| Visualização | Requisitos mínimos | Operações típicas |
| --- | --- | --- |
| Barras | Coluna de categoria e medida/agregação | Contagem, soma ou média por categoria |
| Linhas temporais | Coluna de data e medida/agregação | Contagem, soma ou média por dia/mês |
| Histograma | Coluna numérica | Frequências por intervalos |

A interface deve permitir escolher o tipo de gráfico e oferecer **somente** colunas adequadas aos eixos e às agregações. Não assumir que há sempre campo de data. Tratar datas inválidas, ausência de categorias e datasets vazios.

O módulo `analises.py` (ou equivalente existente) prepara/agrega os dados. A renderização deve permanecer na interface Streamlit.

## 7. Cronograma de execução — Parte 4

> Planejamento proposto em 21/10/2026; os períodos dependem da disponibilidade efetiva dos módulos de entrada, persistência e interface da equipe.

| Período | Etapa | Entrega verificável |
| --- | --- | --- |
| **21–22/10** | Auditoria e contratos | Inventário do código, dependências e plano de refatoração |
| **23–25/10** | KPIs genéricos | Operações testadas de contagem, distintos, soma, média, mínimo e máximo |
| **26–27/10** | Filtros dinâmicos | Filtros categóricos, numéricos e temporais combináveis |
| **28–30/10** | Gráficos | Barras, linhas temporais e histograma com dados genéricos |
| **31/10–01/11** | Testes e correções | Suíte de testes com datasets de diferentes domínios |
| **02–04/11** | Integração e demonstração | Fluxo de BI funcionando em Streamlit |

### 7.1. Dependências e plano de contingência

- **Backend/importação incompletos:** integrar inicialmente com DataFrames locais pequenos e documentados; conectar ao backend após estabilização do contrato.
- **Alterações conflitantes de integrantes:** isolar a Parte 4 em funções desacopladas e alinhar interfaces antes de editar arquivos compartilhados.
- **Prazo curto:** priorizar operações analíticas corretas e fluxo demonstrável; adiar recursos avançados e polimento não essencial.
- **Datas/tipos de coluna inconsistentes:** validar tipagem na fronteira entre importação e camada de BI, sem conversões automáticas destrutivas.
- **IA indisponível:** manter caminho manual funcional de importação e configuração de análises.

## 8. Prompts de implementação (executar em sequência)

**Modo de uso:** iniciar com o Prompt 0 como contexto mestre; executar o Prompt 1 antes de qualquer edição de código; avançar nas etapas somente após revisar o resultado e os testes. Usar uma ferramenta com acesso real ao repositório. Não presumir que a IA executou comandos ou verificou arquivos sem evidência.

### Prompt 0 — Contexto mestre do OneWorld

```text
Você está auxiliando no desenvolvimento do OneWorld.

CONTEXTO DO PROJETO:
O OneWorld é uma aplicação LOCAL de Business Intelligence (BI), de código aberto, desenvolvida principalmente com Python, Streamlit, pandas e SQLite.

O objetivo é democratizar a análise de dados, permitindo que pessoas sem experiência em BI utilizem datasets de diferentes áreas.

O sistema NÃO é uma aplicação de gerenciamento de eventos, vendas, escolas ou qualquer outro segmento específico.

A Casa Grande Eventos é apenas uma parceira de validação do projeto, não o domínio central da aplicação.

ESCOPO DA PARTE 4:
Desenvolver o mecanismo genérico de BI:
- KPIs configuráveis;
- filtros dinâmicos;
- gráficos;
- integração com a interface;
- testes e tratamento de erros.

REGRAS OBRIGATÓRIAS:
1. Nunca codifique colunas fixas como "evento", "convidado", "cliente", "receita" ou "reserva".
2. Trabalhe com pandas.DataFrame e metadados de colunas.
3. Separe cálculos de BI da interface Streamlit.
4. Não coloque regras específicas de um negócio dentro de funções genéricas.
5. Não altere o banco de dados ou outros módulos compartilhados desnecessariamente.
6. Não introduza novas bibliotecas sem justificar a necessidade.
7. A aplicação deve funcionar sem serviços de IA.
8. Preserve as funcionalidades existentes que não estejam em conflito com estes requisitos.
9. Não assuma que arquivos, funções ou tabelas existem: inspecione o repositório.
10. Escreva código legível, documentado e testável.
11. Não invente resultados de testes nem afirme que executou algo que não executou.

A IA integrada ao produto, quando existir, utiliza BYOK e apenas sugere mapeamentos de colunas para domínios configurados. Não deve definir métricas, regras de negócio ou gravar dados autonomamente.

Ao finalizar cada etapa:
- descreva os arquivos modificados;
- explique as decisões técnicas;
- informe quais testes foram executados;
- registre limitações e pendências.

O princípio mais importante é:
"O usuário fornece os dados e configura a análise; o OneWorld oferece as operações analíticas sem pressupor o contexto de negócio."
```

### Prompt 1 — Auditoria técnica (sem editar código)

```text
Analise a implementação atual do OneWorld antes de realizar alterações.

Examine os arquivos existentes relacionados a:
- carregamento e armazenamento de dados;
- dashboards;
- KPIs;
- filtros;
- gráficos;
- frontend e backend.

Identifique:
1. Quais funcionalidades já estão implementadas.
2. Quais estão parcialmente implementadas.
3. Quais dependem de colunas ou regras específicas de eventos.
4. Quais podem ser reaproveitadas sem alterações.
5. Quais precisam ser refatoradas para trabalhar com datasets genéricos.
6. Quais contratos de integração existem entre frontend, backend e banco.

Defina um plano de refatoração com o menor impacto possível.

Não altere o código ainda.

Entregue:
- diagnóstico por arquivo;
- dependências e riscos;
- interfaces propostas;
- sequência de implementação;
- testes necessários.

Não assuma a existência de funções ou módulos sem verificá-los.
```

### Prompt 2 — KPIs genéricos

```text
Implemente a camada genérica de indicadores do OneWorld.

Utilize pandas e o contrato de dados identificado na auditoria.

Crie ou adapte o módulo de indicadores (preferencialmente indicadores.py, caso compatível com a arquitetura atual).

OPERAÇÕES DO MVP:
- contar registros;
- contar valores distintos de uma coluna;
- somar valores numéricos;
- calcular média;
- encontrar mínimo;
- encontrar máximo.

REQUISITOS:
1. Receber um DataFrame e uma configuração de KPI.
2. Nunca depender de nomes fixos de colunas.
3. Validar se a coluna existe.
4. Validar compatibilidade da operação com o tipo da coluna.
5. Tratar valores nulos corretamente.
6. Retornar resultado estruturado, apropriado para a interface.
7. Permitir que o usuário defina o título do indicador.
8. Permitir formatação independente da lógica, como número, percentual ou moeda quando escolhido explicitamente.
9. Não assumir que uma coluna chamada "valor" significa receita.
10. Não acessar Streamlit, SQLite ou APIs de IA dentro das funções de cálculo.

Para datasets sem registros após filtros, retorne contagem 0 e sinalize indisponibilidade das agregações que não podem ser calculadas.

Inclua testes automatizados com dados de diferentes domínios.

Preserve funções já existentes que sejam realmente genéricas.

Ao final, demonstre que a mesma implementação calcula indicadores em planilhas com estruturas diferentes.
```

### Prompt 3 — Filtros dinâmicos

```text
Implemente os filtros genéricos do OneWorld.

Os filtros devem ser definidos pelas características das colunas do DataFrame, e não pelo segmento de negócio.

REQUISITOS:
1. Colunas categóricas: seleção de um ou vários valores.
2. Colunas numéricas: filtro por intervalo mínimo e máximo.
3. Colunas de data: filtro por período.
4. Colunas inadequadas: não apresentar filtros incompatíveis.
5. Permitir remover ou redefinir todos os filtros.
6. Combinar filtros de colunas diferentes com lógica AND.
7. Preservar os tipos e a estrutura original dos dados.
8. Não modificar o DataFrame recebido.
9. Tratar valores nulos, datas inválidas e ausência de registros.
10. Não criar filtros obrigatórios de eventos, clientes, reservas ou status.

A camada de processamento deve ser independente da interface Streamlit.

O DataFrame filtrado será utilizado tanto pelos KPIs quanto pelos gráficos.

Inclua testes de filtragem combinada e de resultado vazio.

Integre à arquitetura existente com mudanças mínimas.
```

### Prompt 4 — Gráficos genéricos

```text
Implemente a preparação de gráficos genéricos para a Parte 4 do OneWorld.

A biblioteca de visualização deve seguir o que já estiver disponível no projeto; priorize componentes compatíveis com Streamlit.

GRÁFICOS DO MVP:
- barras para comparação entre categorias;
- linhas para evolução temporal;
- histograma para distribuição de valores numéricos.

REQUISITOS:
1. O usuário deve selecionar o tipo de gráfico.
2. As opções de eixos devem depender das colunas existentes.
3. Permitir selecionar coluna de agrupamento, quando aplicável.
4. Permitir contagem, soma ou média como agregação.
5. Para séries temporais, permitir agrupamento por período.
6. Reutilizar o DataFrame filtrado.
7. Validar compatibilidade dos tipos de dados com o gráfico.
8. Tratar valores ausentes e conjuntos vazios.
9. Não depender de colunas chamadas "evento", "receita", "cliente" ou semelhantes.
10. Não alterar o banco de dados ou a lógica de importação.

Separe a preparação/agregação dos dados da renderização no Streamlit.

Não adicione métricas ou interpretações automaticamente baseadas no nome das colunas.

Inclua exemplos e testes com datasets de naturezas diferentes.
```

### Prompt 5 — Testes automatizados

```text
Crie uma suíte de testes automatizados para o mecanismo genérico de BI do OneWorld.

Utilize pytest se for compatível com o ambiente existente.

Crie datasets pequenos e independentes:
1. Vendas: produto, categoria, valor, data.
2. Educação: aluno, turma, nota.
3. Estoque: produto, quantidade, categoria.

Não utilize tabelas ou dependências de eventos como requisito.

TESTE:
- contagem de registros;
- soma e média corretas;
- mínimo e máximo;
- valores distintos;
- filtros categóricos;
- filtros numéricos;
- filtros de datas;
- combinação de filtros;
- integração de filtros com KPIs;
- agregação utilizada nos gráficos;
- dataset vazio;
- valores nulos;
- colunas ausentes;
- tipos incompatíveis.

Garanta que nenhuma operação exija IA ou acesso à internet.

Não adapte os resultados esperados aos resultados produzidos pelo código: use resultados conhecidos previamente.

Execute os testes quando possível e relate resultados reais, falhas e correções.

Não modifique módulos de outros integrantes apenas para fazer um teste passar.
```

### Prompt 6 — Integração final com Streamlit

```text
Integre os módulos genéricos de BI à interface atual do OneWorld.

ANTES:
Revise os contratos entre frontend.py, backend.py, database.py e os módulos implementados.

OBJETIVO:
Permitir que o usuário:
1. Selecione um domínio ou conjunto de dados disponível.
2. Visualize suas colunas e registros.
3. Aplique filtros compatíveis com os dados.
4. Configure KPIs.
5. Configure gráficos.
6. Visualize os resultados atualizados.

REQUISITOS:
- Evite duplicar regras de negócio no frontend.
- KPIs e gráficos precisam utilizar o mesmo conjunto filtrado.
- Não crie telas ou menus específicos de eventos.
- Preserve a navegação e o tema existente.
- Não modifique estruturas do banco sem necessidade.
- Utilize mensagens claras para dados ausentes ou incompatíveis.
- Não exija conexão com serviços externos.
- Não altere a integração de IA/BYOK que esteja sob responsabilidade de outro integrante.

Entregue um fluxo demonstrável usando pelo menos dois datasets de domínios diferentes.

Verifique a execução do aplicativo e dos testes.

Documente os arquivos modificados, as funcionalidades concluídas e os problemas pendentes.
```

### Prompt adicional — IA/BYOK (integração da equipe)

```text
Revise a integração opcional de IA/BYOK do OneWorld para garantir que ela seja independente de domínios específicos.

A IA deve receber:
- nomes e tipos das colunas de uma planilha;
- os campos de um domínio configurado pelo usuário;
- amostras mínimas dos dados somente quando necessárias.

A IA deve retornar sugestões estruturadas de correspondência entre colunas de origem e campos de destino.

A interface deve permitir revisão e confirmação manual.

RESTRIÇÕES:
- Não criar esquemas de banco autonomamente.
- Não definir KPIs nem regras de negócio.
- Não gravar dados diretamente.
- Não enviar o dataset completo desnecessariamente.
- Não registrar chaves de API em logs.
- Não impedir o funcionamento do BI quando a IA não estiver configurada.
- Respeitar os limites de utilização previstos no projeto.

Mantenha os provedores BYOK definidos no planejamento, observando a implementação disponível.

Inclua testes com respostas simuladas, sem utilizar chaves reais.
```

## 9. Critérios de aceitação

### 9.1. KPIs

- [ ] Contagem de registros funciona com qualquer DataFrame.
- [ ] Soma, média, mínimo e máximo operam apenas em colunas numéricas compatíveis.
- [ ] Contagem distinta funciona em dados de domínios diferentes.
- [ ] Nulos, colunas ausentes, incompatibilidades e datasets vazios são tratados.

### 9.2. Filtros e gráficos

- [ ] Controles de filtro são derivados dos tipos de colunas.
- [ ] KPIs e gráficos recebem o mesmo DataFrame filtrado.
- [ ] Nenhum gráfico exige nomes de colunas predefinidos.
- [ ] Dados sem coluna de data continuam utilizáveis em análises compatíveis.

### 9.3. Integração e demonstração

- [ ] O BI funciona sem uma chave de IA.
- [ ] Trocar o conjunto de dados não quebra a interface.
- [ ] Dois ou mais domínios de dados funcionam sem modificação de código.
- [ ] Testes são executados com resultados documentados e o aplicativo inicia corretamente.

### 9.4. Teste de independência de domínio

Demonstre o uso do **mesmo mecanismo** com pelo menos:

1. **Vendas:** produto, categoria, valor e data.
2. **Educação:** aluno, turma e nota.
3. **Estoque:** produto, quantidade e categoria.

O teste deve mostrar que a mudança de dataset altera as colunas disponíveis, indicadores e gráficos, **não a implementação** dos cálculos.

## 10. Entregas acadêmicas e validação externa

| Marco | Data prevista no planejamento acadêmico | Objetivo |
| --- | --- | --- |
| Entrega 4 | **04/11/2026** | Desenvolvimento: interface, dashboards, gráficos, análises e demonstração do MVP |
| Entrega 5 | **18/11/2026** | Implantação, manual e capacitação do usuário responsável |
| Entrega 6 | **25/11/2026** | Apresentação, avaliação final, relatório completo e demonstração |

A Casa Grande Eventos pode oferecer dados de validação realistas, mas **o mesmo aplicativo deve ser demonstrável com outra área de dados**, reforçando seu caráter genérico.

## 11. Próximos passos imediatos

1. Suspender prompts anteriores que determinem KPIs de receita, convidados, reservas ou eventos.
2. Executar **Prompt 0** para definir o contexto de escopo.
3. Executar **Prompt 1** para auditar o código **sem editar**.
4. Revisar o diagnóstico antes de aceitar alterações.
5. Executar **Prompt 2** para substituir os KPIs específicos por operações genéricas.
6. Validar o módulo de KPIs com pelo menos dois datasets diferentes.
7. Prosseguir com filtros (**Prompt 3**), gráficos (**Prompt 4**), testes (**Prompt 5**) e integração (**Prompt 6**).
8. Usar o checklist da seção 9 antes de considerar a Parte 4 concluída.

## 12. Referências internas do projeto

Este documento reorganiza o planejamento técnico em conformidade com os arquivos acadêmicos fornecidos pela equipe:

- `Item 1 trabalho big data.docx`: motivação ligada à intuitividade do BI, dashboards universais, natureza open source e IA opcional.
- `entrega_2_oneworld.docx`: sistema local em Python; Streamlit, pandas, SQLite; BYOK com provedores externos; parceiro para requisitos/testes, sem direcionamento exclusivo do escopo; cronograma das Entregas 4–6.

**Nota de consistência:** a Entrega 2 descreve o mapeamento de colunas para campos de um domínio já configurado. Isso **não exige que todos os usuários compartilhem um domínio fixo**, nem autoriza a IA a criar esquemas ou regras de negócio automaticamente.

---

**Princípio final:** **o OneWorld não entrega indicadores de um negócio específico. Ele fornece ferramentas para o usuário construir indicadores a partir dos próprios dados.**

**Estado de implementação:** este documento é um planejamento. A existência dos arquivos e a situação real do código e dos testes precisam ser verificadas no repositório antes da execução.
