"""Data-access object for the Quran verse corpus.

This module owns:
  * Loading the corpus from `database/quran_posts.csv` (UTF-8 with BOM).
  * Tracking posted verses in `database/used_verses.txt` (line-per-id).
  * Selecting a verse (random, by theme, by surah, by id) subject to the
    used-verses ledger, with automatic reset on exhaustion.

The atomic-write contract for the used-verses ledger (`.tmp` + `replace`) is
preserved for backwards compatibility with Phase 1 callers.  Concurrency is
guarded by a cross-platform advisory file lock (Task 1.4, Option A).  The lock
covers the full read-modify-write cycle to prevent TOCTOU races when multiple
processes run ``make_post`` simultaneously.  A sidecar ``.lock`` file is used
so the data file itself is never locked.
"""

import contextlib
import csv
import json
import random
import re
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Any


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


# ---------------------------------------------------------------------------
# Cross-platform advisory file lock
# ---------------------------------------------------------------------------

@contextlib.contextmanager
def _file_lock(lock_path: Path, timeout: float = 10.0):
    """Cross-platform advisory file lock with timeout.

    Uses ``msvcrt.locking`` on Windows and ``fcntl.flock`` on POSIX.
    The lock file is created if it does not exist.

    Parameters
    ----------
    lock_path:
        Path to the sidecar lock file (e.g. ``used_verses.lock``).
    timeout:
        Maximum seconds to wait for the lock before raising ``TimeoutError``.
    """
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    # Ensure the lock file exists.  pathlib.touch() is atomic on both
    # Windows and POSIX and never truncates.
    lock_path.touch(exist_ok=True)
    # If the file is empty (first touch), write a sentinel byte so
    # msvcrt has a byte range to lock.
    if lock_path.stat().st_size == 0:
        try:
            with open(lock_path, "ab") as init_fh:
                init_fh.write(b"L")
        except OSError:
            pass  # another thread may have written already

    fh = None
    acquired = False
    deadline = time.monotonic() + timeout
    try:
        # Retry loop: on Windows, both the open() and the locking() call
        # can raise PermissionError when another thread/process holds a
        # handle.  We retry everything until we succeed or time out.
        while True:
            try:
                if fh is None:
                    fh = open(lock_path, "r+b")  # noqa: SIM115
                fh.seek(0)
                if sys.platform == "win32":
                    import msvcrt
                    msvcrt.locking(fh.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                acquired = True
                break
            except (OSError, BlockingIOError):
                if time.monotonic() >= deadline:
                    raise TimeoutError(
                        f"Could not acquire file lock {lock_path} "
                        f"within {timeout}s"
                    )
                time.sleep(0.05)
        yield
    finally:
        if acquired and fh is not None:
            try:
                if sys.platform == "win32":
                    import msvcrt
                    msvcrt.locking(fh.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(fh.fileno(), fcntl.LOCK_UN)
            except OSError:
                pass
        if fh is not None:
            fh.close()


class VerseDB:
    """Loads, validates, and queries the Quran verse corpus."""

    def __init__(self, csv_path: Path, used_path: Path):
        self.csv_path = Path(csv_path)
        self.used_path = Path(used_path)
        self._lock_path = self.used_path.with_suffix(".lock")
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
        # On Windows, reading can fail transiently when another process is
        # in the middle of an atomic replace.  Retry briefly.
        deadline = time.monotonic() + 2.0
        while True:
            try:
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
                return
            except PermissionError:
                if time.monotonic() >= deadline:
                    raise
                time.sleep(0.05)

    def _persist_used(self):
        # Atomic write: write to .tmp, then replace the original.
        tmp = self.used_path.with_suffix(".tmp")
        with tmp.open("w", encoding="utf-8") as fh:
            for uid in self.used_ids:
                fh.write(f"{uid}\n")
        # On Windows, replace can fail transiently when another process has
        # the target file open for reading.  Retry briefly.
        deadline = time.monotonic() + 2.0
        while True:
            try:
                tmp.replace(self.used_path)
                return
            except PermissionError:
                if time.monotonic() >= deadline:
                    raise
                time.sleep(0.05)

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
        with _file_lock(self._lock_path):
            self._load_used()
            if vid not in self.used_ids:
                self.used_ids.append(vid)
                self._persist_used()

    def reset_used(self):
        with _file_lock(self._lock_path):
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
        with _file_lock(self._lock_path):
            self._load_used()
            keep = self.used_ids[-older_than_days:]
            removed = len(self.used_ids) - len(keep)
            if removed > 0:
                self.used_ids = keep
                self._persist_used()
            return removed

    # ----- public: selection -----

    def select_random(
        self,
        theme: Optional[str] = None,
        dry_run: bool = False,
        exclude_ids: Optional[List[int]] = None
    ) -> Dict[str, str]:
        # Hold the lock for the entire read-pick-mark-write cycle so that
        # two concurrent processes cannot select the same verse.
        with _file_lock(self._lock_path):
            self._load_used()

            def get_candidates() -> List[int]:
                unused = self._get_unused_ids()
                if exclude_ids:
                    unused = [u for u in unused if u not in exclude_ids]
                if theme:
                    t_lower = theme.lower()
                    unused = [u for u in unused if self.verses[u].get("theme", "").lower() == t_lower]
                return unused

            candidates = get_candidates()
            
            if not candidates:
                if not dry_run:
                    self.used_ids = []
                    self._persist_used()
                
                candidates = get_candidates()
                # If STILL no candidates (e.g. dry_run=True simulating reset)
                if not candidates and dry_run:
                    all_ids = list(self.verses.keys())
                    if exclude_ids:
                        all_ids = [u for u in all_ids if u not in exclude_ids]
                    if theme:
                        t_lower = theme.lower()
                        all_ids = [u for u in all_ids if self.verses.get(u, {}).get("theme", "").lower() == t_lower]
                    candidates = all_ids

            while candidates:
                vid = random.choice(candidates)
                verse = self.verses.get(vid)
                if verse and self.validate_verse(verse):
                    if not dry_run:
                        if vid not in self.used_ids:
                            self.used_ids.append(vid)
                            self._persist_used()
                    return verse
                # invalid verse -> mark used to avoid infinite loop
                if not dry_run:
                    if vid not in self.used_ids:
                        self.used_ids.append(vid)
                        self._persist_used()
                candidates.remove(vid)

            raise RuntimeError(f"No valid verses available (theme={theme})")

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


class ThemeDB:
    """Loads and queries the themes registry."""

    def __init__(self, json_path: Path | str):
        self.json_path = Path(json_path)
        self.themes: Dict[str, Dict[str, Any]] = {}
        self._load()

    def _load(self):
        if not self.json_path.exists():
            raise FileNotFoundError(f"Themes JSON not found: {self.json_path}")
        
        with self.json_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
            
        for theme_name, details in data.items():
            color = details.get("accent_color", "")
            if not re.match(r"^#[0-9A-Fa-f]{6}$", color):
                raise ValueError(f"Theme '{theme_name}' has invalid accent_color: {color}")
            self.themes[theme_name] = details

    def get(self, theme: str) -> Dict[str, Any]:
        """Get theme configuration by exact name (case-sensitive as keys)."""
        if theme not in self.themes:
            raise KeyError(f"Theme not found: {theme}")
        return self.themes[theme]

    def names(self) -> List[str]:
        """Return all registered theme names."""
        return list(self.themes.keys())
