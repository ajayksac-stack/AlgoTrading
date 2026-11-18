"""fetch_index_1min_fyers.py -- download Nifty 50 and India VIX 1-min bars from Fyers.

Put this file in the SAME folder as your Fyers bot (it needs fyers_client_id.txt and a
fresh fyers_access_token.txt -- log in as you do every morning first). Then:
    python fetch_index_1min_fyers.py
It writes nifty_spot_1min_2026.csv and india_vix_1min_2026.csv in that folder.
Read-only: it only calls fyers.history(), no orders.

Fyers allows about 100 days of 1-min data per request, so it asks in 30-day pieces.
"""
import time, csv
from datetime import date, datetime, timedelta
from fyers_apiv3 import fyersModel

START, END = date(2026, 1, 1), date(2026, 10, 31)
SYMBOLS = {"NSE:NIFTY50-INDEX": "nifty_spot_1min_2026.csv", "NSE:INDIAVIX-INDEX": "india_vix_1min_2026.csv"}

APP_ID = open("fyers_client_id.txt", encoding="utf-8").read().strip()
TOKEN = open("fyers_access_token.txt", encoding="utf-8").read().strip()
fyers = fyersModel.FyersModel(token=TOKEN, is_async=False, client_id=APP_ID, log_path="")

for sym, out in SYMBOLS.items():
    seen, n = set(), 0
    with open(out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["date", "time", "open", "high", "low", "close", "volume"])
        a = START
        while a <= END:
            b = min(a + timedelta(days=29), END)
            r = fyers.history(data={"symbol": sym, "resolution": "1", "date_format": "1",
                                    "range_from": a.isoformat(), "range_to": b.isoformat(), "cont_flag": "1"})
            candles = (r or {}).get("candles") or []
            if not candles:
                print(f"  {sym} {a}..{b}: no data ({(r or {}).get('message', r)})")
            for c in candles:
                t = datetime(1970, 1, 1) + timedelta(seconds=int(c[0]), hours=5, minutes=30)   # UTC -> IST
                if t in seen:
                    continue
                seen.add(t)
                w.writerow([t.strftime("%Y-%m-%d"), t.strftime("%H:%M"), c[1], c[2], c[3], c[4], c[5] if len(c) > 5 else 0])
                n += 1
            print(f"  {sym} {a}..{b}: {len(candles)} bars")
            a = b + timedelta(days=1)
            time.sleep(0.5)
    print(f"{sym}: {n:,} bars -> {out}")
print("Done. Attach the two CSV files to the chat.")
