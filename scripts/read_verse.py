import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

csv_file = BASE_DIR / "database" / "quran_posts.csv"

df = pd.read_csv(csv_file)

print(df.head())