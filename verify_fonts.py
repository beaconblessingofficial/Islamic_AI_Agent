import sys
from pathlib import Path
import zipfile
import arabic_reshaper
from bidi.algorithm import get_display
from PIL import Image, ImageDraw, ImageFont

# Ensure fontTools is available
sys.path.append(r"D:\Islamic_AI_Agent\venv\Lib\site-packages")
from fontTools.ttLib import TTFont

BASE_DIR = Path(__file__).resolve().parent

# Fonts
zip_path = BASE_DIR / "fonts" / "Amiri-Regular.ttf"
extracted_dir = BASE_DIR / "fonts" / "_extracted_fonts"

amiri_regular_path = extracted_dir / "Amiri-Regular.ttf"
amiri_quran_path = extracted_dir / "AmiriQuran.ttf"

def extract_if_needed():
    if not amiri_regular_path.exists():
        with zipfile.ZipFile(zip_path) as z:
            with z.open("Amiri-1.002/Amiri-Regular.ttf") as inf, open(amiri_regular_path, 'wb') as outf:
                outf.write(inf.read())

def check_font(font_path, font_name, raw_arabic):
    print(f"\n--- Checking {font_name} ---")
    
    # 1. ImageFont load test
    try:
        pil_font = ImageFont.truetype(str(font_path), 60)
        print("ImageFont.truetype() : SUCCESS")
    except Exception as e:
        print(f"ImageFont.truetype() : FAILED ({e})")
        return None
        
    # 2. fontTools Cmap test
    ttfont = TTFont(str(font_path))
    cmap = ttfont.getBestCmap()
    
    reshaped_text = arabic_reshaper.reshape(raw_arabic)
    bidi_text = get_display(reshaped_text)
    
    supported_raw = all(ord(c) in cmap or c == ' ' for c in raw_arabic)
    supported_pres = all(ord(c) in cmap or c == ' ' for c in bidi_text)
    
    print(f"Supports base characters (0600 range)? : {supported_raw}")
    print(f"Supports Presentation Forms (FE70 range)? : {supported_pres}")
    
    missing = [hex(ord(c)) for c in bidi_text if ord(c) not in cmap and c != ' ']
    if missing:
        print(f"Missing codepoints for reshaped text: {missing[:5]}...")
        
    return pil_font, bidi_text

def render_image(font, text, out_name):
    # Render an image
    img = Image.new('RGB', (800, 300), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    # Draw text in the middle
    bbox = draw.textbbox((0, 0), text, font=font)
    x = (800 - (bbox[2] - bbox[0])) // 2
    y = (300 - (bbox[3] - bbox[1])) // 2
    draw.text((x, y), text, font=font, fill=(0, 0, 0))
    
    out_path = BASE_DIR / out_name
    img.save(out_path)
    print(f"Saved test image: {out_path.name}")

def main():
    extract_if_needed()
    
    # Same verse used previously
    raw_arabic = "\u0625\u0650\u0630\u0652 \u0623\u064e\u0648\u064e\u0649 \u0627\u0644\u0652\u0641\u0650\u062a\u0652\u064a\u064e\u0629\u064f \u0625\u0650\u0644\u064e\u0649 \u0627\u0644\u0652\u0643\u064e\u0647\u0652\u0641\u0650"
    
    print("Test verse:", raw_arabic.encode('ascii', 'backslashreplace').decode('ascii'))
    
    res_regular = check_font(amiri_regular_path, "Amiri-Regular.ttf", raw_arabic)
    if res_regular:
        render_image(res_regular[0], res_regular[1], "amiri_regular_test.png")
        
    res_quran = check_font(amiri_quran_path, "AmiriQuran.ttf", raw_arabic)
    if res_quran:
        render_image(res_quran[0], res_quran[1], "amiri_quran_test.png")

if __name__ == '__main__':
    main()
