import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import ttkbootstrap as tb
import os
import stat
import time
from collections import Counter
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.ticker import ScalarFormatter
import threading
import datetime
import logging
from PIL import Image
logger = logging.getLogger(__name__)

class DatasetAnalyzerWindow:

    def __init__(self, parent, base_dir, class_names):
        try:
            self.top = tk.Toplevel(parent)
            self.top.title('Análise Forense do Dataset - God Mode')
            try:
                self.top.state('zoomed')
            except:
                w, h = (self.top.winfo_screenwidth(), self.top.winfo_screenheight())
                self.top.geometry(f'{w}x{h}')
            self.base_dir = base_dir
            self.class_names = class_names
            self.stats = {'counts': Counter(), 'total_images': 0, 'total_objects': 0, 'split': {'train': {'img': 0, 'obj': 0}, 'val': {'img': 0, 'obj': 0}, 'test': {'img': 0, 'obj': 0}, 'uncategorized': {'img': 0, 'obj': 0}}, 'integrity': {'imgs_no_lbl': [], 'lbls_no_img': []}}
            self.detailed_files = []
            self.tree_structure = ''
            self.generated_report_text = ''
            self.fig_standard = None
            self.fig_log = None
            self.fig_split_img = None
            self.fig_split_obj = None
            logger.info(f'Iniciando Análise Forense em: {base_dir}')
            self._create_layout()
            self._start_analysis()
        except Exception as e:
            logger.error(f'Erro crítico ao inicializar analisador: {e}')
            messagebox.showerror('Erro', f'Falha ao abrir analisador: {e}')

    def _create_layout(self):
        header = ttk.Frame(self.top, padding=10)
        header.pack(fill=tk.X)
        ttk.Label(header, text=f'DETALHAMENTO TÉCNICO: {os.path.basename(self.base_dir)}', font=('Impact', 14), bootstyle='inverse-primary').pack(side=tk.LEFT, padx=5)
        self.lbl_status = ttk.Label(header, text='Inicializando varredura...', bootstyle='warning')
        self.lbl_status.pack(side=tk.RIGHT, padx=10)
        self.notebook = ttk.Notebook(self.top)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.tab_report = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_report, text='📑 Relatório Técnico')
        self.tab_dashboard = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_dashboard, text='📊 Classes & Resumo')
        self.tab_log = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_log, text='📈 Distribuição (Colunas)')
        self.tab_split = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_split, text='📊 Distribuição do Split')
        self.tab_integrity = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_integrity, text='⚠️ Integridade & Órfãos')
        self._build_report_tab()
        self._build_dashboard_tab()
        self._build_log_tab()
        self._build_split_tab()
        self._build_integrity_tab()

    def _build_dashboard_tab(self):
        pane = ttk.PanedWindow(self.tab_dashboard, orient=tk.HORIZONTAL)
        pane.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        left_frame = ttk.Labelframe(pane, text='Resumo de Classes', padding=10)
        pane.add(left_frame, weight=1)
        cols = ('ID', 'Classe', 'Qtd', 'Pct', 'Barra')
        self.tree = ttk.Treeview(left_frame, columns=cols, show='headings', selectmode='browse')
        self.tree.heading('ID', text='ID')
        self.tree.heading('Classe', text='Classe')
        self.tree.heading('Qtd', text='Objetos')
        self.tree.heading('Pct', text='%')
        self.tree.heading('Barra', text='Distribuição')
        self.tree.column('ID', width=40, anchor='center')
        self.tree.column('Classe', width=120, anchor='w')
        self.tree.column('Qtd', width=60, anchor='center')
        self.tree.column('Pct', width=60, anchor='center')
        self.tree.column('Barra', width=100, anchor='w')
        sb = ttk.Scrollbar(left_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        right_main_frame = ttk.Frame(pane)
        pane.add(right_main_frame, weight=2)
        chart_toolbar = ttk.Frame(right_main_frame)
        chart_toolbar.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(chart_toolbar, text='Visualização Padrão', font=('Segoe UI', 10, 'bold')).pack(side=tk.LEFT)
        ttk.Button(chart_toolbar, text='📷 Salvar Imagem', command=lambda: self.save_chart_image('standard'), bootstyle='primary').pack(side=tk.RIGHT)
        self.chart_frame = ttk.Frame(right_main_frame)
        self.chart_frame.pack(fill=tk.BOTH, expand=True)

    def _build_log_tab(self):
        toolbar_frame = ttk.Frame(self.tab_log, padding=(10, 5))
        toolbar_frame.pack(fill=tk.X)
        ttk.Label(toolbar_frame, text='Análise de Distribuição (Colunas Normais)', font=('Segoe UI', 11, 'bold')).pack(side=tk.LEFT)
        ttk.Button(toolbar_frame, text='📷 Salvar Imagem', command=lambda: self.save_chart_image('log'), bootstyle='primary').pack(side=tk.RIGHT)
        self.log_chart_frame = ttk.Frame(self.tab_log, padding=10)
        self.log_chart_frame.pack(fill=tk.BOTH, expand=True)

    def _build_split_tab(self):
        toolbar_frame = ttk.Frame(self.tab_split, padding=(10, 5))
        toolbar_frame.pack(fill=tk.X)
        ttk.Label(toolbar_frame, text='Divisão do Dataset (Train / Val / Test)', font=('Segoe UI', 11, 'bold')).pack(side=tk.LEFT)
        ttk.Button(toolbar_frame, text='📷 Salvar Gráficos', command=lambda: self.save_chart_image('split'), bootstyle='primary').pack(side=tk.RIGHT)
        split_content = ttk.Frame(self.tab_split, padding=10)
        split_content.pack(fill=tk.BOTH, expand=True)
        self.split_img_frame = ttk.LabelFrame(split_content, text='Imagens por Split', padding=5)
        self.split_img_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        self.split_obj_frame = ttk.LabelFrame(split_content, text='Anotações (Objetos) por Split', padding=5)
        self.split_obj_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))

    def _build_integrity_tab(self):
        pane = ttk.PanedWindow(self.tab_integrity, orient=tk.HORIZONTAL)
        pane.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        left_fr = ttk.LabelFrame(pane, text='Imagens sem Anotações (ou vazias)', padding=5, bootstyle='danger')
        pane.add(left_fr, weight=1)
        cols = ('Arquivo', 'Caminho')
        self.tree_no_lbl = ttk.Treeview(left_fr, columns=cols, show='headings')
        self.tree_no_lbl.heading('Arquivo', text='Nome do Arquivo')
        self.tree_no_lbl.heading('Caminho', text='Pasta')
        self.tree_no_lbl.column('Arquivo', width=150)
        sb1 = ttk.Scrollbar(left_fr, orient=tk.VERTICAL, command=self.tree_no_lbl.yview)
        self.tree_no_lbl.configure(yscrollcommand=sb1.set)
        self.tree_no_lbl.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb1.pack(side=tk.RIGHT, fill=tk.Y)
        right_fr = ttk.LabelFrame(pane, text='Anotações sem Imagens (Órfãs)', padding=5, bootstyle='warning')
        pane.add(right_fr, weight=1)
        self.tree_no_img = ttk.Treeview(right_fr, columns=cols, show='headings')
        self.tree_no_img.heading('Arquivo', text='Nome do Arquivo (.txt)')
        self.tree_no_img.heading('Caminho', text='Pasta')
        self.tree_no_img.column('Arquivo', width=150)
        sb2 = ttk.Scrollbar(right_fr, orient=tk.VERTICAL, command=self.tree_no_img.yview)
        self.tree_no_img.configure(yscrollcommand=sb2.set)
        self.tree_no_img.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb2.pack(side=tk.RIGHT, fill=tk.Y)

    def _build_report_tab(self):
        toolbar = ttk.Frame(self.tab_report, padding=5)
        toolbar.pack(fill=tk.X)
        ttk.Button(toolbar, text='📋 Copiar Tudo', command=self.copy_to_clipboard, bootstyle='info').pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text='💾 Exportar CSV/TXT', command=self.save_report_file, bootstyle='success').pack(side=tk.LEFT, padx=5)
        ttk.Label(toolbar, text=' (A saída inclui árvore de diretórios ao final)', font=('Segoe UI', 8, 'italic')).pack(side=tk.LEFT, padx=10)
        self.txt_report = tk.Text(self.tab_report, wrap=tk.NONE, font=('Consolas', 9), bg='#1e1e1e', fg='#e0e0e0')
        self.txt_report.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        ys = ttk.Scrollbar(self.txt_report, orient='vertical', command=self.txt_report.yview)
        xs = ttk.Scrollbar(self.txt_report, orient='horizontal', command=self.txt_report.xview)
        self.txt_report.configure(yscrollcommand=ys.set, xscrollcommand=xs.set)
        ys.pack(side=tk.RIGHT, fill=tk.Y)
        xs.pack(side=tk.BOTTOM, fill=tk.X)
        self.txt_report.tag_config('header', foreground='#00ffff', font=('Consolas', 10, 'bold'))
        self.txt_report.tag_config('section', foreground='#ff00ff', font=('Consolas', 10, 'bold'))
        self.txt_report.tag_config('error', foreground='#ff5555')
        self.txt_report.tag_config('tree', foreground='#00ff00')

    def _start_analysis(self):
        self.lbl_status.config(text='Varrendo metadados (isso pode demorar)...', bootstyle='warning')
        threading.Thread(target=self._analyze_data, daemon=True).start()

    def _get_file_attributes(self, filepath):
        attrs = []
        try:
            st = os.stat(filepath)
            if os.name == 'nt':
                import ctypes
                attr = ctypes.windll.kernel32.GetFileAttributesW(filepath)
                if attr != -1 and attr & 2:
                    attrs.append('HIDDEN')
            if not st.st_mode & stat.S_IWUSR:
                attrs.append('READ-ONLY')
        except:
            pass
        return ','.join(attrs) if attrs else 'NORMAL'

    def _generate_tree_string(self, dir_path, prefix=''):
        output = ''
        try:
            items = sorted(os.listdir(dir_path))
            pointers = [('├── ', '│   ')] * (len(items) - 1) + [('└── ', '    ')]
            for pointer, item in zip(pointers, items):
                path = os.path.join(dir_path, item)
                output += prefix + pointer[0] + item + '\n'
                if os.path.isdir(path):
                    output += self._generate_tree_string(path, prefix + pointer[1])
        except PermissionError:
            output += prefix + '└── [Acesso Negado]\n'
        return output

    def _analyze_data(self):
        try:
            self.stats['counts'] = Counter()
            self.stats['total_images'] = 0
            self.stats['total_objects'] = 0
            for k in self.stats['split']:
                self.stats['split'][k] = {'img': 0, 'obj': 0}
            self.stats['integrity']['imgs_no_lbl'] = []
            self.stats['integrity']['lbls_no_img'] = []
            all_images_bases = set()
            all_labels_bases = set()
            for r, _, files in os.walk(self.base_dir):
                if 'labels' in r:
                    continue
                path_lower = r.lower()
                split_cat = 'uncategorized'
                if 'train' in path_lower:
                    split_cat = 'train'
                elif 'valid' in path_lower or 'val' in path_lower:
                    split_cat = 'val'
                elif 'test' in path_lower:
                    split_cat = 'test'
                for f in sorted(files):
                    lower_f = f.lower()
                    if lower_f.endswith(('.jpg', '.png', '.jpeg', '.bmp', '.gif', '.tiff')):
                        full_path = os.path.join(r, f)
                        base_name = os.path.splitext(f)[0]
                        all_images_bases.add(base_name)
                        try:
                            file_stat = os.stat(full_path)
                            size_kb = file_stat.st_size / 1024
                            created_dt = datetime.datetime.fromtimestamp(file_stat.st_ctime).strftime('%Y-%m-%d %H:%M:%S')
                            mod_dt = datetime.datetime.fromtimestamp(file_stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                            attrs = self._get_file_attributes(full_path)
                            with Image.open(full_path) as img:
                                width, height = img.size
                                img_format = img.format
                                img_mode = img.mode
                                label_name = base_name + '.txt'
                                possible_lbls = [os.path.join(os.path.dirname(r), 'labels', label_name), os.path.join(r, label_name)]
                                classes_in_img = []
                                ann_count = 0
                                found_label = False
                                for lbl_path in possible_lbls:
                                    if os.path.exists(lbl_path):
                                        found_label = True
                                        with open(lbl_path, 'r') as lf:
                                            for line in lf:
                                                parts = line.split()
                                                if len(parts) >= 1:
                                                    cid = int(parts[0])
                                                    self.stats['counts'][cid] += 1
                                                    classes_in_img.append(cid)
                                                    ann_count += 1
                                        break
                                self.stats['total_images'] += 1
                                self.stats['total_objects'] += ann_count
                                self.stats['split'][split_cat]['img'] += 1
                                self.stats['split'][split_cat]['obj'] += ann_count
                                if ann_count == 0:
                                    self.stats['integrity']['imgs_no_lbl'].append(full_path)
                                unique_classes = sorted(list(set(classes_in_img)))
                                classes_str = ','.join([str(c) for c in unique_classes]) if unique_classes else 'None'
                                self.detailed_files.append({'name': f, 'res': f'{width}x{height}', 'fmt': img_format, 'mode': img_mode, 'size_kb': f'{size_kb:.2f}', 'created': created_dt, 'mod': mod_dt, 'attrs': attrs, 'anns': ann_count, 'classes': classes_str, 'path': full_path})
                        except Exception as e:
                            self.detailed_files.append({'name': f, 'res': 'ERROR', 'path': full_path + f' [Error: {str(e)}]'})
            for r, _, files in os.walk(self.base_dir):
                for f in files:
                    if f.lower().endswith('.txt') and f.lower() != 'classes.txt':
                        base_name = os.path.splitext(f)[0]
                        all_labels_bases.add(base_name)
                        if base_name not in all_images_bases:
                            self.stats['integrity']['lbls_no_img'].append(os.path.join(r, f))
            self.tree_structure = f'.\n{self._generate_tree_string(self.base_dir)}'
            self.top.after(0, self._update_ui)
        except Exception as e:
            logger.error(f'Erro na thread de análise: {e}')
            self.top.after(0, lambda: messagebox.showerror('Erro de Análise', str(e)))

    def _update_ui(self):
        try:
            self.lbl_status.config(text='Gerando gráficos e relatórios...', bootstyle='info')
            counts = self.stats['counts']
            tot_obj = self.stats['total_objects']
            for i in self.tree.get_children():
                self.tree.delete(i)
            sorted_ids = sorted(counts.keys())
            all_ids = set(sorted_ids) | set(range(len(self.class_names)))
            labels_chart = []
            values_chart = []
            for cid in sorted(all_ids):
                count = counts.get(cid, 0)
                name = self.class_names[cid] if cid < len(self.class_names) else f'ID {cid}'
                pct_val = count / tot_obj * 100 if tot_obj > 0 else 0.0
                bar_len = int(pct_val / 5)
                self.tree.insert('', 'end', values=(cid, name, count, f'{pct_val:.2f}%', '█' * bar_len))
                if count > 0:
                    labels_chart.append(name)
                    values_chart.append(count)
            self._draw_chart(labels_chart, values_chart)
            if labels_chart:
                sorted_data = sorted(zip(labels_chart, values_chart), key=lambda x: x[1])
                log_labels = [x[0] for x in sorted_data]
                log_values = [x[1] for x in sorted_data]
                self._draw_log_chart(log_labels, log_values)
            self._draw_split_charts()
            for i in self.tree_no_lbl.get_children():
                self.tree_no_lbl.delete(i)
            for i in self.tree_no_img.get_children():
                self.tree_no_img.delete(i)
            for path in self.stats['integrity']['imgs_no_lbl']:
                self.tree_no_lbl.insert('', 'end', values=(os.path.basename(path), os.path.dirname(path)))
            for path in self.stats['integrity']['lbls_no_img']:
                self.tree_no_img.insert('', 'end', values=(os.path.basename(path), os.path.dirname(path)))
            self._generate_text_report()
            self.lbl_status.config(text='Análise Completa.', bootstyle='success')
        except Exception as e:
            logger.error(f'Erro ao atualizar UI: {e}')
            messagebox.showerror('Erro de Renderização', str(e))

    def _draw_split_charts(self):
        splits = ['train', 'val', 'test']
        img_counts = [self.stats['split'][s]['img'] for s in splits]
        obj_counts = [self.stats['split'][s]['obj'] for s in splits]
        colors = ['#007bff', '#ffc107', '#28a745']
        for w in self.split_img_frame.winfo_children():
            w.destroy()
        self.fig_split_img, ax1 = plt.subplots(figsize=(4, 4), dpi=100)
        self.fig_split_img.patch.set_facecolor('#2b2b2b')
        ax1.set_facecolor('#2b2b2b')
        bars1 = ax1.bar(splits, img_counts, color=colors)
        ax1.set_title('Imagens por Split', color='white')
        ax1.tick_params(colors='white')
        ax1.spines['bottom'].set_color('white')
        ax1.spines['left'].set_color('white')
        ax1.spines['top'].set_visible(False)
        ax1.spines['right'].set_visible(False)
        for bar in bars1:
            h = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width() / 2, h, str(h), ha='center', va='bottom', color='white', fontweight='bold')
        canvas1 = FigureCanvasTkAgg(self.fig_split_img, master=self.split_img_frame)
        canvas1.draw()
        canvas1.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        for w in self.split_obj_frame.winfo_children():
            w.destroy()
        self.fig_split_obj, ax2 = plt.subplots(figsize=(4, 4), dpi=100)
        self.fig_split_obj.patch.set_facecolor('#2b2b2b')
        ax2.set_facecolor('#2b2b2b')
        bars2 = ax2.bar(splits, obj_counts, color=colors)
        ax2.set_title('Objetos (Anotações) por Split', color='white')
        ax2.tick_params(colors='white')
        ax2.spines['bottom'].set_color('white')
        ax2.spines['left'].set_color('white')
        ax2.spines['top'].set_visible(False)
        ax2.spines['right'].set_visible(False)
        for bar in bars2:
            h = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width() / 2, h, str(h), ha='center', va='bottom', color='white', fontweight='bold')
        canvas2 = FigureCanvasTkAgg(self.fig_split_obj, master=self.split_obj_frame)
        canvas2.draw()
        canvas2.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def _draw_chart(self, labels, values):
        for widget in self.chart_frame.winfo_children():
            widget.destroy()
        if not values:
            return
        plt.style.use('dark_background')
        self.fig_standard, ax = plt.subplots(figsize=(5, 4), dpi=100)
        self.fig_standard.patch.set_facecolor('#2b2b2b')
        ax.set_facecolor('#2b2b2b')
        colors = plt.cm.plasma(range(len(labels)))
        ax.barh(labels, values, color=colors)
        ax.set_xlabel('Quantidade')
        ax.set_title('Distribuição (Linear)')
        for i, v in enumerate(values):
            ax.text(v, i, f' {v}', color='white', va='center', fontweight='bold')
        plt.tight_layout()
        canvas = FigureCanvasTkAgg(self.fig_standard, master=self.chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def _draw_log_chart(self, labels, values):
        for widget in self.log_chart_frame.winfo_children():
            widget.destroy()
        if not values:
            return
        plt.style.use('dark_background')
        self.fig_log, ax = plt.subplots(figsize=(12, 6), dpi=100)
        self.fig_log.patch.set_facecolor('#2b2b2b')
        ax.set_facecolor('#2b2b2b')
        formatter = ScalarFormatter()
        formatter.set_scientific(False)
        ax.yaxis.set_major_formatter(formatter)
        ax.grid(axis='y', linestyle='-', alpha=0.3, color='white')
        ax.set_axisbelow(True)
        colors = plt.cm.Set3(range(len(labels)))
        bars = ax.bar(labels, values, color=colors, edgecolor='#dddddd', linewidth=0.5)
        ax.set_ylabel('Nº de Anotações', fontsize=12, color='white')
        ax.set_xlabel('Classe', fontsize=12, color='white')
        ax.set_title('Distribuição de Anotações (Colunas Normais)', fontsize=16, color='white', pad=20)
        plt.xticks(rotation=45, ha='right', fontsize=10, color='white')
        plt.yticks(color='white')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_color('white')
        ax.spines['left'].set_color('white')
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2.0, height + max(values) * 0.01, f'{int(height)}', ha='center', va='bottom', color='white', fontsize=9, fontweight='bold')
        plt.tight_layout()
        canvas = FigureCanvasTkAgg(self.fig_log, master=self.log_chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def save_chart_image(self, chart_type):
        target_fig = None
        if chart_type == 'standard':
            target_fig = self.fig_standard
        elif chart_type == 'log':
            target_fig = self.fig_log
        elif chart_type == 'split':
            if self.fig_split_img and self.fig_split_obj:
                try:
                    f1 = filedialog.asksaveasfilename(defaultextension='.png', initialfile=f'split_img_{int(time.time())}.png', title='Salvar Gráfico Imagens')
                    if f1:
                        self.fig_split_img.savefig(f1, dpi=300, bbox_inches='tight')
                    f2 = filedialog.asksaveasfilename(defaultextension='.png', initialfile=f'split_obj_{int(time.time())}.png', title='Salvar Gráfico Objetos')
                    if f2:
                        self.fig_split_obj.savefig(f2, dpi=300, bbox_inches='tight')
                    messagebox.showinfo('Sucesso', 'Gráficos salvos.')
                except Exception as e:
                    messagebox.showerror('Erro', str(e))
            return
        if target_fig is None:
            messagebox.showwarning('Aviso', 'O gráfico ainda não foi gerado.')
            return
        default_name = f'grafico_{chart_type}_{int(time.time())}.png'
        filename = filedialog.asksaveasfilename(defaultextension='.png', initialfile=default_name, filetypes=[('PNG Image', '*.png')], title=f'Salvar Gráfico ({chart_type})')
        if filename:
            try:
                target_fig.savefig(filename, dpi=300, bbox_inches='tight')
                messagebox.showinfo('Sucesso', f'Gráfico salvo em:\n{filename}')
            except Exception as e:
                messagebox.showerror('Erro', str(e))

    def copy_to_clipboard(self):
        self.top.clipboard_clear()
        self.top.clipboard_append(self.generated_report_text)
        self.top.update()
        messagebox.showinfo('Clipboard', 'Relatório copiado.')

    def save_report_file(self):
        if not self.generated_report_text:
            return
        filename = filedialog.asksaveasfilename(defaultextension='.txt', filetypes=[('TXT', '*.txt')], title='Salvar Relatório')
        if filename:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(self.generated_report_text)
            messagebox.showinfo('Salvo', f'Relatório salvo em:\n{filename}')

    def _generate_text_report(self):
        timestamp = datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        report = []
        report.append('=' * 120)
        report.append(f'RELATÓRIO DE ANALISE FORENSE - DATASET YOLO')
        report.append(f'Gerado em: {timestamp}')
        report.append(f'Diretório Base: {self.base_dir}')
        report.append('=' * 120 + '\n')
        report.append('[RESUMO ESTATÍSTICO]')
        report.append(f'Total Imagens: {self.stats['total_images']}')
        report.append(f'Total Objetos: {self.stats['total_objects']}')
        report.append(f'Média Objetos/Img: {self.stats['total_objects'] / self.stats['total_images']:.2f}' if self.stats['total_images'] > 0 else '0')
        report.append('\n[DISTRIBUIÇÃO SPLIT]')
        for k, v in self.stats['split'].items():
            report.append(f'  {k.upper()}: {v['img']} imagens, {v['obj']} objetos')
        report.append('\n[PROBLEMAS DE INTEGRIDADE]')
        report.append(f'  Imagens sem anotação: {len(self.stats['integrity']['imgs_no_lbl'])}')
        report.append(f'  Anotações sem imagem: {len(self.stats['integrity']['lbls_no_img'])}')
        report.append('-' * 40 + '\n')
        report.append('[DETALHAMENTO ARQUIVO A ARQUIVO]')
        header = f'{'ARQUIVO':<25} | {'RES':<10} | {'ANNS':<4} | {'CLASSES':<10} | {'CAMINHO'}'
        report.append(header)
        report.append('-' * len(header))
        for item in self.detailed_files:
            line = f'{item['name'][:25]:<25} | {item['res']:<10} | {str(item['anns']):<4} | {item['classes']:<10} | {item['path']}'
            report.append(line)
        report.append('\n' + '=' * 120 + '\n')
        report.append('[ESTRUTURA DE DIRETÓRIOS]')
        report.append(self.tree_structure)
        self.generated_report_text = '\n'.join(report)
        self.txt_report.delete('1.0', tk.END)
        self.txt_report.insert('1.0', self.generated_report_text)