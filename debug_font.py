import sys
from pathlib import Path
BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE / "scripts"))

from image_gen import ImageGenerator
from verse_db import VerseDB
import arabic_reshaper
from bidi.algorithm import get_display
from PIL import ImageFont, ImageDraw, Image

def debug():
    gen = ImageGenerator(BASE / "templates", BASE / "output")
    print("1. Resolved Arabic Font Path:", gen.ar_font_path)
    
    try:
        font = ImageFont.truetype(str(gen.ar_font_path), 40)
        print("2. Font successfully loaded by Pillow ImageFont.truetype()")
    except Exception as e:
        print("2. FAILED to load font:", e)
        return
        
    db = VerseDB(BASE / "database" / "quran_posts.csv", BASE / "database" / "used_verses.txt")
    verse = db.verses[1] if 1 in db.verses else next(iter(db.verses.values()))
    raw_arabic = verse["arabic"]
    print(f"\n3. Raw Arabic (length {len(raw_arabic)}): {raw_arabic[:50].encode('ascii', 'backslashreplace')}...")
    
    # 4. Check if Pillow can find the glyphs for the RAW text
    missing = [c for c in raw_arabic if not font.getmask(c).getbbox()]
    print(f"4. Missing glyphs in RAW text: {len(missing)} out of {len(raw_arabic)}")
    
    reshaped = arabic_reshaper.reshape(raw_arabic)
    print(f"5. Reshaped text (length {len(reshaped)}): {reshaped[:50].encode('ascii', 'backslashreplace')}...")
    missing_reshaped = [c for c in reshaped if not font.getmask(c).getbbox()]
    print(f"6. Missing glyphs in RESHAPED text: {len(missing_reshaped)} out of {len(reshaped)}")
    
    bidi_text = get_display(reshaped)
    print(f"7. Bidi text (length {len(bidi_text)}): {bidi_text[:50].encode('ascii', 'backslashreplace')}...")
    missing_bidi = [c for c in bidi_text if not font.getmask(c).getbbox()]
    print(f"8. Missing glyphs in BIDI text: {len(missing_bidi)} out of {len(bidi_text)}")
    
    print("\n9. Sample of missing bidi codepoints:", [hex(ord(c)) for c in missing_bidi[:10]])
    print("10. Sample of missing reshaped codepoints:", [hex(ord(c)) for c in missing_reshaped[:10]])

if __name__ == "__main__":
    debug()
