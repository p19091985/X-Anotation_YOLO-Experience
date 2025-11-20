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
        if item_type and (item_type.startswith('handle_') or item_type == 'box'):
            on_update_callback(save_history=True)
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