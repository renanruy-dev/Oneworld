# Registro da entrega da Parte 4

Data de verificação: 27/10/2026. Marco acadêmico de referência: Entrega 4,
04/11/2026, conforme o planejamento local.

## Contribuição técnica disponível

O mecanismo de BI do OneWorld permite selecionar dados de arquivos ou de tabelas
do banco SQLite local, aplicar filtros e configurar indicadores e gráficos.
As análises trabalham com as colunas escolhidas pelo usuário. O mesmo mecanismo
é demonstrável com vendas, educação e estoque, sem mudar as funções de cálculo.

Foram implementadas contagem, contagem distinta, soma, média, mínimo e máximo;
filtros de categorias, números e datas; barras, linhas temporais e histogramas.
Tabela, exportação CSV, indicadores e gráfico usam o mesmo conjunto filtrado.
As funções analíticas ficam separadas da interface Streamlit, do banco e da IA.
Tipos incompatíveis, valores nulos e ausência de registros são tratados.

Na retomada, a integração de leitura com SQLite foi concluída e o problema
visual de seletores conservarem nomes de outra fonte foi corrigido. A leitura
do dashboard não grava registros nem altera a estrutura das tabelas existentes.

## Evidências verificáveis

- Suíte completa: 52 testes aprovados em 27/10/2026.
- Demonstração dos indicadores: vendas com soma 450 e média 112,5; educação com
  média 8; estoque com soma 47.
- A mesma suíte cobre filtros e gráficos, erros, conjuntos vazios, precisão
  numérica, arquivos CSV/JSON/XLSX e interação Streamlit.
- Comandos, contratos e limitações constam em `parte4_implementacao.md` e
  `indicadores_genericos.md`. O roteiro está em `guia_dashboard.md`.
- Inspeção visual da leitura SQLite, dos controles e do gráfico após troca de
  fonte. Capturas em `evidencias/fonte_sqlite.png` e `evidencias/grafico_sqlite.png`.

## Limites da conclusão

O BI está disponível para demonstração técnica com arquivos e leitura do banco
atual. Isso não comprova homologação pelo parceiro, envio acadêmico, capacitação
ou aceitação pela equipe. Não há evidência desses eventos nesta cópia.

A persistência de novos datasets genéricos e a integração de IA/BYOK ainda
dependem dos responsáveis pelos demais módulos. Configurações de análise não
são salvas para reabertura futura. O aplicativo contém telas legadas ligadas ao
protótipo de eventos; elas não definem as regras do mecanismo genérico de BI.

## Fechamento acadêmico do integrante

1. Apresentar o roteiro da Parte 4 à equipe e validar o contrato de entrada de
   dados com os responsáveis por backend e banco antes da Entrega 4.
2. Incluir no relatório do sprint as funcionalidades, evidências de testes,
   limitações e capturas da demonstração.
3. Demonstrar ao parceiro e registrar feedback real; não apresentar a inspeção
   técnica como se fosse validação externa.
4. Para 18/11, incorporar o guia ao manual coletivo, apoiar a capacitação e
   registrar a avaliação de reação aplicada pela equipe.
5. Para 25/11, revisar o relato individual com suas experiências reais e apoiar
   apresentação e relatório final. Nenhum depoimento pessoal foi presumido.

Os nomes dos responsáveis e o envio dessas entregas precisam ser confirmados
pelo grupo. Este registro descreve a implementação disponível, não substitui
os documentos acadêmicos nem a comprovação de entrega na disciplina.
