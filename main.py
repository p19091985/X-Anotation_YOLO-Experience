import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from PIL import Image
import os, json, yaml, logging, copy
from typing import List, Tuple, Optional
import localization
import logger_config
from config import Config
from state import AppState
from managers import AnnotationManager, DatasetUtils
from canvas import CanvasController
from ui import UIManager
from window_class_manager import ClassManagerWindow
from window_new_project import NewProjectWindow
from window_split_wizard import SplitWizard
from visualizador_grid import GridViewerWindow
from visualizador_grid import GridViewerWindow
from analisador_dataset import DatasetAnalyzerWindow
from window_about import AboutWindow
logger_config.setup_logging()
logger = logging.getLogger(__name__)

class MainApplication:

    def __init__(self, root: tk.Tk):
        logger.info('Start Application...')
        self.root = root
        self.app_state = AppState()
        self.ann_manager = AnnotationManager()
        self.root.title(Config.APP_NAME)
        self.root.minsize(1024, 700)
        w, h = (self.root.winfo_screenwidth(), self.root.winfo_screenheight())
        try:
            self.root.state('zoomed')
        except:
            self.root.geometry(f'{w}x{h}+0+0')
        self.ui_theme_name = Config.STYLE_THEME
        self._set_theme()
        self._load_config()
        self.ui = UIManager(root, self)
        self.canvas_controller = CanvasController(self.ui.canvas, self.app_state, self.ui)
        self._bind_events()
        self.ui.update_status_bar('Pronto. Segmentation Mode Ativado.')

    def _set_theme(self):
        style = ttk.Style()
        available_themes = style.theme_names()
        if 'clam' in available_themes:
            style.theme_use('clam')
        elif 'alt' in available_themes:
            style.theme_use('alt')
        style.configure('TButton', padding=5)

    def _load_config(self):
        try:
            with open(Config.CONFIG_FILE_PATH, 'r') as f:
                c = json.load(f)
            self.app_state.base_directory = c.get('last_directory', '')
            lang = c.get('language', 'pt_BR')
            localization.set_language(lang)
            if self.app_state.base_directory and os.path.exists(self.app_state.base_directory):
                self.root.after(100, self._load_directory_contents)
        except:
            pass

    def _save_config(self):
        try:
            with open(Config.CONFIG_FILE_PATH, 'w') as f:
                json.dump({'last_directory': self.app_state.base_directory, 'theme': 'default', 'language': localization.get_current_language()}, f)
        except:
            pass

    def save_current_theme(self):
        self._save_config()

    def _bind_events(self):
        self.ui.listbox.bind('<<ListboxSelect>>', self.on_image_select_from_list)
        self.ui.listbox.bind('<Delete>', lambda e: self.delete_image_file(force=False))
        self.ui.listbox.bind('<Shift-Delete>', lambda e: self.delete_image_file(force=True))
        self.ui.annotation_listbox.bind('<<ListboxSelect>>', self.on_annotation_select_from_list)
        self.ui.canvas.bind('<Configure>', self.on_canvas_resize)
        self.ui.canvas.bind('<ButtonPress-1>', self.on_canvas_click_start)
        self.ui.canvas.bind('<B1-Motion>', self.canvas_controller.on_canvas_drag)
        self.ui.canvas.bind('<ButtonRelease-1>', lambda e: self.canvas_controller.on_canvas_release(e, self.process_canvas_update))
        self.ui.canvas.bind('<ButtonPress-3>', lambda e: self.canvas_controller.on_right_click(e, self.process_canvas_update))
        self.ui.canvas.bind('<Motion>', self.canvas_controller.on_mouse_hover)
        self.ui.canvas.bind('<MouseWheel>', self.canvas_controller.on_zoom)
        self.ui.canvas.bind('<ButtonPress-2>', self.canvas_controller.on_pan_start)
        self.ui.canvas.bind('<B2-Motion>', self.canvas_controller.on_pan_move)
        self.ui.canvas.bind('<ButtonRelease-2>', self.canvas_controller.on_pan_end)
        self.root.bind('<Left>', self.handle_left_key)
        self.root.bind('<Right>', self.handle_right_key)
        self.root.bind('<Up>', self.handle_up_key)
        self.root.bind('<Down>', self.handle_down_key)
        self.root.bind('<Delete>', self.delete_current_item)
        self.root.bind('<d>', self.toggle_drawing_mode_event)
        self.root.bind('<D>', self.toggle_drawing_mode_event)
        self.root.bind('<Control-z>', self.undo)
        self.root.protocol('WM_DELETE_WINDOW', self.on_close)

    def toggle_drawing_mode_event(self, e):
        if self.ui.add_box_check.instate(['!disabled']):
            self.ui.add_box_check.invoke()

    def set_annotation_mode(self, mode):
        self.app_state.annotation_mode = mode
        self.app_state.selected_annotation_index = None
        self.canvas_controller.poly_points_buffer = []
        self.canvas_controller.display_image()

    def on_image_select_from_list(self, event):
        sel = self.ui.listbox.curselection()
        if sel:
            self._save_and_refresh()
            self.show_image_at_index(sel[0])

    def on_annotation_select_from_list(self, event):
        sel = self.ui.annotation_listbox.curselection()
        if sel:
            self._select_annotation(sel[0])

    def on_canvas_resize(self, event):
        if self.app_state.current_image_index != -1:
            self.canvas_controller.on_canvas_resize(event)

    def on_canvas_click_start(self, event):
        self.root.focus_set()
        self.canvas_controller.on_canvas_press(event, self.process_canvas_update)

    def handle_left_key(self, event):
        if self.app_state.selected_annotation_index is not None:
            self.save_history()
            self.canvas_controller.move_selection_by_pixel(-1, 0, self.process_canvas_update)
        else:
            self.show_previous_image()

    def handle_right_key(self, event):
        if self.app_state.selected_annotation_index is not None:
            self.save_history()
            self.canvas_controller.move_selection_by_pixel(1, 0, self.process_canvas_update)
        else:
            self.show_next_image()

    def handle_up_key(self, event):
        if self.app_state.selected_annotation_index is not None:
            self.save_history()
            self.canvas_controller.move_selection_by_pixel(0, -1, self.process_canvas_update)

    def handle_down_key(self, event):
        if self.app_state.selected_annotation_index is not None:
            self.save_history()
            self.canvas_controller.move_selection_by_pixel(0, 1, self.process_canvas_update)

    def perform_fine_resize(self, side: str, amount: float):
        if self.app_state.selected_annotation_index is not None:
            self.save_history()
            self.canvas_controller.resize_selection_side(side, amount, self.process_canvas_update)

    def perform_fine_move(self, dx: int, dy: int):
        if self.app_state.selected_annotation_index is not None:
            self.save_history()
            self.canvas_controller.move_selection_by_pixel(dx, dy, self.process_canvas_update)

    def _load_directory_contents(self):
        self.app_state.current_image_index = -1
        self.app_state.data_is_safe_to_save = False
        self.app_state.annotations = []
        self.app_state.undo_stack = []
        if self.app_state.is_drawing:
            self.toggle_drawing_mode(force_state=False)
        self.ui.dir_label.config(text=f'{localization.tr('COL_FOLDER')}: {os.path.basename(self.app_state.base_directory)}')
        self._load_class_names()
        valid = ('.png', '.jpg', '.jpeg', '.bmp')
        self.app_state.image_paths = []
        for r, _, files in os.walk(self.app_state.base_directory):
            if 'labels' in r:
                continue
            for f in sorted(files):
                if f.lower().endswith(valid):
                    self.app_state.image_paths.append(os.path.join(r, f))
        self.ui.refresh_image_list()
        if self.app_state.image_paths:
            self.ui.add_box_check.config(state='normal')
            self.show_image_at_index(0)
        else:
            self.app_state.current_pil_image = None
            self.canvas_controller.displayed_photo = None
            self.ui.canvas.delete('all')
            self.app_state.current_image_index = -1
            self.ui.dir_label.config(text=f'{localization.tr('COL_FOLDER')}: {os.path.basename(self.app_state.base_directory)} (Empty)')
            self.ui.status_label.config(text='--')
            self.ui.annotation_listbox.delete(0, tk.END)
            self.ui.add_box_check.config(state='disabled')

    def show_image_at_index(self, index):
        if not 0 <= index < len(self.app_state.image_paths):
            return
        self.app_state.data_is_safe_to_save = False
        self.app_state.undo_stack.clear()
        self.deselect_all()
        self.app_state.current_image_index = index
        p = self.app_state.get_current_image_path()
        try:
            im = Image.open(p).convert('RGB')
            self.app_state.current_pil_image = im
            self.app_state.original_image_size = im.size
            lp = self.ann_manager.get_label_path(p)
            anns, err = self.ann_manager.load_annotations(lp, im.size)
            if err:
                self.app_state.annotations = []
                logger.error(f'Erro label: {err}')
            else:
                self.app_state.annotations = anns
                self.app_state.data_is_safe_to_save = True
            self.canvas_controller.reset_view()
            self.canvas_controller.display_image()
            self.ui.sync_ui_to_state()
        except Exception as e:
            messagebox.showerror('Erro Imagem', str(e))

    def process_canvas_update(self, **kwargs):
        if kwargs.get('save_history'):
            self.save_history()
        if kwargs.get('add_new_box'):
            self._add_new_shape('box', kwargs['add_new_box'])
        if kwargs.get('add_new_poly'):
            self._add_new_shape('polygon', kwargs['add_new_poly'])
        if kwargs.get('select_annotation_idx') is not None:
            self._select_annotation(kwargs['select_annotation_idx'])
        if kwargs.get('deselect_all'):
            self.deselect_all()
        if kwargs.get('toggle_draw_mode'):
            self.toggle_drawing_mode(force_state=False)
        if kwargs.get('fast_update'):
            self._save_and_refresh(self.app_state.selected_annotation_index, update_listbox=False)
        elif kwargs.get('save_and_refresh'):
            self._save_and_refresh(self.app_state.selected_annotation_index, update_listbox=True)
        if self.app_state.selected_annotation_index is not None:
            idx = self.app_state.selected_annotation_index
            if idx < len(self.app_state.annotations):
                rect = self.app_state.annotations[idx]['rect_orig']
                self.ui.update_inspector_values(rect)

    def _save_and_refresh(self, new_selection=None, update_listbox=True):
        if self.app_state.current_image_index == -1 or not self.app_state.data_is_safe_to_save:
            return
        lp = self.ann_manager.get_label_path(self.app_state.get_current_image_path())
        if self.ann_manager.save_annotations(lp, self.app_state.annotations):
            if update_listbox:
                self.ui.refresh_annotation_list()
            if new_selection is not None:
                self._select_annotation(new_selection)
            self.canvas_controller.display_image()

    def _add_new_shape(self, shape_type, data):
        cid = self._ask_for_class_id()
        if cid is None:
            return
        self.save_history()
        if shape_type == 'box':
            x1, y1, x2, y2 = data
            rect = [min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2)]
            yolo = self.ann_manager.convert_box_to_yolo(cid, tuple(rect), self.app_state.original_image_size)
            self.app_state.annotations.append({'type': 'box', 'yolo_string': yolo, 'rect_orig': rect, 'class_id': cid, 'points': []})
        elif shape_type == 'polygon':
            points = data
            xs = [p[0] for p in points]
            ys = [p[1] for p in points]
            rect = [min(xs), min(ys), max(xs), max(ys)]
            yolo = self.ann_manager.convert_poly_to_yolo(cid, points, self.app_state.original_image_size)
            self.app_state.annotations.append({'type': 'polygon', 'yolo_string': yolo, 'rect_orig': rect, 'class_id': cid, 'points': points})
        self._save_and_refresh(len(self.app_state.annotations) - 1)

    def _select_annotation(self, idx):
        self.app_state.selected_annotation_index = idx
        self.ui.sync_ui_to_state()
        self.canvas_controller.display_image()

    def deselect_all(self, e=None):
        self.app_state.selected_annotation_index = None
        self.ui.sync_ui_to_state()
        self.canvas_controller.display_image()
        return 'break'

    def show_previous_image(self):
        if self.app_state.current_image_index > 0:
            self._save_and_refresh()
            self.show_image_at_index(self.app_state.current_image_index - 1)

    def show_next_image(self):
        if self.app_state.current_image_index < len(self.app_state.image_paths) - 1:
            self._save_and_refresh()
            self.show_image_at_index(self.app_state.current_image_index + 1)

    def save_history(self):
        self.app_state.undo_stack.append(copy.deepcopy(self.app_state.annotations))
        if len(self.app_state.undo_stack) > 50:
            self.app_state.undo_stack.pop(0)

    def undo(self, e=None):
        if self.app_state.undo_stack:
            self.app_state.annotations = self.app_state.undo_stack.pop()
            self._save_and_refresh()

    def delete_current_item(self, e=None):
        if self.app_state.selected_annotation_index is not None:
            self.save_history()
            self.app_state.annotations.pop(self.app_state.selected_annotation_index)
            self.deselect_all()
            self._save_and_refresh()

    def delete_image_file(self, force=False):
        sel = self.ui.listbox.curselection()
        if not sel:
            return
        index = sel[0]
        image_path = self.app_state.image_paths[index]
        image_name = os.path.basename(image_path)
        label_path = self.ann_manager.get_label_path(image_path)
        if not force:
            confirm = messagebox.askyesno('Excluir Imagem', f'Excluir: {image_name}?', icon='warning', parent=self.root)
            if not confirm:
                return
        try:
            if self.app_state.current_image_index == index:
                self.app_state.current_pil_image = None
                self.canvas_controller.displayed_photo = None
                self.ui.canvas.delete('all')
            if os.path.exists(image_path):
                os.remove(image_path)
            if os.path.exists(label_path):
                os.remove(label_path)
            self.app_state.image_paths.pop(index)
            self.ui.listbox.delete(index)
            new_index = min(index, len(self.app_state.image_paths) - 1)
            if new_index >= 0:
                self.ui.listbox.selection_set(new_index)
                self.show_image_at_index(new_index)
            else:
                self.app_state.current_image_index = -1
                self.ui.dir_label.config(text='Pasta vazia')
                self.ui.status_label.config(text='--')
                self.ui.annotation_listbox.delete(0, tk.END)
        except Exception as e:
            messagebox.showerror('Erro', str(e))

    def change_annotation_class(self):
        if self.app_state.selected_annotation_index is None:
            return
        try:
            new_id = self.app_state.class_names.index(self.ui.class_id_var.get())
            self.save_history()
            self.app_state.annotations[self.app_state.selected_annotation_index]['class_id'] = new_id
            idx = self.app_state.selected_annotation_index
            self.canvas_controller._update_yolo_string(idx)
            self._save_and_refresh(idx)
        except:
            pass

    def toggle_drawing_mode(self, force_state: Optional[bool]=None):
        if self.app_state.current_image_index == -1 or not self.app_state.current_pil_image:
            self.ui.drawing_mode_var.set(False)
            self.app_state.is_drawing = False
            return
        if force_state is not None:
            self.ui.drawing_mode_var.set(force_state)
        self.app_state.is_drawing = self.ui.drawing_mode_var.get()
        self.deselect_all()
        mode_txt = 'Polígono' if self.app_state.annotation_mode == 'polygon' else 'Box'
        status = f'Modo Desenho: ON ({mode_txt})' if self.app_state.is_drawing else 'Modo de Navegação'
        self.ui.update_status_bar(status)
        self.ui.canvas.config(cursor='crosshair' if self.app_state.is_drawing else '')

    def _load_class_names(self):
        self.app_state.class_names = []
        p = os.path.join(self.app_state.base_directory, 'classes.txt')
        if os.path.exists(p):
            with open(p, 'r') as f:
                self.app_state.class_names = [x.strip() for x in f if x.strip()]
        self.ui.update_class_selector()

    def _ask_for_class_id(self):
        if not self.app_state.class_names:
            return simpledialog.askinteger('Classe', 'ID:', parent=self.root)
        w = tk.Toplevel(self.root)
        w.geometry('250x100')
        w.title('Classe')
        v = tk.StringVar(value=self.app_state.class_names[0])
        ttk.Combobox(w, textvariable=v, values=self.app_state.class_names).pack(pady=10)
        res = []

        def ok():
            res.append(v.get())
            w.destroy()
        ttk.Button(w, text='OK', command=ok).pack()
        self.root.wait_window(w)
        if res:
            try:
                return self.app_state.class_names.index(res[0])
            except:
                return 0
        return None

    def on_project_created(self, path):
        self.app_state.base_directory = path
        self._save_config()
        self._load_directory_contents()
        self.root.lift()

    def open_new_project_wizard(self):
        NewProjectWindow(self.root, self.on_project_created)

    def refresh_directory(self):
        self._load_directory_contents()

    def open_class_manager(self):
        ClassManagerWindow(self.root, self.app_state.class_names, self._on_classes_updated)

    def _on_classes_updated(self, l):
        self.app_state.class_names = l
        with open(os.path.join(self.app_state.base_directory, 'classes.txt'), 'w') as f:
            f.write('\n'.join(l))
        self.ui.update_class_selector()
        self.show_image_at_index(self.app_state.current_image_index)

    def perform_dataset_split(self, train, val, test, shuffle):
        if not self.app_state.base_directory:
            return
        try:
            DatasetUtils.split_dataset(base_dir=self.app_state.base_directory, train_ratio=train, val_ratio=val, test_ratio=test, shuffle=shuffle)
            messagebox.showinfo('Sucesso', 'Dataset dividido com sucesso! As pastas train/val/test foram criadas.')
            self.refresh_directory()
        except Exception as e:
            messagebox.showerror('Erro', f'Falha ao dividir dataset: {str(e)}')

    def open_split_wizard(self):
        SplitWizard(self.root, self.perform_dataset_split)

    def open_grid_viewer(self):
        if not self.app_state.image_paths:
            messagebox.showwarning('Aviso', 'Abra um dataset.')
            return
        GridViewerWindow(self.root, self)

    def open_dataset_analyzer(self):
        if not self.app_state.base_directory:
            messagebox.showwarning('Aviso', 'Abra um dataset.')
            return
        DatasetAnalyzerWindow(self.root, self.app_state.base_directory, self.app_state.class_names)

    def select_directory(self):
        p = filedialog.askdirectory()
        if p:
            self.app_state.base_directory = p
            self._load_directory_contents()
            self._save_config()

    def show_about_dialog(self):
        localization.reload()
        AboutWindow(self.root)

    def change_language(self, code):
        localization.set_language(code)
        self._save_config()
        self.ui.refresh_ui()

    def on_close(self):
        if self.app_state.data_is_safe_to_save:
            self._save_and_refresh()
        self._save_config()
        self.root.destroy()
if __name__ == '__main__':
    root = tk.Tk()
    app = MainApplication(root)
    root.mainloop()