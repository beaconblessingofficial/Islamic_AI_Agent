from PIL import ImageFont
from pathlib import Path

fonts = [Path('fonts') / 'Amiri-Regular.ttf', Path('fonts') / 'PlayfairDisplay-Regular.ttf']

for f in fonts:
    print('Checking', f)
    try:
        ft = ImageFont.truetype(str(f), 24)
        print('Loaded OK:', f, '-> size', ft.size)
    except Exception as e:
        print('Failed to load', f, '->', type(e).__name__, e)
    try:
        with open(f, 'rb') as fh:
            h = fh.read(8)
            print('Header bytes:', h[:8])
    except Exception as e:
        print('Cannot read file bytes for', f, '->', e)

