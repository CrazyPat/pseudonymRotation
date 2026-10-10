"""Summiert die Marktanteile aller Browser mit Chromium-Engine (Anhang A, Tabelle A.1)."""
import pandas as pd
from pathlib import Path

df = pd.read_csv(Path(__file__).parent / '../Data/datensatz/statsCounterData.csv')

chromium_cols = [
    "Chrome", # https://www.chromium.org/chromium-projects/
    "Edge", # https://learn.microsoft.com/en-us/microsoft-edge/extensions/
    "Samsung Internet", # https://developer.samsung.com/internet/blog/en/2021/09/01/introducing-the-samsung-internet-160-beta
    "Opera", # https://blogs.opera.com/news/2025/01/opera-joins-supporters-of-chromium-based-browsers-open-source-ecosystem/
    "Brave", # https://support.brave.app/hc/de/articles/10742158329613-Was-entfernt-Brave-aus-der-Chromium-Engine
]

df['Total'] = df[chromium_cols].sum(axis=1)

print(df[['Date', 'Total']])
