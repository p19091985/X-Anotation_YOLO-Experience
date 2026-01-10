import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import os
import yaml
import utils_ui
from utils_ui import log_errors
from config import Config
import localization

class NewProjectWindow(tk.Toplevel):

    def __init__(self, master, callback):
        super().__init__(master)
        self.callback = callback
        self.title(localization.tr('TITLE_NEW_PROJECT'))
        self.geometry('700x650')
        self.resizable(False, False)
        self.base_path = ''
        self.classes_list = []
        self.transient(master)
        self.grab_set()
        self._create_ui()
        utils_ui.center_window(self, master)
        self.focus_force()

    def _create_ui(self):
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        info_frame = ttk.LabelFrame(main_frame, text=localization.tr('GRP_PROJECT_DEF'), padding=15)
        info_frame.pack(fill=tk.X, pady=(0, 20))
        ttk.Label(info_frame, text=localization.tr('LBL_PROJECT_NAME'), font=Config.FONTS['main_bold']).grid(row=0, column=0, sticky='w', pady=5)
        self.e_name = ttk.Entry(info_frame, font=Config.FONTS['main'])
        self.e_name.grid(row=0, column=1, sticky='ew', padx=10, pady=5)
        ttk.Label(info_frame, text=localization.tr('LBL_LOCATION'), font=('Segoe UI', 10, 'bold')).grid(row=1, column=0, sticky='w', pady=5)
        path_container = ttk.Frame(info_frame)
        path_container.grid(row=1, column=1, sticky='ew', padx=10, pady=5)
        self.entry_path = ttk.Entry(path_container, state='readonly')
        self.entry_path.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(path_container, text=localization.tr('BTN_BROWSE'), command=self.browse).pack(side=tk.RIGHT, padx=(5, 0))
        info_frame.columnconfigure(1, weight=1)
        cls_frame = ttk.LabelFrame(main_frame, text=localization.tr('GRP_CLASS_STRUCT'), padding=15)
        cls_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        toolbar = ttk.Frame(cls_frame)
        toolbar.pack(fill=tk.X, pady=(0, 10))
        ttk.Button(toolbar, text=localization.tr('BTN_ADD'), command=self.add_class).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar, text=localization.tr('BTN_EDIT'), command=self.edit_class).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text=localization.tr('BTN_REMOVE'), command=self.remove_class).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text=localization.tr('BTN_CLEAR_ALL'), command=self.clear_classes).pack(side=tk.RIGHT)
        tree_frame = ttk.Frame(cls_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        cols = ('ID', 'Nome da Classe')
        self.tree = ttk.Treeview(tree_frame, columns=cols, show='headings', selectmode='browse', height=8)
        self.tree.heading('ID', text=localization.tr('COL_ID'))
        self.tree.heading('Nome da Classe', text=localization.tr('COL_CLASS_NAME'))
        self.tree.column('ID', width=50, anchor='center', stretch=False)
        self.tree.column('Nome da Classe', anchor='w', stretch=True)
        sb = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.bind('<Double-1>', lambda e: self.edit_class())
        self._refresh_tree()
        footer = ttk.Frame(main_frame)
        footer.pack(fill=tk.X, side=tk.BOTTOM)
        ttk.Button(footer, text=localization.tr('BTN_CANCEL'), command=self.destroy).pack(side=tk.LEFT)
        self.btn_create = ttk.Button(footer, text=localization.tr('BTN_CREATE_YOLO'), command=self.create_structure)
        self.btn_create.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(10, 0))

    def browse(self):
        path = filedialog.askdirectory(title='Selecione o diretório pai do projeto', parent=self)
        self.lift()
        if path:
            self.base_path = path
            self.entry_path.config(state='normal')
            self.entry_path.delete(0, tk.END)
            self.entry_path.insert(0, self.base_path)
            self.entry_path.config(state='readonly')

    def _refresh_tree(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for idx, name in enumerate(self.classes_list):
            self.tree.insert('', 'end', values=(idx, name))

    def add_class(self):
        new_cls = simpledialog.askstring('Nova Classe', 'Digite o nome da classe:', parent=self)
        if new_cls:
            clean_name = new_cls.strip()
            if clean_name:
                if clean_name in self.classes_list:
                    messagebox.showwarning('Duplicada', f"A classe '{clean_name}' já existe.", parent=self)
                else:
                    self.classes_list.append(clean_name)
                    self._refresh_tree()

    def edit_class(self):
        sel = self.tree.selection()
        if not sel:
            return
        item = self.tree.item(sel[0])
        idx = item['values'][0]
        old_name = self.classes_list[idx]
        new_name = simpledialog.askstring(localization.tr('DIALOG_EDIT_CLASS_TITLE'), localization.tr('DIALOG_EDIT_CLASS_MSG'), initialvalue=old_name, parent=self)
        if new_name:
            clean = new_name.strip()
            if clean and clean != old_name:
                self.classes_list[idx] = clean
                self._refresh_tree()

    def remove_class(self):
        sel = self.tree.selection()
        if not sel:
            return
        item = self.tree.item(sel[0])
        idx = item['values'][0]
        name = self.classes_list[idx]
        if messagebox.askyesno(localization.tr('DIALOG_CONFIRM_TITLE'), localization.tr('MSG_REMOVE_CLASS_BODY').format(name), parent=self):
            self.classes_list.pop(idx)
            self._refresh_tree()

    def clear_classes(self):
        if self.classes_list:
            if messagebox.askyesno(localization.tr('DIALOG_CLEAR_TITLE'), localization.tr('MSG_CLEAR_ALL_BODY'), parent=self):
                self.classes_list = []
                self._refresh_tree()

    def create_structure(self):
        project_name = self.e_name.get().strip()
        if not project_name:
            messagebox.showwarning(localization.tr('MSG_WARN_TITLE'), localization.tr('MSG_REQ_NAME'), parent=self)
            self.e_name.focus()
            return
        if not self.base_path:
            messagebox.showwarning(localization.tr('MSG_WARN_TITLE'), localization.tr('MSG_REQ_PATH'), parent=self)
            self.browse()
            return
        if not self.classes_list:
            messagebox.showwarning(localization.tr('MSG_WARN_TITLE'), localization.tr('MSG_REQ_CLASS'), parent=self)
            return
        full_path = os.path.join(self.base_path, project_name)
        if os.path.exists(full_path):
            messagebox.showerror(localization.tr('MSG_ERR_EXISTS_TITLE'), localization.tr('MSG_ERR_EXISTS_BODY').format(project_name), parent=self)
            return
        try:
            subdirs = ['train/images', 'train/labels', 'valid/images', 'valid/labels', 'test/images', 'test/labels']
            os.makedirs(full_path, exist_ok=True)
            for d in subdirs:
                os.makedirs(os.path.join(full_path, d), exist_ok=True)
            classes_txt_path = os.path.join(full_path, 'classes.txt')
            with open(classes_txt_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(self.classes_list))
            train_path = os.path.abspath(os.path.join(full_path, 'train/images'))
            val_path = os.path.abspath(os.path.join(full_path, 'valid/images'))
            test_path = os.path.abspath(os.path.join(full_path, 'test/images'))
            yaml_data = {'path': os.path.abspath(full_path), 'train': train_path, 'val': val_path, 'test': test_path, 'nc': len(self.classes_list), 'names': self.classes_list}
            yaml_path = os.path.join(full_path, 'data.yaml')
            with open(yaml_path, 'w', encoding='utf-8') as f:
                yaml.dump(yaml_data, f, sort_keys=False, allow_unicode=True)
            messagebox.showinfo(localization.tr('MSG_SUCCESS_TITLE'), localization.tr('MSG_SUCCESS_BODY').format(project_name), parent=self)
            self.callback(full_path)
            self.destroy()
        except Exception as e:
            messagebox.showerror(localization.tr('MSG_ERR_CRITICAL_TITLE'), localization.tr('MSG_ERR_CREATE_BODY').format(str(e)), parent=self)