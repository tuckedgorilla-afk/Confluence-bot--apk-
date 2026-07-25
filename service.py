import time
import requests

TELEGRAM_BOT_TOKEN = "8910884559:AAG195RVIYw1-McHPTyDcGiHluvB1qhvkA0"
TELEGRAM_CHAT_ID = "6034818819"

MIN_FUNDING_RATE = -0.05
MAX_FUNDING_RATE = 0.05
CHECK_INTERVAL = 120  # 2-minute polling for battery optimization

alert_cooldowns = {}
COOLDOWN_TIME = 900

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception:
        pass

def get_futures_tickers():
    url = "https://fapi.binance.com/fapi/v1/ticker/24hr"
    try:
        res = requests.get(url, timeout=10).json()
        return {item['symbol']: item for item in res if item['symbol'].endswith('USDT')}
    except Exception:
        return {}

def get_funding_rates():
    url = "https://fapi.binance.com/fapi/v1/premiumIndex"
    try:
        res = requests.get(url, timeout=10).json()
        return {item['symbol']: float(item['lastFundingRate']) * 100 for item in res if item['symbol'].endswith('USDT')}
    except Exception:
        return {}

def get_advanced_confluence(symbol, volume_24h):
    if volume_24h < 50_000_000:
        min_buy_ratio, max_buy_ratio, min_5m_change = 0.58, 0.42, 0.35
    else:
        min_buy_ratio, max_buy_ratio, min_5m_change = 0.65, 0.35, 0.80

    url_5m = f"https://fapi.binance.com/fapi/v1/klines?symbol={symbol}&interval=5m&limit=15"
    url_1m = f"https://fapi.binance.com/fapi/v1/klines?symbol={symbol}&interval=1m&limit=2"
    
    try:
        res_5m = requests.get(url_5m, timeout=5).json()
        res_1m = requests.get(url_1m, timeout=5).json()
        if len(res_5m) < 15 or len(res_1m) < 2:
            return None
        
        tr_list = [
            max(float(res_5m[i][2]) - float(res_5m[i][3]), 
                abs(float(res_5m[i][2]) - float(res_5m[i-1][4])), 
                abs(float(res_5m[i][3]) - float(res_5m[i-1][4])))
            for i in range(1, len(res_5m))
        ]
        atr = sum(tr_list) / len(tr_list)
        
        c5m = res_5m[-1]
        open_5m, close_5m = float(c5m[1]), float(c5m[4])
        vol_5m, buy_vol_5m = float(c5m[5]), float(c5m[9])
        
        c1m = res_1m[-1]
        open_1m, close_1m = float(c1m[1]), float(c1m[4])
        change_1m = ((close_1m - open_1m) / open_1m) * 100

        if vol_5m == 0:
            return None

        change_5m = ((close_5m - open_5m) / open_5m) * 100
        buy_ratio = buy_vol_5m / vol_5m
        
        price_str = str(c5m[4])
        decimals = len(price_str.split('.')[1]) if '.' in price_str else 2

        return {
            "entry_price": close_5m, "change_5m": change_5m, "change_1m": change_1m,
            "buy_ratio": buy_ratio, "atr": atr, "decimals": decimals,
            "min_buy_ratio": min_buy_ratio, "max_buy_ratio": max_buy_ratio,
            "min_5m_change": min_5m_change
        }
    except Exception:
        return None

def run_scanner():
    while True:
        try:
            tickers = get_futures_tickers()
            funding_rates = get_funding_rates()
            current_time = time.time()
            
            for symbol, funding in funding_rates.items():
                if symbol in alert_cooldowns and (current_time - alert_cooldowns[symbol] < COOLDOWN_TIME):
                    continue
                if symbol not in tickers:
                    continue
                
                vol_24h = float(tickers[symbol]['quoteVolume'])
                
                # SHORT SQUEEZE (LONG ENTRY)
                if funding <= MIN_FUNDING_RATE:
                    data = get_advanced_confluence(symbol, vol_24h)
                    if data and data["change_5m"] >= data["min_5m_change"] and data["buy_ratio"] >= data["min_buy_ratio"]:
                        entry, atr, dec = data["entry_price"], data["atr"], data["decimals"]
                        sl = entry - (atr * 1.0)
                        risk = entry - sl
                        tp1, tp2 = entry + (risk * 1.5), entry + (risk * 3.0)
                        
                        msg = (
                            f"🔥 *HIGH-CONFLUENCE SHORT SQUEEZE (LONG)*\n"
                            f"📌 *Pair:* #{symbol}\n"
                            f"📉 *Funding:* `{funding:.4f}%` | *Buy Vol:* `{data['buy_ratio']*100:.1f}%`\n"
                            f"⚡ *1m Velocity:* `{data['change_1m']:+.2f}%` | *5m Change:* `{data['change_5m']:+.2f}%`\n\n"
                            f"🎯 *TRADE EXECUTION LEVELS:*\n"
                            f"▶️ *Entry Price:* `{entry:.{dec}f}`\n"
                            f"🛑 *Stop Loss:* `{sl:.{dec}f}` (-{((entry-sl)/entry)*100:.2f}%)\n"
                            f"🎯 *Take Profit 1:* `{tp1:.{dec}f}` (+{((tp1-entry)/entry)*100:.2f}%)\n"
                            f"🚀 *Take Profit 2:* `{tp2:.{dec}f}` (+{((tp2-entry)/entry)*100:.2f}%)\n\n"
                            f"⚖️ *Risk/Reward:* 1:3.0 (1.0x ATR Managed)"
                        )
                        send_telegram(msg)
                        alert_cooldowns[symbol] = current_time

                # DUMP ALERT (SHORT ENTRY)
                elif funding >= MAX_FUNDING_RATE:
                    data = get_advanced_confluence(symbol, vol_24h)
                    if data and data["change_5m"] <= -data["min_5m_change"] and data["buy_ratio"] <= data["max_buy_ratio"]:
                        entry, atr, dec = data["entry_price"], data["atr"], data["decimals"]
                        sl = entry + (atr * 1.0)
                        risk = sl - entry
                        tp1, tp2 = entry - (risk * 1.5), entry - (risk * 3.0)
                        
                        msg = (
                            f"🚨 *HIGH-CONFLUENCE DUMP ALERT (SHORT)*\n"
                            f"📌 *Pair:* #{symbol}\n"
                            f"📈 *Funding:* `+{funding:.4f}%` | *Sell Vol:* `{(1 - data['buy_ratio'])*100:.1f}%`\n"
                            f"⚡ *1m Velocity:* `{data['change_1m']:+.2f}%` | *5m Change:* `{data['change_5m']:+.2f}%`\n\n"
                            f"🎯 *TRADE EXECUTION LEVELS:*\n"
                            f"▶️ *Entry Price:* `{entry:.{dec}f}`\n"
                            f"🛑 *Stop Loss:* `{sl:.{dec}f}` (-{((sl-entry)/entry)*100:.2f}%)\n"
                            f"🎯 *Take Profit 1:* `{tp1:.{dec}f}` (+{((entry-tp1)/entry)*100:.2f}%)\n"
                            f"🚀 *Take Profit 2:* `{tp2:.{dec}f}` (+{((entry-tp2)/entry)*100:.2f}%)\n\n"
                            f"⚖️ *Risk/Reward:* 1:3.0 (1.0x ATR Managed)"
                        )
                        send_telegram(msg)
                        alert_cooldowns[symbol] = current_time

            time.sleep(CHECK_INTERVAL)
        except Exception:
            time.sleep(10)

if __name__ == '__main__':
    run_scanner()
