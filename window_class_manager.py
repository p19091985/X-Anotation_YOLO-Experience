import tkinter as tk
from tkinter import ttk, simpledialog, Listbox
from typing import List
import utils_ui
import localization

class ClassManagerWindow(tk.Toplevel):

    def __init__(self, master, class_list: List[str], callback: callable):
        super().__init__(master)

    def __init__(self, master, class_list: List[str], callback: callable):
        super().__init__(master)
        self.title(localization.tr('TITLE_CLASS_MANAGER'))
        self.geometry('450x550')
        self.transient(master)
        self.grab_set()
        self.class_list = class_list[:]
        self.callback = callback
        main_container = ttk.Frame(self, padding=15)
        main_container.pack(fill=tk.BOTH, expand=True)
        list_frame = ttk.LabelFrame(main_container, text=localization.tr('GRP_CURRENT_CLASSES'), padding=5)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        self.lb = Listbox(list_frame, font=('Segoe UI', 11), activestyle='none')
        self.lb.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.lb.yview)
        self.lb.configure(yscrollcommand=sb.set)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        for i in self.class_list:
            self.lb.insert(tk.END, i)
        btn_fr = ttk.Frame(main_container)
        btn_fr.pack(fill=tk.X, pady=5)
        btn_fr.columnconfigure(0, weight=1)
        btn_fr.columnconfigure(1, weight=1)
        btn_fr.columnconfigure(2, weight=1)
        ttk.Button(btn_fr, text=localization.tr('BTN_ADD'), command=self.add).grid(row=0, column=0, padx=2, sticky='ew')
        ttk.Button(btn_fr, text=localization.tr('BTN_RENAME'), command=self.edit).grid(row=0, column=1, padx=2, sticky='ew')
        ttk.Button(btn_fr, text=localization.tr('BTN_DELETE'), command=self.delete).grid(row=0, column=2, padx=2, sticky='ew')
        ttk.Separator(main_container, orient='horizontal').pack(fill=tk.X, pady=10)
        ttk.Button(main_container, text=localization.tr('BTN_SAVE_CLOSE'), command=self.save).pack(fill=tk.X)
        utils_ui.center_window(self, master)

    def add(self):
        n = simpledialog.askstring(localization.tr('DIALOG_NEW_CLASS_TITLE'), localization.tr('DIALOG_NEW_CLASS_MSG'), parent=self)
        if n:
            self.class_list.append(n)
            self.lb.insert(tk.END, n)

    def edit(self):
        sel = self.lb.curselection()
        if not sel:
            return
        idx = sel[0]
        old = self.class_list[idx]
        new = simpledialog.askstring(localization.tr('DIALOG_EDIT_TITLE'), localization.tr('DIALOG_EDIT_MSG'), initialvalue=old, parent=self)
        if new:
            self.class_list[idx] = new
            self.lb.delete(idx)
            self.lb.insert(idx, new)

    def delete(self):
        sel = self.lb.curselection()
        if not sel:
            return
        self.class_list.pop(sel[0])
        self.lb.delete(sel[0])

    def save(self):
        self.callback(self.class_list)
        self.destroy()