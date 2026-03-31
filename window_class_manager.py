import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
from typing import List, Optional

import localization
import utils_ui


class ClassManagerWindow(tk.Toplevel):

    def __init__(self, master, class_list: List[str], callback: callable, usage_counts: Optional[List[int]]=None):
        super().__init__(master)
        self.title(localization.tr('TITLE_CLASS_MANAGER'))
        self.geometry('620x560')
        self.minsize(520, 460)
        self.transient(master)
        self.grab_set()
        self.callback = callback
        usage_counts = usage_counts or []
        self.class_entries = [
            {
                'source_index': idx,
                'name': name,
                'image_count': usage_counts[idx] if idx < len(usage_counts) else 0,
            }
            for idx, name in enumerate(class_list)
        ]

        main_container = ttk.Frame(self, padding=15)
        main_container.pack(fill=tk.BOTH, expand=True)

        list_frame = ttk.LabelFrame(main_container, text=localization.tr('GRP_CURRENT_CLASSES'), padding=8)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        tree_frame = ttk.Frame(list_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        columns = ('id', 'class_name', 'images')
        self.tree = ttk.Treeview(tree_frame, columns=columns, show='headings', selectmode='browse')
        self.tree.heading('id', text=localization.tr('COL_ID'))
        self.tree.heading('class_name', text=localization.tr('COL_CLASS_NAME'))
        self.tree.heading('images', text=self._tr('COL_IMAGE_USAGE', 'Imagens'))
        self.tree.column('id', width=60, anchor='center', stretch=False)
        self.tree.column('class_name', width=320, anchor='w', stretch=True)
        self.tree.column('images', width=90, anchor='center', stretch=False)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.tree.bind('<Double-1>', lambda _event: self.edit())

        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        btn_fr = ttk.Frame(main_container)
        btn_fr.pack(fill=tk.X, pady=5)
        btn_fr.columnconfigure(0, weight=1)
        btn_fr.columnconfigure(1, weight=1)
        btn_fr.columnconfigure(2, weight=1)
        ttk.Button(btn_fr, text=localization.tr('BTN_ADD'), command=self.add).grid(row=0, column=0, padx=2, sticky='ew')
        ttk.Button(btn_fr, text=localization.tr('BTN_EDIT'), command=self.edit).grid(row=0, column=1, padx=2, sticky='ew')
        ttk.Button(btn_fr, text=localization.tr('BTN_DELETE'), command=self.delete).grid(row=0, column=2, padx=2, sticky='ew')

        ttk.Separator(main_container, orient='horizontal').pack(fill=tk.X, pady=10)
        ttk.Button(main_container, text=localization.tr('BTN_SAVE_CLOSE'), command=self.save).pack(fill=tk.X)

        self._refresh_tree()
        utils_ui.center_window(self, master)

    def _tr(self, key: str, default: str) -> str:
        value = localization.tr(key)
        return default if value == key else value

    def _normalize_class_name(self, value: str) -> str:
        return ' '.join(value.strip().split())

    def _class_exists(self, value: str, ignore_index=None) -> bool:
        normalized = value.casefold()
        for idx, entry in enumerate(self.class_entries):
            if ignore_index is not None and idx == ignore_index:
                continue
            if entry['name'].casefold() == normalized:
                return True
        return False

    def _selected_index(self):
        selection = self.tree.selection()
        if not selection:
            return None
        return int(self.tree.item(selection[0], 'values')[0])

    def _refresh_tree(self):
        current_selection = self._selected_index()
        for item in self.tree.get_children():
            self.tree.delete(item)
        for idx, entry in enumerate(self.class_entries):
            self.tree.insert('', 'end', iid=str(idx), values=(idx, entry['name'], entry['image_count']))
        if current_selection is not None and current_selection < len(self.class_entries):
            iid = str(current_selection)
            self.tree.selection_set(iid)
            self.tree.focus(iid)

    def add(self):
        new_name = simpledialog.askstring(
            localization.tr('DIALOG_NEW_CLASS_TITLE'),
            localization.tr('DIALOG_NEW_CLASS_MSG'),
            parent=self
        )
        if not new_name:
            return
        clean_name = self._normalize_class_name(new_name)
        if not clean_name:
            return
        if self._class_exists(clean_name):
            messagebox.showwarning(
                localization.tr('MSG_DUPLICATE_TITLE'),
                localization.tr('MSG_DUPLICATE_BODY').format(clean_name),
                parent=self
            )
            return
        self.class_entries.append({'source_index': None, 'name': clean_name, 'image_count': 0})
        self._refresh_tree()
        iid = str(len(self.class_entries) - 1)
        self.tree.selection_set(iid)
        self.tree.focus(iid)

    def edit(self):
        idx = self._selected_index()
        if idx is None:
            return
        old_name = self.class_entries[idx]['name']
        new_name = simpledialog.askstring(
            localization.tr('DIALOG_EDIT_CLASS_TITLE'),
            localization.tr('DIALOG_EDIT_CLASS_MSG'),
            initialvalue=old_name,
            parent=self
        )
        if not new_name:
            return
        clean_name = self._normalize_class_name(new_name)
        if not clean_name or clean_name == old_name:
            return
        if self._class_exists(clean_name, ignore_index=idx):
            messagebox.showwarning(
                localization.tr('MSG_DUPLICATE_TITLE'),
                localization.tr('MSG_DUPLICATE_BODY').format(clean_name),
                parent=self
            )
            return
        self.class_entries[idx]['name'] = clean_name
        self._refresh_tree()

    def delete(self):
        idx = self._selected_index()
        if idx is None:
            return
        entry = self.class_entries[idx]
        if entry['image_count'] > 0:
            messagebox.showwarning(
                self._tr('MSG_CLASS_IN_USE_TITLE', localization.tr('MSG_WARN_TITLE')),
                self._tr(
                    'MSG_CLASS_IN_USE_BODY',
                    "A classe '{}' não pode ser excluída porque já está usada em {} imagem(ns)."
                ).format(entry['name'], entry['image_count']),
                parent=self
            )
            return
        if messagebox.askyesno(
            localization.tr('DIALOG_CONFIRM_TITLE'),
            localization.tr('MSG_REMOVE_CLASS_BODY').format(entry['name']),
            parent=self
        ):
            self.class_entries.pop(idx)
            self._refresh_tree()

    def save(self):
        class_names = [entry['name'] for entry in self.class_entries]
        if not class_names:
            messagebox.showwarning(localization.tr('MSG_WARN_TITLE'), localization.tr('MSG_REQ_CLASS'), parent=self)
            return
        class_id_map = {
            entry['source_index']: idx
            for idx, entry in enumerate(self.class_entries)
            if entry['source_index'] is not None
        }
        self.callback({'classes': class_names, 'id_map': class_id_map})
        self.destroy()
