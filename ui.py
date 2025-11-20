import tkinter as tk
from tkinter import ttk, messagebox
import ttkbootstrap as tb
import os
from typing import TYPE_CHECKING
from config import Config
from windows import PreviewWindow
if TYPE_CHECKING:
    from main import MainApplication

class UIManager:

    def __init__(self, root: tk.Tk, app: 'MainApplication'):
        self.root = root
        self.app = app
        self.app_state = app.app_state
        self.drawing_mode_var = tk.BooleanVar(value=False)
        self.class_id_var = tk.StringVar()
        self.preview_window = None
        self.current_theme = tk.StringVar(value=self.app.ui_theme_name)
        self._create_widgets()

    def _create_widgets(self) -> None:
        top_frame = ttk.Frame(self.root, padding=(10, 10, 10, 0))
        top_frame.pack(fill=tk.X)
        btn_new_proj = ttk.Button(top_frame, text='✨ Novo Dataset', command=self.app.open_new_project_wizard)
        btn_new_proj.pack(side=tk.LEFT, padx=(0, 5))
        btn_select_dir = ttk.Button(top_frame, text='📂 Abrir Pasta', command=self.app.select_directory)
        btn_select_dir.pack(side=tk.LEFT, padx=(0, 5))
        btn_preview = ttk.Button(top_frame, text='👁️ Prévia', command=self.toggle_preview_window)
        btn_preview.pack(side=tk.LEFT, padx=5)
        self.dir_label = ttk.Label(top_frame, text='Nenhuma pasta selecionada', style='TLabel')
        self.dir_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)
        ttk.Label(top_frame, text='Tema:').pack(side=tk.RIGHT, padx=(5, 0))
        available_themes = self.root.style.theme_names()
        self.theme_combo = ttk.Combobox(top_frame, values=available_themes, textvariable=self.current_theme, state='readonly', width=10)
        self.theme_combo.pack(side=tk.RIGHT, padx=5)
        self.theme_combo.bind('<<ComboboxSelected>>', self.change_theme)
        content_frame = ttk.Frame(self.root, padding=(10, 10, 10, 0))
        content_frame.pack(fill=tk.BOTH, expand=True)
        content_frame.grid_columnconfigure(1, weight=1)
        content_frame.grid_rowconfigure(0, weight=1)
        left_panel = ttk.Frame(content_frame, width=320)
        left_panel.grid(row=0, column=0, sticky='ns', padx=(0, 10))
        left_panel.pack_propagate(False)
        images_frame = ttk.LabelFrame(left_panel, text='Imagens')
        images_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        self.listbox = tk.Listbox(images_frame, borderwidth=0, highlightthickness=0)
        img_scrollbar = ttk.Scrollbar(images_frame, orient='vertical', command=self.listbox.yview)
        self.listbox.config(yscrollcommand=img_scrollbar.set)
        img_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        annotations_frame = ttk.LabelFrame(left_panel, text='Anotações (W/S para navegar)')
        annotations_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        self.annotation_listbox = tk.Listbox(annotations_frame, exportselection=False, borderwidth=0, highlightthickness=0)
        ann_scrollbar = ttk.Scrollbar(annotations_frame, orient='vertical', command=self.annotation_listbox.yview)
        self.annotation_listbox.config(yscrollcommand=ann_scrollbar.set)
        ann_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.annotation_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        actions_frame = ttk.LabelFrame(left_panel, text='Ações')
        actions_frame.pack(fill=tk.X, pady=5)
        self.add_box_check = ttk.Checkbutton(actions_frame, text='Adicionar Caixa (B)', variable=self.drawing_mode_var, command=self.app.toggle_drawing_mode, style='Switch.TCheckbutton')
        self.add_box_check.pack(side=tk.TOP, anchor='w', padx=5, pady=(5, 10))
        self.add_box_check.config(state='disabled')
        class_edit_frame = ttk.Frame(actions_frame)
        class_edit_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(class_edit_frame, text='Classe:').pack(side=tk.LEFT)
        self.change_class_button = ttk.Button(class_edit_frame, text='Alterar', command=self.app.change_annotation_class)
        self.change_class_button.pack(side=tk.RIGHT, padx=(5, 0))
        self.class_selector = ttk.Combobox(class_edit_frame, textvariable=self.class_id_var, state='readonly')
        self.class_selector.pack(side=tk.LEFT, padx=(5, 5), expand=True, fill=tk.X)
        btn_manage_classes = ttk.Button(actions_frame, text='⚙️ Gerenciar Classes', command=self.app.open_class_manager)
        btn_manage_classes.pack(fill=tk.X, padx=5, pady=10)
        self.set_edit_controls_state('disabled')
        self.canvas = tk.Canvas(content_frame, bg=Config.CANVAS_BG_COLOR, highlightthickness=0)
        self.canvas.grid(row=0, column=1, sticky='nsew')
        bottom_frame = ttk.Frame(self.root, padding=10)
        bottom_frame.pack(fill=tk.X)
        self.prev_button = ttk.Button(bottom_frame, text='← Anterior', command=self.app.show_previous_image)
        self.prev_button.pack(side=tk.LEFT)
        self.next_button = ttk.Button(bottom_frame, text='Próximo →', command=self.app.show_next_image)
        self.next_button.pack(side=tk.RIGHT)
        self.status_label = ttk.Label(bottom_frame, text='Imagem 0 de 0', anchor='center')
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        status_bar_frame = ttk.Frame(self.root, padding=(10, 0, 10, 5))
        status_bar_frame.pack(fill=tk.X)
        ttk.Separator(status_bar_frame, orient='horizontal').pack(fill=tk.X, pady=(0, 2))
        self.coord_label = ttk.Label(status_bar_frame, text='', anchor='w')
        self.coord_label.pack(fill=tk.X)

    def update_status_bar(self, text: str) -> None:
        self.coord_label.config(text=text)

    def set_edit_controls_state(self, state: str) -> None:
        self.class_selector.config(state=state)
        self.change_class_button.config(state=state)
        if state == 'disabled':
            self.class_id_var.set('')

    def refresh_image_list(self) -> None:
        self.listbox.delete(0, tk.END)
        for img_path in self.app_state.image_paths:
            self.listbox.insert(tk.END, os.path.relpath(img_path, self.app_state.base_directory))

    def refresh_annotation_list(self) -> None:
        self.annotation_listbox.delete(0, tk.END)
        for ann in self.app_state.annotations:
            class_name = self.app_state.class_names[ann['class_id']] if ann['class_id'] < len(self.app_state.class_names) else 'ID?'
            self.annotation_listbox.insert(tk.END, f'ID {ann['class_id']} ({class_name})')

    def update_class_selector(self) -> None:
        self.class_selector['values'] = self.app_state.class_names or []
        self.class_selector.config(state='readonly' if self.app_state.class_names else 'disabled')

    def sync_ui_to_state(self) -> None:
        self.drawing_mode_var.set(self.app_state.is_drawing)
        if self.app_state.current_image_index != -1:
            self.listbox.selection_clear(0, tk.END)
            self.listbox.selection_set(self.app_state.current_image_index)
            self.listbox.see(self.app_state.current_image_index)
            self.status_label.config(text=f'Imagem {self.app_state.current_image_index + 1} de {len(self.app_state.image_paths)}')
        else:
            self.status_label.config(text='Imagem 0 de 0')
        self.refresh_annotation_list()
        if self.app_state.selected_annotation_index is not None:
            idx = self.app_state.selected_annotation_index
            self.annotation_listbox.selection_set(idx)
            self.annotation_listbox.activate(idx)
            self.set_edit_controls_state('normal' if self.app_state.class_names else 'disabled')
            class_id = self.app_state.annotations[idx]['class_id']
            if class_id < len(self.app_state.class_names):
                self.class_id_var.set(self.app_state.class_names[class_id])
            else:
                self.class_id_var.set('')
        else:
            self.annotation_listbox.selection_clear(0, tk.END)
            self.set_edit_controls_state('disabled')
        if self.preview_window and self.preview_window.winfo_exists():
            self.preview_window.update_previews()

    def toggle_preview_window(self) -> None:
        if not self.app.app_state.image_paths:
            messagebox.showwarning('Aviso', 'Nenhuma imagem carregada.')
            return
        if self.preview_window is None or not self.preview_window.winfo_exists():
            self.preview_window = PreviewWindow(self.root, self.app)
            self.preview_window.update_previews()
        else:
            self.preview_window.on_close()

    def change_theme(self, event) -> None:
        new_theme = self.theme_combo.get()
        if new_theme:
            self.root.style.theme_use(new_theme)
            self.app.ui_theme_name = new_theme
            self.app.save_current_theme()