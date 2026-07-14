from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

from scripts.image_gen import ImageGenerator
from database.dao import VerseDB


def main():
    assets = BASE_DIR / "templates"
    out = BASE_DIR / "output"
    gen = ImageGenerator(assets, out)
    db = VerseDB(BASE_DIR / "database" / "quran_posts.csv", BASE_DIR / "database" / "used_verses.txt")

    paths = []
    for i in range(20):
        v = db.select_random()
        p = gen.generate_post(v, output_name=f"post_{i+1:02d}.png")
        print("Saved:", p)
        paths.append(p)

    print(f"Generated {len(paths)} images")


if __name__ == '__main__':
    main()
