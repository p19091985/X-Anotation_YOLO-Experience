from pathlib import Path
from types import SimpleNamespace

import yaml

import main as main_module
import utils_ui
import window_class_manager as class_manager_module
import window_new_project as new_project_module
from main import DatasetCopyOptions, MainApplication
from managers import AnnotationManager
from state import AppState
from tests.helpers import DummyEntry, DummyFrame, DummyVar, FakeTree
from window_class_manager import ClassManagerWindow
from window_new_project import NewProjectWindow
from window_split_wizard import SplitWizard


def _build_app(base_dir, class_names):
    callbacks = {'selector_updated': False, 'index': None}
    app = MainApplication.__new__(MainApplication)
    app.root = object()
    app.app_state = SimpleNamespace(
        base_directory=str(base_dir),
        class_names=list(class_names),
        current_image_index=-1
    )
    app.ui = SimpleNamespace(update_class_selector=lambda: callbacks.__setitem__('selector_updated', True))
    app.show_image_at_index = lambda index: callbacks.__setitem__('index', index)
    return app, callbacks


def test_app_state_get_current_image_path_handles_valid_and_invalid_indexes():
    state = AppState()
    state.image_paths = ['a.jpg', 'b.jpg']
    state.current_image_index = 1
    assert state.get_current_image_path() == 'b.jpg'

    state.current_image_index = 5
    assert state.get_current_image_path() is None


def test_new_project_window_create_structure_writes_dataset_files(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    base_path = tmp_path / 'datasets'
    base_path.mkdir()

    window = NewProjectWindow.__new__(NewProjectWindow)
    window.classes_list = ['cat', 'dog']
    window.base_path = str(base_path)
    window.e_name = DummyEntry('demo')

    callbacks = {}
    infos = []
    monkeypatch.setattr(new_project_module.messagebox, 'showinfo', lambda title, body, parent=None: infos.append((title, body)))
    monkeypatch.setattr(new_project_module.messagebox, 'showwarning', lambda *args, **kwargs: None)
    monkeypatch.setattr(new_project_module.messagebox, 'showerror', lambda *args, **kwargs: None)
    window.callback = lambda path: callbacks.setdefault('path', path)
    window.destroy = lambda: callbacks.setdefault('destroyed', True)

    window.create_structure()

    project_dir = base_path / 'demo'
    assert project_dir.exists()
    assert (project_dir / 'classes.txt').read_text(encoding='utf-8') == 'cat\ndog'
    yaml_data = yaml.safe_load((project_dir / 'data.yaml').read_text(encoding='utf-8'))
    assert yaml_data['path'] == './datasets/demo'
    assert yaml_data['names'] == ['cat', 'dog']
    assert callbacks['path'] == str(project_dir)
    assert callbacks['destroyed'] is True
    assert infos


def test_new_project_window_create_structure_requires_name(monkeypatch, tmp_path):
    window = NewProjectWindow.__new__(NewProjectWindow)
    window.classes_list = ['cat']
    window.base_path = str(tmp_path)
    window.e_name = DummyEntry('')

    warnings = []
    monkeypatch.setattr(new_project_module.messagebox, 'showwarning', lambda title, body, parent=None: warnings.append((title, body)))

    window.create_structure()

    assert warnings
    assert window.e_name.focused is True


def test_class_manager_window_delete_blocks_class_in_use(monkeypatch):
    window = ClassManagerWindow.__new__(ClassManagerWindow)
    window.class_entries = [{'source_index': 0, 'name': 'cat', 'image_count': 2}]
    window.tree = FakeTree()
    window.tree.insert('', 'end', iid='0', values=(0, 'cat', 2))
    window.tree.selection_set('0')

    warnings = []
    monkeypatch.setattr(class_manager_module.messagebox, 'showwarning', lambda title, body, parent=None: warnings.append((title, body)))

    window.delete()

    assert len(window.class_entries) == 1
    assert warnings


def test_class_manager_window_save_returns_names_and_id_map():
    window = ClassManagerWindow.__new__(ClassManagerWindow)
    window.class_entries = [
        {'source_index': 0, 'name': 'cat', 'image_count': 1},
        {'source_index': 2, 'name': 'dog', 'image_count': 0},
        {'source_index': None, 'name': 'bird', 'image_count': 0},
    ]
    captured = {}
    window.callback = lambda payload: captured.setdefault('payload', payload)
    window.destroy = lambda: captured.setdefault('destroyed', True)

    window.save()

    assert captured['payload'] == {
        'classes': ['cat', 'dog', 'bird'],
        'id_map': {0: 0, 2: 1},
    }
    assert captured['destroyed'] is True


def test_split_wizard_toggle_enables_default_test_percentage():
    wizard = SplitWizard.__new__(SplitWizard)
    wizard.include_test = DummyVar(True)
    wizard.test_pct = DummyVar(0)
    wizard.test_scale_frame = DummyFrame()
    wizard.chk_shuffle = object()
    calls = []
    wizard._on_scale_change = lambda: calls.append('changed')

    wizard._on_test_toggle()

    assert wizard.test_pct.get() == 10
    assert wizard.test_scale_frame.pack_calls
    assert calls == ['changed']


def test_split_wizard_toggle_disables_test_percentage():
    wizard = SplitWizard.__new__(SplitWizard)
    wizard.include_test = DummyVar(False)
    wizard.test_pct = DummyVar(15)
    wizard.test_scale_frame = DummyFrame()
    calls = []
    wizard._on_scale_change = lambda: calls.append('changed')

    wizard._on_test_toggle()

    assert wizard.test_pct.get() == 0
    assert wizard.test_scale_frame.forgotten is True
    assert calls == ['changed']


def test_log_errors_decorator_reports_exceptions(monkeypatch):
    errors = []
    monkeypatch.setattr(utils_ui.messagebox, 'showerror', lambda title, body: errors.append((title, body)))

    @utils_ui.log_errors
    def explode():
        raise RuntimeError('kaboom')

    assert explode() is None
    assert errors
    assert 'kaboom' in errors[0][1]


def test_center_window_positions_child_relative_to_parent():
    class FakeWindow:
        def __init__(self):
            self.geometry_value = None

        def update_idletasks(self):
            return None

        def winfo_width(self):
            return 200

        def winfo_height(self):
            return 100

        def geometry(self, value):
            self.geometry_value = value

    class FakeParent:
        def winfo_rootx(self):
            return 10

        def winfo_rooty(self):
            return 20

        def winfo_width(self):
            return 500

        def winfo_height(self):
            return 300

    window = FakeWindow()
    utils_ui.center_window(window, FakeParent())

    assert window.geometry_value == '+160+120'


def test_maximize_window_falls_back_to_screen_geometry():
    class FakeWindow:
        def __init__(self):
            self.tk = self
            self.geometry_value = None

        def call(self, *args):
            raise RuntimeError('no windowing system')

        def attributes(self, *args):
            raise RuntimeError('no zoom attr')

        def state(self, value):
            raise RuntimeError('no zoom state')

        def winfo_screenwidth(self):
            return 1920

        def winfo_screenheight(self):
            return 1080

        def geometry(self, value):
            self.geometry_value = value

    window = FakeWindow()
    utils_ui.maximize_window(window)

    assert window.geometry_value == '1920x1080+0+0'


def test_main_load_class_names_from_yaml_when_classes_file_is_missing(tmp_path):
    base_dir = tmp_path / 'dataset'
    base_dir.mkdir()
    (base_dir / 'data.yaml').write_text('names:\n  0: cat\n  1: dog\n', encoding='utf-8')

    app = MainApplication.__new__(MainApplication)
    app.app_state = SimpleNamespace(base_directory=str(base_dir), class_names=[])
    calls = []
    app.ui = SimpleNamespace(update_class_selector=lambda: calls.append('updated'))

    app._load_class_names()

    assert app.app_state.class_names == ['cat', 'dog']
    assert calls == ['updated']


def test_fit_current_image_to_canvas_retries_until_canvas_has_real_size():
    class FakeCanvas:
        def __init__(self):
            self.width = 1
            self.height = 1

        def winfo_width(self):
            return self.width

        def winfo_height(self):
            return self.height

    class FakeRoot:
        def __init__(self):
            self.calls = []

        def after(self, delay_ms, callback):
            self.calls.append((delay_ms, callback))

    canvas = FakeCanvas()
    root = FakeRoot()
    render_calls = []

    app = MainApplication.__new__(MainApplication)
    app.root = root
    app.ui = SimpleNamespace(canvas=canvas)
    app.canvas_controller = SimpleNamespace(
        reset_view=lambda: render_calls.append('reset'),
        display_image=lambda: render_calls.append('display'),
    )
    app.app_state = SimpleNamespace(current_image_index=0, current_pil_image=object())

    app._fit_current_image_to_canvas_when_ready(0, retries=2)

    assert render_calls == []
    assert len(root.calls) == 1

    canvas.width = 1200
    canvas.height = 800
    _, callback = root.calls.pop()
    callback()

    assert render_calls == ['reset', 'display']


def test_remove_images_without_labels_creates_filtered_copy_without_changing_original(monkeypatch, tmp_path):
    base_dir = tmp_path / 'dataset'
    image_dir = base_dir / 'images'
    label_dir = base_dir / 'labels'
    image_dir.mkdir(parents=True)
    label_dir.mkdir()
    unlabeled_image = image_dir / 'missing.jpg'
    labeled_image = image_dir / 'labeled.jpg'
    empty_label_image = image_dir / 'empty.jpg'
    unlabeled_image.write_text('img', encoding='utf-8')
    labeled_image.write_text('img', encoding='utf-8')
    empty_label_image.write_text('img', encoding='utf-8')
    (label_dir / 'labeled.txt').write_text('0 0.5 0.5 0.2 0.2\n', encoding='utf-8')
    (label_dir / 'empty.txt').write_text('', encoding='utf-8')

    app = MainApplication.__new__(MainApplication)
    app.root = object()
    app.ann_manager = AnnotationManager()
    app.app_state = AppState()
    app.app_state.base_directory = str(base_dir)
    app.app_state.image_paths = [str(unlabeled_image), str(labeled_image), str(empty_label_image)]
    app._ask_remove_unlabeled_cleanup_options = lambda missing, empty: False

    infos = []
    monkeypatch.setattr(main_module.messagebox, 'showinfo', lambda title, body, parent=None: infos.append((title, body)))

    app.remove_images_without_labels()

    filtered_dir = tmp_path / 'dataset_copia_sem_label'
    assert filtered_dir.exists()
    assert unlabeled_image.exists()
    assert labeled_image.exists()
    assert empty_label_image.exists()
    assert (label_dir / 'empty.txt').exists()
    assert not (filtered_dir / 'images' / 'missing.jpg').exists()
    assert (filtered_dir / 'images' / 'labeled.jpg').exists()
    assert (filtered_dir / 'labels' / 'labeled.txt').exists()
    assert (filtered_dir / 'images' / 'empty.jpg').exists()
    assert (filtered_dir / 'labels' / 'empty.txt').exists()
    assert infos


def test_remove_images_without_labels_can_include_empty_label_files(monkeypatch, tmp_path):
    base_dir = tmp_path / 'dataset'
    image_dir = base_dir / 'images'
    label_dir = base_dir / 'labels'
    image_dir.mkdir(parents=True)
    label_dir.mkdir()
    unlabeled_image = image_dir / 'missing.jpg'
    labeled_image = image_dir / 'labeled.jpg'
    empty_label_image = image_dir / 'empty.jpg'
    unlabeled_image.write_text('img', encoding='utf-8')
    labeled_image.write_text('img', encoding='utf-8')
    empty_label_image.write_text('img', encoding='utf-8')
    (label_dir / 'labeled.txt').write_text('0 0.5 0.5 0.2 0.2\n', encoding='utf-8')
    empty_label = label_dir / 'empty.txt'
    empty_label.write_text('  \n', encoding='utf-8')

    app = MainApplication.__new__(MainApplication)
    app.root = object()
    app.ann_manager = AnnotationManager()
    app.app_state = AppState()
    app.app_state.base_directory = str(base_dir)
    app.app_state.image_paths = [str(unlabeled_image), str(labeled_image), str(empty_label_image)]
    app._ask_remove_unlabeled_cleanup_options = lambda missing, empty: True

    monkeypatch.setattr(main_module.messagebox, 'showinfo', lambda *args, **kwargs: None)

    app.remove_images_without_labels()

    filtered_dir = tmp_path / 'dataset_copia_sem_label_sem_vazio'
    assert filtered_dir.exists()
    assert unlabeled_image.exists()
    assert empty_label_image.exists()
    assert empty_label.exists()
    assert labeled_image.exists()
    assert (label_dir / 'labeled.txt').exists()
    assert not (filtered_dir / 'images' / 'missing.jpg').exists()
    assert not (filtered_dir / 'images' / 'empty.jpg').exists()
    assert not (filtered_dir / 'labels' / 'empty.txt').exists()
    assert (filtered_dir / 'images' / 'labeled.jpg').exists()
    assert (filtered_dir / 'labels' / 'labeled.txt').exists()


def test_remove_images_without_labels_saves_current_annotated_image_before_scan(monkeypatch, tmp_path):
    base_dir = tmp_path / 'dataset'
    image_dir = base_dir / 'images'
    label_dir = base_dir / 'labels'
    image_dir.mkdir(parents=True)
    label_dir.mkdir()
    current_image = image_dir / 'current.jpg'
    other_image = image_dir / 'other.jpg'
    current_image.write_text('img', encoding='utf-8')
    other_image.write_text('img', encoding='utf-8')

    app = MainApplication.__new__(MainApplication)
    app.root = object()
    app.ann_manager = AnnotationManager()
    app.app_state = AppState()
    app.app_state.base_directory = str(base_dir)
    app.app_state.image_paths = [str(current_image), str(other_image)]
    app.app_state.current_image_index = 0
    app.app_state.data_is_safe_to_save = True
    app.app_state.annotations = [{'yolo_string': '0 0.5 0.5 0.2 0.2'}]
    app._save_and_refresh = lambda update_listbox=True: (label_dir / 'current.txt').write_text(
        '0 0.5 0.5 0.2 0.2\n',
        encoding='utf-8'
    )
    app._ask_remove_unlabeled_cleanup_options = lambda missing, empty: False

    monkeypatch.setattr(main_module.messagebox, 'showinfo', lambda *args, **kwargs: None)

    app.remove_images_without_labels()

    filtered_dir = tmp_path / 'dataset_copia_sem_label'
    assert current_image.exists()
    assert other_image.exists()
    assert (label_dir / 'current.txt').exists()
    assert (filtered_dir / 'images' / 'current.jpg').exists()
    assert (filtered_dir / 'labels' / 'current.txt').exists()
    assert not (filtered_dir / 'images' / 'other.jpg').exists()


def test_dataset_reduction_count_keeps_at_least_one_image():
    app = MainApplication.__new__(MainApplication)

    assert app._calculate_dataset_reduction_count(1, 50) == 0
    assert app._calculate_dataset_reduction_count(2, 99) == 1
    assert app._calculate_dataset_reduction_count(10, 30) == 3
    assert app._calculate_dataset_reduction_count(10, 99) == 9


def test_reduce_dataset_randomly_creates_reduced_copy_without_changing_original(monkeypatch, tmp_path):
    base_dir = tmp_path / 'dataset'
    image_dir = base_dir / 'images'
    label_dir = base_dir / 'labels'
    image_dir.mkdir(parents=True)
    label_dir.mkdir()
    (base_dir / 'classes.txt').write_text('cat', encoding='utf-8')
    (base_dir / 'data.yaml').write_text('path: /old/path\ntrain: images\nnames:\n- cat\n', encoding='utf-8')
    image_paths = []
    for index in range(10):
        image_path = image_dir / f'img_{index:02d}.jpg'
        label_path = label_dir / f'img_{index:02d}.txt'
        image_path.write_text('img', encoding='utf-8')
        label_path.write_text('0 0.5 0.5 0.2 0.2\n', encoding='utf-8')
        image_paths.append(str(image_path))

    app = MainApplication.__new__(MainApplication)
    app.root = object()
    app.ann_manager = AnnotationManager()
    app.app_state = AppState()
    app.app_state.base_directory = str(base_dir)
    app.app_state.image_paths = image_paths
    app._ask_reduce_dataset_percentage = lambda: 30
    refresh_calls = []
    app.refresh_directory = lambda: refresh_calls.append('refresh')
    infos = []

    monkeypatch.setattr(main_module.random, 'sample', lambda items, count: sorted(items)[:count])
    monkeypatch.setattr(main_module.messagebox, 'showinfo', lambda title, body, parent=None: infos.append((title, body)))

    app.reduce_dataset_randomly()

    reduced_dir = tmp_path / 'dataset_reduzido_70pct'
    assert reduced_dir.exists()
    for index in range(3):
        assert (image_dir / f'img_{index:02d}.jpg').exists()
        assert (label_dir / f'img_{index:02d}.txt').exists()
        assert not (reduced_dir / 'images' / f'img_{index:02d}.jpg').exists()
        assert not (reduced_dir / 'labels' / f'img_{index:02d}.txt').exists()
    for index in range(3, 10):
        assert (image_dir / f'img_{index:02d}.jpg').exists()
        assert (label_dir / f'img_{index:02d}.txt').exists()
        assert (reduced_dir / 'images' / f'img_{index:02d}.jpg').exists()
        assert (reduced_dir / 'labels' / f'img_{index:02d}.txt').exists()
    assert (reduced_dir / 'classes.txt').read_text(encoding='utf-8') == 'cat'
    reduced_yaml = yaml.safe_load((reduced_dir / 'data.yaml').read_text(encoding='utf-8'))
    assert reduced_yaml['path'] == '.'
    assert refresh_calls == []
    assert infos


def test_open_dataset_copy_dialog_can_combine_cleanup_and_reduction(monkeypatch, tmp_path):
    base_dir = tmp_path / 'dataset'
    image_dir = base_dir / 'images'
    label_dir = base_dir / 'labels'
    image_dir.mkdir(parents=True)
    label_dir.mkdir()
    (base_dir / 'classes.txt').write_text('cat', encoding='utf-8')
    (base_dir / 'data.yaml').write_text('path: /old/path\ntrain: images\nnames:\n- cat\n', encoding='utf-8')

    missing_image = image_dir / 'missing.jpg'
    missing_image.write_text('img', encoding='utf-8')
    image_paths = [str(missing_image)]
    for name in ('a', 'b', 'c'):
        image_path = image_dir / f'{name}.jpg'
        label_path = label_dir / f'{name}.txt'
        image_path.write_text('img', encoding='utf-8')
        label_path.write_text('0 0.5 0.5 0.2 0.2\n', encoding='utf-8')
        image_paths.append(str(image_path))

    app = MainApplication.__new__(MainApplication)
    app.root = object()
    app.ann_manager = AnnotationManager()
    app.app_state = AppState()
    app.app_state.base_directory = str(base_dir)
    app.app_state.image_paths = image_paths
    app._ask_dataset_copy_options = lambda: DatasetCopyOptions(remove_missing_labels=True, reduce_percentage=50)

    infos = []
    monkeypatch.setattr(main_module.random, 'sample', lambda items, count: sorted(items)[:count])
    monkeypatch.setattr(main_module.messagebox, 'showinfo', lambda title, body, parent=None: infos.append((title, body)))

    app.open_dataset_copy_dialog()

    filtered_dir = tmp_path / 'dataset_copia_sem_label_reduzido_25pct'
    assert filtered_dir.exists()
    assert missing_image.exists()
    assert not (filtered_dir / 'images' / 'missing.jpg').exists()
    assert not (filtered_dir / 'images' / 'a.jpg').exists()
    assert not (filtered_dir / 'images' / 'b.jpg').exists()
    assert (filtered_dir / 'images' / 'c.jpg').exists()
    assert (filtered_dir / 'labels' / 'c.txt').exists()
    filtered_yaml = yaml.safe_load((filtered_dir / 'data.yaml').read_text(encoding='utf-8'))
    assert filtered_yaml['path'] == '.'
    assert infos


def test_main_on_classes_updated_creates_yaml_when_missing(tmp_path):
    base_dir = tmp_path / 'dataset'
    base_dir.mkdir()
    (base_dir / 'classes.txt').write_text('', encoding='utf-8')

    app, callbacks = _build_app(base_dir, [])
    app._on_classes_updated(['cat'])

    yaml_data = yaml.safe_load((base_dir / 'data.yaml').read_text(encoding='utf-8'))
    assert yaml_data['nc'] == 1
    assert yaml_data['names'] == {0: 'cat'}
    assert callbacks['selector_updated'] is True
    assert callbacks['index'] == -1


def test_main_on_classes_updated_warns_when_deleted_class_is_still_used(monkeypatch, tmp_path):
    base_dir = tmp_path / 'dataset'
    labels_dir = base_dir / 'train' / 'labels'
    labels_dir.mkdir(parents=True)
    (base_dir / 'classes.txt').write_text('cat\ndog', encoding='utf-8')
    (labels_dir / 'img.txt').write_text('1 0.5 0.5 0.2 0.2\n', encoding='utf-8')

    app, callbacks = _build_app(base_dir, ['cat', 'dog'])
    warnings = []
    monkeypatch.setattr(main_module.messagebox, 'showwarning', lambda title, body, parent=None: warnings.append((title, body)))

    app._on_classes_updated({'classes': ['cat'], 'id_map': {0: 0}})

    assert warnings
    assert (base_dir / 'classes.txt').read_text(encoding='utf-8') == 'cat\ndog'
    assert app.app_state.class_names == ['cat', 'dog']
    assert callbacks['selector_updated'] is False


def test_main_open_class_manager_warns_without_open_dataset(monkeypatch):
    app = MainApplication.__new__(MainApplication)
    app.root = object()
    app.app_state = SimpleNamespace(base_directory='', class_names=[])

    warnings = []
    monkeypatch.setattr(main_module.messagebox, 'showwarning', lambda title, body, parent=None: warnings.append((title, body)))

    app.open_class_manager()

    assert warnings


def test_main_open_class_manager_passes_usage_counts(monkeypatch, tmp_path):
    base_dir = tmp_path / 'dataset'
    base_dir.mkdir()

    app = MainApplication.__new__(MainApplication)
    app.root = object()
    app.app_state = SimpleNamespace(base_directory=str(base_dir), class_names=['cat', 'dog'])

    captured = {}
    monkeypatch.setattr(main_module.ClassCatalogManager, 'count_class_usage', lambda base_directory, class_count: [5, 0])
    monkeypatch.setattr(
        main_module,
        'ClassManagerWindow',
        lambda root, class_names, callback, usage_counts: captured.update(
            root=root,
            class_names=list(class_names),
            callback=callback,
            usage_counts=list(usage_counts),
        )
    )

    app.open_class_manager()

    assert captured['class_names'] == ['cat', 'dog']
    assert captured['usage_counts'] == [5, 0]
    assert captured['callback'] == app._on_classes_updated


def test_main_load_directory_contents_accepts_base_dir_with_labels_in_name(tmp_path):
    base_dir = tmp_path / 'final_labels'
    image_dir = base_dir / 'train' / 'images'
    labels_dir = base_dir / 'train' / 'labels'
    image_dir.mkdir(parents=True)
    labels_dir.mkdir(parents=True)
    (image_dir / 'img1.jpg').write_text('img', encoding='utf-8')
    (labels_dir / 'img1.txt').write_text('0 0.5 0.5 0.2 0.2\n', encoding='utf-8')

    class DummyWidget:
        def __init__(self):
            self.calls = []

        def config(self, **kwargs):
            self.calls.append(kwargs)

    app = MainApplication.__new__(MainApplication)
    app.app_state = SimpleNamespace(
        base_directory=str(base_dir),
        current_image_index=-1,
        data_is_safe_to_save=True,
        annotations=['old'],
        undo_stack=['old'],
        is_drawing=False,
        image_paths=[]
    )
    app.ui = SimpleNamespace(
        dir_label=DummyWidget(),
        add_box_check=DummyWidget(),
        refresh_image_list=lambda: None,
    )
    app._load_class_names = lambda: None
    shown_indexes = []
    app.show_image_at_index = lambda index: shown_indexes.append(index)

    app._load_directory_contents()

    assert app.app_state.image_paths == [str(image_dir / 'img1.jpg')]
    assert shown_indexes == [0]
    assert app.ui.add_box_check.calls[-1] == {'state': 'normal'}
