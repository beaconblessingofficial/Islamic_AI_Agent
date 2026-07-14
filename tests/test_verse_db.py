import sys
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from database.dao import VerseDB
from scripts.config import config


def main():
    csv_file = config.CSV_PATH
    used_file = config.USED_VERSES_PATH

    # backup existing used file
    backup = None
    if used_file.exists():
        backup = used_file.read_text(encoding="utf-8")

    db = VerseDB(csv_file, used_file)
    db.reset_used()
    total = len(db.verses)
    seen = set()

    print(f"Total verses in CSV: {total}")

    # select exactly `total` times and ensure no duplicates
    for i in range(total):
        v = db.select_random()
        vid = int(v["id"])
        assert vid not in seen, f"Duplicate verse selected before exhaustion: {vid}"
        seen.add(vid)

    print("No duplicates in single cycle — OK")

    # Next selection should trigger automatic reset and succeed
    v2 = db.select_random()
    print(f"After exhaustion, selection after reset: id={v2['id']} surah={v2['surah']}")

    # restore backup
    if backup is not None:
        used_file.write_text(backup, encoding="utf-8")
    else:
        if used_file.exists():
            used_file.unlink()

    print("Test completed successfully")


if __name__ == '__main__':
    main()
