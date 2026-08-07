import os
from dotenv import load_dotenv
from binance.client import Client

load_dotenv()

print("Kripto Sinyal Botu başlatıldı")

API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_SECRET_KEY")

client = Client(API_KEY, API_SECRET)
client.API_URL = "https://api.binance.com"
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
    try:
        fiyat = client.get_symbol_ticker(symbol=coin)
        print(coin, ":", fiyat["price"])
    except Exception as e:
        print(coin, "hata:", e)
