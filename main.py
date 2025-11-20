import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import ttkbootstrap as tb
from PIL import Image
import os
import json
import yaml
import logging
from typing import List, Tuple, Optional
import logger_config
logger_config.setup_logging()
logger = logging.getLogger(__name__)
from config import Config
from state import AppState
from managers import AnnotationManager
from canvas import CanvasController
from ui import UIManager
from windows import ClassManagerWindow, NewProjectWindow

class MainApplication:

    def __init__(self, root: tb.Window):
        logger.info('Inicializando MainApplication...')
        self.root = root
        self.app_state = AppState()
        self.ann_manager = AnnotationManager()
        self.root.title(Config.APP_NAME)
        self.root.geometry(Config.DEFAULT_GEOMETRY)
        self.root.minsize(*map(int, Config.MIN_GEOMETRY.split('x')))
        self.ui_theme_name = 'darkly'
        self._load_config()
        self.ui = UIManager(root, self)
        self.canvas_controller = CanvasController(self.ui.canvas, self.app_state, self.ui)
        self._bind_events()
        self.ui.update_status_bar('Bem-vindo! Selecione uma pasta ou crie um novo projeto para começar.')
        logger.info('Interface inicializada.')

    def _load_config(self) -> None:
        logger.info('Carregando configurações...')
        try:
            with open(Config.CONFIG_FILE_PATH, 'r') as f:
                config = json.load(f)
            self.app_state.base_directory = config.get('last_directory', '')
            saved_theme = config.get('theme', 'darkly')
            valid_themes = self.root.style.theme_names()
            if saved_theme not in valid_themes:
                logger.warning(f"Tema salvo '{saved_theme}' não é válido para ttkbootstrap. Revertendo para 'darkly'.")
                saved_theme = 'darkly'
            self.ui_theme_name = saved_theme
            self.root.style.theme_use(saved_theme)
            if self.app_state.base_directory and os.path.exists(self.app_state.base_directory):
                if self._verify_dataset_structure(self.app_state.base_directory):
                    logger.info(f'Carregando diretório anterior: {self.app_state.base_directory}')
                    self.root.after(100, self._load_directory_contents)
                else:
                    logger.warning('Diretório anterior não possui estrutura válida.')
                    self.app_state.base_directory = ''
        except (FileNotFoundError, json.JSONDecodeError):
            logger.warning('Arquivo de configuração não encontrado ou inválido. Usando padrões.')

    def save_current_theme(self):
        self._save_config()

    def _save_config(self) -> None:
        config = {'last_directory': self.app_state.base_directory, 'theme': self.ui_theme_name}
        try:
            with open(Config.CONFIG_FILE_PATH, 'w') as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            logger.error(f'Erro ao salvar configuração: {e}')

    def _verify_dataset_structure(self, path: str) -> bool:
        required_dirs = {'train', 'test', 'valid'}
        found_dirs = set()
        if not os.path.isdir(path):
            return False
        for item in os.listdir(path):
            if os.path.isdir(os.path.join(path, item)):
                found_dirs.add(item)
        is_valid = required_dirs.issubset(found_dirs)
        if not is_valid:
            logger.debug(f'Estrutura inválida em {path}. Encontrado: {found_dirs}')
        return is_valid

    def _bind_events(self) -> None:
        self.ui.listbox.bind('<<ListboxSelect>>', self.on_image_select_from_list)
        self.ui.annotation_listbox.bind('<<ListboxSelect>>', self.on_annotation_select_from_list)
        self.ui.canvas.bind('<Configure>', self.on_canvas_resize)
        self.ui.canvas.bind('<ButtonPress-1>', lambda e: self.canvas_controller.on_canvas_press(e, self.process_canvas_update))
        self.ui.canvas.bind('<B1-Motion>', self.canvas_controller.on_canvas_drag)
        self.ui.canvas.bind('<ButtonRelease-1>', lambda e: self.canvas_controller.on_canvas_release(e, self.process_canvas_update))
        self.ui.canvas.bind('<Motion>', self.canvas_controller.on_mouse_hover)
        self.ui.canvas.bind('<MouseWheel>', self.canvas_controller.on_zoom)
        self.ui.canvas.bind('<Button-4>', self.canvas_controller.on_zoom)
        self.ui.canvas.bind('<Button-5>', self.canvas_controller.on_zoom)
        self.ui.canvas.bind('<ButtonPress-2>', self.canvas_controller.on_pan_start)
        self.ui.canvas.bind('<ButtonPress-3>', self.canvas_controller.on_pan_start)
        self.ui.canvas.bind('<B2-Motion>', self.canvas_controller.on_pan_move)
        self.ui.canvas.bind('<B3-Motion>', self.canvas_controller.on_pan_move)
        self.ui.canvas.bind('<ButtonRelease-2>', self.canvas_controller.on_pan_end)
        self.ui.canvas.bind('<ButtonRelease-3>', self.canvas_controller.on_pan_end)
        self.root.bind('<Left>', lambda e: self.show_previous_image())
        self.root.bind('<Right>', lambda e: self.show_next_image())
        self.root.bind('<Delete>', self.delete_current_item)
        self.root.bind('<b>', self.toggle_drawing_mode_event)
        self.root.bind('<w>', self.select_prev_annotation)
        self.root.bind('<s>', self.select_next_annotation)
        self.root.bind('<Escape>', self.deselect_all)
        self.root.protocol('WM_DELETE_WINDOW', self.on_close)

    def open_new_project_wizard(self) -> None:
        NewProjectWindow(self.root, self.load_created_project)

    def load_created_project(self, path: str) -> None:
        logger.info(f'Carregando novo projeto criado: {path}')
        if not os.path.exists(path):
            logger.error('Caminho do projeto não existe.')
            return
        if self._verify_dataset_structure(path):
            self.app_state.base_directory = path
            self._load_directory_contents()
            self._save_config()
            messagebox.showinfo('Projeto Carregado', "Dataset criado com sucesso.\n\nAgora adicione suas imagens nas pastas 'train/images', 'valid/images', etc.", parent=self.root)
        else:
            logger.error('Estrutura do projeto inválida após criação.')
            messagebox.showerror('Erro', 'A estrutura do projeto criado parece inválida.', parent=self.root)

    def select_directory(self) -> None:
        path = filedialog.askdirectory(title='Selecione a pasta raiz do seu dataset (deve conter train/test/valid)', parent=self.root)
        if not path:
            return
        if not self._verify_dataset_structure(path):
            messagebox.showerror('Estrutura Inválida', "A pasta selecionada deve conter os subdiretórios 'train', 'test' e 'valid'.\n\nO programa não carregará esta pasta.", parent=self.root)
            return
        self.app_state.base_directory = path
        self._load_directory_contents()
        self._save_config()

    def _load_directory_contents(self) -> None:
        logger.info('Lendo conteúdo do diretório...')
        self.ui.dir_label.config(text=f'Pasta: {os.path.basename(self.app_state.base_directory)}')
        try:
            self._load_class_names()
        except Exception as e:
            logger.error(f'Erro ao carregar classes: {e}', exc_info=True)
        self.app_state.image_paths = []
        valid_extensions = ('.png', '.jpg', '.jpeg', '.bmp', '.gif')
        for root_dir, _, files in os.walk(self.app_state.base_directory):
            if os.path.basename(root_dir).startswith(('.', '_')):
                continue
            for file in sorted(files):
                if file.lower().endswith(valid_extensions):
                    self.app_state.image_paths.append(os.path.join(root_dir, file))
        logger.info(f'Imagens encontradas: {len(self.app_state.image_paths)}')
        self.ui.refresh_image_list()
        if self.app_state.image_paths:
            self.show_image_at_index(0)
            self.ui.add_box_check.config(state='normal')
            self.ui.update_status_bar(f'{len(self.app_state.image_paths)} imagens carregadas. Use as setas para navegar.')
        else:
            logger.info('Nenhuma imagem encontrada no diretório.')
            self.app_state.current_pil_image = None
            self.app_state.current_image_index = -1
            self.app_state.annotations = []
            self.canvas_controller.display_image()
            self.ui.sync_ui_to_state()
            messagebox.showwarning('Nenhuma Imagem', f"Nenhuma imagem encontrada em '{self.app_state.base_directory}'.", parent=self.root)
            self.ui.add_box_check.config(state='disabled')

    def _load_class_names(self) -> None:
        self.app_state.class_names = []
        logger.info('Procurando definições de classes...')
        for yaml_name in ('data.yaml', 'dataset.yaml'):
            yaml_path = os.path.join(self.app_state.base_directory, yaml_name)
            if os.path.exists(yaml_path):
                try:
                    with open(yaml_path, 'r', encoding='utf-8') as f:
                        data = yaml.safe_load(f)
                    if 'names' in data and isinstance(data['names'], list):
                        self.app_state.class_names = data['names']
                        self.ui.update_class_selector()
                        logger.info(f'Classes carregadas de {yaml_name}: {self.app_state.class_names}')
                        return
                except Exception as e:
                    logger.error(f'Erro ao ler {yaml_name}: {e}')
                    messagebox.showerror('Erro de Leitura', f"Não foi possível ler '{yaml_name}':\n{e}", parent=self.root)
        classes_path = os.path.join(self.app_state.base_directory, 'classes.txt')
        if not os.path.exists(classes_path):
            parent_dir_classes = os.path.join(os.path.dirname(self.app_state.base_directory), 'classes.txt')
            if os.path.exists(parent_dir_classes):
                classes_path = parent_dir_classes
            else:
                logger.warning('Nenhum arquivo de classes encontrado.')
                self.ui.update_class_selector()
                return
        try:
            with open(classes_path, 'r', encoding='utf-8') as f:
                self.app_state.class_names = [line.strip() for line in f if line.strip()]
            logger.info(f'Classes carregadas de classes.txt: {self.app_state.class_names}')
        except Exception as e:
            logger.error(f'Erro ao ler classes.txt: {e}')
            messagebox.showerror('Erro de Leitura', f"Não foi possível ler 'classes.txt':\n{e}", parent=self.root)
        self.ui.update_class_selector()

    def show_image_at_index(self, index: int) -> None:
        if not self.app_state.image_paths:
            return
        if not 0 <= index < len(self.app_state.image_paths):
            logger.warning(f'Tentativa de acessar índice inválido: {index}')
            return
        self.deselect_all()
        self.app_state.current_image_index = index
        image_path = self.app_state.get_current_image_path()
        if not image_path:
            return
        logger.debug(f'Abrindo imagem: {image_path}')
        try:
            image = Image.open(image_path)
            if image.mode == 'P':
                image = image.convert('RGBA')
            else:
                image = image.convert('RGB')
            self.app_state.current_pil_image = image
            self.app_state.original_image_size = image.size
        except Exception as e:
            logger.error(f'Erro ao abrir imagem {image_path}: {e}')
            messagebox.showerror('Erro de Imagem', f'Não foi possível carregar a imagem:\n{image_path}\n\nErro: {e}', parent=self.root)
            self.app_state.current_pil_image = None
            return
        label_path = self.ann_manager.get_label_path(image_path)
        self.app_state.annotations, error = self.ann_manager.load_annotations(label_path, self.app_state.original_image_size)
        if error:
            self._handle_malformed_annotation_file(label_path, error)
        self.canvas_controller.reset_view()
        self.canvas_controller.display_image()
        self.ui.sync_ui_to_state()

    def process_canvas_update(self, **kwargs) -> None:
        if kwargs.get('select_annotation_idx') is not None:
            self._select_annotation(kwargs['select_annotation_idx'])
        if kwargs.get('deselect_all'):
            self.deselect_all()
        if kwargs.get('toggle_draw_mode'):
            self.toggle_drawing_mode()
        if kwargs.get('add_new_box'):
            self._add_new_box_at(kwargs['add_new_box'])
        if kwargs.get('save_and_refresh'):
            self._save_and_refresh(new_selection=self.app_state.selected_annotation_index)

    def _select_annotation(self, index: int) -> None:
        if not 0 <= index < len(self.app_state.annotations):
            return
        self.deselect_all()
        self.app_state.selected_annotation_index = index
        self.ui.sync_ui_to_state()
        self.canvas_controller.display_image()

    def deselect_all(self, event: Optional[tk.Event]=None) -> str:
        if self.app_state.selected_annotation_index is not None:
            self.app_state.selected_annotation_index = None
            self.ui.sync_ui_to_state()
            self.canvas_controller.display_image()
        return 'break'

    def _save_and_refresh(self, new_selection: Optional[int]=None) -> None:
        if self.app_state.current_image_index == -1:
            return
        image_path = self.app_state.get_current_image_path()
        if not image_path:
            return
        label_path = self.ann_manager.get_label_path(image_path)
        if not self.ann_manager.save_annotations(label_path, self.app_state.annotations):
            messagebox.showerror('Erro', 'Falha ao salvar o arquivo de anotação.', parent=self.root)
            return
        self.ui.refresh_annotation_list()
        if new_selection is not None and new_selection < len(self.app_state.annotations):
            self._select_annotation(new_selection)
        else:
            self.deselect_all()
        self.canvas_controller.display_image()

    def _add_new_box_at(self, box_coords: Tuple[float, float, float, float]) -> None:
        class_id = self._ask_for_class_id()
        if class_id is None:
            return
        yolo_string = self.ann_manager.convert_to_yolo_format(class_id, box_coords, self.app_state.original_image_size)
        x1, y1, x2, y2 = box_coords
        rect_orig = [min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2)]
        self.app_state.annotations.append({'yolo_string': yolo_string, 'rect_orig': rect_orig, 'class_id': class_id})
        self._save_and_refresh(new_selection=len(self.app_state.annotations) - 1)
        self.ui.update_status_bar(f'Nova caixa adicionada e salva.')

    def change_annotation_class(self) -> None:
        if self.app_state.selected_annotation_index is None or not self.app_state.class_names:
            return
        selected_class_name = self.ui.class_id_var.get()
        if not selected_class_name:
            return
        try:
            new_id = self.app_state.class_names.index(selected_class_name)
        except ValueError:
            return
        idx = self.app_state.selected_annotation_index
        ann = self.app_state.annotations[idx]
        parts = ann['yolo_string'].split()
        parts[0] = str(new_id)
        ann['class_id'] = new_id
        ann['yolo_string'] = ' '.join(parts)
        self._save_and_refresh(new_selection=idx)
        self.ui.update_status_bar(f"Classe alterada para '{selected_class_name}' e salva.")

    def delete_current_item(self, event: Optional[tk.Event]=None) -> None:
        if self.app_state.current_image_index == -1:
            return
        if self.app_state.selected_annotation_index is not None:
            if messagebox.askyesno('Confirmar Exclusão', 'Deletar a anotação selecionada?', parent=self.root):
                idx_to_del = self.app_state.selected_annotation_index
                self.app_state.annotations.pop(idx_to_del)
                self.deselect_all()
                self._save_and_refresh()
            return

    def on_image_select_from_list(self, event: tk.Event) -> None:
        selections = self.ui.listbox.curselection()
        if selections:
            self._save_and_refresh()
            self.show_image_at_index(selections[0])

    def on_annotation_select_from_list(self, event: tk.Event) -> None:
        selections = self.ui.annotation_listbox.curselection()
        if selections:
            self._select_annotation(selections[0])

    def on_canvas_resize(self, event: tk.Event) -> None:
        if self.app_state.current_image_index != -1:
            self.canvas_controller.display_image()

    def show_previous_image(self) -> None:
        if self.app_state.current_image_index > 0:
            self._save_and_refresh()
            self.show_image_at_index(self.app_state.current_image_index - 1)

    def show_next_image(self) -> None:
        if self.app_state.current_image_index < len(self.app_state.image_paths) - 1:
            self._save_and_refresh()
            self.show_image_at_index(self.app_state.current_image_index + 1)

    def _select_adj_annotation(self, direction: int) -> None:
        if not self.ui.annotation_listbox.size():
            return
        current_idx = self.app_state.selected_annotation_index if self.app_state.selected_annotation_index is not None else -1
        new_idx = max(0, min(self.ui.annotation_listbox.size() - 1, current_idx + direction))
        self._select_annotation(new_idx)

    def select_prev_annotation(self, event: Optional[tk.Event]=None) -> None:
        self._select_adj_annotation(-1)

    def select_next_annotation(self, event: Optional[tk.Event]=None) -> None:
        self._select_adj_annotation(1)

    def toggle_drawing_mode(self) -> None:
        self.deselect_all()
        self.app_state.is_drawing = self.ui.drawing_mode_var.get()
        status = 'Modo de Desenho: Clique e arraste na imagem para criar uma caixa.' if self.app_state.is_drawing else 'Modo de Navegação: Clique numa caixa para editar ou mover.'
        self.ui.update_status_bar(status)

    def toggle_drawing_mode_event(self, event: Optional[tk.Event]=None) -> None:
        if self.ui.add_box_check['state'] == 'normal':
            self.ui.drawing_mode_var.set(not self.ui.drawing_mode_var.get())
            self.toggle_drawing_mode()

    def _ask_for_class_id(self) -> Optional[int]:
        if not self.app_state.class_names:
            return simpledialog.askinteger('ID da Classe', 'Digite o ID para a nova caixa:', parent=self.root, minvalue=0)
        dialog = tk.Toplevel(self.root)
        dialog.title('Selecionar Classe')
        dialog.geometry('300x120')
        dialog.resizable(False, False)
        ttk.Label(dialog, text='Selecione a classe para a nova caixa:').pack(pady=10, padx=10)
        class_var = tk.StringVar()
        combo = ttk.Combobox(dialog, textvariable=class_var, values=self.app_state.class_names, state='readonly')
        combo.pack(padx=10, fill=tk.X, expand=True)
        if self.app_state.class_names:
            combo.set(self.app_state.class_names[0])
        result = tk.IntVar(value=-1)

        def on_ok() -> None:
            if class_var.get():
                try:
                    result.set(self.app_state.class_names.index(class_var.get()))
                except ValueError:
                    result.set(-1)
            dialog.destroy()
        ttk.Button(dialog, text='OK', command=on_ok).pack(pady=10)
        dialog.transient(self.root)
        dialog.grab_set()
        self.root.wait_window(dialog)
        return result.get() if result.get() != -1 else None

    def _handle_malformed_annotation_file(self, label_path: str, error: Exception) -> None:
        msg = f'O arquivo de anotação está corrompido ou mal formatado:\n{os.path.basename(label_path)}\n\nErro: {error}\n\nDeseja deletar o arquivo corrompido?'
        if messagebox.askyesno('Arquivo Corrompido', msg, icon='error', parent=self.root):
            try:
                os.remove(label_path)
                logger.info(f'Arquivo corrompido removido: {label_path}')
            except OSError as e:
                logger.error(f'Falha ao remover arquivo: {e}')
                messagebox.showerror('Erro', f'Não foi possível deletar o arquivo:\n{e}', parent=self.root)

    def open_class_manager(self) -> None:
        if not self.app_state.base_directory:
            messagebox.showwarning('Aviso', 'Selecione uma pasta de projeto primeiro.', parent=self.root)
            return
        manager = ClassManagerWindow(self.root, self.app_state.class_names, self._on_classes_updated)
        self.root.wait_window(manager)

    def _on_classes_updated(self, new_class_list: List[str]) -> None:
        self.app_state.class_names = new_class_list
        classes_path = os.path.join(self.app_state.base_directory, 'classes.txt')
        try:
            with open(classes_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(new_class_list))
            self.ui.update_class_selector()
            if self.app_state.current_image_index != -1:
                self.show_image_at_index(self.app_state.current_image_index)
            self.ui.update_status_bar('Lista de classes atualizada com sucesso.')
        except Exception as e:
            logger.error(f'Erro ao atualizar classes.txt: {e}')
            messagebox.showerror('Erro de Escrita', f"Não foi possível salvar 'classes.txt':\n{e}", parent=self.root)

    def on_close(self) -> None:
        self._save_and_refresh()
        self._save_config()
        logger.info('Encerrando aplicação.')
        self.root.destroy()
if __name__ == '__main__':
    root = tb.Window(themename='darkly')
    app = MainApplication(root)
    root.mainloop()