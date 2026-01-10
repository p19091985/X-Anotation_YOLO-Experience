import tkinter as tk
from tkinter import ttk, messagebox
import logging
import functools
logger = logging.getLogger(__name__)

def log_errors(func):

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.exception(f'Erro crítico em {func.__name__}: {str(e)}')
            messagebox.showerror('Erro Inesperado', f"Ocorreu um erro durante a operação:\n\n{str(e)}\n\nConsulte 'application.log' para detalhes técnicos.")
    return wrapper

def center_window(window, parent):
    window.update_idletasks()
    width = window.winfo_width()
    height = window.winfo_height()
    parent_x = parent.winfo_rootx()
    parent_y = parent.winfo_rooty()
    parent_width = parent.winfo_width()
    parent_height = parent.winfo_height()
    x = parent_x + parent_width // 2 - width // 2
    y = parent_y + parent_height // 2 - height // 2
    x = max(0, x)
    y = max(0, y)
    window.geometry(f'+{x}+{y}')

def maximize_window(window):
    try:
        if window.tk.call('tk', 'windowingsystem') == 'win32':
            window.state('zoomed')
        else:
            window.attributes('-zoomed', True)
    except Exception:
        w, h = (window.winfo_screenwidth(), window.winfo_screenheight())
        window.geometry(f'{w}x{h}+0+0')

class ScrolledFrame(ttk.Frame):

    def __init__(self, parent, autohide=False, width=None, height=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.canvas = tk.Canvas(self, highlightthickness=0)
        self.v_scroll = ttk.Scrollbar(self, orient='vertical', command=self.canvas.yview)
        self.v_scroll.pack(side='right', fill='y')
        self.canvas.pack(side='left', fill='both', expand=True)
        self.canvas.configure(yscrollcommand=self.v_scroll.set)
        self.interior = ttk.Frame(self.canvas)
        self.canvas_window = self.canvas.create_window((0, 0), window=self.interior, anchor='nw')
        self.interior.bind('<Configure>', self._on_interior_configure)
        self.canvas.bind('<Configure>', self._on_canvas_configure)
        if width:
            self.canvas.configure(width=width)
        if height:
            self.canvas.configure(height=height)

    def _on_interior_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox('all'))

    def _on_canvas_configure(self, event):
        if self.canvas.winfo_width() > self.interior.winfo_reqwidth():
            self.canvas.itemconfig(self.canvas_window, width=self.canvas.winfo_width())
    pass