from typing import List, Dict, Tuple, Optional, Any
from PIL import Image

class AppState:

    def __init__(self) -> None:
        self.base_directory: str = ''
        self.image_paths: List[str] = []
        self.class_names: List[str] = []
        self.current_image_index: int = -1
        self.current_pil_image: Optional[Image.Image] = None
        self.original_image_size: Tuple[int, int] = (0, 0)
        self.annotations: List[Dict[str, Any]] = []
        self.selected_annotation_index: Optional[int] = None
        self.is_drawing: bool = False

    def get_current_image_path(self) -> Optional[str]:
        if 0 <= self.current_image_index < len(self.image_paths):
            return self.image_paths[self.current_image_index]
        return None