import os
from pathlib import Path
from dotenv import load_dotenv

# Base paths
from scripts.paths import BASE_DIR, OUTPUT, DATABASE, TEMPLATES, FONTS, NASHEEDS

# Load overrides if .env exists
load_dotenv(BASE_DIR / ".env")

class Config:
    # -----------------------------
    # App Environment
    # -----------------------------
    APP_ENV = os.getenv("APP_ENV", "development")

    # -----------------------------
    # Folders and Paths
    # -----------------------------
    CSV_PATH = Path(os.getenv("CSV_PATH", DATABASE / "quran_posts.csv"))
    USED_VERSES_PATH = Path(os.getenv("USED_VERSES_PATH", DATABASE / "used_verses.txt"))
    THEMES_PATH = Path(os.getenv("THEMES_PATH", DATABASE / "themes.json"))
    ASSETS_DIR = Path(os.getenv("ASSETS_DIR", TEMPLATES))
    OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", OUTPUT))
    FONTS_DIR = Path(os.getenv("FONTS_DIR", FONTS))
    NASHEEDS_DIR = Path(os.getenv("NASHEEDS_DIR", NASHEEDS))

    # -----------------------------
    # Rendering - Dimensions
    # -----------------------------
    IMAGE_WIDTH = int(os.getenv("IMAGE_WIDTH", 1080))
    IMAGE_HEIGHT = int(os.getenv("IMAGE_HEIGHT", 1080))
    MARGIN_X = int(os.getenv("MARGIN_X", 80))
    GAPS = int(os.getenv("GAPS", 20))

    # -----------------------------
    # Rendering - Assets
    # -----------------------------
    BACKGROUND_IMAGE = ASSETS_DIR / os.getenv("BACKGROUND_IMAGE", "background.jpg")
    LOGO_IMAGE = ASSETS_DIR / os.getenv("LOGO_IMAGE", "logo.png")
    SEPARATOR_IMAGE = ASSETS_DIR / os.getenv("SEPARATOR_IMAGE", "separator.png")

    # -----------------------------
    # Rendering - Fonts
    # -----------------------------
    ARABIC_FONT_PATH = FONTS_DIR / os.getenv("ARABIC_FONT_NAME", "_extracted_fonts/Amiri-Regular.ttf")
    ENGLISH_FONT_PATH = FONTS_DIR / os.getenv("ENGLISH_FONT_NAME", "PlayfairDisplay-Regular.ttf")
    
    ARABIC_FONT_SIZE_BASE = int(os.getenv("ARABIC_FONT_SIZE_BASE", 72))
    TRANSLIT_FONT_SIZE_BASE = int(os.getenv("TRANSLIT_FONT_SIZE_BASE", 36))
    TRANS_FONT_SIZE_BASE = int(os.getenv("TRANS_FONT_SIZE_BASE", 30))
    REF_FONT_SIZE_BASE = int(os.getenv("REF_FONT_SIZE_BASE", 22))

    # -----------------------------
    # Rendering - Colors (RGB string to tuple)
    # -----------------------------
    @staticmethod
    def _parse_rgb(val: str) -> tuple:
        return tuple(int(x.strip()) for x in val.split(','))

    BG_COLOR = _parse_rgb(os.getenv("BG_COLOR", "245,244,240"))
    BG_ALPHA = float(os.getenv("BG_ALPHA", 0.35))
    COLOR_ARABIC = _parse_rgb(os.getenv("COLOR_ARABIC", "10,10,10"))
    COLOR_TRANSLIT = _parse_rgb(os.getenv("COLOR_TRANSLIT", "40,40,40"))
    COLOR_TRANS = _parse_rgb(os.getenv("COLOR_TRANS", "30,30,30"))
    COLOR_REF = _parse_rgb(os.getenv("COLOR_REF", "90,90,90"))

config = Config()
