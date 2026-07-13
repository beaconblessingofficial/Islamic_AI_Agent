from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import arabic_reshaper
from bidi.algorithm import get_display

sample = 'رَبِّ لَا تَذَرْنِي فَرْدًا'
reshaped = arabic_reshaper.reshape(sample)
display = get_display(reshaped)

candidates = [
    Path(r'C:/Windows/Fonts/arial.ttf'),
    Path(r'C:/Windows/Fonts/arialbd.ttf'),
    Path(r'C:/Windows/Fonts/arialbi.ttf'),
    Path(r'C:/Windows/Fonts/arialn.ttf'),
    Path(r'C:/Windows/Fonts/arabtype.ttf'),
    Path(r'C:/Windows/Fonts/tradbdo.ttf'),
    Path(r'C:/Windows/Fonts/times.ttf'),
    Path(r'C:/Windows/Fonts/tahoma.ttf'),
    Path(r'C:/Windows/Fonts/seguisym.ttf'),
    Path(r'C:/Windows/Fonts/seguisym.ttf'),
]

out_dir = Path(__file__).resolve().parent.parent / 'output'
out_dir.mkdir(exist_ok=True)
for font_path in candidates:
    if not font_path.exists():
        continue
    try:
        font = ImageFont.truetype(str(font_path), 72)
        img = Image.new('RGB', (1200, 200), (255, 255, 255))
        draw = ImageDraw.Draw(img)
        draw.text((10, 10), display, font=font, fill='black')
        out = out_dir / f'test_font_{font_path.stem}.png'
        img.save(out)
        print('saved', out)
    except Exception as e:
        print('failed', font_path, e)
