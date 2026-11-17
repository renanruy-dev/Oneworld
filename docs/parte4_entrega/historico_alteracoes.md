# Histórico de alterações — OneWorld / Parte 4

Registro criado em **05/11/2026**, fuso America/Sao_Paulo.

## Resultado da verificação

**A entrega da nossa branch mudou o conteúdo e o subtítulo do Dashboard. Não houve renomeação das páginas do menu nem do nome padrão OneWorld no código comparado.**

O commit `23a35be6211a1126e24c46d198264e0aae01b124`, de **03/11/2026 às 17:28:50 -03:00**, está registrado em nome de `felipecarreira07`, com mensagem `feat: adiciona dashboard de BI genérico`. Ele está na branch local `felipe/parte-oneworld` e na referência local `origin/felipe/parte-oneworld`.

## Mudanças visíveis confirmadas

Comparação: versão inicial `7d884f5` → entrega `23a35be`.

| Local | Antes | Depois | Evidência |
| --- | --- | --- | --- |
| Subtítulo do Dashboard | Visão geral dos dados e indicadores | Análise configurável de conjuntos de dados | `oneworld/frontend.py`, função `pagina_dashboard` |
| Conteúdo do Dashboard | Painel fixo de eventos e convidados | Interface de BI configurável, chamada por `mostrar_dashboard` | `oneworld/frontend.py` e novo `oneworld/frontend_bi.py` |
| Indicadores | Eventos, Convidados previstos, Receita prevista, Pendências e Convidados confirmados | Indicadores configurados conforme o dataset e a operação escolhida | Remoção do bloco fixo em `pagina_dashboard`; controles no módulo de BI |
| Gráficos e blocos do Dashboard | Receita prevista por mês, Eventos por status, Notificações e Próximos eventos | Gráfico configurável, filtros, tabela e exportação do conjunto selecionado | Mesmo diff; os antigos blocos deixam de ser desenhados nessa página |
| Filtros ao mudar de página | Limpeza apenas das chaves em `FILTROS`, quando configurada | Inclui chaves com prefixo `bi_cfg_filtro_` | `oneworld/frontend.py`, função `main` |

A mudança do Dashboard é uma substituição de conteúdo e comportamento, além da troca do subtítulo. Não foi apenas uma alteração de nome.

## Nomes e páginas que já existiam

Na versão inicial `7d884f5`, de **20/10/2026 às 23:58:52 -03:00**, registrada por **Renan**, a lista `PAGINAS` em `oneworld/config.py` já era:

- Dashboard
- Eventos
- Convidados & Planilhas
- Dados Externos
- Orientação IA
- Anotações
- Configurações

Essa lista permanece igual na entrega auditada. O nome padrão `OneWorld` em `oneworld/config.py` e o `page_title="OneWorld"` em `app.py` também permanecem iguais. Não há renomeação de arquivos no diff da entrega (`git diff --name-status` mostra apenas adições e modificações).

`app.py`, `oneworld/config.py`, `oneworld/backend.py`, `oneworld/tema.py` e `README.md` não têm diferenças entre esses dois commits. As outras telas e suas rotas não foram renomeadas no diff de `oneworld/frontend.py`.

## Demais alterações da entrega

O commit contém **18 arquivos alterados, 1.454 inserções e 51 exclusões**:

- **Módulos adicionados:** `oneworld/analises.py`, `filtros.py`, `fontes_sqlite.py`, `formatacao.py`, `frontend_bi.py`, `indicadores.py` e `metadados.py`.
- **Exemplos adicionados:** `exemplos/demonstrar_indicadores.py`, `educacao.csv`, `estoque.csv` e `vendas.csv`.
- **Testes adicionados:** `tests/test_bi.py`, `test_fontes_sqlite.py`, `test_frontend_bi.py` e `test_indicadores.py`.
- **Interface modificada:** `oneworld/frontend.py`, conforme descrito acima, incluindo atualização da descrição do módulo.
- **Banco:** `oneworld/database.py` recebeu importação e uso de `typing.cast` em duas leituras. O diff não renomeia tabelas ou campos e não contém migração.
- **Arquivos ignorados:** `.gitignore` passou a incluir `.env` e `.env.*`, com exceção para `.env.example`; comentários foram traduzidos para inglês.

## Documentação e limites da apuração

- A pasta `docs/` estava **não rastreada no Git** (`?? docs/`) antes desta auditoria. Ela reúne planejamento, manuais, relatórios, logs e evidências da Parte 4. Este histórico passa a fazer parte dela. Esses documentos não integram o commit `23a35be`.
- A referência local `origin/patch-romulo` também foi comparada à versão inicial: não apresenta diferenças em `app.py`, `oneworld/config.py` ou `oneworld/frontend.py`. Tem outras mudanças, que não devem ser atribuídas à nossa entrega.
- As referências remotas acima são as disponíveis localmente. Esta auditoria não consultou o estado atual do GitHub, outras máquinas, versões fora do repositório ou configurações persistidas do banco. Não identifica quem possa ter alterado nomes por dentro do aplicativo.
- Como não foram indicados os nomes ou as páginas específicos vistos pelo colega, a conclusão cobre as alterações comprovadas nesta cópia. Outras mudanças precisam ser confrontadas com o trecho ou a versão correspondente.

