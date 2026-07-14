from pathlib import Path
import sys
BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE / 'scripts'))
from image_gen import ImageGenerator
from PIL import Image, ImageDraw, ImageFont

sample = 'رَبَّنَا لَا تُزِغْ قُلُوبَنَا'

assets = BASE / 'templates'
output = BASE / 'output'
gen = ImageGenerator(assets, output)
print('Selected Arabic font:', gen.ar_font_path)
print('Exists:', gen.ar_font_path.exists())

font = ImageFont.truetype(str(gen.ar_font_path), 80)
img = Image.new('RGB', (900, 220), (255, 255, 255))
Draw = ImageDraw.Draw(img)
reshaped = __import__('arabic_reshaper').reshape(sample)
displayed = __import__('bidi.algorithm').algorithm.get_display(reshaped)
Draw.text((20, 20), displayed, font=font, fill='black')
img.save(output / 'font_render_test.png')
print('Saved:', output / 'font_render_test.png')
