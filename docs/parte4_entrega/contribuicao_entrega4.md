# Contribuição técnica da Parte 4 — Entrega 4 do OneWorld

Preparado em **27/10/2026**, referência America/Sao_Paulo. **Material técnico preparado; revisão pela equipe e envio à disciplina pendentes.** A data de 04/11/2026 é a previsão documental para a Entrega 4 e depende de confirmação pela disciplina.

## Base e alcance deste texto

Este documento reúne evidências existentes para incorporação ao relatório coletivo. Aplica o contexto mestre (contexto inicial), os contratos e as restrições do [planejamento v2](../oneworld_planejamento_execucao_v2.md), identificado nas etapas anteriores como a base disponível. Não foi localizado um arquivo separado chamado prompt-base. O princípio aplicado é: o usuário fornece os dados e configura a análise; o OneWorld oferece operações analíticas sem pressupor o contexto de negócio.

Foram consultados o código atual, os exemplos, o [checklist](checklist.md), a [validação técnica atual](validacao_tecnica.md), os [registros da rodada final de 27/10/2026](evidencias/validacao_20261027/README.md), seus logs e manifestos. Os resultados de execução abaixo pertencem às rodadas identificadas nesses registros; nesta preparação de materiais (etapa documental) foi feita consolidação documental, sem nova execução da aplicação ou da suíte. Os DOCX originais não foram alterados e nenhuma entrega foi enviada.

### Limite de atribuição individual

O recorte apresentado é o **mecanismo genérico de BI da Parte 4**. A existência dos arquivos e os registros de alterações comprovam o estado técnico e as verificações descritas, mas não comprovam autoria humana individual. A auditoria anterior registrou ausência de histórico Git suficiente para atribuir autoria individual. Por isso, o texto descreve o módulo, sem afirmar que um integrante escreveu todo o código, criou o backend, o banco, as telas gerais ou a integração de IA.

Antes de identificar este material como contribuição individual no relatório final, a equipe deve confirmar as tarefas e arquivos atribuíveis ao integrante, com registro verificável (P4-16 do checklist). Experiências pessoais, divisão nominal de trabalho e aceite dos colegas continuam pendentes; não foram inventados neste documento.

## 1. Problema que o mecanismo de BI resolve

Planilhas de áreas diferentes exigem selecionar dados, conferir tipos, recortar registros e produzir medidas e gráficos consistentes. O mecanismo da Parte 4 oferece essas operações em um painel local configurável, com controles derivados das colunas do dataset, reduzindo a necessidade de programar uma análise para cada área.

O OneWorld é proposto como BI genérico local e de código aberto. Vendas, educação e estoque são exemplos de aplicação do mesmo motor, não domínios obrigatórios. A Casa Grande Eventos é parceira prevista de validação; não define os nomes de colunas nem as regras das funções genéricas. A publicação e a licença da proposta open source ainda dependem da equipe. Benefícios como economia de tempo, facilidade de uso ou impacto no parceiro são objetivos, sem medição externa comprovada neste pacote.

## 2. Funcionalidades efetivamente implementadas

| Recurso disponível | Alcance confirmado no código e nas evidências |
| --- | --- |
| Seleção de dados | Três CSV de exemplo, upload de CSV/XLSX/JSON e leitura de tabelas existentes do SQLite local. A interface permite adicionar arquivos e selecionar um dataset por vez; não faz junção automática entre arquivos. XLSX utiliza a primeira aba. |
| Metadados | Validação de DataFrame com nomes de colunas textuais únicos; identificação de números, categorias, datas e tipos incompatíveis; contagem de nulos. Booleanos são categorias. |
| Datas explícitas | Escolha da coluna e do formato pelo usuário. Valores que falham na conversão viram nulos na cópia usada pela análise, com aviso. Datas textuais não são convertidas silenciosamente. |
| KPIs configuráveis | De um a seis indicadores, com contagem de linhas, valores distintos não nulos, soma, média, mínimo e máximo; escolha de coluna e título. Operações numéricas exigem tipo compatível. |
| Apresentação dos KPIs | Número, percentual ou moeda com símbolo escolhido. Percentual apenas apresenta uma fração; não calcula uma taxa. A apresentação não muda o valor bruto. |
| Filtros dinâmicos | Seleção de categorias, intervalos numéricos e de datas inclusivos, opção de incluir nulos/valores não finitos e combinação por E (AND). Botão de limpeza restaura o conjunto e os controles. |
| Gráficos | Um gráfico configurável por vez: barras por categoria, linhas por dia/mês e histograma numérico com 1 a 100 intervalos. Barras/linhas permitem contagem, soma, média, mínimo e máximo conforme os tipos. |
| Conferência e exportação | Tabela de registros filtrados, tabela dos dados agregados do gráfico e download dos registros filtrados em CSV UTF-8 com BOM. Exportar registros não equivale a salvar o painel. |
| Estado e erros | Configurações vinculadas à identidade do conteúdo da fonte, reiniciadas quando a fonte/conteúdo muda; mensagens para incompatibilidades, vazios e erros de configuração cobertos pelos testes. |

As funções analíticas retornam cópias ou resultados sem alterar o DataFrame original. Nulos e infinitos são ignorados nas medidas numéricas; em conjunto vazio, contagens retornam zero e agregações numéricas, inclusive soma, ficam indisponíveis. A leitura SQLite do BI usa `mode=ro`; a aplicação completa inicializa tabelas e tem escrita nas telas legadas, portanto essa propriedade não se estende ao aplicativo inteiro.

## 3. Fluxo de entrada, tratamento, filtragem, agregação e visualização

1. **Entrada:** `_selecionar_dados` em [frontend_bi.py](../../oneworld/frontend_bi.py) escolhe exemplo, upload ou tabela SQLite. Arquivos passam por `backend.ler_arquivo`; tabelas, por `fontes_sqlite.carregar_tabela`. O contrato comum é um `pandas.DataFrame`.
2. **Tratamento:** `inspecionar_colunas` valida nomes e tipos. `configurar_datas` converte somente as datas escolhidas e informa falhas. Colunas incompatíveis não recebem operações automáticas. Não há imputação, padronização universal ou limpeza automática de todos os problemas de entrada.
3. **Filtragem:** a interface constrói configurações conforme os metadados. `aplicar_filtros` combina as máscaras por AND e devolve uma cópia dos registros selecionados, preservando a entrada.
4. **Agregação:** `calcular_kpi` recebe o conjunto filtrado e a configuração explícita, retornando `ResultadoKPI(titulo, valor, erro, mensagem)`. `preparar_grafico` produz `grupo/valor` ou `intervalo/frequencia`, com validação de tipos, exclusão de grupos nulos e ordenação aplicável. Linhas não preenchem períodos ausentes.
5. **Visualização e saída:** Streamlit apresenta métricas, gráfico, dados do gráfico e registros. **O mesmo DataFrame filtrado alimenta KPIs, preparação do gráfico, tabela de registros e CSV**, mantendo o recorte consistente. A tabela do gráfico contém agregações; a exportação contém os registros filtrados.

Ao trocar de fonte ou detectar mudança de conteúdo, o painel reconstrói os controles para evitar filtros e colunas herdados do dataset anterior. Na leitura SQLite, a identidade combina esquema e hash dos valores; isso evita os defeitos documentados de BLOB não UTF-8 e pequenas atualizações de números REAL na serialização JSON anterior.

## 4. Tecnologias e separação de responsabilidades

Responsabilidades abaixo são **dos componentes**, sem atribuição nominal a integrantes.

| Camada/componente | Tecnologia e responsabilidade técnica |
| --- | --- |
| [metadados.py](../../oneworld/metadados.py), [filtros.py](../../oneworld/filtros.py) | Python e pandas: contrato tabular, classificação de tipos, conversão explícita e seleção de registros. |
| [indicadores.py](../../oneworld/indicadores.py), [analises.py](../../oneworld/analises.py) | Python e pandas: cálculos e preparação das agregações, sem Streamlit, SQL ou chamadas de IA. |
| [formatacao.py](../../oneworld/formatacao.py) | Apresentação de valores separada do cálculo. |
| [frontend_bi.py](../../oneworld/frontend_bi.py) | Streamlit: controles, estado da sessão, integração das operações, mensagens, métricas, gráficos, tabelas e download. |
| [backend.py](../../oneworld/backend.py) | Leitura reutilizada de arquivos com pandas e openpyxl para XLSX. As demais regras de importação/mapeamento e respostas simuladas ainda incluem o domínio legado de eventos/convidados. |
| [fontes_sqlite.py](../../oneworld/fontes_sqlite.py) | SQLite via `sqlite3` e pandas: catálogo de tabelas e leitura, com validação de nomes e identificadores escapados. Não implementa escrita genérica. |
| [app.py](../../app.py), [frontend.py](../../oneworld/frontend.py), [tema.py](../../oneworld/tema.py), [database.py](../../oneworld/database.py), [config.py](../../oneworld/config.py) | Infraestrutura existente: entrada, navegação, tema, configuração, esquema e CRUD legados. Integração consumida pela Parte 4; autoria não inferida. |
| [Testes](../../tests/test_frontend_bi.py) e registros de validação | `unittest`, Streamlit AppTest e bancos temporários para verificação automatizada; inspeção de navegador e capturas registradas separadamente na rodada final de 27/10/2026. |

O ambiente registrado usou Python 3.14.7, Streamlit 1.66.0, pandas 3.0.6, openpyxl 3.1.5 e SQLite 3.50.4 (ver [validação técnica atual](validacao_tecnica.md) e [ambiente registrado](evidencias/validacao_20261027/demonstracao.json)). `requirements.txt` lista Streamlit, pandas e openpyxl, sem fixar integralmente versões. Não foi acrescentada biblioteca para esta contribuição documental.

## 5. Testes efetivamente executados e resultados

A referência mais recente é a [rodada final de 27/10/2026](validacao_tecnica.md). Nesta preparação documental não houve nova execução do sistema nem da suíte. Os resultados anteriores foram conferidos nos registros; as contagens das rodadas não devem ser somadas.

| Verificação anterior | Resultado comprovado | Evidência e alcance |
| --- | --- | --- |
| Suíte automatizada, `python -B -m unittest discover -s tests -v` | **60 testes aprovados em 9,082 s**, saída 0; a rodada começou com 56 aprovados. | [Log final integral](evidencias/validacao_20261027/testes_finais.txt). Inclui KPIs, formatos, filtros, gráficos, entradas válidas/inválidas, SQLite e integração com AppTest. Upload foi injetado nos testes; não é envio manual de arquivo no navegador. |
| Compilação em memória | Fontes e testes compilados sem escrita de caches, resultado OK. | [Log](evidencias/validacao_20261027/compilacao.txt). Verificação sintática separada dos testes funcionais. |
| Demonstração programática | Seis operações nos três exemplos, filtros, gráficos, CSV reaberto e SQLite sintético com assertivas aprovadas. | [Resultados](evidencias/validacao_20261027/demonstracao.json) e [script existente](evidencias/validacao_20261027/preparar_demo.py). |
| Inspeção técnica no navegador | Educação média 8; turma A média 7; limpeza restaura média 8; vendas 450 e linhas diárias; estoque 47 e histograma; leitura do banco sintético. | [Capturas e TXT](evidencias/validacao_20261027/README.md), em cópia isolada. Não representa uso por participante do parceiro. |
| Download real do CSV | Duas linhas, mesmas colunas, ordem e células do recorte de educação; comparação por pandas aprovada. | [CSV baixado](evidencias/validacao_20261027/educacao_download_real.csv) e [comparação](evidencias/validacao_20261027/download_verificado.txt). Não há evidência de abertura manual em Excel. |
| SQLite e integridade | Leitor usa `mode=ro`; testes recusam escrita. Hash do banco sintético idêntico antes/depois das consultas; banco real preservado na rodada. | [Integridade](evidencias/validacao_20261027/resultado_integridade.json), [antes](evidencias/validacao_20261027/sqlite_visual_antes.json), [depois](evidencias/validacao_20261027/sqlite_visual_depois.json). O aplicativo completo pode escrever na inicialização e nas telas legadas. |
| Fluxo sem serviço de IA | Teste existente executado sem chaves e com sentinela que falharia caso `responder_ia` fosse chamado; aprovado. | [Validação técnica](validacao_tecnica.md) e [teste de integração](../../tests/test_frontend_bi.py). Não comprova instalação offline em uma máquina nova. |

O registro atual documenta correção do erro de formato de data inválido e da ordenação de categorias textuais/booleanas. Registros anteriores documentam identidade SQLite para BLOB/pequenas alterações REAL, ordenação do histograma e limpeza visual de filtros. São resultados do artefato, sem atribuição automática ao integrante. Os logs preservam avisos de ScriptRunContext e de overflow do teste intencional de extremos; a suíte final terminou em OK.

### Resultados com exemplos sintéticos

| Fonte e configuração | Resultado verificável | Registro |
| --- | --- | --- |
| Vendas: medida `valor`; distintos por `produto` | 4 linhas; 3 produtos; soma 450; média 112,5; mínimo 50; máximo 200. Linhas por dia: 100/200/100/50. | [Resultados](evidencias/validacao_20261027/demonstracao.json), [KPI](evidencias/validacao_20261027/04_vendas_450.png), [linhas](evidencias/validacao_20261027/06_vendas_linhas.txt). |
| Educação: média de `nota` | Geral: 3 linhas e média 8; turma A: Ana/8 e Bruno/6, 2 linhas e média 7; limpeza restaura 3 linhas e média 8. | [Filtro](evidencias/validacao_20261027/02_educacao_turma_A.txt), [limpeza](evidencias/validacao_20261027/03_limpeza.txt), [CSV](evidencias/validacao_20261027/educacao_download_real.csv). |
| Estoque: soma de `quantidade`, histograma | 12 + 30 + 5 = 47; 3 linhas; soma das frequências do histograma = 3. | [Soma](evidencias/validacao_20261027/07_estoque_47.txt), [histograma](evidencias/validacao_20261027/08_estoque_histograma.txt). |
| SQLite sintético: tabela `demo_estoque` | Caderno/12, Lapis/30 e Cabo/5; soma 47. | [Tabela e barras](evidencias/validacao_20261027/10_sqlite_barras.txt). Não são dados do parceiro ou do banco original. |

Esses resultados comprovam as operações nos cenários registrados, sem métricas de benefício social, satisfação ou tempo poupado. Teste técnico e inspeção local não substituem validação pelo parceiro. Não há nesta cópia registro de reunião, capacitação, aceite externo ou submissão acadêmica desta Parte 4.

## 6. Preparação e análise de dados

Selecionar a fonte delimita os dados de interesse. Inspecionar tipos e nulos e converter datas explicitamente prepara a análise; filtros recortam a população observada; agregações e histogramas resumem os registros; tabelas e gráficos apoiam interpretação humana. São atividades relacionadas à seleção, preparação, transformação e interpretação em KDD, sem comprovar um processo completo de descoberta de conhecimento.

A solução demonstrada realiza BI descritivo. Não implementa treinamento de modelos, previsão, classificação ou avaliação preditiva. Agregação de registros por soma/média não é aprendizado de máquina. Heurísticas locais e respostas simuladas de outros módulos não constituem integração externa de IA/BYOK concluída.

## 7. Limitações e dependências

- Uploads e configurações ficam na sessão, com reinício ao trocar fonte/conteúdo; não há salvar/reabrir painel, junção automática de datasets ou múltiplos gráficos simultâneos. Erros que interrompem a tela podem fazer controles posteriores retornar aos padrões.
- XLSX lê a primeira aba. Números textuais e conteúdos heterogêneos podem exigir tratamento na origem; não há limpeza universal. Datas requerem formato explícito. Linhas não preenchem períodos ausentes.
- Grupos nulos e medidas inválidas podem ser omitidos do gráfico conforme a operação. A origem filtrada é comum, mas cada cálculo trata ausências segundo suas regras.
- Há rótulos de histogramas truncados em telas estreitas; a tabela de dados do gráfico permite conferência. Não foram feitos ensaio de carga, avaliação de acessibilidade, matriz ampla de versões ou instalação em outra máquina.
- Backend, banco, navegação, tema e telas legadas são infraestrutura reutilizada; não se atribui sua autoria ao integrante. Leitura SQLite não implementa catálogo de datasets importados nem escrita genérica. A aplicação completa contém gravações.
- Facilidade de uso, autonomia, utilidade e benefícios precisam de avaliação real; publicação/licença da proposta de código aberto também não estão comprovadas.

Todas as ações coletivas estão em [dependencias_equipe.md](dependencias_equipe.md): autoria/versão (D01); contrato, entrada, IA, telas e persistência (D02–D06); ambiente (D07); parceiro/documentos (D08–D09); calendário (D10); licença (D11); revisão coletiva (D12); capacitação/reação (D13–D14); apresentação (D15); benefícios (D16); submissão (D17). Os papéis são encaminhamentos a confirmar, sem atribuições nominais presumidas.

## 8. Materiais para incorporação e próximos marcos

Este texto pode compor a seção técnica do relatório após revisão de autoria e integração pela equipe. Complementos: [roteiro de apresentação](roteiro_apresentacao.md), [manual](manual_dashboard.md), [capacitação](roteiro_capacitacao.md), [validação do parceiro](roteiro_validacao_parceiro.md), [avaliação em branco](avaliacao_reacao.md), [encerramento](encerramento_parte4.md) e [relato individual base](relato_individual_base.md).

Para anexos técnicos, selecionar o log de 60 testes, capturas finais/TXT, CSV verificado e manifesto da [rodada atual](evidencias/validacao_20261027/README.md). Preservar o contexto e a data das evidências. Formulários vazios são instrumentos, não resultados de aplicação.

O [planejamento](../oneworld_planejamento_execucao_v2.md) prevê **04/11/2026** (Entrega 4), **18/11/2026** (Entrega 5) e **25/11/2026** (Entrega 6): **datas previstas nos documentos, ainda sujeitas à confirmação da disciplina**. Revisão coletiva, experiências pessoais, aplicação dos instrumentos e envio seguem pendentes no [checklist](checklist.md).
