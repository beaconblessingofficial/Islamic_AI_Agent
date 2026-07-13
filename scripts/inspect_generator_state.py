from pathlib import Path
import sys
BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE / 'scripts'))
from image_gen import ImageGenerator
from verse_db import VerseDB
from PIL import Image, ImageDraw, ImageFont
import arabic_reshaper
from bidi.algorithm import get_display

assets = BASE / 'templates'
output = BASE / 'output'
gen = ImageGenerator(assets, output)

print('logo exists', gen.logo_path.exists(), 'logo path', gen.logo_path)
print('separator exists', gen.separator_path.exists(), 'separator path', gen.separator_path)
print('bg exists', gen.background_path.exists(), 'bg path', gen.background_path)
print('ar_font_path', gen.ar_font_path)
print('en_font_path', gen.en_font_path)

# choose a sample verse
db = VerseDB(BASE / 'database' / 'quran_posts.csv', BASE / 'database' / 'used_verses.txt')
verse = db.verses[2] if 2 in db.verses else next(iter(db.verses.values()))
print('verse id', verse['id'])
print('arabic', verse['arabic'])

# replicate calculations
WIDTH = gen.WIDTH
HEIGHT = gen.HEIGHT
margin_x = 80
content_width = WIDTH - margin_x * 2

ar_size = 72
trans_size = 30
tri_size = 36
ref_size = 22

draw = ImageDraw.Draw(Image.new('RGB',(WIDTH,HEIGHT),(255,255,255)))
logo = None
if gen.logo_path.exists():
    logo = __import__('PIL').Image.open(gen.logo_path).convert('RGBA')
    max_logo_w = int(WIDTH*0.25)
    if logo.width > max_logo_w:
        logo = logo.resize((max_logo_w, int(max_logo_w * logo.height / logo.width)), __import__('PIL').Image.LANCZOS)
separator = None
if gen.separator_path.exists():
    separator = __import__('PIL').Image.open(gen.separator_path).convert('RGBA')
    if separator.width > content_width:
        separator = separator.resize((content_width, int(separator.height * content_width / separator.width)), __import__('PIL').Image.LANCZOS)

for attempt in range(12):
    ar_font = ImageFont.truetype(str(gen.ar_font_path), ar_size)
    tri_font = ImageFont.truetype(str(gen.en_font_path), tri_size)
    trans_font = ImageFont.truetype(str(gen.en_font_path), trans_size)
    ref_font = ImageFont.truetype(str(gen.en_font_path), ref_size)

    arabic_display = get_display(arabic_reshaper.reshape(verse['arabic']))
    ar_lines = gen._wrap_text(draw, arabic_display, ar_font, int(content_width * 0.95), is_rtl=True)
    tri_lines = gen._wrap_text(draw, verse['transliteration'], tri_font, content_width)
    trans_lines = gen._wrap_text(draw, verse['translation'], trans_font, content_width)

    total_h = 0
    gaps = 20
    if logo:
        total_h += logo.height + gaps
    for l in ar_lines:
        bbox = draw.textbbox((0,0), l, font=ar_font)
        total_h += bbox[3]-bbox[1]+8
    total_h += gaps
    for l in tri_lines:
        bbox = draw.textbbox((0,0), l, font=tri_font)
        total_h += bbox[3]-bbox[1]+6
    total_h += gaps
    if separator:
        total_h += separator.height + gaps
    for l in trans_lines:
        bbox = draw.textbbox((0,0), l, font=trans_font)
        total_h += bbox[3]-bbox[1]+6
    total_h += gaps
    if separator:
        total_h += separator.height + gaps
    bbox = draw.textbbox((0,0), f"{verse['surah']} {verse['ayah']}", font=ref_font)
    total_h += bbox[3]-bbox[1]

    print('attempt', attempt, 'sizes', ar_size, trans_size, tri_size, ref_size)
    print('ar_lines', ar_lines)
    print('tri_lines', tri_lines)
    print('trans_lines', trans_lines)
    print('total_h', total_h)
    y = (HEIGHT - total_h)//2
    print('start y', y)
    if total_h <= HEIGHT-160:
        break
    ar_size = max(28, int(ar_size*0.9))
    tri_size = max(14, int(tri_size*0.95))
    trans_size = max(12, int(trans_size*0.95))
    ref_size = max(10, int(ref_size*0.95))

# print all y positions
print('logo height', logo.height if logo else None)
print('separator height', separator.height if separator else None)
if logo:
    y_logo = y
    y2 = y_logo + logo.height + 20
    print('logo_y', y_logo)
else:
    y2 = y
for l in ar_lines:
    bbox = draw.textbbox((0,0), l, font=ar_font)
    print('arabic line', l, 'y', y2, 'bbox', bbox)
    y2 += bbox[3]-bbox[1]+8
print('after arabic y', y2)
