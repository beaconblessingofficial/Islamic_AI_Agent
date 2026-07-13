import csv
import random
from pathlib import Path
from typing import Dict, List


REQUIRED_COLUMNS = [
    "id",
    "surah",
    "ayah",
    "theme",
    "arabic",
    "transliteration",
    "translation",
    "caption_topic",
]


class VerseDB:
    def __init__(self, csv_path: Path, used_path: Path):
        self.csv_path = Path(csv_path)
        self.used_path = Path(used_path)
        self.verses: Dict[int, Dict[str, str]] = {}
        self.used_ids: List[int] = []
        self._load_csv()
        self._load_used()

    def _load_csv(self):
        if not self.csv_path.exists():
            raise FileNotFoundError(f"CSV file not found: {self.csv_path}")

        with self.csv_path.open("r", encoding="utf-8-sig") as fh:
            reader = csv.DictReader(fh)
            headers = [h.strip() for h in reader.fieldnames or []]
            missing = [c for c in REQUIRED_COLUMNS if c not in headers]
            if missing:
                raise ValueError(f"CSV missing required columns: {missing}")

            for row in reader:
                try:
                    vid = int(row["id"])
                except Exception:
                    continue
                # normalize values
                verse = {k: (row.get(k, "") or "").strip() for k in REQUIRED_COLUMNS}
                # Auto-generate caption_topic when missing: prefer theme, else use short translation excerpt
                if not verse.get("caption_topic"):
                    theme_val = verse.get("theme", "").strip()
                    if theme_val:
                        verse["caption_topic"] = theme_val
                    else:
                        # take first 6 words of translation as fallback
                        trans = verse.get("translation", "")
                        excerpt = " ".join(trans.split()[:6]).strip()
                        verse["caption_topic"] = excerpt or "Quran Verse"
                self.verses[vid] = verse

        if not self.verses:
            raise ValueError("No verses loaded from CSV")

    def _load_used(self):
        if not self.used_path.exists():
            self.used_ids = []
            return
        with self.used_path.open("r", encoding="utf-8") as fh:
            ids = []
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    ids.append(int(line))
                except ValueError:
                    continue
            self.used_ids = ids

    def _persist_used(self):
        # atomic write
        tmp = self.used_path.with_suffix(".tmp")
        with tmp.open("w", encoding="utf-8") as fh:
            for uid in self.used_ids:
                fh.write(f"{uid}\n")
        tmp.replace(self.used_path)

    def _get_unused_ids(self) -> List[int]:
        all_ids = set(self.verses.keys())
        used = set(self.used_ids)
        unused = list(all_ids - used)
        return unused

    def validate_verse(self, verse: Dict[str, str]) -> bool:
        # Ensure all required fields are present and non-empty
        for k in REQUIRED_COLUMNS:
            v = verse.get(k, "")
            if not v:
                return False
        return True

    def reset_used(self):
        self.used_ids = []
        self._persist_used()

    def mark_used(self, vid: int):
        if vid not in self.used_ids:
            self.used_ids.append(vid)
            self._persist_used()

    def select_random(self) -> Dict[str, str]:
        # pick from unused; if exhausted, reset and continue
        unused = self._get_unused_ids()
        if not unused:
            # reset automatically
            self.reset_used()
            unused = self._get_unused_ids()

        attempts = 0
        while unused:
            vid = random.choice(unused)
            verse = self.verses.get(vid)
            attempts += 1
            if verse and self.validate_verse(verse):
                self.mark_used(vid)
                return verse
            # invalid verse -> mark used to avoid infinite loop
            self.mark_used(vid)
            unused = self._get_unused_ids()

        raise RuntimeError("No valid verses available")


if __name__ == "__main__":
    BASE_DIR = Path(__file__).resolve().parent.parent
    csv_file = BASE_DIR / "database" / "quran_posts.csv"
    used_file = BASE_DIR / "database" / "used_verses.txt"

    db = VerseDB(csv_file, used_file)
    v = db.select_random()
    print("Selected verse:")
    for k in REQUIRED_COLUMNS:
        print(f"{k}: {v.get(k)}")
