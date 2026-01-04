import tkinter as tk
from tkinter import ttk, messagebox
import ttkbootstrap as tb
from PIL import Image, ImageTk, ImageDraw, ImageFont, ImageOps
import os
import threading
import logging
import math
from config import Config
logger = logging.getLogger(__name__)

class GridViewerWindow:

    def __init__(self, parent, app_controller):
        self.top = tk.Toplevel(parent)
        self.top.title('Matrix Viewer Pro - Revisão de Dataset')
        try:
            self.top.state('zoomed')
        except:
            w = self.top.winfo_screenwidth()
            h = self.top.winfo_screenheight()
            self.top.geometry(f'{w}x{h}')
        self.app = app_controller
        self.items_options = [8, 16, 24, 40]
        self.items_per_page = 8
        self.current_page = 0
        self.total_pages = 0
        self.card_size = 350
        self.cols_count = 4
        self.current_page_refs = []
        self.is_loading = False
        try:
            self.font_large = ImageFont.truetype('arialbd.ttf', 16)
            self.font_small = ImageFont.truetype('arial.ttf', 12)
        except:
            self.font_large = ImageFont.load_default()
            self.font_small = ImageFont.load_default()
        logger.info('Iniciando Grid Viewer v11.1 - Stable Fix')
        self._calculate_total_pages()
        self._create_layout()
        self.top.after(200, self._initial_load)
        self.top.bind('<Left>', lambda e: self.prev_page())
        self.top.bind('<Right>', lambda e: self.next_page())
        self.top.bind('<Configure>', self._on_window_resize)

    def _initial_load(self):
        self._recalc_layout_metrics()
        self._load_current_page()

    def _on_window_resize(self, event):
        if event.widget != self.top:
            return
        if hasattr(self, '_resize_timer'):
            self.top.after_cancel(self._resize_timer)
        self._resize_timer = self.top.after(500, self._refresh_on_resize)

    def _refresh_on_resize(self):
        self._recalc_layout_metrics()
        self._load_current_page()

    def _recalc_layout_metrics(self):
        screen_w = self.main_container.winfo_width()
        if screen_w < 100:
            screen_w = self.top.winfo_screenwidth()
        if self.items_per_page <= 8:
            self.cols_count = 4
        elif self.items_per_page <= 16:
            self.cols_count = 5
        elif self.items_per_page <= 24:
            self.cols_count = 6
        else:
            self.cols_count = 8
        new_size = screen_w // self.cols_count - 24
        new_size = max(120, min(new_size, 450))
        self.card_size = new_size

    def _calculate_total_pages(self):
        total_imgs = len(self.app.app_state.image_paths)
        if total_imgs == 0:
            self.total_pages = 1
        else:
            self.total_pages = math.ceil(total_imgs / self.items_per_page)
        if self.current_page >= self.total_pages:
            self.current_page = max(0, self.total_pages - 1)

    def _create_layout(self):
        header = ttk.Frame(self.top, padding=(20, 10), bootstyle='dark')
        header.pack(fill=tk.X)
        ttk.Label(header, text='VISUALIZAÇÃO ADAPTATIVA', font=('Impact', 16), bootstyle='inverse-dark').pack(side=tk.LEFT)
        frame_ctrl = ttk.Frame(header, bootstyle='dark')
        frame_ctrl.pack(side=tk.LEFT, padx=30)
        ttk.Label(frame_ctrl, text='Densidade (Itens):', bootstyle='inverse-dark').pack(side=tk.LEFT, padx=5)
        self.combo_qtd = ttk.Combobox(frame_ctrl, values=self.items_options, width=5, state='readonly', font=('Segoe UI', 10, 'bold'))
        self.combo_qtd.set(self.items_per_page)
        self.combo_qtd.pack(side=tk.LEFT)
        self.combo_qtd.bind('<<ComboboxSelected>>', self._on_change_grid_size)
        self.lbl_page_info = ttk.Label(header, text='Página 1', font=('Segoe UI', 12), bootstyle='inverse-dark')
        self.lbl_page_info.pack(side=tk.LEFT, padx=30)
        self.lbl_loading = ttk.Label(header, text='', bootstyle='warning-inverse')
        self.lbl_loading.pack(side=tk.RIGHT)
        self.main_container = ttk.Frame(self.top)
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.grid_frame = ttk.Frame(self.main_container)
        self.grid_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        footer = ttk.Frame(self.top, padding=10, bootstyle='secondary')
        footer.pack(fill=tk.X, side=tk.BOTTOM)
        self.btn_prev = ttk.Button(footer, text='◄ Anterior', command=self.prev_page, bootstyle='light-outline', width=15)
        self.btn_prev.pack(side=tk.LEFT, padx=20)
        self.btn_next = ttk.Button(footer, text='Próximo ►', command=self.next_page, bootstyle='light-outline', width=15)
        self.btn_next.pack(side=tk.RIGHT, padx=20)
        ttk.Label(footer, text='Navegue com as Setas do Teclado', font=('Segoe UI', 9), bootstyle='inverse-secondary').pack(side=tk.TOP)

    def _on_change_grid_size(self, event):
        try:
            new_val = int(self.combo_qtd.get())
            if new_val != self.items_per_page:
                self.items_per_page = new_val
                self.current_page = 0
                self._calculate_total_pages()
                self._recalc_layout_metrics()
                self._load_current_page()
        except:
            pass

    def _load_current_page(self):
        if self.is_loading:
            return
        self.is_loading = True
        self.lbl_loading.config(text='Processando Grid...')
        for widget in self.grid_frame.winfo_children():
            widget.destroy()
        threading.Thread(target=self._render_page_thread, daemon=True).start()

    def _render_page_thread(self):
        start_idx = self.current_page * self.items_per_page
        end_idx = start_idx + self.items_per_page
        paths = self.app.app_state.image_paths[start_idx:end_idx]
        prepared_cards = []
        class_names = self.app.app_state.class_names
        for idx, path in enumerate(paths):
            try:
                orig_img = Image.open(path)
                orig_w, orig_h = orig_img.size
                fmt = orig_img.format or 'UNK'
                size_kb = os.path.getsize(path) / 1024
                thumb_img = Image.new('RGB', (self.card_size, self.card_size), (25, 25, 25))
                img_copy = orig_img.copy().convert('RGB')
                img_copy.thumbnail((self.card_size, self.card_size), Image.Resampling.LANCZOS)
                paste_x = (self.card_size - img_copy.width) // 2
                paste_y = (self.card_size - img_copy.height) // 2
                thumb_img.paste(img_copy, (paste_x, paste_y))
                label_path = self.app.ann_manager.get_label_path(path)
                ann_count = 0
                if os.path.exists(label_path):
                    draw = ImageDraw.Draw(thumb_img)
                    with open(label_path, 'r') as f:
                        for line in f:
                            parts = line.strip().split()
                            if len(parts) >= 5:
                                ann_count += 1
                                cid = int(parts[0])
                                cx, cy, cw, ch = map(float, parts[1:5])
                                abs_cx = cx * img_copy.width + paste_x
                                abs_cy = cy * img_copy.height + paste_y
                                abs_w = cw * img_copy.width
                                abs_h = ch * img_copy.height
                                x1, y1 = (abs_cx - abs_w / 2, abs_cy - abs_h / 2)
                                x2, y2 = (abs_cx + abs_w / 2, abs_cy + abs_h / 2)
                                color = Config.CLASS_COLORS[cid % len(Config.CLASS_COLORS)]
                                draw.rectangle([x1, y1, x2, y2], outline=color, width=2)
                                cls_name = class_names[cid] if cid < len(class_names) else str(cid)
                                text_bbox = draw.textbbox((x1, y1), cls_name, font=self.font_small)
                                text_w = text_bbox[2] - text_bbox[0]
                                text_h = text_bbox[3] - text_bbox[1]
                                draw.rectangle([x1, y1 - text_h - 4, x1 + text_w + 4, y1], fill=color)
                                draw.text((x1 + 2, y1 - text_h - 4), cls_name, fill='black', font=self.font_small)
                prepared_cards.append({'pil': thumb_img, 'path': path, 'index': start_idx + idx, 'res': f'{orig_w}x{orig_h}', 'fmt': fmt, 'size': f'{size_kb:.0f} KB', 'ann_count': ann_count})
            except Exception as e:
                logger.error(f'Erro grid img {path}: {e}')
        self.top.after(0, lambda: self._draw_grid(prepared_cards))

    def _draw_grid(self, cards_data):
        self.current_page_refs.clear()
        for i, card in enumerate(cards_data):
            row = i // self.cols_count
            col = i % self.cols_count
            card_frame = ttk.Frame(self.grid_frame, bootstyle='secondary', padding=1)
            card_frame.grid(row=row, column=col, padx=4, pady=4)
            tk_img = ImageTk.PhotoImage(card['pil'])
            self.current_page_refs.append(tk_img)
            img_lbl = tk.Label(card_frame, image=tk_img, bg='#1e1e1e', cursor='hand2')
            img_lbl.pack()
            fname = os.path.basename(card['path'])
            tk.Label(card_frame, text=fname, font=('Segoe UI', 9, 'bold'), fg='#ffffff', bg='#333', anchor='center').pack(fill=tk.X)
            meta_frame = tk.Frame(card_frame, bg='#222')
            meta_frame.pack(fill=tk.X)
            center_meta = tk.Frame(meta_frame, bg='#222')
            center_meta.pack(anchor='center')
            tk.Label(center_meta, text=card['res'], fg='#00ffff', bg='#222', font=('Consolas', 7)).pack(side=tk.LEFT, padx=2)
            tk.Label(center_meta, text='|', fg='#555', bg='#222', font=('Consolas', 7)).pack(side=tk.LEFT)
            tk.Label(center_meta, text=card['fmt'], fg='#ff00ff', bg='#222', font=('Consolas', 7)).pack(side=tk.LEFT, padx=2)
            tk.Label(center_meta, text='|', fg='#555', bg='#222', font=('Consolas', 7)).pack(side=tk.LEFT)
            tk.Label(center_meta, text=card['size'], fg='#ffff00', bg='#222', font=('Consolas', 7)).pack(side=tk.LEFT, padx=2)
            if card['ann_count'] > 0:
                status_bg = '#155724'
                status_fg = '#d4edda'
                status_txt = f'✅ {card['ann_count']} Anotações'
            else:
                status_bg = '#721c24'
                status_fg = '#f8d7da'
                status_txt = '⚠ 0 Anotações'
            lbl_status = tk.Label(card_frame, text=status_txt, bg=status_bg, fg=status_fg, font=('Segoe UI', 8, 'bold'), anchor='center', justify='center')
            lbl_status.pack(fill=tk.X)
            img_lbl.bind('<Button-1>', lambda e, idx=card['index']: self._open_editor(idx))

            def on_enter(e, f=card_frame):
                f.configure(bootstyle='info')

            def on_leave(e, f=card_frame):
                f.configure(bootstyle='secondary')
            img_lbl.bind('<Enter>', on_enter)
            img_lbl.bind('<Leave>', on_leave)
        self.lbl_page_info.config(text=f'Página {self.current_page + 1} de {self.total_pages}')
        self.lbl_loading.config(text='')
        self.is_loading = False
        self._update_buttons()

    def _update_buttons(self):
        self.btn_prev.config(state='normal' if self.current_page > 0 else 'disabled')
        self.btn_next.config(state='normal' if self.current_page < self.total_pages - 1 else 'disabled')

    def next_page(self):
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self._load_current_page()

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self._load_current_page()

    def _open_editor(self, index):
        self.app.show_image_at_index(index)
        self.app.root.lift()