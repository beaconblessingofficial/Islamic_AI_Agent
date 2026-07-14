from pathlib import Path
import sys

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))

from scripts.image_gen import ImageGenerator
from database.dao import VerseDB
from scripts.config import config

gen = ImageGenerator(config.ASSETS_DIR, config.OUTPUT_DIR)
db = VerseDB(config.CSV_PATH, config.USED_VERSES_PATH)

v = db.select_random()
p = gen.generate_post(v, output_name="single_sample.png")
print("Generated:", p)
print("Verse:", v['surah'], v['ayah'])
print("Arabic:", v['arabic'])
