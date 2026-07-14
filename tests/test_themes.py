import pytest
import json
import re
from pathlib import Path
from database.dao import ThemeDB
from scripts.config import config

THEMES_PATH = config.THEMES_PATH

@pytest.fixture
def theme_db():
    return ThemeDB(THEMES_PATH)

def test_themes_json_loads(theme_db):
    """Test that all 21 themes are present."""
    themes = theme_db.names()
    assert len(themes) == 21
    expected_themes = [
        'Acceptance', 'Balance', 'Communication', 'Ease', 'Facilitation',
        'Faith', 'Family', 'Forgiveness', 'Guidance', 'Knowledge', 'Mercy',
        'Need', 'Patience', 'Power', 'Prayer', 'Reflection', 'Repentance',
        'Steadfastness', 'Submission', 'Trust', 'Understanding'
    ]
    for theme in expected_themes:
        assert theme in themes

def test_each_theme_has_required_fields(theme_db):
    """Test that each entry is complete."""
    for theme in theme_db.names():
        details = theme_db.get(theme)
        assert "caption_prompt" in details
        assert "hashtags" in details
        assert isinstance(details["hashtags"], list)
        assert "accent_color" in details
        assert "nasheed_pool" in details
        assert isinstance(details["nasheed_pool"], list)

def test_accent_colors_are_valid_hex(theme_db):
    """Test valid CSS hex input."""
    for theme in theme_db.names():
        color = theme_db.get(theme)["accent_color"]
        assert re.match(r"^#[0-9A-Fa-f]{6}$", color)

def test_nasheed_pool_references_known_files(theme_db):
    """Test that each entry references only the known files."""
    known_files = {"calm_01.mp3", "calm_02.mp3", "emotional_01.mp3", "emotional_02.mp3"}
    for theme in theme_db.names():
        pool = theme_db.get(theme)["nasheed_pool"]
        for nasheed in pool:
            assert nasheed in known_files

def test_themedb_get_raises_for_unknown_theme(theme_db):
    """Test ThemeDB error handling."""
    with pytest.raises(KeyError):
        theme_db.get("NonExistent")
