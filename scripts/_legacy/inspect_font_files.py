from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import struct

BASE = Path(__file__).resolve().parent.parent
fonts_dir = BASE / 'fonts'
print('BASE', BASE)
for p in sorted(fonts_dir.iterdir()):
    if p.is_file():
        print('FILE', p.name, p.stat().st_size)
        with open(p, 'rb') as f:
            header = f.read(4)
        print('  header', header)
        try:
            font = ImageFont.truetype(str(p), 40)
            print('  load ok')
            for ch in ['ا', 'م', 'ر', 'ي', ' ']:
                bbox = font.getbbox(ch)
                print(f'    {ch} bbox', bbox)
        except Exception as e:
            print('  load fail', e)

ext_dir = fonts_dir / '_extracted_fonts'
if ext_dir.exists():
    for p in sorted(ext_dir.iterdir()):
        if p.is_file():
            print('EXTRACTED', p.name, p.stat().st_size)
            with open(p, 'rb') as f:
                header = f.read(4)
            print('  header', header)
            try:
                font = ImageFont.truetype(str(p), 40)
                print('  load ok')
                for ch in ['ا', 'م', 'ر', 'ي', ' ']:
                    bbox = font.getbbox(ch)
                    print(f'    {ch} bbox', bbox)
            except Exception as e:
                print('  load fail', e)
