from typing import Dict, Any, Tuple
from pathlib import Path
import random
from moviepy import VideoClip, ImageClip, ColorClip
import numpy as np

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
