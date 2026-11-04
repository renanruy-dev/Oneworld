# OneWorld — Escopo (compacto p/ IA)

BI local Python, open-source. Extensionista Big Data, 6 alunos, 15/09–18/11. MVP; código c/ apoio IA.

Parceiro externo (exigência disciplina, NÃO direciona escopo): Casa Grande Eventos / contato Kleber — ref. apenas; não implementar p/ necessidades dele salvo pedido explícito.

## Stack
Python | Streamlit (dashboard) | pandas | SQLite (`to_sql()`, tipo auto) | `.env` (secrets) | IA externa BYOK: OpenAI / Anthropic / Gemini

## Entrada de dados
1. Template padrão — sem IA [MVP]
2. Manual (formulário) — sem IA [MVP]
3. Planilha livre — com IA [extra]: IA recebe amostra (não a planilha inteira) → mapeamento coluna→campo → usuário revisa/edita (cards) → confirma inserção

## Schema/domínio
Padrão pré-config, editável [MVP] | Genérico (campos do zero) [fora MVP] | IA NUNCA define schema — só mapeia dado→campo existente

## IA — única função
Mapear planilha não estruturada (modo 3) | SEM chatbot interno c/ contexto BI | SEM participação em criação de domínio | Limite 1 chamada/dia (contador SQLite, reset diário) | Config: dropdown provedor + key mascarada + teste conexão | Key grátis; uso pode ter custo (exceto Gemini free tier → p/ testes)

## Decision Intelligence (fora do sistema)
Export Markdown do BI via pandas/código — SEM IA, sem limite. Usuário cola em IA externa de preferência p/ análise decisória.

## Usuário/infra
Uso único, sem login/auth. Local, single-instance.

## Fora do MVP
Domínio genérico | Multiusuário/auth | Chatbot interno | Billing avançado

## Pendências
Local storage API key (.env vs SQLite) — decidir na implementação | Dados demo — não criados | Avaliação: relatório escrito (detalhe separado)

---

## Entregas (disciplina)
E2 16/09 Planejamento (cronograma, metodologia, recursos, riscos, indicadores, comunicação) | E3 07/10 Ata de validação+revisão (validar proposta, apresentar escopo/req/protótipos ao cliente, registrar sugestões, ajustar) | E4 04/11 Dev/Sprint (interfaces, dashboard, gráficos, análises; KDD/ML se pertinente) | E5 18/11 Implantação+capacitação (implantar, manual, treinar usuário, avaliação de reação) | E6 25/11 Apresentação+avaliação final (problema, diagnóstico, solução, tech, resultados, ODS/ESG, demo; relatório final c/ relato coletivo+individual)
Fases internas: não definidas; datas acima = prazos/marcos máx.

## Metodologia
PBL. Reunião 01/09: levantamento de requisitos c/ cliente (Kleber)

## Recursos
6 alunos | orientadora: Larissa de Paula Serrão Garcia | ferramentas = stack (BYOK etc) | carga horária: N/A p/ planejamento

## Papéis (divisão pela equipe, não pela IA)
Dev Backend | Dev Frontend/Dashboard | Dev IA | Dados/Banco | QA/Documentação | Gestão/Comunicação

## Riscos
Levantamento enxuto (prazo curto, dependência BYOK, IA escopo limitado, parceiro não vinculante). Matriz prob×impacto só se exigida pela disciplina "Tópicos de Big Data" (a confirmar)

## Indicadores
Foco: progresso do projeto (não produto)

## Comunicação c/ parte interessada
Kleber = cliente (requisitos+testes, NÃO define escopo). Contatos: reunião 01/09 (feita) + validação E3 07/10 (prevista). Aberto a mais se necessário. Orientadora Larissa = parte interessada institucional
