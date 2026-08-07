
import requests

print("Kripto Sinyal Botu başlatıldı")

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

    for coin_id, symbol in coins.items():
        coin = data.get(coin_id)

        if not coin:
            print(symbol, "verisi alınamadı")
            continue

        price = coin.get("usd")
        change = coin.get("usd_24h_change", 0)

        if change >= 2:
            signal = "LONG AĞIRLIKLI"
        elif change <= -2:
            signal = "SHORT AĞIRLIKLI"
        else:
            signal = "BEKLE"

        print(
            f"{symbol}: ${price} | "
            f"24s: {change:.2f}% | "
            f"Sinyal: {signal}"
        )

except Exception as e:
    print("Veri alınırken hata oluştu:", e)
