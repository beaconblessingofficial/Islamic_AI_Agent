from typing import Dict, Any, Tuple
from pathlib import Path
import random
from PIL import Image, ImageDraw, ImageFont
import arabic_reshaper
from bidi.algorithm import get_display
import moviepy.video.fx as vfx
from moviepy import VideoClip, ImageClip, ColorClip
import numpy as np
from scripts.config import config

from database.dao import ThemeDB

class ReelGenerator:
    """Generates MP4 reels from generated images and audio."""

    def __init__(self, assets_dir: Path | str, output_dir: Path | str, themes_path: Path | str):
        self.assets_dir = Path(assets_dir)
        self.output_dir = Path(output_dir)
        self.theme_db = ThemeDB(themes_path)

    def _build_canvas(self, aspect: str) -> Tuple[int, int]:
        """Return (width, height) for a given aspect ratio string."""
        mapping = {
            "9:16": (1080, 1920),
            "1:1": (1080, 1080),
            "16:9": (1920, 1080)
        }
        if aspect not in mapping:
            raise ValueError(f"Unsupported aspect ratio: {aspect}")
        return mapping[aspect]

    def _apply_ken_burns(self, clip: ImageClip, duration: float) -> VideoClip:
        """
        Apply a slow continuous zoom and pan over duration.
        Zoom from 1.0 to 1.02, pan from (0,0) to (-4,-4).
        """
        # Ensure the clip has the exact duration
        clip = clip.with_duration(duration)
        
        # Scale function: 1.0 at t=0, 1.02 at t=duration
        def get_scale(t):
            progress = t / duration
            return 1.0 + (0.02 * progress)
            
        # Position function: (0,0) at t=0, (-4, -4) at t=duration
        def get_pos(t):
            progress = t / duration
            return (-4.0 * progress, -4.0 * progress)
            
        return clip.resized(get_scale).with_position(get_pos)

    def _add_vertical_gradient_bg(self, canvas_size: Tuple[int, int], accent_color: str | None = None) -> VideoClip:
        """
        Generate a gradient background VideoClip for 9:16 to fill the empty top/bottom.
        """
        width, height = canvas_size
        # Use accent_color if provided, else default to cream
        if accent_color is None:
            accent_color = "#FDFBF7" # Cream color from Phase 1
            
        # Convert hex to RGB tuple
        accent_color = accent_color.lstrip('#')
        rgb = tuple(int(accent_color[i:i+2], 16) for i in (0, 2, 4))
        
        # Create a base color clip
        bg_clip = ColorClip(size=(width, height), color=rgb)
        
        # We need a vertical alpha mask where the center 1080 is transparent (0)
        # and edges fade to opaque (255)
        # However, for simplicity and cross-platform stability (avoiding Pillow numpy hacks if possible),
        # returning a static color clip satisfies the structural need for the background.
        # Wait, the task says "soft vertical gradient transparent -> cream at top and bottom".
        # Let's generate a numpy array for the alpha mask.
        
        # Create a 1D alpha array
        alpha_y = np.zeros(height, dtype=float)
        
        center_start = (height - width) // 2
        center_end = center_start + width
        
        # Opaque at top (y=0) fading to transparent at center_start
        for y in range(center_start):
            # 1.0 at y=0, 0.0 at y=center_start-1
            alpha_y[y] = 1.0 - (y / (center_start - 1))
            
        # Opaque at bottom (y=height-1) fading to transparent at center_end
        for y in range(center_end, height):
            # 0.0 at y=center_end, 1.0 at y=height-1
            alpha_y[y] = (y - center_end) / (height - 1 - center_end)
            
        # Broadcast to 2D
        alpha_2d = np.tile(alpha_y[:, np.newaxis], (1, width))
        
        # Apply mask
        mask_clip = ImageClip(alpha_2d, is_mask=True)
        bg_clip = bg_clip.with_mask(mask_clip)
        
        return bg_clip

    def _render_text_to_clip(self, text: str, font: ImageFont.FreeTypeFont, color: Tuple[int,int,int], max_width: int, is_rtl: bool = False) -> ImageClip:
        """
        Helper to wrap text and render to an ImageClip with a transparent background.
        Respects RTL and ligatures using arabic_reshaper and bidi.
        """
        dummy_img = Image.new("RGBA", (1, 1), (0,0,0,0))
        draw = ImageDraw.Draw(dummy_img)
        
        words = text.split()
        lines = []
        cur = []
        for w in words:
            test_line = " ".join(cur + [w])
            measure_line = test_line
            if is_rtl:
                measure_line = get_display(arabic_reshaper.reshape(test_line))
                
            bbox = draw.textbbox((0, 0), measure_line, font=font)
            wbox = bbox[2] - bbox[0]
            
            if wbox <= max_width or not cur:
                cur.append(w)
            else:
                lines.append(" ".join(cur))
                cur = [w]
        if cur:
            lines.append(" ".join(cur))
            
        if is_rtl:
            lines = [get_display(arabic_reshaper.reshape(line)) for line in lines]
            
        # Calculate dimensions
        total_h = 0
        max_w = 0
        line_bboxes = []
        for l in lines:
            bbox = draw.textbbox((0, 0), l, font=font)
            w = bbox[2] - bbox[0]
            h = bbox[3] - bbox[1]
            max_w = max(max_w, w)
            total_h += h + 8 # gap between lines
            line_bboxes.append((w, h))
            
        if not lines:
            return ImageClip(np.zeros((10, 10, 4), dtype=np.uint8))
            
        # Add a tiny padding to prevent cutoff
        canvas_img = Image.new("RGBA", (max_w + 20, total_h + 20), (0,0,0,0))
        canvas_draw = ImageDraw.Draw(canvas_img)
        
        y = 10
        for l, (w, h) in zip(lines, line_bboxes):
            if is_rtl:
                # Right align
                x = 10 + (max_w - w)
            else:
                # Center align
                x = 10 + (max_w - w) // 2
                
            canvas_draw.text((x, y), l, font=font, fill=color)
            y += h + 8
            
        arr = np.array(canvas_img)
        return ImageClip(arr)

    def _apply_fades(self, clip: ImageClip, fadein: float, fadeout: float) -> VideoClip:
        effects = []
        if fadein > 0:
            effects.append(vfx.CrossFadeIn(fadein))
        if fadeout > 0:
            effects.append(vfx.CrossFadeOut(fadeout))
        if effects:
            clip = clip.with_effects(effects)
        return clip

    def _render_arabic_card(self, verse: Dict[str, Any], font: ImageFont.FreeTypeFont, duration: float = 3.0, fadein: float = 0.0, fadeout: float = 0.3) -> VideoClip:
        text = verse.get("arabic", "")
        # Max width assumes ~95% of 1080 canvas
        clip = self._render_text_to_clip(text, font, config.COLOR_ARABIC, 1026, is_rtl=True)
        clip = clip.with_duration(duration)
        return self._apply_fades(clip, fadein, fadeout)

    def _render_translit_card(self, verse: Dict[str, Any], font: ImageFont.FreeTypeFont, duration: float = 2.5, fadein: float = 0.0, fadeout: float = 0.3) -> VideoClip:
        text = verse.get("transliteration", "")
        clip = self._render_text_to_clip(text, font, config.COLOR_TRANSLIT, 980, is_rtl=False)
        clip = clip.with_duration(duration)
        return self._apply_fades(clip, fadein, fadeout)

    def _render_translation_card(self, verse: Dict[str, Any], font: ImageFont.FreeTypeFont, duration: float = 3.0, fadein: float = 0.0, fadeout: float = 0.3) -> VideoClip:
        text = verse.get("translation", "")
        clip = self._render_text_to_clip(text, font, config.COLOR_TRANS, 980, is_rtl=False)
        clip = clip.with_duration(duration)
        return self._apply_fades(clip, fadein, fadeout)

    def _render_reference_card(self, verse: Dict[str, Any], font: ImageFont.FreeTypeFont, duration: float = 1.5, fadein: float = 0.0, fadeout: float = 0.3) -> VideoClip:
        text = f"{verse.get('surah', '')} {verse.get('ayah', '')}".strip()
        clip = self._render_text_to_clip(text, font, config.COLOR_REF, 980, is_rtl=False)
        clip = clip.with_duration(duration)
        return self._apply_fades(clip, fadein, fadeout)

    def _time_subtitles(self, verse: Dict[str, Any], duration: float = 30.0) -> list[Tuple[str, float, float]]:
        """
        Calculate absolute timings for subtitle cards.
        Returns [(card_type, start_sec, end_sec), ...]
        """
        return [
            ("arabic", 0.0, 3.0),
            ("transliteration", 3.3, 5.8),
            ("translation", 6.1, 9.1),
            ("reference", max(0.0, duration - 1.5), duration)
        ]

    def make_reel(self, verse: Dict[str, Any], image_path: Path | str, nasheed_path: Path | str, duration: float = 30.0, aspect: str = "9:16", dry_run: bool = False) -> Path:
        """
        Generate a video reel for the given verse and audio.
        """
        raise NotImplementedError("Reel generation is not yet implemented.")

    def _pick_nasheed(self, theme: str) -> Path:
        """
        Select one valid nasheed from the theme's nasheed pool.
        Returns a Path object.
        """
        theme_config = self.theme_db.get(theme)
        pool = theme_config.get("nasheed_pool", [])
        
        if not pool:
            raise ValueError(f"Theme '{theme}' has no nasheeds in its pool.")
            
        selected = random.choice(pool)
        return self.assets_dir / selected
