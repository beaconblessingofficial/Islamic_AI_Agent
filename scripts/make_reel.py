import argparse
import sys
import logging
from pathlib import Path

from scripts.config import config
from database.dao import VerseDB
from database.history import record_nasheed_use, init_db
from scripts.video_gen import ReelGenerator

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description="Generate a video reel for a Quran verse.")
    parser.add_argument("--verse-id", type=int, help="ID of the verse to process. If omitted, selects a random unused verse.")
    parser.add_argument("--duration", type=float, default=30.0, help="Duration of the reel in seconds.")
    parser.add_argument("--aspect", type=str, default="9:16", help="Aspect ratio (e.g., 9:16 or 1:1).")
    parser.add_argument("--theme", type=str, help="Override the theme for the verse.")
    parser.add_argument("--dry-run", action="store_true", help="Run without writing to the final output folder (uses pending/).")
    
    args = parser.parse_args()

    logger.info("Initializing database and generators...")
    init_db()
    dao = VerseDB(config.CSV_PATH, config.USED_VERSES_PATH)
    
    # Select Verse
    if args.verse_id is not None:
        verse = dao.select_by_id(args.verse_id)
        if verse is None:
            logger.error(f"Verse ID {args.verse_id} not found in database.")
            sys.exit(1)
    else:
        verse = dao.select_random(theme=args.theme, dry_run=args.dry_run)
        if verse is None:
            logger.error("No unused verses found. Consider resetting used verses.")
            sys.exit(1)

    # Determine Theme
    theme = args.theme if args.theme else verse.get("theme")
    if not theme:
        logger.error(f"No theme specified or found for verse {verse.get('id')}.")
        sys.exit(1)

    logger.info(f"Selected Verse: ID={verse.get('id')}, Theme='{theme}'")

    gen = ReelGenerator(
        assets_dir=config.ASSETS_DIR,
        output_dir=config.OUTPUT_DIR,
        themes_path=config.THEMES_PATH
    )

    # Select Nasheed
    try:
        nasheed_path = gen._pick_nasheed(theme)
        logger.info(f"Selected Nasheed: {nasheed_path.name}")
    except ValueError as e:
        logger.error(f"Nasheed selection failed: {e}")
        sys.exit(1)

    # Select Background
    bg_image = config.BACKGROUND_IMAGE
    if not bg_image.exists():
        logger.error(f"Background image not found at {bg_image}")
        sys.exit(1)

    # Generate Reel
    logger.info(f"Starting generation (duration={args.duration}s, aspect={args.aspect}, dry_run={args.dry_run})...")
    try:
        out_path = gen.make_reel(
            verse=verse,
            image_path=bg_image,
            nasheed_path=nasheed_path,
            duration=args.duration,
            aspect=args.aspect,
            dry_run=args.dry_run
        )
        logger.info(f"Successfully generated reel at: {out_path}")
    except Exception as e:
        logger.error(f"Failed to generate reel: {e}", exc_info=True)
        sys.exit(1)

    # Record History
    try:
        record_nasheed_use(nasheed_file=nasheed_path.name, post_id=None)
        logger.info("Logged nasheed usage to history.")
    except Exception as e:
        logger.error(f"Failed to record nasheed history: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
