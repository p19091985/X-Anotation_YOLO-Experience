import os
import logging
from typing import List, Dict, Tuple, Optional, Any
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
    def load_annotations(label_path: str, image_size: Tuple[int, int], known_classes: List[str]=None) -> Tuple[List[Dict[str, Any]], Optional[Exception]]:
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
                    if len(parts) != 5:
                        raise ValueError(f'Linha {i + 1} não tem 5 valores.')
                    class_id, x_c, y_c, w, h = map(float, parts)
                    class_id = int(class_id)
                    if known_classes is not None:
                        if class_id < 0 or class_id >= len(known_classes):
                            logger.warning(f"Aviso: ID de classe {class_id} encontrado em '{os.path.basename(label_path)}' não existe em classes.txt!")
                    x1 = (x_c - w / 2) * img_w
                    y1 = (y_c - h / 2) * img_h
                    x2 = (x_c + w / 2) * img_w
                    y2 = (y_c + h / 2) * img_h
                    annotations.append({'yolo_string': line, 'rect_orig': [x1, y1, x2, y2], 'class_id': class_id})
            return (annotations, None)
        except (ValueError, IndexError, UnicodeDecodeError) as e:
            return ([], e)
        except Exception as e:
            return ([], e)

    @staticmethod
    def save_annotations(label_path: str, annotations: List[Dict[str, Any]]) -> bool:
        try:
            label_dir = os.path.dirname(label_path)
            if not os.path.exists(label_dir):
                os.makedirs(label_dir, exist_ok=True)
            if not annotations:
                if os.path.exists(label_path):
                    os.remove(label_path)
                return True
            with open(label_path, 'w', encoding='utf-8') as f:
                all_lines = [ann['yolo_string'] for ann in annotations]
                f.write('\n'.join(all_lines))
            return True
        except Exception:
            return False

    @staticmethod
    def convert_to_yolo_format(class_id: int, box_coords: Tuple[float, float, float, float], image_size: Tuple[int, int]) -> str:
        x1, y1, x2, y2 = box_coords
        orig_w, orig_h = image_size
        if orig_w == 0 or orig_h == 0:
            return ''
        abs_x1, abs_y1 = (min(x1, x2), min(y1, y2))
        abs_x2, abs_y2 = (max(x1, x2), max(y1, y2))
        box_w, box_h = (abs_x2 - abs_x1, abs_y2 - abs_y1)
        center_x, center_y = (abs_x1 + box_w / 2, abs_y1 + box_h / 2)
        return f'{class_id} {center_x / orig_w:.6f} {center_y / orig_h:.6f} {box_w / orig_w:.6f} {box_h / orig_h:.6f}'