from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import zipfile
import time
from typing import Optional, Dict
import arabic_reshaper
from bidi.algorithm import get_display


class ImageGenerator:
    WIDTH = 1080
    HEIGHT = 1080

    def __init__(self, assets_dir: Path, output_dir: Path):
        self.assets_dir = Path(assets_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # fonts
        default_ar = self.assets_dir.parent / "fonts" / "_extracted_fonts" / "Amiri-Regular.ttf"
        self.ar_font_path = self._resolve_font_path(default_ar)
        if not self.ar_font_path.exists():
            raise FileNotFoundError(f"Arabic font not found at {self.ar_font_path}")
        self.en_font_path = self._resolve_font_path(self.assets_dir.parent / "fonts" / "PlayfairDisplay-Regular.ttf")

        # templates
        self.background_path = self.assets_dir / "background.jpg"
        self.logo_path = self.assets_dir / "logo.png"
        self.separator_path = self.assets_dir / "separator.png"

    def _resolve_font_path(self, path: Path) -> Path:
        # Some font files may actually be zipped archives (header PK..). If so, extract the first TTF/OTF inside.
        path = Path(path)
        try:
            with open(path, 'rb') as fh:
                header = fh.read(4)
                if header == b'PK\x03\x04':
                    # it's a zip; extract first .ttf or .otf
                    z = zipfile.ZipFile(path)
                    available = [name for name in z.namelist() if name.lower().endswith(('.ttf', '.otf'))]
                    preferred = None
                    for name in available:
                        name_l = name.lower()
                        if 'quran' in name_l and 'colored' not in name_l:
                            preferred = name
                            break
                    if preferred is None:
                        for name in available:
                            if 'amiri-regular.ttf' in name.lower() or 'amiri.ttf' in name.lower():
                                preferred = name
                                break
                    if preferred is None and available:
                        preferred = available[0]
                    if preferred:
                        out_dir = path.parent / "_extracted_fonts"
                        out_dir.mkdir(exist_ok=True)
                        out_path = out_dir / Path(preferred).name
                        if not out_path.exists():
                            with z.open(preferred) as inf, open(out_path, 'wb') as outf:
                                outf.write(inf.read())
                        return out_path
        except Exception:
            pass
        return path

    def _font_fallback_paths(self):
        return [
            Path("C:/Windows/Fonts/arial.ttf"),
            Path("C:/Windows/Fonts/arabtype.ttf"),
            Path("C:/Windows/Fonts/tahoma.ttf"),
            Path("C:/Windows/Fonts/segeo.ttf"),
        ]

    def _get_arabic_font_path(self) -> Path:
        # Prefer the local Quranic Amiri font package, then fallback to Windows Arabic-capable fonts.
        local_arabi = self.assets_dir.parent / "fonts" / "Amiri-Regular.ttf"
        if local_arabi.exists():
            try:
                return self._resolve_font_path(local_arabi)
            except Exception:
                pass

        windows_candidates = [
            Path("C:/Windows/Fonts/arabtype.ttf"),
            Path("C:/Windows/Fonts/tahoma.ttf"),
            Path("C:/Windows/Fonts/arial.ttf"),
        ]
        for candidate in windows_candidates:
            if candidate.exists():
                try:
                    ImageFont.truetype(str(candidate), 72)
                    return candidate
                except Exception:
                    continue

        raise FileNotFoundError("No usable Arabic font found. Install Amiri or an Arabic-capable Windows font.")

    def _load_font(self, path: Path, size: int) -> ImageFont.FreeTypeFont:
        try:
            return ImageFont.truetype(str(path), size)
        except Exception:
            for fallback in self._font_fallback_paths():
                if fallback.exists():
                    try:
                        return ImageFont.truetype(str(fallback), size)
                    except Exception:
                        continue
        raise

    def _wrap_text(self, draw: ImageDraw.Draw, text: str, font: ImageFont.FreeTypeFont, max_width: int, is_rtl=False):
        words = text.split()
        lines = []
        cur = []
        for w in words:
            test_line = " ".join(cur + [w])
            
            # Reshape RTL text BEFORE measuring to get true ligature widths
            measure_line = test_line
            if is_rtl:
                measure_line = get_display(arabic_reshaper.reshape(test_line))
                
            # measure
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
            # Arabic words should be reshaped and reversed for PIL rendering
            lines = [get_display(arabic_reshaper.reshape(line)) for line in lines]

        return lines

    def generate_post(self, verse: Dict[str, str], output_name: Optional[str] = None) -> Path:
        # Prepare canvas
        img = Image.new("RGB", (self.WIDTH, self.HEIGHT), color=(245, 244, 240))
        draw = ImageDraw.Draw(img)

        # background
        if self.background_path.exists():
            bg = Image.open(self.background_path).convert("RGB").resize((self.WIDTH, self.HEIGHT))
            img = Image.blend(bg, img, alpha=0.35)
            draw = ImageDraw.Draw(img)

        margin_x = 80
        content_width = self.WIDTH - margin_x * 2

        # Load logo and separator if available
        logo = None
        if self.logo_path.exists():
            logo = Image.open(self.logo_path).convert("RGBA")
            max_logo_w = int(self.WIDTH * 0.25)
            max_logo_h = int(self.HEIGHT * 0.12)
            logo.thumbnail((max_logo_w, max_logo_h), Image.LANCZOS)

        separator = None
        if self.separator_path.exists():
            separator = Image.open(self.separator_path).convert("RGBA")
            max_sep_w = content_width
            max_sep_h = int(self.HEIGHT * 0.08)
            separator.thumbnail((max_sep_w, max_sep_h), Image.LANCZOS)
            if separator.width > max_sep_w or separator.height > max_sep_h:
                separator = separator.resize((min(separator.width, max_sep_w), min(separator.height, max_sep_h)), Image.LANCZOS)
            if separator.height < 4 or separator.width < 20:
                separator = None

        # Fonts baseline sizes
        ar_size = 72
        trans_size = 30
        tri_size = 36
        ref_size = 22

        # load fonts
        ar_font = self._load_font(self.ar_font_path, ar_size)
        trans_font = self._load_font(self.en_font_path, trans_size)
        tri_font = self._load_font(self.en_font_path, tri_size)
        ref_font = self._load_font(self.en_font_path, ref_size)

        # Prepare text
        arabic = verse.get("arabic", "")
        translit = verse.get("transliteration", "")
        translation = verse.get("translation", "")
        reference = f"{verse.get('surah','')} {verse.get('ayah','')}"

        # Dynamic sizing loop: reduce arabic font until fits vertically
        for attempt in range(12):
            ar_font = self._load_font(self.ar_font_path, ar_size)
            tri_font = self._load_font(self.en_font_path, tri_size)
            trans_font = self._load_font(self.en_font_path, trans_size)
            ref_font = self._load_font(self.en_font_path, ref_size)

            # wrap lines
            ar_lines = self._wrap_text(draw, arabic, ar_font, int(content_width * 0.95), is_rtl=True)
            tri_lines = self._wrap_text(draw, translit, tri_font, content_width)
            trans_lines = self._wrap_text(draw, translation, trans_font, content_width)

            # compute total height
            total_h = 0
            gaps = 20
            if logo:
                total_h += logo.height + gaps
            # arabic block
            for l in ar_lines:
                bbox = draw.textbbox((0, 0), l, font=ar_font)
                total_h += bbox[3] - bbox[1] + 8
            total_h += gaps
            # transliteration
            for l in tri_lines:
                bbox = draw.textbbox((0, 0), l, font=tri_font)
                total_h += bbox[3] - bbox[1] + 6
            total_h += gaps
            # separator
            if separator:
                total_h += separator.height + gaps
            # translation
            for l in trans_lines:
                bbox = draw.textbbox((0, 0), l, font=trans_font)
                total_h += bbox[3] - bbox[1] + 6
            total_h += gaps
            if separator:
                total_h += separator.height + gaps
            # reference
            bbox = draw.textbbox((0, 0), reference, font=ref_font)
            total_h += bbox[3] - bbox[1]

            if total_h <= self.HEIGHT - 160:
                break
            # else reduce sizes
            ar_size = max(28, int(ar_size * 0.9))
            tri_size = max(14, int(tri_size * 0.95))
            trans_size = max(12, int(trans_size * 0.95))
            ref_size = max(10, int(ref_size * 0.95))

        # Start drawing from vertical center to balance
        y = (self.HEIGHT - total_h) // 2

        # logo
        if logo:
            x = (self.WIDTH - logo.width) // 2
            img.paste(logo, (x, y), logo)
            y += logo.height + gaps

        # Arabic
        for l in ar_lines:
            bbox = draw.textbbox((0, 0), l, font=ar_font)
            w = bbox[2] - bbox[0]
            x = (self.WIDTH - w) // 2
            draw.text((x, y), l, font=ar_font, fill=(10, 10, 10))
            y += bbox[3] - bbox[1] + 8

        y += gaps
        # transliteration
        for l in tri_lines:
            bbox = draw.textbbox((0, 0), l, font=tri_font)
            w = bbox[2] - bbox[0]
            x = (self.WIDTH - w) // 2
            draw.text((x, y), l, font=tri_font, fill=(40, 40, 40))
            y += bbox[3] - bbox[1] + 6

        y += gaps
        if separator:
            x = (self.WIDTH - separator.width) // 2
            img.paste(separator, (x, y), separator)
            y += separator.height + gaps

        # translation
        for l in trans_lines:
            bbox = draw.textbbox((0, 0), l, font=trans_font)
            w = bbox[2] - bbox[0]
            x = (self.WIDTH - w) // 2
            draw.text((x, y), l, font=trans_font, fill=(30, 30, 30))
            y += bbox[3] - bbox[1] + 6

        y += gaps
        if separator:
            x = (self.WIDTH - separator.width) // 2
            img.paste(separator, (x, y), separator)
            y += separator.height + gaps

        # reference
        bbox = draw.textbbox((0, 0), reference, font=ref_font)
        w = bbox[2] - bbox[0]
        x = (self.WIDTH - w) // 2
        draw.text((x, y), reference, font=ref_font, fill=(90, 90, 90))

        # save
        ts = int(time.time() * 1000)
        out_name = output_name or f"post_{ts}.png"
        out_path = self.output_dir / out_name
        img.save(out_path, format="PNG")
        return out_path


if __name__ == '__main__':
    import sys
    BASE = Path(__file__).resolve().parent.parent
    assets = BASE / "templates"
    out = BASE / "output"
    gen = ImageGenerator(assets, out)
    # quick smoke test: use first verse from CSV
    from scripts.verse_db import VerseDB
    db = VerseDB(BASE / "database" / "quran_posts.csv", BASE / "database" / "used_verses.txt")
    v = db.select_random()
    p = gen.generate_post(v)
    print("Generated:", p)
