import sys
sys.path.append(r"D:\Islamic_AI_Agent\venv\Lib\site-packages")
from fontTools.ttLib import TTFont

font = TTFont(r"D:\Islamic_AI_Agent\fonts\_extracted_fonts\Amiri-Italic.ttf")
cmap = font.getBestCmap()
print(f"Total glyphs mapped: {len(cmap)}")

# Check Arabic base block (0x0600 - 0x06FF)
base_count = sum(1 for cp in cmap if 0x0600 <= cp <= 0x06FF)
print(f"Arabic Base (0600-06FF): {base_count}")

# Check Presentation Forms-B (0xFE70 - 0xFEFF)
pres_b_count = sum(1 for cp in cmap if 0xFE70 <= cp <= 0xFEFF)
print(f"Presentation Forms-B (FE70-FEFF): {pres_b_count}")

# Check Presentation Forms-A (0xFB50 - 0xFDFF)
pres_a_count = sum(1 for cp in cmap if 0xFB50 <= cp <= 0xFDFF)
print(f"Presentation Forms-A (FB50-FDFF): {pres_a_count}")
