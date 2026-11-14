# Relato individual — base factual da Parte 4

Atualizado em **27/10/2026** (Prompt 2) para a Entrega 6. **Rascunho incompleto:** preencher as experiências pessoais, confirmar a autoria com a equipe e adaptar ao modelo da disciplina antes de enviar. Nenhum trecho abaixo constitui depoimento em primeira pessoa. Campos `[PREENCHER ...]` não são respostas nem experiências presumidas.

Aplicado o contexto mestre do [planejamento v2](../oneworld_planejamento_execucao_v2.md), base disponível nesta cópia. O [encerramento técnico](encerramento_parte4.md) detalha evidências e limites. A Casa Grande Eventos é parceira de validação de um BI genérico, não o domínio obrigatório do produto.

Prazos do [planejamento](../oneworld_planejamento_execucao_v2.md): **04/11/2026** (Entrega 4), **18/11/2026** (Entrega 5) e **25/11/2026** (Entrega 6), **datas previstas nos documentos, ainda sujeitas à confirmação da disciplina**.

## 1. Identificação e participação — informação pessoal pendente

- **Nome:** [PREENCHER PELO INTEGRANTE].
- **Curso, turma, disciplina e identificação acadêmica exigida:** [PREENCHER CONFORME MODELO].
- **Período efetivo de participação:** [PREENCHER DATAS REAIS].
- **Responsabilidades acordadas com a equipe:** [PREENCHER E CONFIRMAR COM A EQUIPE].
- **Versão final a que o relato se refere:** [IDENTIFICAR COM A EQUIPE].

## 2. Fatos técnicos disponíveis como contexto

Os fatos abaixo descrevem a solução encontrada e seus registros. Só podem ser convertidos em afirmações de participação individual após confirmação de quais tarefas o integrante realizou, revisou ou acompanhou. O histórico Git local não fornece comprovação suficiente de autoria individual.

| Fato comprovado no material | Evidência | Limite para o relato |
| --- | --- | --- |
| Motor recebe DataFrame e configurações, com seis operações de KPI, filtros genéricos e preparação de gráficos. | [indicadores](../../oneworld/indicadores.py), [filtros](../../oneworld/filtros.py), [análises](../../oneworld/analises.py), [contratos](../indicadores_genericos.md) | Não afirmar que o integrante criou todos esses componentes sem confirmar sua participação. |
| Cálculo e formatação estão separados da interface Streamlit; o mesmo recorte alimenta KPI, gráfico, tabela e CSV. | [formatação](../../oneworld/formatacao.py), [interface de BI](../../oneworld/frontend_bi.py), [validação técnica](validacao_tecnica.md) | Não atribuir autoria da infraestrutura reutilizada nem declarar backend inteiro genérico. |
| Foram documentadas correções de identidade SQLite para BLOB/REAL, ordem do histograma, controles após limpeza, formato inválido de datas e categorias mistas texto/booleano. | [Validação técnica](validacao_tecnica.md), [rodada atual](evidencias/validacao_20261027/README.md) | Diferenciar identificar, implementar, testar, revisar e apenas conhecer uma correção. |
| A rodada final de 27/10/2026 registrou 56 testes iniciais e **60 finais aprovados em 9,082 s**. Registros anteriores de 52/55/56 são históricos. | [Log final atual](evidencias/validacao_20261027/testes_finais.txt), [validação](validacao_tecnica.md) | Rodadas sucessivas, sem soma dos totais. Não houve nova execução da suíte na preparação documental do Prompt 2. |
| Exemplos sintéticos mostram vendas soma 450/média 112,5; educação média 8, turma A média 7; estoque soma 47. | [Demonstração atual](evidencias/validacao_20261027/demonstracao.json), [registros da interface](evidencias/validacao_20261027/README.md) | Não são dados reais do parceiro nem medições de benefício. |
| CSV baixado da turma A foi reaberto por pandas e comparado à tabela esperada, com duas linhas e média 7. | [CSV](evidencias/validacao_20261027/educacao_download_real.csv), [comparação](evidencias/validacao_20261027/download_verificado.txt) | Não há registro de abertura manual em Excel. |
| Fluxo básico passou sem chave/chamada de IA; leitura SQLite do BI usa conexão somente de leitura. | [Validação](validacao_tecnica.md), [leitor](../../oneworld/fontes_sqlite.py) | Aplicação completa tem inicialização/escrita legada; instalação offline nova não foi demonstrada. |
| Manual, roteiros de apresentação/capacitação/validação, avaliação em branco e textos de entrega foram preparados ou atualizados nesta pasta. | [Checklist dos materiais](checklist.md), [apresentação](roteiro_apresentacao.md), [encerramento](encerramento_parte4.md) | Preparação não comprova capacitação, reação coletada, revisão coletiva ou submissão. |

## 3. Registro das contribuições pessoais — a preencher

Preencher uma linha por tarefa efetiva. Informar o tipo de participação evita atribuir ao integrante todo o trabalho existente no componente. Indicar uso de ferramentas e assistência quando pertinente às regras acadêmicas, sem presumir uma forma de trabalho.

| Tarefa e período real | Participação individual efetiva | Decisão ou resultado verificável | Evidência e confirmação |
| --- | --- | --- | --- |
| [PREENCHER] | [IMPLEMENTAÇÃO / REVISÃO / TESTE / DOCUMENTAÇÃO / OUTRA — DESCREVER] | [PREENCHER SEM AMPLIAR O ALCANCE] | [ARQUIVO, REGISTRO OU REUNIÃO REAL; CONFIRMAÇÃO DA EQUIPE] |
| [ADICIONAR SOMENTE SE HOUVER OUTRA TAREFA] | [PREENCHER] | [PREENCHER] | [PREENCHER] |

**Texto pessoal sobre a atuação:** [PREENCHER PELO INTEGRANTE: explicar as tarefas realmente assumidas, o trabalho feito em conjunto e como a contribuição se conectou aos outros módulos. Não copiar a lista técnica como se toda ela fosse autoria individual.]

## 4. Experiências, dificuldades e aprendizados — exclusivamente pessoais

- **Experiência concreta:** [PREENCHER: uma situação real, seu contexto e a atuação pessoal; incluir data aproximada se lembrada].
- **Dificuldade efetivamente vivida:** [PREENCHER: o que ocorreu, como foi percebido, tentativas realizadas e apoio recebido].
- **Decisão e justificativa:** [PREENCHER: decisão de que participou, alternativa considerada e motivo real da escolha].
- **Aprendizado técnico:** [PREENCHER: o que passou a compreender ou fazer, ligado a uma tarefa concreta e a uma evidência quando disponível].
- **Aprendizado sobre colaboração:** [PREENCHER: experiência real de comunicação, divisão de tarefas, revisão ou integração].
- **Limite ou tarefa que não conseguiu concluir:** [PREENCHER SE OCORREU: motivo, estado atual e encaminhamento; não inventar dificuldade para completar o campo].
- **O que faria diferente:** [PREENCHER: reflexão própria e melhoria proposta, sem apresentar intenção como resultado].

## 5. Contato com usuário, comunidade e avaliação — confirmar ocorrência

**Participação pessoal em demonstração, capacitação ou coleta de retorno:** [PREENCHER: se ocorreu, informar papel, data, contexto, tarefas e registro autorizado; se não participou, declarar isso de forma factual. Se não souber se ocorreu, marcar informação pendente.]

**Retorno real observado:** [PREENCHER SOMENTE COM REGISTRO: distinguir observação própria, fala do participante e interpretação. Não inventar citações, aprovação ou satisfação.]

**Reflexão pessoal sobre autonomia e comunidade:** [PREENCHER: relacionar funcionalidades a possibilidades de uso, preservando o caráter de hipótese quando não houve avaliação. Não quantificar tempo poupado nem vincular ODS/ESG sem justificativa e evidência.]

Nesta cópia, não há evidência de homologação do parceiro, capacitação realizada ou avaliação de reação preenchida. Eventuais registros externos devem ser identificados e conferidos antes da incorporação ao relato. Ações dependentes de colegas estão em [dependencias_equipe.md](dependencias_equipe.md).

## 6. Revisão e conclusão do relato — pendente

- [ ] Campos pessoais preenchidos ou marcados como não aplicáveis, com justificativa factual.
- [ ] Tarefas, autoria e divisão com colegas confirmadas; referências coerentes com a participação real.
- [ ] Distinção entre implementação, teste técnico, experiência pessoal e benefício ainda não medido preservada.
- [ ] Modelo, extensão, critérios e calendário conferidos com a equipe/disciplina.
- [ ] Texto final lido e aprovado pelo próprio integrante; incorporação ao relatório e envio registrados separadamente.

## 7. Perguntas pessoais para finalizar o relato

1. Qual nome, identificação acadêmica e período de participação devem constar?
2. Quais tarefas foram combinadas para você e quais você efetivamente realizou? Em quais arquivos, decisões ou registros isso aparece?
3. Em cada tarefa, você implementou, testou, revisou, documentou ou acompanhou? O que foi feito junto com colegas e como dividir os créditos?
4. Quais ferramentas, referências e apoios você utilizou e como devem ser declarados segundo as regras da disciplina?
5. Qual situação concreta melhor representa sua participação e o que você fez nela?
6. Que dificuldade você realmente enfrentou, quais tentativas fez e que ajuda recebeu? Houve algo que ficou sem solução?
7. De qual decisão técnica participou e por que essa escolha foi feita?
8. O que aprendeu tecnicamente e qual tarefa mostra esse aprendizado?
9. O que aprendeu sobre colaboração e integração com o restante da equipe?
10. Você participou de demonstração, capacitação ou conversa com o parceiro? Quando, em qual papel e onde está o registro? Se não participou, qual foi o alcance real da sua atuação?
11. Que retorno de usuário você observou diretamente e que evidência permite relatá-lo? Quais benefícios continuam apenas como hipótese?
12. O que faria diferente em uma próxima versão e qual contribuição ainda pretende realizar?
