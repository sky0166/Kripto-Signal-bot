import os
import requests
import math
from datetime import datetime, timezone

print("🚀 GELİŞMİŞ KRİPTO SİNYAL BOTU BAŞLATILDI")

# =========================================================
# TELEGRAM
# =========================================================

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
    raise RuntimeError("TELEGRAM_TOKEN veya TELEGRAM_CHAT_ID bulunamadı.")

# =========================================================
# AYARLAR
# =========================================================

SYMBOLS = [
    "BTCUSDT",
    "ETHUSDT",
    "AVAXUSDT",
    "DOGEUSDT",
    "XRPUSDT",
    "ARBUSDT",
    "APTUSDT",
    "GRTUSDT",
    "THETAUSDT",
    "ONDOUSDT",
    "APEUSDT"
]

INTERVAL = "4h"
LIMIT = 250

BINANCE_URL = "https://api.binance.com/api/v3/klines"

# =========================================================
# BINANCE VERİSİ
# =========================================================

def get_klines(symbol):
    response = requests.get(
        BINANCE_URL,
        params={
            "symbol": symbol,
            "interval": INTERVAL,
            "limit": LIMIT
        },
        timeout=20
    )

    response.raise_for_status()
    return response.json()


# =========================================================
# EMA
# =========================================================

def ema(values, period):
    if len(values) < period:
        return None

    multiplier = 2 / (period + 1)

    result = sum(values[:period]) / period

    for price in values[period:]:
        result = (price - result) * multiplier + result

    return result


# =========================================================
# RSI
# =========================================================

def rsi(values, period=14):
    if len(values) <= period:
        return None

    gains = []
    losses = []

    for i in range(1, len(values)):
        change = values[i] - values[i - 1]

        if change > 0:
            gains.append(change)
            losses.append(0)
        else:
            gains.append(0)
            losses.append(abs(change))

    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    for i in range(period, len(gains)):
        avg_gain = ((avg_gain * (period - 1)) + gains[i]) / period
        avg_loss = ((avg_loss * (period - 1)) + losses[i]) / period

    if avg_loss == 0:
        return 100

    rs = avg_gain / avg_loss

    return 100 - (100 / (1 + rs))


# =========================================================
# MACD
# =========================================================

def calculate_macd(values):
    ema12 = ema(values, 12)
    ema26 = ema(values, 26)

    if ema12 is None or ema26 is None:
        return None, None

    macd = ema12 - ema26

    # Basit MACD yön teyidi
    return macd, ema12


# =========================================================
# ANALİZ
# =========================================================

def analyze(symbol):

    candles = get_klines(symbol)

    closes = [float(x[4]) for x in candles]
    highs = [float(x[2]) for x in candles]
    lows = [float(x[3]) for x in candles]
    volumes = [float(x[5]) for x in candles]

    price = closes[-1]

    ema20 = ema(closes, 20)
    ema50 = ema(closes, 50)
    ema200 = ema(closes, 200)

    rsi_value = rsi(closes, 14)

    macd_value, _ = calculate_macd(closes)

    if not all([ema20, ema50, ema200, rsi_value is not None, macd_value is not None]):
        return None

    # -----------------------------------------------------
    # HACİM
    # -----------------------------------------------------

    average_volume = sum(volumes[-20:]) / 20
    current_volume = volumes[-1]

    volume_ratio = current_volume / average_volume if average_volume else 0

    # -----------------------------------------------------
    # PUAN SİSTEMİ
    # -----------------------------------------------------

    long_score = 0
    short_score = 0

    reasons_long = []
    reasons_short = []

    # EMA20 / EMA50
    if price > ema20:
        long_score += 15
        reasons_long.append("Fiyat EMA20 üstünde")

    else:
        short_score += 15
        reasons_short.append("Fiyat EMA20 altında")

    if ema20 > ema50:
        long_score += 15
        reasons_long.append("EMA20 > EMA50")

    else:
        short_score += 15
        reasons_short.append("EMA20 < EMA50")

    # EMA200 ana trend
    if price > ema200:
        long_score += 20
        reasons_long.append("Ana trend yukarı")

    else:
        short_score += 20
        reasons_short.append("Ana trend aşağı")

    # RSI
    if 50 < rsi_value < 70:
        long_score += 15
        reasons_long.append("RSI yükseliş bölgesinde")

    elif 30 < rsi_value < 50:
        short_score += 15
        reasons_short.append("RSI düşüş bölgesinde")

    elif rsi_value >= 70:
        short_score += 5
        reasons_short.append("RSI aşırı alım")

    elif rsi_value <= 30:
        long_score += 5
        reasons_long.append("RSI aşırı satım")

    # MACD
    if macd_value > 0:
        long_score += 15
        reasons_long.append("MACD pozitif")

    else:
        short_score += 15
        reasons_short.append("MACD negatif")

    # Hacim
    if volume_ratio >= 1.20:
        if long_score > short_score:
            long_score += 20
            reasons_long.append("Hacim güçlü")

        elif short_score > long_score:
            short_score += 20
            reasons_short.append("Hacim güçlü")

    # -----------------------------------------------------
    # SİNYAL
    # -----------------------------------------------------

    if long_score >= 70 and long_score > short_score:
        signal = "🟢 GÜÇLÜ LONG"
        score = long_score
        direction = "LONG"
        reasons = reasons_long

    elif long_score >= 55 and long_score > short_score:
        signal = "🟢 LONG"
        score = long_score
        direction = "LONG"
        reasons = reasons_long

    elif short_score >= 70 and short_score > long_score:
        signal = "🔴 GÜÇLÜ SHORT"
        score = short_score
        direction = "SHORT"
        reasons = reasons_short

    elif short_score >= 55 and short_score > long_score:
        signal = "🔴 SHORT"
        score = short_score
        direction = "SHORT"
        reasons = reasons_short

    else:
        signal = "⚪ BEKLE"
        score = max(long_score, short_score)
        direction = "WAIT"
        reasons = []

    # -----------------------------------------------------
    # ATR BENZERİ VOLATİLİTE HESABI
    # -----------------------------------------------------

    ranges = []

    for i in range(-14, 0):
        ranges.append(highs[i] - lows[i])

    average_range = sum(ranges) / len(ranges)

    # Stop mesafesi
    stop_distance = average_range * 1.5

    if direction == "LONG":

        stop = price - stop_distance

        tp1 = price + stop_distance * 1.5
        tp2 = price + stop_distance * 2.5
        tp3 = price + stop_distance * 4

    elif direction == "SHORT":

        stop = price + stop_distance

        tp1 = price - stop_distance * 1.5
        tp2 = price - stop_distance * 2.5
        tp3 = price - stop_distance * 4

    else:

        stop = None
        tp1 = None
        tp2 = None
        tp3 = None

    return {
        "symbol": symbol.replace("USDT", ""),
        "price": price,
        "signal": signal,
        "score": score,
        "rsi": rsi_value,
        "ema20": ema20,
        "ema50": ema50,
        "ema200": ema200,
        "macd": macd_value,
        "volume_ratio": volume_ratio,
        "direction": direction,
        "stop": stop,
        "tp1": tp1,
        "tp2": tp2,
        "tp3": tp3,
        "reasons": reasons
    }


# =========================================================
# TELEGRAM MESAJI
# =========================================================

def send_telegram(message):

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    response = requests.post(
        url,
        data={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message
        },
        timeout=20
    )

    response.raise_for_status()


# =========================================================
# ANA PROGRAM
# =========================================================

results = []

for symbol in SYMBOLS:

    try:

        result = analyze(symbol)

        if result:
            results.append(result)

        print(f"{symbol} analiz edildi.")

    except Exception as error:

        print(f"{symbol} hata: {error}")


# =========================================================
# TELEGRAM RAPORU
# =========================================================

now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

message = f"🚀 KRİPTO SİNYAL MERKEZİ\n"
message += f"⏱️ Zaman Dilimi: 4 SAAT\n"
message += f"🕐 {now}\n"
message += "━━━━━━━━━━━━━━━━━━\n\n"

for result in results:

    message += f"💎 {result['symbol']}/USDT\n"
    message += f"💰 Fiyat: {result['price']:.8g}\n"
    message += f"📊 Sinyal: {result['signal']}\n"
    message += f"🎯 Skor: {result['score']}/100\n"
    message += f"📈 RSI: {result['rsi']:.2f}\n"
    message += f"EMA20: {result['ema20']:.8g}\n"
    message += f"EMA50: {result['ema50']:.8g}\n"
    message += f"EMA200: {result['ema200']:.8g}\n"
    message += f"📦 Hacim: {result['volume_ratio']:.2f}x\n"

    if result["direction"] != "WAIT":

        message += "\n🎯 İŞLEM PLANI\n"
        message += f"📍 Giriş: {result['price']:.8g}\n"
        message += f"🛑 Stop: {result['stop']:.8g}\n"
        message += f"🥇 TP1: {result['tp1']:.8g}\n"
        message += f"🥈 TP2: {result['tp2']:.8g}\n"
        message += f"🥉 TP3: {result['tp3']:.8g}\n"

        if result["reasons"]:

            message += "\n🧠 TEYİTLER\n"

            for reason in result["reasons"][:5]:
                message += f"• {reason}\n"

    message += "\n━━━━━━━━━━━━━━━━━━\n\n"


if not results:
    message += "⚠️ Veri alınamadı."

send_telegram(message)

print("✅ Telegram mesajı gönderildi.")
print("🚀 Analiz tamamlandı.")
