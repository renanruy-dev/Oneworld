# Roteiro de apresentação — Parte 4

Preparado em **27/10/2026**. Duração sugerida: **5 minutos**. Roteiro disponível para ensaio; apresentação e ensaio coletivo não comprovados. Atribuição individual deve ser confirmada com a equipe (D01).

Prazos previstos no [planejamento](../oneworld_planejamento_execucao_v2.md): Entrega 4 em **04/11/2026**, Entrega 5 em **18/11/2026** e Entrega 6 em **25/11/2026**, todos sujeitos à confirmação da disciplina.

## Preparação local

**Orientação final do Prompt 3 (27/10/2026):** seguir o comando completo de [leia_primeiro.md — como abrir e demonstrar](leia_primeiro.md#como-abrir-e-demonstrar). Ele usa o interpretador existente da `.venv` e cria uma nova cópia temporária de `evidencias/validacao_20261027/demo__m55hy_i/`, com exemplos e SQLite sintético. Assim, o app completo inicializa somente o banco da cópia de trabalho, preservando o banco real e o ambiente histórico das evidências.

Abrir `http://127.0.0.1:18657`, entrar em **Dashboard** e encerrar com Ctrl+C ao terminar. Se a porta estiver ocupada, escolher outra porta livre no comando e no endereço. Se o ambiente não abrir, usar a contingência; instalação em outra máquina depende de D07. Novas interações não são as evidências de 27/10: registrar separadamente qualquer resultado futuro.

Não reexecutar `preparar_demo.py` apenas para abrir o sistema: o script cria uma nova pasta, mas também sobrescreve resultados em `demonstracao.json` e CSV da pasta histórica. A cópia pronta foi conferida contra as fontes atuais e é suficiente ao roteiro. Nesta conferência final não foi iniciado novo servidor.

## Fala e demonstração

| Tempo | Fala/ação | Resultado esperado e conferência |
| --- | --- | --- |
| 0:00–0:35 | “A Parte 4 permite explorar tabelas de diferentes áreas: escolher dados, recortar registros e configurar indicadores e gráficos.” Explicar fonte → tipos/datas → filtros → cálculo → tela e CSV. | Delimitar BI descritivo; utilidade e facilidade de uso ainda precisam de avaliação pelo parceiro. |
| 0:35–1:20 | Escolher **Exemplo: vendas**. Em **Configurar KPI 1**, selecionar Soma, coluna `valor`, apresentação Número. No gráfico, barras por `produto`, Soma de `valor`. | 4 registros; soma **450**; barras Borracha 50, Caneta 200, Livro 200. |
| 1:20–2:00 | Abrir **Tipos de colunas e datas**, interpretar `data` com `%Y-%m-%d`. Selecionar linhas, agrupar por `data`, Soma de `valor`, período dia. | 01 a 04/10/2026, valores **100/200/100/50**. Conferir em **Dados do gráfico**. |
| 2:00–3:10 | Trocar para **Exemplo: educacao**; configurar Média de `nota` (**8**). Em filtros, ativar `turma` e selecionar A. Exportar CSV, conferir e limpar filtros. | Turma A: **2 linhas e média 7**; CSV com Ana/A/8 e Bruno/A/6. Limpar restaura **3 linhas e média 8**, filtros desmarcados. |
| 3:10–3:45 | Trocar para **Exemplo: estoque**. Configurar Soma de `quantidade` e histograma dessa coluna, 1 intervalo. | Configurações anteriores reiniciadas; **3 linhas, soma 47**, frequência 3. A altura do histograma conta observações. |
| 3:45–4:15 | Se o banco sintético estiver acessível, marcar **Incluir tabelas do banco local**, escolher **Banco local: demo_estoque** e Soma de `quantidade`. | **47**, com Caderno/12, Lapis/30, Cabo/5. Consulta do BI somente de leitura; esse valor não é gabarito do banco real. Etapa opcional: registrar indisponibilidade se ocorrer. |
| 4:15–5:00 | Mostrar o [log de 60 testes](evidencias/validacao_20261027/testes_finais.txt) e o [CSV já verificado](evidencias/validacao_20261027/educacao_download_real.csv). Explicar limites e próximos passos. | Identificar como resultados técnicos anteriores de 27/10/2026. Painel em sessão, um gráfico, primeira aba XLSX; validação externa e capacitação pendentes. IA externa/BYOK não comprovada; cálculos do BI independem dela. |

## Alternativa se algum módulo da equipe estiver indisponível

1. Se banco, importação legada ou IA estiverem indisponíveis, usar **Exemplo: vendas**, **Exemplo: educacao** e **Exemplo: estoque** no Dashboard. Esses exemplos não exigem cadastro de eventos, importação para SQLite ou chave de IA. Os arquivos são [vendas.csv](../../exemplos/vendas.csv), [educacao.csv](../../exemplos/educacao.csv) e [estoque.csv](../../exemplos/estoque.csv).
2. Se os exemplos não aparecerem, mas o upload funcionar, adicionar esses CSV e selecioná-los em **Conjunto de dados**. Repetir os mesmos passos e gabaritos. Se o leitor de arquivos compartilhado falhar, não prometer que o upload contornará a falha: seguir para o registro documental.
3. Se navegação, ambiente ou Dashboard não abrirem, mostrar as [capturas e TXT existentes](evidencias/validacao_20261027/README.md): vendas 450/linhas, educação 8/7/limpeza e estoque 47/histograma. Abrir o CSV da turma A e o log. Dizer: “Estes são registros da verificação técnica de 27/10/2026; a demonstração ao vivo está indisponível.”
4. Registrar módulo, sintoma e etapa não demonstrada; encaminhar a dependência pelos IDs D02–D07/D15 de [dependencias_equipe.md](dependencias_equipe.md). Não declarar a etapa aprovada por ter mostrado uma imagem.

O [manual](manual_dashboard.md) apoia a operação. O [roteiro do parceiro](roteiro_validacao_parceiro.md) é a atividade posterior de validação externa; esta apresentação não preenche seus campos.
