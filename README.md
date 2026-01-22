<div align="center">

# 🎯 X-Annotation YOLO Experience

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux-lightgrey.svg)]()
[![Languages](https://img.shields.io/badge/Languages-100%2B-orange.svg)]()

[🇺🇸 English](#-english) | [🇧🇷 Português](#-português)

</div>

---

<div id="english"></div>

## 🇺🇸 English

**A state-of-the-art, cross-platform dataset annotation tool for YOLO, built with Python & Tkinter.**

X-Annotation YOLO Experience is a professional-grade GUI for creating, visualizing, and managing object detection datasets. Designed for efficiency and reliability, it supports the latest YOLO formats (v5, v8, v11) and provides advanced features for computer vision workflows.

### ✨ Features

#### 🚀 Core Experience
*   **Modern Native UI**: Built with standard `tkinter` for maximum performance and native look-and-feel on Windows and Linux (no heavy external dependencies).
*   **Robust Stability**: Validated with an automated macro testing suite to ensure high reliability.
*   **Universal Compatibility**: Optimized for seamless operation across different operating systems with automatic font handling and DPI scaling.

#### 🌍 Global Reach
*   **Multi-Language Support**: Complete translations for **100+ languages**.
*   **Searchable Language Selector**: Quickly find your language with a smart, filterable dropdown.
*   **Intelligent Fallback**: Automatic English fallback ensures the interface never breaks, even if a translation is missing.

#### 🛠️ Advanced Tooling
*   **Project Management**:
    *   **Automated Setup**: Instantly creates standardized YOLO directory structures (`train`, `valid`, `test`, `data.yaml`).
    *   **Class Manager**: Add, rename, or delete classes dynamically.
*   **Data Analysis**:
    *   **Grid Viewer**: Visualize your dataset in a mosaic grid to spot inconsistencies.
    *   **Dataset Analyzer**: Generating distribution charts and statistics (train/val split ratio, class balance).
    *   **Split Wizard**: Easily redistribute images between training and validation sets with intuitive sliders.

#### ✏️ Annotation Power
*   **Smart Drawing**: Rapid bounding box creation with "Draw Mode" (`B`).
*   **Fine Controls**:
    *   Precision resizing with "W" and "H" spinners (with safety checks against inversion).
    *   Pixel-perfect movement using arrow keys or UI controls.
*   **Zoom & Pan**: Smooth navigation using mouse wheel and drag (right/middle click) for detailing high-res images.

### 🛠️ Installation

Ensure you have **Python 3.10+** installed.

#### 1. Clone the Repository
```bash
git clone https://github.com/SeuUsuario/X-Anotation_YOLO-Experience.git
cd X-Anotation_YOLO-Experience
```

#### 2. Create a Virtual Environment (Recommended)
**Linux/Mac:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Windows:**
```powershell
python -m venv .venv
.venv\Scripts\activate
```

#### 3. Install Dependencies
```bash
pip install -r requirements.txt
```
*(Or manually: `pip install pillow pyyaml`)*

### 🚀 Usage

Launch the application:
```bash
python main.py
```

#### Workflow

1.  **Create Project**: Click `✨ New Project`, define your classes, and choose a save location.
2.  **Add Data**: Drop your images into the created `train/images` folder.
3.  **Annotate**:
    *   Press `B` to toggle **Draw Mode**.
    *   Drag to draw boxes.
    *   Select classes from the right panel.
4.  **Manage**: Use the `Statistics` or `Grid` tabs to audit your dataset quality.
5.  **Export**: Your data is always saved in real-time in standard YOLO format (`.txt` files).

### ⌨️ Shortcuts

| Action | Control / Key |
| :--- | :--- |
| **Draw Mode** | `B` (Toggle) |
| **Next Image** | `Right Arrow` |
| **Previous Image** | `Left Arrow` |
| **Delete Box** | `Delete` |
| **Next Annotation** | `S` |
| **Prev Annotation** | `W` |
| **Zoom** | `Mouse Wheel` |
| **Pan Image** | `Right/Middle Click + Drag` |
| **Cancel** | `Esc` |

### 📂 Project Structure

X-Annotation adheres to the rigorous YOLO filesystem standard:

```text
MyProject/
├── classes.txt       # Class definitions
├── data.yaml         # Dataset configuration needed for training
├── train/
│   ├── images/       # Source images
│   └── labels/       # YOLO format annotations
├── valid/
│   ├── images/
│   └── labels/
└── test/
    ├── images/
    └── labels/
```

### 🔧 Architecture

The project follows a clean, modular Model-View-Controller (MVC) adaptation:

*   **`main.py`**: Application entry point and controller orchestrator.
*   **`ui.py`**: UI definition (View) using pure Tkinter/TTK.
*   **`canvas.py`**: Complex canvas logic (Zoom, Pan, Draw, Resize).
*   **`state.py`**: Centralized application state management.
*   **`localization.py`**: Dynamic translation engine.
*   **`managers.py`**: E/S de arquivos para formatos YOLO.
*   **`tests/macro/`**: Automated UI test suite for stability verification.

### 📄 License

Distributed under the **MIT License**. See `LICENSE` for more information.

---

<div id="português"></div>

## 🇧🇷 Português

**Uma ferramenta de anotação de datasets para YOLO de última geração e multiplataforma, construída com Python e Tkinter.**

X-Annotation YOLO Experience é uma interface gráfica profissional para criar, visualizar e gerenciar datasets de detecção de objetos. Projetado para eficiência e confiabilidade, suporte os formatos YOLO mais recentes (v5, v8, v11) e fornece recursos avançados para fluxos de trabalho de visão computacional.

### ✨ Funcionalidades

#### 🚀 Experiência Principal
*   **Interface Nativa Moderna**: Construída com `tkinter` padrão para desempenho máximo e visual nativo no Windows e Linux (sem dependências externas pesadas).
*   **Estabilidade Robusta**: Validada com uma suíte de testes de macro automatizados para garantir alta confiabilidade.
*   **Compatibilidade Universal**: Otimizada para operação perfeita em diferentes sistemas operacionais com manipulação automática de fontes e escala de DPI.

#### 🌍 Alcance Global
*   **Suporte Multi-Idioma**: Traduções completas para **100+ idiomas**.
*   **Seletor de Idioma Pesquisável**: Encontre rapidamente seu idioma com um menu suspenso inteligente e filtrável.
*   **Fallback Inteligente**: O fallback automático para inglês garante que a interface nunca quebre, mesmo se uma tradução estiver faltando.

#### 🛠️ Ferramentas Avançadas
*   **Gerenciamento de Projetos**:
    *   **Configuração Automatizada**: Cria instantaneamente estruturas de diretórios YOLO padronizadas (`train`, `valid`, `test`, `data.yaml`).
    *   **Gerenciador de Classes**: Adicione, renomeie ou exclua classes dinamicamente.
*   **Análise de Dados**:
    *   **Visualizador de Grade**: Visualize seu dataset em uma grade de mosaico para identificar inconsistências.
    *   **Analisador de Dataset**: Geração de gráficos de distribuição e estatísticas (proporção de divisão treino/val, equilíbrio de classes).
    *   **Assistente de Divisão**: Redistribua facilmente imagens entre conjuntos de treinamento e validação com controles deslizantes intuitivos.

#### ✏️ Poder de Anotação
*   **Desenho Inteligente**: Criação rápida de caixas delimitadoras com "Modo de Desenho" (`B`).
*   **Controles Finos**:
    *   Redimensionamento de precisão com spinners "W" e "H" (com verificações de segurança contra inversão).
    *   Movimento pixel a pixel usando teclas de seta ou controles da interface.
*   **Zoom e Pan**: Navegação suave usando a roda do mouse e arrastar (clique direito/meio) para detalhar imagens de alta resolução.

### 🛠️ Instalação

Certifique-se de ter **Python 3.10+** instalado.

#### 1. Clonar o Repositório
```bash
git clone https://github.com/SeuUsuario/X-Anotation_YOLO-Experience.git
cd X-Anotation_YOLO-Experience
```

#### 2. Criar um Ambiente Virtual (Recomendado)
**Linux/Mac:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Windows:**
```powershell
python -m venv .venv
.venv\Scripts\activate
```

#### 3. Instalar Dependências
```bash
pip install -r requirements.txt
```
*(Ou manualmente: `pip install pillow pyyaml`)*

### 🚀 Uso

Inicie a aplicação:
```bash
python main.py
```

#### Fluxo de Trabalho

1.  **Criar Projeto**: Clique em `✨ New Project`, defina suas classes e escolha um local de salvamento.
2.  **Adicionar Dados**: Solte suas imagens na pasta `train/images` criada.
3.  **Anotar**:
    *   Pressione `B` para alternar o **Modo de Desenho**.
    *   Arraste para desenhar caixas.
    *   Selecione classes no painel direito.
4.  **Gerenciar**: Use as abas `Statistics` ou `Grid` para auditar a qualidade do seu dataset.
5.  **Exportar**: Seus dados são sempre salvos em tempo real no formato YOLO padrão (arquivos `.txt`).

### ⌨️ Atalhos

| Ação | Controle / Tecla |
| :--- | :--- |
| **Modo de Desenho** | `B` (Alternar) |
| **Próxima Imagem** | `Seta Direita` |
| **Imagem Anterior** | `Seta Esquerda` |
| **Excluir Caixa** | `Delete` |
| **Próxima Anotação** | `S` |
| **Anotação Anterior** | `W` |
| **Zoom** | `Roda do Mouse` |
| **Mover Imagem** | `Clique Direito/Meio + Arrastar` |
| **Cancelar** | `Esc` |

### 📂 Estrutura do Projeto

O X-Annotation adere ao rigoroso padrão de sistema de arquivos YOLO:

```text
MyProject/
├── classes.txt       # Definições de classes
├── data.yaml         # Configuração do dataset necessária para treinamento
├── train/
│   ├── images/       # Imagens de origem
│   └── labels/       # Anotações no formato YOLO
├── valid/
│   ├── images/
│   └── labels/
└── test/
    ├── images/
    └── labels/
```

### 🔧 Arquitetura

O projeto segue uma adaptação limpa e modular de Model-View-Controller (MVC):

*   **`main.py`**: Ponto de entrada da aplicação e orquestrador do controlador.
*   **`ui.py`**: Definição da UI (View) usando Tkinter/TTK puro.
*   **`canvas.py`**: Lógica complexa do canvas (Zoom, Pan, Desenhar, Redimensionar).
*   **`state.py`**: Gerenciamento centralizado de estado da aplicação.
*   **`localization.py`**: Motor de tradução dinâmica.
*   **`managers.py`**: E/S de arquivos para formatos YOLO.
*   **`tests/macro/`**: Suíte de testes de UI automatizados para verificação de estabilidade.

### 📄 Licença

Distribuído sob a **Licença MIT**. Veja `LICENSE` para mais informações.

<p align="center">
  <i>Quality Tools for Computer Vision. Built with ❤️ by the X-Annotation Team.</i>
</p>