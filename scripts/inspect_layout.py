from pathlib import Path
import sys
BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE / 'scripts'))
from image_gen import ImageGenerator
from verse_db import VerseDB
from PIL import Image, ImageDraw

assets = BASE / 'templates'
output = BASE / 'output'
gen = ImageGenerator(assets, output)
print('background exists', gen.background_path.exists())
print('logo exists', gen.logo_path.exists(), 'logo path', gen.logo_path)
print('separator exists', gen.separator_path.exists(), 'separator path', gen.separator_path)
print('ar_font_path', gen.ar_font_path)
print('en_font_path', gen.en_font_path)

# load a sample verse
db = VerseDB(BASE / 'database' / 'quran_posts.csv', BASE / 'database' / 'used_verses.txt')
verse = db.select_random()
print('verse id', verse['id'])
print('arabic', verse['arabic'])
print('transliteration', verse['transliteration'])
print('translation', verse['translation'])

from PIL import ImageFont
import arabic_reshaper
from bidi.algorithm import get_display

ar_font = ImageFont.truetype(str(gen.ar_font_path), 72)
tri_font = ImageFont.truetype(str(gen.en_font_path), 36)
trans_font = ImageFont.truetype(str(gen.en_font_path), 30)
ref_font = ImageFont.truetype(str(gen.en_font_path), 22)
img = Image.new('RGB', (1080, 1080), color=(255,255,255))
draw = ImageDraw.Draw(img)

arabic_display = get_display(arabic_reshaper.reshape(verse['arabic']))
print('arabic_display repr', repr(arabic_display))
print('arabic_display length', len(arabic_display))

ar_lines = gen._wrap_text(draw, arabic_display, ar_font, int((1080-160)*0.95), is_rtl=True)
tri_lines = gen._wrap_text(draw, verse['transliteration'], tri_font, 1080-160)
trans_lines = gen._wrap_text(draw, verse['translation'], trans_font, 1080-160)
print('ar_lines', ar_lines)
print('tri_lines', tri_lines)
print('trans_lines', trans_lines)
print('ar bbox', [draw.textbbox((0,0), l, font=ar_font) for l in ar_lines])
print('tri bbox', [draw.textbbox((0,0), l, font=tri_font) for l in tri_lines])
print('trans bbox', [draw.textbbox((0,0), l, font=trans_font) for l in trans_lines])
