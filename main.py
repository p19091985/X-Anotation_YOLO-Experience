import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from dataclasses import dataclass
from pathlib import Path
from PIL import Image
import os, json, yaml, logging, copy, random, shutil
from typing import List, Tuple, Optional
import localization
import logger_config
from config import Config
from state import AppState
from managers import AnnotationManager, ClassCatalogManager, DatasetUtils
from canvas import CanvasController
from ui import UIManager
from window_class_manager import ClassManagerWindow
from window_new_project import NewProjectWindow
from window_split_wizard import SplitWizard
from visualizador_grid import GridViewerWindow
from analisador_dataset import DatasetAnalyzerWindow
from window_about import AboutWindow
from utils_ui import center_window, maximize_window
logger_config.setup_logging()
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DatasetCopyOptions:
    remove_missing_labels: bool = False
    remove_empty_labels: bool = False
    reduce_percentage: int = 0


@dataclass(frozen=True)
class DatasetCopyPlan:
    total_images: int
    images_to_copy: Tuple[str, ...]
    removed_missing_labels: int = 0
    removed_empty_labels: int = 0
    removed_by_reduction: int = 0

    @property
    def copied_count(self) -> int:
        return len(self.images_to_copy)

    @property
    def removed_total(self) -> int:
        return self.removed_missing_labels + self.removed_empty_labels + self.removed_by_reduction


class MainApplication:

    def __init__(self, root: tk.Tk):
        logger.info('Start Application...')
        self.root = root
        self.app_state = AppState()
        self.ann_manager = AnnotationManager()
        self.root.title(Config.APP_NAME)
        self.root.minsize(1024, 700)
        maximize_window(self.root)
        self.ui_theme_name = Config.STYLE_THEME
        self._set_theme()
        self._load_config()
        self.ui = UIManager(root, self)
        self.canvas_controller = CanvasController(self.ui.canvas, self.app_state, self.ui)
        self.canvas_controller.on_zoom_changed = self.ui.sync_zoom_display
        self._bind_events()
        self.ui.update_status_bar('Pronto.')

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
                config_data = json.load(f)
            self.app_state.base_directory = self._resolve_saved_directory(config_data.get('last_directory', ''))
            lang = config_data.get('language', 'pt_BR')
            localization.set_language(lang)
            if self.app_state.base_directory and os.path.exists(self.app_state.base_directory):
                self.root.after(100, self._load_directory_contents)
        except Exception:
            self.app_state.base_directory = ''

    def _save_config(self):
        try:
            with open(Config.CONFIG_FILE_PATH, 'w') as f:
                json.dump(
                    {
                        'last_directory': self._serialize_directory(self.app_state.base_directory),
                        'theme': 'default',
                        'language': localization.get_current_language(),
                    },
                    f
                )
        except Exception:
            logger.exception('Falha ao salvar configuracao local.')

    def _resolve_saved_directory(self, raw_path: str) -> str:
        if not raw_path:
            return ''
        path = Path(raw_path)
        candidates = [path]
        if not path.is_absolute():
            candidates.insert(0, Path.cwd() / path)
        for candidate in candidates:
            if candidate.exists():
                return str(candidate.resolve())
        return ''

    def _serialize_directory(self, directory: str) -> str:
        if not directory:
            return ''
        resolved = Path(directory).resolve()
        try:
            return str(resolved.relative_to(Path.cwd()))
        except ValueError:
            return str(resolved)

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
        self.ui.canvas.bind('<Control-MouseWheel>', self.canvas_controller.on_ctrl_zoom)
        self.ui.canvas.bind('<Button-4>', self.canvas_controller.on_zoom)
        self.ui.canvas.bind('<Button-5>', self.canvas_controller.on_zoom)
        self.ui.canvas.bind('<Control-Button-4>', self.canvas_controller.on_ctrl_zoom)
        self.ui.canvas.bind('<Control-Button-5>', self.canvas_controller.on_ctrl_zoom)
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
        self.root.bind('<p>', lambda e: self.ui.set_pan_mode())
        self.root.bind('<P>', lambda e: self.ui.set_pan_mode())
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
        if self.app_state.is_drawing:
            mode_txt = 'Polígono' if self.app_state.annotation_mode == 'polygon' else 'Box'
            self.ui.update_status_bar(f'Modo Desenho: ON ({mode_txt})')

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
        self.ui.dir_label.config(text=f"{localization.tr('COL_FOLDER')}: {os.path.basename(self.app_state.base_directory)}")
        self._load_class_names()
        valid = ('.png', '.jpg', '.jpeg', '.bmp')
        self.app_state.image_paths = []
        for r, dirs, files in os.walk(self.app_state.base_directory):
            dirs[:] = [directory for directory in dirs if directory.casefold() != 'labels']
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
            self.ui.dir_label.config(text=f"{localization.tr('COL_FOLDER')}: {os.path.basename(self.app_state.base_directory)} (Empty)")
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
            self.ui.sync_ui_to_state()
            self._fit_current_image_to_canvas_when_ready(index)
        except Exception as e:
            messagebox.showerror('Erro Imagem', str(e))

    def _fit_current_image_to_canvas_when_ready(self, image_index: int, retries: int=8):
        if self.app_state.current_image_index != image_index or not self.app_state.current_pil_image:
            return

        canvas_width = self.ui.canvas.winfo_width()
        canvas_height = self.ui.canvas.winfo_height()
        if canvas_width > 1 and canvas_height > 1:
            self.canvas_controller.reset_view()
            self.canvas_controller.display_image()
            return

        if retries <= 0:
            self.canvas_controller.display_image()
            return

        self.root.after(30, lambda: self._fit_current_image_to_canvas_when_ready(image_index, retries - 1))

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

    def _save_current_annotations_before_bulk_cleanup(self):
        current_image_path = self.app_state.get_current_image_path()
        if not current_image_path or not getattr(self.app_state, 'data_is_safe_to_save', False):
            return
        label_path = self.ann_manager.get_label_path(current_image_path)
        if os.path.isfile(label_path) or self.app_state.annotations:
            self._save_and_refresh(update_listbox=False)

    def _label_file_is_empty(self, label_path: str) -> bool:
        try:
            with open(label_path, 'r', encoding='utf-8') as handle:
                return not any(line.strip() for line in handle)
        except OSError:
            return False

    def _delete_image_paths(
        self,
        image_paths: List[str],
        remove_associated_labels: bool=False,
        remove_empty_label_files: bool=False,
    ) -> Tuple[int, List[str]]:
        removed_count = 0
        errors = []
        for image_path in image_paths:
            label_path = self.ann_manager.get_label_path(image_path)
            try:
                image_removed = False
                if os.path.exists(image_path):
                    os.remove(image_path)
                    image_removed = True
                    removed_count += 1
                should_remove_label = (
                    remove_associated_labels
                    or (remove_empty_label_files and self._label_file_is_empty(label_path))
                )
                if image_removed and should_remove_label and os.path.isfile(label_path):
                    os.remove(label_path)
            except Exception as exc:
                errors.append(f'{os.path.basename(image_path)}: {exc}')
        return (removed_count, errors)

    def _get_unlabeled_cleanup_groups(self) -> Tuple[List[str], List[str]]:
        missing_label_images = []
        empty_label_images = []
        for image_path in self.app_state.image_paths:
            label_path = self.ann_manager.get_label_path(image_path)
            if not os.path.isfile(label_path):
                missing_label_images.append(image_path)
            elif self._label_file_is_empty(label_path):
                empty_label_images.append(image_path)
        return (missing_label_images, empty_label_images)

    def _format_cleanup_preview(self, image_paths: List[str]) -> str:
        if not image_paths:
            return 'Nenhuma imagem selecionada para remocao.'
        preview_limit = 10
        preview_items = [
            os.path.relpath(image_path, self.app_state.base_directory)
            for image_path in image_paths[:preview_limit]
        ]
        preview = '\n'.join(preview_items)
        remaining = len(image_paths) - preview_limit
        if remaining > 0:
            preview += f'\n... e mais {remaining} imagem(ns)'
        return preview

    def _ask_remove_unlabeled_cleanup_options(self, missing_label_images: List[str], empty_label_images: List[str]) -> Optional[bool]:
        dialog = tk.Toplevel(self.root)
        dialog.title('Limpeza de imagens')
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()

        include_empty_labels = tk.BooleanVar(value=False)
        result = {'confirmed': False, 'include_empty_labels': False}

        container = ttk.Frame(dialog, padding=14)
        container.pack(fill=tk.BOTH, expand=True)

        ttk.Label(
            container,
            text='Remover imagens sem label',
            font=Config.FONTS['main_bold'],
        ).pack(anchor='w')
        ttk.Label(
            container,
            text=(
                f'{len(missing_label_images)} imagem(ns) sem arquivo .txt associado.\n'
                f'{len(empty_label_images)} imagem(ns) com arquivo .txt vazio.'
            ),
            justify='left',
            wraplength=520,
        ).pack(anchor='w', pady=(8, 6))

        empty_check = ttk.Checkbutton(
            container,
            text='Remover tambem imagens com label vazio',
            variable=include_empty_labels,
        )
        empty_check.pack(anchor='w', pady=(0, 8))
        if not empty_label_images:
            empty_check.config(state='disabled')

        ttk.Label(
            container,
            text='Arquivos que serao removidos:',
            font=Config.FONTS['main_bold'],
        ).pack(anchor='w')
        preview_label = ttk.Label(container, justify='left', wraplength=520)
        preview_label.pack(anchor='w', fill=tk.X, pady=(4, 10))

        ttk.Label(
            container,
            text='Esta acao exclui permanentemente as imagens selecionadas do dataset.',
            foreground='#A33',
            wraplength=520,
        ).pack(anchor='w', pady=(0, 12))

        button_frame = ttk.Frame(container)
        button_frame.pack(fill=tk.X)

        def selected_images():
            if include_empty_labels.get():
                return missing_label_images + empty_label_images
            return missing_label_images

        def update_preview(*_):
            images_to_remove = selected_images()
            preview_label.config(text=self._format_cleanup_preview(images_to_remove))
            remove_button.config(state='normal' if images_to_remove else 'disabled')

        def confirm():
            result['confirmed'] = True
            result['include_empty_labels'] = include_empty_labels.get()
            dialog.destroy()

        def cancel():
            dialog.destroy()

        ttk.Button(button_frame, text='Cancelar', command=cancel).pack(side=tk.RIGHT)
        remove_button = ttk.Button(button_frame, text='Remover', command=confirm)
        remove_button.pack(side=tk.RIGHT, padx=(0, 8))

        include_empty_labels.trace_add('write', update_preview)
        update_preview()
        dialog.protocol('WM_DELETE_WINDOW', cancel)
        try:
            center_window(dialog, self.root)
        except Exception:
            pass
        dialog.wait_window()

        if not result['confirmed']:
            return None
        return bool(result['include_empty_labels'])

    def _build_dataset_copy_plan(self, options: DatasetCopyOptions) -> DatasetCopyPlan:
        total_images = len(self.app_state.image_paths)
        missing_label_images = []
        empty_label_images = []
        cleanup_exclusions = set()
        removed_missing_labels = 0
        removed_empty_labels = 0

        if options.remove_missing_labels or options.remove_empty_labels:
            missing_label_images, empty_label_images = self._get_unlabeled_cleanup_groups()
            if options.remove_missing_labels:
                cleanup_exclusions.update(missing_label_images)
                removed_missing_labels = len(missing_label_images)
            if options.remove_empty_labels:
                cleanup_exclusions.update(empty_label_images)
                removed_empty_labels = len(empty_label_images)

        candidate_images = [
            image_path
            for image_path in self.app_state.image_paths
            if image_path not in cleanup_exclusions
        ]

        removed_by_reduction = 0
        images_to_copy = list(candidate_images)
        if options.reduce_percentage > 0:
            removed_by_reduction = self._calculate_dataset_reduction_count(len(candidate_images), options.reduce_percentage)
            if removed_by_reduction > 0:
                excluded_by_reduction = set(random.sample(candidate_images, removed_by_reduction))
                images_to_copy = [
                    image_path
                    for image_path in candidate_images
                    if image_path not in excluded_by_reduction
                ]

        return DatasetCopyPlan(
            total_images=total_images,
            images_to_copy=tuple(images_to_copy),
            removed_missing_labels=removed_missing_labels,
            removed_empty_labels=removed_empty_labels,
            removed_by_reduction=removed_by_reduction,
        )

    def _format_dataset_copy_plan_summary(self, plan: DatasetCopyPlan, copied_count: Optional[int]=None) -> str:
        copied = plan.copied_count if copied_count is None else copied_count
        lines = [
            f'Total original: {plan.total_images} imagem(ns)',
            f'Copiadas na nova pasta: {copied} imagem(ns)',
        ]
        if plan.removed_missing_labels:
            lines.append(f'Fora da copia por falta de label: {plan.removed_missing_labels} imagem(ns)')
        if plan.removed_empty_labels:
            lines.append(f'Fora da copia por label vazio: {plan.removed_empty_labels} imagem(ns)')
        if plan.removed_by_reduction:
            lines.append(f'Fora da copia por reducao aleatoria: {plan.removed_by_reduction} imagem(ns)')
        return '\n'.join(lines)

    def _build_dataset_copy_directory(self, options: DatasetCopyOptions, plan: DatasetCopyPlan) -> Path:
        base_path = Path(self.app_state.base_directory).resolve()
        keep_percentage = int(round((plan.copied_count / plan.total_images) * 100)) if plan.total_images else 0

        if (
            options.reduce_percentage > 0
            and not options.remove_missing_labels
            and not options.remove_empty_labels
        ):
            target_name = f'{base_path.name}_reduzido_{keep_percentage}pct'
        else:
            name_parts = ['copia']
            if options.remove_missing_labels:
                name_parts.append('sem_label')
            if options.remove_empty_labels:
                name_parts.append('sem_vazio')
            if options.reduce_percentage > 0:
                name_parts.append(f'reduzido_{keep_percentage}pct')
            target_name = f'{base_path.name}_' + '_'.join(name_parts)

        candidate = base_path.parent / target_name
        suffix = 2
        while candidate.exists():
            candidate = base_path.parent / f'{target_name}_{suffix}'
            suffix += 1
        return candidate

    def _create_dataset_copy(self, options: DatasetCopyOptions) -> Optional[Path]:
        if not self.app_state.base_directory or not self.app_state.image_paths:
            messagebox.showwarning('Aviso', 'Abra um dataset com imagens.', parent=self.root)
            return None

        self._save_current_annotations_before_bulk_cleanup()
        plan = self._build_dataset_copy_plan(options)

        if plan.removed_total <= 0:
            messagebox.showinfo('Copia do dataset', 'Nenhuma imagem seria alterada com as opcoes escolhidas.', parent=self.root)
            return None

        if plan.copied_count <= 0:
            messagebox.showinfo('Copia do dataset', 'Nenhuma imagem restou para compor a nova copia.', parent=self.root)
            return None

        target_dir = self._build_dataset_copy_directory(options, plan)
        try:
            copied_count, errors = self._copy_selected_dataset_files(list(plan.images_to_copy), target_dir)
        except Exception as exc:
            messagebox.showerror('Erro', f'Falha ao criar copia derivada:\n\n{exc}', parent=self.root)
            return None

        summary = self._format_dataset_copy_plan_summary(plan, copied_count=copied_count)
        if errors:
            details = '\n'.join(errors[:5])
            if len(errors) > 5:
                details += f'\n... e mais {len(errors) - 5} erro(s)'
            messagebox.showwarning(
                'Copia parcial',
                f'Copia criada em:\n{target_dir}\n\n{summary}\n\nAlguns arquivos falharam:\n\n{details}',
                parent=self.root,
            )
        else:
            messagebox.showinfo(
                'Copia derivada criada',
                f'Copia criada em:\n{target_dir}\n\n{summary}',
                parent=self.root,
            )

        return target_dir

    def _ask_dataset_copy_options(self) -> Optional[DatasetCopyOptions]:
        total_images = len(self.app_state.image_paths)
        if total_images <= 0:
            messagebox.showwarning('Aviso', 'Abra um dataset com imagens.', parent=self.root)
            return None

        missing_label_images, empty_label_images = self._get_unlabeled_cleanup_groups()
        allow_cleanup = Config.FEATURE_SHOW_REMOVE_UNLABELED
        allow_reduction = Config.FEATURE_SHOW_REDUCE_DATASET

        dialog = tk.Toplevel(self.root)
        dialog.title('Criar copia derivada')
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()

        remove_missing_var = tk.BooleanVar(value=allow_cleanup and bool(missing_label_images))
        remove_empty_var = tk.BooleanVar(value=allow_cleanup and not missing_label_images and bool(empty_label_images))
        apply_reduction_var = tk.BooleanVar(value=allow_reduction and not allow_cleanup)
        percentage_var = tk.DoubleVar(value=10)
        result = {'options': None}

        container = ttk.Frame(dialog, padding=14)
        container.pack(fill=tk.BOTH, expand=True)

        ttk.Label(
            container,
            text='Criar copia derivada do dataset',
            font=Config.FONTS['main_bold'],
        ).pack(anchor='w')
        ttk.Label(
            container,
            text='Escolha quais transformacoes devem ser aplicadas na nova pasta. O dataset original permanecera intacto.',
            justify='left',
            wraplength=540,
        ).pack(anchor='w', pady=(8, 10))

        if allow_cleanup:
            cleanup_frame = ttk.LabelFrame(container, text='Filtrar por labels', padding=10)
            cleanup_frame.pack(fill=tk.X, pady=(0, 10))
            ttk.Label(
                cleanup_frame,
                text=(
                    f'{len(missing_label_images)} imagem(ns) sem arquivo .txt associado.\n'
                    f'{len(empty_label_images)} imagem(ns) com arquivo .txt vazio.'
                ),
                justify='left',
                wraplength=500,
            ).pack(anchor='w', pady=(0, 8))

            missing_check = ttk.Checkbutton(
                cleanup_frame,
                text='Deixar fora da copia imagens sem label',
                variable=remove_missing_var,
            )
            missing_check.pack(anchor='w')
            if not missing_label_images:
                remove_missing_var.set(False)
                missing_check.config(state='disabled')

            empty_check = ttk.Checkbutton(
                cleanup_frame,
                text='Deixar fora da copia imagens com label vazio',
                variable=remove_empty_var,
            )
            empty_check.pack(anchor='w', pady=(4, 0))
            if not empty_label_images:
                remove_empty_var.set(False)
                empty_check.config(state='disabled')

        percentage_label = None
        slider = None
        if allow_reduction:
            reduction_frame = ttk.LabelFrame(container, text='Reducao aleatoria', padding=10)
            reduction_frame.pack(fill=tk.X, pady=(0, 10))

            reduction_toggle = ttk.Checkbutton(
                reduction_frame,
                text='Aplicar reducao percentual na copia',
                variable=apply_reduction_var,
            )
            reduction_toggle.pack(anchor='w')

            percentage_label = ttk.Label(reduction_frame, font=Config.FONTS['main_bold'])
            percentage_label.pack(anchor='w', pady=(8, 0))

            slider = ttk.Scale(
                reduction_frame,
                from_=1,
                to=99,
                orient=tk.HORIZONTAL,
                variable=percentage_var,
                length=360,
            )
            slider.pack(fill=tk.X, pady=(6, 0))

        summary_label = ttk.Label(container, justify='left', wraplength=540)
        summary_label.pack(anchor='w', pady=(0, 10))

        ttk.Label(
            container,
            text='A pasta nova sera criada ao lado do dataset atual, com nome unico automatico.',
            foreground='#2F6B3F',
            wraplength=540,
        ).pack(anchor='w', pady=(0, 12))

        button_frame = ttk.Frame(container)
        button_frame.pack(fill=tk.X)

        def current_options() -> DatasetCopyOptions:
            reduce_percentage = 0
            if allow_reduction and apply_reduction_var.get():
                reduce_percentage = max(1, min(99, int(float(percentage_var.get()) + 0.5)))
            return DatasetCopyOptions(
                remove_missing_labels=allow_cleanup and remove_missing_var.get(),
                remove_empty_labels=allow_cleanup and remove_empty_var.get(),
                reduce_percentage=reduce_percentage,
            )

        def update_summary(*_):
            options = current_options()
            if percentage_label is not None:
                if options.reduce_percentage > 0:
                    percentage_label.config(text=f'Reduzir aleatoriamente em {options.reduce_percentage}%')
                else:
                    percentage_label.config(text='Reducao desativada')
            if slider is not None:
                slider.config(state='normal' if options.reduce_percentage > 0 else 'disabled')

            if not (options.remove_missing_labels or options.remove_empty_labels or options.reduce_percentage > 0):
                summary_label.config(text='Selecione pelo menos uma transformacao para criar a copia.')
                create_button.config(state='disabled')
                return

            plan = self._build_dataset_copy_plan(options)
            preview = self._format_dataset_copy_plan_summary(plan)
            if options.reduce_percentage > 0:
                preview += '\nA selecao aleatoria sera definida ao confirmar.'
            if plan.removed_total <= 0 or plan.copied_count <= 0:
                if plan.copied_count <= 0:
                    preview += '\nNenhuma imagem restaria na copia com as opcoes atuais.'
                create_button.config(state='disabled')
            else:
                create_button.config(state='normal')
            summary_label.config(text=preview)

        def confirm():
            result['options'] = current_options()
            dialog.destroy()

        def cancel():
            dialog.destroy()

        ttk.Button(button_frame, text='Cancelar', command=cancel).pack(side=tk.RIGHT)
        create_button = ttk.Button(button_frame, text='Criar copia', command=confirm)
        create_button.pack(side=tk.RIGHT, padx=(0, 8))

        if allow_cleanup:
            remove_missing_var.trace_add('write', update_summary)
            remove_empty_var.trace_add('write', update_summary)
        if allow_reduction:
            apply_reduction_var.trace_add('write', update_summary)
            slider.config(command=update_summary)

        update_summary()
        dialog.protocol('WM_DELETE_WINDOW', cancel)
        try:
            center_window(dialog, self.root)
        except Exception:
            pass
        dialog.wait_window()

        return result['options']

    def open_dataset_copy_dialog(self):
        if not self.app_state.base_directory or not self.app_state.image_paths:
            messagebox.showwarning('Aviso', 'Abra um dataset com imagens.', parent=self.root)
            return

        self._save_current_annotations_before_bulk_cleanup()
        options = self._ask_dataset_copy_options()
        if options is None:
            return
        self._create_dataset_copy(options)

    def remove_images_without_labels(self):
        if not self.app_state.base_directory or not self.app_state.image_paths:
            messagebox.showwarning('Aviso', 'Abra um dataset com imagens.', parent=self.root)
            return

        self._save_current_annotations_before_bulk_cleanup()
        missing_label_images, empty_label_images = self._get_unlabeled_cleanup_groups()
        if not missing_label_images and not empty_label_images:
            messagebox.showinfo('Limpeza', 'Nenhuma imagem sem label ou com label vazio foi encontrada.', parent=self.root)
            return

        include_empty_labels = self._ask_remove_unlabeled_cleanup_options(missing_label_images, empty_label_images)
        if include_empty_labels is None:
            return

        self._create_dataset_copy(
            DatasetCopyOptions(
                remove_missing_labels=True,
                remove_empty_labels=include_empty_labels,
            )
        )

    def _calculate_dataset_reduction_count(self, total_images: int, reduce_percentage: int) -> int:
        if total_images <= 1 or reduce_percentage <= 0:
            return 0
        percentage = max(1, min(99, int(reduce_percentage)))
        delete_count = int(total_images * percentage / 100 + 0.5)
        return min(total_images - 1, max(1, delete_count))

    def _ask_reduce_dataset_percentage(self) -> Optional[int]:
        total_images = len(self.app_state.image_paths)
        if total_images <= 1:
            messagebox.showinfo('Reduzir dataset', 'O dataset precisa ter pelo menos 2 imagens para ser reduzido.', parent=self.root)
            return None

        dialog = tk.Toplevel(self.root)
        dialog.title('Reduzir dataset')
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()

        percentage_var = tk.DoubleVar(value=10)
        result = {'percentage': None}

        container = ttk.Frame(dialog, padding=14)
        container.pack(fill=tk.BOTH, expand=True)

        ttk.Label(
            container,
            text='Reduzir dataset aleatoriamente',
            font=Config.FONTS['main_bold'],
        ).pack(anchor='w')
        ttk.Label(
            container,
            text='Escolha a porcentagem de imagens que ficara fora da copia reduzida.',
            justify='left',
            wraplength=520,
        ).pack(anchor='w', pady=(8, 10))

        percentage_label = ttk.Label(container, font=Config.FONTS['main_bold'])
        percentage_label.pack(anchor='w')

        slider = ttk.Scale(container, from_=1, to=99, orient=tk.HORIZONTAL, variable=percentage_var, length=360)
        slider.pack(fill=tk.X, pady=(6, 10))

        summary_label = ttk.Label(container, justify='left', wraplength=520)
        summary_label.pack(anchor='w', pady=(0, 10))

        ttk.Label(
            container,
            text='O dataset original nao sera alterado. Uma nova pasta reduzida sera criada ao lado dele.',
            foreground='#2F6B3F',
            wraplength=520,
        ).pack(anchor='w', pady=(0, 12))

        button_frame = ttk.Frame(container)
        button_frame.pack(fill=tk.X)

        def current_percentage():
            return max(1, min(99, int(float(percentage_var.get()) + 0.5)))

        def update_summary(*_):
            percentage = current_percentage()
            delete_count = self._calculate_dataset_reduction_count(total_images, percentage)
            remaining = total_images - delete_count
            percentage_label.config(text=f'Reduzir em {percentage}%')
            summary_label.config(
                text=(
                    f'Total atual: {total_images} imagem(ns)\n'
                    f'Ficarao fora da copia: {delete_count} imagem(ns)\n'
                    f'Serao copiadas: {remaining} imagem(ns)'
                )
            )

        def confirm():
            result['percentage'] = current_percentage()
            dialog.destroy()

        def cancel():
            dialog.destroy()

        ttk.Button(button_frame, text='Cancelar', command=cancel).pack(side=tk.RIGHT)
        ttk.Button(button_frame, text='Criar copia', command=confirm).pack(side=tk.RIGHT, padx=(0, 8))

        slider.config(command=update_summary)
        update_summary()
        dialog.protocol('WM_DELETE_WINDOW', cancel)
        try:
            center_window(dialog, self.root)
        except Exception:
            pass
        dialog.wait_window()

        return result['percentage']

    def _build_reduced_dataset_directory(self, total_images: int, delete_count: int) -> Path:
        keep_count = max(total_images - delete_count, 0)
        keep_percentage = int(round((keep_count / total_images) * 100)) if total_images else 0
        plan = DatasetCopyPlan(total_images=total_images, images_to_copy=tuple([''] * keep_count))
        return self._build_dataset_copy_directory(
            DatasetCopyOptions(reduce_percentage=max(1, min(99, delete_count)) if delete_count else 0),
            plan,
        )

    def _relative_to_dataset_base(self, path: str) -> Optional[Path]:
        try:
            return Path(path).resolve().relative_to(Path(self.app_state.base_directory).resolve())
        except ValueError:
            return None

    def _copy_dataset_metadata_to_target_dir(self, target_dir: Path) -> None:
        base_path = Path(self.app_state.base_directory).resolve()
        metadata_files = ['classes.txt', *Config.SUPPORTED_DATA_FILES]
        for file_name in metadata_files:
            source_path = base_path / file_name
            if not source_path.is_file():
                continue
            target_path = target_dir / file_name
            target_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_path, target_path)
            if file_name in Config.SUPPORTED_DATA_FILES:
                try:
                    with open(target_path, 'r', encoding='utf-8') as handle:
                        data = yaml.safe_load(handle) or {}
                    if isinstance(data, dict) and 'path' in data:
                        data['path'] = '.'
                        with open(target_path, 'w', encoding='utf-8') as handle:
                            yaml.dump(data, handle, sort_keys=False, allow_unicode=True)
                except Exception:
                    logger.exception(f'Falha ao ajustar path em {target_path}')

    def _copy_dataset_metadata_to_reduced_dir(self, target_dir: Path) -> None:
        self._copy_dataset_metadata_to_target_dir(target_dir)

    def _copy_selected_dataset_files(self, image_paths: List[str], target_dir: Path) -> Tuple[int, List[str]]:
        copied_count = 0
        errors = []
        target_dir.mkdir(parents=True, exist_ok=False)
        self._copy_dataset_metadata_to_target_dir(target_dir)

        for image_path in image_paths:
            try:
                relative_image_path = self._relative_to_dataset_base(image_path)
                if relative_image_path is None:
                    errors.append(f'{os.path.basename(image_path)}: caminho fora do dataset')
                    continue
                target_image_path = target_dir / relative_image_path
                target_image_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(image_path, target_image_path)
                copied_count += 1

                label_path = self.ann_manager.get_label_path(image_path)
                if os.path.isfile(label_path):
                    relative_label_path = self._relative_to_dataset_base(label_path)
                    if relative_label_path is not None:
                        target_label_path = target_dir / relative_label_path
                        target_label_path.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(label_path, target_label_path)
            except Exception as exc:
                errors.append(f'{os.path.basename(image_path)}: {exc}')
        return (copied_count, errors)

    def _copy_reduced_dataset_files(self, image_paths: List[str], target_dir: Path) -> Tuple[int, List[str]]:
        return self._copy_selected_dataset_files(image_paths, target_dir)

    def reduce_dataset_randomly(self):
        if not self.app_state.base_directory or not self.app_state.image_paths:
            messagebox.showwarning('Aviso', 'Abra um dataset com imagens.', parent=self.root)
            return

        self._save_current_annotations_before_bulk_cleanup()
        reduce_percentage = self._ask_reduce_dataset_percentage()
        if reduce_percentage is None:
            return

        self._create_dataset_copy(DatasetCopyOptions(reduce_percentage=reduce_percentage))

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
        if self.app_state.is_drawing and self.canvas_controller.pan_mode:
            self.ui.set_pan_mode(False)
        self.deselect_all()
        mode_txt = 'Polígono' if self.app_state.annotation_mode == 'polygon' else 'Box'
        status = f'Modo Desenho: ON ({mode_txt})' if self.app_state.is_drawing else 'Modo de Navegação'
        self.ui.update_status_bar(status)
        self.ui.canvas.config(cursor='crosshair' if self.app_state.is_drawing else '')

    def _load_class_names(self):
        self.app_state.class_names = []
        p = os.path.join(self.app_state.base_directory, 'classes.txt')
        if os.path.exists(p):
            with open(p, 'r', encoding='utf-8') as f:
                self.app_state.class_names = [x.strip() for x in f if x.strip()]
        else:
            for yaml_file in Config.SUPPORTED_DATA_FILES:
                yaml_path = os.path.join(self.app_state.base_directory, yaml_file)
                if os.path.exists(yaml_path):
                    try:
                        with open(yaml_path, 'r', encoding='utf-8') as f:
                            data = yaml.safe_load(f)
                            if data and 'names' in data:
                                names = data['names']
                                if isinstance(names, dict):
                                    self.app_state.class_names = [str(names[k]) for k in sorted(names.keys())]
                                elif isinstance(names, list):
                                    self.app_state.class_names = [str(n) for n in names]
                        if self.app_state.class_names:
                            break
                    except Exception as e:
                        logger.error(f"Erro ao carregar classes de {yaml_file}: {e}")
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
        if not self.app_state.base_directory:
            messagebox.showwarning(localization.tr('MSG_WARN_TITLE'), 'Abra um dataset.', parent=self.root)
            return
        usage_counts = ClassCatalogManager.count_class_usage(
            self.app_state.base_directory,
            len(self.app_state.class_names)
        )
        ClassManagerWindow(self.root, self.app_state.class_names, self._on_classes_updated, usage_counts)

    def _on_classes_updated(self, payload):
        old_classes = list(self.app_state.class_names)
        if isinstance(payload, dict):
            class_names = list(payload.get('classes', []))
            class_id_map = {
                int(old_id): int(new_id)
                for old_id, new_id in (payload.get('id_map') or {}).items()
            }
        else:
            class_names = list(payload)
            class_id_map = {
                idx: idx
                for idx in range(min(len(old_classes), len(class_names)))
            }

        deleted_ids = set(range(len(old_classes))) - set(class_id_map)
        try:
            ClassCatalogManager.remap_annotation_class_ids(
                self.app_state.base_directory,
                class_id_map,
                deleted_ids=deleted_ids
            )
        except ValueError as exc:
            messagebox.showwarning(localization.tr('MSG_WARN_TITLE'), str(exc), parent=self.root)
            return

        self.app_state.class_names = class_names
        with open(os.path.join(self.app_state.base_directory, 'classes.txt'), 'w', encoding='utf-8') as f:
            f.write('\n'.join(class_names))
        yaml_updated = False
        for yaml_file in Config.SUPPORTED_DATA_FILES:
            yaml_path = os.path.join(self.app_state.base_directory, yaml_file)
            if not os.path.exists(yaml_path):
                continue
            try:
                with open(yaml_path, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f) or {}
                if not isinstance(data, dict):
                    continue
                data['nc'] = len(class_names)
                if isinstance(data.get('names'), dict):
                    data['names'] = {idx: name for idx, name in enumerate(class_names)}
                else:
                    data['names'] = class_names
                with open(yaml_path, 'w', encoding='utf-8') as f:
                    yaml.dump(data, f, sort_keys=False, allow_unicode=True)
                yaml_updated = True
            except Exception as exc:
                logger.error(f'Erro ao atualizar {yaml_file}: {exc}')
        if not yaml_updated:
            yaml_path = os.path.join(self.app_state.base_directory, 'data.yaml')
            data = {
                'nc': len(class_names),
                'names': {idx: name for idx, name in enumerate(class_names)},
            }
            with open(yaml_path, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, sort_keys=False, allow_unicode=True)
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
        initial_dir = self.app_state.base_directory or str(Path.cwd())
        p = filedialog.askdirectory(initialdir=initial_dir)
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
