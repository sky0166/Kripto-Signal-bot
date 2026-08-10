import os
import time
import requests
import pandas as pd
from datetime import datetime, timezone

# ============================================================
# GELİŞMİŞ KRİPTO SİNYAL BOTU
# Veri kaynağı: CoinGecko
# Zaman dilimi: 4 Saat
# Telegram bildirimleri: Aktif
# ============================================================

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# CoinGecko ID -> Binance sembolü
COINS = {
    "bitcoin": "BTCUSDT",
    "ethereum": "ETHUSDT",
    "avalanche-2": "AVAXUSDT",
    "dogecoin": "DOGEUSDT",
    "ripple": "XRPUSDT",
    "arbitrum": "ARBUSDT",
    "aptos": "APTUSDT",
    "the-graph": "GRTUSDT",
    "theta-token": "THETAUSDT",
    "ondo-finance": "ONDOUSDT",
    "apecoin": "APEUSDT",
}


def get_market_data(coin_id):
    """CoinGecko'dan yaklaşık 4 saatlik mum verisi oluşturur."""

    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"

    params = {
        "vs_currency": "usd",
        "days": "90",
        "interval": "hourly"
    }

    response = requests.get(
        url,
        params=params,
        timeout=30,
        headers={
            "User-Agent": "Mozilla/5.0"
        }
    )

    response.raise_for_status()

    data = response.json()

    if "prices" not in data or len(data["prices"]) < 100:
        raise Exception("Yeterli piyasa verisi alınamadı.")

    # Fiyat verisini DataFrame'e çevir
    df = pd.DataFrame(
        data["prices"],
        columns=["timestamp", "close"]
    )

    df["timestamp"] = pd.to_datetime(
        df["timestamp"],
        unit="ms",
        utc=True
    )

    df = df.set_index("timestamp")

    # Saatlik veriyi 4 saatliğe dönüştür
    df = df["close"].resample("4h").last().dropna()

    if len(df) < 60:
        raise Exception("4 saatlik analiz için yeterli veri yok.")

    return df


def calculate_indicators(df):
    """Teknik göstergeleri hesaplar."""

    close = df.copy()

    # EMA
    close["EMA20"] = close["close"].ewm(
        span=20,
        adjust=False
    ).mean()

    close["EMA50"] = close["close"].ewm(
        span=50,
        adjust=False
    ).mean()

    close["EMA200"] = close["close"].ewm(
        span=200,
        adjust=False
    ).mean()

    # RSI 14
    delta = close["close"].diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()

    rs = avg_gain / avg_loss.replace(0, 1e-10)

    close["RSI"] = 100 - (
        100 / (1 + rs)
    )

    # MACD
    ema12 = close["close"].ewm(
        span=12,
        adjust=False
    ).mean()

    ema26 = close["close"].ewm(
        span=26,
        adjust=False
    ).mean()

    close["MACD"] = ema12 - ema26

    close["MACD_SIGNAL"] = close["MACD"].ewm(
        span=9,
        adjust=False
    ).mean()

    # Momentum
    close["MOMENTUM"] = close["close"].pct_change(6) * 100

    return close


def generate_signal(df, symbol):
    """LONG / SHORT / BEKLE sinyali üretir."""

    latest = df.iloc[-1]

    price = latest["close"]
    ema20 = latest["EMA20"]
    ema50 = latest["EMA50"]
    ema200 = latest["EMA200"]
    rsi = latest["RSI"]
    macd = latest["MACD"]
    macd_signal = latest["MACD_SIGNAL"]
    momentum = latest["MOMENTUM"]

    long_score = 0
    short_score = 0

    # Trend
    if price > ema20:
        long_score += 1
    else:
        short_score += 1

    if ema20 > ema50:
        long_score += 1
    else:
        short_score += 1

    if price > ema200:
        long_score += 1
    else:
        short_score += 1

    # RSI
    if 50 <= rsi <= 70:
        long_score += 1

    if 30 <= rsi < 50:
        short_score += 1

    # MACD
    if macd > macd_signal:
        long_score += 1
    else:
        short_score += 1

    # Momentum
    if momentum > 0:
        long_score += 1
    else:
        short_score += 1

    # Sinyal
    if long_score >= 5 and long_score > short_score:
        signal = "🟢 LONG"
        confidence = long_score
    elif short_score >= 5 and short_score > long_score:
        signal = "🔴 SHORT"
        confidence = short_score
    else:
        signal = "🟡 BEKLE"
        confidence = max(long_score, short_score)

    # RSI durumunu belirle
    if rsi >= 70:
        rsi_status = "Aşırı alım"
    elif rsi <= 30:
        rsi_status = "Aşırı satım"
    else:
        rsi_status = "Normal"

    result = {
        "symbol": symbol,
        "price": price,
        "signal": signal,
        "confidence": confidence,
        "rsi": rsi,
        "rsi_status": rsi_status,
        "ema20": ema20,
        "ema50": ema50,
        "ema200": ema200,
        "macd": macd,
        "macd_signal": macd_signal,
        "momentum": momentum,
    }

    return result


def format_signal(result):
    """Telegram mesajını hazırlar."""

    return (
        f"{result['signal']} {result['symbol']}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"💰 Fiyat: ${result['price']:.6f}\n"
        f"📊 Güven skoru: {result['confidence']}/6\n"
        f"📈 RSI(14): {result['rsi']:.2f} ({result['rsi_status']})\n"
        f"📉 EMA20: ${result['ema20']:.6f}\n"
        f"📉 EMA50: ${result['ema50']:.6f}\n"
        f"📉 EMA200: ${result['ema200']:.6f}\n"
        f"〽️ MACD: {result['macd']:.6f}\n"
        f"〽️ MACD Signal: {result['macd_signal']:.6f}\n"
        f"🚀 Momentum: {result['momentum']:.2f}%\n"
        f"⏱ Zaman dilimi: 4H\n"
    )


def send_telegram(message):
    """Telegram'a mesaj gönderir."""

    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("❌ Telegram Secret bilgileri bulunamadı.")
        return False

    url = (
        f"https://api.telegram.org/bot"
        f"{TELEGRAM_TOKEN}/sendMessage"
    )

    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message
    }

    response = requests.post(
        url,
        json=payload,
        timeout=30
    )

    response.raise_for_status()

    return True


def main():

    print("🚀 GELİŞMİŞ KRİPTO SİNYAL BOTU BAŞLATILDI")
    print("📡 Veri kaynağı: CoinGecko")
    print("⏱ Zaman dilimi: 4H")
    print("")

    results = []

    for coin_id, symbol in COINS.items():

        try:
            print(f"🔎 {symbol} analiz ediliyor...")

            df = get_market_data(coin_id)

            df = calculate_indicators(df)

            result = generate_signal(df, symbol)

            results.append(result)

            print(
                f"{symbol}: "
                f"{result['signal']} | "
                f"RSI {result['rsi']:.2f} | "
                f"Skor {result['confidence']}/6"
            )

            # API'yi gereksiz zorlamamak için kısa bekleme
            time.sleep(1)

        except Exception as e:

            print(
                f"❌ {symbol} hata: {e}"
            )

    print("")
    print("📊 Analiz tamamlandı.")

    # Telegram özeti
    now = datetime.now(timezone.utc).strftime(
        "%d.%m.%Y %H:%M UTC"
    )

    header = (
        "🚀 KRİPTO SİNYAL BOTU\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"🕐 {now}\n"
        "⏱ 4 Saatlik Analiz\n"
        "📡 CoinGecko piyasa verisi\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
    )

    if results:

        messages = [header]

        for result in results:
            messages.append(
                format_signal(result)
            )

        messages.append(
            "\n⚠️ Bu sinyaller teknik analiz "
            "verilerine dayanır. Finansal tavsiye değildir."
        )

        telegram_message = "\n".join(messages)

    else:

        telegram_message = (
            header +
            "❌ Hiçbir coin için veri alınamadı."
        )

    try:

        if send_telegram(telegram_message):
            print("✅ Telegram mesajı gönderildi.")

    except Exception as e:

        print(
            f"❌ Telegram gönderim hatası: {e}"
        )

    print("🚀 Analiz tamamlandı.")


if __name__ == "__main__":
    main()
