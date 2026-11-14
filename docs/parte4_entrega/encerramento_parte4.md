# Encerramento da Parte 4 — síntese para o relatório final

Atualizado em **27/10/2026** na preparação documental do Prompt 2. Texto técnico pronto como insumo para o relatório; encerramento coletivo, apresentação e submissão dependem dos registros próprios. Não houve nova execução da aplicação ou dos testes nesta preparação.

## Síntese técnica

A Parte 4 disponibiliza análise descritiva configurável em Python, pandas e Streamlit. O painel aceita exemplos, arquivos CSV/XLSX/JSON e tabelas existentes do SQLite local. O usuário escolhe colunas e operações, interpreta datas explicitamente, combina filtros categóricos, numéricos e temporais e confere os resultados em indicadores, gráfico e tabela. O recorte pode ser exportado em CSV.

O fluxo é fonte → DataFrame → tipos/datas → filtros → indicadores e agregações → visualização e exportação. Um mesmo DataFrame filtrado alimenta os quatro destinos. As operações de cálculo estão separadas da interface e da formatação; o mecanismo não exige nomes de colunas de um setor. Vendas, educação e estoque são amostras sintéticas do mesmo motor. A Casa Grande Eventos é parceira prevista de validação, sem tornar eventos o domínio obrigatório.

Há até seis KPIs com contagem, distintos, soma, média, mínimo e máximo; filtros com limites inclusivos combinados por E; barras, linhas por dia/mês e histograma com 1 a 100 intervalos. Percentual formata frações sem calcular uma taxa; moeda acrescenta símbolo sem converter valores. Contagem vazia retorna zero; agregações sem números válidos, inclusive soma, ficam indisponíveis. Nulos e infinitos são ignorados nas medidas numéricas.

As funcionalidades descrevem o artefato, sem atribuição de autoria individual. A solução reutiliza leitor de arquivos, banco, navegação, tema e demais componentes da equipe. O integrante deve confirmar sua participação no [relato individual base](relato_individual_base.md); presença de arquivos, logs e hashes não comprova autoria.

## Resultados comprovados e alcance

A referência mais recente é a [validação técnica de 27/10/2026](validacao_tecnica.md), com [evidências da rodada final](evidencias/validacao_20261027/README.md).

| Evidência existente | Resultado | Limite da conclusão |
| --- | --- | --- |
| [Suíte final](evidencias/validacao_20261027/testes_finais.txt) | **60 testes aprovados em 9,082 s**, saída 0, após 56 iniciais aprovados. | Testes de KPIs, filtros, gráficos, formatos, erros, SQLite e AppTest nos cenários cobertos. Rodadas anteriores de 52/55/56 são histórico, não testes adicionais a somar. |
| [Compilação](evidencias/validacao_20261027/compilacao.txt) e [demonstração](evidencias/validacao_20261027/demonstracao.json) | Compilação em memória OK e assertivas em três domínios aprovadas. | Não é teste de instalação, volume ou validação externa. |
| [Inspeção local](evidencias/validacao_20261027/README.md) | Vendas: soma 450 e linhas 100/200/100/50. Educação: média 8, turma A média 7/duas linhas, limpeza restaura média 8/três linhas. Estoque: soma 47 e frequência total 3. | Cópia isolada e dados sintéticos; capturas com recortes e TXT complementares. Não são benefícios medidos para o parceiro. |
| [CSV baixado](evidencias/validacao_20261027/educacao_download_real.csv), [comparação](evidencias/validacao_20261027/download_verificado.txt) | Download real comparado por pandas: Ana/A/8 e Bruno/A/6, mesmas colunas, ordem e células esperadas. | Não comprova abertura manual em Excel nem uso por parceiro. |
| [SQLite sintético](evidencias/validacao_20261027/10_sqlite_barras.txt) e [integridade](evidencias/validacao_20261027/resultado_integridade.json) | Tabela demo_estoque com soma 47; hashes iguais após consulta; banco real preservado na rodada. Testes recusam escrita pela conexão do BI. | Leitor é somente de leitura; inicialização do app completo e telas legadas podem escrever. |
| [Teste sem IA](validacao_tecnica.md) | Fluxo básico aprovado sem chaves e sem chamada à função de IA, com sentinela no teste. | Não demonstra integração externa de IA nem instalação offline nova. |

Foram documentadas correções de BLOB/identidade SQLite, atualização de valores REAL, ordem do histograma e limpeza visual. A rodada mais recente também tratou formato de data inválido e categorias mistas texto/booleano. Os respectivos testes e registros estão na validação técnica; não se atribui a implementação dessas correções ao integrante sem confirmar sua participação.

Os resultados demonstram funcionamento técnico nos cenários registrados. Não há nesta cópia comprovação de reunião com o parceiro, capacitação realizada, avaliação respondida, homologação, revisão coletiva ou envio. Instrumentos preparados continuam separados dos registros de uso efetivo. Não foram medidas satisfação, economia de tempo, impacto social ou melhoria de decisões.

## Limitações e dependências

O painel mantém uploads e configurações na sessão, sem salvar/reabrir dashboards. Trocar fonte/conteúdo reinicia escolhas; após erro que interrompe a renderização, controles posteriores podem voltar aos padrões. Há um gráfico por vez e leitura da primeira aba XLSX. Não há limpeza universal, junção automática de fontes nem preenchimento de períodos temporais ausentes. Dados incompatíveis exigem revisão na origem.

Não foram realizados ensaio de carga, avaliação de acessibilidade, matriz ampla de versões ou instalação em outra máquina. Rótulos longos do histograma podem ficar truncados em telas estreitas; a tabela permite consultar os intervalos. As dependências de bibliotecas não estão integralmente fixadas.

Backend e telas legadas mantêm regras de eventos/convidados. Leitura SQLite existente não comprova escrita ou catálogo de datasets genéricos. IA/BYOK externa permanece sem comprovação: heurísticas e respostas simuladas não equivalem a serviço integrado. A solução realiza BI descritivo, com seleção, preparação explícita, filtros e agregações; não implementa ML, previsões ou processo KDD completo.

Autoria, integração, ambiente, validação externa, capacitação, reação, revisão e submissão estão detalhados em [dependencias_equipe.md](dependencias_equipe.md), IDs D01–D17. Prazos do [planejamento](../oneworld_planejamento_execucao_v2.md): **04/11/2026**, **18/11/2026** e **25/11/2026**, respectivamente Entregas 4, 5 e 6, **datas previstas nos documentos e ainda sujeitas à confirmação da disciplina**.

## Possíveis trabalhos futuros

Priorizar, conforme decisão da equipe, a revisão do contrato entre fontes e motor, a instalação no ambiente de uso e o teste do fluxo integrado. Em seguida, aplicar os [exercícios de capacitação](roteiro_capacitacao.md), o [roteiro do parceiro](roteiro_validacao_parceiro.md) e a [avaliação de reação](avaliacao_reacao.md), registrar retorno real e retestar problemas observados.

Persistência de painéis, catálogo/escrita genérica, seleção de abas, melhoria para grandes bases, acessibilidade e legibilidade em telas estreitas são propostas futuras, sem compromisso de implementação nesta entrega. Publicação e licença da proposta open source dependem de definição da equipe. Autonomia do usuário e utilidade comunitária são objetivos a avaliar por tarefas e relatos reais; não há evidência para quantificá-los ou afirmar relação específica com ODS/ESG.

O [roteiro de apresentação](roteiro_apresentacao.md) centraliza a demonstração final e a alternativa com CSV/capturas. O [checklist](checklist.md) separa os materiais concluídos das ações externas e pessoais ainda pendentes.
