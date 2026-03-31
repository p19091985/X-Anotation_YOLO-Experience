import importlib
from pathlib import Path
from types import SimpleNamespace
import xml.etree.ElementTree as ET

import yaml

import localization as localization_module
from config import Config
from main import MainApplication
from managers import ClassCatalogManager
from window_new_project import NewProjectWindow
from window_split_wizard import SplitWizard


class DummyVar:

    def __init__(self, value):
        self.value = value

    def get(self):
        return self.value

    def set(self, value):
        self.value = value


class DummyLabel:

    def __init__(self):
        self.text = None

    def config(self, **kwargs):
        if 'text' in kwargs:
            self.text = kwargs['text']


def test_config_exposes_generic_template_defaults():
    assert 'Marinho' in Config.APP_NAME
    assert Config.FEATURE_SHOW_GRID_VIEW is True
    assert Config.FEATURE_ENABLE_TOOLTIPS is True
    assert 100 in Config.ZOOM_PRESETS
    assert Config.MIN_ZOOM_LEVEL < 1 < Config.MAX_ZOOM_LEVEL


def test_localization_loads_languages_independent_of_cwd(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    module = importlib.reload(localization_module)
    languages = module.get_languages()
    assert languages
    assert any(code == 'pt_BR' for _, code in languages)
    assert module.tr('ABOUT')


def test_repository_metadata_is_generic():
    files_to_check = [
        Path('README.md'),
        Path('generate_languages.py'),
        Path('teste/macro/runner.py'),
    ]
    forbidden = ('X-Annotation', 'X-Anotation', 'Patrik', 'Unisenai', 'Docol', 'dataset-geral-01')
    for file_path in files_to_check:
        content = file_path.read_text(encoding='utf-8')
        for token in forbidden:
            assert token not in content, f'{token} encontrado em {file_path}'


def test_languages_xml_about_titles_are_generic():
    tree = ET.parse('languages.xml')
    root = tree.getroot()
    forbidden = ('X-Annotation', 'X-Anotation', 'Patrik', 'Docol')
    for title_node in root.findall(".//string[@key='TITLE_ABOUT']"):
        text = title_node.text or ''
        for token in forbidden:
            assert token not in text


def test_main_serializes_and_resolves_relative_directory(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    project_dir = tmp_path / 'data' / 'demo'
    project_dir.mkdir(parents=True)
    app = MainApplication.__new__(MainApplication)
    serialized = app._serialize_directory(str(project_dir))
    assert serialized == 'data/demo'
    resolved = app._resolve_saved_directory(serialized)
    assert resolved == str(project_dir.resolve())


def test_new_project_yaml_uses_relative_paths(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    window = NewProjectWindow.__new__(NewProjectWindow)
    window.classes_list = ['class_a', 'class_b']
    yaml_data = window._build_yaml_data(str(tmp_path / 'datasets' / 'sample'))
    assert yaml_data['path'] == './datasets/sample'
    assert yaml_data['train'] == 'train/images'
    assert yaml_data['val'] == 'valid/images'
    assert yaml_data['test'] == 'test/images'
    assert yaml_data['names'] == ['class_a', 'class_b']


def test_on_classes_updated_refreshes_classes_txt_and_yaml(tmp_path):
    base_dir = tmp_path / 'dataset'
    base_dir.mkdir()
    (base_dir / 'classes.txt').write_text('', encoding='utf-8')
    (base_dir / 'data.yaml').write_text('nc: 1\nnames:\n  0: old\n', encoding='utf-8')

    callbacks = {'selector_updated': False, 'index': None}

    app = MainApplication.__new__(MainApplication)
    app.app_state = SimpleNamespace(base_directory=str(base_dir), class_names=[], current_image_index=-1)
    app.ui = SimpleNamespace(update_class_selector=lambda: callbacks.__setitem__('selector_updated', True))
    app.show_image_at_index = lambda index: callbacks.__setitem__('index', index)

    app._on_classes_updated(['foo', 'bar'])

    assert (base_dir / 'classes.txt').read_text(encoding='utf-8') == 'foo\nbar'
    yaml_data = yaml.safe_load((base_dir / 'data.yaml').read_text(encoding='utf-8'))
    assert yaml_data['nc'] == 2
    assert yaml_data['names'] == {0: 'foo', 1: 'bar'}
    assert callbacks['selector_updated'] is True
    assert callbacks['index'] == -1


def test_class_catalog_counts_usage_and_remaps_ids(tmp_path):
    base_dir = tmp_path / 'dataset'
    labels_dir = base_dir / 'train' / 'labels'
    labels_dir.mkdir(parents=True)
    label_a = labels_dir / 'img_a.txt'
    label_b = labels_dir / 'img_b.txt'
    label_a.write_text('0 0.5 0.5 0.2 0.2\n2 0.3 0.3 0.1 0.1\n', encoding='utf-8')
    label_b.write_text('2 0.4 0.4 0.2 0.2\n', encoding='utf-8')

    usage = ClassCatalogManager.count_class_usage(str(base_dir), 4)

    assert usage == [1, 0, 2, 0]

    ClassCatalogManager.remap_annotation_class_ids(str(base_dir), {0: 0, 2: 1}, deleted_ids={3})

    assert label_a.read_text(encoding='utf-8') == '0 0.5 0.5 0.2 0.2\n1 0.3 0.3 0.1 0.1\n'
    assert label_b.read_text(encoding='utf-8') == '1 0.4 0.4 0.2 0.2\n'


def test_on_classes_updated_remaps_annotation_ids_when_unused_class_is_removed(tmp_path):
    base_dir = tmp_path / 'dataset'
    labels_dir = base_dir / 'train' / 'labels'
    labels_dir.mkdir(parents=True)
    (base_dir / 'classes.txt').write_text('foo\nbar\nbaz', encoding='utf-8')
    (base_dir / 'data.yaml').write_text('nc: 3\nnames:\n  0: foo\n  1: bar\n  2: baz\n', encoding='utf-8')
    (labels_dir / 'img.txt').write_text('0 0.5 0.5 0.2 0.2\n2 0.3 0.3 0.1 0.1\n', encoding='utf-8')

    callbacks = {'selector_updated': False, 'index': None}

    app = MainApplication.__new__(MainApplication)
    app.app_state = SimpleNamespace(base_directory=str(base_dir), class_names=['foo', 'bar', 'baz'], current_image_index=-1)
    app.ui = SimpleNamespace(update_class_selector=lambda: callbacks.__setitem__('selector_updated', True))
    app.show_image_at_index = lambda index: callbacks.__setitem__('index', index)

    app._on_classes_updated({'classes': ['foo', 'baz'], 'id_map': {0: 0, 2: 1}})

    assert (base_dir / 'classes.txt').read_text(encoding='utf-8') == 'foo\nbaz'
    yaml_data = yaml.safe_load((base_dir / 'data.yaml').read_text(encoding='utf-8'))
    assert yaml_data['nc'] == 2
    assert yaml_data['names'] == {0: 'foo', 1: 'baz'}
    assert (labels_dir / 'img.txt').read_text(encoding='utf-8') == '0 0.5 0.5 0.2 0.2\n1 0.3 0.3 0.1 0.1\n'
    assert callbacks['selector_updated'] is True
    assert callbacks['index'] == -1


def test_split_wizard_apply_forwards_optional_test_ratio():
    captured = {}
    wizard = SplitWizard.__new__(SplitWizard)
    wizard.train_pct = DummyVar(70)
    wizard.val_pct = DummyVar(20)
    wizard.test_pct = DummyVar(10)
    wizard.include_test = DummyVar(True)
    wizard.shuffle = DummyVar(False)
    wizard.callback = lambda *args: captured.setdefault('args', args)
    wizard.destroy = lambda: captured.setdefault('destroyed', True)

    wizard.apply()

    assert captured['args'] == (0.7, 0.2, 0.1, False)
    assert captured['destroyed'] is True


def test_split_wizard_scale_change_clamps_train_against_test():
    captured = {}
    wizard = SplitWizard.__new__(SplitWizard)
    wizard.train_pct = DummyVar(95)
    wizard.val_pct = DummyVar(0)
    wizard.test_pct = DummyVar(10)
    wizard.include_test = DummyVar(True)
    wizard.lbl_train_val = DummyLabel()
    wizard.lbl_val_val = DummyLabel()
    wizard.lbl_test_val = DummyLabel()
    wizard._update_chart = lambda train, val, test: captured.setdefault('chart', (train, val, test))

    wizard._on_scale_change()

    assert wizard.train_pct.get() == 90
    assert wizard.val_pct.get() == 0
    assert wizard.lbl_train_val.text == '90%'
    assert wizard.lbl_val_val.text == ' | Val: 0%'
    assert wizard.lbl_test_val.text == ' | Test: 10%'
    assert captured['chart'] == (90, 0, 10)
