import tkinter as tk
from tkinter import ttk, simpledialog, messagebox, Listbox, filedialog
import os
import yaml
import logging
from PIL import Image, ImageTk
from typing import List, TYPE_CHECKING
if TYPE_CHECKING:
    from main import MainApplication
logger = logging.getLogger(__name__)

class ClassManagerWindow(tk.Toplevel):

    def __init__(self, master, class_list: List[str], callback: callable):
        super().__init__(master)
        self.title('Gerenciador de Classes')
        self.geometry('400x450')
        self.transient(master)
        self.grab_set()
        self.class_list = class_list[:]
        self.callback = callback
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        self.listbox = Listbox(list_frame)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox.config(yscrollcommand=scrollbar.set)
        for item in self.class_list:
            self.listbox.insert(tk.END, item)
        self.listbox.bind('<Double-1>', self.edit_item)
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=5)
        ttk.Button(button_frame, text='Adicionar', command=self.add_item).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        ttk.Button(button_frame, text='Renomear', command=self.edit_item).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        ttk.Button(button_frame, text='Excluir', command=self.delete_item).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        action_frame = ttk.Frame(main_frame)
        action_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=(10, 0))
        ttk.Button(action_frame, text='Salvar e Fechar', command=self.save_and_close).pack(side=tk.RIGHT)
        ttk.Button(action_frame, text='Cancelar', command=self.destroy).pack(side=tk.RIGHT, padx=10)

    def add_item(self) -> None:
        new_class = simpledialog.askstring('Nova Classe', 'Nome da nova classe:', parent=self)
        if new_class and new_class.strip() and (new_class not in self.class_list):
            self.class_list.append(new_class)
            self.listbox.insert(tk.END, new_class)

    def edit_item(self, event=None) -> None:
        selected = self.listbox.curselection()
        if not selected:
            return
        idx = selected[0]
        old_name = self.listbox.get(idx)
        new_name = simpledialog.askstring('Renomear Classe', f"Novo nome para '{old_name}':", initialvalue=old_name, parent=self)
        if new_name and new_name.strip() and (new_name != old_name) and (new_name not in self.class_list):
            self.class_list[idx] = new_name
            self.listbox.delete(idx)
            self.listbox.insert(idx, new_name)
            self.listbox.selection_set(idx)

    def delete_item(self) -> None:
        selected = self.listbox.curselection()
        if not selected:
            return
        idx = selected[0]
        if messagebox.askyesno('Confirmar', f"Tem certeza que deseja excluir '{self.listbox.get(idx)}'?", parent=self):
            self.class_list.pop(idx)
            self.listbox.delete(idx)

    def save_and_close(self) -> None:
        self.callback(self.class_list)
        self.destroy()

class PreviewWindow(tk.Toplevel):

    def __init__(self, master, app_instance: 'MainApplication'):
        super().__init__(master)
        self.app = app_instance
        self.title('Prévia das Próximas Imagens')
        self.geometry('650x250')
        self.minsize(500, 200)
        self.photo_images = []
        main_frame = ttk.Frame(self, padding='10')
        main_frame.pack(fill=tk.BOTH, expand=True)
        self.image_labels = []
        self.filename_labels = []
        for i in range(3):
            frame = ttk.Frame(main_frame)
            frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
            img_label = ttk.Label(frame, background='gray30', anchor=tk.CENTER)
            img_label.pack(fill=tk.BOTH, expand=True)
            filename_label = ttk.Label(frame, text='', anchor=tk.CENTER, wraplength=180)
            filename_label.pack(fill=tk.X, pady=(5, 0))
            self.image_labels.append(img_label)
            self.filename_labels.append(filename_label)
        self.protocol('WM_DELETE_WINDOW', self.on_close)

    def update_previews(self) -> None:
        self.photo_images.clear()
        current_index = self.app.app_state.current_image_index
        all_paths = self.app.app_state.image_paths
        for i in range(3):
            preview_index = current_index + 1 + i
            if preview_index < len(all_paths):
                try:
                    path = all_paths[preview_index]
                    image = Image.open(path)
                    image.thumbnail((190, 190), Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(image)
                    self.photo_images.append(photo)
                    self.image_labels[i].config(image=photo)
                    self.filename_labels[i].config(text=os.path.basename(path))
                except Exception as e:
                    logger.error(f'Erro ao carregar preview: {e}')
                    self.image_labels[i].config(image='', text='Erro ao carregar')
            else:
                self.image_labels[i].config(image='')
                self.filename_labels[i].config(text='Fim da lista')

    def on_close(self) -> None:
        self.app.ui.preview_window = None
        self.destroy()

class NewProjectWindow(tk.Toplevel):

    def __init__(self, master, callback_load_project: callable):
        super().__init__(master)
        self.title('Criar Novo Dataset YOLO')
        self.geometry('500x550')
        self.transient(master)
        self.grab_set()
        self.callback_load_project = callback_load_project
        self.base_path = ''
        self.classes = []
        logger.info('Janela de Novo Projeto aberta.')
        self._create_ui()

    def _create_ui(self):
        main_frame = ttk.Frame(self, padding=15)
        main_frame.pack(fill=tk.BOTH, expand=True)
        info_frame = ttk.LabelFrame(main_frame, text='Configuração do Projeto', padding=10)
        info_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(info_frame, text='Nome do Projeto:').grid(row=0, column=0, sticky='w', pady=5)
        self.entry_name = ttk.Entry(info_frame)
        self.entry_name.grid(row=0, column=1, sticky='ew', padx=5)
        ttk.Label(info_frame, text='Localização:').grid(row=1, column=0, sticky='w', pady=5)
        self.entry_path = ttk.Entry(info_frame, state='readonly')
        self.entry_path.grid(row=1, column=1, sticky='ew', padx=5)
        btn_browse = ttk.Button(info_frame, text='...', width=3, command=self.browse_folder)
        btn_browse.grid(row=1, column=2)
        info_frame.columnconfigure(1, weight=1)
        class_frame = ttk.LabelFrame(main_frame, text='Classes do Dataset', padding=10)
        class_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        input_frame = ttk.Frame(class_frame)
        input_frame.pack(fill=tk.X, pady=(0, 5))
        self.entry_class = ttk.Entry(input_frame)
        self.entry_class.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.entry_class.bind('<Return>', lambda e: self.add_class())
        ttk.Button(input_frame, text='+ Adicionar', command=self.add_class).pack(side=tk.LEFT)
        list_frame = ttk.Frame(class_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        self.listbox_classes = Listbox(list_frame, height=10)
        self.listbox_classes.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.listbox_classes.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox_classes.config(yscrollcommand=scrollbar.set)
        btn_remove_class = ttk.Button(class_frame, text='Remover Selecionada', command=self.remove_class)
        btn_remove_class.pack(anchor='e', pady=5)
        ttk.Button(main_frame, text='✅ CRIAR E ABRIR PROJETO', command=self.create_structure, style='Accent.TButton').pack(fill=tk.X, pady=10)

    def browse_folder(self):
        path = filedialog.askdirectory(title='Selecione a pasta onde o projeto será criado', parent=self)
        if path:
            self.entry_path.config(state='normal')
            self.entry_path.delete(0, tk.END)
            self.entry_path.insert(0, path)
            self.entry_path.config(state='readonly')
            self.base_path = path
            logger.debug(f'Pasta base selecionada: {path}')

    def add_class(self):
        name = self.entry_class.get().strip()
        if name and name not in self.classes:
            self.classes.append(name)
            self.listbox_classes.insert(tk.END, name)
            self.entry_class.delete(0, tk.END)
            logger.debug(f'Classe adicionada: {name}')

    def remove_class(self):
        selection = self.listbox_classes.curselection()
        if selection:
            idx = selection[0]
            removed = self.classes.pop(idx)
            self.listbox_classes.delete(idx)
            logger.debug(f'Classe removida: {removed}')

    def create_structure(self):
        project_name = self.entry_name.get().strip()
        logger.info(f'Iniciando criação do projeto: {project_name}')
        if not project_name or not self.base_path:
            messagebox.showwarning('Atenção', 'Preencha o nome do projeto e selecione um local.', parent=self)
            return
        if not self.classes:
            if not messagebox.askyesno('Sem Classes', 'Você não definiu nenhuma classe. Deseja criar o projeto mesmo assim?', parent=self):
                return
        full_path = os.path.join(self.base_path, project_name)
        if os.path.exists(full_path):
            messagebox.showerror('Erro', 'Já existe uma pasta com esse nome no local selecionado.', parent=self)
            return
        try:
            subdirs = ['train/images', 'train/labels', 'valid/images', 'valid/labels', 'test/images', 'test/labels']
            logger.info(f'Criando diretórios em: {full_path}')
            for sub in subdirs:
                p = os.path.join(full_path, sub)
                os.makedirs(p, exist_ok=True)
                logger.debug(f'Dir criado: {p}')
            classes_txt_path = os.path.join(full_path, 'classes.txt')
            with open(classes_txt_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(self.classes))
            logger.info(f'Arquivo classes.txt criado em {classes_txt_path}')
            data_yaml_path = os.path.join(full_path, 'data.yaml')
            data_yaml = {'train': os.path.join(full_path, 'train/images'), 'val': os.path.join(full_path, 'valid/images'), 'test': os.path.join(full_path, 'test/images'), 'nc': len(self.classes), 'names': self.classes}
            with open(data_yaml_path, 'w', encoding='utf-8') as f:
                yaml.dump(data_yaml, f, allow_unicode=True)
            logger.info(f'Arquivo data.yaml criado em {data_yaml_path}')
            messagebox.showinfo('Sucesso', f"Projeto '{project_name}' criado com sucesso!", parent=self)
            logger.info('Chamando callback de carregamento...')
            self.callback_load_project(full_path)
            self.destroy()
        except Exception as e:
            logger.error('Falha crítica ao criar estrutura do projeto', exc_info=True)
            messagebox.showerror('Erro Crítico', f"Falha ao criar diretórios:\n{e}\n\nConsulte 'application.log' para detalhes.", parent=self)