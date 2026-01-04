import tkinter as tk
from tkinter import ttk, simpledialog, messagebox, Listbox, filedialog
import os
import yaml
import logging
from PIL import Image, ImageTk
from typing import List, TYPE_CHECKING
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
if TYPE_CHECKING:
    from main import MainApplication
logger = logging.getLogger(__name__)

class ClassManagerWindow(tk.Toplevel):

    def __init__(self, master, class_list: List[str], callback: callable):
        super().__init__(master)
        self.title('Gerenciar Classes')
        self.geometry('400x450')
        self.transient(master)
        self.grab_set()
        self.class_list = class_list[:]
        self.callback = callback
        self.geometry('+%d+%d' % (master.winfo_rootx() + 50, master.winfo_rooty() + 50))
        fr = ttk.Frame(self, padding=10)
        fr.pack(fill=tk.BOTH, expand=True)
        self.lb = Listbox(fr)
        self.lb.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        for i in self.class_list:
            self.lb.insert(tk.END, i)
        btn_fr = ttk.Frame(fr)
        btn_fr.pack(fill=tk.X, pady=5)
        ttk.Button(btn_fr, text='Adicionar', command=self.add).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        ttk.Button(btn_fr, text='Renomear', command=self.edit).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        ttk.Button(btn_fr, text='Excluir', command=self.delete).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        ttk.Button(self, text='Salvar e Fechar', command=self.save, bootstyle='success').pack(pady=10, fill=tk.X, padx=10)

    def add(self):
        n = simpledialog.askstring('Nova Classe', 'Nome:')
        if n:
            self.class_list.append(n)
            self.lb.insert(tk.END, n)

    def edit(self):
        sel = self.lb.curselection()
        if not sel:
            return
        idx = sel[0]
        old = self.class_list[idx]
        new = simpledialog.askstring('Editar', 'Nome:', initialvalue=old)
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

class NewProjectWindow(tk.Toplevel):

    def __init__(self, master, cb):
        super().__init__(master)
        self.cb = cb
        self.title('Novo Projeto YOLO')
        self.geometry('500x350')
        self.path = ''
        self.geometry('+%d+%d' % (master.winfo_rootx() + 100, master.winfo_rooty() + 100))
        p = ttk.Frame(self, padding=20)
        p.pack(fill=tk.BOTH, expand=True)
        ttk.Label(p, text='Nome do Projeto:', font=('Segoe UI', 10, 'bold')).pack(anchor='w')
        self.e_name = ttk.Entry(p)
        self.e_name.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(p, text='Localização:', font=('Segoe UI', 10, 'bold')).pack(anchor='w')
        f_dir = ttk.Frame(p)
        f_dir.pack(fill=tk.X, pady=(0, 10))
        self.l_path = ttk.Label(f_dir, text='Nenhuma pasta selecionada', bootstyle='secondary', relief='sunken')
        self.l_path.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(f_dir, text='Browse', command=self.browse, bootstyle='info-outline').pack(side=tk.RIGHT)
        ttk.Label(p, text='Classes Iniciais (separadas por vírgula):', font=('Segoe UI', 10, 'bold')).pack(anchor='w')
        self.e_cls = ttk.Entry(p)
        self.e_cls.pack(fill=tk.X, pady=(0, 20))
        self.e_cls.insert(0, 'pessoa, carro, moto')
        ttk.Button(p, text='Criar Estrutura YOLO', command=self.create, bootstyle='success').pack(fill=tk.X, pady=10)

    def browse(self):
        self.path = filedialog.askdirectory()
        self.l_path.config(text=self.path)

    def create(self):
        name = self.e_name.get()
        cls = [x.strip() for x in self.e_cls.get().split(',') if x.strip()]
        if not name or not self.path:
            messagebox.showwarning('Aviso', 'Preencha o nome e selecione uma pasta.')
            return
        full = os.path.join(self.path, name)
        try:
            for s in ['train/images', 'train/labels', 'valid/images', 'valid/labels', 'test/images', 'test/labels']:
                os.makedirs(os.path.join(full, s), exist_ok=True)
            with open(os.path.join(full, 'classes.txt'), 'w') as f:
                f.write('\n'.join(cls))
            data_yaml = {'train': os.path.abspath(os.path.join(full, 'train/images')), 'val': os.path.abspath(os.path.join(full, 'valid/images')), 'nc': len(cls), 'names': cls}
            with open(os.path.join(full, 'data.yaml'), 'w') as f:
                yaml.dump(data_yaml, f)
            self.cb(full)
            self.destroy()
        except Exception as e:
            messagebox.showerror('Erro', str(e))

class SplitWizard(tk.Toplevel):

    def __init__(self, master, callback):
        super().__init__(master)
        self.callback = callback
        self.title('Assistente de Divisão de Dataset (Split)')
        self.geometry('700x500')
        self.resizable(False, False)
        self.geometry('+%d+%d' % (master.winfo_rootx() + 50, master.winfo_rooty() + 50))
        self.train_pct = tk.DoubleVar(value=80)
        self.val_pct = tk.DoubleVar(value=20)
        self.test_pct = tk.DoubleVar(value=0)
        self.shuffle = tk.BooleanVar(value=True)
        self.use_test_set = tk.BooleanVar(value=False)
        self._setup_ui()
        self._update_chart()

    def _setup_ui(self):
        main_frame = ttk.Frame(self, padding=15)
        main_frame.pack(fill=tk.BOTH, expand=True)
        ttk.Label(main_frame, text='Configurar Distribuição do Dataset', font=('Segoe UI', 14, 'bold')).pack(pady=(0, 10))
        ttk.Checkbutton(main_frame, text='Incluir Conjunto de Teste (Test Set)', variable=self.use_test_set, command=self._toggle_test_set, bootstyle='round-toggle').pack(pady=(0, 15))
        content = ttk.Frame(main_frame)
        content.pack(fill=tk.BOTH, expand=True)
        left_panel = ttk.Frame(content)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        ttk.Label(left_panel, text='Treino (Train)', bootstyle='primary').pack(anchor='w')
        self.lbl_train = ttk.Label(left_panel, text='80%', font=('Segoe UI', 10, 'bold'), foreground='#007bff')
        self.lbl_train.pack(anchor='w')
        self.scale_train = ttk.Scale(left_panel, from_=0, to=100, variable=self.train_pct, command=self._on_train_change, bootstyle='primary')
        self.scale_train.pack(fill=tk.X, pady=(0, 15))
        ttk.Label(left_panel, text='Validação (Val)', bootstyle='warning').pack(anchor='w')
        self.lbl_val = ttk.Label(left_panel, text='20%', font=('Segoe UI', 10, 'bold'), foreground='#ffc107')
        self.lbl_val.pack(anchor='w')
        self.scale_val = ttk.Scale(left_panel, from_=0, to=100, variable=self.val_pct, command=self._on_val_change, bootstyle='warning')
        self.scale_val.pack(fill=tk.X, pady=(0, 15))
        self.lbl_test_title = ttk.Label(left_panel, text='Teste (Test)', bootstyle='secondary')
        self.lbl_test_title.pack(anchor='w')
        self.lbl_test = ttk.Label(left_panel, text='0% (Desativado)', font=('Segoe UI', 12, 'bold'), foreground='#6c757d')
        self.lbl_test.pack(anchor='w', pady=(0, 20))
        ttk.Checkbutton(left_panel, text='Embaralhar (Shuffle)', variable=self.shuffle, bootstyle='round-toggle').pack(anchor='w', pady=10)
        right_panel = ttk.Frame(content, width=320)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        self.fig = plt.Figure(figsize=(3, 3), dpi=100)
        self.fig.patch.set_facecolor('#2b2b2b')
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor('#2b2b2b')
        self.canvas = FigureCanvasTkAgg(self.fig, master=right_panel)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        ttk.Button(main_frame, text='APLICAR DIVISÃO', command=self.apply, bootstyle='success').pack(fill=tk.X, pady=10)

    def _toggle_test_set(self):
        if self.use_test_set.get():
            self.lbl_test_title.configure(bootstyle='success')
            self.lbl_test.configure(foreground='#28a745')
            current_val = self.val_pct.get()
            if current_val > 10:
                self.val_pct.set(current_val - 10)
                self.test_pct.set(10)
            else:
                self.train_pct.set(self.train_pct.get() - 10)
                self.test_pct.set(10)
        else:
            self.lbl_test_title.configure(bootstyle='secondary')
            self.lbl_test.configure(foreground='#6c757d', text='DESATIVADO')
            self.test_pct.set(0)
            t = self.train_pct.get()
            self.val_pct.set(100 - t)
        self._update_ui_values()

    def _on_train_change(self, val):
        t = int(float(val))
        if self.use_test_set.get():
            v = int(self.val_pct.get())
            if t + v > 100:
                v = 100 - t
                self.val_pct.set(v)
        else:
            self.val_pct.set(100 - t)
        self._update_ui_values()

    def _on_val_change(self, val):
        v = int(float(val))
        if self.use_test_set.get():
            t = int(self.train_pct.get())
            if t + v > 100:
                t = 100 - v
                self.train_pct.set(t)
        else:
            self.train_pct.set(100 - v)
        self._update_ui_values()

    def _update_ui_values(self):
        t = int(self.train_pct.get())
        v = int(self.val_pct.get())
        if self.use_test_set.get():
            test = 100 - t - v
            self.test_pct.set(test)
            self.lbl_test.config(text=f'{test}%')
        else:
            self.test_pct.set(0)
            self.lbl_test.config(text='0% (Desativado)')
        self.lbl_train.config(text=f'{t}%')
        self.lbl_val.config(text=f'{v}%')
        self._update_chart()

    def _update_chart(self):
        t = self.train_pct.get()
        v = self.val_pct.get()
        te = self.test_pct.get()
        self.ax.clear()
        if self.use_test_set.get():
            sizes = [t, v, te]
            labels = ['Train', 'Val', 'Test']
            colors = ['#007bff', '#ffc107', '#28a745']
            explode = (0.05, 0, 0)
        else:
            sizes = [t, v]
            labels = ['Train', 'Val']
            colors = ['#007bff', '#ffc107']
            explode = (0.05, 0)
        final_sizes = []
        final_labels = []
        final_colors = []
        final_explode = []
        for i, s in enumerate(sizes):
            if s > 0:
                final_sizes.append(s)
                final_labels.append(labels[i])
                final_colors.append(colors[i])
                final_explode.append(explode[i])
        if final_sizes:
            self.ax.pie(final_sizes, labels=final_labels, autopct='%1.1f%%', startangle=90, colors=final_colors, explode=final_explode, pctdistance=0.85, textprops=dict(color='white'))
            centre_circle = plt.Circle((0, 0), 0.7, fc='#2b2b2b')
            self.ax.add_artist(centre_circle)
        self.ax.axis('equal')
        self.canvas.draw()

    def apply(self):
        t = self.train_pct.get() / 100
        v = self.val_pct.get() / 100
        te = self.test_pct.get() / 100 if self.use_test_set.get() else 0.0
        shuff = self.shuffle.get()
        total = t + v + te
        if abs(total - 1.0) > 0.01:
            messagebox.showerror('Erro', 'A soma das porcentagens não é 100%. Ajuste os sliders.')
            return
        self.callback(t, v, te, shuff)
        self.destroy()