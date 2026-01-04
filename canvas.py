import tkinter as tk
from PIL import Image, ImageTk, ImageDraw, ImageFont
from typing import Tuple, Optional, List, TYPE_CHECKING
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
        draw = ImageDraw.Draw(display_image)
        img_w_orig, img_h_orig = self.app_state.original_image_size
        for i, ann in enumerate(self.app_state.annotations):
            rx1, ry1, rx2, ry2 = ann['rect_orig']
            x1, x2 = (min(rx1, rx2), max(rx1, rx2))
            y1, y2 = (min(ry1, ry2), max(ry1, ry2))
            sx1 = x1 / img_w_orig * final_w
            sy1 = y1 / img_h_orig * final_h
            sx2 = x2 / img_w_orig * final_w
            sy2 = y2 / img_h_orig * final_h
            is_selected = i == self.app_state.selected_annotation_index
            class_id = ann['class_id']
            base_color = self._get_color_for_class(class_id)
            outline_color = Config.HIGHLIGHT_COLOR if is_selected else base_color
            line_width = Config.HIGHLIGHT_WIDTH if is_selected else Config.BOX_WIDTH
            draw.rectangle([sx1, sy1, sx2, sy2], outline=outline_color, width=line_width)
            label_text = str(class_id)
            if 0 <= class_id < len(self.app_state.class_names):
                label_text = f' {self.app_state.class_names[class_id]} '
            bbox = draw.textbbox((0, 0), label_text, font=self.font)
            text_w = bbox[2] - bbox[0]
            text_h = bbox[3] - bbox[1] + 4
            text_x = sx1
            text_y = sy1 - text_h
            if text_y < 0:
                text_y = sy1
            draw.rectangle([text_x, text_y, text_x + text_w, text_y + text_h], fill=base_color)
            draw.text((text_x, text_y), label_text, fill='white', font=self.font)
        self.displayed_photo = ImageTk.PhotoImage(display_image)
        cw, ch = (self.canvas.winfo_width(), self.canvas.winfo_height())
        pos_x = cw / 2 + self.pan_offset[0]
        pos_y = ch / 2 + self.pan_offset[1]
        self.canvas.create_image(pos_x, pos_y, anchor=tk.CENTER, image=self.displayed_photo, tags='image')
        if self.app_state.selected_annotation_index is not None:
            self._draw_handles()

    def _draw_handles(self) -> None:
        self.canvas.delete('handles')
        idx = self.app_state.selected_annotation_index
        if idx is None or idx >= len(self.app_state.annotations):
            return
        rect = self.app_state.annotations[idx]['rect_orig']
        x1, x2 = (min(rect[0], rect[2]), max(rect[0], rect[2]))
        y1, y2 = (min(rect[1], rect[3]), max(rect[1], rect[3]))
        coords = [(x1, y1, 'nw'), (x2, y1, 'ne'), (x1, y2, 'sw'), (x2, y2, 'se')]
        s = 5
        for wx, wy, tag in coords:
            cx, cy = self.world_to_canvas(wx, wy)
            self.canvas.create_rectangle(cx - s, cy - s, cx + s, cy + s, fill='white', outline='black', tags=('handles', tag))

    def get_item_at(self, event_x: int, event_y: int) -> Tuple[Optional[str], Optional[int], Optional[str]]:
        if self.app_state.selected_annotation_index is not None:
            item = self.canvas.find_closest(event_x, event_y, halo=6)
            if item:
                tags = self.canvas.gettags(item[0])
                if 'handles' in tags:
                    handle_type = None
                    for t in tags:
                        if t in ['nw', 'ne', 'sw', 'se']:
                            handle_type = t
                            break
                    return ('handle', self.app_state.selected_annotation_index, handle_type)
        for i in range(len(self.app_state.annotations) - 1, -1, -1):
            ann = self.app_state.annotations[i]
            rect = ann['rect_orig']
            wx, wy = self.canvas_to_world(event_x, event_y)
            min_x, max_x = sorted((rect[0], rect[2]))
            min_y, max_y = sorted((rect[1], rect[3]))
            hit_box = min_x <= wx <= max_x and min_y <= wy <= max_y
            cx1, cy1 = self.world_to_canvas(min_x, min_y)
            class_id = ann['class_id']
            label_text = str(class_id)
            if 0 <= class_id < len(self.app_state.class_names):
                label_text = f' {self.app_state.class_names[class_id]} '
            bbox = self.font.getbbox(label_text)
            text_w = bbox[2] - bbox[0]
            text_h = bbox[3] - bbox[1] + 4
            text_x = cx1
            text_y = cy1 - text_h
            if text_y < 0:
                text_y = cy1
            hit_text = text_x <= event_x <= text_x + text_w and text_y <= event_y <= text_y + text_h
            if hit_box or hit_text:
                return ('box', i, None)
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
        if self.app_state.is_drawing:
            self.draw_start_pos = (event.x, event.y)
            self.temp_rect = self.canvas.create_rectangle(event.x, event.y, event.x, event.y, outline=Config.NEW_BOX_COLOR, width=2, dash=(4, 2))
            self.temp_text = self.canvas.create_text(event.x + 5, event.y - 10, anchor='w', text='', fill=Config.DIMENSION_TEXT_COLOR)
            return
        item_type, item_index, handle_type = self.get_item_at(event.x, event.y)
        if item_type == 'handle' or item_type == 'box':
            on_update_callback(save_history=True)
        if item_type == 'handle':
            self.action_mode = 'resizing'
            self.active_handle = handle_type
            self.drag_start_pos = (event.x, event.y)
            self.original_drag_rect = self.app_state.annotations[item_index]['rect_orig'][:]
        elif item_type == 'box':
            if item_index != self.app_state.selected_annotation_index:
                on_update_callback(select_annotation_idx=item_index)
            self.action_mode = 'moving'
            self.drag_start_pos = (event.x, event.y)
            self.original_drag_rect = self.app_state.annotations[item_index]['rect_orig'][:]
        else:
            on_update_callback(deselect_all=True)

    def on_canvas_drag(self, event: tk.Event) -> None:
        self.is_interacting = True
        if self.app_state.is_drawing and self.temp_rect:
            x1, y1 = self.draw_start_pos
            self.canvas.coords(self.temp_rect, x1, y1, event.x, event.y)
            wx1, wy1 = self.canvas_to_world(x1, y1)
            wx2, wy2 = self.canvas_to_world(event.x, event.y)
            self.canvas.coords(self.temp_text, event.x + 5, event.y - 10)
            self.canvas.itemconfig(self.temp_text, text=f'{abs(wx2 - wx1):.0f}x{abs(wy2 - wy1):.0f}')
            return
        if self.action_mode and self.drag_start_pos and self.original_drag_rect:
            cur_wx, cur_wy = self.canvas_to_world(event.x, event.y)
            start_wx, start_wy = self.canvas_to_world(*self.drag_start_pos)
            dx = cur_wx - start_wx
            dy = cur_wy - start_wy
            rect = list(self.original_drag_rect)
            if self.action_mode == 'moving':
                rect[0] += dx
                rect[1] += dy
                rect[2] += dx
                rect[3] += dy
            elif self.action_mode == 'resizing' and self.active_handle:
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
                rect = [min_x, min_y, max_x, max_y]
            self.app_state.annotations[self.app_state.selected_annotation_index]['rect_orig'] = rect
            self.display_image()

    def on_canvas_release(self, event: tk.Event, on_update_callback: callable) -> None:
        self.is_interacting = False
        self.active_handle = None
        if self.app_state.is_drawing and self.draw_start_pos:
            self.canvas.delete(self.temp_rect)
            self.canvas.delete(self.temp_text)
            self.temp_rect = None
            self.temp_text = None
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
            rect = self.app_state.annotations[idx]['rect_orig']
            x1, x2 = (min(rect[0], rect[2]), max(rect[0], rect[2]))
            y1, y2 = (min(rect[1], rect[3]), max(rect[1], rect[3]))
            self.app_state.annotations[idx]['rect_orig'] = [x1, y1, x2, y2]
            self._update_yolo_string(idx)
            on_update_callback(save_and_refresh=True)
            self.display_image()

    def on_mouse_hover(self, event: tk.Event) -> None:
        if self.action_mode or self.pan_start_pos:
            return
        cursor = 'crosshair' if self.app_state.is_drawing else ''
        if not cursor:
            item, _, _ = self.get_item_at(event.x, event.y)
            if item == 'handle':
                cursor = 'sizing'
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
        rect = self.app_state.annotations[idx]['rect_orig']
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
        rect = self.app_state.annotations[idx]['rect_orig']
        x1, x2 = (min(rect[0], rect[2]), max(rect[0], rect[2]))
        y1, y2 = (min(rect[1], rect[3]), max(rect[1], rect[3]))
        if side == 'top':
            y1 -= amount
        elif side == 'bottom':
            y2 += amount
        elif side == 'left':
            x1 -= amount
        elif side == 'right':
            x2 += amount
        self.app_state.annotations[idx]['rect_orig'] = [x1, y1, x2, y2]
        self._update_yolo_string(idx)
        on_update(fast_update=True)

    def _update_yolo_string(self, idx):
        rect = self.app_state.annotations[idx]['rect_orig']
        self.app_state.annotations[idx]['yolo_string'] = AnnotationManager.convert_to_yolo_format(self.app_state.annotations[idx]['class_id'], tuple(rect), self.app_state.original_image_size)