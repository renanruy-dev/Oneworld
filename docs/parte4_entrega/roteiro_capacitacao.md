# Roteiro de capacitação — Parte 4 / Entrega 5

Atualizado em 27/10/2026 (etapa documental). **Roteiro não aplicado nesta etapa.** Duração sugerida: 60 minutos, a ajustar à pessoa participante. A capacitação, a participação e os resultados observados continuam pendentes.

Objetivo: permitir que o usuário responsável selecione uma fonte, confira tipos, aplique filtros, configure indicadores e gráficos, exporte e reconheça os limites da sessão. O mesmo mecanismo atende diferentes áreas; os exemplos não impõem um domínio ao produto.

Prazos do [planejamento](../oneworld_planejamento_execucao_v2.md): **04/11/2026** (Entrega 4), **18/11/2026** (Entrega 5) e **25/11/2026** (Entrega 6), **datas previstas nos documentos, ainda sujeitas à confirmação da disciplina**.

## Preparação pela equipe — antes de agendar

- Confirmar participante, facilitador, agenda e versão a demonstrar; preencher os campos de registro abaixo apenas quando houver informação real.
- Confirmar disponibilização e abertura do sistema no ambiente de uso. As instruções do [manual](manual_dashboard.md) pressupõem ambiente preparado; esta atividade não instala nem hospeda o sistema.
- Usar a cópia isolada e as instruções do [roteiro de apresentação](roteiro_apresentacao.md). A inicialização do app completo pode escrever; o banco do projeto não é necessário aos exercícios.
- Ter os três [CSV de exemplo](../../exemplos/) disponíveis na aplicação e o manual acessível. Usar os arquivos como estão: os gabaritos abaixo se referem a esses conteúdos.
- Selecionar com os responsáveis uma tabela de uma cópia autorizada para demonstração, adequada à leitura. Como alternativa sintética já existente, usar `demo_estoque` na cópia isolada: Caderno/12, Lapis/30, Cabo/5, total 47. Não gravar dados nem alterar tabelas para executar a atividade. Se indisponível, registrar a pendência e usar os exemplos nos demais exercícios.
- Disponibilizar a [avaliação de reação em branco](avaliacao_reacao.md). Não preencher pelo participante nem presumir satisfação.

## Sequência proposta

| Tempo sugerido | Atividade |
| --- | --- |
| 0–5 min | Apresentar objetivo, fonte de dados e limites de sessão. |
| 5–12 min | Demonstrar seleção, tipos e conversão de datas. |
| 12–40 min | Participante realiza exercícios 1–6, com apoio quando necessário. |
| 40–50 min | Exercícios 7–8: upload, leitura do banco e cuidados ao sair. |
| 50–55 min | Repetir uma tarefa com menos apoio e esclarecer dúvidas. |
| 55–60 min | Convidar à avaliação de reação e registrar próximos passos. |

## Exercícios e gabaritos

Os números são resultados esperados dos exemplos, não resultados de uma capacitação realizada. Antes de cada exercício, confira a fonte e use **Limpar filtros**. Na troca de fonte, confira novamente as configurações, pois elas reiniciam. Use apresentação Número nos KPIs.

### 1. Selecionar vendas e calcular indicadores

Selecione **Exemplo: vendas**. Configure seis KPIs: Contagem de registros; Soma, Média, Mínimo e Máximo de `valor`; Valores distintos de `produto`.

**Gabarito:** 4 registros; soma 450; média 112,5; mínimo 50; máximo 200; 3 produtos distintos. Peça que a pessoa explique a diferença entre contar linhas e contar produtos distintos. A formatação visual pode acrescentar casas decimais.

### 2. Filtrar e comparar categorias

Ainda em vendas, abra **Filtros dinâmicos**, ative `categoria` e selecione apenas `Papelaria`. Configure barras, **Agrupar por** `produto`, **Agregação** Soma e **Medida** `valor`. Confira **Dados do gráfico**.

**Gabarito:** 3 de 4 registros; soma 250; média de `valor` = 250/3 (aproximadamente 83,33); barras Caneta = 200 e Borracha = 50. Clique em **Limpar filtros**: voltam 4 registros e soma 450; barras Caneta = 200, Livro = 200 e Borracha = 50.

### 3. Interpretar e filtrar datas

Com vendas sem filtros, em **Tipos de colunas e datas**, selecione `data` para interpretação temporal e informe `%Y-%m-%d`. Configure linhas, agrupamento `data`, Soma de `valor`, período dia.

**Gabarito:** 01/10/2026 = 100; 02/10 = 200; 03/10 = 100; 04/10 = 50. No período mes, outubro/2026 totaliza 450. Ative filtro de `data` de 02/10/2026 até 03/10/2026: 2 registros, soma 300, média 150 e dois pontos diários (200 e 100). Os dois limites estão incluídos.

### 4. Educação, exportação e filtros combinados

Selecione **Exemplo: educacao** e configure Média de `nota`: **8**, com 3 registros. Ative filtro `turma` e deixe apenas A: **2 registros**, Ana (8) e Bruno (6), média **7**. Exporte em **Exportar dados filtrados** e abra o CSV em planilha, importando por vírgula/UTF-8 se necessário.

**Gabarito do arquivo:** colunas `aluno,turma,nota`, somente Ana/A/8 e Bruno/A/6; sem Clara e sem coluna extra de índice. O CSV não contém as configurações ou os cartões de KPI.

Mantendo turma A, ative filtro de `nota` de 7 a 10: sobra Ana, 1 registro, média 8. Mude para 9 a 10: nenhum registro; contagem 0 e média indisponível (traço), sem falha do sistema. Limpe filtros: 3 registros e média 8. Explique por que turma A E nota de 9 a 10 não retorna Clara.

### 5. Estoque e histograma

Selecione **Exemplo: estoque**. Configure Soma de `quantidade` e depois histograma dessa coluna, com **Intervalos** = 1. Confira **Dados do gráfico**.

**Gabarito:** 3 registros, soma 47 e uma faixa com frequência 3 (valores 12, 30 e 5). A faixa conta observações; sua altura não é 47. Se mudar o número de intervalos, a soma das frequências permanece 3 neste exemplo sem nulos.

### 6. Reconhecer avisos e recuperar a análise

Retorne a vendas sem filtros. Selecione `data` como data e use temporariamente o formato incompatível `%d/%m/%Y` para os textos `2026-10-01` etc.

**Gabarito:** aviso de 4 valores fora do formato e datas consideradas nulas nesta análise. Volte a `%Y-%m-%d`: quatro datas válidas, de 01 a 04/10/2026. O CSV de origem permanece intacto. Peça que a pessoa encontre no manual a orientação para “Não foi possível ler o arquivo”, sem provocar falhas no banco.

### 7. Usar um arquivo e compreender a sessão

Envie `exemplos/educacao.csv` pelo controle de arquivos e selecione **Arquivo …: educacao.csv** em **Conjunto de dados**. Configure Média de `nota` e filtre turma A.

**Gabarito:** os mesmos 2 registros e média 7 do exercício 4. Troque para estoque e depois volte ao arquivo: a configuração anterior é reiniciada; confira a tabela completa com 3 registros e configure a média novamente para obter 8. Peça que a pessoa descreva o que guardar para repetir o trabalho: original, CSV exportado e anotação das escolhas. Não prometer recuperação após fechar ou atualizar a sessão.

### 8. Consultar o banco existente

Com a equipe, marque **Incluir tabelas do banco local**, escolha uma tabela adequada e confira colunas/quantidade. Antes do exercício, o responsável deve registrar uma contagem e, se houver coluna numérica apropriada, um total de referência obtidos independentemente. Configure o KPI correspondente e compare. Não use 450 ou 47 como gabarito do banco real.

**Alternativa verificável:** na cópia isolada, selecionar **Banco local: demo_estoque** e configurar Soma de `quantidade`: 3 registros e soma 47. Para dados de outra origem, preencher a referência independente antes de comparar.

**Critério conhecido:** a consulta do BI permite analisar a tabela sem gravá-la; a inicialização do aplicativo completo pode escrever no banco da cópia, razão para usar ambiente isolado; os resultados devem coincidir com a referência registrada para aquele conteúdo. Uma tabela vazia tem contagem 0. Cada interação consulta novamente a tabela; mudanças detectadas no conteúdo reiniciam configurações. Não provocar alterações no banco durante a capacitação. Se não houver referência ou acesso autorizado, marcar exercício pendente, sem declarar aprovação.

Fontes dos gabaritos: [CSV originais](../../exemplos/), [resultados técnicos atuais](evidencias/validacao_20261027/demonstracao.json) e [download conferido](evidencias/validacao_20261027/download_verificado.txt). Os exercícios ampliam os recortes para prática; resultados esperados não são afirmações de execução por participante. Ambiente, capacitação e aplicação da avaliação dependem de D07/D13/D14 em [dependencias_equipe.md](dependencias_equipe.md).

## Registro de execução — preencher somente após a atividade

Data/horário: ____________________  Local/modalidade: ____________________

Participante (identificação acordada): ____________________

Facilitador: ____________________  Versão/ambiente: ____________________

| Exercício | Resultado observado | Apoio necessário / dificuldade | Estado (concluído, parcial, pendente) |
| --- | --- | --- | --- |
| 1 | | | |
| 2 | | | |
| 3 | | | |
| 4 e CSV | | | |
| 5 | | | |
| 6 | | | |
| 7 | | | |
| 8 | | | |

Tabela do banco e referência independente (fonte, data, contagem/total): ____________________

Tarefa repetida com menos apoio e resultado: ____________________

Pendências, responsável e prazo acordado: ____________________

Evidência de participação autorizada e local de guarda: ____________________

Avaliação de reação: convite realizado em ______; resposta recebida em ______; registro ______. Deixar em branco se não realizado. O desempenho nos exercícios e a opinião de usabilidade são registros diferentes.
