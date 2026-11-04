# OneWorld — Contexto e Escopo do Projeto (Atualizado)

Projeto: sistema de BI local em Python, **open source**. Trabalho extensionista (Big Data), 6 estudantes, prazo 15/09–18/11. Abordagem: MVP/protótipo, código gerado com apoio de IA.

Nota: existe parceiro externo formal (empresa fictícia/real "Casa Grande Eventos", contato Kleber) exigido pelos parâmetros da disciplina. Suas necessidades específicas (previsão de demanda, gestão de fornecedores) NÃO direcionam o escopo funcional — mantido apenas como informação de referência, não implementar com base nele a menos que solicitado.

## Stack
- Python
- Dashboard: Streamlit
- Dados: pandas
- Banco: SQLite (tabelas via `to_sql()`, inferência automática de tipo)
- Config/segredos: `.env`
- IA externa: BYOK (usuário fornece própria API key) — OpenAI, Anthropic (Claude), Gemini

## Modos de entrada de dados
1. **Template padrão** (sem IA) — planilha-modelo fornecida pelo sistema, leitura direta. [MVP]
2. **Manual** (sem IA) — formulário na interface. [MVP]
3. **Planilha livre** (com IA) — formato desconhecido; IA recebe amostra (não a planilha inteira) e retorna mapeamento coluna→campo; usuário revisa/edita em tela de cards antes de confirmar inserção. [extra, se houver tempo]

## Domínio (schema)
- Padrão pré-configurado, editável pelo usuário. [MVP]
- Genérico (usuário cria campos do zero). [fora do MVP]
- IA nunca define estrutura/schema — só mapeia dados para estrutura já existente.

## Escopo da IA — única função no sistema
- Sugerir mapeamento de planilha não estruturada (Modo 3 acima).
- Sem chatbot interno com contexto do BI (removido do escopo).
- Sem participação em criação de domínio.
- Limite: 1 chamada de IA/dia (contador no SQLite, reset diário).
- Conexão: usuário insere key própria em tela de configurações (dropdown provedor + campo key mascarado + teste de conexão). Key gratuita de gerar; uso pode gerar custo (exceto Gemini free tier, recomendado para testes).

## Decision Intelligence (fora do sistema)
- Sistema gera export em Markdown do conteúdo do BI — **sem usar IA** (só pandas/código), portanto sem limite de uso.
- Usuário cola esse Markdown em chatbot de IA externo de sua preferência para análises de decisão.

## Usuário / infraestrutura
- Uso único, sem login/autenticação.
- Local, single-instance.

## Fora do MVP (trabalho futuro)
- Domínio genérico
- Multiusuário/autenticação
- Chatbot interno
- Billing avançado

## Pendências
- Onde salvar API key (.env vs tabela SQLite) — a decidir na implementação
- Dados de demonstração — ainda não criados
- Avaliação da disciplina será via relatório escrito (detalhamento à parte)

---

# Gestão do Projeto Extensionista

## Entregas e cronograma da disciplina
| Entrega | Prazo | Conteúdo |
|---|---|---|
| 2 | 16/09 | Planejamento: cronograma, metodologia, recursos, riscos, indicadores, plano de comunicação com a parte interessada |
| 3 | 07/10 | Ata de validação e versão revisada do projeto: validar proposta, apresentar escopo/requisitos/protótipos à parte interessada, registrar sugestões, ajustar proposta |
| 4 | 04/11 | Desenvolvimento (Sprint): criar interfaces, dashboard, gráficos e análises; aplicar KDD/ML quando pertinente |
| 5 | 18/11 | Implantação e capacitação: implantar/disponibilizar sistema, produzir manual, treinar usuário responsável, aplicar avaliação de reação |
| 6 | 25/11 | Apresentação e avaliação final: apresentar problema, diagnóstico, solução, tecnologias, resultados, contribuição sociocomunitária, ODS, ESG + demonstração do sistema; entrega do relatório final completo (relato coletivo e individual) |

Observação: a divisão interna de fases (dentro de cada entrega) ainda não foi definida pela equipe. As datas acima funcionam como prazos/marcos máximos.

## Metodologia
- PBL (Aprendizagem Baseada em Projetos).
- Reunião realizada em 01/09: levantamento de requisitos e entendimento da dor do cliente (Kleber / Casa Grande Eventos).

## Recursos
- Equipe: 6 estudantes.
- Orientadora da disciplina: Larissa de Paula Serrão Garcia.
- Ferramentas: as listadas na seção Stack (incluindo IA externa BYOK).
- Carga horária individual dos estudantes: não definida (não considerada relevante para este planejamento).

## Papéis da equipe
6 papéis previstos; a divisão entre os integrantes específicos será feita pela própria equipe (fora do escopo deste documento):
1. Dev Backend
2. Dev Frontend/Dashboard
3. Dev IA (integração BYOK / mapeamento)
4. Dados/Banco (SQLite, modelagem)
5. QA/Documentação
6. Gestão/Comunicação

## Riscos
- Levantamento a ser feito de forma enxuta e sem grande profundidade, cobrindo pontos como: prazo curto, dependência do BYOK (usuário precisa fornecer própria key), escopo da IA deliberadamente limitado, parceiro externo não vinculante ao escopo (risco de expectativa desalinhada), entre outros.
- Classificação formal por matriz de probabilidade x impacto só será incluída se exigida pelo escopo da disciplina "Tópicos de Big Data" (a confirmar).

## Indicadores
- Foco em indicadores de **progresso do projeto** (não indicadores de produto/BI).

## Plano de comunicação com a parte interessada
- **Parte interessada externa (cliente):** Kleber / Casa Grande Eventos — papel de cliente para levantamento de requisitos e testes; suas necessidades específicas NÃO direcionam o escopo funcional do sistema.
  - Contato já realizado: reunião de 01/09 (levantamento de requisitos, entendimento da dor do cliente).
  - Contato previsto: validação de escopo/requisitos/protótipos na Entrega 3 (07/10).
  - Aberto a novos contatos futuros, conforme necessidade.
- **Parte interessada institucional:** orientadora Larissa de Paula Serrão Garcia.
