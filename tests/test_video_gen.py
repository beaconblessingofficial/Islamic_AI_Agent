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

def test_build_canvas(dummy_themes_path):
    gen = ReelGenerator(assets_dir="/mock", output_dir="/mock", themes_path=dummy_themes_path)
    assert gen._build_canvas("9:16") == (1080, 1920)
    assert gen._build_canvas("1:1") == (1080, 1080)
    assert gen._build_canvas("16:9") == (1920, 1080)
    with pytest.raises(ValueError):
        gen._build_canvas("4:3")

def test_apply_ken_burns(dummy_themes_path):
    from moviepy import ColorClip
    gen = ReelGenerator(assets_dir="/mock", output_dir="/mock", themes_path=dummy_themes_path)
    # Use a dummy ColorClip in place of ImageClip for testing
    dummy_clip = ColorClip(size=(1080, 1080), color=(255, 0, 0), duration=1.0)
    kb_clip = gen._apply_ken_burns(dummy_clip, duration=5.0)
    
    # Verify the returned clip has the exact specified duration
    assert kb_clip.duration == 5.0
    
def test_add_vertical_gradient_bg(dummy_themes_path):
    gen = ReelGenerator(assets_dir="/mock", output_dir="/mock", themes_path=dummy_themes_path)
    # Provide a size and a custom color
    bg_clip = gen._add_vertical_gradient_bg((1080, 1920), "#123456")
    
    # Should be a VideoClip (ColorClip with mask)
    assert bg_clip.mask is not None

def test_time_subtitles(dummy_themes_path):
    gen = ReelGenerator(assets_dir="/mock", output_dir="/mock", themes_path=dummy_themes_path)
    timings = gen._time_subtitles({}, duration=15.0)
    
    assert len(timings) == 4
    
    # check structure
    assert timings[0] == ("arabic", 0.0, 3.0)
    assert timings[1] == ("transliteration", 3.3, 5.8)
    assert timings[2] == ("translation", 6.1, 9.1)
    
    # check reference math: duration - 1.5 -> 13.5 to 15.0
    assert timings[3] == ("reference", 13.5, 15.0)

def test_render_arabic_card(dummy_themes_path):
    from PIL import ImageFont
    gen = ReelGenerator(assets_dir="/mock", output_dir="/mock", themes_path=dummy_themes_path)
    verse = {"arabic": "بِسْمِ اللَّهِ الرَّحْمَنِ الرَّحِيمِ"}
    font = ImageFont.load_default()
    
    # Render with 3.0 duration and 0.0 fadein, 0.3 fadeout
    clip = gen._render_arabic_card(verse, font, duration=3.0, fadein=0.0, fadeout=0.3)
    
    # Verify clip properties
    assert clip.duration == 3.0
    assert clip.size[0] > 0
    assert clip.size[1] > 0
    
    # FadeOut effect should be applied in clip.effects or functionally wrapped.
    # At minimum, MoviePy should not throw errors during instantiation.
