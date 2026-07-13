from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import arabic_reshaper
from bidi.algorithm import get_display

BASE_DIR = Path(__file__).resolve().parent.parent
fonts_dir = BASE_DIR / "fonts"
phrase = "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ"
shaped = get_display(arabic_reshaper.reshape(phrase))

output_dir = BASE_DIR / "output" / "arabic_font_tests"
output_dir.mkdir(parents=True, exist_ok=True)

fonts = sorted(
    p for p in fonts_dir.rglob("*")
    if p.suffix.lower() in {".ttf", ".otf"}
)

results = []
for font_path in fonts:
    try:
        font = ImageFont.truetype(str(font_path), 80)
        img = Image.new("RGB", (1400, 260), "white")
        draw = ImageDraw.Draw(img)
        draw.text((10, 10), shaped, font=font, fill="black")
        output_file = output_dir / f"test_{font_path.name}.png"
        img.save(output_file)
        results.append((font_path.name, "saved", output_file))
    except Exception as exc:
        results.append((font_path.name, "error", str(exc)))

for font_name, status, info in results:
    print(f"{font_name}: {status} - {info}")
