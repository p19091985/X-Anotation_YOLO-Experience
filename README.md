<h1 align="center">🎯 X-Anotation_YOLO-Experience</h1>

<p align="center"><strong>A reusable Tkinter-based workspace for annotating, reviewing, splitting, and analyzing YOLO datasets.</strong></p>

<p align="center">
  <img src="https://img.shields.io/badge/version-Template-0d6efd?style=for-the-badge" alt="version" />
  <img src="https://img.shields.io/badge/status-reusable%20base-2f6b3f?style=for-the-badge" alt="status" />
  <img src="https://img.shields.io/badge/license-MIT-292929?style=for-the-badge" alt="license" />
</p>
<p align="center">
  <img src="https://img.shields.io/badge/Python-3.x-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/UI-Tkinter-1f6f43?style=flat-square" alt="Tkinter" />
  <img src="https://img.shields.io/badge/Format-YOLO-aa6c39?style=flat-square" alt="YOLO" />
</p>

<p align="center">
  <kbd><a href="#english">🇬🇧 English</a></kbd>&nbsp;&nbsp;
  <kbd><a href="#portugues">🇧🇷 Português</a></kbd>
</p>

---

<!-- ═══════════════════════════════════════════════════════════ -->
<!-- ██████████████████   ENGLISH SECTION   ██████████████████ -->
<!-- ═══════════════════════════════════════════════════════════ -->

<a id="english"></a>

<h2 align="center">🇬🇧 English</h2>

<p align="center"><strong>A reusable Python + Tkinter base for YOLO dataset tooling.</strong></p>

<p align="center"><em>This project is designed as a template repository rather than a client-specific product.<br />It gives you a starting point for annotation, review, dataset cleanup, split management, and analysis.</em></p>

---

### 📑 Table of Contents

| | Section | | Section |
|:---|:---|:---|:---|
| 🎯 | [Why This Template Exists](#why-this-template-exists) | 🧩 | [Main Workflows](#main-workflows) |
| ✨ | [Highlights](#highlights) | 📂 | [Repository Tour](#repository-tour) |
| 🚀 | [Quick Start](#quick-start) | 🏗️ | [Architecture at a Glance](#architecture-at-a-glance) |
| 🔧 | [Manual Setup](#manual-setup) | 🧪 | [Running Tests](#running-tests) |
| 💻 | [Requirements](#requirements) | ⚙️ | [Reuse and Customization](#reuse-and-customization) |
| ⌨️ | [Keyboard Shortcuts](#keyboard-shortcuts) | 📄 | [License](#license-en) |

---

<a id="why-this-template-exists"></a>

## 🎯 Why This Template Exists

This repository is meant to be a **practical base** for teams that work with YOLO-style datasets and want a UI-first workflow in Python.

<table>
  <tr>
    <td align="center" width="25%">🖍️<br /><strong>ANNOTATE</strong><br /><sub>Create and edit bounding boxes, with optional polygon support for segmentation workflows.</sub></td>
    <td align="center" width="25%">🧹<br /><strong>CLEAN</strong><br /><sub>Create derived dataset copies that can filter unlabeled images, ignore empty labels, and apply random reduction.</sub></td>
    <td align="center" width="25%">📊<br /><strong>ANALYZE</strong><br /><sub>Inspect class distribution, split balance, orphan files, and dataset integrity issues.</sub></td>
    <td align="center" width="25%">🧱<br /><strong>REUSE</strong><br /><sub>Turn features on or off through configuration and adapt the project into client-specific internal tools.</sub></td>
  </tr>
</table>

- It is intentionally generic and reusable
- It keeps the application identity, labels, and visible buttons configurable
- It includes both operational tools and automated tests
- It is structured so derived applications can keep the same backbone while changing branding and workflow details

---

<a id="highlights"></a>

## ✨ Highlights

| Feature | Description |
|:---|:---|
| 🖼️ Image annotation | Bounding box workflow with optional polygon mode |
| 🔎 Fast review | Image list, annotation list, zoom presets, mouse-wheel zoom, and pan mode |
| ✂️ Dataset tools modal | One dialog can create filtered or reduced dataset copies without touching the original |
| 🧪 Split wizard | Train / valid / optional test split with visual percentage controls |
| 📈 Analyzer | Charts, summaries, orphan checks, and class-level distribution views |
| 🌍 Localization | UI text comes from `languages.xml` and can be switched at runtime |
| ⚙️ Feature flags | `config.py` can hide or simplify modules for derived builds |
| 🧪 Test suite | Automated tests live under `tests/` and cover workflows, managers, and smoke checks |

---

<a id="quick-start"></a>

## 🚀 Quick Start

### Run the app

<table>
<tr>
<td align="center"><b>🐧 Linux / 🍎 macOS / WSL</b></td>
<td align="center"><b>🪟 Windows PowerShell</b></td>
</tr>
<tr>
<td>

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

</td>
<td>

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

</td>
</tr>
</table>

### First things to try

1. Open an existing dataset or create a new YOLO structure
2. Review images and labels in the main window
3. Use `Dataset Tools` to create a derived copy with filtering and/or reduction
4. Run the split wizard if you need `train`, `valid`, and `test`
5. Open the analyzer for distribution and integrity checks

---

<a id="manual-setup"></a>

## 🔧 Manual Setup

<details>
<summary>🔽 Expand manual environment setup</summary>

### 1. Create the virtual environment

```bash
python -m venv .venv
```

### 2. Activate it

```bash
# Linux / macOS / WSL
source .venv/bin/activate

# Windows PowerShell
.venv\Scripts\Activate.ps1

# Windows CMD
.venv\Scripts\activate.bat
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Start the application

```bash
python main.py
```

</details>

---

<a id="requirements"></a>

## 💻 Requirements

| Item | Requirement |
|:---|:---|
| 🐍 Python | Python 3 |
| 🖥️ GUI | Environment capable of opening a Tkinter window |
| 🖼️ Imaging | `Pillow` |
| 📊 Analysis | `matplotlib`, `numpy`, `PyYAML` |
| 🌍 Localization tooling | `deep-translator` is used by the language generation workflow |

> The exact pinned versions are listed in [`requirements.txt`](requirements.txt).

---

<a id="main-workflows"></a>

## 🧩 Main Workflows

### Annotation and review

- Browse images from the current dataset
- Inspect saved annotations in the side list
- Edit labels while using zoom and pan controls
- Switch between box and polygon mode when polygon support is enabled

### Dataset copy tools

- Open the unified dataset tools button in the top toolbar
- Build a **derived copy** of the dataset instead of mutating the source
- Exclude images without labels
- Optionally exclude images whose label files are empty
- Optionally apply random reduction by percentage

### Dataset maintenance

- Create YOLO folder structures for new datasets
- Manage class names and keep YAML metadata synchronized
- Split datasets into `train`, `valid`, and optional `test`
- Run analysis for class balance and file-integrity checks

---

<a id="repository-tour"></a>

## 📂 Repository Tour

```text
.
├── main.py                  # main application controller
├── ui.py                    # main UI composition
├── canvas.py                # zoom, pan, drawing, and selection behavior
├── managers.py              # annotation I/O and dataset utilities
├── window_new_project.py    # YOLO structure creation window
├── window_split_wizard.py   # train/valid/test split flow
├── visualizador_grid.py     # grid review window
├── analisador_dataset.py    # dataset analysis and integrity checks
├── window_class_manager.py  # class rename/remove workflow
├── window_about.py          # template metadata dialog
├── config.py                # feature flags and generic identity
├── languages.xml            # localization catalog
├── tests/                   # automated suite and manual macro runner
│   ├── test_*.py            # managers, workflows, regression, smoke tests
│   └── macro/runner.py      # deeper manual Tkinter exercise runner
└── requirements.txt         # pinned Python dependencies
```

---

<a id="architecture-at-a-glance"></a>

## 🏗️ Architecture at a Glance

```text
MainApplication
├── UIManager
├── CanvasController
├── AnnotationManager
├── ClassCatalogManager
├── DatasetUtils
└── Windows
    ├── NewProjectWindow
    ├── SplitWizard
    ├── GridViewerWindow
    ├── DatasetAnalyzerWindow
    └── ClassManagerWindow
```

### Key modules

| Module | Responsibility |
|:---|:---|
| [`main.py`](main.py) | Application entry point and workflow orchestration |
| [`ui.py`](ui.py) | Main toolbar, panels, selectors, and controls |
| [`canvas.py`](canvas.py) | Drawing, selecting, dragging, zooming, and panning |
| [`managers.py`](managers.py) | Annotation persistence, class remapping, and split utilities |
| [`config.py`](config.py) | Feature toggles and application branding defaults |
| [`languages.xml`](languages.xml) | Translation strings used by the UI |

---

<a id="running-tests"></a>

## 🧪 Running Tests

### Full suite

```bash
python3 -m pytest -q tests
```

### Useful paths

| Path | Purpose |
|:---|:---|
| [`tests/test_components_and_workflows.py`](tests/test_components_and_workflows.py) | End-to-end workflow checks |
| [`tests/test_managers.py`](tests/test_managers.py) | Low-level manager logic |
| [`tests/test_system_smoke.py`](tests/test_system_smoke.py) | Import and documentation smoke checks |
| [`tests/test_template_regression.py`](tests/test_template_regression.py) | Generic-template regressions |
| [`tests/macro/runner.py`](tests/macro/runner.py) | Manual GUI stress runner |

---

<a id="reuse-and-customization"></a>

## ⚙️ Reuse and Customization

This repository is especially useful if you want to derive an internal tool without rebuilding everything from scratch.

| Area | How to customize it |
|:---|:---|
| Branding | Adjust `Config.APP_NAME`, description, author, and about dialog content |
| Visible features | Toggle `FEATURE_SHOW_*` flags in [`config.py`](config.py) |
| Segmentation support | Use `FEATURE_ENABLE_POLYGON` to disable polygon mode |
| Localization | Edit [`languages.xml`](languages.xml) and regenerate if needed |
| Default dataset behavior | Extend workflows in [`main.py`](main.py) |
| Persistence | `yolo_editor_config.json` stores language and last opened directory |

---

<a id="keyboard-shortcuts"></a>

## ⌨️ Keyboard Shortcuts

| Action | Shortcut |
|:---|:---:|
| Toggle draw mode | `D` |
| Toggle pan mode | `P` |
| Delete selected annotation | `Delete` |
| Undo | `Ctrl+Z` |
| Zoom | `MouseWheel` |
| Fine zoom | `Ctrl+MouseWheel` |
| Navigate images / move selection | `Arrow Keys` |

---

<a id="license-en"></a>

## 📄 License

This repository is distributed under the **MIT License**. See [`LICENSE.txt`](LICENSE.txt) for the full text.

---

<p align="center"><strong>X-Anotation_YOLO-Experience is a reusable YOLO tooling base: annotate, review, split, analyze, and derive without rebuilding the whole stack.</strong></p>

---

<br />

<!-- ═══════════════════════════════════════════════════════════ -->
<!-- █████████████████   SEÇÃO EM PORTUGUÊS   █████████████████ -->
<!-- ═══════════════════════════════════════════════════════════ -->

<p align="center">
  <kbd><a href="#english">🇬🇧 English</a></kbd>&nbsp;&nbsp;
  <kbd><a href="#portugues">🇧🇷 Português</a></kbd>
</p>

<a id="portugues"></a>

<h2 align="center">🇧🇷 Português</h2>

<p align="center"><strong>Uma base reutilizável em Python + Tkinter para ferramentas de dataset no formato YOLO.</strong></p>

<p align="center"><em>Este projeto foi pensado como repositório-base, e não como produto fechado para um cliente específico.<br />Ele serve como ponto de partida para anotação, revisão, limpeza, divisão e análise de datasets.</em></p>

---

### 📑 Índice

| | Seção | | Seção |
|:---|:---|:---|:---|
| 🎯 | [Por que este template existe?](#por-que-este-template-existe) | 🧩 | [Fluxos principais](#fluxos-principais) |
| ✨ | [Destaques](#destaques) | 📂 | [Tour do repositório](#tour-do-repositorio) |
| 🚀 | [Início rápido](#inicio-rapido) | 🏗️ | [Arquitetura resumida](#arquitetura-resumida) |
| 🔧 | [Instalação manual](#instalacao-manual) | 🧪 | [Executando testes](#executando-testes) |
| 💻 | [Requisitos](#requisitos) | ⚙️ | [Reuso e customização](#reuso-e-customizacao) |
| ⌨️ | [Atalhos de teclado](#atalhos-de-teclado) | 📄 | [Licença](#licenca) |

---

<a id="por-que-este-template-existe"></a>

## 🎯 Por que este template existe?

Este repositório foi feito para servir como **base prática** para times que trabalham com datasets no estilo YOLO e querem um fluxo visual em Python.

<table>
  <tr>
    <td align="center" width="25%">🖍️<br /><strong>ANOTAR</strong><br /><sub>Criar e editar bounding boxes, com suporte opcional a polígonos em fluxos de segmentação.</sub></td>
    <td align="center" width="25%">🧹<br /><strong>LIMPAR</strong><br /><sub>Criar cópias derivadas do dataset filtrando imagens sem label, ignorando labels vazios e aplicando redução aleatória.</sub></td>
    <td align="center" width="25%">📊<br /><strong>ANALISAR</strong><br /><sub>Inspecionar distribuição de classes, equilíbrio de splits, arquivos órfãos e problemas de integridade.</sub></td>
    <td align="center" width="25%">🧱<br /><strong>REUTILIZAR</strong><br /><sub>Ligar ou desligar recursos por configuração e adaptar a base para ferramentas internas específicas.</sub></td>
  </tr>
</table>

- Ele é intencionalmente genérico e reutilizável
- Mantém identidade visual, rótulos e botões configuráveis
- Inclui ferramentas operacionais e suíte automatizada
- Foi estruturado para facilitar a criação de derivados sem perder a espinha dorsal do projeto

---

<a id="destaques"></a>

## ✨ Destaques

| Funcionalidade | Descrição |
|:---|:---|
| 🖼️ Anotação de imagens | Fluxo por bounding box com modo opcional de polígono |
| 🔎 Revisão rápida | Lista de imagens, lista de anotações, zoom por presets, scroll do mouse e pan |
| ✂️ Modal de ferramentas do dataset | Uma única janela cria cópias filtradas ou reduzidas sem alterar o dataset original |
| 🧪 Assistente de split | Divisão `train` / `valid` / `test` opcional com controle visual de percentuais |
| 📈 Analisador | Gráficos, resumos, checagem de órfãos e visões por classe |
| 🌍 Localização | Os textos da UI vêm de `languages.xml` e podem mudar em tempo de execução |
| ⚙️ Flags de recurso | `config.py` pode esconder ou simplificar módulos em builds derivados |
| 🧪 Suíte de testes | Os testes automatizados ficam em `tests/` cobrindo workflows, managers e smoke checks |

---

<a id="inicio-rapido"></a>

## 🚀 Início Rápido

### Rodar a aplicação

<table>
<tr>
<td align="center"><b>🐧 Linux / 🍎 macOS / WSL</b></td>
<td align="center"><b>🪟 Windows PowerShell</b></td>
</tr>
<tr>
<td>

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

</td>
<td>

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

</td>
</tr>
</table>

### Primeiros passos sugeridos

1. Abra um dataset existente ou crie uma estrutura YOLO nova
2. Revise imagens e labels na tela principal
3. Use `Ajustar Dataset` para criar uma cópia derivada com filtro e/ou redução
4. Rode o assistente de split se precisar de `train`, `valid` e `test`
5. Abra o analisador para checagens de distribuição e integridade

---

<a id="instalacao-manual"></a>

## 🔧 Instalação Manual

<details>
<summary>🔽 Expandir configuração manual do ambiente</summary>

### 1. Criar o ambiente virtual

```bash
python -m venv .venv
```

### 2. Ativar o ambiente

```bash
# Linux / macOS / WSL
source .venv/bin/activate

# Windows PowerShell
.venv\Scripts\Activate.ps1

# Windows CMD
.venv\Scripts\activate.bat
```

### 3. Instalar dependências

```bash
pip install -r requirements.txt
```

### 4. Iniciar a aplicação

```bash
python main.py
```

</details>

---

<a id="requisitos"></a>

## 💻 Requisitos

| Item | Requisito |
|:---|:---|
| 🐍 Python | Python 3 |
| 🖥️ GUI | Ambiente capaz de abrir janelas Tkinter |
| 🖼️ Imagem | `Pillow` |
| 📊 Análise | `matplotlib`, `numpy`, `PyYAML` |
| 🌍 Ferramenta de localização | `deep-translator` é usado no fluxo de geração de idiomas |

> As versões exatas estão listadas em [`requirements.txt`](requirements.txt).

---

<a id="fluxos-principais"></a>

## 🧩 Fluxos Principais

### Anotação e revisão

- Navegar pelas imagens do dataset atual
- Inspecionar anotações salvas na lista lateral
- Editar labels com zoom e pan
- Alternar entre box e polígono quando o suporte a polígono estiver ativo

### Ferramentas de cópia do dataset

- Abrir o botão unificado de ferramentas do dataset na barra superior
- Criar uma **cópia derivada** do dataset, sem mutar a origem
- Excluir da cópia imagens sem label
- Excluir opcionalmente imagens com label vazio
- Aplicar opcionalmente redução aleatória por percentual

### Manutenção do dataset

- Criar estruturas YOLO para novos datasets
- Gerenciar classes e manter YAML sincronizado
- Dividir datasets em `train`, `valid` e `test` opcional
- Rodar análise de balanceamento e integridade de arquivos

---

<a id="tour-do-repositorio"></a>

## 📂 Tour do Repositório

```text
.
├── main.py                  # controlador principal da aplicação
├── ui.py                    # composição da interface principal
├── canvas.py                # zoom, pan, desenho e seleção
├── managers.py              # E/S de anotações e utilitários de dataset
├── window_new_project.py    # janela de criação da estrutura YOLO
├── window_split_wizard.py   # fluxo de split train/valid/test
├── visualizador_grid.py     # janela de revisão em grade
├── analisador_dataset.py    # análise do dataset e checagens de integridade
├── window_class_manager.py  # fluxo de renomear/remover classes
├── window_about.py          # diálogo de metadados do template
├── config.py                # flags de recurso e identidade genérica
├── languages.xml            # catálogo de localização
├── tests/                   # suíte automatizada e runner macro manual
│   ├── test_*.py            # managers, workflows, regressões e smoke tests
│   └── macro/runner.py      # runner manual mais profundo para Tkinter
└── requirements.txt         # dependências Python com versão fixa
```

---

<a id="arquitetura-resumida"></a>

## 🏗️ Arquitetura Resumida

```text
MainApplication
├── UIManager
├── CanvasController
├── AnnotationManager
├── ClassCatalogManager
├── DatasetUtils
└── Windows
    ├── NewProjectWindow
    ├── SplitWizard
    ├── GridViewerWindow
    ├── DatasetAnalyzerWindow
    └── ClassManagerWindow
```

### Módulos principais

| Módulo | Responsabilidade |
|:---|:---|
| [`main.py`](main.py) | Entrada da aplicação e orquestração dos fluxos |
| [`ui.py`](ui.py) | Barra superior, painéis, seletores e controles |
| [`canvas.py`](canvas.py) | Desenho, seleção, arraste, zoom e pan |
| [`managers.py`](managers.py) | Persistência de anotação, remapeamento de classes e split |
| [`config.py`](config.py) | Feature flags e branding padrão |
| [`languages.xml`](languages.xml) | Strings de tradução da interface |

---

<a id="executando-testes"></a>

## 🧪 Executando Testes

### Suíte completa

```bash
python3 -m pytest -q tests
```

### Caminhos úteis

| Caminho | Finalidade |
|:---|:---|
| [`tests/test_components_and_workflows.py`](tests/test_components_and_workflows.py) | Checagens de workflow ponta a ponta |
| [`tests/test_managers.py`](tests/test_managers.py) | Lógica dos managers |
| [`tests/test_system_smoke.py`](tests/test_system_smoke.py) | Smoke tests de importação e documentação |
| [`tests/test_template_regression.py`](tests/test_template_regression.py) | Regressões do template genérico |
| [`tests/macro/runner.py`](tests/macro/runner.py) | Runner manual de estresse da GUI |

---

<a id="reuso-e-customizacao"></a>

## ⚙️ Reuso e Customização

Este repositório é especialmente útil para derivar ferramentas internas sem reconstruir tudo do zero.

| Área | Como customizar |
|:---|:---|
| Branding | Ajuste `Config.APP_NAME`, descrição, autor e conteúdo da janela sobre |
| Recursos visíveis | Altere as flags `FEATURE_SHOW_*` em [`config.py`](config.py) |
| Suporte a segmentação | Use `FEATURE_ENABLE_POLYGON` para desligar polígonos |
| Localização | Edite [`languages.xml`](languages.xml) e regenere se necessário |
| Comportamento padrão | Estenda workflows em [`main.py`](main.py) |
| Persistência local | `yolo_editor_config.json` guarda idioma e último diretório aberto |

---

<a id="atalhos-de-teclado"></a>

## ⌨️ Atalhos de Teclado

| Ação | Atalho |
|:---|:---:|
| Alternar modo desenho | `D` |
| Alternar modo pan | `P` |
| Remover anotação selecionada | `Delete` |
| Desfazer | `Ctrl+Z` |
| Zoom | `MouseWheel` |
| Zoom fino | `Ctrl+MouseWheel` |
| Navegar entre imagens / mover seleção | `Setas` |

---

<a id="licenca"></a>

## 📄 Licença

Este repositório é distribuído sob a **MIT License**. Veja [`LICENSE.txt`](LICENSE.txt) para o texto completo.

---

<p align="center"><strong>X-Anotation_YOLO-Experience é uma base reutilizável para ferramentas YOLO: anotar, revisar, dividir, analisar e derivar sem reconstruir toda a stack.</strong></p>
