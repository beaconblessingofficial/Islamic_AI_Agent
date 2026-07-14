from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "scripts"))

from verse_db import VerseDB, REQUIRED_COLUMNS


def main():
    csv_file = BASE_DIR / "database" / "quran_posts.csv"
    used_file = BASE_DIR / "database" / "used_verses.txt"
    db = VerseDB(csv_file, used_file)
    print(f"Loaded {len(db.verses)} verses")
    for vid, v in list(db.verses.items())[:5]:
        print("---")
        print("id:", vid)
        for k in REQUIRED_COLUMNS:
            val = v.get(k)
            print(f"{k}: ({len(val) if val is not None else 0}) '{val}'")
        print("valid:", db.validate_verse(v))


if __name__ == '__main__':
    main()
