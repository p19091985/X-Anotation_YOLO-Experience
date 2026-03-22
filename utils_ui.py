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
    window.geometry(f'+{x}+{y}')

def maximize_window(window):
    try:
        if window.tk.call('tk', 'windowingsystem') == 'win32':
            window.state('zoomed')
        else:
            window.attributes('-zoomed', True)
    except Exception:
        try:
            window.state('zoomed')
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

class ToolTip:

    def __init__(self, widget, text=''):
        self.widget = widget
        self.text = text
        self.tip_window = None
        self.after_id = None
        self.widget.bind('<Enter>', self.enter, add='+')
        self.widget.bind('<Leave>', self.leave, add='+')
        self.widget.bind('<ButtonPress>', self.leave, add='+')

    def update_text(self, text):
        self.text = text or ''
        if self.tip_window and not self.text:
            self.hide_tip()

    def enter(self, event=None):
        if not self.text:
            return
        self.unschedule()
        self.after_id = self.widget.after(400, self.show_tip)

    def leave(self, event=None):
        self.unschedule()
        self.hide_tip()

    def unschedule(self):
        if self.after_id:
            self.widget.after_cancel(self.after_id)
            self.after_id = None

    def show_tip(self):
        if self.tip_window or not self.text:
            return
        x = self.widget.winfo_rootx() + 16
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 8
        self.tip_window = tip = tk.Toplevel(self.widget)
        tip.wm_overrideredirect(True)
        tip.wm_geometry(f'+{x}+{y}')
        try:
            tip.attributes('-topmost', True)
        except Exception:
            pass
        label = tk.Label(
            tip,
            text=self.text,
            justify='left',
            background='#FFF7D6',
            foreground='black',
            relief='solid',
            borderwidth=1,
            wraplength=320,
            padx=6,
            pady=4
        )
        label.pack()

    def hide_tip(self):
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None
