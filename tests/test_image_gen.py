import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from scripts.image_gen import ImageGenerator
from database.dao import VerseDB
from scripts.config import config

def main():
    gen = ImageGenerator(config.ASSETS_DIR, config.OUTPUT_DIR)
    db = VerseDB(config.CSV_PATH, config.USED_VERSES_PATH)

    paths = []
    for i in range(20):
        v = db.select_random()
        p = gen.generate_post(v, output_name=f"post_{i+1:02d}.png")
        print("Saved:", p)
        paths.append(p)

    print(f"Generated {len(paths)} images")


if __name__ == '__main__':
    main()
