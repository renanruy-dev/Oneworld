# Conferência final — conferência final, 27/10/2026

Atualização de 14/11/2026 disponível em [status da entrega](status_entrega.md). Os registros abaixo preservam suas datas históricas.

**Parte 4 pronta para revisão e demonstração local**, com limites e dependências no [checklist final](checklist.md) e no [guia inicial](leia_primeiro.md). Nenhuma correção técnica foi necessária nesta conferência. A suíte não foi repetida: as 19 fontes e os 61 artefatos do manifesto continuam idênticos, os 20 arquivos de código/apoio da cópia visual correspondem ao projeto e as versões principais do ambiente permanecem as registradas. O log de 60 testes aprovados continua sendo evidência da rodada funcional abaixo, sem ser apresentado como nova execução.

Conferidos os controles do manual, os caminhos/comandos da demonstração, os links, os gabaritos dos exemplos e o CSV baixado. O banco real foi apenas lido como bytes para SHA-256, sem conexão SQLite ou inicialização do aplicativo. Registro detalhado e preservação antes/depois em [logs/conferencia_final.json](logs/conferencia_final.json).

**Orientação atual para abrir:** usar a nova cópia temporária descrita em [leia_primeiro.md](leia_primeiro.md#como-abrir-e-demonstrar), preservando o ambiente histórico. As instruções de reprodução abaixo pertencem à rodada anterior. `preparar_demo.py` cria uma nova pasta, mas também sobrescreve `demonstracao.json` e CSV na pasta histórica; não o reexecutar para simples demonstração. Uma nova validação deve separar saídas e identificar a nova rodada, sem substituir a evidência existente. O script e os artefatos históricos não foram alterados nesta conferência.

Não foram realizados homologação, capacitação, aprovação coletiva, envio ou publicação. Essas ações permanecem pendentes, separadas da preparação técnica local.

---

# Validação técnica atual — etapa técnica, rodada final de 27/10/2026

Esta seção registra uma **nova execução** sobre o estado real da pasta. Os registros anteriores foram preservados abaixo. A referência de 52 testes estava desatualizada: a cópia recebida já tinha 56 testes, todos aprovados novamente; a versão final tem **60 testes aprovados em 9,082 s**. Não há homologação externa, publicação, envio ou commit nesta rodada.

## Escopo e preservação

Leitura dos quatro documentos solicitados e dos módulos/testes existentes antes da implementação. Git apresenta arquivos não rastreados, sem base de diff útil; foi feito inventário SHA-256 antes de executar os testes. Não houve instalação nem mudança de dependências/configurações. Alterados somente:

- `oneworld/metadados.py`: conversão de datas com formato inválido gera `ErroBI` exibido pela interface.
- `oneworld/analises.py`: agrupamentos de categorias textuais e booleanas são ordenados por rótulo, sem comparar `str` com `bool`; datas continuam em ordem cronológica.
- `tests/test_bi.py` e `tests/test_frontend_bi.py`: quatro regressões adicionais para os defeitos e o descarte de configurações antigas entre datasets.

Nenhuma mudança nos outros sete arquivos permitidos foi necessária. Nenhum arquivo preexistente fora da lista de código foi alterado, conforme [integridade](evidencias/validacao_20261027/resultado_integridade.json). Banco real preservado, SHA-256 `383e32db1d5c4060dd7629142b579334e267eb2697da34084ba78a9a9416b679`. Relatórios/evidências novos concentrados em `docs/parte4_entrega/`; os documentos anteriores desta pasta foram preservados, com esta atualização acrescentada.

## Execuções e evidências da rodada atual

| Execução | Resultado | Evidência |
| --- | --- | --- |
| `.venv/Scripts/python.exe -B -m unittest discover -s tests -v`, antes de corrigir | 56 testes, 6,964 s, OK | [Log inicial](evidencias/validacao_20261027/testes_antes.txt) |
| Sondagem de formato `%Q` e categorias `A/True/B/False` | `ValueError` no formato e `TypeError` na comparação; AppTest confirma exceção na tela de datas | [Reprodução inicial](evidencias/validacao_20261027/sondagem.txt) |
| Testes adicionais antes da correção | Falhas/erros reproduzidos; o log também contém duas expectativas incorretas do teste novo (estoque usa produto; a identidade se repete ao retornar ao mesmo conteúdo), ajustadas sem mudar o produto | [Log de desenvolvimento](evidencias/validacao_20261027/regressoes_antes.txt) |
| Suíte final, mesmo comando | **60 testes, 9,082 s, OK**; saída Python 0 | [Log final integral](evidencias/validacao_20261027/testes_finais.txt) |
| Compilação com `compile()` em memória | oneworld/*.py, tests/*.py, app.py e preparar_demo.py, OK, sem escrever caches | [Compilação](evidencias/validacao_20261027/compilacao.txt) |
| Script reproduzível de demonstração | Três domínios, seis KPIs, filtros, CSV reaberto, barras/histogramas/linhas e SQLite sintético com assertivas aprovadas | [Script](evidencias/validacao_20261027/preparar_demo.py), [resultados](evidencias/validacao_20261027/demonstracao.json) |
| Inspeção visual da versão final | Aplicação completa em nova cópia isolada, porta local 18657; dados e banco sintéticos. Aba e servidor encerrados após inspeção | [Índice visual](evidencias/validacao_20261027/README.md) |
| Clique real em Exportar dados filtrados | CSV com Ana/A/8 e Bruno/A/6; comparação pandas idêntica ao recorte esperado | [CSV baixado](evidencias/validacao_20261027/educacao_download_real.csv), [comparação](evidencias/validacao_20261027/download_verificado.txt) |
| Leitura SQLite no navegador | Soma 47; barras Cabo 5/Caderno 12/Lapis 30; SHA-256 igual antes/depois das consultas | [Antes](evidencias/validacao_20261027/sqlite_visual_antes.json), [depois](evidencias/validacao_20261027/sqlite_visual_depois.json) |

Ambiente efetivo: Python 3.14.7, pandas 3.0.6, Streamlit 1.66.0, openpyxl 3.1.5, SQLite 3.50.4. Os logs preservam avisos de ScriptRunContext e overflow do teste intencional de extremos; não houve falha na suíte final. A sondagem JSON misto passou sem exceção na interface; Streamlit registrou conversão de compatibilidade Arrow para tipos mistos, sem alterar os grupos no resultado analítico ([log](evidencias/validacao_20261027/json_misto.txt)).

## Auditoria funcional concluída

| Área | Verificação e resultado |
| --- | --- |
| KPIs e formatos | Contagem, distintos, soma, média, mínimo, máximo; vazio, nulos/infinitos, tipos incompatíveis, nullable, precisão inteira, erro estruturado; número, percentual e moeda explícitos. Até seis KPIs exercitados. |
| Filtros | Categorias, seleção vazia, nulos, números e dias inclusivos; AND, índices duplicados, intervalos inválidos; limpeza dos dados e do estado visual confirmada. |
| Gráficos | Barras e agregações, linhas por dia/mês, histogramas com extremos/constantes/vazios; mesma seleção da tabela/indicadores/exportação; intervalos do histograma preservam ordem numérica. |
| Arquivos e exportação | CSV/JSON/XLSX válidos e inválidos por leitor real e AppTest; upload injetado nos testes por limitação do AppTest. CSV conferido programaticamente e após download real do navegador. |
| SQLite | Conexão mode=ro, escrita recusada, banco ausente não criado, identificadores especiais/injeção, BLOB não UTF-8 e pequenas atualizações REAL; atualização de conteúdo reinicia a análise. |
| Troca de datasets | Educação → vendas → estoque e SQLite/exemplos; novo teste exercita seis KPIs, título, moeda, filtro vazio, data e linhas mensais em vendas, e verifica o descarte ao trocar e ao retornar. Opções dos seletores pertencem à fonte atual, sem datas herdadas. |
| Separação e IA | Funções puras mantidas; teste existente com ambiente sem chaves e sentinela em responder_ia aprovado, sem chamada de IA. |

Demonstração dos seis KPIs (contagem/distintos/soma/média/mínimo/máximo):

| Amostra | Colunas de medida/distintos | Resultados |
| --- | --- | --- |
| Vendas | valor/produto | 4 / 3 / 450 / 112,5 / 50 / 200 |
| Educação | nota/turma | 3 / 2 / 24 / 8 / 6 / 10 |
| Estoque | quantidade/categoria | 3 / 2 / 47 / 15,666666… / 5 / 30 |

Visualmente: educação média 8; turma A média 7 e duas linhas; limpar restaura média 8/três linhas/caixas desmarcadas. Vendas soma 450; datas convertidas geram linha 100/200/100/50. Formato `%Q` mostra mensagem amigável e a correção do formato recupera a tela. Estoque soma 47/histograma de frequência total 3. SQLite sintético soma 47/barras 5/12/30. As capturas PNG são do viewport estreito real; TXT complementam os controles fora do recorte.

## Reprodução isolada

Na raiz do projeto, executar:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
.venv/Scripts/python.exe -B -m unittest discover -s tests -v
.venv/Scripts/python.exe -B docs/parte4_entrega/evidencias/validacao_20261027/preparar_demo.py
```

O script cria uma **nova** pasta `demo_*` em evidências e informa o caminho em `demonstracao.json`; nunca copia nem abre o banco real. Usa os módulos atuais e amostras existentes. Para repetir a inspeção visual, guardar o caminho absoluto de `.venv/Scripts/python.exe`, entrar na pasta isolada indicada e executar esse interpretador com `-B -m streamlit run app.py --server.address 127.0.0.1 --server.port 18657 --server.headless true --browser.gatherUsageStats false`. O aplicativo completo inicializa tabelas legadas **somente no banco sintético da cópia**. Não executar a demonstração visual sobre o banco real. Selecionar os três exemplos e Banco local: demo_estoque; seguir o guia existente.

## Limites e encaminhamentos

- Inspeção técnica local; aceite da equipe/parceiro, capacitação e envio acadêmico permanecem sem comprovação. Ver checklist atualizado.
- Sessão sem persistência/reabertura, um gráfico, primeira aba XLSX, sem ensaio de carga ou matriz ampla de versões: limites já existentes, sem ampliação de MVP nesta rodada.
- Em largura estreita, rótulos longos de histograma ficam truncados; a tabela dos intervalos funciona. Não foi feita avaliação de acessibilidade ou por usuários finais.
- Depois de um erro de configuração que interrompe a renderização, controles posteriores podem voltar aos padrões no rerun, comportamento observado ao corrigir `%Q`; não há promessa de persistência dessas configurações.
- O navegador salvou automaticamente o download em `C:/Users/felip/Downloads/analise_filtrada (1).csv`. A evidência foi copiada para a pasta autorizada; tentativa de mover esse arquivo novo recebeu acesso negado pelo sandbox. O duplicado pode ser removido pelo usuário. Nenhum arquivo anterior de Downloads foi editado. Não foi solicitada ampliação de acesso.
- Dependências de catálogo/escrita, módulos legados, IA e validação coletiva continuam com a equipe, conforme [dependências](dependencias_equipe.md). Nenhuma mudança fora do escopo foi executada para atendê-las.

---

# Registros anteriores preservados

# Validação técnica — Parte 4

Execução em **27/10/2026**, referência de data: America/Sao_Paulo. Resultado: **52 testes existentes aprovados antes das alterações; 55 aprovados ao final**, sem falhas ou testes ignorados. Compilação aprovada. Dois defeitos na identidade da fonte SQLite foram corrigidos apenas na integração de BI.

## Base, escopo e ambiente

Aplicados o contexto inicial, os contratos e as restrições dos Prompts 1 e 5–6 do [planejamento v2](../oneworld_planejamento_execucao_v2.md) e o [checklist anterior](checklist.md). Não existe um prompt-base separado nesta cópia nem uma lista adicional explícita de arquivos permitidos. O escopo foi limitado ao módulo próprio `oneworld/frontend_bi.py`, seus testes e documentação de entrega. Não foram alterados módulos compartilhados, importação, IA, esquema ou dados do banco.

- Diretório: `C:\Users\felip\Documents\Projetos\One World`.
- Windows 10, build 19045, AMD64; shell PowerShell.
- Interpretador: `.venv\Scripts\python.exe`, Python 3.14.7, MSC v.1944, 64 bits.
- pandas 3.0.6; Streamlit 1.66.0; openpyxl 3.1.5; SQLite 3.50.4.
- Dependências existentes utilizadas; nenhuma biblioteca instalada ou adicionada.
- Git presente, arquivos não rastreados e sem commit de referência. A versão testada é identificada pelos hashes em [manifesto_fontes.json](logs/manifesto_fontes.json), não por um commit presumido.
- [Ambiente e integridade](logs/ambiente_integridade.json): hashes dos arquivos compartilhados e banco conferidos antes e depois da rodada final, todos iguais. Esse intervalo de hashes não constitui um histórico anterior da pasta. Os testes de escrita e inicialização utilizam bancos temporários.

## Comandos e resultados efetivos

Comandos executados na raiz, com stdout e stderr integrais redirecionados aos logs indicados. Códigos de saída abaixo são dos processos Python.

| Comando | Resultado | Evidência |
| --- | --- | --- |
| `.\.venv\Scripts\python.exe -m unittest discover -s tests -v` antes das mudanças | exit 0; 52 testes, 5,422 s, OK | [Suíte inicial](logs/testes_iniciais.txt) |
| `.\.venv\Scripts\python.exe -m unittest discover -s tests -p test_fontes_sqlite.py -v` após adicionar regressões, antes da correção | exit 1; 5 testes, uma falha reproduzida por BLOB não UTF-8 | [Falha original](logs/regressao_sqlite_antes.txt) |
| Mesmo comando após a correção | exit 0; 5 testes, 1,723 s, OK | [Regressão corrigida](logs/regressao_sqlite_depois.txt) |
| `.\.venv\Scripts\python.exe -m unittest discover -s tests -p test_frontend_bi.py -v` | exit 0; 9 testes, 5,567 s, OK | [Integração](logs/integracao_frontend.txt) |
| `.\.venv\Scripts\python.exe -m unittest discover -s tests -v` na versão final | exit 0; 55 testes, 7,081 s, OK | [Suíte final integral](logs/testes_finais.txt) |
| `.\.venv\Scripts\python.exe -m compileall -q oneworld exemplos tests app.py` | exit 0 | [Compilação](logs/compilacao.txt) |
| `.\.venv\Scripts\python.exe exemplos/demonstrar_indicadores.py` | exit 1; `ModuleNotFoundError: oneworld` pela invocação direta | [Tentativa direta](logs/demonstracao.txt) |
| `.\.venv\Scripts\python.exe -m exemplos.demonstrar_indicadores` | exit 0; resultados conhecidos nos três domínios | [Demonstração como módulo](logs/demonstracao_modulo.txt) |

A invocação como módulo já é o comando documentado em `docs/indicadores_genericos.md`; foi usada sem editar o script nem alterar o caminho de importação do projeto. A tentativa direta acima fica registrada, sem ser apresentada como falha de cálculo. Algumas acentuações na saída da tabela foram afetadas pela codificação do terminal; as assertivas e os valores numéricos passaram.

Para reproduzir o log principal em PowerShell:

```powershell
& .\.venv\Scripts\python.exe -m unittest discover -s tests -v *> docs/parte4_entrega/logs/testes_finais.txt
$resultadoTestes = $LASTEXITCODE
Get-Content docs/parte4_entrega/logs/testes_finais.txt -Tail 6
Write-Output "EXIT_CODE=$resultadoTestes"
```

## Cobertura e resultados observados

| Verificação solicitada | Evidência executada e resultado |
| --- | --- |
| Operações dos KPIs | `test_bi.TestKPIs`, `test_indicadores.TestContratoKPI` e `TestPlanilhasDiferentes`: contagem, distintos, soma, média, mínimo e máximo, sem coerção de texto. Vendas: 4/3/450/112,5/50/200; educação: 3/2/24/8/6/10; estoque: 3/2/47/15,666…/5/30. |
| Filtros combinados e limpeza | `TestFiltros` cobre AND, inclusividade, nulos, fuso e preservação da entrada. Novo `TestDashboard.test_filtros_combinados_exportacao_e_limpeza_sem_ia` combina categoria Papelaria, valor mínimo 100 e data máxima 02/10/2026: resta Caneta/100/01-10. Limpar desativa os três filtros, devolve 4 registros e soma 450. |
| Barras, linhas e histogramas | `TestGraficos` cobre agregações, ordenação por mês, extremos, constantes, vazios e tipos inválidos; `test_datas_histograma_e_multiplos_kpis` cobre linhas por dia na interface. No novo teste combinado, barras e linhas somam 100; histograma tem frequência total 1. |
| Mesmo conjunto para os quatro destinos | Novo teste compara CSV decodificado/reaberto com a tabela exibida, e confere KPI e dados do gráfico, para cada um dos três tipos. A seleção vazia produz tabela e CSV vazios com cabeçalho, KPI de soma indisponível e nenhuma exceção. Limpeza restaura a exportação com 4 linhas. |
| Troca de datasets e colunas | `test_inicializacao_e_troca_dataset`, `test_datas_histograma_e_multiplos_kpis` e teste SQLite: troca educação/vendas/estoque e banco/exemplo, reinicialização de configurações e remoção de linhas quando não há datas. |
| SQLite sem escrita pelo BI | Testes de leitura com igualdade dos bytes e banco ausente não criado; identificadores especiais e tentativa de SQL. Novo teste da conexão efetivamente usada pelo leitor recusa INSERT com `sqlite3.OperationalError`. Novo teste do dashboard isolado confirma bytes do banco iguais após consulta/renderização, sem executar a inicialização legada. |
| Vazios, nulos e tipos incompatíveis | Suíte cobre contagem vazia 0, soma/média/mínimo/máximo indisponíveis, nulos/infinitos ignorados, booleanos como categorias, aninhados e complexos incompatíveis, colunas ausentes/duplicadas e precisão de inteiros nullable. Novo teste SQLite também aceita BLOB na tabela, classificando-o como incompatível para operações automáticas sem derrubar o painel. |
| Erros de configuração | Testes de KPI malformado retornam erro estruturado; filtros invertidos/inválidos e gráficos incompatíveis produzem `ErroBI`; interface exibe mensagem para limites invertidos; arquivos CSV/JSON/XLSX inválidos não geram exceção não tratada. |
| Sem chave de IA | O novo teste combinado executa os reruns de análise com `os.environ` vazio e substitui `backend.responder_ia` por uma função que falharia se chamada; nenhuma chamada ocorreu. Cálculos, filtros, gráficos, tabela e exportação passaram nesse contexto. Não comprova uma instalação nova offline. |

## Defeitos encontrados e correção restrita

1. **BLOB SQLite derrubava o dashboard.** A leitura retornava corretamente os dados, mas `to_json()` usado para identificar a fonte tentava decodificar bytes como UTF-8, fora do tratamento de erro. A regressão usa `b'\xff\x00'` e falhou antes da correção com `UnicodeDecodeError`; passou depois.
2. **Pequenas alterações REAL podiam ficar invisíveis.** `to_json()` com precisão padrão produzia a mesma identidade para 1,00000000001 e 1,00000000002, mantendo os dados anteriores na sessão. A reprodução comparou a serialização antiga e o hash novo ([resultado](logs/precisao_identidade.txt)). O teste real atualiza a tabela SQLite, executa rerun e exige identidade diferente e o novo valor exato na tabela.

`frontend_bi.py` agora calcula a identidade a partir do esquema (nomes e dtypes) e de `pandas.util.hash_pandas_object`, sem converter os valores para JSON. Preserva a leitura, o contrato DataFrame e as regras de reinício da análise. Nenhum tratamento do backend foi substituído.

Foram acrescentados **três métodos de teste**, apenas para os dois defeitos e os riscos de integração exigidos nesta etapa: BLOB/atualização REAL; bloqueio efetivo de escrita; consistência de exportação/filtros/limpeza/IA. A suíte existente foi preservada, sem enfraquecer assertivas. Distribuição final: 25 BI + 16 indicadores + 9 frontend + 5 SQLite = 55 métodos, além dos subtestes.

## Dependências e limitações

- **Inicialização da aplicação completa:** `frontend.main()` chama `database.init_db()` e as telas legadas têm escrita. Isso permanece com frontend/banco da equipe; não se pode declarar o aplicativo inteiro somente para leitura. A alternativa restrita ao BI foi validada por AppTest chamando `mostrar_dashboard()` diretamente sobre banco temporário existente. O leitor de BI usa `mode=ro`, inclusive quando iniciado pela aplicação completa.
- Não houve defeito reproduzido em módulo alheio que exigisse modificação nesta rodada. Catálogo/escrita de datasets, IA/BYOK, persistência dos painéis e adequação das telas legadas continuam dependências já registradas no checklist.
- AppTest executa a interface e seus reruns; não é inspeção visual no navegador. Upload é injetado porque a ferramenta não controla envio de arquivos. A exportação foi verificada nos bytes entregues ao botão real e reaberta por pandas; não houve clique de download nem abertura manual em Excel.
- Avisos `missing ScriptRunContext` do AppTest e `RuntimeWarning: overflow encountered in reduce` no teste intencional de overflow permanecem no log integral. O teste exige erro estruturado para o resultado fora do intervalo; os avisos não foram suprimidos.
- Sem servidor/health check novo nesta etapa, teste de instalação em outra máquina, ensaio de volume/cardinalidade ou matriz completa de versões. Bibliotecas não estão integralmente fixadas em `requirements.txt`.
- Validação técnica não encerra autoria individual, acordo de contrato com a equipe, demonstração completa registrada, aceite do parceiro ou submissão acadêmica. P4-15–P4-18 e os marcos coletivos permanecem pendentes no alcance indicado no checklist.

## Arquivos alterados e criados nesta etapa

- Alterado `oneworld/frontend_bi.py`: identidade SQLite sem JSON.
- Alterado `tests/test_fontes_sqlite.py`: dois testes de regressão/risco real.
- Alterado `tests/test_frontend_bi.py`: um teste de integração de filtros/exportação/IA.
- Atualizado `docs/parte4_entrega/checklist.md` conforme as evidências.
- Criado este `docs/parte4_entrega/validacao_tecnica.md`.
- Criados os logs e manifestos em `docs/parte4_entrega/logs/`, todos vinculados acima. A compilação também atualizou caches Python derivados; não são alterações de fonte.
