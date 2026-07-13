from pathlib import Path
import sys

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE / "scripts"))

from image_gen import ImageGenerator
from verse_db import VerseDB

assets = BASE / "templates"
output = BASE / "output"

gen = ImageGenerator(assets, output)
print("background exists", gen.background_path.exists())
print("logo exists", gen.logo_path.exists(), "logo path", gen.logo_path)
print("separator exists", gen.separator_path.exists(), "separator path", gen.separator_path)
print("ar_font_path", gen.ar_font_path)
print("en_font_path", gen.en_font_path)

db = VerseDB(BASE / "database" / "quran_posts.csv", BASE / "database" / "used_verses.txt")
verse = db.select_random()
print("verse id", verse["id"])
print("arabic text length", len(verse["arabic"]))
print("transliteration length", len(verse["transliteration"]))
print("translation length", len(verse["translation"]))

path = gen.generate_post(verse, output_name="debug_post.png")
print("generated", path)
