import tkinter as tk
from tkinter import ttk, messagebox
import ttkbootstrap as tb
import os
from typing import TYPE_CHECKING
from config import Config
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
        self.prop_x = tk.StringVar(value='0')
        self.prop_y = tk.StringVar(value='0')
        self.prop_w = tk.StringVar(value='0')
        self.prop_h = tk.StringVar(value='0')
        self._create_widgets()

    def _create_widgets(self) -> None:
        top_frame = ttk.Frame(self.root, padding=(10, 10, 10, 0))
        top_frame.pack(fill=tk.X)
        ttk.Button(top_frame, text='✨ Novo', command=self.app.open_new_project_wizard, bootstyle='success').pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(top_frame, text='📂 Abrir', command=self.app.select_directory, bootstyle='primary').pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(top_frame, text='🔄', width=3, command=self.app.refresh_directory, bootstyle='outline').pack(side=tk.LEFT, padx=(0, 5))
        ttk.Separator(top_frame, orient='vertical').pack(side=tk.LEFT, fill=tk.Y, padx=10)
        ttk.Button(top_frame, text='🔍 Grid', command=self.app.open_grid_viewer, bootstyle='info-outline').pack(side=tk.LEFT, padx=5)
        ttk.Button(top_frame, text='📊 Stats', command=self.app.open_dataset_analyzer, bootstyle='warning-outline').pack(side=tk.LEFT, padx=5)
        ttk.Button(top_frame, text='⚖️ Split', command=self.app.open_split_wizard, bootstyle='secondary-outline').pack(side=tk.LEFT, padx=5)
        self.dir_label = ttk.Label(top_frame, text='Nenhum projeto aberto', style='TLabel')
        self.dir_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)
        ttk.Label(top_frame, text='Tema:').pack(side=tk.RIGHT)
        self.theme_combo = ttk.Combobox(top_frame, values=self.root.style.theme_names(), textvariable=self.current_theme, state='readonly', width=10)
        self.theme_combo.pack(side=tk.RIGHT, padx=5)
        self.theme_combo.bind('<<ComboboxSelected>>', self.change_theme)
        content_frame = ttk.Frame(self.root, padding=(10, 10, 10, 0))
        content_frame.pack(fill=tk.BOTH, expand=True)
        content_frame.grid_columnconfigure(1, weight=1)
        content_frame.grid_rowconfigure(0, weight=1)
        left_panel = ttk.Frame(content_frame, width=340)
        left_panel.grid(row=0, column=0, sticky='ns', padx=(0, 10))
        left_panel.pack_propagate(False)
        img_fr = ttk.LabelFrame(left_panel, text='Imagens')
        img_fr.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        self.listbox = tk.Listbox(img_fr, borderwidth=0, highlightthickness=0)
        sb = ttk.Scrollbar(img_fr, orient='vertical', command=self.listbox.yview)
        self.listbox.config(yscrollcommand=sb.set)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        ann_fr = ttk.LabelFrame(left_panel, text='Anotações (Objects)')
        ann_fr.pack(fill=tk.BOTH, expand=True, pady=5)
        self.annotation_listbox = tk.Listbox(ann_fr, exportselection=False, borderwidth=0, highlightthickness=0)
        sb_a = ttk.Scrollbar(ann_fr, orient='vertical', command=self.annotation_listbox.yview)
        self.annotation_listbox.config(yscrollcommand=sb_a.set)
        sb_a.pack(side=tk.RIGHT, fill=tk.Y)
        self.annotation_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        act_fr = ttk.LabelFrame(left_panel, text='Propriedades & Ferramentas')
        act_fr.pack(fill=tk.X, pady=5)
        self.add_box_check = ttk.Checkbutton(act_fr, text='Modo Desenho (D)', variable=self.drawing_mode_var, command=self.app.toggle_drawing_mode, style='Switch.TCheckbutton')
        self.add_box_check.pack(anchor='w', padx=5, pady=5)
        self.add_box_check.config(state='normal')
        cls_row = ttk.Frame(act_fr)
        cls_row.pack(fill=tk.X, padx=5, pady=2)
        ttk.Label(cls_row, text='Classe:').pack(side=tk.LEFT)
        self.class_selector = ttk.Combobox(cls_row, textvariable=self.class_id_var, state='readonly')
        self.class_selector.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.change_class_button = ttk.Button(cls_row, text='Set', width=4, command=self.app.change_annotation_class)
        self.change_class_button.pack(side=tk.RIGHT)
        ttk.Button(act_fr, text='⚙️ Gerenciar Classes', command=self.app.open_class_manager).pack(fill=tk.X, padx=5, pady=5)
        ttk.Separator(act_fr, orient='horizontal').pack(fill=tk.X, padx=5, pady=5)
        geo_fr = ttk.Frame(act_fr)
        geo_fr.pack(fill=tk.X, padx=5, pady=5)

        def create_geo_control(parent, label_text, var, cmd_minus, cmd_plus, row):
            ttk.Label(parent, text=label_text, font=('Consolas', 10, 'bold'), width=2).grid(row=row, column=0, padx=2, pady=2)
            e = ttk.Entry(parent, textvariable=var, width=5, justify='center', state='readonly', font=('Consolas', 10))
            e.grid(row=row, column=1, padx=2, pady=2)
            btn_frame = ttk.Frame(parent)
            btn_frame.grid(row=row, column=2, padx=2)
            ttk.Button(btn_frame, text='◄', width=2, command=cmd_minus, bootstyle='secondary-link').pack(side=tk.LEFT)
            ttk.Button(btn_frame, text='►', width=2, command=cmd_plus, bootstyle='secondary-link').pack(side=tk.LEFT)
        create_geo_control(geo_fr, 'X', self.prop_x, lambda: self.app.perform_fine_move(-1, 0), lambda: self.app.perform_fine_move(1, 0), 0)
        create_geo_control(geo_fr, 'Y', self.prop_y, lambda: self.app.perform_fine_move(0, -1), lambda: self.app.perform_fine_move(0, 1), 1)
        create_geo_control(geo_fr, 'W', self.prop_w, lambda: self.app.perform_fine_resize('right', -1), lambda: self.app.perform_fine_resize('right', 1), 2)
        create_geo_control(geo_fr, 'H', self.prop_h, lambda: self.app.perform_fine_resize('bottom', -1), lambda: self.app.perform_fine_resize('bottom', 1), 3)
        ttk.Label(act_fr, text='Use Setas Teclado para Mover', font=('', 8), foreground='gray').pack(pady=2)
        self.canvas = tk.Canvas(content_frame, bg=Config.CANVAS_BG_COLOR, highlightthickness=0)
        self.canvas.grid(row=0, column=1, sticky='nsew')
        bot_frame = ttk.Frame(self.root, padding=10)
        bot_frame.pack(fill=tk.X)
        ttk.Button(bot_frame, text='← Anterior', command=self.app.show_previous_image).pack(side=tk.LEFT)
        self.status_label = ttk.Label(bot_frame, text='--', anchor='center')
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(bot_frame, text='Próximo →', command=self.app.show_next_image).pack(side=tk.RIGHT)
        self.coord_label = ttk.Label(self.root, text='', anchor='w', padding=(10, 0))
        self.coord_label.pack(fill=tk.X)

    def update_status_bar(self, text: str) -> None:
        self.coord_label.config(text=text)

    def set_edit_controls_state(self, state: str) -> None:
        self.class_selector.config(state=state)
        self.change_class_button.config(state=state)
        if state == 'disabled':
            self.class_id_var.set('')
            self.update_inspector_values(None)

    def update_inspector_values(self, rect_coords):
        if not rect_coords:
            self.prop_x.set('-')
            self.prop_y.set('-')
            self.prop_w.set('-')
            self.prop_h.set('-')
            return
        x1, y1, x2, y2 = rect_coords
        rx1, rx2 = (min(x1, x2), max(x1, x2))
        ry1, ry2 = (min(y1, y2), max(y1, y2))
        w = rx2 - rx1
        h = ry2 - ry1
        self.prop_x.set(f'{int(rx1)}')
        self.prop_y.set(f'{int(ry1)}')
        self.prop_w.set(f'{int(w)}')
        self.prop_h.set(f'{int(h)}')

    def refresh_image_list(self) -> None:
        self.listbox.delete(0, tk.END)
        for p in self.app_state.image_paths:
            self.listbox.insert(tk.END, os.path.relpath(p, self.app_state.base_directory))

    def refresh_annotation_list(self) -> None:
        self.annotation_listbox.delete(0, tk.END)
        for ann in self.app_state.annotations:
            c_name = self.app_state.class_names[ann['class_id']] if ann['class_id'] < len(self.app_state.class_names) else 'ID?'
            self.annotation_listbox.insert(tk.END, f'ID {ann['class_id']} ({c_name})')

    def update_class_selector(self) -> None:
        self.class_selector['values'] = self.app_state.class_names or []
        self.class_selector.config(state='readonly' if self.app_state.class_names else 'disabled')

    def sync_ui_to_state(self) -> None:
        self.drawing_mode_var.set(self.app_state.is_drawing)
        if self.app_state.current_image_index != -1:
            self.listbox.selection_clear(0, tk.END)
            self.listbox.selection_set(self.app_state.current_image_index)
            self.listbox.see(self.app_state.current_image_index)
            path = self.app_state.get_current_image_path()
            if path:
                self.status_label.config(text=f'Img {self.app_state.current_image_index + 1} / {len(self.app_state.image_paths)} : {os.path.basename(path)}')
        else:
            self.status_label.config(text='--')
        self.add_box_check.config(state='normal')
        self.refresh_annotation_list()
        idx = self.app_state.selected_annotation_index
        if idx is not None and idx < len(self.app_state.annotations):
            self.annotation_listbox.selection_set(idx)
            self.annotation_listbox.activate(idx)
            self.annotation_listbox.see(idx)
            self.set_edit_controls_state('normal')
            rect = self.app_state.annotations[idx]['rect_orig']
            self.update_inspector_values(rect)
            cid = self.app_state.annotations[idx]['class_id']
            if cid < len(self.app_state.class_names):
                self.class_id_var.set(self.app_state.class_names[cid])
        else:
            self.annotation_listbox.selection_clear(0, tk.END)
            self.set_edit_controls_state('disabled')

    def change_theme(self, event) -> None:
        t = self.theme_combo.get()
        if t:
            self.root.style.theme_use(t)
            self.app.ui_theme_name = t
            self.app.save_current_theme()