from PIL import Image, ImageDraw, ImageFont
import pandas as pd
from pathlib import Path
import textwrap
import datetime
import arabic_reshaper
from bidi.algorithm import get_display

# ==========================
# PATHS
# ==========================

BASE_DIR = Path(__file__).resolve().parent.parent

csv_file = BASE_DIR / "database" / "quran_posts.csv"
background_path = BASE_DIR / "templates" / "background.jpg"
logo_path = BASE_DIR / "templates" / "logo.png"
separator_path = BASE_DIR / "templates" / "separator.png"

english_font_path = r"C:\Windows\Fonts\georgia.ttf"
arabic_font_path = BASE_DIR / "fonts" / "_extracted_fonts" / "AmiriQuran.ttf"
if not arabic_font_path.exists():
    raise FileNotFoundError(
        f"Arabic font not found: {arabic_font_path}. Please install AmiriQuran.ttf in fonts/_extracted_fonts."
    )

# ==========================
# OUTPUT FILE
# ==========================

timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

output_path = (
    BASE_DIR
    / "output"
    / f"post_{timestamp}.png"
)

# ==========================
# LOAD CSV
# ==========================

df = pd.read_csv(csv_file)

# ==========================
# USED VERSES
# ==========================

used_file = BASE_DIR / "database" / "used_verses.txt"

if not used_file.exists():
    used_file.touch()

with open(used_file, "r") as f:
    used_ids = [
        int(line.strip())
        for line in f
        if line.strip()
    ]

available = df[
    ~df["id"].isin(used_ids)
]

if len(available) == 0:

    print("All verses used. Resetting list.")

    with open(used_file, "w") as f:
        pass

    available = df

verse = available.sample(
    n=1
).iloc[0]

with open(used_file, "a") as f:
    f.write(
        str(verse["id"]) + "\n"
    )

# ==========================
# VERSE DATA
# ==========================

arabic = str(verse["arabic"])

transliteration = str(
    verse["transliteration"]
)

translation = str(
    verse["translation"]
)

reference = (
    f"{verse['surah']} ({verse['ayah']})"
)

# ==========================
# IMAGE
# ==========================

img = Image.open(background_path).convert("RGBA")
img = img.resize((1080, 1080))

draw = ImageDraw.Draw(img)

# ==========================
# FONTS
# ==========================

def _font_supports(font_path: Path, codepoints: set) -> bool:
    try:
        tt = TTFont(font_path)
        supported = set()
        for table in tt['cmap'].tables:
            supported.update(table.cmap.keys())
        return all(cp in supported for cp in codepoints)
    except Exception:
        return False

# Force use of the single confirmed working font: Amiri-Italic.ttf
arabic_font_path = BASE_DIR / 'fonts' / '_extracted_fonts' / 'Amiri-Italic.ttf'
if not arabic_font_path.exists():
    raise FileNotFoundError(f"Required Arabic font not found: {arabic_font_path}")

# Load Arabic font
arabic_font = ImageFont.truetype(str(arabic_font_path), 96)


translit_font = ImageFont.truetype(
    english_font_path,
    34
)

translation_font = ImageFont.truetype(
    english_font_path,
    60
)

reference_font = ImageFont.truetype(
    english_font_path,
    34
)

# ==========================
# LOGO
# ==========================

logo = Image.open(
    logo_path
).convert("RGBA")

logo = logo.resize((190, 190))

logo_width = logo.width
logo_height = logo.height

# ==========================
# HELPERS
# ==========================

def wrap_text(draw, text, font, max_width):
    words = text.split()
    if not words:
        return []

    lines = []
    current = []
    for word in words:
        candidate = " ".join(current + [word]) if current else word
        bbox = draw.textbbox((0, 0), candidate, font=font)
        width = bbox[2] - bbox[0]
        if width <= max_width or not current:
            current.append(word)
        else:
            lines.append(" ".join(current))
            current = [word]

    if current:
        lines.append(" ".join(current))

    return lines


def measure_block(draw, lines, font, spacing=0):
    width = 0
    height = 0
    for index, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        line_w = bbox[2] - bbox[0]
        line_h = bbox[3] - bbox[1]
        width = max(width, line_w)
        height += line_h
        if index < len(lines) - 1:
            height += spacing
    return width, height


def layout_blocks(draw, max_width, ar_size, tri_size, trans_size, ref_size, translation_max_width=None):
    ar_font = ImageFont.truetype(arabic_font_path, ar_size)
    tri_font = ImageFont.truetype(english_font_path, tri_size)
    translation_font = ImageFont.truetype(english_font_path, trans_size)
    ref_font = ImageFont.truetype(english_font_path, ref_size)

    if translation_max_width is None:
        translation_max_width = max_width

    ar_lines = wrap_text(draw, arabic, ar_font, max_width)
    tri_lines = wrap_text(draw, transliteration, tri_font, max_width)
    translation_lines = wrap_text(draw, translation, translation_font, translation_max_width)

    ar_width, ar_height = measure_block(draw, ar_lines, ar_font, spacing=16)
    tri_width, tri_height = measure_block(draw, tri_lines, tri_font, spacing=10)
    translation_width, translation_height = measure_block(draw, translation_lines, translation_font, spacing=16)
    ref_width, ref_height = measure_block(draw, [reference], ref_font)

    return {
        "ar_font": ar_font,
        "tri_font": tri_font,
        "translation_font": translation_font,
        "ref_font": ref_font,
        "ar_lines": ar_lines,
        "tri_lines": tri_lines,
        "translation_lines": translation_lines,
        "widths": {
            "arabic": ar_width,
            "translit": tri_width,
            "translation": translation_width,
            "reference": ref_width,
        },
        "heights": {
            "arabic": ar_height,
            "translit": tri_height,
            "translation": translation_height,
            "reference": ref_height,
        },
    }

# ==========================
# LOAD SEPARATOR
# ==========================

separator = None
separator_width = 0
separator_height = 0

if separator_path.exists():
    separator = Image.open(separator_path).convert("RGBA")
    separator = separator.resize((780, 90), Image.LANCZOS)
    separator_width = separator.width
    separator_height = separator.height

# ==========================
# DYNAMIC LAYOUT
# ==========================

content_max_width = 1080 - 2 * 80
max_total_height = 1080 - 2 * 40

ar_size = 82
tri_size = 34
trans_size = 60
ref_size = 34

layout = None
start_sizes = (ar_size, tri_size, trans_size, ref_size)
translation_max_width = int(1080 * 0.75)

for _ in range(20):
    layout = layout_blocks(draw, content_max_width, ar_size, tri_size, trans_size, ref_size, translation_max_width)
    total_height = (
        logo_height
        + 35
        + layout["heights"]["arabic"]
        + 30
        + layout["heights"]["translit"]
        + 35
        + (separator_height + 35 if separator else 0)
        + layout["heights"]["translation"]
        + 35
        + (separator_height + 35 if separator else 0)
        + layout["heights"]["reference"]
    )

    max_width_used = max(layout["widths"].values())
    if total_height <= max_total_height and max_width_used <= content_max_width:
        break

    # Prioritize reducing transliteration and translation sizes before reducing Arabic.
    reduced = False
    if tri_size > 12:
        tri_size = max(12, int(tri_size * 0.9))
        reduced = True
    if trans_size > 14:
        trans_size = max(14, int(trans_size * 0.9))
        reduced = True
    if not reduced:
        # Only reduce Arabic after transliteration/translation are at minimum
        ar_size = max(80, int(ar_size * 0.92))
        ref_size = max(16, int(ref_size * 0.92))

reduced = (ar_size, tri_size, trans_size, ref_size) != start_sizes
if reduced:
    print(
        f"REDUCTION: verse={verse['id']} surah={verse['surah']} ayah={verse['ayah']} "
        f"from={start_sizes} to={(ar_size, tri_size, trans_size, ref_size)}"
    )

wrap_info = {
    'arabic': len(layout['ar_lines']),
    'transliteration': len(layout['tri_lines']),
    'translation': len(layout['translation_lines']),
}
if any(v > 1 for v in wrap_info.values()):
    print(
        f"WRAP: verse={verse['id']} surah={verse['surah']} ayah={verse['ayah']} "
        f"arabic_lines={wrap_info['arabic']} transliteration_lines={wrap_info['transliteration']} "
        f"translation_lines={wrap_info['translation']}"
    )

if layout is None:
    raise RuntimeError("Unable to compute layout")

logo_y = max(25, (1080 - total_height) // 2)
img.paste(logo, ((1080 - logo_width) // 2, logo_y), logo)
current_y = logo_y + logo_height + 35

# ==========================
# DRAW ARABIC
# ==========================

for line in layout["ar_lines"]:
    bbox = draw.textbbox((0, 0), line, font=layout["ar_font"])
    line_width = bbox[2] - bbox[0]
    x = (1080 - line_width) // 2
    draw.text((x, current_y), line, fill="black", font=layout["ar_font"])
    current_y += bbox[3] - bbox[1] + 16

current_y += 28

# ==========================
# DRAW TRANSLITERATION
# ==========================

for line in layout["tri_lines"]:
    bbox = draw.textbbox((0, 0), line, font=layout["tri_font"])
    line_width = bbox[2] - bbox[0]
    x = (1080 - line_width) // 2
    draw.text((x, current_y), line, fill="black", font=layout["tri_font"])
    current_y += bbox[3] - bbox[1] + 10

current_y += 25

# ==========================
# TOP SEPARATOR
# ==========================

if separator:
    sep_x = (1080 - separator_width) // 2
    img.paste(separator, (sep_x, current_y), separator)
    current_y += separator_height + 35

# ==========================
# DRAW TRANSLATION
# ==========================

for line in layout["translation_lines"]:
    bbox = draw.textbbox((0, 0), line, font=layout["translation_font"])
    line_width = bbox[2] - bbox[0]
    x = (1080 - line_width) // 2
    draw.text((x, current_y), line, fill="black", font=layout["translation_font"])
    current_y += bbox[3] - bbox[1] + 16

current_y += 20

# ==========================
# BOTTOM SEPARATOR
# ==========================

if separator:
    img.paste(separator, (sep_x, current_y), separator)
    current_y += separator_height + 35

# ==========================
# DRAW REFERENCE
# ==========================

bbox = draw.textbbox((0, 0), reference, font=layout["ref_font"])
ref_width = bbox[2] - bbox[0]
ref_x = (1080 - ref_width) // 2

draw.text((ref_x, current_y), reference, fill="black", font=layout["ref_font"])

# ==========================
# SAVE
# ==========================

img.save(output_path)

print()
print("Saved Successfully")
print(output_path)
print()