<div align="center">
  <img src="OneWorld-logo.jpg" alt="OneWorld Logo" width="220" />
  <h1>OneWorld</h1>
  <p><strong>Plataforma Desktop de Gestão Empresarial e BI Operacional</strong></p>

  <p>
    <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
    <img src="https://img.shields.io/badge/PyQt6-41CD52?style=for-the-badge&logo=qt&logoColor=white" alt="PyQt6" />
    <img src="https://img.shields.io/badge/Pandas-150458?style=for-the-badge&logo=pandas&logoColor=white" alt="Pandas" />
    <img src="https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white" alt="SQLite" />
  </p>
</div>

---

## 📌 Sobre o Projeto

O **OneWorld** é uma aplicação desktop nativa, multiplataforma e modular desenvolvida em **Python** e **PyQt6** para Business Intelligence (BI) e gestão de pequenos negócios e empreendimentos.

O sistema opera de forma 100% local com banco de dados **SQLite**, garantindo total privacidade, agilidade e autonomia de dados, sem dependência de navegadores externos. Conta com perfis de negócio configuráveis (Gestão Geral, Vendas, Serviços e Eventos), suporte a importação inteligente de planilhas (Excel, CSV e JSON) e recursos analíticos.

---

## 🚀 Funcionalidades Principais

- 📊 **Dashboard Integrado:** Visão consolidada de operações ativas, volume/quantidade, receita prevista, pendências e gráficos de barras nativos em tempo real.
- 🏢 **Perfis de Negócio & Nomenclatura Personalizável:** Alterne entre perfis prontos (*Gestão Empresarial Geral*, *Comércio & Vendas*, *Serviços & Projetos*, *Eventos & Recepção*) ou personalize os nomes de menus e colunas livremente.
- 📋 **Gestão de Operações & Cadastros:** Cadastro completo, acompanhamento de status (*Em planejamento*, *Confirmado*, *Concluído*, *Pendente*) e controle de valores.
- 📥 **Importação Inteligente de Planilhas:** Mapeamento automático de cabeçalhos com detecção de sinônimos para arquivos `.xlsx`, `.xls`, `.csv` e `.json`.
- 💡 **Orientação com IA & Exportação:** Módulo de análises com geração de relatórios e exportação estruturada em Markdown para Decision Intelligence.
- 🧾 **Planilha padrão e IA externa:** Exportação em XLSX padrão com prompts prontos para levar manualmente a um chat de IA (sem chave de API) e reimportação com prévia e confirmação. Veja [Planilha padrão e IA externa](#-planilha-padrão-e-ia-externa).
- 📝 **Bloco de Anotações:** Registro de observações, pendências e anotações com datas previstas.
- 💾 **Backup e Segurança:** Cópia rápida do banco local e backup completo em JSON, com restauração (substituir os dados atuais) ou complementação (adicionar apenas o que falta). Veja [Backup e restauração](#-backup-e-restauração).
- 🎨 **Personalização Visual:** Suporte a temas Claro, Escuro e Automático com paleta de cores corporativa personalizada.

---

## 🗂️ Estrutura do Projeto

```text
Oneworld/
├── oneworld/
│   ├── __init__.py          # Inicialização do pacote Python
│   ├── backend.py           # Regras de negócio, formatação e processamento de dados
│   ├── backup.py            # Backup completo em JSON: exportar, validar, substituir e adicionar o que falta
│   ├── config.py            # Constantes, perfis de negócio e esquemas de dados
│   ├── database.py          # Camada de persistência e acesso a dados (SQLite)
│   ├── frontend.py          # Interface gráfica desktop nativa e componentes (PyQt6)
│   ├── planilha_padrao.py   # Planilha padrão XLSX, prompts para IA externa e reimportação com prévia
│   └── tema.py              # Definições de temas Claro/Escuro e estilos QSS
├── app.py                   # Ponto de entrada da aplicação desktop
├── Iniciar_OneWorld.bat     # Inicializador rápido para Windows (dois cliques)
├── OneWorld-logo.jpg        # Identidade visual / Logo do projeto
├── OneWorld.ico             # Ícone oficial do aplicativo desktop
├── requirements.txt         # Dependências do projeto (PyQt6, pandas, openpyxl)
├── AGENTS.md                # Diretrizes do assistente de código
├── .gitignore               # Regras de exclusão do Git
└── README.md                # Documentação do repositório
```

---

## ⚙️ Como Executar o Projeto Localmente

### Pré-requisitos

- **Python 3.10** ou superior instalado em seu sistema ([Download Python](https://www.python.org/downloads/)).
- **Git** instalado ([Download Git](https://git-scm.com/)).

### Passo a Passo

1. **Clone o repositório:**
   ```bash
   git clone https://github.com/renanruy-dev/Oneworld.git
   cd Oneworld
   ```

2. **Crie e ative um ambiente virtual (recomendado):**

   * No Windows (PowerShell):
     ```powershell
     python -m venv .venv
     .\.venv\Scripts\Activate.ps1
     ```

   * No Linux / macOS:
     ```bash
     python3 -m venv .venv
     source .venv/bin/activate
     ```

3. **Instale as dependências:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Inicie a aplicação:**

   * Via linha de comando:
     ```bash
     python app.py
     ```

   * No Windows (dois cliques):
     Basta executar o arquivo `Iniciar_OneWorld.bat`.

---

## 💾 Backup e restauração

Tudo fica em **Configurações › Segurança**.

### Cópia rápida do banco (`.db`)

O botão **Fazer backup agora** copia o arquivo `oneworld.db` para a pasta `backups/`. Serve como cópia de segurança, mas não é importado pela tela.

### Exportar backup completo (JSON)

1. Clique em **Exportar backup...** e escolha o nome e o local do arquivo.
2. O arquivo `.json` contém a identificação OneWorld, a versão do formato, a data de geração, a quantidade de registros e os dados das seis tabelas: operações (eventos), cadastros (convidados), anotações, relatórios de IA, histórico de arquivos importados e configurações (inclusive campos personalizados).
3. **Não entram no backup:** o arquivo `.env`, chaves de API (itens de configuração com nome de segredo, como `api_key`, `token` ou `senha`, são omitidos) e o banco público DFP (`dfp_cia_aberta.db`, que pode ser regenerado).

A leitura é feita em uma única transação (retrato consistente do banco). O arquivo é gravado primeiro como temporário e só depois renomeado, então uma falha nunca deixa um backup pela metade nem estraga um arquivo que já existia com o mesmo nome.

### Importar backup

Clique em **Importar backup...** e escolha o arquivo. Antes de qualquer alteração, o arquivo é validado por inteiro: identificação, versão, estrutura, tabelas, colunas, tipos de cada valor, campos extras e configurações JSON. Se algo estiver errado, a mensagem indica onde, e nada é alterado. Em seguida aparece o resumo com as quantidades por tabela e duas opções. **Cancelar** em qualquer etapa deixa o banco intacto.

#### Substituir dados atuais (restaurar)

- Apaga **todos** os dados e configurações atuais e coloca os do backup, **com os mesmos IDs** e vínculos.
- Pede confirmação explícita.
- Antes de alterar qualquer dado, salva uma cópia do banco atual em `backups/oneworld_antes_da_restauracao_<data>.db` e verifica a integridade dela. Se a cópia falhar, a restauração é interrompida.
- Tudo acontece em uma única transação: se der erro no meio, nada muda.
- Depois de restaurar, a tela recarrega as configurações do banco. Alterações não salvas na tela de Configurações são descartadas.

#### Adicionar apenas o que falta (complementar)

- Mantém todos os registros atuais e acrescenta só os registros do backup que ainda não existem. Os registros inseridos recebem **novos IDs**.
- Mantém as configurações atuais. Só **une os campos personalizados** do backup que forem compatíveis.
- Mostra uma prévia (quantos registros serão adicionados e quantos ignorados por tabela) e, no fim, o total adicionado e ignorado.
- Reimportar o mesmo backup não adiciona nada de novo.

**Como a comparação funciona (e seus limites):**

- Compara o **conteúdo completo** de cada registro, **sem o ID**. Não usa "cliente + data" como chave.
- Considera iguais apenas equivalências seguras: números equivalentes (`10` e `10.0`) e campos extras com o mesmo conteúdo em outra ordem ou formatação.
- **Não** remove espaços, **não** ignora maiúsculas/minúsculas e **não** trata vazio (`""`) como igual a nulo. `"Ana"` e `"Ana "` são registros diferentes.
- Conta ocorrências: se o banco tem 1 registro idêntico e o backup tem 3, são adicionados 2.
- **Não atualiza registros existentes.** Um registro que foi editado (ex.: mesmo cliente e data, outro valor) é considerado novo e é adicionado ao lado do antigo. Para voltar exatamente ao estado do backup, use *Substituir dados atuais*.
- O vínculo entre cadastros e operações (o texto do campo de vínculo) é gravado exatamente como está no backup.
- Um campo personalizado do backup é **incompatível** quando tem o nome de uma coluna padrão (ex.: "Valor") ou é parecido, mas não idêntico, a um campo atual (ex.: "fornecedor" × "Fornecedor"). Nesses casos o conflito é mostrado antes da gravação: você pode cancelar ou continuar sem adicionar esses campos à lista. Os valores deles continuam gravados nos dados extras dos registros importados.

---

## 🧾 Planilha padrão e IA externa

Fica em **Orientação IA › Planilha padrão e IA externa**. O OneWorld **não chama nenhuma IA** neste fluxo: você leva a planilha e o prompt, você mesmo, a um chat externo (ChatGPT, Gemini, Claude...). Ao fazer isso, os dados saem do seu computador.

### Exportar

1. Marque as tabelas: Operações e Cadastros (marcadas por padrão) e Anotações (opcional).
2. Se quiser, filtre por período. Operações e Anotações usam a própria data. **Cadastros não têm data**: entram quando a operação vinculada (mesmo texto em `evento` e `cliente`) está no período. Se houver operações com o mesmo nome dentro e fora do período, esses cadastros ficam de fora por vínculo ambíguo, e o arquivo informa quantos.
3. Escolha o tipo:
   - **Para análise:** resumo por mês e dados **sem** nomes, contatos, observações e campos personalizados (salvo se marcados), sem identificadores do sistema. O arquivo é marcado como *somente análise* e **não pode ser importado de volta**. Atenção: textos livres ainda podem conter informações pessoais.
   - **Para edição e reimportação:** todos os campos, com `id_oneworld` e `controle`. Antes de gerar, o sistema mostra as tabelas e quantidades e pede confirmação, avisando que nomes e contatos estarão no arquivo.
4. **Baixar modelo vazio** gera a mesma estrutura sem registros, para preencher do zero.
5. **Copiar prompt de análise** e **Copiar prompt de preenchimento** copiam textos que correspondem às tabelas marcadas. Os prompts também vão na aba `LEIA-ME` do arquivo.

### Estrutura do arquivo (formato `oneworld-planilha`, versão 1)

| Aba | Conteúdo | Na importação |
|---|---|---|
| `LEIA-ME` | Instruções e prompts | Ignorada |
| `OneWorld` | Identificação (formato, versão, tipo, `base_id`, data de geração, abas) e informações (período, contagens) | Identificação é obrigatória e não pode mudar; contagens são só informativas |
| `Dicionario` | Tipo, obrigatoriedade, significado do vazio e valores permitidos de cada coluna | Ignorada |
| `Resumo_Periodos` | Totais por mês: quantidade de operações e **valor previsto** | Ignorada |
| `Operacoes`, `Cadastros`, `Anotacoes` | Dados, com o cabeçalho na linha 1 | Validadas e importadas |

`valor` é sempre **valor previsto**, não pagamento recebido. O sistema não tem gastos, impostos nem receita realizada.

### Importar

**Importar planilha preenchida...** aceita somente `.xlsx` exportado **para edição** ou o modelo vazio. Primeiro aparece uma **prévia**, com inclusões, alterações, limpezas, vínculos atualizados, duplicados, linhas sem gravação, conflitos e erros. Abrir a prévia ou cancelar não altera nada.

- **Tudo ou nada:** qualquer erro ou conflito bloqueia a confirmação.
- Ao confirmar, o sistema cria uma cópia do banco em `backups/` (se ela falhar, a importação para), refaz toda a validação dentro de uma transação e grava tudo de uma vez. O registro no histórico de arquivos entra na mesma transação. Se os dados mudaram desde a prévia, nada é gravado e você precisa revisar de novo.

**Como cada linha é tratada:**

- **Linha nova** (`id_oneworld` e `controle` vazios) vira inclusão. Se o conteúdo for idêntico a um registro existente ou a uma linha anterior do arquivo, é marcada como **duplicada** e ignorada.
- **Linha existente** é identificada por `base_id` + `id_oneworld` + `controle`, nunca por nome ou posição. O `controle` é o SHA-256 do registro como estava na exportação; ele verifica consistência, não autentica o arquivo.
  - O registro não mudou no sistema e a linha mudou: **alteração**.
  - O conteúdo da linha já está no sistema: **já aplicada** (reimportar o mesmo arquivo não repete nada).
  - O registro mudou no sistema e a linha não foi editada: **mantido** como está no sistema.
  - O registro mudou no sistema e a linha também: **conflito**.
- **Arquivo de outra base** nunca atualiza registros por coincidência de ID: as linhas são tratadas como inclusões, e as idênticas como duplicadas.
- **Célula vazia** em coluna presente **limpa** o valor; números ficam 0. A limpeza aparece destacada na prévia. Campos obrigatórios não podem ficar vazios.
- **Coluna removida** não altera nada. **Linha removida** não exclui nada.
- **Valores permitidos:** status e situação só aceitam os valores exatos da lista. Datas: `AAAA-MM-DD`, `DD/MM/AAAA` ou célula de data do Excel. Números: célula numérica ou texto como `1.234,56`.
- **Colunas de texto** precisam conter texto; um número é recusado para não perder zeros à esquerda.
- **Recusados:** fórmulas, abas ou colunas desconhecidas, campos personalizados inexistentes e abas que não faziam parte da exportação. O OneWorld **não cria tabelas, colunas nem campos** a partir do arquivo.

**Vínculos por texto:** um cadastro aponta para a operação pelo texto do nome, e `cliente` não é único. Por isso:

- Os vínculos são validados no estado final da importação, contando operações novas e renomeadas.
- Um cadastro que aponta para uma operação inexistente, ou para um nome usado por mais de uma operação, bloqueia a importação.
- Renomear uma operação atualiza os cadastros vinculados (mesmo os que não estão na planilha) somente quando não há ambiguidade. Se houver duas operações com o nome antigo, ou se outra operação ficar com esse nome, a mudança é bloqueada com a explicação do motivo.

---

## 📦 Dependências

As bibliotecas utilizadas estão listadas no arquivo `requirements.txt`:

- [PyQt6](https://pypi.org/project/PyQt6/) — Interface gráfica desktop nativa
- [Pandas](https://pandas.pydata.org/) — Manipulação e análise estruturada de dados
- [OpenPyXL](https://openpyxl.readthedocs.io/) — Leitura e gravação de arquivos Excel (.xlsx)

---

## 📄 Licença

Este projeto é desenvolvido para fins acadêmicos e operacionais. Consulte os autores para detalhes sobre distribuição.
