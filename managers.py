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
                for i, line in enumerate(f):
                    line = line.strip()
                    if not line:
                        continue
                    parts = line.split()
                    if len(parts) < 5:
                        continue
                    class_id = int(parts[0])
                    cx, cy, w, h = map(float, parts[1:5])
                    center_x = cx * img_w
                    center_y = cy * img_h
                    width = w * img_w
                    height = h * img_h
                    x1 = center_x - width / 2
                    y1 = center_y - height / 2
                    x2 = center_x + width / 2
                    y2 = center_y + height / 2
                    annotations.append({'class_id': class_id, 'rect_orig': [x1, y1, x2, y2], 'yolo_string': line})
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
    def convert_to_yolo_format(class_id: int, rect: Tuple[float, float, float, float], img_size: Tuple[int, int]) -> str:
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