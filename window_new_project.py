import os
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk

import yaml

import localization
import utils_ui
from config import Config


class NewProjectWindow(tk.Toplevel):

    def __init__(self, master, callback):
        super().__init__(master)
        self.callback = callback
        self.title(localization.tr('TITLE_NEW_PROJECT'))
        self.geometry('860x650')
        self.minsize(760, 560)
        self.resizable(True, True)
        self.base_path = str(Path.cwd())
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

        ttk.Label(info_frame, text=localization.tr('LBL_LOCATION'), font=Config.FONTS['main_bold']).grid(row=1, column=0, sticky='w', pady=5)
        path_container = ttk.Frame(info_frame)
        path_container.grid(row=1, column=1, sticky='ew', padx=10, pady=5)
        self.entry_path = ttk.Entry(path_container, state='readonly')
        self.entry_path.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(path_container, text=localization.tr('BTN_BROWSE'), command=self.browse).pack(side=tk.RIGHT, padx=(5, 0))
        info_frame.columnconfigure(1, weight=1)

        self._set_base_path(self.base_path)

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
        cols = ('id', 'class_name')
        self.tree = ttk.Treeview(tree_frame, columns=cols, show='headings', selectmode='browse', height=8)
        self.tree.heading('id', text=localization.tr('COL_ID'))
        self.tree.heading('class_name', text=localization.tr('COL_CLASS_NAME'))
        self.tree.column('id', width=50, anchor='center', stretch=False)
        self.tree.column('class_name', anchor='w', stretch=True)
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

    def _set_base_path(self, path: str):
        self.base_path = path
        self.entry_path.config(state='normal')
        self.entry_path.delete(0, tk.END)
        self.entry_path.insert(0, self.base_path)
        self.entry_path.config(state='readonly')

    def browse(self):
        path = filedialog.askdirectory(title=localization.tr('DIALOG_DIR_TITLE'), initialdir=self.base_path, parent=self)
        self.lift()
        if path:
            self._set_base_path(path)

    def _refresh_tree(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for idx, name in enumerate(self.classes_list):
            self.tree.insert('', 'end', values=(idx, name))

    def _normalize_class_name(self, value: str) -> str:
        return ' '.join(value.strip().split())

    def _class_exists(self, value: str, ignore_index=None) -> bool:
        normalized = value.casefold()
        for idx, current in enumerate(self.classes_list):
            if ignore_index is not None and idx == ignore_index:
                continue
            if current.casefold() == normalized:
                return True
        return False

    def add_class(self):
        new_cls = simpledialog.askstring(localization.tr('DIALOG_NEW_CLASS_TITLE'), localization.tr('DIALOG_NEW_CLASS_MSG'), parent=self)
        if new_cls:
            clean_name = self._normalize_class_name(new_cls)
            if clean_name:
                if self._class_exists(clean_name):
                    messagebox.showwarning(localization.tr('MSG_DUPLICATE_TITLE'), localization.tr('MSG_DUPLICATE_BODY').format(clean_name), parent=self)
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
        new_name = simpledialog.askstring(
            localization.tr('DIALOG_EDIT_CLASS_TITLE'),
            localization.tr('DIALOG_EDIT_CLASS_MSG'),
            initialvalue=old_name,
            parent=self
        )
        if new_name:
            clean = self._normalize_class_name(new_name)
            if clean and clean != old_name:
                if self._class_exists(clean, ignore_index=idx):
                    messagebox.showwarning(localization.tr('MSG_DUPLICATE_TITLE'), localization.tr('MSG_DUPLICATE_BODY').format(clean), parent=self)
                    return
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
        if self.classes_list and messagebox.askyesno(localization.tr('DIALOG_CLEAR_TITLE'), localization.tr('MSG_CLEAR_ALL_BODY'), parent=self):
            self.classes_list = []
            self._refresh_tree()

    def _build_yaml_data(self, full_path: str):
        resolved = Path(full_path).resolve()
        try:
            relative_root = f'./{resolved.relative_to(Path.cwd())}'
        except ValueError:
            relative_root = str(resolved)
        return {
            'path': relative_root,
            'train': 'train/images',
            'val': 'valid/images',
            'test': 'test/images',
            'nc': len(self.classes_list),
            'names': self.classes_list,
        }

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
            for subdir in subdirs:
                os.makedirs(os.path.join(full_path, subdir), exist_ok=True)

            with open(os.path.join(full_path, 'classes.txt'), 'w', encoding='utf-8') as f:
                f.write('\n'.join(self.classes_list))

            with open(os.path.join(full_path, 'data.yaml'), 'w', encoding='utf-8') as f:
                yaml.dump(self._build_yaml_data(full_path), f, sort_keys=False, allow_unicode=True)

            messagebox.showinfo(localization.tr('MSG_SUCCESS_TITLE'), localization.tr('MSG_SUCCESS_BODY').format(project_name), parent=self)
            self.callback(full_path)
            self.destroy()
        except Exception as exc:
            messagebox.showerror(localization.tr('MSG_ERR_CRITICAL_TITLE'), localization.tr('MSG_ERR_CREATE_BODY').format(str(exc)), parent=self)
