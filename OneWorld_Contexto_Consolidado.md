# OneWorld — Contexto Consolidado, Escopo e Regras de Continuidade

**Data de consolidação:** 07/10/2026  
**Projeto:** OneWorld  
**Natureza:** documento de contexto para futuras IAs e pessoas que continuarem o projeto  
**Status:** referência consolidada; não é uma especificação de implementação concluída nem um documento acadêmico final

## 1. Autoridade e finalidade

Este arquivo reúne, em uma única referência autossuficiente, o propósito do OneWorld, as decisões confirmadas, os limites do MVP, os fluxos previstos, as condicionais e as pendências reais. Seu objetivo é evitar que futuras IAs tratem sugestões antigas, protótipos demonstrativos ou afirmações não validadas como requisitos aprovados.

### Hierarquia para resolver conflitos

1. Instruções e decisões explícitas posteriores do usuário.
2. Decisões consolidadas neste arquivo, quando não contradisserem instrução posterior do usuário.
3. Slides da apresentação revisada, como referência de segundo nível.
4. Arquivos Markdown, PDFs antigos e protótipos, somente como contexto e evidência histórica.

Quando uma fonte antiga divergir deste arquivo, a decisão mais recente e explícita do usuário prevalece. A conclusão e o futuro apresentados nos slides devem ser lidos como evolução possível, não como compromisso adicional do MVP.

### Regras gerais para futuras IAs

- Não transformar uma sugestão em requisito sem confirmação do usuário.
- Não afirmar que uma funcionalidade está implementada apenas porque aparece no protótipo, nos slides ou em um PDF.
- Distinguir sempre **confirmado**, **condicional**, **em estudo**, **pendente**, **fora do MVP** e **não verificado**.
- Não inventar metas, carga horária, distribuição de papéis, métricas, formatos exatos, telas, integrações ou resultados.
- Preservar os documentos existentes; este arquivo é uma consolidação nova.
- Em documentos do projeto e documentos acadêmicos, não mencionar **Power BI**, inclusive como comparação ou concorrente.

## 2. Identidade do projeto

O OneWorld é uma proposta de Business Intelligence (BI) geral, open source e local, construída em Python para democratizar BI e Decision Intelligence (DI), especialmente para empreendedores e pequenos negócios que precisam organizar dados e obter visões analíticas sem depender de soluções complexas.

O foco é permitir que o usuário registre ou importe dados de seu próprio empreendimento, organize-os em domínios e estruturas flexíveis e visualize informações em dashboards, totais, comparações e indicadores. A DI é tratada como apoio à interpretação e à decisão, sem substituir o julgamento do usuário.

### Parceiro extensionista e exemplo de domínio

Casa Grande Eventos é o cliente/parceiro externo obrigatório para a disciplina extensionista e também um exemplo de contexto de uso. Kleber, seu proprietário, pode ser citado quando for conveniente; o nome completo não é obrigatório.

O parceiro contribui para levantamento de requisitos, validação e testes, mas não transforma suas necessidades específicas em especialização obrigatória do produto. O MVP deve permanecer genérico para empreendimentos diversos. Eventos, convidados, reservas e receita prevista são exemplos de domínio, não a definição exclusiva do sistema.

## 3. Objetivo e público

### Objetivo geral

Construir uma base local, open source e acessível de BI em Python que permita a empreendedores organizar seus dados e obter análises visuais e apoio à decisão, com controle do usuário sobre a entrada, a revisão e a gravação das informações.

### Público de referência

O público é amplo: empreendedores, pequenos negócios e usuários que precisam de BI sem depender de uma equipe especializada. Não devem ser reproduzidas como fatos do projeto características demográficas presentes em documentos antigos.

## 4. Escopo funcional confirmado do MVP

### 4.1 Domínios, tabelas e campos

- O usuário pode criar e editar domínios conforme o próprio empreendimento.
- Dentro de um domínio, o usuário pode criar e editar tabelas e campos livremente.
- A estrutura deve servir a diferentes tipos de negócio, e não apenas a eventos.
- Em um domínio já existente, a inserção manual de novos registros deve ser simples, sem exigir a edição da estrutura a cada lançamento.
- A descrição deve falar em interface e possibilidade de revisão/confirmação, sem detalhar layout de campos, cards, telas ou organização visual.

### 4.2 Registro e histórico de dados

O sistema deve permitir manter histórico suficiente para gráficos, totais, comparações e indicadores. Quando fizer sentido ao domínio, registros podem conter data, valor e período.

Pagamentos, quando modelados, são registros financeiros do domínio. Isso não significa integração com meios de pagamento, agenda, calendário externo ou serviço bancário.

No exemplo de eventos, convidados, reservas e valores são dados de negócio; receita prevista não equivale a recebimento realizado.

### 4.3 Entrada manual

A entrada manual é obrigatória no MVP. O usuário deve conseguir inserir registros em uma estrutura existente com revisão e confirmação antes da gravação.

### 4.4 Planilhas e intercâmbio

Planilhas/importação fazem parte do MVP, mesmo sem a adoção de um modelo BYOK. O sistema deve participar de um intercâmbio de dados tabulares que permita preparar, importar, validar, visualizar uma prévia, revisar e confirmar os dados antes de gravá-los.

O formato padrão exato do intercâmbio ainda está pendente. CSV, JSON, Markdown, PDF e outros formatos foram mencionados em materiais ou discussões, mas não devem ser tratados como conjunto final aprovado. Importação de PDF não é promessa do MVP.

### 4.5 Dashboard e análise

Os dados confirmados devem poder ser dispostos em dashboards com gráficos, totais, comparações e indicadores coerentes com os campos e períodos disponíveis. O documento não fixa layout, posição de cards, organização de telas ou estilo visual.

O propósito analítico é transformar dados organizados em informação compreensível e apoiar a interpretação humana. Não há compromisso do MVP com predição validada, treinamento de modelos, previsão de demanda, sazonalidade, fornecedores ou aprendizado de máquina.

### 4.6 Backup manual

O backup manual está confirmado: o usuário aciona uma ação que gera um arquivo com as informações e recebe, no sistema operacional, a indicação do caminho em que o arquivo foi salvo.

O formato do arquivo, o conteúdo exato, o destino configurável e a restauração ainda precisam ser definidos. Backup automático é evolução futura, não requisito confirmado do MVP.

## 5. Fluxos de Decision Intelligence e IA externa

Decision Intelligence é obrigatória como conceito e fluxo de apoio, mas não significa que o OneWorld precise conter um chatbot interno ou fazer chamadas automáticas a um provedor no MVP.

### Fluxo A — análise externa de dados preparados

1. O sistema prepara, copia ou exporta dados selecionados em um formato padrão.
2. O sistema fornece ou acompanha um prompt orientador.
3. O usuário leva os dados e o prompt a um chat de IA externo de sua escolha.
4. A IA externa devolve orientação, interpretação ou apoio à decisão.
5. O usuário avalia a resposta; a decisão permanece humana.

Não há exportação local automática para IA, nem envio automático de todo o SQLite. O usuário escolhe o que compartilhar.

### Fluxo B — dados devolvidos por IA externa

1. O sistema fornece um prompt para solicitar que um chat externo devolva dados em formato tabular padrão.
2. O usuário recebe a resposta e a salva ou copia para o formato de intercâmbio definido pelo projeto.
3. O usuário importa o arquivo ou conteúdo.
4. O sistema valida o formato, lê os dados e mostra uma prévia.
5. O usuário revisa e confirma.
6. Somente após a confirmação o sistema grava novos domínios, novas tabelas, novos campos ou registros em estruturas existentes, conforme o conteúdo validado.

Neste fluxo, a IA externa pode sugerir estruturas, inclusive ajudar a superar a restrição de formatos, mas não tem acesso direto ao SQLite nem autorização para gravar. Usuário e validação do sistema controlam a persistência.

### IA integrada e acesso por API — situação atual

Chatbot integrado e acesso de IA aos dados por API estão **em estudo**. Não devem ser excluídos definitivamente, mas também não devem ser prometidos como parte garantida do MVP.

Se uma integração for implementada, ela deve ser tratada como caminho opcional, com dados selecionados explicitamente pelo usuário, aviso de envio e possível custo, revisão humana e nenhuma alteração automática nos registros.

## 6. BYOK: condições, riscos e limites

BYOK significa que o usuário fornece a própria chave de API. É tecnicamente viável em uma aplicação local sem login próprio, mas depende de conta/chave válida no provedor e de internet. Os dados enviados ao provedor saem do computador; portanto, não se deve afirmar processamento 100% local quando houver chamada externa.

OpenAI, Anthropic e Gemini são candidatos, não uma garantia de suporte simultâneo a todos. Chave de equipe embutida ainda não foi decidida.

Se o BYOK for implementado, o comportamento esperado inclui:

- campo de chave mascarada e teste de conexão;
- mensagens compreensíveis para chave inválida, falta de permissão, cota, saldo, limite temporário, rede, timeout, serviço indisponível e resposta inválida;
- segredo fora de logs;
- envio apenas dos dados selecionados;
- aviso de que o uso pode gerar custo e de que os dados serão enviados ao provedor;
- tentativas limitadas somente para falhas transitórias, sem repetir indiscriminadamente erros de saldo ou cota;
- faturamento tratado pelo provedor, sem cobrança, recarga ou painel de saldo obrigatório no OneWorld.

Saldo exato, alertas antecipados e controle de gasto por tokens são opcionais e dependem da API escolhida. A persistência da chave — `.env`, SQLite, memória ou armazenamento do sistema operacional — permanece em aberto.

Não está confirmada a regra de uma chamada por dia que aparece em materiais antigos. Ela só pode ser adotada após nova decisão explícita.

## 7. Stack e infraestrutura

### Confirmado

- Python.
- Streamlit para a interface e dashboards.
- pandas para leitura, transformação e análise tabular.
- SQLite como armazenamento local obrigatório do produto.
- Windows como plataforma principal.
- Linux é desejável, mas a compatibilidade não está garantida.
- Uso local, single-instance, sem login próprio, sem nuvem e sem multiusuário no MVP.

### Não confundir protótipo com produto

O arquivo `oneworld_modelo_base.py` é um protótipo demonstrativo. Ele usa `st.session_state`, apresenta exemplos de eventos/convidados, upload/mapeamento e uma resposta de IA simulada. Não prova que o produto final já use SQLite, que a IA esteja integrada ou que os fluxos estejam completos.

## 8. Limites e fora do MVP

Os itens abaixo não são requisitos aprovados do MVP:

- login próprio, autenticação, permissões ou multiusuário;
- nuvem, APIs de ingestão, pipelines automáticos e integrações externas;
- chatbot integrado garantido;
- IA que altere registros automaticamente;
- cobrança, recarga ou administração de billing;
- backup automático;
- integração de pagamentos ou calendário;
- importação de PDF prometida;
- treinamento de ML, previsão de demanda ou predição de sazonalidade;
- Hadoop como parte da stack de implementação;
- painel detalhado de consumo/saldo de provedor;
- opções do protótipo como 2FA, idiomas, moedas, calendário, pagamentos e autobackup, enquanto não forem confirmadas;
- necessidades específicas de Casa Grande Eventos como especialização obrigatória.

Cloud, APIs, pipelines, multiusuário, permissões e IA integrada podem ser evolução futura. A conclusão/futuro dos slides é referência de direção, não escopo atual.

## 9. Decisões antigas superadas

As seguintes regras de materiais anteriores não devem ser reutilizadas sem confirmação:

- **Domínio apenas pré-configurado:** superado. O usuário poderá criar e editar domínios, tabelas e campos de forma genérica no MVP.
- **IA somente mapeia para schema preexistente:** superado para os fluxos externos. A IA externa pode sugerir estruturas; a validação do sistema e a confirmação do usuário controlam a gravação.
- **IA exclusivamente como mapeador interno de planilha livre:** não é mais a descrição completa do papel da IA. A DI externa e o fluxo de devolução de dados também fazem parte do contexto, enquanto a integração interna continua condicional.
- **Importação como extra se houver tempo:** superado. Planilhas/importação são obrigatórias no MVP; o formato padrão exato ainda está pendente.
- **Uma chamada de IA por dia:** não confirmada; não tratar como requisito.
- **Casa Grande Eventos como produto especializado:** superado. É cliente/parceiro obrigatório da disciplina e exemplo de domínio.

## 10. KDD, Big Data e aprendizado de máquina

O fluxo proposto é compatível, em termos gerais, com seleção, limpeza/validação, transformação, análise e interpretação de dados. Isso não comprova que a mineração de dados completa tenha sido realizada.

A adoção formal da metodologia KDD não está confirmada. A Entrega 4 menciona KDD ou ML quando pertinente, sem tornar ML obrigatório. Não se deve afirmar treinamento, modelo preditivo, previsão de demanda ou validação de sazonalidade.

Hadoop pode ser citado como referência teórica da disciplina, mas não é stack aprovada do OneWorld. Dados públicos, `dados.gov.br` e CVM também não têm papel funcional do MVP definido neste documento.

## 11. Projeto extensionista e governança

### Contexto acadêmico

- Disciplina: Tópicos de Big Data em Python.
- Instituição: FACI WYDEN.
- Natureza: trabalho extensionista.
- Período técnico informado: 15/09/2026 a 18/11/2026.
- Data acadêmica final confirmada: 25/11/2026.
- Metodologia de referência: PBL/aprendizagem baseada em projetos, com desenvolvimento incremental de MVP.
- Orientadora: Larissa de Paula Serrão Garcia.

### Equipe

1. Renan Ruy Secco de Oliveira
2. João Victor Palhares Ribeiro
3. Eduardo Souza Initherio
4. Felipe Carreira da Cunha Antunes
5. Rômulo Pessoa Guanais
6. Miguel Adriano Cardoso Abdon Júnior

Os seis papéis abaixo foram previstos como categorias de trabalho, mas não há atribuição individual confirmada:

- backend;
- frontend/dashboard;
- IA, se aplicável;
- dados/banco;
- QA/documentação;
- gestão/comunicação.

Não inventar divisão de pessoas, carga horária ou cronograma interno detalhado.

### Entregas e marcos

As datas são marcos/prazos e não significam que as entregas já estejam concluídas:

| Entrega | Data | Conteúdo de referência |
|---|---:|---|
| 2 | 16/09/2026 | planejamento, cronograma, metodologia, recursos, riscos, indicadores e comunicação |
| 3 | 07/10/2026 | validação, ata, revisão de proposta, escopo, requisitos e protótipos |
| 4 | 04/11/2026 | desenvolvimento, dashboard, gráficos e análises; KDD/ML quando pertinente |
| 5 | 18/11/2026 | disponibilização, manual, capacitação e avaliação de reação |
| 6 | 25/11/2026 | apresentação, relatório coletivo/individual, contribuição sociocomunitária, ODS/ESG e demonstração |

Uma reunião de 01/09 aparece nos documentos como levantamento de requisitos com Kleber. Para futuras atas, tratá-la como fato a confirmar/documentar; não reproduzir sua transcrição como verificação independente.

### Indicadores e comunicação

Os indicadores confirmados são de progresso do projeto, não metas inventadas de desempenho do produto. Exemplos já previstos nos materiais: tarefas concluídas por entrega, cumprimento de prazos, reuniões com a parte interessada, funcionalidades do MVP implementadas e pendências resolvidas.

Kleber/Casa Grande Eventos é parte interessada externa para requisitos, validação e testes. Larissa é parte interessada institucional para orientação e avaliação acadêmica. O escopo continua sob controle da equipe e das decisões do usuário.

## 12. Pendências reais

Estas decisões continuam abertas e devem permanecer marcadas como pendentes até nova confirmação:

- formato padrão exato do intercâmbio e extensão/conjunto final de arquivos;
- tratamento definitivo de CSV, JSON, Markdown e outros formatos;
- formato, conteúdo, destino e restauração do backup manual;
- persistência segura de chave BYOK;
- se e quando haverá chatbot/API de IA integrada;
- provedores efetivamente suportados, caso BYOK avance;
- eventual política de limite de chamadas;
- chave de equipe versus chave individual;
- uso funcional de dados públicos;
- necessidade de matriz formal de risco;
- divisão de papéis e cronograma interno;
- dados de demonstração;
- critérios detalhados da avaliação escrita da disciplina.

Não preencher pendências com recomendações técnicas como se fossem decisões. Recomendações podem ser registradas como recomendações, mas precisam de aprovação para virar requisito.

## 13. Fontes consultadas e tratamento da evidência

Referências consultadas para esta consolidação:

- [OneWorld_Contexto_IA.md](<C:/Users/renan/OneDrive/Documentos/Faculdade/Topico de Big Data/OneWorld/OneWorld_Contexto_IA.md>) — contexto anterior, sujeito às decisões mais recentes.
- [OneWorld_Escopo_Projeto.md](<C:/Users/renan/OneDrive/Documentos/Faculdade/Topico de Big Data/OneWorld/OneWorld_Escopo_Projeto.md>) — escopo anterior, parcialmente superado.
- [oneworld_modelo_base.py](<C:/Users/renan/OneDrive/Documentos/Faculdade/Topico de Big Data/OneWorld/oneworld_modelo_base.py>) — protótipo demonstrativo, não produto final.
- [SEPESQI — Apresentação editável revisada.pdf-1.pdf](<C:/Users/renan/OneDrive/Documentos/Faculdade/Topico de Big Data/OneWorld/SEPESQI — Apresentação editável revisada.pdf-1.pdf>) — apresentação revisada; segundo nível de autoridade.
- [content.pdf](<C:/Users/renan/OneDrive/Documentos/Faculdade/Topico de Big Data/OneWorld/content.pdf>) — dissertação de José Maria da Cunha Ribeiro Soares Pereira (2023), referência teórica.
- [entrega_1_renan_ruy_secco_oneworld_topicos_de_big_data_em_python.pdf](<C:/Users/renan/OneDrive/Documentos/Faculdade/Topico de Big Data/entrega_1_renan_ruy_secco_oneworld_topicos_de_big_data_em_python.pdf>) — entrega antiga, contextual e não necessariamente factual em todos os pontos.
- [entrega_2_grupo_oneworld_topicos_de_big_data.pdf](<C:/Users/renan/OneDrive/Documentos/Faculdade/Topico de Big Data/entrega_2_grupo_oneworld_topicos_de_big_data.pdf>) — planejamento acadêmico e marcos da disciplina.

Os PDFs de entregas antigas podem conter transcrições, caracterizações ou afirmações que não foram confirmadas nesta consolidação. Não importar automaticamente a bibliografia interna inteira desses PDFs nem tratar todos os autores ali citados como fontes lidas; esse levantamento permanece pendente.

## 14. Núcleo bibliográfico para futuros documentos

O usuário exige que os autores/obras abaixo sejam mencionados em **todos os futuros documentos do trabalho**, e não apenas quando uma bibliografia for considerada pertinente. As menções devem ter relação real com o tema do documento. Não atribuir a uma fonte uma ideia que não foi consultada ou confirmada, nem fabricar citações indiretas; quando a relação for apenas bibliográfica, registrar a referência sem inventar conteúdo derivado.

- SHARDA, Ramesh; DELEN, Dursun; TURBAN, Efraim. *Business Intelligence, Analytics, Data Science, and AI: a managerial perspective*. 5. ed. New York: Pearson, 2024.
- WHITE, Tom. *Hadoop: the definitive guide*. 4. ed. Sebastopol: O'Reilly Media, 2015.
- MCKINNEY, Wes. *Python for Data Analysis: data wrangling with pandas, NumPy, and Jupyter*. 3. ed. Sebastopol: O'Reilly Media, 2022.
- PEREIRA, José Maria da Cunha Ribeiro Soares. *Comunicação de Empresas em Redes Sociais baseada em Big Data, Data Analytics e Inteligência Artificial*. 2023. Dissertação — IADE, Universidade Europeia. Orientador: António Manuel Gorgel Couto Pinto; orientador não é coautor.
- MORAES, Julio Cezar Medina. “A contribuição do Business Intelligence na tomada de decisão em empresas internacionais”. *RCMOS*, v. 1, n. 1, 2026. DOI: `10.51473/rcmos.v1i1.2026.2624`. Data de publicação indicada nos metadados: 09/07/2026. Página do artigo: <https://submissoesrevistarcmos.com.br/rcmos/article/view/2624>.

O núcleo acima não autoriza inventar uma bibliografia completa dos documentos antigos. Para citações formais, conferir os dados bibliográficos na fonte correspondente.

## 15. Regra de segurança para Google

Qualquer mutação por Google Drive, Google Docs, Google Sheets, Google Slides ou Google Drive Comments exige, antes da ação:

1. declarar o alvo exato;
2. declarar a ação pretendida;
3. pedir confirmação explícita do usuário.

Isso inclui criar, editar, mover, compartilhar, alterar permissões, comentar, responder, resolver e excluir. A autorização vale somente para os alvos e a ação nomeados na solicitação atual. Para excluir, identificar todos os alvos, explicar se serão movidos para a lixeira ou removidos permanentemente e pedir confirmação que nomeie a exclusão. Nunca inferir autorização para exclusão em lote ou alvo ambíguo.

Inspeção, busca e resumo somente leitura não exigem confirmação. Nesta consolidação não foi feita nenhuma mutação Google.

## 16. Regra final de continuidade

Antes de implementar, escrever outro documento, alterar um requisito ou responder a uma nova solicitação sobre o OneWorld, a futura IA deve:

1. consultar este arquivo;
2. verificar se a solicitação é confirmada, condicional, pendente ou fora do MVP;
3. conferir as fontes apenas para contexto e evidência;
4. apontar conflitos com este arquivo;
5. pedir nova decisão quando a mudança ultrapassar o que foi autorizado.

Este documento é a referência consolidada em 07/10/2026, mas decisões explícitas posteriores do usuário podem atualizá-lo.
