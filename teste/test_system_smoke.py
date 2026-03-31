import importlib
from pathlib import Path


def test_core_modules_import_successfully():
    modules = [
        'analisador_dataset',
        'canvas',
        'config',
        'generate_languages',
        'localization',
        'logger_config',
        'main',
        'managers',
        'state',
        'ui',
        'utils',
        'utils_ui',
        'visualizador_grid',
        'window_about',
        'window_class_manager',
        'window_new_project',
        'window_split_wizard',
        'windows',
    ]

    imported = [importlib.import_module(module_name) for module_name in modules]

    assert len(imported) == len(modules)


def test_readme_documents_test_folder_and_command():
    readme = Path('README.md').read_text(encoding='utf-8')

    assert 'teste/' in readme
    assert 'python3 -m pytest -q teste' in readme
