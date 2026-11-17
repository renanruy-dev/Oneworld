# Evidências reais — inspeção visual da Etapa 3

Execução em **27/10/2026**, fuso **America/Sao_Paulo**. Teste técnico local; **validação externa pendente**. Nenhum participante, feedback ou aprovação
foi presumido e ninguém foi contatado.

## Ambiente e escopo

Aplicados o escopo e as restrições da Parte 4 do
[planejamento](../../oneworld_planejamento_execucao_v2.md), após leitura dos
[registros anteriores](../validacao_tecnica.md). As correções ficaram em
`oneworld/frontend_bi.py` e `tests/test_frontend_bi.py`; documentação e evidências
ficam na entrega. Módulos compartilhados e banco original foram preservados.

A pasta `ambiente_isolado/` contém cópia de app.py, oneworld, exemplos, logo,
requirements e configuração .streamlit, com banco criado do zero para teste.
Não houve cópia do banco original nem uso de suas tabelas reais. A inicialização
normal da aplicação criou as tabelas legadas apenas nesse banco de teste.
`teste_bi` contém Item 1/A/12, Item 2/A/30 e Item 3/B/5.

Servidor próprio em `http://127.0.0.1:18653`, acessível só em loopback,
sem serviços de IA; Python 3.14.7, Streamlit 1.66.0 e pandas 3.0.6.
Navegador integrado controlado pela interface; capturas JPEG reais, sem montagem,
com viewport estreito padrão. Cada imagem registra a região visível naquele
momento; os TXT complementam os controles/tabelas fora da região visível.
`fullPage` não expande o contêiner rolável interno do Streamlit neste navegador.

Comando usado dentro de `ambiente_isolado` (a partir de sua raiz):

```powershell
& 'C:\Users\felip\Documents\Projetos\One World\.venv\Scripts\python.exe' -m streamlit run app.py --server.address 127.0.0.1 --server.port 18653 --server.headless true --browser.gatherUsageStats false
```

O servidor foi reiniciado após as correções para carregar os módulos atualizados,
e encerrado ao concluir. A cópia é material de reprodução do teste, não outra
versão oficial do produto. Os hashes da cópia e das fontes finais constam no JSON.

## Resultados observados

| Critério | Resultado real | Capturas e registros |
| --- | --- | --- |
| Vendas: soma de valor | **450**, 4 registros | [14 final](14_vendas_final_450.jpg), [controles](14_vendas_final_450.txt); [01 com barras](01_vendas_450.jpg) |
| Educação: média de nota | **8.00**, 3 registros | [16](16_educacao_final_8.jpg), [controles](16_educacao_final_8.txt) |
| Educação: turma A | **7.00**, 2 registros | [17](17_turma_A_final_7.jpg), [controles](17_turma_A_final_7.txt), [20 após última correção](20_filtro_antes_limpeza.txt) |
| Estoque: soma de quantidade | **47**, 3 registros | [08](08_estoque_47.jpg), [controles](08_estoque_47.txt) |
| Gráficos compatíveis | Vendas: barras 50/200/200 por produto e linhas 100/200/100/50 por dia após conversão explícita. Educação: barras por turma A=7, B=10; filtrada, só A=7. Estoque: histograma de quantidade, frequências totalizando 3. | [01](01_vendas_450.jpg), [04](04_educacao_grafico_A.jpg), [15 linhas](15_vendas_linhas.jpg), [valores das linhas](15_vendas_linhas.txt), [13 histograma corrigido](13_histograma_corrigido.jpg), [eixo na acessibilidade](13_histograma_corrigido.txt) |
| Troca de fontes | Educação com A ativo → estoque: contagem reinicia em 3, filtros só produto/quantidade/categoria desmarcados, agrupamento produto e sem nota/turma. Vendas com data tipada/linhas → educação: contagem e barras reiniciadas, sem seletores temporais antigos. | [07](07_troca_sem_filtros_antigos.jpg), [controles 07](07_troca_sem_filtros_antigos.txt), [16](16_educacao_final_8.txt) |
| Limpeza | Após correção: turma desmarcada, valores removidos, 3 de 3 registros, média **8.00** e tabela com Clara novamente. | [21 caixas limpas](21_limpeza_corrigida.jpg), [22 média restaurada](22_media8_apos_limpeza.jpg), [estado completo](21_limpeza_corrigida.txt) |
| Exportação da tabela filtrada | Clique real no botão e download `analise_filtrada.csv`. Cópia preservada com exatamente Ana,A,8 e Bruno,A,6. Reabertura por pandas e igualdade de todas as células, colunas e ordem aprovadas; média 7. | [05 tabela visível](05_exportacao_tabela.jpg), [CSV baixado](educacao_turma_A_download.csv), [assertiva/resultado](resultados_verificados.json) |
| SQLite de teste | Fonte `Banco local: teste_bi`, leitura indicada, 3 registros e soma **47** de quantidade. Tabela confere com os registros sintéticos. | [10 fonte](10_sqlite_fonte.jpg), [11 soma](11_sqlite_soma47.jpg), [estado](11_sqlite_soma47.txt), [12 tabela](12_sqlite_tabela.jpg), `ambiente_isolado/oneworld.db` |

Os nomes de alunos e itens pertencem às amostras sintéticas; não são participantes
de validação. A exportação foi aberta programaticamente após o clique real;
não se declara abertura manual em Excel.

## Defeitos encontrados e correções

1. **Histograma em ordem alfabética:** a captura [09](09_estoque_histograma.jpg)
   mostra `(7.5, 10.0]` deslocado ao fim. O DataFrame já estava ordenado; a camada
   de renderização o reordenava. O frontend usa `sort=False` somente no histograma.
   A captura [13](13_histograma_corrigido.jpg) e seu TXT mostram limites crescentes.
   Novo teste confere a especificação real Vega-Lite (`x.sort=null`) e frequência 3.
2. **Limpeza com checkbox visualmente marcado:** [18](18_limpeza_final.jpg) e seu
   [TXT](18_limpeza_final.txt) mostram dados restaurados, mas turma ainda marcada.
   Agora a limpeza incrementa a revisão de identidade dos widgets de filtro,
   além de apagar o estado. O teste existente confere nova chave e valor falso.
   Após reiniciar o servidor, [21](21_limpeza_corrigida.jpg) mostra as três caixas
   desmarcadas e [22](22_media8_apos_limpeza.jpg), média 8. O TXT 19 pertence à
   tentativa anterior ao reinício; o TXT 20 pertence ao processo atualizado.
3. **Configuração do isolamento:** na primeira rodada faltava a cópia de
   `.streamlit/config.toml`, causando controles escuros junto ao tema claro do
   produto. Foi copiada a configuração original, sem alterar o tema compartilhado.
   Capturas 01–09 são dessa rodada inicial; 10 em diante usam o tema original.

Durante reruns há estados intermediários do navegador com rótulos antigos;
a verificação considera o estado concluído. Interações que coincidiram com a
reconstrução foram conferidas e repetidas. Não foram tratadas como sucesso sem
verificação do resultado visível.

## Testes e integridade

- `.venv\Scripts\python.exe -m unittest discover -s tests -v`: **56 testes
  aprovados**, incluindo regressão do eixo do histograma e identidade após limpeza.
  [Log integral final](testes_etapa3.txt), sem suprimir avisos de ScriptRunContext
  e o aviso numérico do teste de extremos.
- `.venv\Scripts\python.exe -m compileall -q oneworld tests app.py`: saída 0;
  [log](compilacao.txt) sem erros.
- [Resultados verificados](resultados_verificados.json): conteúdo e SHA-256 do
  CSV, versões do ambiente, registros SQLite e comparação da cópia com a fonte.
- [Hashes antes](integridade_antes.json) e [depois](integridade_depois.json):
  somente frontend_bi.py e test_frontend_bi.py mudaram entre os arquivos
  preexistentes inventariados. Banco original com SHA-256 idêntico.
- [Manifesto das evidências](manifesto_evidencias.json): hashes dos artefatos
  desta pasta, excluindo o próprio manifesto e caches Python.

## Limites e pendências

Conferência visual limitada ao navegador e às amostras deste registro. Não é teste
exaustivo de formatos, volume, acessibilidade ou de todas as versões admitidas
pelas dependências. As legendas extensas dos intervalos do histograma ficam pouco
legíveis na largura estreita observada; a tabela de dados do gráfico permite
consultar os valores completos. Persistência de dashboards e módulos de IA/legados
continuam fora desta etapa. Nenhuma biblioteca foi adicionada.

**Validação externa: PENDENTE DE APLICAÇÃO.** O
[roteiro](../roteiro_validacao_parceiro.md) contém tarefas, resultados esperados,
campos de dificuldades, sugestões e aceite, todos sem respostas inventadas.
