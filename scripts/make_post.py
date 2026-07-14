"""Entry point for image post generation.

Usage (from the repo root):
    python -m scripts.make_post [options]

Options:
    --verse-id N       Use a specific verse id (bypasses random selection).
    --theme T          Filter random selection to verses with this theme.
    --count N          Number of posts to generate (default: 1).
    --output-name NAME Base filename for output PNGs.
                       When --count > 1 an index suffix is appended automatically.
                       Default: post_<YYYYMMDD_HHMMSS>.png
    --dry-run          Generate images but do NOT mark verses as used in
                       database/used_verses.txt.

Examples:
    # One random post
    python -m scripts.make_post

    # Five posts from the Guidance theme, no used-verse writes
    python -m scripts.make_post --theme Guidance --count 5 --dry-run

    # Force a specific verse
    python -m scripts.make_post --verse-id 7
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

# Ensure the repo root is on sys.path when run directly (not as a module)
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(_REPO_ROOT / ".env")

from scripts.config import config           # noqa: E402
from scripts.image_gen import ImageGenerator  # noqa: E402
from database.dao import VerseDB, ThemeDB     # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_output_name(base: str | None, index: int, count: int) -> str:
    """Return the output filename for a given post index.

    If *base* is given it is used as-is for single posts, or with a
    zero-padded index suffix for batches.  When *base* is None the name
    is generated from the current timestamp.
    """
    if base:
        stem = Path(base).stem
        suffix = Path(base).suffix or ".png"
        if count == 1:
            return f"{stem}{suffix}"
        return f"{stem}_{index + 1:02d}{suffix}"
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    if count == 1:
        return f"post_{ts}.png"
    return f"post_{ts}_{index + 1:02d}.png"


# ---------------------------------------------------------------------------
# Core pipeline
# ---------------------------------------------------------------------------

def run(
    verse_id: int | None,
    theme: str | None,
    count: int,
    output_name: str | None,
    dry_run: bool,
) -> list[Path]:
    """Generate *count* images and return their output paths."""

    gen = ImageGenerator(config.ASSETS_DIR, config.OUTPUT_DIR)
    db = VerseDB(config.CSV_PATH, config.USED_VERSES_PATH)
    theme_db = ThemeDB(config.THEMES_PATH)

    paths: list[Path] = []

    for i in range(count):
        # --- Select verse -----------------------------------------------
        if verse_id is not None:
            verse = db.select_by_id(verse_id)
            if verse is None:
                print(
                    f"[ERROR] Verse id {verse_id} not found in corpus.",
                    file=sys.stderr,
                )
                sys.exit(1)
        elif theme:
            unused_ids = db.list_unused(theme=theme)
            if not unused_ids:
                # All theme verses used – soft reset limited to this theme by
                # clearing the full ledger (the broader reset guard; acceptable
                # at Phase 0 scale).
                print(
                    f"[WARNING] All verses for theme '{theme}' already used. "
                    "Resetting used-verse ledger.",
                    file=sys.stderr,
                )
                db.reset_used()
                unused_ids = db.list_unused(theme=theme)
            if not unused_ids:
                print(
                    f"[ERROR] No verses found for theme '{theme}'.",
                    file=sys.stderr,
                )
                sys.exit(1)
            import random
            vid = random.choice(unused_ids)
            verse = db.select_by_id(vid)
        else:
            verse = db.select_random()

        # --- Generate image ---------------------------------------------
        name = _build_output_name(output_name, i, count)
        
        verse_theme = verse.get("theme")
        accent_color = None
        if verse_theme:
            try:
                accent_color = theme_db.get(verse_theme).get("accent_color")
            except KeyError:
                pass
                
        path = gen.generate_post(verse, output_name=name, accent_color=accent_color)
        paths.append(path)
        print(
            f"[{i + 1}/{count}] Generated: {path}  "
            f"(id={verse['id']} {verse['surah']} {verse['ayah']})"
        )

        # --- Mark used --------------------------------------------------
        if not dry_run and verse_id is None:
            # verse_id runs are never bulk-marked as used (they are explicit
            # one-off renders, not "next in rotation").
            db.mark_used(int(verse["id"]))

    return paths


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="python -m scripts.make_post",
        description="Generate Islamic Quran image posts.",
    )
    parser.add_argument(
        "--verse-id",
        type=int,
        default=None,
        metavar="N",
        help="Target a specific verse id (bypasses random selection).",
    )
    parser.add_argument(
        "--theme",
        type=str,
        default=None,
        metavar="T",
        help="Filter random selection to verses with this theme.",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=1,
        metavar="N",
        help="Number of posts to generate (default: 1).",
    )
    parser.add_argument(
        "--output-name",
        type=str,
        default=None,
        metavar="NAME",
        help="Base filename for output PNGs.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Do not mark verses as used after generation.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)

    if args.count < 1:
        print("[ERROR] --count must be >= 1.", file=sys.stderr)
        sys.exit(1)

    if args.verse_id is not None and args.theme is not None:
        print(
            "[ERROR] --verse-id and --theme are mutually exclusive.",
            file=sys.stderr,
        )
        sys.exit(1)

    if args.dry_run:
        print("[DRY-RUN] used_verses.txt will NOT be updated.")

    paths = run(
        verse_id=args.verse_id,
        theme=args.theme,
        count=args.count,
        output_name=args.output_name,
        dry_run=args.dry_run,
    )

    print(f"\nDone. {len(paths)} image(s) written to {config.OUTPUT_DIR}")


if __name__ == "__main__":
    main()
