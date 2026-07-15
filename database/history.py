import sqlite3
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

DB_PATH = Path("database/post_history.sqlite")
SCHEMA_PATH = Path("database/schema.sql")

def _get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, timeout=10.0)
    conn.row_factory = sqlite3.Row
    return conn

def init_db() -> None:
    """Initialize the SQLite database with the schema."""
    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(f"Schema file not found at {SCHEMA_PATH}")
    
    with _get_connection() as conn:
        conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))

def log_post(verse_id: int, theme: str, image_path: str) -> Dict[str, Any]:
    """Log a newly generated static post to the database."""
    with _get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO posts (verse_id, theme, image_path, status) VALUES (?, ?, ?, 'pending')",
            (verse_id, theme, image_path)
        )
        post_id = cursor.lastrowid
        row = conn.execute("SELECT * FROM posts WHERE post_id = ?", (post_id,)).fetchone()
        return dict(row)

def mark_published(post_id: int, platform: str, platform_post_id: str, platform_url: str) -> Dict[str, Any]:
    """Mark a post as published on a specific platform."""
    with _get_connection() as conn:
        # Insert into post_platforms
        cursor = conn.execute(
            """INSERT INTO post_platforms (post_id, platform, platform_post_id, platform_url)
               VALUES (?, ?, ?, ?)""",
            (post_id, platform, platform_post_id, platform_url)
        )
        pp_id = cursor.lastrowid
        
        # Update posts status if it was just pending
        conn.execute(
            "UPDATE posts SET status = 'published', published_at = CURRENT_TIMESTAMP WHERE post_id = ?",
            (post_id,)
        )
        
        row = conn.execute("SELECT * FROM post_platforms WHERE id = ?", (pp_id,)).fetchone()
        return dict(row)

def update_engagement(platform_id: int, engagement_data: Dict[str, Any]) -> Dict[str, Any]:
    """Update the engagement JSON for a specific published post on a platform."""
    with _get_connection() as conn:
        engagement_json = json.dumps(engagement_data)
        conn.execute(
            "UPDATE post_platforms SET engagement_json = ?, last_polled_at = CURRENT_TIMESTAMP WHERE id = ?",
            (engagement_json, platform_id)
        )
        row = conn.execute("SELECT * FROM post_platforms WHERE id = ?", (platform_id,)).fetchone()
        if not row:
            raise ValueError(f"Platform record {platform_id} not found.")
        return dict(row)

def list_recent(n: int) -> List[Dict[str, Any]]:
    """List the N most recently created posts."""
    with _get_connection() as conn:
        cursor = conn.execute("SELECT * FROM posts ORDER BY created_at DESC, post_id DESC LIMIT ?", (n,))
        return [dict(row) for row in cursor.fetchall()]

def record_nasheed_use(nasheed_file: str, post_id: Optional[int] = None) -> Dict[str, Any]:
    """Record that a nasheed was used."""
    with _get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO nasheed_history (nasheed_file, post_id) VALUES (?, ?)",
            (nasheed_file, post_id)
        )
        row_id = cursor.lastrowid
        row = conn.execute("SELECT * FROM nasheed_history WHERE id = ?", (row_id,)).fetchone()
        return dict(row)

def get_nasheed_recently_used(days: int) -> List[str]:
    """Get a list of nasheed filenames used in the last `days` days."""
    from datetime import timezone
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    cutoff_str = cutoff.strftime("%Y-%m-%d %H:%M:%S")
    with _get_connection() as conn:
        cursor = conn.execute(
            "SELECT DISTINCT nasheed_file FROM nasheed_history WHERE used_at >= ?",
            (cutoff_str,)
        )
        return [row["nasheed_file"] for row in cursor.fetchall()]
