import tkinter as tk
from tkinter import ttk

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import localization
import utils_ui
from config import Config


class SplitWizard(tk.Toplevel):

    def __init__(self, master, callback):
        super().__init__(master)
        self.callback = callback
        self.title(localization.tr('TITLE_SPLIT_WIZARD'))
        self.geometry('700x480')
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()
        self.train_pct = tk.DoubleVar(value=80)
        self.val_pct = tk.DoubleVar(value=20)
        self.test_pct = tk.DoubleVar(value=0)
        self.include_test = tk.BooleanVar(value=False)
        self.shuffle = tk.BooleanVar(value=True)
        self._setup_ui()
        self._on_scale_change()
        utils_ui.center_window(self, master)

    def _tr_default(self, key: str, default: str) -> str:
        value = localization.tr(key)
        return default if value == key else value

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
        ttk.Label(lbl_frame, text=localization.tr('LBL_TRAIN'), font=Config.FONTS['main_bold'], foreground='#007BFF').pack(side=tk.LEFT)
        ttk.Label(lbl_frame, text=localization.tr('LBL_VAL'), font=Config.FONTS['main_bold'], foreground='#FFC107').pack(side=tk.RIGHT)

        self.scale = ttk.Scale(left_panel, from_=0, to=100, variable=self.train_pct, command=self._on_scale_change)
        self.scale.pack(fill=tk.X, pady=5)

        info_frame = ttk.Frame(left_panel)
        info_frame.pack(fill=tk.X, pady=5)
        self.lbl_train_val = ttk.Label(info_frame, text='80%', font=Config.FONTS['sub_header'], foreground='#007BFF')
        self.lbl_train_val.pack(side=tk.LEFT)
        self.lbl_val_val = ttk.Label(info_frame, text=' | Val: 20%', font=Config.FONTS['sub_header'], foreground='#FFC107')
        self.lbl_val_val.pack(side=tk.LEFT)
        self.lbl_test_val = ttk.Label(info_frame, text='', font=Config.FONTS['sub_header'], foreground='#28A745')
        self.lbl_test_val.pack(side=tk.LEFT)

        ttk.Separator(left_panel, orient='horizontal').pack(fill=tk.X, pady=10)

        chk_label = self._tr_default('CHK_ENABLE_TEST_SPLIT', 'Habilitar split de teste')
        self.chk_test = ttk.Checkbutton(left_panel, text=chk_label, variable=self.include_test, command=self._on_test_toggle)
        self.chk_test.pack(anchor='w', pady=5)

        self.test_scale_frame = ttk.Frame(left_panel)
        ttk.Label(
            self.test_scale_frame,
            text=self._tr_default('LBL_TEST', 'TEST'),
            font=Config.FONTS['main_bold'],
            foreground='#28A745'
        ).pack(side=tk.LEFT)
        self.scale_test = ttk.Scale(self.test_scale_frame, from_=0, to=50, variable=self.test_pct, command=self._on_scale_change)
        self.scale_test.pack(fill=tk.X, pady=5)

        ttk.Separator(left_panel, orient='horizontal').pack(fill=tk.X, pady=10)

        self.chk_shuffle = ttk.Checkbutton(left_panel, text=localization.tr('CHK_SHUFFLE'), variable=self.shuffle)
        self.chk_shuffle.pack(anchor='w')
        ttk.Button(left_panel, text=localization.tr('BTN_APPLY_SPLIT'), command=self.apply).pack(fill=tk.X, side=tk.BOTTOM)

        right_panel = ttk.Frame(content, width=260)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH)
        self.fig = plt.Figure(figsize=(3.2, 3.2), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=right_panel)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def _on_test_toggle(self):
        if self.include_test.get():
            self.test_scale_frame.pack(fill=tk.X, pady=5, before=self.chk_shuffle)
            if self.test_pct.get() == 0:
                self.test_pct.set(10)
        else:
            self.test_scale_frame.pack_forget()
            self.test_pct.set(0)
        self._on_scale_change()

    def _on_scale_change(self, val=None):
        train_value = int(self.train_pct.get())
        test_value = int(self.test_pct.get()) if self.include_test.get() else 0
        if train_value + test_value > 100:
            train_value = 100 - test_value
            self.train_pct.set(train_value)
        val_value = 100 - train_value - test_value
        self.val_pct.set(val_value)

        self.lbl_train_val.config(text=f'{train_value}%')
        self.lbl_val_val.config(text=f' | Val: {val_value}%')
        self.lbl_test_val.config(text=f' | Test: {test_value}%' if test_value > 0 else '')
        self._update_chart(train_value, val_value, test_value)

    def _update_chart(self, train_value, val_value, test_value):
        self.ax.clear()
        labels = [localization.tr('LBL_TRAIN'), localization.tr('LBL_VAL')]
        colors = ['#007BFF', '#FFC107']
        sizes = [train_value, val_value]
        explode = [0.05, 0]

        if test_value > 0:
            labels.append(self._tr_default('LBL_TEST', 'TEST'))
            colors.append('#28A745')
            sizes.append(test_value)
            explode.append(0)

        filtered_sizes = []
        filtered_labels = []
        filtered_colors = []
        filtered_explode = []
        for idx, size in enumerate(sizes):
            if size > 0:
                filtered_sizes.append(size)
                filtered_labels.append(labels[idx])
                filtered_colors.append(colors[idx])
                filtered_explode.append(explode[idx])

        if filtered_sizes:
            self.ax.pie(
                filtered_sizes,
                labels=filtered_labels,
                autopct='%1.1f%%',
                startangle=90,
                colors=filtered_colors,
                explode=filtered_explode,
                pctdistance=0.85,
                textprops={'fontweight': 'bold'}
            )
            centre_circle = plt.Circle((0, 0), 0.7, fc='white')
            self.ax.add_artist(centre_circle)
            self.ax.axis('equal')
        self.canvas.draw()

    def apply(self):
        self.callback(
            self.train_pct.get() / 100,
            self.val_pct.get() / 100,
            self.test_pct.get() / 100 if self.include_test.get() else 0.0,
            self.shuffle.get()
        )
        self.destroy()
