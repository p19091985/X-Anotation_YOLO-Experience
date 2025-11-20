import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog, Toplevel, Listbox, Frame, Entry
from PIL import Image, ImageTk, ImageDraw, ImageFont
import os
import json
import yaml
from typing import List, Dict, Tuple, Optional, Any

class Config:
    APP_NAME = 'Editor e Visualizador de Anotações YOLO (v6.4 Verificação)'
    DEFAULT_GEOMETRY = '1366x768'
    MIN_GEOMETRY = '1024x600'
    STYLE_THEME = 'dark'
    CANVAS_BG_COLOR = '#2E2E2E'
    HIGHLIGHT_COLOR = '#00AEEF'
    BOX_COLOR = '#50C878'
    FONT_COLOR = '#FFFFFF'
    LABEL_BG_COLOR = '#202020'
    NEW_BOX_COLOR = '#00AEEF'
    DIMENSION_TEXT_COLOR = '#FFFFFF'
    FONT_SIZE = 14
    MIN_BOX_SIZE_TO_SHOW_LABEL = 30
    AUTO_DISABLE_DRAW_MODE = True
    CONFIG_FILE_PATH = '../yolo_editor_config.json'

def find_font_path() -> Optional[str]:
    font_paths = ['c:/windows/fonts/arial.ttf', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', '/System/Library/Fonts/Supplemental/Arial.ttf']
    for path in font_paths:
        if os.path.exists(path):
            return path
    return None

class AppState:

    def __init__(self) -> None:
        self.base_directory: str = ''
        self.image_paths: List[str] = []
        self.class_names: List[str] = []
        self.current_image_index: int = -1
        self.current_pil_image: Optional[Image.Image] = None
        self.original_image_size: Tuple[int, int] = (0, 0)
        self.annotations: List[Dict[str, Any]] = []
        self.selected_annotation_index: Optional[int] = None
        self.is_drawing: bool = False

    def get_current_image_path(self) -> Optional[str]:
        if 0 <= self.current_image_index < len(self.image_paths):
            return self.image_paths[self.current_image_index]
        return None

class AnnotationManager:

    @staticmethod
    def get_label_path(image_path: str) -> str:
        image_dir = os.path.dirname(image_path)
        base_name = os.path.splitext(os.path.basename(image_path))[0]
        if os.path.basename(image_dir).lower() == 'images':
            parent_dir = os.path.dirname(image_dir)
            label_dir = os.path.join(parent_dir, 'labels')
            return os.path.join(label_dir, base_name + '.txt')
        else:
            return os.path.join(image_dir, base_name + '.txt')

    @staticmethod
    def load_annotations(label_path: str, image_size: Tuple[int, int]) -> Tuple[List[Dict[str, Any]], Optional[Exception]]:
        annotations = []
        img_w, img_h = image_size
        if not os.path.exists(label_path):
            return (annotations, None)
        try:
            with open(label_path, 'r', encoding='utf-8') as f:
                for i, line in enumerate(f):
                    line = line.strip()
                    if not line:
                        continue
                    parts = line.split()
                    if len(parts) != 5:
                        raise ValueError(f'Linha {i + 1} não tem 5 valores.')
                    class_id, x_c, y_c, w, h = map(float, parts)
                    x1 = (x_c - w / 2) * img_w
                    y1 = (y_c - h / 2) * img_h
                    x2 = (x_c + w / 2) * img_w
                    y2 = (y_c + h / 2) * img_h
                    annotations.append({'yolo_string': line, 'rect_orig': [x1, y1, x2, y2], 'class_id': int(class_id)})
            return (annotations, None)
        except (ValueError, IndexError, UnicodeDecodeError) as e:
            return ([], e)
        except Exception as e:
            return ([], e)

    @staticmethod
    def save_annotations(label_path: str, annotations: List[Dict[str, Any]]) -> bool:
        try:
            label_dir = os.path.dirname(label_path)
            if not os.path.exists(label_dir):
                os.makedirs(label_dir, exist_ok=True)
            if not annotations:
                if os.path.exists(label_path):
                    os.remove(label_path)
                return True
            with open(label_path, 'w', encoding='utf-8') as f:
                all_lines = [ann['yolo_string'] for ann in annotations]
                f.write('\n'.join(all_lines))
            return True
        except Exception:
            return False

    @staticmethod
    def convert_to_yolo_format(class_id: int, box_coords: Tuple[float, float, float, float], image_size: Tuple[int, int]) -> str:
        x1, y1, x2, y2 = box_coords
        orig_w, orig_h = image_size
        if orig_w == 0 or orig_h == 0:
            return ''
        abs_x1, abs_y1 = (min(x1, x2), min(y1, y2))
        abs_x2, abs_y2 = (max(x1, x2), max(y1, y2))
        box_w, box_h = (abs_x2 - abs_x1, abs_y2 - abs_y1)
        center_x, center_y = (abs_x1 + box_w / 2, abs_y1 + box_h / 2)
        return f'{class_id} {center_x / orig_w:.6f} {center_y / orig_h:.6f} {box_w / orig_w:.6f} {box_h / orig_h:.6f}'

class CanvasController:

    def __init__(self, canvas: tk.Canvas, app_state: AppState, ui_manager: 'UIManager'):
        self.canvas = canvas
        self.app_state = app_state
        self.ui = ui_manager
        self.zoom_level: float = 1.0
        self.pan_offset: Tuple[float, float] = (0.0, 0.0)
        self.displayed_photo: Optional[ImageTk.PhotoImage] = None
        self.action_mode: Optional[str] = None
        self.drag_start_pos: Optional[Tuple[int, int]] = None
        self.original_drag_rect: Optional[List[float]] = None
        self.pan_start_pos: Optional[Tuple[int, int]] = None
        self.temp_rect: Optional[int] = None
        self.temp_text: Optional[int] = None
        self.draw_start_pos: Optional[Tuple[int, int]] = None
        try:
            font_path = find_font_path()
            self.font = ImageFont.truetype(font_path, size=Config.FONT_SIZE) if font_path else ImageFont.load_default()
        except IOError:
            self.font = ImageFont.load_default()

    def reset_view(self) -> None:
        self.zoom_level = 1.0
        self.pan_offset = (0.0, 0.0)

    def world_to_canvas(self, wx: float, wy: float) -> Tuple[float, float]:
        canvas_w, canvas_h = (self.canvas.winfo_width(), self.canvas.winfo_height())
        img_w, img_h = self.app_state.original_image_size
        if img_w == 0 or img_h == 0:
            return (0, 0)
        center_x_canvas = canvas_w / 2 + self.pan_offset[0]
        center_y_canvas = canvas_h / 2 + self.pan_offset[1]
        offset_wx = wx - img_w / 2
        offset_wy = wy - img_h / 2
        scaled_offset_x = offset_wx * self.zoom_level
        scaled_offset_y = offset_wy * self.zoom_level
        cx = center_x_canvas + scaled_offset_x
        cy = center_y_canvas + scaled_offset_y
        return (cx, cy)

    def canvas_to_world(self, cx: float, cy: float) -> Tuple[float, float]:
        canvas_w, canvas_h = (self.canvas.winfo_width(), self.canvas.winfo_height())
        img_w, img_h = self.app_state.original_image_size
        if img_w == 0 or img_h == 0 or self.zoom_level == 0:
            return (0, 0)
        center_x_canvas = canvas_w / 2 + self.pan_offset[0]
        center_y_canvas = canvas_h / 2 + self.pan_offset[1]
        scaled_offset_x = cx - center_x_canvas
        scaled_offset_y = cy - center_y_canvas
        offset_wx = scaled_offset_x / self.zoom_level
        offset_wy = scaled_offset_y / self.zoom_level
        wx = offset_wx + img_w / 2
        wy = offset_wy + img_h / 2
        return (wx, wy)

    def display_image(self) -> None:
        self.canvas.delete('all')
        if not self.app_state.current_pil_image:
            return
        view_width = int(self.app_state.original_image_size[0] * self.zoom_level)
        view_height = int(self.app_state.original_image_size[1] * self.zoom_level)
        if view_width < 1 or view_height < 1:
            return
        display_image = self.app_state.current_pil_image.resize((view_width, view_height), Image.Resampling.LANCZOS)
        draw = ImageDraw.Draw(display_image)
        for i, ann in enumerate(self.app_state.annotations):
            rect = ann['rect_orig']
            x1_display = (rect[0] - self.app_state.original_image_size[0] / 2) * self.zoom_level + view_width / 2
            y1_display = (rect[1] - self.app_state.original_image_size[1] / 2) * self.zoom_level + view_height / 2
            x2_display = (rect[2] - self.app_state.original_image_size[0] / 2) * self.zoom_level + view_width / 2
            y2_display = (rect[3] - self.app_state.original_image_size[1] / 2) * self.zoom_level + view_height / 2
            box_coords = [x1_display, y1_display, x2_display, y2_display]
            is_selected = i == self.app_state.selected_annotation_index
            color = Config.HIGHLIGHT_COLOR if is_selected else Config.BOX_COLOR
            width = 3 if is_selected else 2
            draw.rectangle(box_coords, outline=color, width=width)
            if x2_display - x1_display > Config.MIN_BOX_SIZE_TO_SHOW_LABEL:
                class_id = ann['class_id']
                if 0 <= class_id < len(self.app_state.class_names):
                    label = self.app_state.class_names[class_id]
                    text_pos = (box_coords[0] + width, box_coords[1] + width)
                    try:
                        bbox = draw.textbbox(text_pos, label, font=self.font)
                        draw.rectangle(bbox, fill=Config.LABEL_BG_COLOR)
                        draw.text(text_pos, label, font=self.font, fill=Config.FONT_COLOR)
                    except Exception:
                        pass
        self.displayed_photo = ImageTk.PhotoImage(display_image)
        canvas_w, canvas_h = (self.canvas.winfo_width(), self.canvas.winfo_height())
        pos_x = canvas_w / 2 + self.pan_offset[0]
        pos_y = canvas_h / 2 + self.pan_offset[1]
        self.canvas.create_image(pos_x, pos_y, anchor=tk.CENTER, image=self.displayed_photo, tags='image')
        if self.app_state.selected_annotation_index is not None:
            self._draw_handles()

    def _draw_handles(self) -> None:
        self.canvas.delete('handles')
        idx = self.app_state.selected_annotation_index
        if idx is None:
            return
        rect = self.app_state.annotations[idx]['rect_orig']
        x1w, y1w, x2w, y2w = rect
        coords_canvas = [self.world_to_canvas(x1w, y1w), self.world_to_canvas(x2w, y1w), self.world_to_canvas(x1w, y2w), self.world_to_canvas(x2w, y2w)]
        s = 5
        tags_map = ['handle_nw', 'handle_ne', 'handle_sw', 'handle_se']
        for i, (px, py) in enumerate(coords_canvas):
            self.canvas.create_rectangle(px - s, py - s, px + s, py + s, fill=Config.HIGHLIGHT_COLOR, outline='black', tags=('handles', tags_map[i]))

    def get_item_at(self, event_x: int, event_y: int) -> Tuple[Optional[str], Optional[int]]:
        wx, wy = self.canvas_to_world(event_x, event_y)
        if self.app_state.selected_annotation_index is not None:
            item = self.canvas.find_closest(event_x, event_y, halo=5)
            if item:
                tags = self.canvas.gettags(item[0])
                if 'handles' in tags:
                    return (tags[1], self.app_state.selected_annotation_index)
        for i in range(len(self.app_state.annotations) - 1, -1, -1):
            rect = self.app_state.annotations[i]['rect_orig']
            if rect[0] <= wx <= rect[2] and rect[1] <= wy <= rect[3]:
                return ('box', i)
        return (None, None)

    def on_canvas_press(self, event: tk.Event, on_update_callback: callable) -> None:
        if self.app_state.is_drawing:
            self.draw_start_pos = (event.x, event.y)
            self.temp_rect = self.canvas.create_rectangle(event.x, event.y, event.x, event.y, outline=Config.NEW_BOX_COLOR, width=2, dash=(4, 2))
            self.temp_text = self.canvas.create_text(event.x + 5, event.y - 10, anchor='w', text='', fill=Config.DIMENSION_TEXT_COLOR)
            return
        item_type, item_index = self.get_item_at(event.x, event.y)
        if item_type and item_type.startswith('handle_'):
            self.action_mode = item_type
            self.drag_start_pos = (event.x, event.y)
            if item_index is not None:
                self.original_drag_rect = self.app_state.annotations[item_index]['rect_orig'][:]
        elif item_type == 'box':
            if item_index != self.app_state.selected_annotation_index:
                on_update_callback(select_annotation_idx=item_index)
            self.action_mode = 'moving'
            self.drag_start_pos = (event.x, event.y)
            if item_index is not None:
                self.original_drag_rect = self.app_state.annotations[item_index]['rect_orig'][:]
        else:
            on_update_callback(deselect_all=True)

    def on_canvas_drag(self, event: tk.Event) -> None:
        if self.app_state.is_drawing and self.temp_rect and self.draw_start_pos:
            x1, y1 = self.draw_start_pos
            x2, y2 = (event.x, event.y)
            self.canvas.coords(self.temp_rect, x1, y1, x2, y2)
            wx1, wy1 = self.canvas_to_world(x1, y1)
            wx2, wy2 = self.canvas_to_world(x2, y2)
            w_world, h_world = (abs(wx2 - wx1), abs(wy2 - wy1))
            self.canvas.coords(self.temp_text, x2 + 5, y2 - 10)
            self.canvas.itemconfig(self.temp_text, text=f'{w_world:.0f}x{h_world:.0f}')
            return
        if not self.action_mode or self.original_drag_rect is None or self.drag_start_pos is None or (self.app_state.selected_annotation_index is None):
            return
        current_wx, current_wy = self.canvas_to_world(event.x, event.y)
        start_wx, start_wy = self.canvas_to_world(self.drag_start_pos[0], self.drag_start_pos[1])
        dwx, dwy = (current_wx - start_wx, current_wy - start_wy)
        x1, y1, x2, y2 = self.original_drag_rect
        new_coords = [x1, y1, x2, y2]
        if self.action_mode == 'moving':
            new_coords = [x1 + dwx, y1 + dwy, x2 + dwx, y2 + dwy]
        else:
            if 'n' in self.action_mode:
                new_coords[1] = y1 + dwy
            if 's' in self.action_mode:
                new_coords[3] = y2 + dwy
            if 'w' in self.action_mode:
                new_coords[0] = x1 + dwx
            if 'e' in self.action_mode:
                new_coords[2] = x2 + dwx
        self.app_state.annotations[self.app_state.selected_annotation_index]['rect_orig'] = new_coords
        self.display_image()

    def on_canvas_release(self, event: tk.Event, on_update_callback: callable) -> None:
        if self.app_state.is_drawing:
            if self.temp_rect:
                self.canvas.delete(self.temp_rect)
            if self.temp_text:
                self.canvas.delete(self.temp_text)
            self.temp_rect, self.temp_text = (None, None)
            if Config.AUTO_DISABLE_DRAW_MODE:
                on_update_callback(toggle_draw_mode=True)
            if self.draw_start_pos is None:
                return
            x1_c, y1_c = self.draw_start_pos
            x2_c, y2_c = (event.x, event.y)
            self.draw_start_pos = None
            if abs(x2_c - x1_c) < 5 and abs(y2_c - y1_c) < 5:
                return
            wx1, wy1 = self.canvas_to_world(x1_c, y1_c)
            wx2, wy2 = self.canvas_to_world(x2_c, y2_c)
            on_update_callback(add_new_box=(wx1, wy1, wx2, wy2))
            return
        if self.action_mode and self.app_state.selected_annotation_index is not None:
            idx = self.app_state.selected_annotation_index
            rect = self.app_state.annotations[idx]['rect_orig']
            x1, y1, x2, y2 = rect
            if x1 > x2:
                x1, x2 = (x2, x1)
            if y1 > y2:
                y1, y2 = (y2, y1)
            self.app_state.annotations[idx]['rect_orig'] = [x1, y1, x2, y2]
            yolo_str = AnnotationManager.convert_to_yolo_format(self.app_state.annotations[idx]['class_id'], (x1, y1, x2, y2), self.app_state.original_image_size)
            self.app_state.annotations[idx]['yolo_string'] = yolo_str
            self.action_mode = None
            on_update_callback(save_and_refresh=True)

    def on_mouse_hover(self, event: tk.Event) -> None:
        if self.action_mode or self.pan_start_pos:
            return
        cursor = ''
        if self.app_state.is_drawing:
            cursor = 'crosshair'
        else:
            item_type, _ = self.get_item_at(event.x, event.y)
            if item_type:
                if 'handle' in item_type:
                    cursor = 'sizing'
                elif item_type == 'box':
                    cursor = 'fleur'
        self.canvas.config(cursor=cursor)

    def on_zoom(self, event: tk.Event) -> None:
        factor = 1.1 if event.delta > 0 or event.num == 4 else 1 / 1.1
        self.zoom_level *= factor
        self.display_image()

    def on_pan_start(self, event: tk.Event) -> None:
        self.pan_start_pos = (event.x, event.y)
        self.canvas.config(cursor='fleur')

    def on_pan_move(self, event: tk.Event) -> None:
        if self.pan_start_pos:
            dx = event.x - self.pan_start_pos[0]
            dy = event.y - self.pan_start_pos[1]
            self.pan_offset = (self.pan_offset[0] + dx, self.pan_offset[1] + dy)
            self.pan_start_pos = (event.x, event.y)
            self.display_image()

    def on_pan_end(self, event: tk.Event) -> None:
        self.pan_start_pos = None
        self.on_mouse_hover(event)

class UIManager:

    def __init__(self, root: tk.Tk, app: 'MainApplication'):
        self.root = root
        self.app = app
        self.app_state = app.app_state
        self.drawing_mode_var = tk.BooleanVar(value=False)
        self.class_id_var = tk.StringVar()
        self.preview_window = None
        self.theme_var = tk.StringVar(value=Config.STYLE_THEME)
        self._create_widgets()

    def _create_widgets(self) -> None:
        top_frame = ttk.Frame(self.root, padding=(10, 10, 10, 0))
        top_frame.pack(fill=tk.X)
        btn_select_dir = ttk.Button(top_frame, text='📂 Abrir Pasta', command=self.app.select_directory)
        btn_select_dir.pack(side=tk.LEFT, padx=(0, 5))
        btn_preview = ttk.Button(top_frame, text='👁️ Prévia', command=self.toggle_preview_window)
        btn_preview.pack(side=tk.LEFT, padx=5)
        self.dir_label = ttk.Label(top_frame, text='Nenhuma pasta selecionada', style='TLabel')
        self.dir_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)
        theme_switch = ttk.Checkbutton(top_frame, text='Tema Escuro', variable=self.theme_var, command=self.app.toggle_theme, onvalue='dark', offvalue='light', style='Switch.TCheckbutton')
        theme_switch.pack(side=tk.RIGHT, padx=5)
        content_frame = ttk.Frame(self.root, padding=(10, 10, 10, 0))
        content_frame.pack(fill=tk.BOTH, expand=True)
        content_frame.grid_columnconfigure(1, weight=1)
        content_frame.grid_rowconfigure(0, weight=1)
        left_panel = ttk.Frame(content_frame, width=300)
        left_panel.grid(row=0, column=0, sticky='ns', padx=(0, 10))
        left_panel.pack_propagate(False)
        images_frame = ttk.LabelFrame(left_panel, text='Imagens')
        images_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        self.listbox = tk.Listbox(images_frame, borderwidth=0, highlightthickness=0)
        img_scrollbar = ttk.Scrollbar(images_frame, orient='vertical', command=self.listbox.yview)
        self.listbox.config(yscrollcommand=img_scrollbar.set)
        img_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        annotations_frame = ttk.LabelFrame(left_panel, text='Anotações (W/S para navegar)')
        annotations_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        self.annotation_listbox = tk.Listbox(annotations_frame, exportselection=False, borderwidth=0, highlightthickness=0)
        ann_scrollbar = ttk.Scrollbar(annotations_frame, orient='vertical', command=self.annotation_listbox.yview)
        self.annotation_listbox.config(yscrollcommand=ann_scrollbar.set)
        ann_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.annotation_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        actions_frame = ttk.LabelFrame(left_panel, text='Ações')
        actions_frame.pack(fill=tk.X, pady=5)
        self.add_box_check = ttk.Checkbutton(actions_frame, text='Adicionar Caixa (B)', variable=self.drawing_mode_var, command=self.app.toggle_drawing_mode, style='Switch.TCheckbutton')
        self.add_box_check.pack(side=tk.TOP, anchor='w', padx=5, pady=(5, 10))
        self.add_box_check.config(state='disabled')
        class_edit_frame = ttk.Frame(actions_frame)
        class_edit_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(class_edit_frame, text='Classe:').pack(side=tk.LEFT)
        self.class_selector = ttk.Combobox(class_edit_frame, textvariable=self.class_id_var, state='readonly')
        self.class_selector.pack(side=tk.LEFT, padx=(5, 5), expand=True, fill=tk.X)
        self.change_class_button = ttk.Button(class_edit_frame, text='Alterar', command=self.app.change_annotation_class)
        self.change_class_button.pack(side=tk.LEFT)
        btn_manage_classes = ttk.Button(actions_frame, text='⚙️ Gerenciar Classes', command=self.app.open_class_manager)
        btn_manage_classes.pack(fill=tk.X, padx=5, pady=10)
        self.set_edit_controls_state('disabled')
        self.canvas = tk.Canvas(content_frame, bg=Config.CANVAS_BG_COLOR, highlightthickness=0)
        self.canvas.grid(row=0, column=1, sticky='nsew')
        bottom_frame = ttk.Frame(self.root, padding=10)
        bottom_frame.pack(fill=tk.X)
        self.prev_button = ttk.Button(bottom_frame, text='← Anterior', command=self.app.show_previous_image)
        self.prev_button.pack(side=tk.LEFT)
        self.next_button = ttk.Button(bottom_frame, text='Próximo →', command=self.app.show_next_image)
        self.next_button.pack(side=tk.RIGHT)
        self.status_label = ttk.Label(bottom_frame, text='Imagem 0 de 0', anchor='center')
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        status_bar_frame = ttk.Frame(self.root, padding=(10, 0, 10, 5))
        status_bar_frame.pack(fill=tk.X)
        ttk.Separator(status_bar_frame, orient='horizontal').pack(fill=tk.X, pady=(0, 2))
        self.coord_label = ttk.Label(status_bar_frame, text='', anchor='w')
        self.coord_label.pack(fill=tk.X)

    def update_status_bar(self, text: str) -> None:
        self.coord_label.config(text=text)

    def set_edit_controls_state(self, state: str) -> None:
        self.class_selector.config(state=state)
        self.change_class_button.config(state=state)
        if state == 'disabled':
            self.class_id_var.set('')

    def refresh_image_list(self) -> None:
        self.listbox.delete(0, tk.END)
        for img_path in self.app_state.image_paths:
            self.listbox.insert(tk.END, os.path.relpath(img_path, self.app_state.base_directory))

    def refresh_annotation_list(self) -> None:
        self.annotation_listbox.delete(0, tk.END)
        for ann in self.app_state.annotations:
            class_name = self.app_state.class_names[ann['class_id']] if ann['class_id'] < len(self.app_state.class_names) else 'ID?'
            self.annotation_listbox.insert(tk.END, f'ID {ann['class_id']} ({class_name})')

    def update_class_selector(self) -> None:
        self.class_selector['values'] = self.app_state.class_names or []
        self.class_selector.config(state='readonly' if self.app_state.class_names else 'disabled')

    def sync_ui_to_state(self) -> None:
        self.drawing_mode_var.set(self.app_state.is_drawing)
        if self.app_state.current_image_index != -1:
            self.listbox.selection_clear(0, tk.END)
            self.listbox.selection_set(self.app_state.current_image_index)
            self.listbox.see(self.app_state.current_image_index)
            self.status_label.config(text=f'Imagem {self.app_state.current_image_index + 1} de {len(self.app_state.image_paths)}')
        else:
            self.status_label.config(text='Imagem 0 de 0')
        self.refresh_annotation_list()
        if self.app_state.selected_annotation_index is not None:
            idx = self.app_state.selected_annotation_index
            self.annotation_listbox.selection_set(idx)
            self.annotation_listbox.activate(idx)
            self.set_edit_controls_state('normal' if self.app_state.class_names else 'disabled')
            class_id = self.app_state.annotations[idx]['class_id']
            if class_id < len(self.app_state.class_names):
                self.class_id_var.set(self.app_state.class_names[class_id])
            else:
                self.class_id_var.set('')
        else:
            self.annotation_listbox.selection_clear(0, tk.END)
            self.set_edit_controls_state('disabled')
        if self.preview_window and self.preview_window.winfo_exists():
            self.preview_window.update_previews()

    def toggle_preview_window(self) -> None:
        if not self.app.app_state.image_paths:
            messagebox.showwarning('Aviso', 'Nenhuma imagem carregada.')
            return
        if self.preview_window is None or not self.preview_window.winfo_exists():
            self.preview_window = PreviewWindow(self.root, self.app)
            self.preview_window.update_previews()
        else:
            self.preview_window.on_close()

class MainApplication:

    def __init__(self, root: tk.Tk):
        self.root = root
        self.app_state = AppState()
        self.ann_manager = AnnotationManager()
        self.root.title(Config.APP_NAME)
        self.root.geometry(Config.DEFAULT_GEOMETRY)
        self.root.minsize(*map(int, Config.MIN_GEOMETRY.split('x')))
        self.ui = UIManager(root, self)
        self.canvas_controller = CanvasController(self.ui.canvas, self.app_state, self.ui)
        self._load_config()
        self._bind_events()
        self.ui.update_status_bar('Bem-vindo! Selecione uma pasta para começar.')

    def _load_config(self) -> None:
        try:
            with open(Config.CONFIG_FILE_PATH, 'r') as f:
                config = json.load(f)
            self.app_state.base_directory = config.get('last_directory', '')
            self.ui.theme_var.set(config.get('theme', Config.STYLE_THEME))
            self.toggle_theme(update_config=False)
            if self.app_state.base_directory and os.path.exists(self.app_state.base_directory):
                if self._verify_dataset_structure(self.app_state.base_directory):
                    self.root.after(100, self._load_directory_contents)
                else:
                    self.app_state.base_directory = ''
        except (FileNotFoundError, json.JSONDecodeError):
            self.toggle_theme(update_config=False)

    def _save_config(self) -> None:
        config = {'last_directory': self.app_state.base_directory, 'theme': self.ui.theme_var.get()}
        with open(Config.CONFIG_FILE_PATH, 'w') as f:
            json.dump(config, f, indent=4)

    def _verify_dataset_structure(self, path: str) -> bool:
        required_dirs = {'train', 'test', 'valid'}
        found_dirs = set()
        if not os.path.isdir(path):
            return False
        for item in os.listdir(path):
            if os.path.isdir(os.path.join(path, item)):
                found_dirs.add(item)
        return required_dirs.issubset(found_dirs)

    def _bind_events(self) -> None:
        self.ui.listbox.bind('<<ListboxSelect>>', self.on_image_select_from_list)
        self.ui.annotation_listbox.bind('<<ListboxSelect>>', self.on_annotation_select_from_list)
        self.ui.canvas.bind('<Configure>', self.on_canvas_resize)
        self.ui.canvas.bind('<ButtonPress-1>', lambda e: self.canvas_controller.on_canvas_press(e, self.process_canvas_update))
        self.ui.canvas.bind('<B1-Motion>', self.canvas_controller.on_canvas_drag)
        self.ui.canvas.bind('<ButtonRelease-1>', lambda e: self.canvas_controller.on_canvas_release(e, self.process_canvas_update))
        self.ui.canvas.bind('<Motion>', self.canvas_controller.on_mouse_hover)
        self.ui.canvas.bind('<MouseWheel>', self.canvas_controller.on_zoom)
        self.ui.canvas.bind('<Button-4>', self.canvas_controller.on_zoom)
        self.ui.canvas.bind('<Button-5>', self.canvas_controller.on_zoom)
        self.ui.canvas.bind('<ButtonPress-2>', self.canvas_controller.on_pan_start)
        self.ui.canvas.bind('<ButtonPress-3>', self.canvas_controller.on_pan_start)
        self.ui.canvas.bind('<B2-Motion>', self.canvas_controller.on_pan_move)
        self.ui.canvas.bind('<B3-Motion>', self.canvas_controller.on_pan_move)
        self.ui.canvas.bind('<ButtonRelease-2>', self.canvas_controller.on_pan_end)
        self.ui.canvas.bind('<ButtonRelease-3>', self.canvas_controller.on_pan_end)
        self.root.bind('<Left>', lambda e: self.show_previous_image())
        self.root.bind('<Right>', lambda e: self.show_next_image())
        self.root.bind('<Delete>', self.delete_current_item)
        self.root.bind('<b>', self.toggle_drawing_mode_event)
        self.root.bind('<w>', self.select_prev_annotation)
        self.root.bind('<s>', self.select_next_annotation)
        self.root.bind('<Escape>', self.deselect_all)
        self.root.protocol('WM_DELETE_WINDOW', self.on_close)

    def select_directory(self) -> None:
        path = filedialog.askdirectory(title='Selecione a pasta raiz do seu dataset (deve conter train/test/valid)')
        if not path:
            return
        if not self._verify_dataset_structure(path):
            messagebox.showerror('Estrutura Inválida', "A pasta selecionada deve conter os subdiretórios 'train', 'test' e 'valid'.\n\nO programa será encerrado.")
            self.root.destroy()
            return
        self.app_state.base_directory = path
        self._load_directory_contents()
        self._save_config()

    def _load_directory_contents(self) -> None:
        self.ui.dir_label.config(text=f'Pasta: {os.path.basename(self.app_state.base_directory)}')
        self._load_class_names()
        self.app_state.image_paths = []
        valid_extensions = ('.png', '.jpg', '.jpeg', '.bmp', '.gif')
        for root_dir, _, files in os.walk(self.app_state.base_directory):
            if os.path.basename(root_dir).startswith(('.', '_')):
                continue
            for file in sorted(files):
                if file.lower().endswith(valid_extensions):
                    self.app_state.image_paths.append(os.path.join(root_dir, file))
        self.ui.refresh_image_list()
        if self.app_state.image_paths:
            self.show_image_at_index(0)
            self.ui.add_box_check.config(state='normal')
            self.ui.update_status_bar(f'{len(self.app_state.image_paths)} imagens carregadas. Use as setas para navegar.')
        else:
            self.app_state.current_pil_image = None
            self.app_state.current_image_index = -1
            self.app_state.annotations = []
            self.canvas_controller.display_image()
            self.ui.sync_ui_to_state()
            messagebox.showwarning('Nenhuma Imagem', f"Nenhuma imagem encontrada em '{self.app_state.base_directory}'.")
            self.ui.add_box_check.config(state='disabled')

    def _load_class_names(self) -> None:
        self.app_state.class_names = []
        for yaml_name in ('data.yaml', 'dataset.yaml'):
            yaml_path = os.path.join(self.app_state.base_directory, yaml_name)
            if os.path.exists(yaml_path):
                try:
                    with open(yaml_path, 'r', encoding='utf-8') as f:
                        data = yaml.safe_load(f)
                    if 'names' in data and isinstance(data['names'], list):
                        self.app_state.class_names = data['names']
                        self.ui.update_class_selector()
                        return
                except Exception as e:
                    messagebox.showerror('Erro de Leitura', f"Não foi possível ler '{yaml_name}':\n{e}")
        classes_path = os.path.join(self.app_state.base_directory, 'classes.txt')
        if not os.path.exists(classes_path):
            parent_dir_classes = os.path.join(os.path.dirname(self.app_state.base_directory), 'classes.txt')
            if os.path.exists(parent_dir_classes):
                classes_path = parent_dir_classes
            else:
                self.ui.update_class_selector()
                return
        try:
            with open(classes_path, 'r', encoding='utf-8') as f:
                self.app_state.class_names = [line.strip() for line in f if line.strip()]
        except Exception as e:
            messagebox.showerror('Erro de Leitura', f"Não foi possível ler 'classes.txt':\n{e}")
        self.ui.update_class_selector()

    def show_image_at_index(self, index: int) -> None:
        if not 0 <= index < len(self.app_state.image_paths):
            return
        self.deselect_all()
        self.app_state.current_image_index = index
        image_path = self.app_state.get_current_image_path()
        if not image_path:
            return
        try:
            image = Image.open(image_path)
            if image.mode == 'P':
                image = image.convert('RGBA')
            else:
                image = image.convert('RGB')
            self.app_state.current_pil_image = image
            self.app_state.original_image_size = image.size
        except Exception as e:
            messagebox.showerror('Erro de Imagem', f'Não foi possível carregar a imagem:\n{image_path}\n\nErro: {e}')
            self.app_state.current_pil_image = None
            return
        label_path = self.ann_manager.get_label_path(image_path)
        self.app_state.annotations, error = self.ann_manager.load_annotations(label_path, self.app_state.original_image_size)
        if error:
            self._handle_malformed_annotation_file(label_path, error)
        self.canvas_controller.reset_view()
        self.canvas_controller.display_image()
        self.ui.sync_ui_to_state()

    def process_canvas_update(self, **kwargs) -> None:
        if kwargs.get('select_annotation_idx') is not None:
            self._select_annotation(kwargs['select_annotation_idx'])
        if kwargs.get('deselect_all'):
            self.deselect_all()
        if kwargs.get('toggle_draw_mode'):
            self.toggle_drawing_mode()
        if kwargs.get('add_new_box'):
            self._add_new_box_at(kwargs['add_new_box'])
        if kwargs.get('save_and_refresh'):
            self._save_and_refresh(new_selection=self.app_state.selected_annotation_index)

    def _select_annotation(self, index: int) -> None:
        if not 0 <= index < len(self.app_state.annotations):
            return
        self.deselect_all()
        self.app_state.selected_annotation_index = index
        self.ui.sync_ui_to_state()
        self.canvas_controller.display_image()

    def deselect_all(self, event: Optional[tk.Event]=None) -> str:
        if self.app_state.selected_annotation_index is not None:
            self.app_state.selected_annotation_index = None
            self.ui.sync_ui_to_state()
            self.canvas_controller.display_image()
        return 'break'

    def _save_and_refresh(self, new_selection: Optional[int]=None) -> None:
        if self.app_state.current_image_index == -1:
            return
        image_path = self.app_state.get_current_image_path()
        if not image_path:
            return
        label_path = self.ann_manager.get_label_path(image_path)
        if not self.ann_manager.save_annotations(label_path, self.app_state.annotations):
            messagebox.showerror('Erro', 'Falha ao salvar o arquivo de anotação.')
            return
        self.ui.refresh_annotation_list()
        if new_selection is not None and new_selection < len(self.app_state.annotations):
            self._select_annotation(new_selection)
        else:
            self.deselect_all()
        self.canvas_controller.display_image()

    def _add_new_box_at(self, box_coords: Tuple[float, float, float, float]) -> None:
        class_id = self._ask_for_class_id()
        if class_id is None:
            return
        yolo_string = self.ann_manager.convert_to_yolo_format(class_id, box_coords, self.app_state.original_image_size)
        x1, y1, x2, y2 = box_coords
        rect_orig = [min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2)]
        self.app_state.annotations.append({'yolo_string': yolo_string, 'rect_orig': rect_orig, 'class_id': class_id})
        self._save_and_refresh(new_selection=len(self.app_state.annotations) - 1)
        self.ui.update_status_bar(f'Nova caixa adicionada e salva.')

    def change_annotation_class(self) -> None:
        if self.app_state.selected_annotation_index is None or not self.app_state.class_names:
            return
        selected_class_name = self.ui.class_id_var.get()
        if not selected_class_name:
            return
        try:
            new_id = self.app_state.class_names.index(selected_class_name)
        except ValueError:
            return
        idx = self.app_state.selected_annotation_index
        ann = self.app_state.annotations[idx]
        parts = ann['yolo_string'].split()
        parts[0] = str(new_id)
        ann['class_id'] = new_id
        ann['yolo_string'] = ' '.join(parts)
        self._save_and_refresh(new_selection=idx)
        self.ui.update_status_bar(f"Classe alterada para '{selected_class_name}' e salva.")

    def delete_current_item(self, event: Optional[tk.Event]=None) -> None:
        if self.app_state.current_image_index == -1:
            return
        if self.app_state.selected_annotation_index is not None:
            if messagebox.askyesno('Confirmar Exclusão', 'Deletar a anotação selecionada?'):
                idx_to_del = self.app_state.selected_annotation_index
                self.app_state.annotations.pop(idx_to_del)
                self.deselect_all()
                self._save_and_refresh()
            return

    def on_image_select_from_list(self, event: tk.Event) -> None:
        selections = self.ui.listbox.curselection()
        if selections:
            self._save_and_refresh()
            self.show_image_at_index(selections[0])

    def on_annotation_select_from_list(self, event: tk.Event) -> None:
        selections = self.ui.annotation_listbox.curselection()
        if selections:
            self._select_annotation(selections[0])

    def on_canvas_resize(self, event: tk.Event) -> None:
        if self.app_state.current_image_index != -1:
            self.canvas_controller.display_image()

    def show_previous_image(self) -> None:
        if self.app_state.current_image_index > 0:
            self._save_and_refresh()
            self.show_image_at_index(self.app_state.current_image_index - 1)

    def show_next_image(self) -> None:
        if self.app_state.current_image_index < len(self.app_state.image_paths) - 1:
            self._save_and_refresh()
            self.show_image_at_index(self.app_state.current_image_index + 1)

    def _select_adj_annotation(self, direction: int) -> None:
        if not self.ui.annotation_listbox.size():
            return
        current_idx = self.app_state.selected_annotation_index if self.app_state.selected_annotation_index is not None else -1
        new_idx = max(0, min(self.ui.annotation_listbox.size() - 1, current_idx + direction))
        self._select_annotation(new_idx)

    def select_prev_annotation(self, event: Optional[tk.Event]=None) -> None:
        self._select_adj_annotation(-1)

    def select_next_annotation(self, event: Optional[tk.Event]=None) -> None:
        self._select_adj_annotation(1)

    def toggle_drawing_mode(self) -> None:
        self.deselect_all()
        self.app_state.is_drawing = self.ui.drawing_mode_var.get()
        status = 'Modo de Desenho: Clique e arraste na imagem para criar uma caixa.' if self.app_state.is_drawing else 'Modo de Navegação: Clique numa caixa para editar ou mover.'
        self.ui.update_status_bar(status)

    def toggle_drawing_mode_event(self, event: Optional[tk.Event]=None) -> None:
        if self.ui.add_box_check['state'] == 'normal':
            self.ui.drawing_mode_var.set(not self.ui.drawing_mode_var.get())
            self.toggle_drawing_mode()

    def _ask_for_class_id(self) -> Optional[int]:
        if not self.app_state.class_names:
            return simpledialog.askinteger('ID da Classe', 'Digite o ID para a nova caixa:', parent=self.root, minvalue=0)
        dialog = tk.Toplevel(self.root)
        dialog.title('Selecionar Classe')
        dialog.geometry('300x120')
        dialog.resizable(False, False)
        ttk.Label(dialog, text='Selecione a classe para a nova caixa:').pack(pady=10, padx=10)
        class_var = tk.StringVar()
        combo = ttk.Combobox(dialog, textvariable=class_var, values=self.app_state.class_names, state='readonly')
        combo.pack(padx=10, fill=tk.X, expand=True)
        if self.app_state.class_names:
            combo.set(self.app_state.class_names[0])
        result = tk.IntVar(value=-1)

        def on_ok() -> None:
            if class_var.get():
                try:
                    result.set(self.app_state.class_names.index(class_var.get()))
                except ValueError:
                    result.set(-1)
            dialog.destroy()
        ttk.Button(dialog, text='OK', command=on_ok).pack(pady=10)
        dialog.transient(self.root)
        dialog.grab_set()
        self.root.wait_window(dialog)
        return result.get() if result.get() != -1 else None

    def _handle_malformed_annotation_file(self, label_path: str, error: Exception) -> None:
        msg = f'O arquivo de anotação está corrompido ou mal formatado:\n{os.path.basename(label_path)}\n\nErro: {error}\n\nDeseja deletar o arquivo corrompido?'
        if messagebox.askyesno('Arquivo Corrompido', msg, icon='error'):
            try:
                os.remove(label_path)
            except OSError as e:
                messagebox.showerror('Erro', f'Não foi possível deletar o arquivo:\n{e}')

    def open_class_manager(self) -> None:
        if not self.app_state.base_directory:
            messagebox.showwarning('Aviso', 'Selecione uma pasta de projeto primeiro.')
            return
        manager = ClassManagerWindow(self.root, self.app_state.class_names, self._on_classes_updated)
        self.root.wait_window(manager)

    def _on_classes_updated(self, new_class_list: List[str]) -> None:
        self.app_state.class_names = new_class_list
        classes_path = os.path.join(self.app_state.base_directory, 'classes.txt')
        try:
            with open(classes_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(new_class_list))
            self.ui.update_class_selector()
            if self.app_state.current_image_index != -1:
                self.show_image_at_index(self.app_state.current_image_index)
            self.ui.update_status_bar('Lista de classes atualizada com sucesso.')
        except Exception as e:
            messagebox.showerror('Erro de Escrita', f"Não foi possível salvar 'classes.txt':\n{e}")

    def on_close(self) -> None:
        self._save_and_refresh()
        self._save_config()
        self.root.destroy()

    def toggle_theme(self, update_config: bool=True) -> None:
        try:
            import sv_ttk
            sv_ttk.set_theme(self.ui.theme_var.get())
            if update_config:
                self._save_config()
        except (ImportError, Exception):
            self.ui.update_status_bar("Módulo 'sv_ttk' não encontrado ou falha ao aplicar tema.")

class ClassManagerWindow(Toplevel):

    def __init__(self, master, class_list: List[str], callback: callable):
        super().__init__(master)
        self.title('Gerenciador de Classes')
        self.geometry('400x450')
        self.transient(master)
        self.grab_set()
        self.class_list = class_list[:]
        self.callback = callback
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        self.listbox = Listbox(list_frame)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox.config(yscrollcommand=scrollbar.set)
        for item in self.class_list:
            self.listbox.insert(tk.END, item)
        self.listbox.bind('<Double-1>', self.edit_item)
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=5)
        ttk.Button(button_frame, text='Adicionar', command=self.add_item).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        ttk.Button(button_frame, text='Renomear', command=self.edit_item).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        ttk.Button(button_frame, text='Excluir', command=self.delete_item).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        action_frame = ttk.Frame(main_frame)
        action_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=(10, 0))
        ttk.Button(action_frame, text='Salvar e Fechar', command=self.save_and_close).pack(side=tk.RIGHT)
        ttk.Button(action_frame, text='Cancelar', command=self.destroy).pack(side=tk.RIGHT, padx=10)

    def add_item(self) -> None:
        new_class = simpledialog.askstring('Nova Classe', 'Nome da nova classe:', parent=self)
        if new_class and new_class.strip() and (new_class not in self.class_list):
            self.class_list.append(new_class)
            self.listbox.insert(tk.END, new_class)

    def edit_item(self, event=None) -> None:
        selected = self.listbox.curselection()
        if not selected:
            return
        idx = selected[0]
        old_name = self.listbox.get(idx)
        new_name = simpledialog.askstring('Renomear Classe', f"Novo nome para '{old_name}':", initialvalue=old_name, parent=self)
        if new_name and new_name.strip() and (new_name != old_name) and (new_name not in self.class_list):
            self.class_list[idx] = new_name
            self.listbox.delete(idx)
            self.listbox.insert(idx, new_name)
            self.listbox.selection_set(idx)

    def delete_item(self) -> None:
        selected = self.listbox.curselection()
        if not selected:
            return
        idx = selected[0]
        if messagebox.askyesno('Confirmar', f"Tem certeza que deseja excluir '{self.listbox.get(idx)}'?"):
            self.class_list.pop(idx)
            self.listbox.delete(idx)

    def save_and_close(self) -> None:
        self.callback(self.class_list)
        self.destroy()

class PreviewWindow(Toplevel):

    def __init__(self, master, app_instance: MainApplication):
        super().__init__(master)
        self.app = app_instance
        self.title('Prévia das Próximas Imagens')
        self.geometry('650x250')
        self.minsize(500, 200)
        self.photo_images = []
        main_frame = ttk.Frame(self, padding='10')
        main_frame.pack(fill=tk.BOTH, expand=True)
        self.image_labels = []
        self.filename_labels = []
        for i in range(3):
            frame = ttk.Frame(main_frame)
            frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
            img_label = ttk.Label(frame, background='gray30', anchor=tk.CENTER)
            img_label.pack(fill=tk.BOTH, expand=True)
            filename_label = ttk.Label(frame, text='', anchor=tk.CENTER, wraplength=180)
            filename_label.pack(fill=tk.X, pady=(5, 0))
            self.image_labels.append(img_label)
            self.filename_labels.append(filename_label)
        self.protocol('WM_DELETE_WINDOW', self.on_close)

    def update_previews(self) -> None:
        self.photo_images.clear()
        current_index = self.app.app_state.current_image_index
        all_paths = self.app.app_state.image_paths
        for i in range(3):
            preview_index = current_index + 1 + i
            if preview_index < len(all_paths):
                try:
                    path = all_paths[preview_index]
                    image = Image.open(path)
                    image.thumbnail((190, 190), Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(image)
                    self.photo_images.append(photo)
                    self.image_labels[i].config(image=photo)
                    self.filename_labels[i].config(text=os.path.basename(path))
                except Exception:
                    self.image_labels[i].config(image='', text='Erro ao carregar')
            else:
                self.image_labels[i].config(image='')
                self.filename_labels[i].config(text='Fim da lista')

    def on_close(self) -> None:
        self.app.ui.preview_window = None
        self.destroy()
if __name__ == '__main__':
    root = tk.Tk()
    app = MainApplication(root)
    root.mainloop()