from pathlib import Path
import random
from typing import Dict, Any

from database.dao import ThemeDB

class ReelGenerator:
    """Generates MP4 reels from generated images and audio."""

    def __init__(self, assets_dir: Path | str, output_dir: Path | str, themes_path: Path | str):
        self.assets_dir = Path(assets_dir)
        self.output_dir = Path(output_dir)
        self.theme_db = ThemeDB(themes_path)

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
        
        # Assume nasheeds are stored in the assets directory under 'audio'
        # Or just return the path relative to assets_dir if the pool specifies it.
        # But for now, we just return Path(selected) based on the simplest implementation.
        # Wait, the prompt says "Keep the implementation easy to extend in later phases."
        # If the pool contains strings like "audio/nasheed1.mp3", then:
        return self.assets_dir / selected
