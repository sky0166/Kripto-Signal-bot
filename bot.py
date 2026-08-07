import os
import requests

print("Kripto Sinyal Botu başlatıldı")

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

coins = {
    "bitcoin": "BTC",
    "ethereum": "ETH",
    "avalanche-2": "AVAX",
    "dogecoin": "DOGE",
    "ripple": "XRP",
    "arbitrum": "ARB",
    "aptos": "APT",
    "the-graph": "GRT",
    "theta-token": "THETA",
    "ondo-finance": "ONDO",
    "apecoin": "APE"
}

url = "https://api.coingecko.com/api/v3/simple/price"

params = {
    "ids": ",".join(coins.keys()),
    "vs_currencies": "usd",
    "include_24hr_change": "true"
}

try:
    response = requests.get(url, params=params, timeout=20)
    response.raise_for_status()
    data = response.json()

    mesaj = "📊 KRİPTO SİNYALLERİ\n\n"

    for coin_id, symbol in coins.items():
        coin = data.get(coin_id)

        if not coin:
            continue

        price = coin.get("usd")
        change = coin.get("usd_24h_change", 0)

        if change >= 2:
            signal = "🟢 LONG AĞIRLIKLI"
        elif change <= -2:
            signal = "🔴 SHORT AĞIRLIKLI"
        else:
            signal = "⚪ BEKLE"

        mesaj += (
            f"{symbol}: ${price}\n"
            f"24s: {change:.2f}%\n"
            f"Sinyal: {signal}\n\n"
        )

    telegram_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    telegram_response = requests.post(
        telegram_url,
        data={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": mesaj
        },
        timeout=20
    )

    telegram_response.raise_for_status()

    print("Telegram mesajı gönderildi.")

except Exception as e:
    print("Hata:", e)
    raise
