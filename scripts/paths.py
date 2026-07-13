from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

UPLOADS = BASE_DIR / "uploads"
OUTPUT = BASE_DIR / "output"
DATABASE = BASE_DIR / "database"
NASHEEDS = BASE_DIR / "nasheeds"
TEMPLATES = BASE_DIR / "templates"
FONTS = BASE_DIR / "fonts"

print("BASE:", BASE_DIR)
print("UPLOADS:", UPLOADS)
print("OUTPUT:", OUTPUT)