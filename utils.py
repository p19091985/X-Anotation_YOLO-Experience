import os
from typing import Optional

def find_font_path() -> Optional[str]:
    font_paths = ['c:/windows/fonts/arial.ttf', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', '/System/Library/Fonts/Supplemental/Arial.ttf']
    for path in font_paths:
        if os.path.exists(path):
            return path
    return None