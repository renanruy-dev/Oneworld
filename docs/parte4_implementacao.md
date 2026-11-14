# Parte 4 — mecanismo genérico de BI

Registro de execução: 22/10/2026.

O Dashboard permite selecionar arquivos locais, configurar filtros, até seis KPIs
e um gráfico. Tabela, exportação, indicadores e gráfico recebem o mesmo DataFrame
filtrado. O BI não consulta IA nem depende de chaves ou serviços externos.

## Auditoria inicial

- `app.py` inicializa Streamlit e chama `frontend.main()`.
- `frontend.py` continha o dashboard com indicadores, filtros e gráficos fixos
  para o domínio do protótipo anterior.
- `backend.py` oferece leitura de CSV/XLSX/JSON e funções específicas do protótipo.
  A leitura foi reaproveitada; os cálculos específicos não são usados no novo BI.
- `database.py` possui tabelas fixas e funções CRUD, sem um catálogo genérico de
  datasets. Não houve modificação nesse módulo nem migração de banco.
- Não havia suíte de testes nem módulos de BI independentes.
- Os arquivos abertos no IDE sob `docs/antigos/` e os demais documentos citados no
  contexto não estavam presentes nesta cópia. O planejamento v2 foi inspecionado.
- Esta pasta não possui repositório Git inicializado; não foi possível produzir
  um diff Git ou commit.

## Etapas e arquivos

| Etapa | Arquivos criados/modificados | Decisão e validação |
| --- | --- | --- |
| Tipos e contratos | `oneworld/metadados.py` | Identifica números, categorias, datas e tipos incompatíveis a partir dos dtypes/valores. Conversão de datas exige escolha explícita. Testes de tipos, falhas de conversão, duplicidade de nomes e preservação da origem. |
| KPIs | `oneworld/indicadores.py` | Contagem, distintos, soma, média, mínimo e máximo, com resultado estruturado. Testes de operações, dados vazios, nulos, tipos incompatíveis, infinitos e inteiros grandes. |
| Filtros | `oneworld/filtros.py` | Categorias e intervalos numéricos/temporais com AND e cópia da entrada. Testes de intervalos inclusivos, fim do dia, fuso, nulos, seleção vazia, limites inválidos e índices duplicados. |
| Gráficos | `oneworld/analises.py` | Prepara barras, linhas por dia/mês e histogramas sem renderização. Testes de agregações, ordenação temporal, extremos do histograma, constantes, vazios e precisão numérica. |
| Interface | `oneworld/frontend_bi.py`; modificado `oneworld/frontend.py` | Dashboard genérico isolado; navegação e tema existentes preservados. Upload reutiliza a leitura do backend. Testes AppTest de troca de datasets, KPIs, filtros, datas, gráficos e erros de leitura. |
| Demonstração | `exemplos/vendas.csv`, `exemplos/educacao.csv`, `exemplos/estoque.csv` | Nomes de domínio aparecem apenas nas amostras e testes. O mesmo fluxo analítico é executado nos três conjuntos. |
| Verificação | `tests/test_bi.py`, `tests/test_frontend_bi.py` | Usa `unittest` da biblioteca padrão e AppTest já incluído no Streamlit; nenhuma dependência adicionada. |
| Documentação | `docs/parte4_implementacao.md` | Este registro de decisões, resultados e pendências. |

## Contratos de integração

As funções puras não importam Streamlit, SQLite nem módulos de IA:

```python
meta = inspecionar_colunas(df)
filtrado = aplicar_filtros(df, configuracoes_de_filtros)
resultado = calcular_kpi(filtrado, {
    "operacao": "soma", "coluna": coluna_escolhida, "titulo": titulo
})
tabela = preparar_grafico(filtrado, {
    "tipo": "barras", "grupo": categoria_escolhida,
    "operacao": "soma", "coluna": coluna_escolhida
})
```

- A entrada deve ser `pandas.DataFrame`, com nomes de colunas textuais únicos.
- `inspecionar_colunas()` retorna um dicionário de objetos `Coluna`, contendo nome,
  tipo e quantidade de nulos. Booleanos são categorias, não medidas.
- Strings numéricas continuam texto. Não há conversão numérica automática.
- Datas textuais continuam categorias até escolha explícita de colunas e formato.
  Conversões inválidas viram nulos na cópia de análise, com aviso de quantidade;
  o arquivo original não é alterado.
- `aplicar_filtros()` recebe uma lista de dicionários com `coluna`, `tipo`,
  `valores` (categoria) ou `minimo`/`maximo` (número/data) e `incluir_nulos`.
  Intervalos são inclusivos; datas abrangem dias locais inteiros. Filtros usam
  AND. Uma seleção categórica vazia não seleciona valores; a lista de filtros
  vazia retorna uma cópia integral. Nulos são excluídos salvo escolha explícita.
- `calcular_kpi()` retorna `ResultadoKPI(titulo, valor, erro, mensagem)`.
  Distintos ignora nulos. Contagens vazias são zero; todas as agregações numéricas
  sem valores válidos, inclusive soma, retornam `None`, exibido como `—`.
  Nulos e infinitos são ignorados. Soma/média em texto retorna erro, sem coerção.
- `preparar_grafico()` retorna `grupo`/`valor` para barras e linhas, ou
  `intervalo`/`frequencia` para histograma. Grupos nulos são omitidos;
  agregações ignoram medidas nulas/não finitas. Contagem conta linhas por grupo.
  Linhas ordenam datas e não inventam períodos ausentes. Barras exigem categoria,
  linhas exigem datetime e histogramas exigem medida numérica.
- Configurações incompatíveis de filtros/gráficos levantam `ErroBI`, mostrado
  como mensagem pela interface. KPI representa esse erro em seu resultado.
- Moeda e percentual são escolhas de apresentação. Percentual formata uma
  fração (0,25 → 25%); nenhuma taxa ou regra financeira é criada.

Detalhes da evolução da camada de KPIs, apresentação reutilizável, novos testes
e demonstração: [Indicadores genéricos](indicadores_genericos.md).

## Como demonstrar

```powershell
python -m streamlit run app.py
```

1. Abra Dashboard e escolha `Exemplo: vendas`.
2. Configure o KPI como soma de `valor`: resultado **450**. Média: **112,5**.
   Distintos de `produto`: **3**.
3. Configure barras agrupadas por `categoria`, com soma de `valor`.
4. Ative um filtro categórico ou numérico e observe KPI, gráfico e tabela juntos.
5. Em Tipos de colunas e datas, selecione `data`, formato `%Y-%m-%d`.
   Escolha linhas e agregação por dia ou mês.
6. Troque para `Exemplo: educacao`: média de `nota` = **8** e distintos de
   `turma` = **2**. Esse conjunto não exige coluna de data.
7. Troque para `Exemplo: estoque`: soma de `quantidade` = **47**.
   Escolha histograma para analisar sua distribuição.
8. Adicione um CSV, XLSX ou JSON e selecione o novo conjunto. A troca de conteúdo
   reinicia configurações da análise para evitar colunas ou filtros antigos.
9. Use Limpar filtros e Exportar dados filtrados conforme necessário.

## Verificações executadas

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
python -m compileall -q oneworld app.py
```

- Suíte final: **32 testes aprovados** no ambiente `.venv` do projeto,
  com Python 3.14.7, pandas 3.0.6 e Streamlit 1.66.0.
- Antes do último teste de regressão, os outros **31 testes** também passaram
  no Python 3.14.7 global, pandas 3.0.5 e Streamlit 1.64.0.
- Os testes AppTest executam `app.py` com banco SQLite temporário e simulações
  de interação/rerun. Cobrem troca dos três datasets, configuração de múltiplos
  KPIs, filtros e limpeza, dados filtrados compartilhados, ausência de datas,
  linhas, histogramas, limites invertidos e leitura de CSV/JSON/XLSX válidos
  ou inválidos, além de filtro exato de inteiros grandes (com entrada textual
  para evitar o limite de precisão dos widgets numéricos do navegador).
  O upload é injetado porque AppTest não oferece controle de envio
  de arquivo; a leitura e o restante da interface são reais.
- A suíte emite avisos de `missing ScriptRunContext` no thread principal de
  AppTest, sem falhas de testes ou exceções não tratadas nos fluxos verificados.
- Compilação dos módulos verificada sem erros.
- Servidor iniciado por subprocesso em `127.0.0.1:18651`, em modo headless;
  `/_stcore/health` respondeu **HTTP 200, `ok`**. Processo encerrado após a
  verificação. A execução das telas é coberta separadamente pelo AppTest.
- Não foi realizada inspeção visual manual em navegador.

## Limitações e pendências

- Os dados enviados e as configurações da análise ficam na sessão Streamlit.
  Não há gravação de datasets ou dashboards genéricos no SQLite. O catálogo de
  domínios e a persistência devem ser integrados quando seus contratos existirem.
- O BI ainda não consome as tabelas legadas do SQLite como datasets genéricos.
  A fonte atual é upload ou arquivo de exemplo, conforme contingência do plano.
- Os menus e módulos legados específicos de domínio permanecem fora do novo
  dashboard. A tela de IA simulada preexistente ainda tem análises específicas
  do protótipo; sua adequação ao contrato BYOK de somente sugerir mapeamentos
  continua pendente para o responsável pela integração. Nenhuma integração de
  IA/BYOK foi alterada nesta etapa.
- O leitor reaproveitado mantém suas regras de CSV/JSON e lê a primeira aba
  do XLSX. Seleção de abas, separador/encoding manual, tipagem numérica textual,
  objetos aninhados e fusos mistos precisam de trabalho no módulo de entrada.
- Colunas aninhadas/complexas são sinalizadas como incompatíveis. Valores
  numéricos não finitos são tratados como ausentes nas operações numéricas.
- Um gráfico por vez, até seis KPIs; sem fórmulas arbitrárias, painéis persistidos,
  preenchimento temporal ou limitação de cardinalidade/volume. Arquivos e
  categorias muito grandes podem exigir paginação e controles adicionais.
- Testes validam os ambientes registrados, não toda combinação de versões
  permitida pelo `requirements.txt` existente.

## Retomada em 27 de outubro de 2026

As seções anteriores registram a execução de 22/10. A etapa de indicadores
genéricos é a última alteração identificável pelos registros locais, mas eles
não permitem afirmar qual processo foi interrompido pelo usuário.

- A suíte anterior foi executada novamente: 49 testes passaram.
- Criado `oneworld/fontes_sqlite.py`, que lista e lê tabelas do banco existente
  com conexão somente para leitura. Não cria banco ausente nem migra esquemas.
- O Dashboard oferece Incluir tabelas do banco local. A origem SQLite recebe
  os mesmos filtros, indicadores, gráficos e exportação que os arquivos.
- Uma mudança no conteúdo da tabela reinicia as configurações da análise.
- A inspeção no navegador identificou seletores com nomes de colunas antigas
  após trocar de dataset. Os controles agora têm identidade vinculada ao
  conteúdo da fonte para reconstruir os campos corretamente.
- A suíte atual tem 52 testes aprovados, incluindo integração SQLite com média,
  filtro, atualização do banco, retorno a exemplos, nomes de tabela especiais,
  tentativa de SQL em identificador e preservação dos bytes do banco lido.
- Os testes de banco usam arquivos temporários. Avisos de ScriptRunContext e
  overflow no caso de teste de extremos permanecem, sem falhas da suíte.
- Criado `docs/guia_dashboard.md`, com roteiro de uso e resultados esperados.
- Compilação de `oneworld`, `exemplos`, `tests` e `app.py` concluída sem erros.
- Aplicativo reiniciado e inspecionado no navegador: seleção de SQLite,
  contagem de registros, agrupamento com as colunas da fonte atual e barras
  correspondentes aos registros. Evidências: `evidencias/fonte_sqlite.png` e
  `evidencias/grafico_sqlite.png`. A conferência visual não equivale a teste
  com o parceiro nem a homologação de todos os fluxos da equipe.

A pendência de leitura das tabelas legadas foi resolvida. Permanecem com a
integração da equipe o catálogo/escrita de datasets genéricos e a IA/BYOK.
Arquivos enviados e configurações dos dashboards continuam apenas na sessão.
Os documentos acadêmicos originais em Downloads não foram modificados.
