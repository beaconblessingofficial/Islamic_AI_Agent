from pathlib import Path
import sys
BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE / 'scripts'))
from image_gen import ImageGenerator
from PIL import ImageFont

gen = ImageGenerator(BASE / 'templates', BASE / 'output')
print('selected ar font:', gen.ar_font_path)
print('exists:', gen.ar_font_path.exists())
try:
    font = ImageFont.truetype(str(gen.ar_font_path), 72)
    print('loaded ok')
except Exception as e:
    print('load error', e)
