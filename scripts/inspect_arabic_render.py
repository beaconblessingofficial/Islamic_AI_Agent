from pathlib import Path
import sys
BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE / 'scripts'))
from image_gen import ImageGenerator
from verse_db import VerseDB
import arabic_reshaper
from bidi.algorithm import get_display

# sample verse with diacritics
verse = 'رَبِّ لَا تَذَرْنِي فَرْدًا'
print('original:', repr(verse))
reshaped = arabic_reshaper.reshape(verse)
print('reshaped:', repr(reshaped))
display = get_display(reshaped)
print('display:', repr(display))
print('display repr:', display)

# create sample image
from PIL import Image, ImageDraw, ImageFont
font_path = Path('fonts') / '_extracted_fonts' / 'Amiri-Italic.ttf'
font = ImageFont.truetype(str(font_path), 72)
img = Image.new('RGB', (900, 200), (255, 255, 255))
draw = ImageDraw.Draw(img)
draw.text((10,10), display, fill='black', font=font)
out = BASE / 'output' / 'inspect_arabic.png'
img.save(out)
print('saved', out)
