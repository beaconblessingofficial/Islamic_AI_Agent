from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import arabic_reshaper
from bidi.algorithm import get_display

BASE = Path(__file__).resolve().parent.parent
sample = 'رَبَّنَا لَا تُزِغْ قُلُوبَنَا'
reshaped = arabic_reshaper.reshape(sample)
display = get_display(reshaped)

candidates = [
    BASE / 'fonts' / '_extracted_fonts' / 'Amiri-Italic.ttf',
    BASE / 'fonts' / '_extracted_fonts' / 'AmiriQuran.ttf',
    BASE / 'fonts' / '_extracted_fonts' / 'AmiriQuranColored.ttf',
    BASE / 'fonts' / '_extracted_fonts' / 'PlayfairDisplay-Regular.ttf',
    Path(r'C:/Windows/Fonts/arabtype.ttf'),
    Path(r'C:/Windows/Fonts/arial.ttf'),
    Path(r'C:/Windows/Fonts/tahoma.ttf'),
]
out_dir = BASE / 'output'
out_dir.mkdir(exist_ok=True)
for font_path in candidates:
    if not font_path.exists():
        print('missing', font_path)
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
