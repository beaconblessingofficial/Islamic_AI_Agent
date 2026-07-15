import pytest
import json
from pathlib import Path
from scripts.video_gen import ReelGenerator

@pytest.fixture
def dummy_themes_path(tmp_path):
    themes_file = tmp_path / "dummy_themes.json"
    data = {
        "Guidance": {
            "accent_color": "#FF0000",
            "nasheed_pool": ["audio/track1.mp3", "audio/track2.mp3"]
        },
        "EmptyTheme": {
            "accent_color": "#00FF00",
            "nasheed_pool": []
        },
        "MissingPool": {
            "accent_color": "#0000FF"
        }
    }
    themes_file.write_text(json.dumps(data))
    return themes_file

def test_pick_nasheed_success(dummy_themes_path):
    """Test that a nasheed is picked successfully from the pool."""
    gen = ReelGenerator(assets_dir="/mock/assets", output_dir="/mock/out", themes_path=dummy_themes_path)
    picked = gen._pick_nasheed("Guidance")
    assert isinstance(picked, Path)
    # The picked path should be relative to assets_dir
    assert str(picked) in [str(Path("/mock/assets/audio/track1.mp3")), str(Path("/mock/assets/audio/track2.mp3"))]

def test_pick_nasheed_empty_pool(dummy_themes_path):
    """Test that picking a nasheed raises ValueError if pool is empty."""
    gen = ReelGenerator(assets_dir="/mock/assets", output_dir="/mock/out", themes_path=dummy_themes_path)
    
    with pytest.raises(ValueError, match="has no nasheeds in its pool"):
        gen._pick_nasheed("EmptyTheme")
        
    with pytest.raises(ValueError, match="has no nasheeds in its pool"):
        gen._pick_nasheed("MissingPool")

def test_make_reel_not_implemented(dummy_themes_path):
    """Test that make_reel raises NotImplementedError."""
    gen = ReelGenerator(assets_dir="/mock/assets", output_dir="/mock/out", themes_path=dummy_themes_path)
    
    with pytest.raises(NotImplementedError, match="Reel generation is not yet implemented"):
        gen.make_reel(verse={}, image_path="img.png", nasheed_path="audio.mp3")

