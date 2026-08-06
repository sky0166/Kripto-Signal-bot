import os
from dotenv import load_dotenv

load_dotenv()

print("Kripto Sinyal Botu başlatıldı")

coins = [
    "GRTUSDT",
    "ARBUSDT",
    "AVAXUSDT",
    "HOTUSDT",
    "TLMUSDT",
    "APTUSDT",
    "XRPUSDT",
    "TAOUSDT",
    "ONDOUSDT",
    "APEUSDT",
    "DOGEUSDT"
]

for coin in coins:
    print(coin, "analiz ediliyor...")
