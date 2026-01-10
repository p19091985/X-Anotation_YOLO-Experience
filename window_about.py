import tkinter as tk
from tkinter import ttk
import localization
from config import Config

class AboutWindow:

    def __init__(self, parent):
        self.top = tk.Toplevel(parent)
        self.top.title(localization.tr('TITLE_ABOUT'))
        self.top.geometry('500x350')
        self.top.resizable(False, False)
        self.top.transient(parent)
        self.top.grab_set()
        self._create_widgets()
        self.top.update_idletasks()
        width = self.top.winfo_width()
        height = self.top.winfo_height()
        parent_x = parent.winfo_rootx()
        parent_y = parent.winfo_rooty()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()
        x = parent_x + parent_width // 2 - width // 2
        y = parent_y + parent_height // 2 - height // 2
        self.top.geometry(f'{width}x{height}+{x}+{y}')

    def _create_widgets(self):
        main_frame = ttk.Frame(self.top, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        ttk.Label(main_frame, text='X-Annotation YOLO Ultimate', font=('Segoe UI', 20, 'bold')).pack(pady=(0, 20))
        info_frame = ttk.Frame(main_frame)
        info_frame.pack(fill=tk.X, pady=10)
        ttk.Label(info_frame, text=localization.tr('LBL_AUTHOR'), font=('Segoe UI', 10, 'bold')).grid(row=0, column=0, sticky='e', padx=5, pady=2)
        ttk.Label(info_frame, text='Patrik').grid(row=0, column=1, sticky='w', padx=5, pady=2)
        ttk.Label(info_frame, text=localization.tr('LBL_EMAIL'), font=('Segoe UI', 10, 'bold')).grid(row=1, column=0, sticky='e', padx=5, pady=2)
        ttk.Label(info_frame, text='patrik.lima.pereira@gmail.com').grid(row=1, column=1, sticky='w', padx=5, pady=2)
        ttk.Label(info_frame, text=localization.tr('LBL_VERSION'), font=('Segoe UI', 10, 'bold')).grid(row=2, column=0, sticky='e', padx=5, pady=2)
        ttk.Label(info_frame, text='2.0.0').grid(row=2, column=1, sticky='w', padx=5, pady=2)
        ttk.Label(main_frame, text=localization.tr('LBL_DESC'), font=('Segoe UI', 10, 'bold')).pack(anchor='w', pady=(15, 5))
        desc_frame = ttk.Frame(main_frame, relief='sunken', borderwidth=1)
        desc_frame.pack(fill=tk.BOTH, expand=True)
        lbl_desc = ttk.Label(desc_frame, text=localization.tr('MSG_DESC_TEXT'), wraplength=440, justify='left')
        lbl_desc.pack(padx=10, pady=10, fill=tk.BOTH)
        ttk.Button(main_frame, text=localization.tr('BTN_CLOSE'), command=self.top.destroy).pack(side=tk.BOTTOM, pady=(10, 0))