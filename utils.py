import os
from typing import Optional

def find_font_path() -> Optional[str]:
    try:
        from matplotlib import font_manager
        font_path = font_manager.findfont('Arial')
        if os.path.exists(font_path):
            return font_path
    except ImportError:
        pass
    font_paths = ['c:/windows/fonts/arial.ttf', 'c:/windows/fonts/segoeui.ttf', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf', '/System/Library/Fonts/Supplemental/Arial.ttf', '/Library/Fonts/Arial.ttf']
    for path in font_paths:
        if os.path.exists(path):
            return path
    return None