import tkinter as tk
from PIL import Image, ImageTk, ImageDraw, ImageFont
from typing import Tuple, Optional, List, Any, TYPE_CHECKING
from config import Config
from state import AppState
from managers import AnnotationManager
from utils import find_font_path
if TYPE_CHECKING:
    from ui import UIManager

class CanvasController:

    def __init__(self, canvas: tk.Canvas, app_state: AppState, ui_manager: 'UIManager'):
        self.canvas = canvas
        self.app_state = app_state
        self.ui = ui_manager
        self.zoom_level: float = 1.0
        self.pan_offset: Tuple[float, float] = (0.0, 0.0)
        self.displayed_photo: Optional[ImageTk.PhotoImage] = None
        self.cached_bg_image: Optional[Image.Image] = None
        self.last_render_params: Optional[Tuple] = None
        self.action_mode: Optional[str] = None
        self.drag_start_pos: Optional[Tuple[int, int]] = None
        self.original_drag_rect: Optional[List[float]] = None
        self.active_handle: Optional[str] = None
        self.poly_points_buffer: List[Tuple[float, float]] = []
        self.temp_poly_line: Optional[int] = None
        self.temp_poly_preview: Optional[int] = None
        self.pan_start_pos: Optional[Tuple[int, int]] = None
        self.temp_rect: Optional[int] = None
        self.temp_text: Optional[int] = None
        self.draw_start_pos: Optional[Tuple[int, int]] = None
        self.is_interacting: bool = False
        try:
            font_path = find_font_path()
            self.font = ImageFont.truetype(font_path, size=Config.FONT_SIZE) if font_path else ImageFont.load_default()
        except IOError:
            self.font = ImageFont.load_default()

    def _get_color_for_class(self, class_id: int) -> str:
        if not Config.CLASS_COLORS:
            return '#00FF00'
        return Config.CLASS_COLORS[class_id % len(Config.CLASS_COLORS)]

    def reset_view(self) -> None:
        self.poly_points_buffer = []
        canvas_w = self.canvas.winfo_width()
        canvas_h = self.canvas.winfo_height()
        img_w, img_h = self.app_state.original_image_size
        if canvas_w <= 1 or img_w == 0:
            return
        scale_w = canvas_w / img_w
        scale_h = canvas_h / img_h
        self.zoom_level = min(scale_w, scale_h) * 0.95
        self.pan_offset = (0.0, 0.0)
        self.last_render_params = None

    def world_to_canvas(self, wx: float, wy: float) -> Tuple[float, float]:
        canvas_w = self.canvas.winfo_width()
        canvas_h = self.canvas.winfo_height()
        img_w, img_h = self.app_state.original_image_size
        center_x = canvas_w / 2 + self.pan_offset[0]
        center_y = canvas_h / 2 + self.pan_offset[1]
        return (center_x + (wx - img_w / 2) * self.zoom_level, center_y + (wy - img_h / 2) * self.zoom_level)

    def canvas_to_world(self, cx: float, cy: float) -> Tuple[float, float]:
        canvas_w = self.canvas.winfo_width()
        canvas_h = self.canvas.winfo_height()
        img_w, img_h = self.app_state.original_image_size
        center_x = canvas_w / 2 + self.pan_offset[0]
        center_y = canvas_h / 2 + self.pan_offset[1]
        if self.zoom_level == 0:
            return (0, 0)
        return ((cx - center_x) / self.zoom_level + img_w / 2, (cy - center_y) / self.zoom_level + img_h / 2)

    def display_image(self) -> None:
        self.canvas.delete('all')
        if not self.app_state.current_pil_image:
            return
        final_w = int(self.app_state.original_image_size[0] * self.zoom_level)
        final_h = int(self.app_state.original_image_size[1] * self.zoom_level)
        if final_w < 1 or final_h < 1:
            return
        current_params = (self.zoom_level, self.pan_offset[0], self.pan_offset[1], self.app_state.current_image_index)
        if self.cached_bg_image and self.last_render_params == current_params:
            display_image = self.cached_bg_image.copy()
        else:
            resample_method = Image.Resampling.NEAREST if self.is_interacting else Image.Resampling.LANCZOS
            try:
                self.cached_bg_image = self.app_state.current_pil_image.resize((final_w, final_h), resample_method)
            except MemoryError:
                self.cached_bg_image = self.app_state.current_pil_image.resize((final_w, final_h), Image.Resampling.NEAREST)
            display_image = self.cached_bg_image.copy()
            self.last_render_params = current_params
        self.displayed_photo = ImageTk.PhotoImage(display_image)
        cw, ch = (self.canvas.winfo_width(), self.canvas.winfo_height())
        pos_x = cw / 2 + self.pan_offset[0]
        pos_y = ch / 2 + self.pan_offset[1]
        self.canvas.create_image(pos_x, pos_y, anchor=tk.CENTER, image=self.displayed_photo, tags='image')
        for i, ann in enumerate(self.app_state.annotations):
            is_selected = i == self.app_state.selected_annotation_index
            class_id = ann['class_id']
            base_color = self._get_color_for_class(class_id)
            outline_color = 'white' if is_selected else base_color
            line_width = Config.HIGHLIGHT_WIDTH if is_selected else Config.BOX_WIDTH
            rx1, ry1, rx2, ry2 = ann['rect_orig']
            if ann.get('type') == 'polygon':
                canvas_points = [self.world_to_canvas(px, py) for px, py in ann['points']]
                flat_points = [coord for point in canvas_points for coord in point]
                if len(canvas_points) >= 3:
                    stipple = '' if is_selected else 'gray12'
                    self.canvas.create_polygon(flat_points, outline=outline_color, width=line_width, fill=base_color, stipple=stipple, tags=f'ann_{i}')
                if canvas_points:
                    top_point = min(canvas_points, key=lambda p: p[1])
                    cx_lbl, cy_lbl = top_point
                else:
                    cx_lbl, cy_lbl = (0, 0)
            else:
                cx1, cy1 = self.world_to_canvas(rx1, ry1)
                cx2, cy2 = self.world_to_canvas(rx2, ry2)
                self.canvas.create_rectangle(cx1, cy1, cx2, cy2, outline=outline_color, width=line_width, tags=f'ann_{i}')
                cx_lbl, cy_lbl = (min(cx1, cx2), min(cy1, cy2))
            self._draw_label(cx_lbl, cy_lbl, class_id, base_color, i, is_selected)
        if self.app_state.selected_annotation_index is not None:
            self._draw_handles()
        if self.app_state.is_drawing and self.app_state.annotation_mode == 'polygon' and self.poly_points_buffer:
            c_points = [self.world_to_canvas(px, py) for px, py in self.poly_points_buffer]
            flat = [c for p in c_points for c in p]
            if len(c_points) > 1:
                self.canvas.create_line(flat, fill=Config.NEW_BOX_COLOR, width=2, tags='temp_poly')
            for cp in c_points:
                self.canvas.create_oval(cp[0] - 2, cp[1] - 2, cp[0] + 2, cp[1] + 2, fill='white', tags='temp_poly')

    def _draw_label(self, x, y, class_id, color, item_index, is_selected=False):
        label_text = str(class_id)
        if 0 <= class_id < len(self.app_state.class_names):
            label_text = f'{class_id}: {self.app_state.class_names[class_id]}'
        font_spec = ('Arial', 10, 'bold')
        tags = (f'ann_{item_index}', 'label_text')
        text_id = self.canvas.create_text(x, y - 2, text=label_text, fill='white', font=font_spec, anchor='sw', tags=tags)
        bbox = self.canvas.bbox(text_id)
        if bbox:
            bg_tags = (f'ann_{item_index}', 'label_bg')
            bg_id = self.canvas.create_rectangle(bbox[0] - 2, bbox[1] - 2, bbox[2] + 2, bbox[3] + 2, fill=color, outline=color, tags=bg_tags)
            if is_selected:
                self.canvas.itemconfigure(bg_id, outline='white', width=1)
            self.canvas.tag_raise(text_id, bg_id)

    def _draw_handles(self) -> None:
        self.canvas.delete('handles')
        idx = self.app_state.selected_annotation_index
        if idx is None or idx >= len(self.app_state.annotations):
            return
        ann = self.app_state.annotations[idx]
        s = 5
        if ann.get('type') == 'polygon':
            for i, (wx, wy) in enumerate(ann['points']):
                cx, cy = self.world_to_canvas(wx, wy)
                self.canvas.create_rectangle(cx - s, cy - s, cx + s, cy + s, fill='yellow', outline='black', tags=('handles', f'v_{i}'))
        else:
            rect = ann['rect_orig']
            x1, x2 = (min(rect[0], rect[2]), max(rect[0], rect[2]))
            y1, y2 = (min(rect[1], rect[3]), max(rect[1], rect[3]))
            coords = [(x1, y1, 'nw'), (x2, y1, 'ne'), (x1, y2, 'sw'), (x2, y2, 'se')]
            for wx, wy, tag in coords:
                cx, cy = self.world_to_canvas(wx, wy)
                self.canvas.create_rectangle(cx - s, cy - s, cx + s, cy + s, fill='white', outline='black', tags=('handles', tag))

    def get_item_at(self, event_x: int, event_y: int) -> Tuple[Optional[str], Optional[int], Optional[Any]]:
        if self.app_state.selected_annotation_index is not None:
            item = self.canvas.find_closest(event_x, event_y, halo=5)
            if item:
                tags = self.canvas.gettags(item[0])
                if 'handles' in tags:
                    handle_id = None
                    for t in tags:
                        if t.startswith('v_'):
                            handle_id = int(t.split('_')[1])
                            return ('handle', self.app_state.selected_annotation_index, handle_id)
                        elif t in ['nw', 'ne', 'sw', 'se']:
                            handle_id = t
                            return ('handle', self.app_state.selected_annotation_index, handle_id)
        items = self.canvas.find_overlapping(event_x - 1, event_y - 1, event_x + 1, event_y + 1)
        for item in reversed(items):
            tags = self.canvas.gettags(item)
            for t in tags:
                if t.startswith('ann_'):
                    idx = int(t.split('_')[1])
                    return ('box', idx, None)
        return (None, None, None)

    def on_zoom(self, event: tk.Event) -> None:
        self.is_interacting = True
        factor = 1.1 if event.delta > 0 or event.num == 4 else 0.9
        self.zoom_level *= factor
        self.display_image()
        self.canvas.after(200, self._finish_interaction)

    def on_pan_start(self, event: tk.Event) -> None:
        self.is_interacting = True
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
        self._finish_interaction()

    def _finish_interaction(self):
        self.is_interacting = False
        self.display_image()

    def on_canvas_press(self, event: tk.Event, on_update_callback: callable) -> None:
        wx, wy = self.canvas_to_world(event.x, event.y)
        if self.app_state.is_drawing:
            if self.app_state.annotation_mode == 'box':
                self.draw_start_pos = (event.x, event.y)
                self.temp_rect = self.canvas.create_rectangle(event.x, event.y, event.x, event.y, outline=Config.NEW_BOX_COLOR, width=2, dash=(4, 2))
                return
            elif self.app_state.annotation_mode == 'polygon':
                self.poly_points_buffer.append((wx, wy))
                self.display_image()
                return
        item_type, item_index, handle_id = self.get_item_at(event.x, event.y)
        if item_type:
            on_update_callback(save_history=True)
            if item_index != self.app_state.selected_annotation_index:
                on_update_callback(select_annotation_idx=item_index)
            self.drag_start_pos = (event.x, event.y)
            ann = self.app_state.annotations[item_index]
            if item_type == 'handle':
                self.action_mode = 'resizing'
                self.active_handle = handle_id
                if ann.get('type') == 'polygon':
                    self.original_drag_rect = [list(p) for p in ann['points']]
                else:
                    self.original_drag_rect = ann['rect_orig'][:]
            elif item_type == 'box':
                self.action_mode = 'moving'
                if ann.get('type') == 'polygon':
                    self.original_drag_rect = [list(p) for p in ann['points']]
                else:
                    self.original_drag_rect = ann['rect_orig'][:]
        else:
            on_update_callback(deselect_all=True)

    def on_canvas_drag(self, event: tk.Event) -> None:
        self.is_interacting = True
        if self.app_state.is_drawing and self.app_state.annotation_mode == 'box' and self.temp_rect:
            x1, y1 = self.draw_start_pos
            self.canvas.coords(self.temp_rect, x1, y1, event.x, event.y)
            return
        if self.action_mode and self.drag_start_pos:
            cur_wx, cur_wy = self.canvas_to_world(event.x, event.y)
            start_wx, start_wy = self.canvas_to_world(*self.drag_start_pos)
            dx = cur_wx - start_wx
            dy = cur_wy - start_wy
            idx = self.app_state.selected_annotation_index
            ann = self.app_state.annotations[idx]
            is_poly = ann.get('type') == 'polygon'
            if self.action_mode == 'moving':
                if is_poly:
                    new_points = []
                    for px, py in self.original_drag_rect:
                        new_points.append((px + dx, py + dy))
                    ann['points'] = new_points
                    xs = [p[0] for p in new_points]
                    ys = [p[1] for p in new_points]
                    ann['rect_orig'] = [min(xs), min(ys), max(xs), max(ys)]
                else:
                    rect = list(self.original_drag_rect)
                    rect[0] += dx
                    rect[1] += dy
                    rect[2] += dx
                    rect[3] += dy
                    ann['rect_orig'] = rect
            elif self.action_mode == 'resizing':
                if is_poly:
                    v_idx = self.active_handle
                    points = [list(p) for p in self.original_drag_rect]
                    points[v_idx][0] += dx
                    points[v_idx][1] += dy
                    ann['points'] = [tuple(p) for p in points]
                    xs = [p[0] for p in points]
                    ys = [p[1] for p in points]
                    ann['rect_orig'] = [min(xs), min(ys), max(xs), max(ys)]
                else:
                    rect = list(self.original_drag_rect)
                    min_x, max_x = (min(rect[0], rect[2]), max(rect[0], rect[2]))
                    min_y, max_y = (min(rect[1], rect[3]), max(rect[1], rect[3]))
                    if self.active_handle == 'nw':
                        min_x += dx
                        min_y += dy
                    elif self.active_handle == 'ne':
                        max_x += dx
                        min_y += dy
                    elif self.active_handle == 'sw':
                        min_x += dx
                        max_y += dy
                    elif self.active_handle == 'se':
                        max_x += dx
                        max_y += dy
                    ann['rect_orig'] = [min_x, min_y, max_x, max_y]
            self.display_image()

    def on_canvas_release(self, event: tk.Event, on_update_callback: callable) -> None:
        self.is_interacting = False
        self.active_handle = None
        if self.app_state.is_drawing and self.app_state.annotation_mode == 'box' and self.draw_start_pos:
            self.canvas.delete(self.temp_rect)
            self.temp_rect = None
            wx1, wy1 = self.canvas_to_world(*self.draw_start_pos)
            wx2, wy2 = self.canvas_to_world(event.x, event.y)
            if abs(wx2 - wx1) > 2 and abs(wy2 - wy1) > 2:
                on_update_callback(add_new_box=(wx1, wy1, wx2, wy2))
            if Config.AUTO_DISABLE_DRAW_MODE:
                on_update_callback(toggle_draw_mode=True)
            self.draw_start_pos = None
            self.display_image()
            return
        if self.action_mode:
            self.action_mode = None
            idx = self.app_state.selected_annotation_index
            self._update_yolo_string(idx)
            on_update_callback(save_and_refresh=True)
            self.display_image()

    def on_right_click(self, event: tk.Event, on_update_callback: callable) -> None:
        if self.app_state.is_drawing and self.app_state.annotation_mode == 'polygon':
            if len(self.poly_points_buffer) > 2:
                on_update_callback(add_new_poly=self.poly_points_buffer)
                self.poly_points_buffer = []
                if Config.AUTO_DISABLE_DRAW_MODE:
                    on_update_callback(toggle_draw_mode=True)
            else:
                self.poly_points_buffer = []
            self.display_image()

    def on_mouse_hover(self, event: tk.Event) -> None:
        if self.app_state.is_drawing and self.app_state.annotation_mode == 'polygon' and self.poly_points_buffer:
            self.canvas.delete('temp_poly_line')
            last_p = self.poly_points_buffer[-1]
            cx1, cy1 = self.world_to_canvas(*last_p)
            self.canvas.create_line(cx1, cy1, event.x, event.y, fill=Config.NEW_BOX_COLOR, dash=(2, 2), tags='temp_poly_line')
        if self.action_mode or self.pan_start_pos:
            return
        cursor = 'crosshair' if self.app_state.is_drawing else ''
        if not cursor:
            item, _, _ = self.get_item_at(event.x, event.y)
            if item == 'handle':
                cursor = 'sizing' if self.app_state.annotation_mode == 'box' else 'hand2'
            elif item == 'box':
                cursor = 'fleur'
        self.canvas.config(cursor=cursor)

    def on_canvas_resize(self, event: tk.Event) -> None:
        if self.app_state.current_image_index != -1:
            self.reset_view()
            self.display_image()

    def move_selection_by_pixel(self, dx: float, dy: float, on_update: callable) -> None:
        idx = self.app_state.selected_annotation_index
        if idx is None:
            return
        ann = self.app_state.annotations[idx]
        if ann.get('type') == 'polygon':
            new_points = []
            for px, py in ann['points']:
                new_points.append((px + dx, py + dy))
            ann['points'] = new_points
            xs = [p[0] for p in new_points]
            ys = [p[1] for p in new_points]
            ann['rect_orig'] = [min(xs), min(ys), max(xs), max(ys)]
        else:
            rect = ann['rect_orig']
            rect[0] += dx
            rect[1] += dy
            rect[2] += dx
            rect[3] += dy
        self._update_yolo_string(idx)
        on_update(fast_update=True)

    def resize_selection_side(self, side: str, amount: float, on_update: callable) -> None:
        idx = self.app_state.selected_annotation_index
        if idx is None:
            return
        ann = self.app_state.annotations[idx]
        if ann.get('type') == 'polygon':
            return
        rect = ann['rect_orig']
        if side == 'right':
            new_x2 = rect[2] + amount
            if new_x2 > rect[0] + 1:
                rect[2] = new_x2
        elif side == 'bottom':
            new_y2 = rect[3] + amount
            if new_y2 > rect[1] + 1:
                rect[3] = new_y2
        self._update_yolo_string(idx)
        on_update(fast_update=True)

    def _update_yolo_string(self, idx):
        ann = self.app_state.annotations[idx]
        if ann.get('type') == 'polygon':
            ann['yolo_string'] = AnnotationManager.convert_poly_to_yolo(ann['class_id'], ann['points'], self.app_state.original_image_size)
        else:
            ann['yolo_string'] = AnnotationManager.convert_box_to_yolo(ann['class_id'], ann['rect_orig'], self.app_state.original_image_size)