<div align="center">
  <img src="OneWorld-logo.jpg" alt="OneWorld Logo" width="220" />
  <h1>OneWorld</h1>
  <p><strong>Plataforma de Gestão de Eventos, Convidados e BI Operacional</strong></p>

  <p>
    <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
    <img src="https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white" alt="Streamlit" />
    <img src="https://img.shields.io/badge/Pandas-150458?style=for-the-badge&logo=pandas&logoColor=white" alt="Pandas" />
    <img src="https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white" alt="SQLite" />
  </p>
</div>

---

## 📌 Sobre o Projeto

O **OneWorld** é uma aplicação completa e modular desenvolvida em Python e Streamlit para gerenciamento de eventos corporativos e sociais, controle de convidados e análise de dados em tempo real.

O sistema opera de forma local com banco de dados **SQLite**, garantindo privacidade, agilidade e autonomia de dados, além de contar com suporte a importação inteligente de planilhas (Excel e CSV) e recursos analíticos.

---

## 🚀 Funcionalidades Principais

- 📊 **Dashboard Integrado:** Visão consolidada de eventos ativos, valores orçados, previsão de público e status operacional.
- 📅 **Gestão de Eventos:** Cadastro completo, acompanhamento de status (*Em planejamento*, *Confirmado*, *Concluído*, *Pendente*) e controle orçamentário.
- 👥 **Gestão de Convidados:** Controle de presença, alocação de mesas, acompanhantes, contatos e restrições alimentares.
- 📥 **Importação Inteligente de Planilhas:** Mapeamento automático de cabeçalhos com detecção de sinônimos para arquivos `.xlsx`, `.xls` e `.csv`.
- 💡 **Orientação com IA:** Módulo de assistência contextual com análises, insights e geração de relatórios.
- 📝 **Bloco de Anotações:** Registro de observações, pendências e anotações vinculadas aos eventos.
- 💾 **Backup e Segurança:** Sistema de backup automático e manual dos dados locais com restauração simplificada.
- 🎨 **Personalização Visual:** Suporte a temas Claro e Escuro com paleta de cores corporativa personalizada.

---

## 🗂️ Estrutura do Projeto

```text
Oneworld/
├── .streamlit/
│   └── config.toml          # Configuração de temas e parâmetros do Streamlit
├── oneworld/
│   ├── __init__.py          # Inicialização do pacote Python
│   ├── backend.py           # Regras de negócio, formatação e processamento de dados
│   ├── config.py            # Constantes, rotas de arquivos e esquemas de tabelas
│   ├── database.py          # Camada de persistência e acesso a dados (SQLite)
│   ├── frontend.py          # Interface gráfica e componentes de tela (Streamlit)
│   └── tema.py              # Definições de estilos CSS e temas (Claro/Escuro)
├── app.py                   # Ponto de entrada da aplicação
├── OneWorld-logo.jpg        # Identidade visual / Logo do projeto
├── requirements.txt         # Dependências do projeto
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
     python -m venv venv
     .\venv\Scripts\Activate.ps1
     ```

   * No Linux / macOS:
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```

3. **Instale as dependências:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Inicie a aplicação:**
   ```bash
   streamlit run app.py
   ```

5. **Acesse no navegador:**
   O Streamlit abrirá automaticamente no endereço: `http://localhost:8501`.

---

## 📦 Dependências

As bibliotecas utilizadas estão listadas no arquivo `requirements.txt`:

- [Streamlit](https://streamlit.io/) — Interface web interativa
- [Pandas](https://pandas.pydata.org/) — Manipulação e análise estruturada de dados
- [OpenPyXL](https://openpyxl.readthedocs.io/) — Leitura e gravação de arquivos Excel (.xlsx)

---

## 📄 Licença

Este projeto é desenvolvido para fins operacionais e de demonstração. Consulte o autor para detalhes sobre distribuição e uso comercial.
