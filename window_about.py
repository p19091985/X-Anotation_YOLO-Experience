import tkinter as tk
from tkinter import ttk

from config import Config
import localization
from utils_ui import center_window


class AboutWindow:

    def __init__(self, parent):
        self.top = tk.Toplevel(parent)
        self.top.title(Config.APP_NAME)
        self.top.geometry('560x420')
        self.top.resizable(False, False)
        self.top.transient(parent)
        self.top.grab_set()
        self._create_widgets()
        center_window(self.top, parent)

    def _create_widgets(self):
        main_frame = ttk.Frame(self.top, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main_frame, text=Config.APP_NAME, font=('Segoe UI', 18, 'bold')).pack(pady=(0, 20))

        info_frame = ttk.Frame(main_frame)
        info_frame.pack(fill=tk.X, pady=5)
        row = 0
        for label, value in [
            (localization.tr('LBL_AUTHOR'), Config.APP_AUTHOR),
            (localization.tr('LBL_EMAIL'), Config.APP_CONTACT),
            (localization.tr('LBL_VERSION'), Config.APP_VERSION),
        ]:
            ttk.Label(info_frame, text=label, font=('Segoe UI', 9, 'bold')).grid(row=row, column=0, sticky='e', padx=5, pady=2)
            ttk.Label(info_frame, text=value).grid(row=row, column=1, sticky='w', padx=5, pady=2)
            row += 1

        ttk.Label(main_frame, text=localization.tr('LBL_DESC'), font=('Segoe UI', 9, 'bold')).pack(anchor='w', pady=(15, 5))
        desc_frame = ttk.Frame(main_frame, relief='sunken', borderwidth=1)
        desc_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        lbl_desc = ttk.Label(desc_frame, text=Config.APP_DESCRIPTION, wraplength=500, justify='left')
        lbl_desc.pack(padx=10, pady=10, fill=tk.BOTH)

        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X)
        btn_close = ttk.Button(btn_frame, text=localization.tr('BTN_CLOSE'), command=self.top.destroy, width=15, default='active', cursor='hand2')
        btn_close.pack(pady=5)
        btn_close.focus_set()
        self.top.bind('<Return>', lambda e: self.top.destroy())
        self.top.bind('<Escape>', lambda e: self.top.destroy())
