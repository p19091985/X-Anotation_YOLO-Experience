import os
import shutil
import random
import logging
from typing import List, Dict, Tuple, Optional, Any
from glob import glob
logger = logging.getLogger(__name__)

class AnnotationManager:

    @staticmethod
    def get_label_path(image_path: str) -> str:
        image_dir = os.path.dirname(image_path)
        base_name = os.path.splitext(os.path.basename(image_path))[0]
        parent_dir = os.path.dirname(image_dir)
        possible_label_dir = os.path.join(parent_dir, 'labels')
        if os.path.exists(possible_label_dir) and os.path.isdir(possible_label_dir):
            return os.path.join(possible_label_dir, base_name + '.txt')
        return os.path.join(image_dir, base_name + '.txt')

    @staticmethod
    def load_annotations(label_path: str, image_size: Tuple[int, int]) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        annotations = []
        img_w, img_h = image_size
        if not os.path.exists(label_path):
            return (annotations, None)
        try:
            with open(label_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    parts = line.split()
                    if len(parts) < 5:
                        continue
                    class_id = int(parts[0])
                    coords = list(map(float, parts[1:]))
                    if len(coords) == 4:
                        cx, cy, w, h = coords
                        center_x = cx * img_w
                        center_y = cy * img_h
                        width = w * img_w
                        height = h * img_h
                        x1 = center_x - width / 2
                        y1 = center_y - height / 2
                        x2 = center_x + width / 2
                        y2 = center_y + height / 2
                        annotations.append({'type': 'box', 'class_id': class_id, 'rect_orig': [x1, y1, x2, y2], 'points': [], 'yolo_string': line})
                    else:
                        points = []
                        for i in range(0, len(coords), 2):
                            px = coords[i] * img_w
                            py = coords[i + 1] * img_h
                            points.append((px, py))
                        xs = [p[0] for p in points]
                        ys = [p[1] for p in points]
                        rect = [min(xs), min(ys), max(xs), max(ys)]
                        annotations.append({'type': 'polygon', 'class_id': class_id, 'rect_orig': rect, 'points': points, 'yolo_string': line})
            return (annotations, None)
        except Exception as e:
            return ([], str(e))

    @staticmethod
    def save_annotations(label_path: str, annotations: List[Dict[str, Any]]) -> bool:
        try:
            os.makedirs(os.path.dirname(label_path), exist_ok=True)
            with open(label_path, 'w', encoding='utf-8') as f:
                for ann in annotations:
                    f.write(ann['yolo_string'] + '\n')
            return True
        except Exception as e:
            logger.error(f'Erro ao salvar anotação {label_path}: {e}')
            return False

    @staticmethod
    def convert_box_to_yolo(class_id: int, rect: List[float], img_size: Tuple[int, int]) -> str:
        img_w, img_h = img_size
        x1, y1, x2, y2 = rect
        dw = 1.0 / img_w
        dh = 1.0 / img_h
        w = x2 - x1
        h = y2 - y1
        x = x1 + w / 2
        y = y1 + h / 2
        x *= dw
        w *= dw
        y *= dh
        h *= dh
        return f'{class_id} {x:.6f} {y:.6f} {w:.6f} {h:.6f}'

    @staticmethod
    def convert_poly_to_yolo(class_id: int, points: List[Tuple[float, float]], img_size: Tuple[int, int]) -> str:
        img_w, img_h = img_size
        parts = [str(class_id)]
        for px, py in points:
            nx = px / img_w
            ny = py / img_h
            nx = max(0.0, min(1.0, nx))
            ny = max(0.0, min(1.0, ny))
            parts.append(f'{nx:.6f} {ny:.6f}')
        return ' '.join(parts)


class ClassCatalogManager:
    IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp')

    @staticmethod
    def iter_annotation_files(base_dir: str) -> List[str]:
        annotation_files = set()
        for root, _, files in os.walk(base_dir):
            image_stems = {
                os.path.splitext(file_name)[0]
                for file_name in files
                if file_name.lower().endswith(ClassCatalogManager.IMAGE_EXTENSIONS)
            }
            is_labels_dir = os.path.basename(root).casefold() == 'labels'
            for file_name in files:
                if not file_name.lower().endswith('.txt') or file_name == 'classes.txt':
                    continue
                stem = os.path.splitext(file_name)[0]
                if is_labels_dir or stem in image_stems:
                    annotation_files.add(os.path.join(root, file_name))
        return sorted(annotation_files)

    @staticmethod
    def _extract_used_class_ids(label_path: str) -> List[int]:
        class_ids = set()
        with open(label_path, 'r', encoding='utf-8') as handle:
            for line in handle:
                stripped = line.strip()
                if not stripped:
                    continue
                parts = stripped.split()
                if len(parts) < 5:
                    continue
                try:
                    class_ids.add(int(parts[0]))
                except ValueError:
                    continue
        return sorted(class_ids)

    @staticmethod
    def count_class_usage(base_dir: str, class_count: int) -> List[int]:
        usage = [0] * max(class_count, 0)
        if class_count <= 0 or not base_dir or not os.path.isdir(base_dir):
            return usage
        for label_path in ClassCatalogManager.iter_annotation_files(base_dir):
            for class_id in ClassCatalogManager._extract_used_class_ids(label_path):
                if 0 <= class_id < class_count:
                    usage[class_id] += 1
        return usage

    @staticmethod
    def remap_annotation_class_ids(base_dir: str, class_id_map: Dict[int, int], deleted_ids=None) -> None:
        if not base_dir or not os.path.isdir(base_dir):
            return
        deleted_ids = set(deleted_ids or [])
        pending_updates = []
        for label_path in ClassCatalogManager.iter_annotation_files(base_dir):
            changed = False
            updated_lines = []
            with open(label_path, 'r', encoding='utf-8') as handle:
                for raw_line in handle:
                    stripped = raw_line.strip()
                    if not stripped:
                        updated_lines.append(raw_line if raw_line.endswith('\n') else raw_line + '\n')
                        continue
                    parts = stripped.split()
                    if len(parts) < 5:
                        updated_lines.append(raw_line if raw_line.endswith('\n') else raw_line + '\n')
                        continue
                    try:
                        class_id = int(parts[0])
                    except ValueError:
                        updated_lines.append(raw_line if raw_line.endswith('\n') else raw_line + '\n')
                        continue
                    if class_id in deleted_ids:
                        raise ValueError(f'Classe em uso detectada em {label_path}: {class_id}')
                    new_class_id = class_id_map.get(class_id, class_id)
                    if new_class_id != class_id:
                        parts[0] = str(new_class_id)
                        updated_lines.append(' '.join(parts) + '\n')
                        changed = True
                    else:
                        updated_lines.append(raw_line if raw_line.endswith('\n') else raw_line + '\n')
            if changed:
                pending_updates.append((label_path, updated_lines))
        for label_path, updated_lines in pending_updates:
            with open(label_path, 'w', encoding='utf-8') as handle:
                handle.writelines(updated_lines)

class DatasetUtils:

    @staticmethod
    def split_dataset(base_dir, train_ratio, val_ratio, test_ratio, shuffle=True):
        logger.info(f'Iniciando Split: Train={train_ratio}, Val={val_ratio}, Test={test_ratio}')
        all_files = []
        valid_ext = ('.jpg', '.jpeg', '.png', '.bmp', '.tiff')
        for r, d, f in os.walk(base_dir):
            if 'labels' in r:
                continue
            for file in f:
                if file.lower().endswith(valid_ext):
                    img_path = os.path.join(r, file)
                    label_path = AnnotationManager.get_label_path(img_path)
                    pair = {'img': img_path, 'lbl': label_path if os.path.exists(label_path) else None, 'name': file}
                    all_files.append(pair)
        if not all_files:
            raise FileNotFoundError('Nenhuma imagem encontrada no diretório base.')
        if shuffle:
            random.shuffle(all_files)
        total = len(all_files)
        train_end = int(total * train_ratio)
        if test_ratio > 0:
            val_end = train_end + int(total * val_ratio)
            train_set = all_files[:train_end]
            val_set = all_files[train_end:val_end]
            test_set = all_files[val_end:]
        else:
            train_set = all_files[:train_end]
            val_set = all_files[train_end:]
            test_set = []
        dirs = {'train': {'img': os.path.join(base_dir, 'train', 'images'), 'lbl': os.path.join(base_dir, 'train', 'labels')}, 'valid': {'img': os.path.join(base_dir, 'valid', 'images'), 'lbl': os.path.join(base_dir, 'valid', 'labels')}}
        if test_ratio > 0:
            dirs['test'] = {'img': os.path.join(base_dir, 'test', 'images'), 'lbl': os.path.join(base_dir, 'test', 'labels')}
        for key in dirs:
            os.makedirs(dirs[key]['img'], exist_ok=True)
            os.makedirs(dirs[key]['lbl'], exist_ok=True)

        def move_files(file_list, dest_key):
            if dest_key not in dirs:
                return
            target_img_dir = dirs[dest_key]['img']
            target_lbl_dir = dirs[dest_key]['lbl']
            for item in file_list:
                try:
                    if os.path.dirname(item['img']) != target_img_dir:
                        shutil.move(item['img'], os.path.join(target_img_dir, item['name']))
                except shutil.Error:
                    pass
                if item['lbl']:
                    lbl_name = os.path.basename(item['lbl'])
                    if os.path.dirname(item['lbl']) != target_lbl_dir:
                        try:
                            shutil.move(item['lbl'], os.path.join(target_lbl_dir, lbl_name))
                        except shutil.Error:
                            pass
        move_files(train_set, 'train')
        move_files(val_set, 'valid')
        if test_ratio > 0:
            move_files(test_set, 'test')
        logger.info(f'Split concluído: Train={len(train_set)}, Val={len(val_set)}, Test={len(test_set)}')
