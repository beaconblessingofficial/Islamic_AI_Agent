"""Tests for database.dao.VerseDB.

Covers (per TODO.md 1.3.9):
  * load
  * select_random
  * exhaustion -> auto-reset
  * mark_used idempotency
  * select_by_theme (case-insensitive)
  * soft_reset

Backs up `database/used_verses.txt` and restores it after each test so the
test is safe to run against the real corpus.
"""

from pathlib import Path

from database.dao import REQUIRED_COLUMNS, VerseDB
from scripts.config import config


CSV_FILE = config.CSV_PATH
USED_FILE = config.USED_VERSES_PATH


def _make_db_with_clean_used() -> VerseDB:
    """Create a VerseDB and reset its used-verses ledger to empty."""
    db = VerseDB(CSV_FILE, USED_FILE)
    db.reset_used()
    return db


def _restore_used_backup(backup: str | None) -> None:
    if backup is None:
        if USED_FILE.exists():
            USED_FILE.unlink()
    else:
        USED_FILE.write_text(backup, encoding="utf-8")


def test_load():
    """Every required column is present; every row has all 8 fields filled."""
    backup = USED_FILE.read_text(encoding="utf-8") if USED_FILE.exists() else None
    try:
        db = _make_db_with_clean_used()
        assert len(db.verses) > 0, "expected at least one verse in the corpus"
        for vid, verse in db.verses.items():
            for col in REQUIRED_COLUMNS:
                assert verse.get(col), f"verse {vid} missing {col!r}"
    finally:
        _restore_used_backup(backup)


def test_select_random_marks_used_and_avoids_duplicates_within_cycle():
    """`select_random` never returns the same verse twice in a single cycle."""
    backup = USED_FILE.read_text(encoding="utf-8") if USED_FILE.exists() else None
    try:
        db = _make_db_with_clean_used()
        total = len(db.verses)
        seen = set()
        for _ in range(total):
            v = db.select_random()
            vid = int(v["id"])
            assert vid not in seen, f"duplicate verse within a single cycle: {vid}"
            seen.add(vid)
        assert len(seen) == total
    finally:
        _restore_used_backup(backup)


def test_exhaustion_triggers_auto_reset():
    """After selecting every verse once, the next selection succeeds via reset."""
    backup = USED_FILE.read_text(encoding="utf-8") if USED_FILE.exists() else None
    try:
        db = _make_db_with_clean_used()
        total = len(db.verses)
        for _ in range(total):
            db.select_random()
        # After exhaustion, the next call must succeed (auto-reset).
        v = db.select_random()
        assert v is not None
        assert int(v["id"]) in db.verses
    finally:
        _restore_used_backup(backup)


def test_mark_used_is_idempotent():
    """Calling mark_used twice on the same id is a no-op (no duplicate line)."""
    backup = USED_FILE.read_text(encoding="utf-8") if USED_FILE.exists() else None
    try:
        db = _make_db_with_clean_used()
        db.mark_used(7)
        db.mark_used(7)
        db.mark_used(7)
        # Read the file directly to confirm only one line for id 7.
        lines = [ln.strip() for ln in USED_FILE.read_text(encoding="utf-8").splitlines() if ln.strip()]
        assert lines.count("7") == 1, f"expected one line for id 7, got {lines.count('7')}"
    finally:
        _restore_used_backup(backup)


def test_select_by_theme_is_case_insensitive():
    """`select_by_theme` returns matching verses regardless of input case."""
    backup = USED_FILE.read_text(encoding="utf-8") if USED_FILE.exists() else None
    try:
        db = _make_db_with_clean_used()
        lower = db.select_by_theme("forgiveness")
        upper = db.select_by_theme("FORGIVENESS")
        mixed = db.select_by_theme("Forgiveness")
        assert lower == upper == mixed
        assert len(lower) > 0, "expected at least one Forgiveness verse in the corpus"
        for v in lower:
            assert v["theme"].lower() == "forgiveness"
    finally:
        _restore_used_backup(backup)


def test_select_by_id_returns_none_for_missing():
    """`select_by_id` returns None for ids that are not in the corpus."""
    backup = USED_FILE.read_text(encoding="utf-8") if USED_FILE.exists() else None
    try:
        db = _make_db_with_clean_used()
        assert db.select_by_id(999_999) is None
        # And a real id returns a verse.
        any_id = next(iter(db.verses.keys()))
        v = db.select_by_id(any_id)
        assert v is not None
        assert int(v["id"]) == any_id
    finally:
        _restore_used_backup(backup)


def test_list_unused_filters_by_theme():
    """`list_unused(theme=...)` returns only unused ids in that theme."""
    backup = USED_FILE.read_text(encoding="utf-8") if USED_FILE.exists() else None
    try:
        db = _make_db_with_clean_used()
        # All Forgiveness verses, all unused.
        all_forg = db.list_unused(theme="Forgiveness")
        assert len(all_forg) > 0
        for vid in all_forg:
            assert db.verses[vid]["theme"].lower() == "forgiveness"
        # Mark one as used; it should drop out.
        db.mark_used(all_forg[0])
        after = db.list_unused(theme="Forgiveness")
        assert all_forg[0] not in after
        assert len(after) == len(all_forg) - 1
    finally:
        _restore_used_backup(backup)


def test_soft_reset_keeps_recent_clears_old():
    """`soft_reset(N)` keeps the most recent N used-ids and clears the rest."""
    backup = USED_FILE.read_text(encoding="utf-8") if USED_FILE.exists() else None
    try:
        db = _make_db_with_clean_used()
        # Mark ids 1..10 as used, in order.
        for vid in range(1, 11):
            db.mark_used(vid)
        # soft_reset(3) keeps the 3 most recent: [8, 9, 10].
        removed = db.soft_reset(older_than_days=3)
        assert removed == 7
        assert db.used_ids == [8, 9, 10]
    finally:
        _restore_used_backup(backup)


def test_soft_reset_zero_keeps_everything():
    """`soft_reset(0)` is a no-op."""
    backup = USED_FILE.read_text(encoding="utf-8") if USED_FILE.exists() else None
    try:
        db = _make_db_with_clean_used()
        for vid in range(1, 6):
            db.mark_used(vid)
        removed = db.soft_reset(older_than_days=0)
        assert removed == 0
        assert db.used_ids == [1, 2, 3, 4, 5]
    finally:
        _restore_used_backup(backup)


def test_list_recently_used_returns_tail_of_ledger():
    """`list_recently_used(N)` returns the last N used-ids, newest-first."""
    backup = USED_FILE.read_text(encoding="utf-8") if USED_FILE.exists() else None
    try:
        db = _make_db_with_clean_used()
        for vid in [3, 5, 7, 9, 11]:
            db.mark_used(vid)
        # Append order: [3, 5, 7, 9, 11]. Last 3 newest-first: [11, 9, 7].
        assert db.list_recently_used(days=3) == [11, 9, 7]
        # Days > len returns the full list, newest-first.
        assert db.list_recently_used(days=10) == [11, 9, 7, 5, 3]
        # Days <= 0 returns empty.
        assert db.list_recently_used(days=0) == []
    finally:
        _restore_used_backup(backup)


# ---------------------------------------------------------------------------
# Task A4: Concurrency-safety tests
# ---------------------------------------------------------------------------

def _cleanup_lock():
    """Remove the sidecar lock file if it exists."""
    lock_file = USED_FILE.with_suffix(".lock")
    if lock_file.exists():
        lock_file.unlink()


def test_concurrent_select_random_no_duplicates():
    """Two threads calling select_random on separate VerseDB instances
    never pick the same verse (Task 1.4 acceptance test)."""
    import threading

    backup = USED_FILE.read_text(encoding="utf-8") if USED_FILE.exists() else None
    try:
        db1 = _make_db_with_clean_used()
        db2 = VerseDB(CSV_FILE, USED_FILE)
        results = [None, None]
        errors = [None, None]

        def pick(idx, db):
            try:
                results[idx] = db.select_random()
            except Exception as e:
                errors[idx] = e

        t1 = threading.Thread(target=pick, args=(0, db1))
        t2 = threading.Thread(target=pick, args=(1, db2))
        t1.start()
        t2.start()
        t1.join(timeout=15)
        t2.join(timeout=15)

        assert errors[0] is None, f"Thread 1 error: {errors[0]}"
        assert errors[1] is None, f"Thread 2 error: {errors[1]}"
        assert results[0] is not None
        assert results[1] is not None
        assert results[0]["id"] != results[1]["id"], (
            f"Both threads picked the same verse: {results[0]['id']}"
        )
    finally:
        _restore_used_backup(backup)
        _cleanup_lock()


def test_concurrent_mark_used_file_integrity():
    """After concurrent mark_used calls from separate VerseDB instances,
    the file contains all expected unique ids with no duplicates."""
    import threading

    backup = USED_FILE.read_text(encoding="utf-8") if USED_FILE.exists() else None
    try:
        _make_db_with_clean_used()  # start clean
        ids_to_mark = list(VerseDB(CSV_FILE, USED_FILE).verses.keys())[:10]
        errors: list = []

        def mark(vid):
            try:
                thread_db = VerseDB(CSV_FILE, USED_FILE)
                thread_db.mark_used(vid)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=mark, args=(vid,)) for vid in ids_to_mark]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=15)

        assert not errors, f"Errors during concurrent mark_used: {errors}"

        final_db = VerseDB(CSV_FILE, USED_FILE)
        for vid in ids_to_mark:
            assert vid in final_db.used_ids, (
                f"id {vid} missing after concurrent writes"
            )
        assert len(final_db.used_ids) == len(set(final_db.used_ids)), (
            "Duplicate ids in used_verses.txt after concurrent writes"
        )
    finally:
        _restore_used_backup(backup)
        _cleanup_lock()


def test_lock_file_created_on_first_use():
    """After a write operation, the sidecar .lock file exists."""
    backup = USED_FILE.read_text(encoding="utf-8") if USED_FILE.exists() else None
    lock_file = USED_FILE.with_suffix(".lock")
    try:
        _cleanup_lock()
        db = _make_db_with_clean_used()
        db.mark_used(1)
        assert lock_file.exists(), "Lock file was not created"
    finally:
        _restore_used_backup(backup)
        _cleanup_lock()


def test_lock_released_after_operation():
    """After mark_used returns, another VerseDB instance can immediately
    acquire the lock (i.e. the lock is not held past the method call)."""
    backup = USED_FILE.read_text(encoding="utf-8") if USED_FILE.exists() else None
    try:
        db1 = _make_db_with_clean_used()
        db1.mark_used(1)
        # If the lock were not released, this would time out.
        db2 = VerseDB(CSV_FILE, USED_FILE)
        db2.mark_used(2)
        # Both ids should be in the file.
        db3 = VerseDB(CSV_FILE, USED_FILE)
        assert 1 in db3.used_ids
        assert 2 in db3.used_ids
    finally:
        _restore_used_backup(backup)
        _cleanup_lock()

