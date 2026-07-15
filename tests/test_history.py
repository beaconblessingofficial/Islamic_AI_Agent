import pytest
import sqlite3
import json
from pathlib import Path
from database import history

@pytest.fixture
def clean_db(monkeypatch, tmp_path):
    """Fixture to provide a clean, temporary database for testing."""
    # Use a temporary file for the database
    db_path = tmp_path / "test_history.sqlite"
    # Ensure schema.sql can be found relative to the project root
    schema_path = Path("database/schema.sql")
    
    # Patch the paths in the history module
    monkeypatch.setattr(history, "DB_PATH", db_path)
    monkeypatch.setattr(history, "SCHEMA_PATH", schema_path)
    
    # Initialize the schema
    history.init_db()
    
    yield db_path
    
    # Cleanup is handled by pytest's tmp_path

def test_init_db(clean_db):
    """Test that init_db creates the database and tables."""
    assert clean_db.exists()
    conn = sqlite3.connect(clean_db)
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = {row[0] for row in cursor.fetchall()}
    assert "posts" in tables
    assert "post_platforms" in tables
    assert "nasheed_history" in tables
    assert "runs" in tables
    conn.close()

def test_log_post(clean_db):
    """Test inserting a new post."""
    post = history.log_post(verse_id=10, theme="Guidance", image_path="out/img1.png")
    assert post["post_id"] == 1
    assert post["verse_id"] == 10
    assert post["theme"] == "Guidance"
    assert post["image_path"] == "out/img1.png"
    assert post["status"] == "pending"
    assert post["created_at"] is not None

def test_mark_published(clean_db):
    """Test marking a post as published."""
    post = history.log_post(verse_id=1, theme="Patience", image_path="out/img2.png")
    
    platform_post = history.mark_published(
        post_id=post["post_id"],
        platform="instagram",
        platform_post_id="ig_12345",
        platform_url="https://ig.com/p/123"
    )
    
    assert platform_post["id"] == 1
    assert platform_post["post_id"] == post["post_id"]
    assert platform_post["platform"] == "instagram"
    assert platform_post["platform_post_id"] == "ig_12345"
    assert platform_post["published_at"] is not None

    # Check that the post status was updated
    conn = sqlite3.connect(clean_db)
    conn.row_factory = sqlite3.Row
    updated_post = conn.execute("SELECT status, published_at FROM posts WHERE post_id=?", (post["post_id"],)).fetchone()
    conn.close()
    
    assert updated_post["status"] == "published"
    assert updated_post["published_at"] is not None

def test_update_engagement_round_trip(clean_db):
    """Test that engagement JSON can be updated and retrieved."""
    post = history.log_post(verse_id=1, theme="Patience", image_path="out.png")
    plat_post = history.mark_published(post["post_id"], "youtube", "yt_1", "http://yt")
    
    engagement_data = {"likes": 150, "views": 1000, "comments": 12}
    updated = history.update_engagement(plat_post["id"], engagement_data)
    
    assert updated["engagement_json"] is not None
    loaded_data = json.loads(updated["engagement_json"])
    assert loaded_data["likes"] == 150
    assert loaded_data["views"] == 1000
    assert updated["last_polled_at"] is not None

def test_list_recent(clean_db):
    """Test listing recent posts ordered by created_at."""
    history.log_post(1, "A", "1.png")
    history.log_post(2, "B", "2.png")
    history.log_post(3, "C", "3.png")
    
    recent = history.list_recent(2)
    assert len(recent) == 2
    assert recent[0]["verse_id"] == 3
    assert recent[1]["verse_id"] == 2

def test_nasheed_usage(clean_db):
    """Test recording and querying nasheed usage."""
    history.record_nasheed_use("track1.mp3", post_id=1)
    history.record_nasheed_use("track2.mp3", post_id=2)
    
    # Query within the last 7 days
    recent_nasheeds = history.get_nasheed_recently_used(days=7)
    assert len(recent_nasheeds) == 2
    assert "track1.mp3" in recent_nasheeds
    assert "track2.mp3" in recent_nasheeds
    
    # Query within 0 days (cutoff is now, but the inserts happened microsecs ago, 
    # it might still match depending on exact timing, but let's query a negative time to ensure no match)
    # Actually just querying -1 days ensures cutoff is in the future
    empty = history.get_nasheed_recently_used(days=-1)
    assert empty == []
