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
- 📝 **Bloco de Anotações:** Registro de observações, pendências e anotações com datas previstas.
- 💾 **Backup e Segurança:** Sistema de cópia de segurança manual dos dados locais com timestamp.
- 🎨 **Personalização Visual:** Suporte a temas Claro, Escuro e Automático com paleta de cores corporativa personalizada.

---

## 🗂️ Estrutura do Projeto

```text
Oneworld/
├── oneworld/
│   ├── __init__.py          # Inicialização do pacote Python
│   ├── backend.py           # Regras de negócio, formatação e processamento de dados
│   ├── config.py            # Constantes, perfis de negócio e esquemas de dados
│   ├── database.py          # Camada de persistência e acesso a dados (SQLite)
│   ├── frontend.py          # Interface gráfica desktop nativa e componentes (PyQt6)
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

## 📦 Dependências

As bibliotecas utilizadas estão listadas no arquivo `requirements.txt`:

- [PyQt6](https://pypi.org/project/PyQt6/) — Interface gráfica desktop nativa
- [Pandas](https://pandas.pydata.org/) — Manipulação e análise estruturada de dados
- [OpenPyXL](https://openpyxl.readthedocs.io/) — Leitura e gravação de arquivos Excel (.xlsx)

---

## 📄 Licença

Este projeto é desenvolvido para fins acadêmicos e operacionais. Consulte os autores para detalhes sobre distribuição.
