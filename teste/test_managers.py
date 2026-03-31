from pathlib import Path

import pytest

from managers import AnnotationManager, DatasetUtils


def test_annotation_manager_get_label_path_prefers_labels_folder(tmp_path):
    image_path = tmp_path / 'train' / 'images' / 'sample.jpg'
    labels_dir = tmp_path / 'train' / 'labels'
    labels_dir.mkdir(parents=True)
    image_path.parent.mkdir(parents=True)
    image_path.write_text('img', encoding='utf-8')

    label_path = AnnotationManager.get_label_path(str(image_path))

    assert label_path == str(labels_dir / 'sample.txt')


def test_annotation_manager_load_annotations_supports_box_and_polygon(tmp_path):
    label_path = tmp_path / 'sample.txt'
    label_path.write_text(
        '0 0.500000 0.500000 0.200000 0.400000\n'
        '1 0.100000 0.100000 0.200000 0.100000 0.300000 0.200000\n',
        encoding='utf-8'
    )

    annotations, error = AnnotationManager.load_annotations(str(label_path), (100, 50))

    assert error is None
    assert len(annotations) == 2
    assert annotations[0]['type'] == 'box'
    assert annotations[0]['class_id'] == 0
    assert annotations[0]['rect_orig'] == [40.0, 15.0, 60.0, 35.0]
    assert annotations[1]['type'] == 'polygon'
    assert annotations[1]['class_id'] == 1
    assert annotations[1]['points'] == [(10.0, 5.0), (20.0, 5.0), (30.0, 10.0)]
    assert annotations[1]['rect_orig'] == [10.0, 5.0, 30.0, 10.0]


def test_annotation_manager_save_annotations_writes_all_lines(tmp_path):
    label_path = tmp_path / 'labels' / 'sample.txt'
    annotations = [
        {'yolo_string': '0 0.1 0.2 0.3 0.4'},
        {'yolo_string': '1 0.5 0.6 0.7 0.8'},
    ]

    saved = AnnotationManager.save_annotations(str(label_path), annotations)

    assert saved is True
    assert label_path.read_text(encoding='utf-8') == '0 0.1 0.2 0.3 0.4\n1 0.5 0.6 0.7 0.8\n'


def test_annotation_manager_convert_box_to_yolo_generates_expected_string():
    result = AnnotationManager.convert_box_to_yolo(3, [25, 25, 75, 75], (100, 100))

    assert result == '3 0.500000 0.500000 0.500000 0.500000'


def test_annotation_manager_convert_poly_to_yolo_clamps_coordinates():
    result = AnnotationManager.convert_poly_to_yolo(2, [(-10, 50), (50, 120)], (100, 100))

    assert result == '2 0.000000 0.500000 0.500000 1.000000'


def test_dataset_utils_split_dataset_moves_images_and_labels(monkeypatch, tmp_path):
    base_dir = tmp_path / 'dataset'
    base_dir.mkdir()
    for index in range(1, 5):
        (base_dir / f'img{index}.jpg').write_text('img', encoding='utf-8')
        (base_dir / f'img{index}.txt').write_text('0 0.5 0.5 0.2 0.2\n', encoding='utf-8')

    monkeypatch.setattr('managers.random.shuffle', lambda items: items.sort(key=lambda item: item['name']))

    DatasetUtils.split_dataset(str(base_dir), train_ratio=0.5, val_ratio=0.25, test_ratio=0.25, shuffle=True)

    expected_locations = {
        'train': ['img1.jpg', 'img2.jpg'],
        'valid': ['img3.jpg'],
        'test': ['img4.jpg'],
    }
    for split_name, image_names in expected_locations.items():
        image_dir = base_dir / split_name / 'images'
        label_dir = base_dir / split_name / 'labels'
        assert sorted(path.name for path in image_dir.iterdir()) == image_names
        assert sorted(path.name for path in label_dir.iterdir()) == [Path(name).with_suffix('.txt').name for name in image_names]


def test_dataset_utils_split_dataset_raises_when_no_images_exist(tmp_path):
    base_dir = tmp_path / 'dataset'
    base_dir.mkdir()

    with pytest.raises(FileNotFoundError):
        DatasetUtils.split_dataset(str(base_dir), train_ratio=0.8, val_ratio=0.2, test_ratio=0.0, shuffle=False)
