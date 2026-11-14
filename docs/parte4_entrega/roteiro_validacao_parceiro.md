# Roteiro de validação com o parceiro — Parte 4

Atualizado em 27/10/2026 (Prompt 2). **Situação: PENDENTE DE APLICAÇÃO.**
Este documento é um formulário em branco. Não houve contato, reunião, participante,
feedback ou aceite externo registrado nesta etapa.

Prazos do [planejamento](../oneworld_planejamento_execucao_v2.md): **04/11/2026** (Entrega 4), **18/11/2026** (Entrega 5) e **25/11/2026** (Entrega 6), **datas previstas nos documentos, ainda sujeitas à confirmação da disciplina**.

## Objetivo e distinção entre as verificações

O teste técnico foi executado localmente pelo agente, em cópia isolada, com dados
sintéticos. Conferiu cálculos, controles, gráficos, limpeza, download e leitura
SQLite. Os resultados estão em [evidências atuais](evidencias/validacao_20261027/README.md), com 60 testes aprovados no log final. Não houve nova execução nesta preparação documental.

A validação externa só ocorrerá quando uma pessoa do parceiro executar as tarefas
e relatar sua experiência. Os resultados técnicos não preenchem os campos abaixo,
não demonstram facilidade de uso para o participante e não constituem aprovação.
O parceiro avalia a utilidade de um BI genérico; não torna seu segmento obrigatório.

## Preparação pelo facilitador, antes da aplicação real

1. Combinar a sessão e registrar os dados abaixo somente quando ela ocorrer.
2. Abrir uma cópia local isolada com a configuração de tema original e os exemplos
   `vendas.csv`, `educacao.csv` e `estoque.csv`. Não usar dados pessoais de produção.
3. Usar a cópia isolada indicada no [roteiro de apresentação](roteiro_apresentacao.md),
   que contém a tabela sintética `demo_estoque`. A inicialização completa pode
   escrever nesse banco de demonstração. Não criar tabelas no banco original.
4. Abrir Dashboard. Explicar que se escolhem colunas e operações e que os arquivos
   e as configurações ficam na sessão. Não é necessária chave de IA.
5. Pedir ao participante que pense em voz alta. Deixar que tente primeiro;
   registrar ajuda oferecida, erros e hesitações sem sugerir uma resposta positiva.
6. Para o CSV, disponibilizar um leitor local já instalado. Registrar qual foi
   usado. Conferir linhas e cabeçalhos; o separador de apresentação pode variar.

Data/hora e fuso: ____________________  Local/modalidade: ____________________

Versão/hash do frontend utilizado: __________________________________________

Participante e papel no parceiro (preencher no ato): __________________________

Facilitador: ____________________  Leitor de CSV utilizado: __________________

Fontes utilizadas e permissão, se necessária: _______________________________

## Tarefas para o participante

Os valores podem aparecer como `8.00` e `7.00`. Isso significa média 8 e média 7.
Em cada linha, registrar **concluiu sozinho / com ajuda / não concluiu / não executado**, resultado
real, dificuldades, sugestões e aceite. Não marcar previamente.

| Nº | Tarefa simples | Resultado esperado |
| --- | --- | --- |
| 1 | Escolha **Exemplo: vendas**. Abra **Configurar KPI 1** e escolha **Soma**, coluna **valor**. | 4 de 4 registros; KPI **450**. |
| 2 | Em vendas, escolha gráfico **barras**, agrupamento **produto**, agregação **Soma**, medida **valor**. | Borracha = 50, Caneta = 200, Livro = 200. |
| 3 | Em **Tipos de colunas e datas**, interprete **data** com `%Y-%m-%d`. Escolha **linhas**, agrupe por **data**, **Soma** de **valor**, período **dia**. | Datas em ordem de 01 a 04/10/2026; valores 100, 200, 100 e 50. |
| 4 | Troque para **Exemplo: educacao**. Configure **Média** de **nota**. | 3 de 3 registros; média **8**. Colunas de vendas e período temporal não permanecem nos controles. |
| 5 | Em educação, configure barras por **turma**, agregação **Média**, medida **nota**. | Turma A = 7 e B = 10. Linhas temporais não estão disponíveis sem coluna de data. |
| 6 | Abra **Filtros dinâmicos**, marque **Filtrar turma** e deixe apenas **A** em **Valores de turma**. | 2 de 3 registros; Ana/A/8 e Bruno/A/6; média **7**; gráfico só com A = 7. |
| 7 | Clique em **Exportar dados filtrados**, abra o CSV baixado e compare com a tabela. | Cabeçalhos aluno,turma,nota; exatamente Ana,A,8 e Bruno,A,6; nenhuma linha de Clara/B. |
| 8 | Clique em **Limpar filtros**. | Caixas de filtro desmarcadas; seletor de valores desaparece; 3 de 3 registros; média **8**; Clara volta à tabela e B ao gráfico. |
| 9 | Ative turma A outra vez e troque para **Exemplo: estoque**. Abra filtros e configure **Soma** de **quantidade**. Escolha **histograma** de **quantidade**. | Filtros antigos desaparecem; somente produto,quantidade,categoria; filtros desmarcados; 3 registros; soma **47**; histograma em ordem numérica e frequências somando 3. |
| 10 | Marque **Incluir tabelas do banco local**, escolha **Banco local: demo_estoque** e configure **Soma** de **quantidade**. Compare a tabela. | Leitura SQLite indicada na tela; Caderno/12/Papelaria, Lapis/30/Papelaria, Cabo/5/Eletronicos; 3 registros; soma **47**. |

Se o banco estiver indisponível, concluir as tarefas 1–9 com os exemplos e marcar a tarefa 10 como **não executada**, com motivo. Capturas anteriores são apoio, sem equivaler à execução pelo participante. Se usar dados reais em outra ocasião, substituir os gabaritos por referências independentes e registrar origem/permissão antes da tarefa. Não presumir o total 47 para o banco real. Agenda, dados adequados e retorno dependem de D08; ambiente, capacitação e avaliação dependem de D07/D13/D14 em [dependencias_equipe.md](dependencias_equipe.md).

## Registro a preencher durante a sessão real

| Tarefa | Execução e resultado real | Dificuldades observadas / ajuda oferecida | Sugestões do participante | Aceite da tarefa: sim / parcial / não |
| --- | --- | --- | --- | --- |
| 1 | __________________ | __________________ | __________________ | __________________ |
| 2 | __________________ | __________________ | __________________ | __________________ |
| 3 | __________________ | __________________ | __________________ | __________________ |
| 4 | __________________ | __________________ | __________________ | __________________ |
| 5 | __________________ | __________________ | __________________ | __________________ |
| 6 | __________________ | __________________ | __________________ | __________________ |
| 7 | __________________ | __________________ | __________________ | __________________ |
| 8 | __________________ | __________________ | __________________ | __________________ |
| 9 | __________________ | __________________ | __________________ | __________________ |
| 10 | __________________ | __________________ | __________________ | __________________ |

Perguntas após as tarefas (anotar as respostas reais):

- Qual tarefa foi mais difícil? ______________________________________________
- Quais nomes ou controles não ficaram claros? _______________________________
- O que ajudaria a analisar um conjunto da sua rotina? _______________________
- Que mudança você priorizaria? _____________________________________________

## Aceite externo — preencher somente após a aplicação

Decisão do participante: [ ] Aceito  [ ] Aceito com pendências  [ ] Não aceito

Justificativa e condições: __________________________________________________

Pendências, responsável acordado e prazo acordado: ___________________________

Identificação/confirmação do participante e data: ____________________________

Evidências reais autorizadas e local do registro: ____________________________

**Estado atual permanece PENDENTE.** Não inferir aceite por ausência de resposta,
por aprovação dos testes técnicos ou pela existência deste roteiro.
