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

def test_make_reel_dry_run(dummy_themes_path, tmp_path):
    from unittest.mock import patch, MagicMock
    gen = ReelGenerator(assets_dir="/mock", output_dir=tmp_path, themes_path=dummy_themes_path)
    
    with patch("scripts.video_gen.ImageClip") as mock_imageclip, \
         patch.object(gen, "_build_canvas", return_value=(1080, 1920)) as mock_canvas, \
         patch.object(gen, "_apply_ken_burns") as mock_kb, \
         patch.object(gen, "_add_vertical_gradient_bg") as mock_grad, \
         patch("scripts.video_gen.CompositeVideoClip") as mock_comp_bg, \
         patch.object(gen, "_time_subtitles", return_value=[]) as mock_time, \
         patch.object(gen, "_compose_cards") as mock_compose, \
         patch.object(gen, "_attach_audio") as mock_audio, \
         patch.object(gen, "_normalize_audio") as mock_norm, \
         patch.object(gen, "_export", return_value=Path("out.mp4")) as mock_export, \
         patch("PIL.Image.open") as mock_img_open:
        
        # Setup mock image to prevent ImageClip crash
        mock_img_open.return_value.convert.return_value = MagicMock()

        verse = {"id": 123}
        out = gen.make_reel(verse, "dummy.png", "dummy.mp3", duration=10.0, aspect="9:16", dry_run=True)
        
        # Verify orchestration
        mock_canvas.assert_called_once_with("9:16")
        mock_kb.assert_called_once()
        mock_grad.assert_called_once()
        mock_comp_bg.assert_called_once()
        mock_time.assert_called_once_with(verse, 10.0)
        mock_compose.assert_called_once()
        mock_audio.assert_called_once()
        mock_norm.assert_called_once()
        
        # Verify dry_run routing
        export_path = mock_export.call_args[0][1]
        assert "pending" in export_path.parts
        assert export_path.name == "reel_123.mp4"

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

def test_compose_cards(dummy_themes_path):
    from moviepy import ColorClip
    gen = ReelGenerator(assets_dir="/mock", output_dir="/mock", themes_path=dummy_themes_path)
    bg = ColorClip((100, 100), color=(0,0,0), duration=10)
    
    c1 = ColorClip((50, 50), color=(255,0,0), duration=2)
    c2 = ColorClip((50, 50), color=(0,255,0), duration=2)
    
    cards = [
        (c1, 0.0, 2.0),
        (c2, 2.0, 4.0)
    ]
    
    comp = gen._compose_cards(cards, (100, 100), bg)
    
    assert comp.duration == 10.0
    assert comp.size == (100, 100)
    
def test_normalize_audio(dummy_themes_path):
    from moviepy import ColorClip
    from moviepy import AudioArrayClip
    import numpy as np
    gen = ReelGenerator(assets_dir="/mock", output_dir="/mock", themes_path=dummy_themes_path)
    
    # Create a 1-second audio array (44100 Hz)
    audio_arr = np.random.uniform(-1, 1, (44100, 2))
    audio_clip = AudioArrayClip(audio_arr, fps=44100)
    
    video = ColorClip((100, 100), color=(0,0,0), duration=1)
    video = video.with_audio(audio_clip)
    
    norm_video = gen._normalize_audio(video)
    assert norm_video.audio is not None

# --- Smoke tests for Phase 2.9.1 ---

def test_make_reel_produces_mp4(dummy_themes_path, tmp_path):
    """Verifies MoviePy export is configured to use H.264, yuv420p, and faststart."""
    from unittest.mock import patch, MagicMock
    gen = ReelGenerator(assets_dir="/mock", output_dir=tmp_path, themes_path=dummy_themes_path)
    
    with patch("scripts.video_gen.ImageClip"), \
         patch.object(gen, "_build_canvas", return_value=(1080, 1920)), \
         patch.object(gen, "_apply_ken_burns"), \
         patch.object(gen, "_add_vertical_gradient_bg"), \
         patch("scripts.video_gen.CompositeVideoClip"), \
         patch.object(gen, "_time_subtitles", return_value=[]), \
         patch.object(gen, "_compose_cards"), \
         patch.object(gen, "_attach_audio"), \
         patch.object(gen, "_normalize_audio") as mock_norm, \
         patch("PIL.Image.open") as mock_img_open:
        
        mock_img_open.return_value.convert.return_value = MagicMock()
        mock_video = MagicMock()
        mock_norm.return_value = mock_video
        
        out = gen.make_reel({"id": 123}, "dummy.png", "dummy.mp3", duration=30.0, aspect="9:16", dry_run=False)
        
        mock_video.write_videofile.assert_called_once()
        kwargs = mock_video.write_videofile.call_args[1]
        assert kwargs.get("codec") == "libx264"
        assert kwargs.get("preset") == "medium"
        assert "yuv420p" in kwargs.get("ffmpeg_params", [])
        assert "+faststart" in kwargs.get("ffmpeg_params", [])

def test_aspect_9_16(dummy_themes_path):
    """dimensions are 1080x1920."""
    gen = ReelGenerator(assets_dir="/mock", output_dir="/mock", themes_path=dummy_themes_path)
    assert gen._build_canvas("9:16") == (1080, 1920)

def test_aspect_1_1(dummy_themes_path):
    """dimensions are 1080x1080."""
    gen = ReelGenerator(assets_dir="/mock", output_dir="/mock", themes_path=dummy_themes_path)
    assert gen._build_canvas("1:1") == (1080, 1080)

def test_file_size_under_30mb_for_30s(dummy_themes_path, tmp_path):
    """Verifies export bitrate configuration is consistent with the target file size."""
    from unittest.mock import patch, MagicMock
    gen = ReelGenerator(assets_dir="/mock", output_dir=tmp_path, themes_path=dummy_themes_path)
    
    with patch("scripts.video_gen.ImageClip"), \
         patch.object(gen, "_build_canvas", return_value=(1080, 1920)), \
         patch.object(gen, "_apply_ken_burns"), \
         patch.object(gen, "_add_vertical_gradient_bg"), \
         patch("scripts.video_gen.CompositeVideoClip"), \
         patch.object(gen, "_time_subtitles", return_value=[]), \
         patch.object(gen, "_compose_cards"), \
         patch.object(gen, "_attach_audio"), \
         patch.object(gen, "_normalize_audio") as mock_norm, \
         patch("PIL.Image.open") as mock_img_open:
         
        mock_img_open.return_value.convert.return_value = MagicMock()
        mock_video = MagicMock()
        mock_norm.return_value = mock_video
        
        out = gen.make_reel({"id": 123}, "dummy.png", "dummy.mp3", duration=30.0, aspect="9:16", dry_run=False)
        
        kwargs = mock_video.write_videofile.call_args[1]
        assert kwargs.get("bitrate") == "5000k"
        assert kwargs.get("audio_bitrate") == "192k"

def test_nasheed_picked_from_theme(dummy_themes_path):
    """nasheed is in the theme's pool."""
    gen = ReelGenerator(assets_dir="/mock", output_dir="/mock", themes_path=dummy_themes_path)
    picked = gen._pick_nasheed("Guidance")
    assert picked.name in ["track1.mp3", "track2.mp3"]

def test_dry_run_writes_to_pending(dummy_themes_path, tmp_path):
    """output path is under output/pending/."""
    from unittest.mock import patch, MagicMock
    gen = ReelGenerator(assets_dir="/mock", output_dir=tmp_path, themes_path=dummy_themes_path)
    
    with patch("scripts.video_gen.ImageClip"), \
         patch.object(gen, "_build_canvas", return_value=(1080, 1920)), \
         patch.object(gen, "_apply_ken_burns"), \
         patch.object(gen, "_add_vertical_gradient_bg"), \
         patch("scripts.video_gen.CompositeVideoClip"), \
         patch.object(gen, "_time_subtitles", return_value=[]), \
         patch.object(gen, "_compose_cards"), \
         patch.object(gen, "_attach_audio"), \
         patch.object(gen, "_normalize_audio") as mock_norm, \
         patch("PIL.Image.open") as mock_img_open:
         
        mock_img_open.return_value.convert.return_value = MagicMock()
        mock_video = MagicMock()
        mock_norm.return_value = mock_video
        
        out_path = gen.make_reel({"id": 123}, "dummy.png", "dummy.mp3", duration=10.0, aspect="9:16", dry_run=True)
        assert "pending" in out_path.parts

