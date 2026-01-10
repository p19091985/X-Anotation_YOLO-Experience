import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk, ImageDraw, ImageFont
import os
import threading
import logging
import math
from config import Config
from utils_ui import log_errors
import localization
logger = logging.getLogger(__name__)

class GridViewerWindow:

    def __init__(self, parent, app_controller):
        self.top = tk.Toplevel(parent)
        self.top.title(localization.tr('TITLE_GRID_VIEWER'))
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
        self.font_scale = 12
        self.last_win_size = (0, 0)
        try:
            self.font_base_path_bd = 'arialbd.ttf'
            self.font_base_path = 'arial.ttf'
            ImageFont.truetype(self.font_base_path, 12)
        except:
            self.font_base_path_bd = None
            self.font_base_path = None
        logger.info(localization.tr('MSG_INIT_GRID'))
        self._calculate_total_pages()
        self._create_layout()
        self.top.after(200, self._initial_load)
        self.top.bind('<Left>', lambda e: self.prev_page())
        self.top.bind('<Right>', lambda e: self.next_page())
        self.top.bind('<Configure>', self._on_window_configure)

    def _initial_load(self):
        self.last_win_size = (self.top.winfo_width(), self.top.winfo_height())
        self._recalc_layout_metrics()
        self._load_current_page()

    def _on_window_configure(self, event):
        if event.widget != self.top:
            return
        current_width = event.width
        current_height = event.height
        if (current_width, current_height) == self.last_win_size:
            return
        self.last_win_size = (current_width, current_height)
        if hasattr(self, '_resize_timer'):
            self.top.after_cancel(self._resize_timer)
        self._resize_timer = self.top.after(300, self._refresh_on_resize)

    def _refresh_on_resize(self):
        self._recalc_layout_metrics()
        self._load_current_page()

    def _recalc_layout_metrics(self):
        screen_w = self.main_container.winfo_width()
        screen_h = self.main_container.winfo_height() - 25
        if screen_w < 100 or screen_h < 100:
            return
        n_items = self.items_per_page
        best_card_size = 0
        best_cols = 4
        gap = 10
        text_space = 110
        for c in range(1, n_items + 1):
            r = math.ceil(n_items / c)
            w_avail = (screen_w - c * gap) // c
            h_avail = (screen_h - r * gap) // r - text_space
            possible_size = min(w_avail, h_avail)
            if possible_size > best_card_size:
                best_card_size = possible_size
                best_cols = c
        self.cols_count = best_cols
        self.card_size = max(120, best_card_size)
        self.font_scale = max(10, int(self.card_size / 22))

    def _calculate_total_pages(self):
        total_imgs = len(self.app.app_state.image_paths)
        if total_imgs == 0:
            self.total_pages = 1
        else:
            self.total_pages = math.ceil(total_imgs / self.items_per_page)
        if self.current_page >= self.total_pages:
            self.current_page = max(0, self.total_pages - 1)

    def _create_layout(self):
        header = ttk.Frame(self.top, padding=(20, 10))
        header.pack(fill=tk.X)
        ttk.Label(header, text=localization.tr('LBL_GRID_HEADER'), font=Config.FONTS['header']).pack(side=tk.LEFT)
        frame_ctrl = ttk.Frame(header)
        frame_ctrl.pack(side=tk.LEFT, padx=30)
        ttk.Label(frame_ctrl, text=localization.tr('LBL_ITEMS_PER_PAGE')).pack(side=tk.LEFT, padx=5)
        self.combo_qtd = ttk.Combobox(frame_ctrl, values=self.items_options, width=5, state='readonly', font=Config.FONTS['main_bold'])
        self.combo_qtd.set(self.items_per_page)
        self.combo_qtd.pack(side=tk.LEFT)
        self.combo_qtd.bind('<<ComboboxSelected>>', self._on_change_grid_size)
        self.lbl_page_info = ttk.Label(header, text=localization.tr('LBL_PAGE_INFO').format(1, self.total_pages), font=Config.FONTS['sub_header'])
        self.lbl_page_info.pack(side=tk.LEFT, padx=30)
        self.lbl_loading = ttk.Label(header, text='', foreground='orange')
        self.lbl_loading.pack(side=tk.RIGHT)
        self.main_container = ttk.Frame(self.top)
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.grid_frame = ttk.Frame(self.main_container)
        self.grid_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        footer = ttk.Frame(self.top, padding=10)
        footer.pack(fill=tk.X, side=tk.BOTTOM)
        self.btn_prev = ttk.Button(footer, text=localization.tr('BTN_PREV_PAGE'), command=self.prev_page, width=15)
        self.btn_prev.pack(side=tk.LEFT, padx=20)
        self.btn_next = ttk.Button(footer, text=localization.tr('BTN_NEXT_PAGE'), command=self.next_page, width=15)
        self.btn_next.pack(side=tk.RIGHT, padx=20)
        ttk.Label(footer, text=localization.tr('LBL_NAV_HINT'), font=('Segoe UI', 9)).pack(side=tk.TOP)

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
        self.lbl_loading.config(text=localization.tr('LBL_RENDERING'))
        for widget in self.grid_frame.winfo_children():
            widget.destroy()
        threading.Thread(target=self._render_page_thread, daemon=True).start()

    def _get_fonts(self):
        size_lg = int(self.font_scale * 1.3)
        size_sm = int(self.font_scale)
        try:
            if self.font_base_path_bd:
                f_lg = ImageFont.truetype(self.font_base_path_bd, size_lg)
                f_sm = ImageFont.truetype(self.font_base_path, size_sm)
            else:
                f_lg = ImageFont.load_default()
                f_sm = ImageFont.load_default()
        except:
            f_lg = ImageFont.load_default()
            f_sm = ImageFont.load_default()
        return (f_lg, f_sm)

    def _draw_grid_label(self, draw, x, y, text, color, font):
        try:
            text_bbox = draw.textbbox((x, y), text, font=font)
            text_w = text_bbox[2] - text_bbox[0]
            text_h = text_bbox[3] - text_bbox[1]
            lbl_pad = 4
            lbl_rect_y1 = y - text_h - lbl_pad
            lbl_rect_y2 = y
            text_pos_y = y - text_h - lbl_pad / 2 - 1
            if lbl_rect_y1 < 0:
                lbl_rect_y1 = y
                lbl_rect_y2 = y + text_h + lbl_pad
                text_pos_y = y + 1
            draw.rectangle([x, lbl_rect_y1, x + text_w + lbl_pad, lbl_rect_y2], fill=color)
            draw.text((x + 2, text_pos_y), text, fill='black', font=font)
        except Exception:
            pass

    def _render_page_thread(self):
        start_idx = self.current_page * self.items_per_page
        end_idx = start_idx + self.items_per_page
        paths = self.app.app_state.image_paths[start_idx:end_idx]
        prepared_cards = []
        class_names = self.app.app_state.class_names
        base_dir = self.app.app_state.base_directory
        font_large, font_small = self._get_fonts()
        for idx, path in enumerate(paths):
            try:
                orig_img = Image.open(path)
                orig_w, orig_h = orig_img.size
                fmt = orig_img.format or 'UNK'
                size_kb = os.path.getsize(path) / 1024
                thumb_img = Image.new('RGB', (self.card_size, self.card_size), (240, 240, 240))
                img_copy = orig_img.copy().convert('RGB')
                safe_margin = 20
                safe_size = max(50, self.card_size - safe_margin)
                img_copy.thumbnail((safe_size, safe_size), Image.Resampling.LANCZOS)
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
                            if not parts:
                                continue
                            ann_count += 1
                            cid = int(parts[0])
                            color = Config.CLASS_COLORS[cid % len(Config.CLASS_COLORS)]
                            cls_name = class_names[cid] if cid < len(class_names) else str(cid)
                            if len(parts) > 5:
                                coords = list(map(float, parts[1:]))
                                points = []
                                for i in range(0, len(coords), 2):
                                    px = coords[i] * img_copy.width + paste_x
                                    py = coords[i + 1] * img_copy.height + paste_y
                                    points.append((px, py))
                                if len(points) > 2:
                                    draw.polygon(points, outline=color, width=max(2, int(self.font_scale / 4)))
                                if points:
                                    self._draw_grid_label(draw, points[0][0], points[0][1], cls_name, color, font_small)
                            elif len(parts) == 5:
                                cx, cy, cw, ch = map(float, parts[1:5])
                                abs_cx = cx * img_copy.width + paste_x
                                abs_cy = cy * img_copy.height + paste_y
                                abs_w = cw * img_copy.width
                                abs_h = ch * img_copy.height
                                x1, y1 = (abs_cx - abs_w / 2, abs_cy - abs_h / 2)
                                x2, y2 = (abs_cx + abs_w / 2, abs_cy + abs_h / 2)
                                draw.rectangle([x1, y1, x2, y2], outline=color, width=max(2, int(self.font_scale / 4)))
                                self._draw_grid_label(draw, x1, y1, cls_name, color, font_small)
                try:
                    rel_path = os.path.relpath(path, base_dir)
                except:
                    rel_path = os.path.basename(path)
                prepared_cards.append({'pil': thumb_img, 'path': path, 'display_name': rel_path, 'index': start_idx + idx, 'res': f'{orig_w}x{orig_h}', 'fmt': fmt, 'size': f'{size_kb:.0f} KB', 'ann_count': ann_count})
            except Exception as e:
                logger.error(f'Erro grid img {path}: {e}')
        self.top.after(0, lambda: self._draw_grid(prepared_cards))

    def _draw_grid(self, cards_data):
        self.current_page_refs.clear()
        ui_font_sz = max(8, self.font_scale - 2)
        ui_font_bd = max(9, self.font_scale - 1)
        for i, card in enumerate(cards_data):
            row = i // self.cols_count
            col = i % self.cols_count
            card_frame = ttk.Frame(self.grid_frame, padding=1, relief='solid', borderwidth=1)
            card_frame.grid(row=row, column=col, padx=4, pady=4)
            tk_img = ImageTk.PhotoImage(card['pil'])
            self.current_page_refs.append(tk_img)
            img_lbl = ttk.Label(card_frame, image=tk_img, cursor='hand2')
            img_lbl.pack()
            ttk.Label(card_frame, text=card['display_name'], font=('Segoe UI', ui_font_bd, 'bold'), anchor='center').pack(fill=tk.X)
            meta_frame = ttk.Frame(card_frame)
            meta_frame.pack(fill=tk.X)
            center_meta = ttk.Frame(meta_frame)
            center_meta.pack(anchor='center')

            def add_meta(txt, color=None):
                ttk.Label(center_meta, text=txt, font=('Consolas', ui_font_sz)).pack(side=tk.LEFT, padx=2)
            add_meta(card['res'])
            add_meta('|')
            add_meta(card['fmt'])
            add_meta('|')
            add_meta(card['size'])
            if card['ann_count'] > 0:
                status_txt = localization.tr('MSG_ANNOTATIONS_COUNT').format(card['ann_count'])
                lbl_status = ttk.Label(card_frame, text=status_txt, foreground='green', font=('Segoe UI', ui_font_bd, 'bold'), anchor='center', justify='center')
            else:
                status_txt = localization.tr('MSG_NO_ANNOTATIONS')
                lbl_status = ttk.Label(card_frame, text=status_txt, foreground='red', font=('Segoe UI', ui_font_bd, 'bold'), anchor='center', justify='center')
            lbl_status.pack(fill=tk.X)
            img_lbl.bind('<Button-1>', lambda e, idx=card['index']: self._open_editor(idx))
        self.lbl_page_info.config(text=localization.tr('LBL_PAGE_INFO').format(self.current_page + 1, self.total_pages))
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