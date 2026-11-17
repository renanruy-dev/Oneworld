# Evidências — nova verificação de 27/10/2026

Esta pasta pertence à nova execução da auditoria técnica. Os registros das rodadas anteriores foram preservados fora dela. Versão final: **60 testes aprovados**; ambiente e resultados em [demonstracao.json](demonstracao.json). Os hashes identificam os arquivos desta rodada; não representam autoria ou homologação externa.

## Capturas reais no navegador

Aplicação completa executada em `demo__m55hy_i`, uma nova cópia isolada com dados sintéticos; banco real não foi copiado. Servidor local `127.0.0.1:18657`, sem telemetria habilitada pelo comando. As imagens são do viewport estreito efetivo do navegador integrado; não são montagens. O Streamlit usa rolagem interna: `fullPage` captura o recorte corrente, e os TXT complementares descrevem os controles que ficaram fora dele.

| Arquivo | Estado final observado |
| --- | --- |
| [01_educacao_8.png](01_educacao_8.png) | Educação, média de nota 8. |
| [02_educacao_turma_A.png](02_educacao_turma_A.png), [TXT](02_educacao_turma_A.txt) | Turma A selecionada, duas linhas, média 7. |
| [03_limpeza.png](03_limpeza.png), [TXT](03_limpeza.txt) | Filtros desativados, três linhas e média 8 restauradas. |
| [04_vendas_450.png](04_vendas_450.png), [TXT](04_vendas_450.txt) | Troca para vendas, soma de valor 450. |
| [05_formato_invalido.png](05_formato_invalido.png), [TXT](05_formato_invalido.txt) | `%Q` produz mensagem amigável, sem traceback na página. Corrigir para `%Y-%m-%d` recuperou quatro linhas. |
| [06_vendas_linhas.png](06_vendas_linhas.png), [TXT](06_vendas_linhas.txt) | Linhas diárias com soma 100/200/100/50, tabela agregada e registros. |
| [07_estoque_47.png](07_estoque_47.png), [TXT](07_estoque_47.txt) | Troca para estoque, soma de quantidade 47. |
| [08_estoque_histograma.png](08_estoque_histograma.png), [TXT](08_estoque_histograma.txt) | Frequência total 3; intervalos em ordem numérica. Rótulos extensos truncados no eixo estreito; tabela permite ler os intervalos. |
| [09_sqlite_47.png](09_sqlite_47.png), [TXT](09_sqlite_47.txt) | Banco sintético demo_estoque, soma 47 e três registros. |
| [10_sqlite_barras.png](10_sqlite_barras.png), [TXT](10_sqlite_barras.txt) | Barras Cabo 5, Caderno 12, Lapis 30 e tabela de origem. |

Após interações houve estados transitórios de rerun, observados e aguardados antes da conferência final. Um `check()` de checkbox não mudou o estado; foi substituído por clique na etiqueta e verificação do valor. Não foi classificado como defeito do produto. Na recuperação de erro de data, controles posteriores voltaram aos padrões da sessão; não se promete persistência dessas configurações.

## Exportação e banco

O clique real em Exportar dados filtrados baixou um CSV, copiado para [educacao_download_real.csv](educacao_download_real.csv); [comparação pandas](download_verificado.txt) confirmou as mesmas colunas, ordem, células e duas linhas do recorte esperado. O navegador usa Downloads automaticamente e deixou um duplicado novo em `C:/Users/felip/Downloads/analise_filtrada (1).csv`; a movimentação foi negada pelo sandbox. Nenhum arquivo anterior foi editado; limpeza opcional pelo usuário, conforme checklist.

O banco sintético foi criado pelo script com demo_vendas/demo_educacao/demo_estoque. A inicialização do app completo acrescentou suas tabelas legadas somente nessa cópia. Entre seleção/consultas do BI, os hashes [antes](sqlite_visual_antes.json) e [depois](sqlite_visual_depois.json) são idênticos. A recusa efetiva de escrita pela conexão mode=ro consta nos testes SQLite. Não se afirma que toda a aplicação é somente leitura.

## Reprodução e testes

Da raiz do projeto:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
.venv/Scripts/python.exe -B -m unittest discover -s tests -v
.venv/Scripts/python.exe -B docs/parte4_entrega/evidencias/validacao_20261027/preparar_demo.py
```

[preparar_demo.py](preparar_demo.py) cria uma nova pasta isolada por execução e executa assertivas dos três domínios, CSV, filtros, gráficos e SQLite sintético. O caminho resultante fica em [demonstracao.json](demonstracao.json). Para abrir, usar o interpretador absoluto da .venv da raiz, entrar na pasta isolada informada e executar `python -B -m streamlit run app.py --server.address 127.0.0.1 --server.port 18657 --server.headless true --browser.gatherUsageStats false`. Selecionar exemplos e a tabela demo_estoque. Encerrar com Ctrl+C após o roteiro.

Logs: [56 testes iniciais](testes_antes.txt), [reprodução dos defeitos](sondagem.txt), [regressões em desenvolvimento](regressoes_antes.txt), [60 testes finais](testes_finais.txt), [compilação](compilacao.txt), [demonstração](demonstracao.txt), [sondagem JSON misto](json_misto.txt). A primeira versão do teste novo tinha duas expectativas incorretas, corrigidas; suas falhas permanecem no log de desenvolvimento, sem atribuí-las ao produto. Avisos de ScriptRunContext e de extremos numéricos permanecem nos logs. O JSON com bool/texto usa fallback de compatibilidade do Streamlit/Arrow e terminou sem exceções na tela.

[Resultado de integridade](resultado_integridade.json): apenas metadados.py, analises.py, test_bi.py e test_frontend_bi.py alterados; sem novos arquivos fora de docs/parte4_entrega; banco real idêntico. [Inventário anterior](integridade_antes.json) e [posterior](integridade_depois.json). A cópia dos módulos usada no navegador é idêntica às fontes finais. [Manifesto](manifesto.json) inclui SHA-256 dos artefatos e fontes finais. O servidor e a aba foram encerrados.

Limites: não houve validação por parceiro, instalação em outra máquina, ensaio de carga ou avaliação de acessibilidade. Esta evidência comprova os cenários técnicos descritos, sem aceite externo.
