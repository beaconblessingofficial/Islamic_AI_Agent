from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import arabic_reshaper
from bidi.algorithm import get_display

BASE = Path(__file__).resolve().parent.parent
font_path = BASE / 'fonts' / '_extracted_fonts' / 'Amiri-Italic.ttf'
text = 'رَبَّنَا لَا تُزِغْ قُلُوبَنَا بَعْدَ أَنْ هَدَيْتَنَا'
reshaped = arabic_reshaper.reshape(text)
display = get_display(reshaped)
print('display repr:', repr(display))
print('font path', font_path)
print('font exists', font_path.exists())
font = ImageFont.truetype(str(font_path), 72)
img = Image.new('RGB', (1080, 300), (255, 255, 255))
draw = ImageDraw.Draw(img)
bbox = draw.textbbox((0, 0), display, font=font)
print('bbox', bbox)
draw.text((20, 20), display, font=font, fill=(0, 0, 0))
out = BASE / 'output' / 'test_arabic_render.png'
img.save(out)
print('saved', out)
