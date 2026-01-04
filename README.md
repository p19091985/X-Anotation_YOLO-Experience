# 🎯 X-Anotation YOLO Experience

Um editor e visualizador de anotações moderno para datasets YOLO, construído em Python com **Tkinter** e **ttkbootstrap**.

Este projeto oferece uma interface gráfica amigável para criar, editar e visualizar *Bounding Boxes* em imagens para treinamento de modelos de Visão Computacional (YOLOv5, v8, v11, etc).

---

## ✨ Funcionalidades Principais

* **🎨 Interface Moderna:** Suporte a múltiplos temas (Darkly, Cosmo, Flatly, etc) via `ttkbootstrap`.
* **📁 Gerenciamento de Projetos:**
    * Crie novos datasets do zero com estrutura automática de pastas (`train`, `valid`, `test`).
    * Carregue datasets existentes.
* **✏️ Edição Completa:**
    * Desenhar novas caixas (Arrastar e soltar).
    * Redimensionar e mover caixas existentes.
    * Alterar a classe de uma anotação.
    * Excluir anotações.
* **🔍 Navegação Avançada:**
    * **Zoom:** Zoom in/out com a roda do mouse.
    * **Pan:** Arraste com o botão direito ou do meio para mover a imagem.
* **⚙️ Gerenciador de Classes:** Adicione, renomeie ou remova classes diretamente na interface (atualiza o `classes.txt`).
* **📝 Logs:** Sistema de log detalhado (`application.log`) para debug e rastreamento de erros.

---

## 🛠️ Instalação

Certifique-se de ter o **Python 3.10+** instalado.
````
1.  **Clone o repositório:**
    ```bash
    git clone [https://github.com/SeuUsuario/X-Anotation_YOLO-Experience.git](https://github.com/SeuUsuario/X-Anotation_YOLO-Experience.git)
    cd X-Anotation_YOLO-Experience
    ```

2.  **Crie um ambiente virtual (Recomendado):**
    ```bash
    # Linux/Mac
    python3 -m venv .venv
    source .venv/bin/activate

    # Windows
    python -m venv .venv
    .venv\Scripts\activate
    ```

3.  **Instale as dependências:**
    ```bash
    pip install pillow pyyaml ttkbootstrap
    ```

---

## 🚀 Como Usar

Execute o arquivo principal para iniciar a aplicação:

```bash
python main.py
````

### Fluxo de Trabalho

1.  **Novo Projeto:** Clique em `✨ Novo Dataset`, escolha o nome, o local e defina as classes iniciais.
2.  **Carregar Imagens:** Coloque suas imagens (`.jpg`, `.png`) dentro da pasta `train/images` (ou `valid/images`) que foi criada.
3.  **Anotar:**
      * Pressione `B` para ativar o modo de desenho.
      * Clique e arraste na imagem para criar uma caixa.
      * Selecione a classe no menu lateral.
4.  **Navegar:** Use as setas do teclado ou os botões na interface para trocar de imagem. **O salvamento é automático** ao mudar de imagem ou fechar o app.

-----

## ⌨️ Atalhos e Controles

| Ação | Comando / Tecla |
| :--- | :--- |
| **Zoom In/Out** | `Roda do Mouse` |
| **Mover Imagem (Pan)** | `Botão Direito` ou `Botão do Meio` (Segurar e arrastar) |
| **Modo Desenho** | Tecla `B` (Alterna entre Navegação/Desenho) |
| **Deletar Caixa** | Tecla `Delete` (Na caixa selecionada) |
| **Próxima Imagem** | `Seta Direita` |
| **Imagem Anterior** | `Seta Esquerda` |
| **Próxima Anotação** | Tecla `S` |
| **Anotação Anterior** | Tecla `W` |
| **Cancelar Seleção** | `Esc` |

-----

## 📂 Estrutura do Dataset

O software trabalha com a estrutura padrão YOLO:

```text
NomeDoProjeto/
├── classes.txt       # Lista de nomes das classes
├── data.yaml         # Configuração do dataset
├── train/
│   ├── images/       # Coloque suas imagens aqui
│   └── labels/       # Onde os .txt das anotações serão salvos
├── valid/
│   ├── images/
│   └── labels/
└── test/
    ├── images/
    └── labels/
```

-----

## 🔧 Estrutura do Código

O projeto foi modularizado seguindo boas práticas (MVC):

  * `main.py`: Ponto de entrada e controle principal.
  * `ui.py`: Construção da interface gráfica.
  * `canvas.py`: Lógica de desenho, zoom e manipulação da imagem.
  * `managers.py`: Leitura e escrita de arquivos YOLO e anotações.
  * `state.py`: Gerenciamento do estado da aplicação (dados).
  * `windows.py`: Janelas secundárias (Novo Projeto, Gerenciador de Classes, Preview).
  * `config.py`: Cores, constantes e configurações.
  * `utils.py`: Funções utilitárias.
  * `logger_config.py`: Configuração do sistema de logs.

-----

## 📄 Licença

Este projeto é distribuído sob a licença MIT. Veja o arquivo LICENSE para mais detalhes.

##  Arquitetura

![Diagrama](Untitled Graph.svg)
```
```