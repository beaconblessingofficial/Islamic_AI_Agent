from pathlib import Path
import sys

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE / "scripts"))

from image_gen import ImageGenerator
from verse_db import VerseDB

assets = BASE / "templates"
output = BASE / "output"

gen = ImageGenerator(assets, output)
db = VerseDB(BASE / "database" / "quran_posts.csv", BASE / "database" / "used_verses.txt")

v = db.select_random()
p = gen.generate_post(v, output_name="single_sample.png")
print("Generated:", p)
print("Verse:", v['surah'], v['ayah'])
print("Arabic:", v['arabic'])
