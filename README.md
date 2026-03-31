# Marinho

Template-base em Python + Tkinter para criar ferramentas de anotacao, revisao e organizacao de datasets YOLO.

## Visao Geral

Este repositorio foi mantido como uma base reutilizavel. Ele nao representa um cliente, empresa ou fluxo institucional especifico.

O template oferece:

- anotacao por bounding box e, opcionalmente, por poligono;
- navegacao entre imagens com salvamento continuo;
- zoom por scroll, zoom predefinido por combobox e modo pan com arraste;
- scrollbars dinamicas no canvas para imagens ampliadas;
- criacao de estrutura padrao YOLO com `train`, `valid`, `test`, `classes.txt` e `data.yaml`;
- atualizacao sincronizada de `classes.txt` e metadados YAML ao editar classes;
- gerenciamento de classes com renomeacao livre e bloqueio de exclusao quando a classe ja esta em uso em alguma imagem;
- visualizador em grade para revisao rapida do dataset;
- assistente de split com suporte opcional a conjunto de teste;
- analisador de dataset com estatisticas e verificacoes de integridade;
- interface multi-idioma baseada em `languages.xml`;
- flags em `config.py` para esconder recursos ou simplificar derivados.

## Estrutura

```text
.
├── main.py                  # controlador principal da aplicacao
├── ui.py                    # composicao da interface principal
├── canvas.py                # zoom, pan, desenho e selecao
├── managers.py              # E/S de anotacoes e utilitarios de dataset
├── window_new_project.py    # criacao da estrutura base YOLO
├── teste/                   # suite automatizada e macro runner manual
│   ├── test_*.py            # cobrindo managers, workflows e smoke tests
│   └── macro/runner.py      # varredura manual profunda da interface
├── window_split_wizard.py   # configuracao visual de split
├── visualizador_grid.py     # revisao em grade
├── analisador_dataset.py    # analise estatistica e integridade
├── window_about.py          # metadados genericos do template
├── config.py                # identidade generica e flags reutilizaveis
└── languages.xml            # catalogo de localizacao
```

## Como Executar

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

No Windows:

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

## Testes

Execute toda a suite automatizada com:

```bash
python3 -m pytest -q teste
```

O projeto tambem inclui um runner manual em `teste/macro/runner.py` para exercicios profundos da interface Tkinter quando houver ambiente grafico disponivel.

## Pontos de Reutilizacao

- Ajuste `Config.APP_NAME`, `Config.APP_DESCRIPTION` e as flags em `config.py`.
- Use `FEATURE_ENABLE_POLYGON` para desligar segmentacao em derivados mais simples.
- Use as flags `FEATURE_SHOW_*` para esconder botoes e paines que nao fizerem sentido no sistema derivado.
- O arquivo `yolo_editor_config.json` guarda idioma e ultimo diretorio aberto.
- O `data.yaml` gerado usa caminhos relativos quando possivel, favorecendo portabilidade do projeto.

## Atalhos Principais

- `D`: alterna o modo de desenho
- `P`: alterna o modo pan
- `Delete`: remove a anotacao selecionada
- `Ctrl+Z`: desfaz a ultima alteracao
- `MouseWheel`: zoom
- `Ctrl+MouseWheel`: zoom fino
- `Setas`: navegam entre imagens ou movem a anotacao selecionada

## English

`Marinho` is a reusable Tkinter-based YOLO template for annotation, review, class management, dataset splitting and dataset analysis.

Key improvements already folded into the base:

- configurable feature flags in `config.py`;
- synchronized zoom controls plus drag-pan mode;
- dynamic scrollbars for zoomed images;
- relative-path `data.yaml` generation;
- safe class management with YAML and label remapping;
- optional `test` split support;
- automatic YAML class metadata refresh;
- automated coverage organized under `teste/`;
- cleaner, generic about metadata and reusable documentation.
