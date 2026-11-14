# Leia primeiro — estado final da Parte 4

Atualização em **14/11/2026**. Consulte o [status da entrega](status_entrega.md) para a verificação atual e as pendências. A conferência histórica abaixo foi realizada em 27/10/2026.

**A Parte 4 está pronta para sua revisão e demonstração local, no ambiente existente e nos cenários documentados.** Não foi identificada pendência técnica local corrigível dentro do escopo autorizado. O projeto coletivo e as entregas acadêmicas continuam pendentes das decisões e atividades abaixo; não há comprovação local de aceite do parceiro, capacitação ou submissão.

A evidência funcional continua sendo a rodada de **60 testes aprovados** de 27/10/2026, com inspeção visual e download real. Nesta conferência, os hashes dos 19 arquivos de fonte do manifesto e dos 61 artefatos permaneceram iguais; os 20 arquivos de código/apoio da demonstração também correspondem ao projeto. Gabaritos, controles, links e versões do ambiente foram conferidos. Sem alteração técnica, não foi repetida a suíte nem iniciada uma nova sessão do aplicativo. Consulte o [registro desta conferência](logs/conferencia_final.json) e a [validação técnica](validacao_tecnica.md).

## Como abrir e demonstrar

O aplicativo completo pode escrever ao inicializar. Gere uma **nova cópia temporária** com os CSVs do projeto e tabelas SQLite sintéticas. O comando abaixo não abre o banco real nem executa o gerador de evidências. Não exige instalar dependências.

No PowerShell:

```powershell
$raizBI = 'C:\Users\felip\Documents\Projetos\One World'
$pythonBI = Join-Path $raizBI '.venv\Scripts\python.exe'
$sessaoDemoBI = & $pythonBI -B (Join-Path $raizBI 'exemplos\preparar_demonstracao.py')
Push-Location -LiteralPath $sessaoDemoBI
try {
    & $pythonBI -B -m streamlit run app.py --server.address 127.0.0.1 --server.port 18657 --server.headless true --browser.gatherUsageStats false
}
finally {
    Pop-Location
}
```

Abra [o sistema local](http://127.0.0.1:18657) enquanto o comando estiver em execução e escolha **Dashboard**. Se a porta estiver ocupada, use outra porta livre no comando e no endereço. Ao terminar, pressione **Ctrl+C**; a cópia permanece na pasta temporária indicada por `$sessaoDemoBI`.

Siga o [roteiro de apresentação de cinco minutos](roteiro_apresentacao.md): vendas, Soma de `valor` = **450**; conversão de `data` com `%Y-%m-%d`, linhas diárias = **100/200/100/50**; educação, Média de `nota` = **8**, turma A = **7** com duas linhas, exportar e limpar; estoque, Soma de `quantidade` = **47** e histograma com frequência total **3**. A opção **Banco local: demo_estoque** consulta somente o banco sintético da cópia, com soma **47**.

Os três exemplos e o cálculo de BI funcionam sem chave de IA. Se o aplicativo não abrir, use as [capturas com TXT complementares](evidencias/validacao_20261027/README.md), o [CSV conferido](evidencias/validacao_20261027/educacao_download_real.csv) e o [log dos testes](evidencias/validacao_20261027/testes_finais.txt), identificando-os como evidência anterior, sem declarar demonstração ao vivo. Instalação em outra máquina continua sendo dependência da equipe.

Não execute `preparar_demo.py` apenas para abrir a demonstração: embora crie uma pasta nova, o script também sobrescreve `demonstracao.json` e CSV na pasta histórica. Uma eventual nova validação deve ter saída separada e registros próprios; isso não é uma pendência desta conferência.

## Materiais preparados

| Material | Uso |
| --- | --- |
| [Checklist final](checklist.md) | A: verificado; B: dependências da equipe; C: ações humanas/externas. |
| [Contribuição para a Entrega 4](contribuicao_entrega4.md) | Texto técnico para revisão e incorporação pela equipe. |
| [Apresentação](roteiro_apresentacao.md) | Sequência, gabaritos e contingência da demonstração. |
| [Manual do dashboard](manual_dashboard.md) | Operação dos controles reais e limites. |
| [Capacitação](roteiro_capacitacao.md) | Exercícios e registro em branco. |
| [Validação com o parceiro](roteiro_validacao_parceiro.md) | Tarefas, resultados observados e aceite a preencher. |
| [Avaliação de reação](avaliacao_reacao.md) | Questionário ainda não aplicado. |
| [Encerramento técnico](encerramento_parte4.md) | Resultados comprovados e limitações para o relatório final. |
| [Relato individual base](relato_individual_base.md) | Fatos técnicos e campos pessoais ainda não preenchidos. |
| [Registro para o relatório da equipe](relatorio_equipe.md) | Insumos da Entrega 5 e disponibilização pendente. |
| [Dependências D01–D17](dependencias_equipe.md) | Encaminhamentos e evidência necessária para encerramento. |
| [Validação técnica](validacao_tecnica.md) e [índice das evidências](evidencias/validacao_20261027/README.md) | Testes, capturas, CSV e manifestos, com seus limites. |

## Somente as ações humanas ainda necessárias

1. **Sua revisão:** ler os materiais e conferir se refletem sua participação; preencher identificação, experiências, dificuldades e aprendizados no relato, sem presumir autoria dos módulos reutilizados (D01).
2. **Aprovação da equipe:** confirmar divisão de tarefas, versão oficial, escopo e integração; incorporar os insumos aos documentos acadêmicos oficiais; confirmar rubrica, calendário, licença/publicação se mantida essa proposta e responsáveis pelo envio (D01–D07/D09–D12).
3. **Demonstração ao parceiro:** confirmar agenda, participante e dados autorizados; executar as tarefas e registrar resultados, dificuldades, retorno e aceite ou pendências reais (D08–D09).
4. **Capacitação e avaliação:** disponibilizar o manual revisado, realizar os exercícios, coletar respostas voluntárias e tratar os problemas observados, com reteste quando necessário (D13–D14/D16).
5. **Apresentação e envio acadêmico:** ensaiar com a equipe, revisar as afirmações de resultados/benefícios, obter aprovação final e enviar pelos responsáveis definidos, guardando comprovantes (D10/D12/D15–D17).

As datas **04/11, 18/11 e 25/11/2026** são previsões dos documentos para as Entregas 4, 5 e 6, sujeitas à confirmação da disciplina. Formulários em branco e textos preparados não comprovam essas atividades.

## Dependências da equipe e impactos

| Dependência | Impacto restante |
| --- | --- |
| Autoria, versão e aprovação coletiva — D01/D12 | Impedem finalizar atribuição individual e relatório coletivo aprovado; não impedem revisar/demonstrar o artefato local. |
| Contrato de dados, importação, catálogo/escrita genéricos — D02–D03 | Impedem prometer integração e entradas além do suporte atual. XLSX lê só a primeira aba; números textuais/estruturas incompatíveis exigem tratamento na origem. |
| IA/BYOK e telas legadas — D04–D05 | Impedem declarar IA externa e coerência integral das telas como concluídas; exemplos e cálculos do dashboard independem de IA. A inicialização legada exige demonstração em cópia isolada. |
| Persistência — D06 | Impede prometer salvar/reabrir dashboards ou uploads; configurações ficam na sessão e reiniciam na troca de fonte/conteúdo. Há um gráfico por vez. |
| Ambiente integrado e disponibilização — D07 | Impede declarar abertura em outra máquina ou implantação pronta. Volume, acessibilidade e matriz ampla de versões não foram validados. |
| Documentos do parceiro, calendário e licença — D09–D11 | Impedem encerrar comprovação documental, formato/prazos e publicação open source. |
| Uso real, capacitação, avaliação, apresentação e submissão — D08/D13–D17 | Impedem homologação externa, afirmações de benefícios medidos e conclusão acadêmica do projeto. Dependem de pessoas e registros reais. |

Essas dependências não bloqueiam a revisão nem a demonstração técnica local com exemplos sintéticos. Nenhum commit, envio, publicação ou contato foi realizado nesta conferência.
