# Checklist final — Parte 4 / Prompt 3

Atualização de 14/11/2026 disponível em [status da entrega](status_entrega.md). Os registros abaixo preservam suas datas históricas.

Conferência de **27/10/2026** (America/Sao_Paulo). **Parte 4 pronta para revisão e demonstração local no ambiente existente.** Não foi identificada pendência técnica local corrigível no escopo autorizado. O projeto coletivo não está declarado concluído: faltam decisões da equipe, atividades com pessoas e comprovação de submissão.

Este é o estado final de referência. O conteúdo anterior está preservado ao final como histórico; suas marcações e contagens não substituem os três grupos atuais. Comece por [leia_primeiro.md](leia_primeiro.md).

## A. Concluído e verificado pelo Codex

- [x] Conferir os materiais de entrega com os sete módulos técnicos permitidos, a navegação e os componentes compartilhados reutilizados, sem alterá-los; manual compatível com os rótulos e controles atuais.
- [x] Confirmar **19 fontes** e **61 artefatos** sem divergência SHA-256 em relação ao [manifesto da rodada funcional](evidencias/validacao_20261027/manifesto.json). A evidência de **60 testes aprovados em 9,082 s** permanece aplicável aos arquivos conferidos; não é uma nova execução desta suíte.
- [x] Confirmar os **20 arquivos de código/apoio** da cópia de demonstração contra o projeto e as versões instaladas de Python/pandas/Streamlit/openpyxl iguais às registradas. Não foi repetida inspeção visual, instalação ou validação integral sem motivo.
- [x] Conferir gabaritos nos CSV: vendas 4 registros, soma 450/média 112,5; educação média 8 e turma A média 7/duas linhas; estoque soma 47/três observações; linhas de vendas 100/200/100/50, filtros e demais resultados dos exercícios.
- [x] Confirmar correspondência do CSV baixado com o recorte da turma A; evidências de gráficos, filtros, troca de datasets e SQLite identificadas na [validação técnica](validacao_tecnica.md) e no [índice visual](evidencias/validacao_20261027/README.md).
- [x] Conferir reprodução do roteiro por inspeção de comandos, arquivos, caminhos e evidência funcional existente; orientar abertura em **nova cópia temporária** do ambiente sintético para preservar a pasta histórica e o banco real. Comando completo no [guia inicial](leia_primeiro.md#como-abrir-e-demonstrar).
- [x] Explicitar que `preparar_demo.py` também sobrescreve resultados históricos na pasta de evidências; sua reexecução não é necessária para a demonstração. Não executado nesta conferência.
- [x] Conferir consistência dos limites: estado da sessão sem salvar/reabrir painel, reinício ao trocar fonte/conteúdo, um gráfico, primeira aba XLSX, datas explícitas, omissões de nulos conforme operação, leitura SQLite do BI sem estender essa garantia ao aplicativo completo, IA externa e benefícios não comprovados.
- [x] Manter capacitação, avaliação e aceite sem preenchimento fictício; relato pessoal e autoria humana continuam pendentes de informação verdadeira.
- [x] Revisar links locais dos materiais atuais e separar as dependências D01–D17 por impacto. Textos, manual, roteiros, instrumentos e síntese técnica preparados para revisão.
- [x] Criar [leia_primeiro.md](leia_primeiro.md), atualizar este checklist e as orientações de demonstração/validação; registrar a [conferência final](logs/conferencia_final.json). Nenhuma correção técnica necessária; nenhuma suíte repetida nesta rodada.
- [x] Preservar código/testes, banco real, dependências, configuração compartilhada, documentos acadêmicos originais e evidências preexistentes. Integridade antes/depois registrada no log. Sem commits, mensagens, envios ou publicações.

**Alcance:** conferência final documental, de integridade e de gabaritos; resultado funcional amparado na execução anterior preservada. Não comprova homologação, capacitação ou envio acadêmico.

## B. Dependências de outros integrantes, sem alterar suas partes

Os responsáveis são papéis a confirmar; a ausência de comprovação nesta cópia não prova ausência de trabalho em outra versão. Critérios e encaminhamentos completos em [dependencias_equipe.md](dependencias_equipe.md).

| Dependência | Papel a confirmar | Impacto / critério para encerrar |
| --- | --- | --- |
| D01/D12 — autoria, versão e integração documental | Gestão, integração, documentação e integrantes | Confirmar participação e versão; integrar/revisar insumos aos artefatos oficiais e registrar aprovação coletiva. Sem isso, relato e relatório coletivo não podem ser tratados como finais. |
| D02/D03 — contrato e suporte de entrada | Backend, banco e importação | Acordar tipos, nulos, datas, atualização, catálogo/escrita e formatos; comprovar o fluxo incluído ou adiar explicitamente. Não bloqueia exemplos locais, mas limita promessas sobre integração e entradas. |
| D04/D05 — IA/BYOK e telas legadas | IA, frontend e integração | Confirmar implementação ou adiamento de IA e coerência das telas gerais. BI local independe de IA; aplicativo completo pode escrever na inicialização, por isso a demonstração é isolada. |
| D06 — persistência | Banco e frontend | Acordar escopo ou implementar/testar pelos responsáveis. Não prometer salvar/reabrir uploads ou painel no estado atual. |
| D07 — ambiente integrado e disponibilização | Qualidade, integração e gestão | Comprovar abertura/roteiro na máquina de uso; não há instalador/hospedagem nem instalação em outra máquina demonstrados nesta contribuição. |
| D09/D10 — documentos e orientações vigentes | Gestão, documentação e disciplina | Identificar documentos finais do parceiro e confirmar rubrica, modelos, calendário, canal e responsáveis. Impedem consolidar exigências acadêmicas como atendidas. |
| D11 — licença e publicação, se mantida a proposta | Equipe e responsável pelo repositório | Decidir licença/publicação e comprovar quando aplicável; não declarar projeto publicado/open source apenas pela presença dos arquivos. |

Nenhuma dessas partes foi alterada. Persistência, novas entradas e IA não foram transformadas em tarefas técnicas locais obrigatórias sem decisão de escopo. D08 e D13–D17 exigem atividades humanas/externas e aparecem no grupo C.

## C. Ações que exigem pessoas ou acesso externo

- [ ] **Sua revisão:** ler materiais, conferir participação efetiva e preencher identificação, experiências, dificuldades e aprendizados no [relato individual](relato_individual_base.md). Confirmar autoria/divisão com colegas (D01).
- [ ] **Aprovação da equipe:** validar versão, escopo e dependências do grupo B; consolidar e aprovar documentos e apresentação oficiais (D01/D12). Papéis e prazos não estão acordados por este checklist.
- [ ] **Demonstração ao parceiro:** confirmar agenda, participantes, documentos e dados autorizados; aplicar o [roteiro](roteiro_validacao_parceiro.md), registrar tarefas, dificuldades, retorno e aceite ou pendências reais (D08/D09).
- [ ] **Capacitação:** disponibilizar o [manual revisado](manual_dashboard.md), realizar os [exercícios](roteiro_capacitacao.md) e registrar participação, ajuda e resultados (D13).
- [ ] **Avaliação e tratamento de retorno:** aplicar a [avaliação de reação](avaliacao_reacao.md) após uso, guardar respostas reais e decidir correções/retestes ou adiamentos; comprovar benefícios antes de afirmá-los (D14/D16).
- [ ] **Apresentação e aprovação final:** ensaiar a versão escolhida, dividir falas e conferir contingência; revisar resultados, créditos e eventuais relações ODS/ESG segundo a rubrica (D12/D15/D16).
- [ ] **Envio acadêmico:** confirmar calendário, modelos, canal e responsáveis; obter aprovação da equipe, apresentar e submeter as entregas, guardando arquivos e recibos/protocolos (D10/D17). Datas 04/11, 18/11 e 25/11/2026 são previsões documentais sujeitas à confirmação da disciplina.

Somente essas decisões/informações e atividades com pessoas impedem os encerramentos restantes conhecidos. Não há nova pendência local identificada no mecanismo de BI ou nos materiais preparados. Revisão pessoal, aceite da equipe, homologação do parceiro e submissão são estados distintos.

---

<details>
<summary>Histórico preservado das rodadas anteriores — não usar como estado atual</summary>

# Checklist atual — materiais da Parte 4 / Prompt 2

Atualizado em **27/10/2026**. Esta seção é a referência atual de preparação documental. As seções seguintes preservam o histórico das etapas anteriores; afirmações de “última execução” ou “atual” dentro delas se referem à época de cada registro. A referência técnica mais recente é **60 testes aprovados**, conforme [log existente](evidencias/validacao_20261027/testes_finais.txt) e [validação técnica](validacao_tecnica.md). Nesta preparação documental não houve nova execução do aplicativo ou da suíte.

## Materiais concluídos para revisão e uso pela equipe

- [x] [contribuicao_entrega4.md](contribuicao_entrega4.md): problema, solução, recursos existentes, fluxo, tecnologias, testes anteriores, resultados, limites e dependências.
- [x] [roteiro_apresentacao.md](roteiro_apresentacao.md): demonstração curta, resultados esperados, cópia isolada e contingência com exemplos/capturas.
- [x] [manual_dashboard.md](manual_dashboard.md): dados, tipos/datas, filtros, KPIs, gráficos, exportação, mensagens e limitações em linguagem de usuário.
- [x] [roteiro_capacitacao.md](roteiro_capacitacao.md): oito exercícios, gabaritos verificáveis e registro em branco.
- [x] [roteiro_validacao_parceiro.md](roteiro_validacao_parceiro.md): tarefas observáveis, resultados esperados, dificuldades, sugestões e aceite em branco; tabela sintética alinhada a demo_estoque.
- [x] [avaliacao_reacao.md](avaliacao_reacao.md): questionário breve sobre facilidade, compreensão, utilidade e dificuldades; sem respostas.
- [x] [encerramento_parte4.md](encerramento_parte4.md): síntese técnica final, resultados comprovados, limites e possibilidades futuras.
- [x] [relato_individual_base.md](relato_individual_base.md): fatos técnicos separados de autoria e campos pessoais a preencher pelo integrante.
- [x] [dependencias_equipe.md](dependencias_equipe.md): D01–D17 preservados, papéis a confirmar e critérios de encerramento; preparação não encerra ações coletivas.
- [x] [relatorio_equipe.md](relatorio_equipe.md) alinhado à referência de 60 testes, preservando o registro histórico da Etapa 5.
- [x] Contagens, datas, gabaritos, fontes, arquivos e distinção entre teste técnico e validação externa revisados entre os materiais.
- [x] Código, banco, relatórios acadêmicos originais e arquivos fora de docs/parte4_entrega/ preservados; sem alteração dos logs, capturas, manifestos ou cópias de demonstração existentes.

Conferência documental, aritmética dos gabaritos e integridade registradas em [logs/revisao_materiais.json](logs/revisao_materiais.json). Essa conferência não é uma nova suíte funcional nem avaliação de usuário.

## Pendências pessoais, coletivas ou externas — não concluídas por esta preparação

- [ ] Integrante preencher identificação, participação efetiva, experiências, dificuldades e aprendizados; confirmar autoria com a equipe (D01).
- [ ] Equipe confirmar versão, contrato de dados, integração, ambiente de uso e limites de módulos legados/IA/persistência (D02–D07).
- [ ] Confirmar documentos do parceiro e agenda; aplicar roteiro, registrar execução real, dificuldades e aceite ou pendências (D08–D09).
- [ ] Confirmar rubrica, calendário, formato e responsáveis; consolidar/revisar os textos na versão acadêmica oficial (D10/D12).
- [ ] Confirmar publicação/licença se mantida a proposta open source (D11).
- [ ] Disponibilizar o manual e realizar capacitação, coletar reação e tratar retorno real (D13–D14).
- [ ] Ensaiar e realizar apresentação; avaliar hipóteses de benefício apenas com evidência (D15–D16).
- [ ] Submeter as entregas e arquivar comprovantes pelo responsável definido (D17).

Não foram enviados arquivos, publicados materiais ou feitos contatos nesta etapa. Material preparado não equivale a reunião, capacitação, aceite ou envio.

## Calendário documental — confirmação ainda pendente

| Marco | Data prevista nos documentos | Situação |
| --- | --- | --- |
| Entrega 4 — desenvolvimento e demonstração | **04/11/2026** | Sujeita à confirmação da disciplina. |
| Entrega 5 — disponibilização, manual e capacitação | **18/11/2026** | Sujeita à confirmação da disciplina. |
| Entrega 6 — apresentação e relatório final | **25/11/2026** | Sujeita à confirmação da disciplina. |

Fonte: [planejamento v2](../oneworld_planejamento_execucao_v2.md). Não foram consultados canais acadêmicos ou de comunicação nesta preparação.

---

# Histórico — execução anterior do Prompt 1 em 27/10/2026

Esta seção preserva o registro da rodada técnica anterior ao Prompt 2; os estados documentais atuais estão no início deste arquivo. Referência atual: **60 testes aprovados** em [validação técnica](validacao_tecnica.md), após 56 testes iniciais aprovados.

## a) Concluído e verificado

- [x] Ler os quatro documentos solicitados e auditar a implementação existente antes de alterar código.
- [x] Executar suíte existente (56 OK), corrigir dois defeitos reais dentro da lista e executar suíte final (60 OK).
- [x] Validar seis KPIs, formatos, filtros, três gráficos, nulos/vazios/erros, precisão e preservação das entradas.
- [x] Validar CSV/JSON/XLSX e consistência entre KPI, gráfico, tabela e exportação; download real comparado ao CSV esperado.
- [x] Validar SQLite somente leitura, bloqueio de escrita, identificadores, BLOB e atualização de conteúdo com banco temporário.
- [x] Validar troca e retorno de datasets, opções atuais dos seletores e descarte de seis KPIs/configurações/filtros/datas antigos.
- [x] Inspecionar visualmente vendas, educação, estoque, filtro/limpeza, linhas, histograma, erro/recuperação de data e SQLite sintético em nova cópia isolada.
- [x] Registrar capturas finais, resultados, logs, script reproduzível e manifesto em [evidências atuais](evidencias/validacao_20261027/README.md).
- [x] Confirmar hash idêntico do banco real e dos arquivos fora da lista. Só quatro arquivos de código/testes permitidos alterados.
- [x] Encerrar aba e servidor da inspeção; não instalar bibliotecas, fazer commits, publicar ou enviar mensagens/arquivos.

## b) Dependência de outro integrante

- [ ] Acordar catálogo/escrita genérica e contrato coletivo de dados com backend/banco (D02/D03 existentes).
- [ ] Definir IA/BYOK e coerência das telas legadas com responsáveis; não necessárias aos cálculos locais (D04/D05).
- [ ] Decidir escopo de persistência de painéis (D06), sem incluir nova funcionalidade nesta entrega.
- [ ] Revisar versão integrada, instalação em outro ambiente e incorporar evidências aos materiais coletivos (D07/D12).

Problema/evidência/impacto/módulo/sugestão detalhados em [dependencias_equipe.md](dependencias_equipe.md). Nenhuma alteração nesses módulos foi feita.

## c) Ação humana ou externa

- [ ] Confirmar autoria/divisão e aceite técnico pela equipe; não inferidos dos arquivos.
- [ ] Demonstrar ao parceiro e registrar retorno real, capacitação, avaliação e aceite/pendências.
- [ ] Confirmar rubrica, calendário, apresentação e submissão acadêmica pelos responsáveis.
- [ ] Se desejado, remover o duplicado do download criado automaticamente pelo navegador em Downloads; acesso de movimentação negado pelo sandbox. Cópia verificada entregue em evidências.

Não há dependência externa bloqueando os testes e a demonstração local concluídos. Nenhuma homologação externa foi declarada.

---

# Checklist anterior preservado

# Checklist auditado — Parte 4 do OneWorld

Data da auditoria: **27/10/2026**. A auditoria inicial foi de leitura, sem alteração de código ou banco. **Atualização da Etapa 2, na mesma data:** testes executados, dois defeitos de identidade SQLite corrigidos no frontend de BI e evidências anexadas em [validação técnica](validacao_tecnica.md). Banco e módulos compartilhados preservados.

Base aplicada: contexto mestre (Prompt 0), auditoria (Prompt 1) e critérios do [planejamento v2](../oneworld_planejamento_execucao_v2.md). O OneWorld é BI genérico local; a Casa Grande Eventos é parceira de validação, não domínio obrigatório. Não foi localizado um arquivo separado chamado prompt-base nesta cópia.

## Como interpretar os estados

- `[x]`: o item descrito tem evidência identificada; seu alcance é apenas o escrito no item.
- `[ ]`: pendente, não comprovado nesta cópia ou dependente de confirmação. Ausência de registro local não prova que uma atividade nunca ocorreu.
- **Implementação**: código existe e foi inspecionado; não comprova execução bem-sucedida.
- **Teste técnico**: código de teste, resultado de execução e inspeção visual são evidências diferentes. Na auditoria inicial houve apenas leitura; na Etapa 2 foram executados testes, compilação e demonstração de indicadores como módulo (E10), sem novo servidor ou inspeção visual no navegador.
- **Validação pelo parceiro**: exige demonstração/uso real e registro de feedback ou aceite identificável. Testes automatizados e capturas locais não substituem isso.
- **Envio acadêmico**: exige artefato final e comprovante de submissão pelo canal da disciplina. Documentação técnica local não comprova envio.
- **Material preparado**: texto, roteiro ou instrumento disponível para revisão; não equivale à atividade descrita nele ter sido realizada.
- **Informação pendente**: dado pessoal, evidência ou orientação ainda necessária; preencher sem presumir resposta ou conclusão.
- **Validação da equipe**: exige revisão/decisão coletiva registrada, separada da preparação documental e do envio.

**Datas:** 04/11/2026, 18/11/2026 e 25/11/2026 são as **datas previstas nos documentos, sujeitas a confirmação da disciplina**. O Quadro 1 dos documentos de Entrega 2 traz dia/mês; o planejamento v2 explicita 2026. Os textos de introdução citam execução até 18/11, embora o quadro inclua 25/11: confirmar o calendário completo com a disciplina.

## Evidências e fontes consultadas

| ID | Fonte | Alcance e limite |
| --- | --- | --- |
| E1 | [Planejamento v2](../oneworld_planejamento_execucao_v2.md), especialmente seções 8–12 | Escopo, prompts e marcos; planejamento não é implementação concluída. |
| E2 | [Registro de implementação](../parte4_implementacao.md), incluindo retomada de 27/10 | Relata evolução de 32 para 49 e depois 52 testes aprovados, compilação, health check anterior e inspeção visual. Não há log bruto de execução anexado aos arquivos auditados. |
| E3 | [Registro da entrega da Parte 4](../entrega_parte4.md) | Síntese técnica e pendências acadêmicas em 27/10; não é recibo de envio nem aceite externo. |
| E4 | [Indicadores genéricos](../indicadores_genericos.md) e [guia do dashboard](../guia_dashboard.md) | Contratos, resultados esperados e roteiro reproduzível; o guia é da Parte 4, não manual coletivo completo. |
| E5 | [Testes de BI](../../tests/test_bi.py), [KPIs](../../tests/test_indicadores.py), [interface](../../tests/test_frontend_bi.py) e [SQLite](../../tests/test_fontes_sqlite.py) | Contagem estática nesta auditoria: 25 + 16 + 8 + 3 = **52 métodos de teste**, com subtestes adicionais. Não equivale a nova execução aprovada. |
| E6 | [Fonte SQLite](../evidencias/fonte_sqlite.png) e [gráfico SQLite](../evidencias/grafico_sqlite.png) | Imagens abertas nesta auditoria: seleção de `Banco local: eventos`, 3 de 3 registros e barras por `data` textual. Não mostram todos os fluxos, a troca de fonte em movimento ou a participação do parceiro. |
| E7 | [Exemplos](../../exemplos/demonstrar_indicadores.py), [vendas](../../exemplos/vendas.csv), [educação](../../exemplos/educacao.csv), [estoque](../../exemplos/estoque.csv) | Dados e script para demonstrar independência de domínio. Resultados esperados registrados em E4 e assertivas em E5. |
| E8 | `C:/Users/felip/Downloads/entrega_2_oneworld.docx` e `C:/Users/felip/Downloads/entrega_2_grupo_oneworld_topicos_de_big_data_atualizada.docx`, Quadro 1 e seções 3.2 e 6 | Conteúdo textual lido diretamente dos DOCX, sem edição. A versão atualizada identifica Casa Grande Eventos e contato Kleber; papéis individuais não estão distribuídos nominalmente. Calendário não confirmado no ambiente da disciplina. |
| E9 | `C:/Users/felip/Downloads/Item 1 trabalho big data.docx` | Motivação, intuitividade, dashboards universais e proposta open source. Contém campos ainda não preenchidos sobre parceiro/termo; confirmar versão vigente com o grupo. |
| E10 | [Validação técnica da Etapa 2](validacao_tecnica.md), [log integral final](logs/testes_finais.txt), [manifesto de fontes](logs/manifesto_fontes.json) e [ambiente/integridade](logs/ambiente_integridade.json) | 52 testes iniciais e 55 finais aprovados; compilação e demonstração como módulo aprovadas. Regressões de BLOB/atualização REAL corrigidas; exportação reaberta por pandas e fluxo sem chave de IA verificados por AppTest. Não comprova clique de download, inspeção visual completa ou aceite externo. |
| E11 | [Inspeção visual da Etapa 3](evidencias/README.md), [log de 56 testes](evidencias/testes_etapa3.txt) e [roteiro do parceiro](roteiro_validacao_parceiro.md) | Nove critérios demonstrados em cópia isolada, capturas e download real de CSV comparado com a tabela filtrada. Corrigidas ordem visual do histograma e marcação residual após limpeza. Banco original preservado por hashes. Validação externa pendente; roteiro não aplicado. |
| E12 | [Contribuição técnica da Etapa 4](contribuicao_entrega4.md) | Consolidação documental das evidências, fluxo, tecnologias, resultados, limites, relação com preparação/análise de dados, roteiro curto e lista de anexos. Não comprova autoria individual, revisão coletiva ou submissão; não houve nova execução de testes nesta etapa. |
| E13 | [Manual da Parte 4](manual_dashboard.md), [roteiro de capacitação](roteiro_capacitacao.md), [avaliação de reação em branco](avaliacao_reacao.md) e [registro para o relatório da equipe](relatorio_equipe.md) | Materiais preparados na Etapa 5 a partir do guia e da interface; exercícios com gabaritos dos exemplos e dependências de disponibilização registradas. Não comprova disponibilização, capacitação, avaliação aplicada, revisão coletiva ou submissão. |
| E14 | [Encerramento da Parte 4](encerramento_parte4.md), [relato individual base](relato_individual_base.md) e [dependências consolidadas](dependencias_equipe.md) | Materiais da Etapa 6: síntese, fatos técnicos, resultados existentes, limites, roteiro final, hipóteses de contribuição e campos pessoais sem depoimentos inventados. Não houve nova execução da suíte, validação externa, revisão coletiva ou submissão nesta etapa. |

Não foram consultados canais da equipe, ambiente acadêmico ou mensagens do parceiro. Não foram encontrados nesta cópia recibos de submissão, ata de homologação da Parte 4, avaliação de reação preenchida ou relatório final coletivo/individual.

## Diagnóstico por arquivo e integração

| Arquivo(s) | Estado confirmado por leitura | Decisão para a entrega |
| --- | --- | --- |
| [indicadores.py](../../oneworld/indicadores.py), [formatacao.py](../../oneworld/formatacao.py) | Seis operações genéricas; resultado estruturado; título e apresentação separados do cálculo; sem acesso a Streamlit, SQLite ou IA nas funções de cálculo. | Reutilizar. Não criar novos KPIs específicos de eventos. |
| [metadados.py](../../oneworld/metadados.py) | Valida DataFrame e colunas textuais únicas; identifica categorias, números e datas; conversão temporal explícita; sinaliza incompatíveis. | Reutilizar contrato e confirmar tipagem com os módulos de entrada. |
| [filtros.py](../../oneworld/filtros.py) | Categoria, número e data; AND, limites inclusivos, nulos opcionais e cópia da entrada. | Reutilizar; não reimplementar filtros no frontend. |
| [analises.py](../../oneworld/analises.py) | Prepara barras, linhas por dia/mês e histograma; valida tipos, agregações e vazios. | Reutilizar; renderização continua na interface. |
| [frontend_bi.py](../../oneworld/frontend_bi.py) | Exemplos, upload e SQLite; até seis KPIs, um gráfico; limpeza de filtros, tabela e CSV; estado por conteúdo da fonte. | Implementado para demonstração técnica; configurações e uploads ficam na sessão. |
| [frontend.py](../../oneworld/frontend.py), [app.py](../../app.py), [tema.py](../../oneworld/tema.py) | Dashboard genérico conectado à navegação e tema existentes. Outras telas continuam ligadas ao protótipo de eventos. | Preservar nesta etapa; revisão global depende da equipe. |
| [fontes_sqlite.py](../../oneworld/fontes_sqlite.py) | Lista e lê tabelas existentes com conexão `mode=ro`, valida nome no catálogo e escapa identificador. | Pendência de leitura SQLite resolvida; não confundir com gravação genérica. |
| [backend.py](../../oneworld/backend.py) | `ler_arquivo` reaproveitável para CSV/XLSX/JSON. Validação/mapeamento de importação e respostas simuladas continuam específicos de eventos/convidados. | Não declarar backend inteiro genérico; adequação é dependência dos responsáveis. |
| [database.py](../../oneworld/database.py), [config.py](../../oneworld/config.py) | Esquema/CRUD fixos, campos extras e configurações do protótipo. Sem catálogo/escrita de datasets genéricos nem salvamento de dashboards de BI. | Alinhar contrato com backend/banco; não migrar nesta auditoria. |
| [requirements.txt](../../requirements.txt) | Streamlit, pandas e openpyxl; versões não totalmente fixadas. | Resultado registrado de um ambiente não demonstra compatibilidade com todas as versões permitidas. |

Contrato já utilizável: fonte → `pandas.DataFrame` com colunas textuais únicas → metadados/conversão explícita de datas → `aplicar_filtros` → o mesmo DataFrame filtrado para `calcular_kpi`, `preparar_grafico`, tabela e exportação. KPI retorna `ResultadoKPI(titulo, valor, erro, mensagem)`; gráficos retornam `grupo/valor` ou `intervalo/frequencia`. Configurações incompatíveis geram `ErroBI` ou erro estruturado do KPI. Não é necessário propor uma interface substituta.

**Precisões da auditoria:** a leitura de `fontes_sqlite.py` é somente de leitura, mas a aplicação completa chama `database.init_db()` na inicialização e possui operações de escrita nas telas legadas. Não afirmar que todo o aplicativo é somente de leitura. O BI não precisa de IA para seus cálculos; isso não comprova instalação offline em uma máquina nova.

**Registros históricos:** a pendência de consumo do SQLite no texto de 22/10 foi resolvida pelo código e pela retomada de 27/10. As contagens 32/49 são etapas anteriores, não suítes adicionais a somar. O registro antigo afirma ausência de Git; hoje há `.git`, porém a branch `main` não tem commits e os arquivos aparecem como não rastreados. Não há histórico Git suficiente para comprovar autoria ou cronologia individual.

## Minha Parte 4

### Implementação disponível — preservar

- [x] **P4-01 — KPIs genéricos:** contagem, distintos, soma, média, mínimo e máximo configuráveis por coluna, com título livre. Evidência: `indicadores.py`, E4 e E5.
- [x] **P4-02 — Apresentação explícita:** número, percentual e moeda sem inferir significado financeiro. Percentual só formata fração. Evidência: `formatacao.py`, `_mostrar_kpis` e testes de apresentação em E5.
- [x] **P4-03 — Filtros:** categorias, intervalos numéricos e temporais, combinação AND e limpeza. Evidência: `filtros.py`, `_configurar_filtros` e E5.
- [x] **P4-04 — Gráficos:** barras, linhas temporais por dia/mês e histogramas com escolhas compatíveis. Evidência: `analises.py`, `_mostrar_grafico` e E5.
- [x] **P4-05 — Integração Streamlit:** fonte selecionável; KPIs, gráfico, tabela e CSV alimentados pelo mesmo resultado filtrado. Evidência: `mostrar_dashboard` e testes de interface em E5. O clique/download real do CSV no navegador não foi comprovado nesta auditoria.
- [x] **P4-06 — Fontes:** três CSV de exemplo, upload CSV/XLSX/JSON e leitura de tabelas SQLite existentes. Evidência: `_selecionar_dados`, `backend.ler_arquivo`, `fontes_sqlite.py`, E5–E7. XLSX usa a primeira aba na interface.
- [x] **P4-07 — Troca de fonte/conteúdo:** identidade de controles vinculada ao conteúdo e reinício das configurações; atualização da tabela em novo rerun. Evidência: `_chave`, `_selecionar_dados` e teste SQLite em E5. Correção visual relatada em E2. E10 corrige e testa BLOB não UTF-8 e atualização REAL pequena que a identidade JSON anterior não distinguia.
- [x] **P4-08 — Tratamento analítico:** valida colunas/tipos, preserva entrada, trata nulos, infinitos, vazios, precisão inteira e erros de configuração cobertos. Contagens vazias = 0; agregações numéricas sem valores, inclusive soma, = indisponível. Evidência: módulos puros e E5. Não é garantia para qualquer entrada arbitrária.
- [x] **P4-09 — Separação e generalidade:** funções analíticas sem colunas de negócio obrigatórias e sem IA; exemplos de vendas, educação e estoque usam a mesma implementação. Evidência: módulos puros, E5 e E7.

### Testes técnicos e material existente

- [x] **P4-10 — Suíte disponível e executada:** 55 métodos em quatro arquivos (25 BI + 16 indicadores + 9 frontend + 5 SQLite), todos aprovados na Etapa 2 (E10). Os 52 anteriores passaram antes das alterações; três métodos adicionais cobrem defeitos e riscos reais.
- [x] **P4-11 — Resultado anterior documentado:** E2/E3 registram 52 testes aprovados em 27/10; E2 também registra compilação e health check anterior. Concluído apenas o item de existência do registro; nenhum desses comandos foi reexecutado nesta etapa.
- [x] **P4-12 — Evidência visual local:** duas capturas SQLite existentes e conferidas (E6). Elas mostram fonte e barras, sem comprovar homologação completa.
- [x] **P4-13 — Roteiro e contratos documentados:** E2–E4 e E7 permitem preparar a demonstração, com vendas soma 450/média 112,5, educação média 8 (turma A = 7) e estoque soma 47.
- [x] **P4-14 — Anexar saída integral de uma execução identificável da suíte:** concluído em E10: comando, ambiente, data, 55 testes aprovados, avisos sem supressão, log integral e hashes das fontes. Compilação e demonstração dos indicadores também executadas e registradas; tentativa incorreta de invocação direta preservada no relatório.
- [x] **P4-15 — Completar evidências da demonstração técnica:** E11 registra inspeção visual isolada dos três domínios, gráficos, troca de fontes, filtros, limpeza e SQLite sintético. Clique real no botão baixou CSV de turma A, reaberto por pandas e comparado integralmente com a tabela esperada. Não houve abertura manual em Excel nem validação externa; P4-18 continua pendente.
- [ ] **P4-16 — Identificar contribuição individual com a equipe:** confirmar arquivos/tarefas de sua autoria e vínculos com o relatório. Critério: divisão de responsabilidades validada e registro verificável; autoria não pode ser inferida pela presença dos arquivos.
- [ ] **P4-17 — Validar contrato com backend/banco:** registrar concordância sobre fonte, tipos, nulos, datas e atualização; critério: decisão da equipe documentada. O contrato técnico já existe, o aceite conjunto não está comprovado.
- [ ] **P4-18 — Demonstrar ao parceiro e registrar retorno real:** data, participante, dataset, tarefas, resultados, dificuldades e aceite/pendências. Critério: feedback identificável anexado; contato informado em E8 não comprova realização.

Não são novas funcionalidades obrigatórias da Parte 4: fórmulas arbitrárias, previsão, chatbot analítico, múltiplos gráficos simultâneos ou regras de um segmento. Uploads e painéis sem persistência, cardinalidade/volume elevados e ausência de seleção de abas são limites a declarar, não motivo para refazer o motor de BI.

## Dependências da equipe

**Referência consolidada na Etapa 6:** [dependencias_equipe.md](dependencias_equipe.md) reúne EQ-01–EQ-11, P4-16–P4-18 e os encaminhamentos coletivos das Entregas 4–6, com papéis e critérios de encerramento. Os IDs abaixo permanecem para rastreabilidade; nenhuma pendência foi encerrada apenas por ser consolidada.

Os responsáveis abaixo são **papéis sugeridos pelo conteúdo dos módulos e pelo planejamento**, não uma atribuição nominal confirmada.

- [ ] **EQ-01 — Backend + banco:** definir e integrar catálogo de domínios/datasets e escrita genérica, se mantidos no MVP coletivo. Evidência exigida: contrato e fluxo integrado demonstrado. CRUD legado e leitura SQLite já existentes não encerram essa pendência.
- [ ] **EQ-02 — Backend/importação:** decidir suporte a aba XLSX, separador/encoding, números textuais, dados aninhados e fusos mistos; documentar o que fica fora do MVP. Evidência exigida: escopo acordado e testes dos formatos assumidos. Leitura básica já está pronta.
- [ ] **EQ-03 — IA/BYOK:** confirmar implementação ou adiamento da sugestão de mapeamento com revisão humana para domínio configurado. Evidência exigida: decisão de escopo ou fluxo real testado. `sugerir()` é heurística local e `responder_ia()` é simulação específica; não comprovam IA externa/BYOK.
- [ ] **EQ-04 — Frontend + integração:** revisar a coerência das telas legadas de eventos com o produto genérico. Evidência exigida: roteiro coletivo e limites das telas documentados; não alterar módulos alheios sem alinhamento.
- [ ] **EQ-05 — Banco + frontend:** decidir se salvar/reabrir uploads e configurações de análise entra no prazo. Evidência exigida: decisão explícita de escopo ou persistência implementada/testada. As configurações gerais do aplicativo não equivalem a dashboards persistidos.
- [ ] **EQ-06 — Qualidade + integração:** validar o fluxo coletivo na versão final, além da Parte 4; conferir instalação em outra máquina e funcionamento básico sem IA. Evidência exigida: ambiente e roteiro executado, resultados e falhas registradas.
- [ ] **EQ-07 — Gestão:** confirmar versão oficial do escopo, nomes dos responsáveis, repositório compartilhado e versão de entrega; esclarecer disponibilidade de outros módulos fora desta cópia. Evidência exigida: divisão e versão acordadas. Ausência local não prova inexistência do trabalho dos colegas.
- [ ] **EQ-08 — Gestão + parceiro:** confirmar contato atual, disponibilidade, usuário responsável pela capacitação e dataset adequado à demonstração. E8 cita Kleber/Casa Grande Eventos; ainda faltam agenda, dados e feedback da Parte 4.
- [ ] **EQ-09 — Gestão + documentação:** obter versão vigente da proposta/ata da Entrega 3, termo e requisitos aceitos; conferir os campos incompletos de E9. Evidência exigida: documentos finais identificados, sem presumir assinatura ou homologação.
- [ ] **EQ-10 — Gestão + disciplina:** confirmar datas, modelos, rubrica, canal de envio e quem fará cada submissão. Evidência exigida: orientação vigente registrada; o cronograma documental é previsão.
- [ ] **EQ-11 — Equipe + documentação:** confirmar publicação e licença da proposta open source. Evidência exigida: repositório e licença definidos; nenhum arquivo de licença foi localizado na cópia auditada. Não bloqueia a demonstração técnica local.

## Entrega 4 — prevista para 04/11/2026

**Data prevista nos documentos, sujeita a confirmação da disciplina.** E8, Quadro 1: desenvolvimento/sprint, interfaces, dashboard, gráficos e análises; KDD ou aprendizado de máquina quando pertinente. Não tratar aprendizado de máquina como obrigação de implementar uma previsão no motor de BI.

### Material preparado — Etapa 4

- [x] **E4-M01 — Contribuição técnica redigida:** E12 reúne problema, implementação, fluxo, tecnologias, demonstrações, resultados e limitações, com fontes rastreáveis.
- [x] **E4-M02 — Preparação e análise de dados contextualizadas:** E12 relaciona seleção, tipos, nulos, conversão, filtros, agregações e interpretação, sem alegar ML nem processo KDD completo.
- [x] **E4-M03 — Roteiro curto e lista de anexos preparados:** seções 9 e 10 de E12; inventário de material existente separado dos registros ainda pendentes.

### Revisado pela equipe

- [ ] **E4-R01 — Autoria individual confirmada:** cumprir P4-16; a redação técnica não atribui autoria sem comprovação.
- [ ] **E4-R02 — Integração e contribuição revisadas:** confirmar P4-17, versão final, incorporação do texto e anexos ao relatório coletivo e ensaio do roteiro.
- [ ] **E4-R03 — Requisitos de submissão conferidos:** equipe confirma rubrica, datas, formato, validação externa exigida e responsável pelo envio.

### Enviado à disciplina

- [ ] **E4-S01 — Entrega coletiva submetida:** ação ainda não realizada nesta etapa.
- [ ] **E4-S02 — Comprovante arquivado:** recibo/protocolo associado ao arquivo e versão enviados.

### Marcos coletivos — mantidos com seus critérios de conclusão

- [x] **E4-01 — Base técnica da Parte 4 disponível:** implementação, suíte, exemplos, guia e duas capturas existem (P4-01–P4-13).
- [ ] **E4-02 — Fechar evidências individuais:** executar/documentar P4-14–P4-17 com a versão que será apresentada. Conclusão: pacote de evidências rastreável, sem afirmar nova implementação do que já existe.
- [ ] **E4-03 — Consolidar relatório do sprint:** inserir contribuição da Parte 4, arquitetura, funcionalidades, testes, resultados, capturas e limitações no documento coletivo. Conclusão: versão final revisada pela equipe; E3 é insumo, não relatório acadêmico final.
- [ ] **E4-04 — Documentar KDD/análise conforme aplicável:** relacionar seleção dos dados, tratamento, análise e visualização realmente feitos; confirmar critério da disciplina. Conclusão: seção coerente com a execução, sem inventar uso de aprendizado de máquina.
- [ ] **E4-05 — Demonstrar MVP integrado à equipe:** confirmar dependências incluídas/adiadas e defeitos remanescentes. Conclusão: roteiro coletivo executado com registro e responsáveis pelas pendências.
- [ ] **E4-06 — Registrar validação externa da Parte 4:** cumprir P4-18 e confirmar com gestão/disciplina em qual marco o registro deve ser anexado. Conclusão: feedback real identificado; a validação planejada da proposta na Entrega 3 não substitui teste desta implementação.
- [ ] **E4-07 — Revisar e enviar:** confirmar data/modelo/canal, consolidar anexos e realizar submissão. Conclusão: arquivo final e recibo/protocolo de envio; nenhum comprovante localizado.

## Entrega 5 — prevista para 18/11/2026

**Data prevista nos documentos, sujeita a confirmação da disciplina.** E8, Quadro 1: disponibilização do sistema, manual, capacitação do usuário responsável e avaliação de reação.

- [x] **E5-01 — Guia da Parte 4 pronto como insumo do manual:** E4 contém abertura, seleção de fonte, KPIs, filtros, gráficos e limites. Não equivale ao manual coletivo concluído.
- [x] **E5-M01 — Manual da Parte 4 preparado:** E13 explica escolha dos dados, tipos/datas, filtros, KPIs, gráficos, exportação, leitura do banco, erros e limites de persistência em linguagem simples. Revisão e incorporação coletiva continuam em E5-03.
- [x] **E5-M02 — Roteiro de capacitação preparado:** E13 inclui preparação, sequência sugerida, exercícios com resultados conhecidos e ficha de execução em branco. Roteiro não aplicado nesta etapa; E5-04 permanece pendente.
- [x] **E5-M03 — Avaliação de reação preparada:** E13 cobre facilidade, compreensão, utilidade, dificuldades e sugestões, com escala e opção N/A. Instrumento não aplicado nesta etapa; E5-05 permanece pendente.
- [x] **E5-M04 — Dependências registradas para o relatório da equipe:** E13 encaminha ambiente/disponibilização, manual coletivo, banco, persistência e ações externas aos papéis a confirmar; não implementa instaladores, hospedagem ou mudanças em módulos compartilhados.
- [ ] **E5-02 — Disponibilizar versão local ao responsável:** equipe confirma instalação, dependências, inicialização e dados no ambiente de uso. Conclusão: registro da disponibilização e teste de abertura nesse ambiente.
- [ ] **E5-03 — Integrar e revisar manual coletivo:** incorporar o guia, instalação e demais módulos efetivamente entregues. Conclusão: manual versionado e acessível ao usuário responsável.
- [ ] **E5-04 — Realizar capacitação:** parceiro/equipe definem participante e agenda; demonstrar tarefas da Parte 4 com dados adequados. Conclusão: data, conteúdo e participação registrados conforme exigência da disciplina.
- [ ] **E5-05 — Aplicar avaliação de reação:** instrumento da Parte 4 preparado em E13; equipe revisa, aplica e coleta respostas reais. Conclusão: instrumento, respostas e síntese anexados, sem inventar satisfação ou depoimentos.
- [ ] **E5-06 — Tratar retorno:** classificar dificuldades/defeitos, registrar correções e retestes necessários ou adiamentos acordados. Conclusão: lista com decisão e evidências dos itens encerrados.
- [ ] **E5-07 — Enviar Entrega 5:** consolidar implantação, manual, capacitação e avaliação; confirmar formato/data. Conclusão: artefatos finais e comprovante acadêmico de submissão.

## Entrega 6 — prevista para 25/11/2026

**Data prevista nos documentos, sujeita a confirmação da disciplina.** E8, Quadro 1: apresentação do problema, diagnóstico, solução, tecnologias, resultados, contribuição sociocomunitária, ODS/ESG, demonstração e relatório completo com relatos coletivo e individual.

### Material preparado — Etapa 6

- [x] **E6-M01 — Encerramento técnico preparado:** E14 reúne síntese, contribuições dos componentes, resultados com fontes, limitações e possibilidades futuras; autoria individual não presumida.
- [x] **E6-M02 — Roteiro final preparado:** E14 contém sequência, valores esperados, preparação em ambiente isolado e contingência por capturas identificadas. Ensaio e apresentação continuam pendentes em E6-02/E6-07.
- [x] **E6-M03 — Base factual do relato preparada:** E14 separa fatos técnicos de campos pessoais e termina com perguntas para o integrante. Não equivale ao relato concluído.
- [x] **E6-M04 — Contribuições possíveis contextualizadas:** autonomia e comunidade tratadas como objetivos/hipóteses, com proposta de avaliação; sem impacto, satisfação, economia de tempo ou vínculo ODS/ESG presumidos.
- [x] **E6-M05 — Dependências de outros integrantes consolidadas:** D01–D17 em E14 abrangem autoria, integração, validação, disponibilização, documentação e submissão, sem alterar seus arquivos.

### Informação pendente

- [ ] **E6-I01 — Vivências pessoais preenchidas:** integrante responde às perguntas do relato, identifica tarefas, período, dificuldades, aprendizados e participação real, inclusive ausência de participação quando aplicável.
- [ ] **E6-I02 — Registros externos identificados:** obter feedback, capacitação, avaliação e eventuais benefícios observados, ou declarar ausência de medição. Não preencher com suposições (D08/D13/D14/D16).
- [ ] **E6-I03 — Regras e versão final identificadas:** confirmar calendário, rubrica/modelo, versão e responsáveis por apresentação/envio (D01/D10).

### Validação da equipe

- [ ] **E6-R01 — Autoria e relato conferidos:** confirmar P4-16/D01; integrante revisa e aprova seu próprio texto.
- [ ] **E6-R02 — Solução integrada e roteiro ensaiados:** cumprir contrato, revisão do fluxo e ensaio registrado na versão escolhida (D02/D05/D07/D15).
- [ ] **E6-R03 — Relatório e apresentação revisados:** incorporar textos e anexos; separar resultados técnicos de benefícios; justificar ODS/ESG apenas se houver base e exigência pertinente (D12/D16).

### Envio acadêmico e apresentação

- [ ] **E6-S01 — Apresentação realizada e registrada:** conforme calendário/rubrica confirmados; roteiro preparado não comprova realização (D10/D17).
- [ ] **E6-S02 — Pacote final submetido:** responsável envia relatório, relatos e anexos exigidos na versão revisada (D17).
- [ ] **E6-S03 — Comprovante arquivado:** recibo/protocolo associado à data e versão efetivamente enviadas (D17).

### Marcos de conclusão — pendentes além da preparação local

- [ ] **E6-01 — Preparar apresentação coletiva:** equipe reúne os tópicos exigidos, contextualizando o BI genérico e o papel do parceiro. Conclusão: apresentação revisada e roteiro dividido entre integrantes.
- [ ] **E6-02 — Preparar demonstração final da Parte 4:** reutilizar funcionalidades e exemplos existentes; escolher versão e plano local de execução. Conclusão: ensaio registrado com resultados esperados e limites claros.
- [ ] **E6-03 — Consolidar resultados reais:** separar números de teste/demonstração do impacto observado pelo parceiro. Conclusão: afirmações de benefício/usabilidade ligadas a registros; não inventar ganho de tempo ou aceitação.
- [ ] **E6-04 — Revisar contribuição sociocomunitária, ODS e ESG:** equipe justifica relação com ações e evidências efetivas. Conclusão: seção aprovada no relatório, sem impactos presumidos.
- [ ] **E6-05 — Escrever relato individual:** integrante registra suas tarefas, decisões, dificuldades e aprendizados reais. Conclusão: relato revisto por você e coerente com P4-16; experiências pessoais ainda dependem de informação sua.
- [ ] **E6-06 — Concluir relato coletivo e relatório final:** equipe integra entregas anteriores, validação, implantação, capacitação, avaliação, evidências e limitações. Conclusão: documento completo revisado e versão identificada.
- [ ] **E6-07 — Apresentar e submeter:** confirmar calendário/rubrica, realizar apresentação e enviar arquivos exigidos. Conclusão: registro de apresentação e comprovante da submissão final. Nenhum dos dois está comprovado nesta cópia.

## Ordem de fechamento sem retrabalho

1. Confirmar com equipe/disciplina escopo, responsáveis, calendário e documentos vigentes.
2. Reutilizar motor e guia existentes; completar registros técnicos e evidências da demonstração em etapa posterior.
3. Demonstrar ao parceiro e coletar feedback verificável na agenda acordada.
4. Consolidar e enviar cada entrega, guardando os comprovantes separadamente dos testes e do aceite externo.

Na auditoria inicial não houve execução. Na Etapa 2 houve testes, compilação e demonstração automatizada dos indicadores, com resultados em E10. Não houve nova inspeção ao vivo no navegador, contato externo ou submissão acadêmica. As alterações do BI partiram de falhas reproduzidas; os demais marcos permanecem com seus critérios originais.

**Atualização da Etapa 6 — 27/10/2026:** E14 foi preparado a partir das fontes e evidências existentes; links locais dos três novos documentos e deste checklist foram conferidos. Não houve alteração de código, banco, módulos de outros integrantes ou logs anteriores, nem nova execução da suíte, ensaio, capacitação, contato com parceiro ou envio acadêmico. A Etapa 3 permanece a última execução integral anexada: 56 testes aprovados. Os marcos E6-01–E6-07 continuam abertos até seus critérios próprios serem cumpridos.


</details>
