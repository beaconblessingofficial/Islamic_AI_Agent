import pandas as pd
from pathlib import Path
import random

BASE_DIR = Path(__file__).resolve().parent.parent

csv_file = BASE_DIR / "database" / "quran_posts.csv"

df = pd.read_csv(csv_file)

verse = df.sample(n=1).iloc[0]

print("Surah:", verse["surah"])
print("Ayah:", verse["ayah"])
print("Theme:", verse["theme"])
print("Translation:", verse["translation"])