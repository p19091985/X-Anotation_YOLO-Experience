import platform

class Config:
    APP_NAME = 'X-Annotation YOLO Ultimate (v7.0)'
    DEFAULT_GEOMETRY = '1440x900'
    MIN_GEOMETRY = '1024x600'
    STYLE_THEME = 'clam'
    IS_WINDOWS = platform.system() == 'Windows'
    IS_LINUX = platform.system() == 'Linux'
    IS_MAC = platform.system() == 'Darwin'
    FONTS = {'main': ('Segoe UI', 10) if IS_WINDOWS else ('Helvetica', 10), 'main_bold': ('Segoe UI', 10, 'bold') if IS_WINDOWS else ('Helvetica', 10, 'bold'), 'header': ('Impact', 16) if IS_WINDOWS else ('Dejavu Sans', 16, 'bold'), 'sub_header': ('Segoe UI', 12) if IS_WINDOWS else ('Helvetica', 12), 'mono': ('Consolas', 10) if IS_WINDOWS else ('Courier New', 10), 'mono_small': ('Consolas', 9) if IS_WINDOWS else ('Courier New', 9), 'small': ('Segoe UI', 8) if IS_WINDOWS else ('Helvetica', 8), 'small_italic': ('Segoe UI', 8, 'italic') if IS_WINDOWS else ('Helvetica', 8, 'italic')}
    CANVAS_BG_COLOR = '#1E1E1E'
    HIGHLIGHT_COLOR = '#FFFFFF'
    NEW_BOX_COLOR = '#00FFFF'
    HIGHLIGHT_WIDTH = 3
    BOX_WIDTH = 2
    FONT_COLOR = '#FFFFFF'
    FONT_SIZE = 12
    DIMENSION_TEXT_COLOR = '#00FF00'
    MIN_BOX_SIZE_TO_SHOW_LABEL = 0
    AUTO_DISABLE_DRAW_MODE = False
    CONFIG_FILE_PATH = 'yolo_editor_config.json'
    CLASS_COLORS = ['#FF3B30', '#4CD964', '#FFCC00', '#5856D6', '#FF9500', '#5AC8FA', '#007AFF', '#FF2D55', '#8E8E93', '#E5E5EA', '#A2845E', '#FF375F', '#BF5AF2', '#64D2FF', '#0A84FF']