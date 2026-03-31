import os
import tkinter as tk
from tkinter import ttk
from typing import TYPE_CHECKING

import localization
from config import Config
from utils_ui import ScrolledFrame, ToolTip

if TYPE_CHECKING:
    from main import MainApplication


class UIManager:

    def __init__(self, root: tk.Tk, app: 'MainApplication'):
        self.root = root
        self.app = app
        self.app_state = app.app_state
        self.drawing_mode_var = tk.BooleanVar(value=False)
        self.annotation_mode_var = tk.StringVar(value='box')
        self.class_id_var = tk.StringVar()
        self.current_theme = tk.StringVar(value=self.app.ui_theme_name)
        self.prop_x = tk.StringVar(value='0')
        self.prop_y = tk.StringVar(value='0')
        self.prop_w = tk.StringVar(value='0')
        self.prop_h = tk.StringVar(value='0')
        self.pan_mode_var = tk.BooleanVar(value=False)
        self.zoom_var = tk.StringVar()
        self._translatable_items = []
        self._tooltip_items = []
        self._create_widgets()

    def _translate_or_default(self, key: str, default: str) -> str:
        value = localization.tr(key)
        return default if value == key else value

    def _register_translation(self, widget, key, attribute='text'):
        self._translatable_items.append((widget, key, attribute))
        val = localization.tr(key)
        try:
            widget[attribute] = val
        except Exception:
            pass

    def _register_tooltip(self, widget, key: str, default: str):
        if not Config.FEATURE_ENABLE_TOOLTIPS:
            return None
        tooltip = ToolTip(widget, self._translate_or_default(key, default))
        self._tooltip_items.append((tooltip, key, default))
        return tooltip

    def refresh_ui(self):
        for widget, key, attr in self._translatable_items:
            try:
                if widget == self.dir_label and self.app_state.base_directory:
                    folder = os.path.basename(self.app_state.base_directory)
                    prefix = localization.tr('COL_FOLDER')
                    if hasattr(self.app_state, 'image_paths') and not self.app_state.image_paths:
                        widget[attr] = f'{prefix}: {folder} (Empty)'
                    else:
                        widget[attr] = f'{prefix}: {folder}'
                    continue
                widget[attr] = localization.tr(key)
            except Exception:
                pass

        for tooltip, key, default in self._tooltip_items:
            tooltip.update_text(self._translate_or_default(key, default))

        self._refresh_zoom_values()
        self._update_pan_button_label()

    def _on_language_change(self, event):
        selection = self.lang_combo.get()
        langs = localization.get_languages()
        code = next((c for name, c in langs if name == selection), None)
        if code:
            self.app.change_language(code)

    def _on_combo_post(self):
        self.lang_combo['values'] = self.all_lang_names
        current_text = self.lang_combo.get()
        if not current_text:
            return
        match = next((l for l in self.all_lang_names if l.lower().startswith(current_text.lower())), None)
        if match:
            self.lang_combo.set(match)

    def _on_lang_key_release(self, event):
        if event.keysym in ('Up', 'Down', 'Return'):
            return
        typed = self.lang_combo.get()
        if typed == '':
            self.lang_combo['values'] = self.all_lang_names
        else:
            filtered = [l for l in self.all_lang_names if typed.lower() in l.lower()]
            self.lang_combo['values'] = filtered

    def _on_lang_combo_return(self, event):
        typed = self.lang_combo.get()
        vals = self.lang_combo['values']
        if typed in vals:
            self._on_language_change(None)
        elif vals:
            self.lang_combo.set(vals[0])
            self._on_language_change(None)

    def _zoom_fit_label(self) -> str:
        return self._translate_or_default('ZOOM_FIT', 'Fit')

    def _refresh_zoom_values(self):
        values = [self._zoom_fit_label(), *[f'{preset}%' for preset in Config.ZOOM_PRESETS]]
        self.zoom_combo['values'] = values
        if not self.zoom_var.get():
            self.zoom_var.set(values[0])
        elif not self.zoom_var.get().endswith('%'):
            self.zoom_var.set(values[0])

    def _update_pan_button_label(self):
        self.pan_btn.config(text='Pan ON' if self.pan_mode_var.get() else 'Pan')

    def _create_widgets(self) -> None:
        top_frame = ttk.Frame(self.root, padding=(10, 10, 10, 0))
        top_frame.pack(fill=tk.X)

        btn_new = ttk.Button(top_frame, command=self.app.open_new_project_wizard)
        self._register_translation(btn_new, 'NEW_PROJECT')
        self._register_tooltip(btn_new, 'TIP_NEW_PROJECT', 'Cria uma estrutura base reutilizavel para um dataset YOLO.')
        if Config.FEATURE_SHOW_NEW_PROJECT:
            btn_new.pack(side=tk.LEFT, padx=(0, 5))

        btn_open = ttk.Button(top_frame, command=self.app.select_directory)
        self._register_translation(btn_open, 'OPEN_PROJECT')
        self._register_tooltip(btn_open, 'TIP_OPEN_PROJECT', 'Abre um diretorio existente com imagens e anotacoes.')
        if Config.FEATURE_SHOW_OPEN_PROJECT:
            btn_open.pack(side=tk.LEFT, padx=(0, 5))

        btn_manage_top = ttk.Button(top_frame, command=self.app.open_class_manager)
        self._register_translation(btn_manage_top, 'MANAGE_CLASSES')
        self._register_tooltip(btn_manage_top, 'TIP_MANAGE_CLASSES', 'Adiciona, renomeia ou remove classes do projeto.')
        btn_manage_top.pack(side=tk.LEFT, padx=(0, 5))

        btn_refresh = ttk.Button(top_frame, text='R', width=3, command=self.app.refresh_directory)
        btn_refresh.pack(side=tk.LEFT, padx=(0, 5))
        self._register_tooltip(btn_refresh, 'TIP_REFRESH_DIRECTORY', 'Recarrega o diretorio atual para refletir alteracoes externas.')

        ttk.Separator(top_frame, orient='vertical').pack(side=tk.LEFT, fill=tk.Y, padx=10)

        btn_grid = ttk.Button(top_frame, command=self.app.open_grid_viewer)
        self._register_translation(btn_grid, 'GRID_VIEW')
        self._register_tooltip(btn_grid, 'TIP_GRID_VIEW', 'Exibe o conjunto atual em grade para revisao rapida.')
        if Config.FEATURE_SHOW_GRID_VIEW:
            btn_grid.pack(side=tk.LEFT, padx=5)

        btn_stats = ttk.Button(top_frame, command=self.app.open_dataset_analyzer)
        self._register_translation(btn_stats, 'ANALYZER')
        self._register_tooltip(btn_stats, 'TIP_ANALYZER', 'Gera estatisticas e verificacoes do dataset atual.')
        if Config.FEATURE_SHOW_ANALYZER:
            btn_stats.pack(side=tk.LEFT, padx=5)

        btn_split = ttk.Button(top_frame, command=self.app.open_split_wizard)
        self._register_translation(btn_split, 'SPLIT')
        self._register_tooltip(btn_split, 'TIP_SPLIT', 'Divide imagens em train, valid e opcionalmente test.')
        if Config.FEATURE_SHOW_SPLIT:
            btn_split.pack(side=tk.LEFT, padx=5)

        btn_about = ttk.Button(top_frame, command=self.app.show_about_dialog)
        self._register_translation(btn_about, 'ABOUT')
        self._register_tooltip(btn_about, 'TIP_ABOUT', 'Exibe informacoes genericas do template base.')
        if Config.FEATURE_SHOW_ABOUT:
            btn_about.pack(side=tk.LEFT, padx=5)

        lang_frame = ttk.Frame(top_frame)
        if Config.FEATURE_SHOW_LANGUAGE_SELECTOR:
            lang_frame.pack(side=tk.RIGHT, padx=5)

        langs = localization.get_languages()
        self.all_lang_names = [l[0] for l in langs]
        self.lang_var = tk.StringVar()
        self.lang_combo = ttk.Combobox(
            lang_frame,
            textvariable=self.lang_var,
            values=self.all_lang_names,
            state='normal',
            width=15,
            postcommand=self._on_combo_post
        )
        self.lang_combo.pack(side=tk.RIGHT)
        self.lang_combo.bind('<KeyRelease>', self._on_lang_key_release)
        self.lang_combo.bind('<Return>', self._on_lang_combo_return)
        curr_code = localization.get_current_language()
        curr_name = next((name for name, code in langs if code == curr_code), 'Português')
        self.lang_combo.set(curr_name)
        self.lang_combo.bind('<<ComboboxSelected>>', self._on_language_change)

        zoom_frame = ttk.Frame(top_frame)
        zoom_frame.pack(side=tk.RIGHT, padx=(0, 10))
        ttk.Label(zoom_frame, text='Zoom').pack(side=tk.LEFT, padx=(0, 4))
        self.zoom_combo = ttk.Combobox(zoom_frame, textvariable=self.zoom_var, state='readonly', width=8)
        self.zoom_combo.pack(side=tk.LEFT)
        self.zoom_combo.bind('<<ComboboxSelected>>', self._on_zoom_combo_select)
        self._register_tooltip(self.zoom_combo, 'TIP_ZOOM_COMBO', 'Seleciona um nivel de zoom. Ctrl+scroll tambem ajusta o zoom.')
        self._refresh_zoom_values()

        self.pan_btn = ttk.Button(zoom_frame, width=8, command=self._toggle_pan_mode)
        self.pan_btn.pack(side=tk.LEFT, padx=(6, 0))
        self._update_pan_button_label()
        self._register_tooltip(self.pan_btn, 'TIP_PAN_MODE', 'Ativa o modo pan para arrastar a imagem com o botao esquerdo. Atalho: P.')

        self.dir_label = ttk.Label(top_frame, style='TLabel')
        self._register_translation(self.dir_label, 'NO_PROJECT')
        if Config.FEATURE_SHOW_DIRECTORY_LABEL:
            self.dir_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)

        content_frame = ttk.Frame(self.root, padding=(10, 10, 10, 0))
        content_frame.pack(fill=tk.BOTH, expand=True)
        content_frame.grid_columnconfigure(1, weight=1)
        content_frame.grid_rowconfigure(0, weight=1)

        left_panel_container = ttk.Frame(content_frame, width=350)
        left_panel_container.grid(row=0, column=0, sticky='ns', padx=(0, 10))
        self.left_scroll = ScrolledFrame(left_panel_container, width=330)
        self.left_scroll.pack(fill=tk.BOTH, expand=True)
        parent_for_scrolled = self.left_scroll.interior

        img_fr = ttk.LabelFrame(parent_for_scrolled, padding=2)
        self._register_translation(img_fr, 'IMAGES_FRAME')
        img_fr.pack(fill=tk.X, expand=False, pady=(0, 5))
        self.listbox = tk.Listbox(img_fr, borderwidth=0, highlightthickness=0, height=12)
        sb = ttk.Scrollbar(img_fr, orient='vertical', command=self.listbox.yview)
        self.listbox.config(yscrollcommand=sb.set)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        ann_fr = ttk.LabelFrame(parent_for_scrolled, padding=2)
        self._register_translation(ann_fr, 'ANNOTATIONS_FRAME')
        ann_fr.pack(fill=tk.X, expand=False, pady=5)
        self.annotation_listbox = tk.Listbox(ann_fr, exportselection=False, borderwidth=0, highlightthickness=0, height=8)
        sb_a = ttk.Scrollbar(ann_fr, orient='vertical', command=self.annotation_listbox.yview)
        self.annotation_listbox.config(yscrollcommand=sb_a.set)
        sb_a.pack(side=tk.RIGHT, fill=tk.Y)
        self.annotation_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        act_fr = ttk.LabelFrame(parent_for_scrolled, padding=5)
        self._register_translation(act_fr, 'TOOLS_FRAME')
        act_fr.pack(fill=tk.X, pady=5, padx=2)

        self.add_box_check = ttk.Checkbutton(act_fr, variable=self.drawing_mode_var, command=self.app.toggle_drawing_mode)
        self._register_translation(self.add_box_check, 'DRAW_MODE')
        self._register_tooltip(self.add_box_check, 'TIP_DRAW_MODE', 'Ativa o modo de desenho manual. Atalho: D.')
        self.add_box_check.pack(anchor='center', padx=5, pady=10, fill=tk.X)
        self.add_box_check.config(state='normal')

        type_frame = ttk.Labelframe(act_fr, padding=5)
        self._register_translation(type_frame, 'ANNOTATION_TYPE')
        type_frame.pack(fill=tk.X, pady=5)

        rb_box = ttk.Radiobutton(type_frame, variable=self.annotation_mode_var, value='box', command=self.change_annotation_mode)
        self._register_translation(rb_box, 'BOX_MODE')
        self._register_tooltip(rb_box, 'TIP_BOX_MODE', 'Cria caixas delimitadoras para deteccao de objetos.')
        rb_box.pack(anchor='w')

        rb_poly = ttk.Radiobutton(type_frame, variable=self.annotation_mode_var, value='polygon', command=self.change_annotation_mode)
        self._register_translation(rb_poly, 'POLY_MODE')
        self._register_tooltip(rb_poly, 'TIP_POLY_MODE', 'Cria poligonos ponto a ponto para segmentacao.')
        if Config.FEATURE_ENABLE_POLYGON:
            rb_poly.pack(anchor='w')

        lbl_hint = ttk.Label(type_frame, font=Config.FONTS['small'], foreground='gray')
        self._register_translation(lbl_hint, 'POLY_HINT')
        if Config.FEATURE_ENABLE_POLYGON:
            lbl_hint.pack(anchor='w', padx=15)

        cls_row = ttk.Frame(act_fr)
        cls_row.pack(fill=tk.X, padx=5, pady=2)
        lbl_class = ttk.Label(cls_row)
        self._register_translation(lbl_class, 'CLASS_LABEL')
        lbl_class.pack(side=tk.LEFT)
        self.class_selector = ttk.Combobox(cls_row, textvariable=self.class_id_var, state='readonly')
        self.class_selector.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.change_class_button = ttk.Button(cls_row, width=6, command=self.app.change_annotation_class)
        self._register_translation(self.change_class_button, 'SET_BTN')
        self._register_tooltip(self.change_class_button, 'TIP_SET_CLASS', 'Aplica a classe selecionada a anotacao ativa.')
        self.change_class_button.pack(side=tk.RIGHT)

        btn_manage = ttk.Button(act_fr, command=self.app.open_class_manager)
        self._register_translation(btn_manage, 'MANAGE_CLASSES')
        self._register_tooltip(btn_manage, 'TIP_MANAGE_CLASSES', 'Adiciona, renomeia ou remove classes do projeto.')
        btn_manage.pack(fill=tk.X, padx=5, pady=5)

        ttk.Separator(act_fr, orient='horizontal').pack(fill=tk.X, padx=5, pady=5)
        geo_fr = ttk.Frame(act_fr)
        geo_fr.pack(fill=tk.X, padx=5, pady=5)

        def create_geo_control(parent, label_text, var, cmd_minus, cmd_plus, row, labels=('<', '>')):
            ttk.Label(parent, text=label_text, font=Config.FONTS['mono'], width=2).grid(row=row, column=0, padx=2, pady=2)
            entry = ttk.Entry(parent, textvariable=var, width=5, justify='center', state='readonly', font=Config.FONTS['mono'])
            entry.grid(row=row, column=1, padx=2, pady=2)
            btn_frame = ttk.Frame(parent)
            btn_frame.grid(row=row, column=2, padx=2)
            ttk.Button(btn_frame, text=labels[0], width=3, command=cmd_minus).pack(side=tk.LEFT)
            ttk.Button(btn_frame, text=labels[1], width=3, command=cmd_plus).pack(side=tk.LEFT)

        create_geo_control(geo_fr, 'X', self.prop_x, lambda: self.app.perform_fine_move(-1, 0), lambda: self.app.perform_fine_move(1, 0), 0)
        create_geo_control(geo_fr, 'Y', self.prop_y, lambda: self.app.perform_fine_move(0, -1), lambda: self.app.perform_fine_move(0, 1), 1, labels=('^', 'v'))
        create_geo_control(geo_fr, 'W', self.prop_w, lambda: self.app.perform_fine_resize('right', -1), lambda: self.app.perform_fine_resize('right', 1), 2)
        create_geo_control(geo_fr, 'H', self.prop_h, lambda: self.app.perform_fine_resize('bottom', -1), lambda: self.app.perform_fine_resize('bottom', 1), 3, labels=('^', 'v'))

        canvas_frame = ttk.Frame(content_frame)
        canvas_frame.grid(row=0, column=1, sticky='nsew')
        canvas_frame.grid_rowconfigure(0, weight=1)
        canvas_frame.grid_columnconfigure(0, weight=1)

        self.canvas = tk.Canvas(canvas_frame, bg=Config.CANVAS_BG_COLOR, highlightthickness=0)
        self.canvas.grid(row=0, column=0, sticky='nsew')

        self.canvas_v_scroll = ttk.Scrollbar(canvas_frame, orient='vertical', command=self._on_v_scroll)
        self.canvas_v_scroll.grid(row=0, column=1, sticky='ns')
        self.canvas_h_scroll = ttk.Scrollbar(canvas_frame, orient='horizontal', command=self._on_h_scroll)
        self.canvas_h_scroll.grid(row=1, column=0, sticky='ew')
        self.canvas_v_scroll.grid_remove()
        self.canvas_h_scroll.grid_remove()

        bot_frame = ttk.Frame(self.root, padding=10)
        bot_frame.pack(fill=tk.X)
        btn_prev = ttk.Button(bot_frame, command=self.app.show_previous_image)
        self._register_translation(btn_prev, 'PREV_IMG')
        self._register_tooltip(btn_prev, 'TIP_PREV_IMAGE', 'Vai para a imagem anterior e salva alteracoes pendentes.')
        btn_prev.pack(side=tk.LEFT)

        self.status_label = ttk.Label(bot_frame, text='--', anchor='center')
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        btn_next = ttk.Button(bot_frame, command=self.app.show_next_image)
        self._register_translation(btn_next, 'NEXT_IMG')
        self._register_tooltip(btn_next, 'TIP_NEXT_IMAGE', 'Vai para a proxima imagem e salva alteracoes pendentes.')
        btn_next.pack(side=tk.RIGHT)

        self.coord_label = ttk.Label(self.root, text='', anchor='w', padding=(10, 0))
        self.coord_label.pack(fill=tk.X)

    def sync_zoom_display(self, percent: int) -> None:
        self.zoom_var.set(f'{percent}%')

    def _fit_zoom(self):
        if hasattr(self.app, 'canvas_controller') and self.app_state.current_pil_image:
            self.app.canvas_controller.reset_view()
            self.app.canvas_controller.display_image()
        else:
            self.zoom_var.set(self._zoom_fit_label())

    def _on_zoom_combo_select(self, event=None):
        selection = self.zoom_var.get()
        if selection == self._zoom_fit_label():
            self._fit_zoom()
            return
        try:
            pct = int(selection.rstrip('%'))
        except ValueError:
            return
        if hasattr(self.app, 'canvas_controller'):
            self.app.canvas_controller.set_zoom(pct)

    def _toggle_pan_mode(self, event=None):
        self.set_pan_mode()

    def set_pan_mode(self, enabled=None):
        if not hasattr(self.app, 'canvas_controller'):
            return
        canvas_controller = self.app.canvas_controller
        if enabled is None:
            enabled = not canvas_controller.pan_mode
        enabled = bool(enabled)
        if enabled and self.app_state.is_drawing:
            self.app.toggle_drawing_mode(force_state=False)
        canvas_controller.pan_mode = enabled
        self.pan_mode_var.set(enabled)
        self._update_pan_button_label()
        if enabled:
            status = self._translate_or_default('STATUS_PAN_ENABLED', 'Modo pan ativo. Arraste com o botao esquerdo.')
            self.update_status_bar(status)
        else:
            self.update_status_bar('')
        canvas_controller.display_image()

    def _on_v_scroll(self, *args):
        if not hasattr(self.app, 'canvas_controller'):
            return
        cc = self.app.canvas_controller
        if not cc.app_state.current_pil_image:
            return
        img_h = cc.app_state.original_image_size[1] * cc.zoom_level
        canvas_h = self.canvas.winfo_height()
        overflow_h = max(img_h - canvas_h, 0)
        if overflow_h <= 0:
            return
        action = args[0]
        if action == 'moveto':
            fraction = float(args[1])
            cc.pan_offset = (cc.pan_offset[0], -(fraction - 0.5) * overflow_h)
        elif action == 'scroll':
            amount = int(args[1])
            unit = args[2]
            step = overflow_h * 0.02 if unit == 'units' else overflow_h * 0.1
            cc.pan_offset = (cc.pan_offset[0], cc.pan_offset[1] - amount * step)
        cc.last_render_params = None
        cc.display_image()

    def _on_h_scroll(self, *args):
        if not hasattr(self.app, 'canvas_controller'):
            return
        cc = self.app.canvas_controller
        if not cc.app_state.current_pil_image:
            return
        img_w = cc.app_state.original_image_size[0] * cc.zoom_level
        canvas_w = self.canvas.winfo_width()
        overflow_w = max(img_w - canvas_w, 0)
        if overflow_w <= 0:
            return
        action = args[0]
        if action == 'moveto':
            fraction = float(args[1])
            cc.pan_offset = (-(fraction - 0.5) * overflow_w, cc.pan_offset[1])
        elif action == 'scroll':
            amount = int(args[1])
            unit = args[2]
            step = overflow_w * 0.02 if unit == 'units' else overflow_w * 0.1
            cc.pan_offset = (cc.pan_offset[0] - amount * step, cc.pan_offset[1])
        cc.last_render_params = None
        cc.display_image()

    def update_scrollbars(self) -> None:
        if not hasattr(self.app, 'canvas_controller'):
            return
        cc = self.app.canvas_controller
        if not cc.app_state.current_pil_image:
            self.canvas_v_scroll.grid_remove()
            self.canvas_h_scroll.grid_remove()
            return

        img_w = cc.app_state.original_image_size[0] * cc.zoom_level
        img_h = cc.app_state.original_image_size[1] * cc.zoom_level
        canvas_w = self.canvas.winfo_width()
        canvas_h = self.canvas.winfo_height()

        if img_h > canvas_h + 2:
            self.canvas_v_scroll.grid()
            overflow = img_h - canvas_h
            frac_top = (0.5 - cc.pan_offset[1] / overflow) - (canvas_h / img_h / 2)
            frac_bottom = frac_top + (canvas_h / img_h)
            self.canvas_v_scroll.set(max(0.0, min(frac_top, 1.0)), max(0.0, min(frac_bottom, 1.0)))
        else:
            self.canvas_v_scroll.grid_remove()

        if img_w > canvas_w + 2:
            self.canvas_h_scroll.grid()
            overflow = img_w - canvas_w
            frac_left = (0.5 - cc.pan_offset[0] / overflow) - (canvas_w / img_w / 2)
            frac_right = frac_left + (canvas_w / img_w)
            self.canvas_h_scroll.set(max(0.0, min(frac_left, 1.0)), max(0.0, min(frac_right, 1.0)))
        else:
            self.canvas_h_scroll.grid_remove()

    def change_annotation_mode(self):
        mode = self.annotation_mode_var.get()
        self.app.set_annotation_mode(mode)

    def update_status_bar(self, text: str) -> None:
        self.coord_label.config(text=text)

    def set_edit_controls_state(self, state: str) -> None:
        self.class_selector.config(state=state)
        self.change_class_button.config(state=state)
        if state == 'disabled':
            self.class_id_var.set('')
            self.update_inspector_values(None)

    def update_inspector_values(self, rect_coords):
        if not rect_coords:
            self.prop_x.set('-')
            self.prop_y.set('-')
            self.prop_w.set('-')
            self.prop_h.set('-')
            return
        x1, y1, x2, y2 = rect_coords
        rx1, rx2 = (min(x1, x2), max(x1, x2))
        ry1, ry2 = (min(y1, y2), max(y1, y2))
        w = rx2 - rx1
        h = ry2 - ry1
        self.prop_x.set(f'{int(rx1)}')
        self.prop_y.set(f'{int(ry1)}')
        self.prop_w.set(f'{int(w)}')
        self.prop_h.set(f'{int(h)}')

    def refresh_image_list(self) -> None:
        self.listbox.delete(0, tk.END)
        for path in self.app_state.image_paths:
            self.listbox.insert(tk.END, os.path.relpath(path, self.app_state.base_directory))

    def refresh_annotation_list(self) -> None:
        self.annotation_listbox.delete(0, tk.END)
        for ann in self.app_state.annotations:
            class_id = ann['class_id']
            class_name = self.app_state.class_names[class_id] if class_id < len(self.app_state.class_names) else 'ID?'
            ann_type = '[BOX]' if ann.get('type', 'box') == 'box' else '[POLY]'
            self.annotation_listbox.insert(tk.END, f"{ann_type} ID {class_id} ({class_name})")

    def update_class_selector(self) -> None:
        self.class_selector['values'] = self.app_state.class_names or []
        self.class_selector.config(state='readonly' if self.app_state.class_names else 'disabled')

    def sync_ui_to_state(self) -> None:
        self.drawing_mode_var.set(self.app_state.is_drawing)
        self.annotation_mode_var.set(self.app_state.annotation_mode)
        canvas_controller = getattr(self.app, 'canvas_controller', None)
        self.pan_mode_var.set(getattr(canvas_controller, 'pan_mode', False))
        self._update_pan_button_label()
        if self.app_state.current_image_index != -1:
            self.listbox.selection_clear(0, tk.END)
            self.listbox.selection_set(self.app_state.current_image_index)
            self.listbox.see(self.app_state.current_image_index)
            path = self.app_state.get_current_image_path()
            if path:
                self.status_label.config(text=f'Img {self.app_state.current_image_index + 1} / {len(self.app_state.image_paths)} : {os.path.basename(path)}')
        else:
            self.status_label.config(text='--')
            self.zoom_var.set(self._zoom_fit_label())
        self.add_box_check.config(state='normal')
        self.refresh_annotation_list()
        idx = self.app_state.selected_annotation_index
        if idx is not None and idx < len(self.app_state.annotations):
            self.annotation_listbox.selection_clear(0, tk.END)
            self.annotation_listbox.selection_set(idx)
            self.annotation_listbox.activate(idx)
            self.annotation_listbox.see(idx)
            self.set_edit_controls_state('normal')
            rect = self.app_state.annotations[idx]['rect_orig']
            self.update_inspector_values(rect)
            class_id = self.app_state.annotations[idx]['class_id']
            if class_id < len(self.app_state.class_names):
                self.class_id_var.set(self.app_state.class_names[class_id])
        else:
            self.annotation_listbox.selection_clear(0, tk.END)
            self.set_edit_controls_state('disabled')
