import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import utils_ui
from utils_ui import log_errors
from config import Config
import localization

class SplitWizard(tk.Toplevel):

    def __init__(self, master, callback):
        super().__init__(master)
        self.callback = callback
        self.title(localization.tr('TITLE_SPLIT_WIZARD'))
        self.geometry('650x450')
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()
        self.train_pct = tk.DoubleVar(value=80)
        self.val_pct = tk.DoubleVar(value=20)
        self.shuffle = tk.BooleanVar(value=True)
        self._setup_ui()
        self._update_chart()
        utils_ui.center_window(self, master)

    def _setup_ui(self):
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        ttk.Label(main_frame, text=localization.tr('LBL_DISTRIBUTION'), font=Config.FONTS['header']).pack(pady=(0, 20))
        content = ttk.Frame(main_frame)
        content.pack(fill=tk.BOTH, expand=True)
        left_panel = ttk.Frame(content)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 20))
        lbl_frame = ttk.Frame(left_panel)
        lbl_frame.pack(fill=tk.X, pady=(10, 0))
        ttk.Label(lbl_frame, text=localization.tr('LBL_TRAIN'), font=Config.FONTS['main_bold'], foreground='#007bff').pack(side=tk.LEFT)
        ttk.Label(lbl_frame, text=localization.tr('LBL_VAL'), font=Config.FONTS['main_bold'], foreground='#ffc107').pack(side=tk.RIGHT)
        self.scale = ttk.Scale(left_panel, from_=0, to=100, variable=self.train_pct, command=self._on_scale_change)
        self.scale.pack(fill=tk.X, pady=5)
        info_frame = ttk.Frame(left_panel)
        info_frame.pack(fill=tk.X, pady=5)
        self.lbl_train_val = ttk.Label(info_frame, text='80%', font=Config.FONTS['sub_header'], foreground='#007bff')
        self.lbl_train_val.pack(side=tk.LEFT)
        self.lbl_val_val = ttk.Label(info_frame, text='20%', font=Config.FONTS['sub_header'], foreground='#ffc107')
        self.lbl_val_val.pack(side=tk.RIGHT)
        ttk.Separator(left_panel, orient='horizontal').pack(fill=tk.X, pady=20)
        ttk.Checkbutton(left_panel, text=localization.tr('CHK_SHUFFLE'), variable=self.shuffle).pack(anchor='w')
        ttk.Button(left_panel, text=localization.tr('BTN_APPLY_SPLIT'), command=self.apply).pack(fill=tk.X, side=tk.BOTTOM)
        right_panel = ttk.Frame(content, width=250)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH)
        self.fig = plt.Figure(figsize=(3, 3), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=right_panel)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def _on_scale_change(self, val):
        t = int(float(val))
        v = 100 - t
        self.train_pct.set(t)
        self.val_pct.set(v)
        self.lbl_train_val.config(text=f'{t}%')
        self.lbl_val_val.config(text=f'{v}%')
        self._update_chart()

    def _update_chart(self):
        t = self.train_pct.get()
        v = self.val_pct.get()
        self.ax.clear()
        sizes = [t, v]
        labels = ['Train', 'Val']
        colors = ['#007bff', '#ffc107']
        explode = (0.05, 0)
        self.ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90, colors=colors, explode=explode, pctdistance=0.85, textprops=dict(fontweight='bold'))
        centre_circle = plt.Circle((0, 0), 0.7, fc='white')
        self.ax.add_artist(centre_circle)
        self.ax.axis('equal')
        self.canvas.draw()

    def apply(self):
        t = self.train_pct.get() / 100
        v = self.val_pct.get() / 100
        shuff = self.shuffle.get()
        self.callback(t, v, 0.0, shuff)
        self.destroy()