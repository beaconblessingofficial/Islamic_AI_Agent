"""Data-access object for the Quran verse corpus.

This module owns:
  * Loading the corpus from `database/quran_posts.csv` (UTF-8 with BOM).
  * Tracking posted verses in `database/used_verses.txt` (line-per-id).
  * Selecting a verse (random, by theme, by surah, by id) subject to the
    used-verses ledger, with automatic reset on exhaustion.

The atomic-write contract for the used-verses ledger (`.tmp` + `replace`) is
preserved for backwards compatibility with Phase 1 callers. Concurrency safety
(file lock or SQLite) is deferred to Phase 2.
"""

import csv
import random
from pathlib import Path
from typing import Dict, List, Optional


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
    """Loads, validates, and queries the Quran verse corpus."""

    def __init__(self, csv_path: Path, used_path: Path):
        self.csv_path = Path(csv_path)
        self.used_path = Path(used_path)
        self.verses: Dict[int, Dict[str, str]] = {}
        self.used_ids: List[int] = []
        self._load_csv()
        self._load_used()

    # ----- internal: load + persist -----

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
                verse = {k: (row.get(k, "") or "").strip() for k in REQUIRED_COLUMNS}
                # Auto-fill caption_topic when missing.
                if not verse.get("caption_topic"):
                    theme_val = verse.get("theme", "").strip()
                    if theme_val:
                        verse["caption_topic"] = theme_val
                    else:
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
        # Atomic write: write to .tmp, then replace the original.
        tmp = self.used_path.with_suffix(".tmp")
        with tmp.open("w", encoding="utf-8") as fh:
            for uid in self.used_ids:
                fh.write(f"{uid}\n")
        tmp.replace(self.used_path)

    def _get_unused_ids(self) -> List[int]:
        all_ids = set(self.verses.keys())
        used = set(self.used_ids)
        return list(all_ids - used)

    # ----- public: validation -----

    def validate_verse(self, verse: Dict[str, str]) -> bool:
        for k in REQUIRED_COLUMNS:
            v = verse.get(k, "")
            if not v:
                return False
        return True

    # ----- public: used-verses ledger -----

    def mark_used(self, vid: int):
        if vid not in self.used_ids:
            self.used_ids.append(vid)
            self._persist_used()

    def reset_used(self):
        self.used_ids = []
        self._persist_used()

    def soft_reset(self, older_than_days: int = 30) -> int:
        """Clear used-verses entries older than the cutoff.

        The used-verses file is line-per-id with no timestamps, so the best
        proxy is the file's natural append order: the most recent N entries
        are at the bottom. We keep the newest `older_than_days` entries and
        clear the rest. Returns the count removed.
        """
        if older_than_days <= 0:
            return 0
        keep = self.used_ids[-older_than_days:]
        removed = len(self.used_ids) - len(keep)
        if removed > 0:
            self.used_ids = keep
            self._persist_used()
        return removed

    # ----- public: selection -----

    def select_random(self) -> Dict[str, str]:
        # pick from unused; if exhausted, reset and continue
        unused = self._get_unused_ids()
        if not unused:
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

    def select_by_id(self, vid: int) -> Optional[Dict[str, str]]:
        return self.verses.get(int(vid))

    def select_by_theme(self, theme: str) -> List[Dict[str, str]]:
        """Return all verses matching the given theme (case-insensitive),
        regardless of used-state."""
        theme_lower = theme.lower()
        return [v for v in self.verses.values()
                if v.get("theme", "").lower() == theme_lower]

    def select_by_surah(self, surah: str) -> List[Dict[str, str]]:
        """Return all verses from the given surah (case-insensitive),
        regardless of used-state."""
        surah_lower = surah.lower()
        return [v for v in self.verses.values()
                if v.get("surah", "").lower() == surah_lower]

    def list_unused(self, theme: Optional[str] = None) -> List[int]:
        """Return ids that have not been used. Optionally filter by theme."""
        used = set(self.used_ids)
        all_unused = [vid for vid in self.verses.keys() if vid not in used]
        if theme is None:
            return all_unused
        theme_lower = theme.lower()
        return [vid for vid in all_unused
                if self.verses[vid].get("theme", "").lower() == theme_lower]

    def list_recently_used(self, days: int = 30) -> List[int]:
        """Return ids used within the last N days, newest-first.

        The used-verses file has no timestamps, so this is a proxy: we return
        the tail of the append-ordered list. Real timestamped history is
        introduced in Phase 2 (database/history.py + SQLite).
        """
        if days <= 0:
            return []
        cutoff = max(0, len(self.used_ids) - days)
        return list(reversed(self.used_ids[cutoff:]))
